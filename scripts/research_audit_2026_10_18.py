"""Read-only retrospective calculations; no organisms or evolution are run."""
from collections import Counter, defaultdict, deque
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
STUDIES = [
    'first_evolution', 'range_and_regulation', 'source_pressure',
    'goal_conditioning', 'factor_curriculum', 'goal_beacon', 'balanced_goal',
    'junction_choice', 'choice_priority', 'distance_curriculum', 'capacity_growth',
]
INPUTS = {}


def read(path):
    path = ROOT / path
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as stream:
        return json.load(stream)


def rows(path):
    path = ROOT / path
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            yield json.loads(line)


def graph_distances(cells, width, source):
    d = [-1] * len(cells)
    d[source] = 0
    queue = deque([source])
    while queue:
        p = queue.popleft()
        candidates = []
        if p % width: candidates.append(p - 1)
        if p % width < width - 1: candidates.append(p + 1)
        if p >= width: candidates.append(p - width)
        if p + width < len(cells): candidates.append(p + width)
        for q in candidates:
            if cells[q] and d[q] < 0:
                d[q] = d[p] + 1
                queue.append(q)
    return d


def collect(out):
    if (out / 'analysis.json').exists():
        raise FileExistsError('Choose a fresh audit output directory')
    started = time.perf_counter()
    studies = []
    for name in STUDIES:
        base = f'results/{name}'
        env, verification = read(base + '/environment.json'), read(base + '/verification.json')
        studies.append(dict(
            study=name, main_seconds=env['elapsed_seconds'],
            training_seconds=env.get('training_seconds'),
            normal_responses=verification.get('normal_maze_evaluations'),
            probe_runs=verification.get('developmental_probe_runs'),
            registered_ids=verification.get('new_individuals', verification.get('lineage_genomes')),
        ))
    base = 'results/capacity_growth'
    champions = read(base + '/champions.json')
    mutations = read(base + '/mutation_events.json')
    populations = []
    for condition, saved in sorted(champions.items()):
        n = saved['config']['population']
        g = saved['next_generation']
        populations.append(dict(condition=condition, population=n, generations=g,
            protected=len(saved['protected']), immigrants_per_generation=n // 10,
            mutated_children=mutations[condition]['children'],
            mean_mutated_children_per_generation=mutations[condition]['children'] / g))

    manifest = {m['case_id']: m for m in read(base + '/mazes.json.gz')}
    pairs = read(base + '/pairs.json')
    geometry = defaultdict(Counter)
    distances = defaultdict(list)
    details = []
    for pair in pairs:
        if pair['decision'] is None: continue
        a, b = [manifest[pair[k]] for k in ('first', 'second')]
        cells = bytes.fromhex(a['cells_hex'])
        region = [pair['decision']['vertex']] + pair['decision']['exits']
        ds = [graph_distances(cells, a['w'], m['goal']) for m in (a, b)]
        nearest = [min(d[p] for p in region) for d in ds]
        vertex = [d[region[0]] for d in ds]
        split = a['split']
        c = geometry[split]
        c['pairs'] += 1
        c['both_goals_outside_region_cone16'] += all(d > 16 for d in nearest)
        c['any_goal_outside_region_cone16'] += any(d > 16 for d in nearest)
        c['both_goals_outside_vertex_cone16'] += all(d > 16 for d in vertex)
        c['goal_to_region_inputs'] += 2
        c['goal_to_region_beyond16'] += sum(d > 16 for d in nearest)
        distances[split].extend(vertex)
        details.append(dict(first=a['case_id'], second=b['case_id'], vertex_distances=vertex,
            nearest_region_distances=nearest, source_goal_edges=[a['oracle_length'] - 1, b['oracle_length'] - 1]))
    for split, values in distances.items():
        geometry[split]['median_goal_to_vertex_distance'] = statistics.median(values)
        geometry[split]['max_goal_to_vertex_distance'] = max(values)

    # Reassess existing bookkeeping only. These are repeated response opportunities,
    # not independent genotypes, layouts, or statistical trials.
    training = defaultdict(Counter)
    for path in sorted((ROOT / base / 'logs/stage0').glob('*.evaluations.jsonl.gz')):
        for r in rows(path.relative_to(ROOT)):
            if r['split'] != 'train': continue
            c = training[r['condition']]
            c['organism_batches'] += 1
            for a in r['cases']:
                c['normal_responses'] += 1
                c['normal_halted_before16'] += a['steps'] < 16
                c['normal_budget_failure'] += 'budget' in a['status']
                c['normal_valid'] += a['valid']
                if a['junction']['eligible']:
                    c['regular_goal_inputs'] += 1
                    c['positive_junction_score'] += a['junction']['score'] > 0
                    c['positive_junction_score_after_ordinary_halt'] += a['junction']['score'] > 0 and a['steps'] < 16
                    c['strict_choice'] += a['junction']['strict']
                    c['strict_choice_after_ordinary_halt'] += a['junction']['strict'] and a['steps'] < 16
                    c['strict_choice_but_invalid_normal'] += a['junction']['strict'] and not a['valid']
                    c['signal_at_least_half'] += a['signal']['score'] >= .5
                    c['signal_at_least_half_but_zero_goal_score'] += a['signal']['score'] >= .5 and a['goal']['score'] == 0

    seed = Counter()
    for r in rows('results/range_and_regulation/holdout.jsonl.gz'):
        if r['arm'] != 'control/local/seeded/frozen' or not r['valid_path']: continue
        seed['valid_outputs'] += 1
        seed['steps_equal_2D_plus1'] += r['steps'] == 2*r['edges'] + 1
        seed['distance_at_least8'] += r['edges'] >= 8
        seed['distance_at_least8_and_steps_over16'] += r['edges'] >= 8 and r['steps'] > 16

    result = dict(
        scope='Retrospective read-only aggregation and graph-distance calculations; no candidate inference, new maze generation, selection or evolution.',
        studies=studies,
        main_seconds_total=sum(r['main_seconds'] for r in studies),
        v3_through_v11_normal_responses=sum(r['normal_responses'] or 0 for r in studies),
        v3_through_v11_probe_runs=sum(r['probe_runs'] or 0 for r in studies),
        registered_ids_sum=sum(r['registered_ids'] or 0 for r in studies),
        v11_population_allocation=populations,
        v11_horizon_geometry=geometry,
        v11_horizon_geometry_details=details,
        v11_training_bookkeeping=training,
        v2_frozen_seed_timing=seed,
        elapsed_seconds=time.perf_counter() - started,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256=INPUTS,
        caveats=[
            'Main wall time excludes separately recorded tests, diagnostic runs, audits and development.',
            'Registered IDs include initial re-identification, copies, controls and resampling; not unique independent discoveries.',
            'Geometry gives necessary local causal-cone conditions, not sufficiency; nonlocal programs have different cones.',
            'If both goals lie outside the entire region at tick 16, deterministic local forced-probe states there cannot distinguish the two inputs.',
            'Training counters count repeated response opportunities, and scalar scores are not general solving.',
        ],
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    small = {k:v for k,v in result.items() if k not in ('input_sha256','v11_horizon_geometry_details','v11_training_bookkeeping','studies')}
    print(json.dumps(small, indent=2))


def verify(out):
    # A second implementation checks the saved geometry, outside all inference.
    sys.path.insert(0, str(ROOT))
    from maze_evolution.evaluator import Maze, distances

    raw = (out / 'analysis.json').read_bytes()
    result = json.loads(raw)
    assert result['source_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for path, expected in result['input_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    base = 'results/capacity_growth'
    manifest = {m['case_id']: m for m in read(base + '/mazes.json.gz')}
    pairs = {p['first']: p for p in read(base + '/pairs.json')}
    checked = 0
    for row in result['v11_horizon_geometry_details']:
        pair = pairs[row['first']]
        region = [pair['decision']['vertex']] + pair['decision']['exits']
        for i, case_id in enumerate((row['first'], row['second'])):
            m = manifest[case_id]
            maze = Maze(bytes.fromhex(m['cells_hex']), m['w'], m['h'], m['start'], m['goal'])
            d = distances(maze, maze.goal)
            assert d[region[0]] == row['vertex_distances'][i]
            assert min(d[p] for p in region) == row['nearest_region_distances'][i]
            assert d[maze.start] == row['source_goal_edges'][i]
            checked += 1
    verification = dict(
        all_checks_passed=True, geometry_inputs_checked=checked,
        input_hashes_checked=len(result['input_sha256']),
        analysis_sha256=hashlib.sha256(raw).hexdigest(),
        scope='Independent distance implementation confirms every saved geometric distance; source result hashes unchanged. No candidate inference.',
    )
    (out / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
    print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'results/repeat_research_audit')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    verify(args.out) if args.verify else collect(args.out)
