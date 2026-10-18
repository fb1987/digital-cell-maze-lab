"""Secondary V12C time course: freeze earlier validation selections before final cases."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from .foundation_calibration import LIMITS, write_json
from .foundation_calibration_audit import lines, unpack
from .foundation_data import load_pairs
from .foundation_fitness import evaluate
from .foundation_study import read_compressed, compressed_json
from .foundation_study_verify_core import Checker
from .growth import Individual
from .growth_runtime import Organism


BOUNDARIES = (48, 128, 256)


def boundary_aliases(states, rounds):
    aliases = []
    for state in states:
        cfg = state['config']
        key = '/'.join(str(cfg[k]) for k in ('study', 'topology', 'origin', 'method', 'replicate'))
        for boundary in (0, *[g for g in BOUNDARIES if g < rounds], rounds):
            identity = state['frozen']['id'] if boundary == 0 else state['history'][boundary - 1]['champion']
            aliases.append(dict(condition=key, config=cfg, generation=boundary, id=identity))
    return aliases


def freeze(out):
    out = Path(out)
    if (out / 'confirmation').exists():
        raise ValueError('Time-course selections must freeze before final cases exist')
    target = out / 'timecourse'
    target.mkdir(exist_ok=False)
    started = time.perf_counter()
    summary = json.loads((out / 'search_summary.json').read_text())
    checkpoint = read_compressed(out / 'checkpoint.latest.json.gz')
    assert checkpoint['generation'] == summary['rounds']
    aliases = boundary_aliases(checkpoint['states'], summary['rounds'])
    needed = {a['id'] for a in aliases}
    models = {}
    for segment in summary['segments']:
        for row in lines(out / segment['files'][0]):
            if row['id'] in needed:
                item = Individual.load(row)
                models[item.identity] = item.save()
        if len(models) == len(needed):
            break
    assert set(models) == needed
    compressed_json(target / 'selections.json.gz', dict(aliases=aliases, models=models))
    selection_sha = hashlib.sha256((target / 'selections.json.gz').read_bytes()).hexdigest()
    result = dict(scope='Secondary time-course selections, fixed before any final-case generation',
        boundaries=BOUNDARIES, actual_rounds=summary['rounds'], selected_aliases=len(aliases), unique_ids=len(models),
        selection_sha256=selection_sha, elapsed_seconds=time.perf_counter() - started,
        search_summary_sha256=hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write_json(target / 'freeze.json', result)
    print(json.dumps(result, indent=2), flush=True)


def run(out):
    out = Path(out)
    target = out / 'timecourse'
    proof = json.loads((target / 'freeze.json').read_text())
    assert hashlib.sha256((target / 'selections.json.gz').read_bytes()).hexdigest() == proof['selection_sha256']
    assert hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest() == proof['search_summary_sha256']
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == proof['source_sha256']
    verification = json.loads((out / 'verification.json').read_text())
    assert verification['all_checks_passed']
    assert hashlib.sha256((out / 'confirmation/summary.json').read_bytes()).hexdigest() == verification['confirmation_summary_sha256']
    if (target / 'summary.json').exists():
        raise FileExistsError('The secondary time course is already completed')
    started = time.perf_counter()
    selected = read_compressed(target / 'selections.json.gz')
    cases, groups = load_pairs(out / 'confirmation')
    pairs = {rep: [p for g in groups if g.key[1] == rep for p in g.pairs] for rep in range(3)}
    cache = {}
    # Reuse exact previously audited ordinary results for identical model/input combinations.
    for record in lines(out / 'confirmation/outputs.jsonl.gz'):
        if record['scope'] == 'micro' and record['key'].startswith('foundation_study/'):
            cache[record['digest'], record['topology'], record['replicate']] = record['cases']
    checker = Checker(cases)
    responses = work = replay_responses = replay_work = 0
    results = []
    with gzip.open(target / 'outputs.jsonl.gz', 'wt') as log:
        for alias in selected['aliases']:
            cfg = alias['config']
            item = Individual.load(selected['models'][alias['id']])
            key = item.genome.digest, cfg['topology'], cfg['replicate']
            if key not in cache:
                ev = evaluate(item, pairs[cfg['replicate']], cfg['topology'], LIMITS, goal_pulse=True)
                cache[key] = ev.rows
                responses += len(ev.rows)
                work += ev.work
                organism = Organism(item.genome, cfg['topology'], LIMITS, goal_pulse=True)
                for row in ev.rows:
                    m = cases[row['case']].maze
                    r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
                    assert np.array_equal(r.mask, unpack(row, len(m.cells)))
                    assert (r.status, r.steps, r.spatial_reads, r.dispatches) == (row['status'], row['steps'], row['reads'], row['dispatches'])
                    replay_responses += 1
                    replay_work += r.spatial_reads + r.dispatches
            rows = cache[key]
            checker.rows(rows)
            entry = dict(condition=alias['condition'], generation=alias['generation'], id=item.identity,
                digest=item.genome.digest, topology=cfg['topology'], replicate=cfg['replicate'],
                levels={str(l): dict(optimal=sum(r['optimal'] for r in rows if f'/level{l}/' in r['case']),
                    paired_optimal=sum(r['pair_optimal'] for r in rows if f'/level{l}/' in r['case']) // 2)
                    for l in range(4)})
            results.append(entry)
            log.write(json.dumps(dict(**entry, cases=rows), separators=(',', ':')) + '\n')
    result = dict(scope='Secondary, pre-final-frozen time course on the same confirmation cases; not independent repeated holdouts',
        results=results, new_responses=responses, new_work=work, replay_responses=replay_responses,
        replay_work=replay_work, independently_graded_rasters=checker.rasters,
        elapsed_seconds=time.perf_counter() - started, selection_sha256=proof['selection_sha256'],
        source_sha256=proof['source_sha256'],
        confirmation_outputs_sha256=hashlib.sha256((out / 'confirmation/outputs.jsonl.gz').read_bytes()).hexdigest())
    write_json(target / 'summary.json', result)
    print(json.dumps({k: result[k] for k in ('new_responses', 'elapsed_seconds', 'replay_responses')}, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--freeze', action='store_true')
    a = p.parse_args()
    (freeze if a.freeze else run)(a.out)
