"""Post-hoc input/range interventions on frozen V12D successes, not new holdouts."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from .evaluator import Maze, Oracle
from .foundation_calibration import ROOT, write_json
from .foundation_calibration_audit import lines, unpack
from .foundation_data import load_pairs
from .foundation_study import read_compressed
from .foundation_study_confirm import normal_row
from .foundation_study_verify_core import Checker
from .growth import Individual
from .growth_runtime import Organism
from .runtime import Limits


def run(out):
    out = Path(out)
    final = out / 'confirmation'
    target = out / 'interventions'
    if target.exists():
        raise FileExistsError('Use a separately labelled diagnostic directory')
    target.mkdir()
    started = time.perf_counter()
    frozen = read_compressed(out / 'frozen_selections.json.gz')
    cases, _ = load_pairs(final)
    with gzip.open(final / 'general_mazes.json.gz', 'rt') as f:
        for row in json.load(f):
            m = Maze(bytes.fromhex(row['cells_hex']), row['w'], row['h'], row['start'], row['goal'],
                     row['family'], row['seed'], row['split'], row['case_id'])
            cases[m.case_id] = Oracle.build(m)
    models = {}
    for state in frozen.values():
        for item in [state['champion'], *[v['item'] for v in state['skills'].values()]]:
            individual = Individual.load(item)
            models[individual.identity] = individual
    tasks, aliases = {}, defaultdict(list)
    for record in lines(final / 'outputs.jsonl.gz'):
        if record['key'] not in frozen or record['role'] not in ('champion', 'skill1', 'skill2', 'skill3'):
            continue
        for row in record['cases']:
            if not row['optimal'] or len(cases[row['case']].path) <= 2:
                continue
            key = record['digest'], record['topology'], tuple(record['limits'].values()), row['case']
            tasks.setdefault(key, dict(id=record['id'], limits=record['limits'], topology=record['topology'], original=row))
            aliases[key].append(dict(condition=record['key'], role=record['role'], scope=record['scope']))
    checker = Checker(cases)
    totals, per_model = Counter(), defaultdict(Counter)
    work = responses = 0
    with gzip.open(target / 'outputs.jsonl.gz', 'wt') as log:
        for key, task in tasks.items():
            digest, topology, _, case = key
            m = cases[case].maze
            item = models[task['id']]
            assert item.genome.digest == digest
            baseline = task['original']
            rows = {}
            for pulse, ablate, name in ((True, False, 'replay'), (False, False, 'no_goal_pulse'),
                                        (True, True, 'zero_nonlocal'), (False, True, 'both')):
                organism = Organism(item.genome, topology, Limits(**task['limits']), ablate_nonlocal=ablate, goal_pulse=pulse)
                r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
                row = normal_row(r, cases[case])
                checker.row(row)
                if name == 'replay':
                    assert np.array_equal(r.mask, unpack(baseline, len(m.cells)))
                    assert r.status == baseline['status'] and r.steps == baseline['steps']
                    assert (r.spatial_reads, r.dispatches) == (baseline['reads'], baseline['dispatches'])
                rows[name] = row
                totals[name + '_retained_shortest'] += row['optimal']
                per_model[digest + '/' + topology][name + '_retained_shortest'] += row['optimal']
                work += r.spatial_reads + r.dispatches
                responses += 1
            per_model[digest + '/' + topology]['successful_inputs'] += 1
            totals['successful_inputs'] += 1
            totals['originals_reading_nonlocal'] += sum(baseline['range_reads'][1:]) > 0
            log.write(json.dumps(dict(id=item.identity, digest=digest, topology=topology, limits=task['limits'],
                case=case, aliases=aliases[key], variants=rows), separators=(',', ':')) + '\n')
    result = dict(scope='Post-hoc success-conditioned interventions on reused final inputs; no new generalization estimate',
        interpretation='No-goal-pulse still retains the static goal flag. Nonlocal ablation replaces radius>1 read values with zero, retaining read charges; it does not substitute local reads.',
        totals=dict(totals), per_model={k: dict(v) for k, v in per_model.items()},
        responses=responses, work=work, independently_graded_rasters=checker.rasters,
        elapsed_seconds=time.perf_counter() - started,
        frozen_sha256=hashlib.sha256((out / 'frozen_selections.json.gz').read_bytes()).hexdigest(),
        confirmation_outputs_sha256=hashlib.sha256((final / 'outputs.jsonl.gz').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write_json(target / 'summary.json', result)
    print(json.dumps(result['totals'], indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
