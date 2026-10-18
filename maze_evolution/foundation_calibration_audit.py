"""Independent saved-raster/score audit, mutation replay and selected inference replay."""
import argparse
from collections import deque
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from cellular_maze_lab import neighbors
from .evaluator import assess, distances
from .foundation_data import load_pairs, prior_manifests, layout_hash
from .foundation_calibration import ROOT, LIMITS, controls, write_json
from .growth import Genome, Individual, replay_mutation
from .growth_runtime import Organism, observe
from .runtime import Reaction


def lines(path):
    with gzip.open(path, 'rt') as f:
        for line in f:
            yield json.loads(line)


def unpack(row, n):
    raw = bytes.fromhex(row['mask'])
    assert len(raw) == (n + 7) // 8
    return np.unpackbits(np.frombuffer(raw, dtype=np.uint8), bitorder='little')[:n]


def independently_scored_partial(mask, oracle):
    if not oracle.path:
        return 0.
    m = oracle.maze
    selected = {i for i, value in enumerate(mask) if value}
    if not selected or any(not m.cells[p] for p in selected):
        return 0.
    adjacency = {p: [q for q in neighbors(p, m.w, m.h) if q in selected] for p in selected}
    reached = []
    scores = []
    for endpoint, opposite in ((m.start, m.goal), (m.goal, m.start)):
        seen = set()
        pending = [endpoint] if endpoint in selected else []
        while pending:
            p = pending.pop()
            if p in seen:
                continue
            seen.add(p)
            pending.extend(q for q in adjacency[p] if q not in seen)
        d = distances(m, opposite)
        progress = max((1 - d[p] / max(1, len(oracle.path) - 1) for p in seen if d[p] >= 0), default=0.)
        scores.append(.1 * bool(seen) + .8 * progress)
        reached.append(seen)
    branches = sum(max(0, len(qs) - (1 if p == m.start or p == m.goal else 2))
                   for p, qs in adjacency.items())
    stray = len(selected - reached[0] - reached[1]) / len(m.cells)
    return min(.99, max(0., .5 * sum(scores) / (1 + 2 * branches) - .2 * stray))


def check_rows(rows, cases):
    for row in rows:
        o = cases[row['case']]
        mask = unpack(row, len(o.maze.cells))
        r = Reaction(mask, row['status'], row['steps'], row['reads'], row['dispatches'], row['array_bytes'])
        a = assess(r, o)
        assert (a.valid_path, a.optimal, a.no_path_correct, a.failure) == (row['valid'], row['optimal'], row['no_path'], row['failure'])
        assert abs(independently_scored_partial(mask, o) - row['partial']) < 1e-10
    for i in range(0, len(rows), 2):
        a, b = rows[i:i + 2]
        assert all(r['pair_valid'] == (a['valid'] and b['valid']) for r in (a, b))
        assert all(r['pair_optimal'] == (a['optimal'] and b['optimal']) for r in (a, b))
        assert all(abs(r['paired_partial'] - min(a['partial'], b['partial'])) < 1e-10 for r in (a, b))
    work = sum(r['reads'] + r['dispatches'] for r in rows)
    complete = all(r['valid'] or r['no_path'] for r in rows)
    fitness = (sum(r['valid'] for r in rows), sum(r['optimal'] for r in rows),
        sum(r['no_path'] for r in rows) - sum(r['reachable'] and r['status'] == 'no_path' for r in rows),
        sum(r['pair_optimal'] for r in rows) // 2,
        round(sum(r['partial'] + r['paired_partial'] for r in rows), 8), -work if complete else 0)
    return fitness, work


def run(out):
    out = Path(out)
    started = time.perf_counter()
    summary = json.loads((out / 'summary.json').read_text())
    for path, sha in {**summary['source_sha256'], **summary['input_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
    assert hashlib.sha256((out / 'frozen_selections.json').read_bytes()).hexdigest() == summary['frozen_sha256']
    cases, groups = load_pairs(out)
    with gzip.open(out / 'fixtures.json.gz', 'rt') as f:
        fixture_rows = json.load(f)
    old = prior_manifests(ROOT) + fixture_rows
    from .evaluator import Maze
    previous = {layout_hash(Maze(bytes.fromhex(m['cells_hex']), m['w'], m['h'], m['start'], m['goal'])) for m in old}
    owners = {}
    for group in groups:
        for pair in group.pairs:
            for o in pair.cases:
                h = layout_hash(o.maze)
                assert h not in previous
                assert owners.setdefault(h, group.identity) == group.identity
                label = o._foundation_label
                if label:
                    assert label['prefix'][0] == o.maze.start
                    assert label['prefix'][-1] == label['vertex']
                    assert label['distance'] + o.to_goal[label['vertex']] == len(o.path) - 1
    states = json.loads((out / 'frozen_selections.json').read_text())
    all_genomes = {}
    mutation_count = evaluation_count = normal_count = replay_count = probe_count = 0
    replay_work = 0
    for key, state in states.items():
        damage, rep = key.split('/r')
        expected = controls()[damage].genome
        registry = list(lines(out / f'{damage}_{rep}.lineage.jsonl.gz'))
        genomes = {}
        for row in registry:
            g = Genome.from_dict(row['genome'])
            if row['parent'] is None:
                assert row['birth'] == 0 and g == expected and row['founder'] == controls()[damage].identity
            else:
                assert replay_mutation(genomes[row['parent']], row['events'], 256) == g
                mutation_count += 1
            genomes[row['id']] = g
        all_genomes.update(genomes)
        work = responses = 0
        for row in lines(out / f'{damage}_{rep}.evaluations.jsonl.gz'):
            rank, units = check_rows(row['cases'], cases)
            assert rank == tuple(row['fitness']) and units == row['work']
            work += units
            responses += len(row['cases'])
            evaluation_count += 1
        assert (work, responses) == (state['work'], state['responses'])
        assert json.loads((out / 'checkpoints' / f'{damage}_{rep}.json').read_text()) == state
        for saved in [state['champion'], state['frozen'], *state['population']]:
            assert genomes[saved['id']] == Genome.from_dict(saved['genome'])
    for row in lines(out / 'holdout.jsonl.gz'):
        if 'cases' not in row:
            o = cases[row['case']]
            mask = unpack(row, len(o.maze.cells))
            assert assess(Reaction(mask, 'emitted', 0, 0, 0, 0), o).optimal
            continue
        rank, _ = check_rows(row['cases'], cases)
        normal_count += len(row['cases'])
        organism = Organism(all_genomes[row['id']], 'local', LIMITS, goal_pulse=True)
        for saved in row['cases']:
            o = cases[saved['case']]
            m = o.maze
            r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
            assert np.array_equal(r.mask, unpack(saved, len(m.cells)))
            assert (r.status, r.steps, r.spatial_reads, r.dispatches) == (saved['status'], saved['steps'], saved['reads'], saved['dispatches'])
            replay_count += 1
            replay_work += r.spatial_reads + r.dispatches
    panel = controls()
    for row in lines(out / 'control_matrix.jsonl.gz'):
        if row['kind'] == 'ordinary':
            check_rows(row['cases'], cases)
            normal_count += len(row['cases'])
            continue
        name, topology, pulse = row['key'].split('/')
        organism = Organism(panel[name].genome, topology, LIMITS, goal_pulse=bool(int(pulse[-1])))
        o = cases[row['case']]
        m = o.maze
        obs = observe(organism, m.cells, m.w, m.h, m.start, m.goal, row['horizon'], True, row['forced'])
        assert hashlib.sha256(obs.state.tobytes()).hexdigest() == row['state_sha256']
        assert np.array_equal(obs.state[2] > 0, unpack(row, len(m.cells)))
        assert (obs.steps, obs.status, obs.reads + obs.dispatches) == (row['steps'], row['status'], row['work'])
        assert abs(independently_scored_partial(obs.state[2] > 0, o) - row['partial']) < 1e-10
        probe_count += 1
        replay_work += obs.reads + obs.dispatches
    result = dict(all_checks_passed=True, source_hashes=len(summary['source_sha256']),
        input_hashes=len(summary['input_sha256']), groups=len(groups), layouts=len(owners),
        mutations=mutation_count, fitness_records=evaluation_count, nontraining_normals=normal_count,
        selected_normal_replays=replay_count, probe_replays=probe_count,
        replay_work=replay_work, elapsed_seconds=time.perf_counter() - started,
        summary_sha256=hashlib.sha256((out / 'summary.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write_json(out / 'verification.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
