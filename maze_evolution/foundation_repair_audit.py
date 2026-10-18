"""V12B independent masks/scores, lineage and confirmation replay."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import time

import numpy as np
from .datasets import seed_for
from .evaluator import Maze, assess
from .foundation_calibration import ROOT, LIMITS, controls, write_json
from .foundation_calibration_audit import lines, unpack, check_rows
from .foundation_data import load_pairs, prior_manifests, layout_hash
from .growth import Genome, replay_mutation
from .growth_runtime import Organism
from .runtime import Reaction


def run(out):
    out = Path(out)
    started = time.perf_counter()
    summary = json.loads((out / 'summary.json').read_text())
    for path, sha in {**summary['source_sha256'], **summary['input_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
    frozen = out / 'frozen_selections.json'
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == summary['frozen_sha256']
    packet = json.loads(frozen.read_text())
    states = packet['states']
    cases, groups = load_pairs(out)
    prior = ROOT / 'results/foundation_calibration'
    previous = prior_manifests(ROOT, [prior / 'mazes.json.gz', prior / 'fixtures.json.gz'])
    old = {layout_hash(Maze(bytes.fromhex(m['cells_hex']), m['w'], m['h'], m['start'], m['goal'])) for m in previous}
    owners = {}
    for group in groups:
        for pair in group.pairs:
            for o in pair.cases:
                h = layout_hash(o.maze)
                assert h not in old and owners.setdefault(h, group.identity) == group.identity
                label = o._foundation_label
                assert label['prefix'][0] == o.maze.start
                assert label['distance'] + o.to_goal[label['vertex']] == len(o.path) - 1
    all_genomes = {i.identity: i.genome for i in controls().values()}
    mutations = records = 0
    for key, state in states.items():
        damage, policy, r = key.split('/')
        rep = int(r[1:])
        slug = f'{damage}_{policy}_{rep}'
        root = controls()[damage]
        genomes = {}
        for row in lines(out / f'{slug}.lineage.jsonl.gz'):
            g = Genome.from_dict(row['genome'])
            if row['parent'] is None:
                assert row['birth'] == 0 and g == root.genome and row['founder'] == root.identity
            else:
                if policy == 'single':
                    assert len(row['events']) == 1
                assert replay_mutation(genomes[row['parent']], row['events'], 256) == g
                mutations += 1
            genomes[row['id']] = g
        all_genomes.update(genomes)
        responses = work = 0
        for row in lines(out / f'{slug}.evaluations.jsonl.gz'):
            fit, units = check_rows(row['cases'], cases)
            assert fit == tuple(row['fitness']) and units == row['work']
            responses += len(row['cases'])
            work += units
            records += 1
        assert (responses, work) == (state['responses'], state['work'])
        assert state == json.loads((out / 'checkpoints' / f'{slug}.json').read_text())
        for item in [state['champion'], state['frozen'], *state['population']]:
            assert Genome.from_dict(item['genome']) == genomes[item['id']]
        rng_state = random.Random(seed_for(summary['seed'], 'repair-paired-rng/' + damage, rep, 0)).getstate()
        assert summary['conditions'][key]['initial_rng_sha256'] == hashlib.sha256(json.dumps(rng_state).encode()).hexdigest()
        other = states[f'{damage}/{"single" if policy == "wide" else "wide"}/r{rep}']
        assert state['initial_digests'] == other['initial_digests']
    ranks = {}
    for policy in ('wide', 'single'):
        chosen = [s for k, s in states.items() if f'/{policy}/' in k]
        ranks[policy] = (sum(s['champion_rank'][1] == len(s['champion_rows']) for s in chosen),
            sum(s['champion_rank'][1] / len(s['champion_rows']) for s in chosen) / len(chosen), int(policy == 'single'))
    assert max(ranks, key=ranks.get) == packet['chosen_policy'] == summary['chosen_policy']
    replays = replay_work = references = 0
    for record in lines(out / 'holdout.jsonl.gz'):
        if 'cases' not in record:
            o = cases[record['case']]
            assert assess(Reaction(unpack(record, len(o.maze.cells)), 'emitted', 0, 0, 0, 0), o).optimal
            references += 1
            continue
        fit, _ = check_rows(record['cases'], cases)
        if record['role'] != 'reference':
            assert fit == tuple(summary['confirmations'][record['key'] + '/' + record['role']]['fitness'])
        organism = Organism(all_genomes[record['id']], 'local', LIMITS, goal_pulse=True)
        for row in record['cases']:
            o = cases[row['case']]
            m = o.maze
            result = organism.react(m.cells, m.w, m.h, m.start, m.goal)
            assert np.array_equal(result.mask, unpack(row, len(m.cells)))
            assert (result.status, result.steps, result.spatial_reads, result.dispatches) == (row['status'], row['steps'], row['reads'], row['dispatches'])
            replays += 1
            replay_work += result.dispatches + result.spatial_reads
    result = dict(all_checks_passed=True, source_hashes=len(summary['source_sha256']), input_hashes=len(summary['input_sha256']),
        layouts=len(owners), groups=len(groups), fitness_records=records, mutations=mutations,
        confirmation_replays=replays, reference_rasters=references, replay_work=replay_work,
        chosen_policy=summary['chosen_policy'], elapsed_seconds=time.perf_counter() - started,
        summary_sha256=hashlib.sha256((out / 'summary.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write_json(out / 'verification.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
