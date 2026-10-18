"""V12A positive-control timing and isolated bounded mutation-repair calibration."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from importlib.metadata import version
import platform
from pathlib import Path
import random
import resource
import subprocess
import time

import numpy as np
from .baselines import baseline, warm_baselines
from .datasets import seed_for, manifest
from .evaluator import assess
from .foundation_data import FoundationData, prior_manifests, prior_hashes
from .foundation_fitness import evaluate, partial
from .foundation_search import Search
from .growth import Genome, Individual
from .growth_runtime import Organism, observe, warm_runtime
from .regulatory import seeded_genome, Gene
from .runtime import Limits, Reaction


ROOT = Path(__file__).resolve().parents[1]
LIMITS = Limits(max_steps=256, reads_per_site=4096, instructions_per_site=32768)
DAMAGES = ('west_return_gate', 'output_register', 'two_return_gates')


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def controls():
    intact = Genome(seeded_genome().genes)
    rows = [g.row() for g in intact.genes]
    changes = dict(intact=[], west_return_gate=[(15, 6, 63)], parent_gate=[(9, 6, 63)],
        output_register=[(28, 2, 63)], two_return_gates=[(15, 6, 63), (23, 6, 63)],
        two_dependencies=[(9, 6, 63), (28, 2, 63)])
    result = {}
    for name, edits in changes.items():
        modified = [list(row) for row in rows]
        for row, field, value in edits:
            modified[row][field] = value
        result[name] = Individual(f'positive_control/{name}', Genome(tuple(Gene(*r) for r in modified)), None, 0)
    return result


def fixtures():
    data = FoundationData(1210)
    for level in range(4):
        for family in ('perfect', 'random'):
            data.group('fixture', 0, 0, level, family, 9 if level < 3 else 17)
    data.disconnected_group('fixture', 0, 0)
    data.group('resume_fixture', 0, 0, 1)
    return data


def validation(data, rep, split):
    return [p for level in (1, 2, 3) for family in ('perfect', 'random')
            for p in data.group(split, rep, 0, level, family, 9 if level < 3 else 17).pairs]


def source_hashes():
    paths = [ROOT / 'cellular_maze_lab.py', ROOT / 'docs/FOUNDATION_CALIBRATION_V12A.md',
             ROOT / 'tests/test_foundation.py', *sorted((ROOT / 'maze_evolution').glob('*.py'))]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(out, seed=2026101812, generations=128, population=64, per_condition_seconds=60):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Choose a new calibration output directory')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'checkpoints').mkdir()
    started = time.perf_counter()
    sources = source_hashes()
    fixture_data = fixtures()
    with gzip.open(out / 'fixtures.json.gz', 'wt') as f:
        json.dump(manifest(fixture_data.cache.values()), f, separators=(',', ':'))
    previous = prior_manifests(ROOT) + manifest(fixture_data.cache.values())
    data = FoundationData(seed, previous)
    models = controls()
    write_json(out / 'controls.json', {k: v.save() for k, v in models.items()})
    warm_runtime()
    warm_baselines()
    warmed = time.perf_counter()
    matrix_pairs = [p for level in range(4) for family in ('perfect', 'random')
        for p in data.group('calibration_matrix', 0, 0, level, family, 9 if level < 3 else 17).pairs]
    matrix_pairs += list(data.disconnected_group('calibration_matrix', 0, 0).pairs)
    matrix_summary = {}
    probe_work = normal_work = normal_responses = probe_responses = 0
    with gzip.open(out / 'control_matrix.jsonl.gz', 'wt') as log:
        for name, item in models.items():
            for topology in ('local', 'evolved'):
                for pulse in (False, True):
                    ev = evaluate(item, matrix_pairs, topology, LIMITS, pulse)
                    normal_work += ev.work
                    normal_responses += len(ev.rows)
                    key = f'{name}/{topology}/pulse{int(pulse)}'
                    matrix_summary[key] = dict(fitness=ev.fitness, outputs=len(ev.rows),
                        optimal_or_no_path=sum(r['optimal'] or r['no_path'] for r in ev.rows),
                        partial_positive=sum(r['partial'] > 0 and not r['valid'] for r in ev.rows))
                    log.write(json.dumps(dict(kind='ordinary', key=key, cases=ev.rows)) + '\n')
                    organism = Organism(item.genome, topology, LIMITS, goal_pulse=pulse)
                    for pair in matrix_pairs:
                        for o in pair.cases:
                            m = o.maze
                            for horizon in (8, 16, 32, 64):
                                for forced in (False, True):
                                    obs = observe(organism, m.cells, m.w, m.h, m.start, m.goal, horizon, True, forced)
                                    mask = (obs.state[2] > 0).astype(np.uint8)
                                    diagnostic = Reaction(mask, 'emitted', obs.steps, obs.reads, obs.dispatches, obs.array_bytes)
                                    a = assess(diagnostic, o)
                                    probe_work += obs.reads + obs.dispatches
                                    probe_responses += 1
                                    row = dict(kind='probe', key=key, case=m.case_id, horizon=horizon, forced=forced,
                                        steps=obs.steps, status=obs.status, work=obs.reads + obs.dispatches,
                                        raster_only_valid=a.valid_path, old_partial=a.partial, partial=partial(mask, o),
                                        state_sha256=hashlib.sha256(obs.state.tobytes()).hexdigest(),
                                        mask=np.packbits(mask, bitorder='little').tobytes().hex())
                                    log.write(json.dumps(row, separators=(',', ':')) + '\n')
    matrix_seconds = time.perf_counter() - warmed
    # Data are shared across damage conditions, generated before repair, and never selected by candidate output.
    validations = {r: validation(data, r, 'repair_validation') for r in range(3)}
    batches = {}
    for rep in range(3):
        for g in range(generations):
            level = 1 + g % 3
            batches[rep, g] = [data.group('repair_train', rep, g, level, family,
                9 if level < 3 else 17).pairs[(g + rep) % 8] for family in ('perfect', 'random')]
    states = {}
    condition_times = {}
    for damage in DAMAGES:
        for rep in range(3):
            key = f'{damage}/r{rep}'
            config = dict(study='foundation_calibration', topology='local', origin=damage,
                method='evolution', replicate=rep, seed=seed, population=population,
                immigrants=0, limits=asdict(LIMITS), goal_pulse=True,
                validation_every=8, validation_nominees=4)
            t = time.perf_counter()
            with gzip.open(out / f'{damage}_{rep}.lineage.jsonl.gz', 'wt') as registry, \
                    gzip.open(out / f'{damage}_{rep}.evaluations.jsonl.gz', 'wt') as evaluations:
                search = Search(config, [models[damage].genome] * population, registry, evaluations,
                    out / 'checkpoints' / f'{damage}_{rep}.json', references=[models[damage].identity] * population)
                search.initialize(validations[rep])
                reason = 'generation_limit'
                for g in range(generations):
                    search.step(batches[rep, g], validations[rep])
                    if search.champion_rank[1] == 2 * len(validations[rep]):
                        reason = 'complete_validation_repair'
                        break
                    if time.perf_counter() - t >= per_condition_seconds:
                        reason = 'wall_limit'
                        break
                states[key] = search.state()
                condition_times[key] = dict(seconds=time.perf_counter() - t, reason=reason)
                print(f'{key}: g{search.next_generation}, validation {search.champion_rank[:2]}, {reason}', flush=True)
    write_json(out / 'frozen_selections.json', states)
    frozen = hashlib.sha256((out / 'frozen_selections.json').read_bytes()).hexdigest()
    # Freeze precedes construction of this independent confirmation corpus.
    tests = {r: validation(data, r, 'repair_test') for r in range(3)}
    results = {}
    holdout_work = holdout_responses = 0
    with gzip.open(out / 'holdout.jsonl.gz', 'wt') as log:
        for key, state in states.items():
            rep = state['config']['replicate']
            for role in ('champion', 'frozen'):
                ev = evaluate(Individual.load(state[role]), tests[rep], 'local', LIMITS)
                holdout_work += ev.work
                holdout_responses += len(ev.rows)
                results[f'{key}/{role}'] = dict(fitness=ev.fitness, outputs=len(ev.rows),
                    paired_optimal=sum(r['pair_optimal'] for r in ev.rows) // 2)
                log.write(json.dumps(dict(key=key, role=role, id=state[role]['id'], cases=ev.rows), separators=(',', ':')) + '\n')
        for rep, pairs in tests.items():
            for pair in pairs:
                for o in pair.cases:
                    m = o.maze
                    r = baseline('compiled_bfs', m.cells, m.w, m.h, m.start, m.goal)
                    a = assess(r, o)
                    if not a.optimal:
                        raise RuntimeError('Reference solver failed calibration holdout')
                    log.write(json.dumps(dict(key=f'baseline/r{rep}', case=m.case_id, optimal=a.optimal,
                        mask=np.packbits(r.mask, bitorder='little').tobytes().hex())) + '\n')
    data.save(out)
    successful = {}
    for damage in DAMAGES:
        passed = 0
        for rep in range(3):
            a, b = results[f'{damage}/r{rep}/champion'], results[f'{damage}/r{rep}/frozen']
            total = a['outputs']
            passed += (a['fitness'][1] >= .95 * total and a['paired_optimal'] >= .95 * total / 2
                       and a['fitness'][1] - b['fitness'][1] >= .25 * total)
        successful[damage] = passed
    control_pass = all(v['optimal_or_no_path'] == v['outputs'] for k, v in matrix_summary.items() if k.startswith('intact/'))
    report = dict(seed=seed, source_sha256=sources, frozen_sha256=frozen,
        input_sha256=prior_hashes(ROOT),
        parent_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        limits=asdict(LIMITS), population=population, max_generations=generations,
        per_condition_seconds=per_condition_seconds, controls=matrix_summary, confirmations=results,
        successful_replicates=successful, control_pass=control_pass,
        repair_gate=control_pass and sum(v >= 2 for v in successful.values()) >= 2,
        conditions=condition_times, normal_responses=normal_responses, probe_responses=probe_responses,
        matrix_normal_work=normal_work, matrix_probe_work=probe_work,
        repair_responses=sum(s['responses'] for s in states.values()),
        repair_work=sum(s['work'] for s in states.values()), holdout_responses=holdout_responses,
        holdout_work=holdout_work, excluded_layouts=data.previous_count,
        resulting_layouts=len(data.layouts), matrix_seconds=matrix_seconds,
        elapsed_seconds=time.perf_counter() - started, max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        platform=platform.platform(), processor=platform.machine(), python=platform.python_version(),
        packages={name: version(name) for name in ('numpy', 'numba', 'llvmlite', 'pytest')})
    write_json(out / 'summary.json', report)
    print(json.dumps({k: report[k] for k in ('control_pass', 'successful_replicates', 'repair_gate', 'elapsed_seconds')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=2026101812)
    args = parser.parse_args()
    run(args.out, args.seed)
