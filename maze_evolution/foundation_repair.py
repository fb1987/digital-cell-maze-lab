"""V12B isolated repair comparison after the negative V12A calibration."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import random
import resource
import subprocess
import time

import numpy as np
from .baselines import baseline, warm_baselines
from .datasets import seed_for
from .evaluator import assess
from .foundation_calibration import ROOT, LIMITS, DAMAGES, controls, validation, write_json
from .foundation_data import FoundationData, prior_manifests, prior_hashes
from .foundation_fitness import evaluate
from .foundation_repair_search import MutationSearch
from .growth import Individual
from .growth_runtime import warm_runtime


def run(out, seed=2026101814, generations=64, population=64):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Choose a fresh repair output directory')
    previous_dir = ROOT / 'results/foundation_calibration'
    proof = json.loads((previous_dir / 'verification.json').read_text())
    assert proof['all_checks_passed']
    assert hashlib.sha256((previous_dir / 'summary.json').read_bytes()).hexdigest() == proof['summary_sha256']
    extras = [previous_dir / 'mazes.json.gz', previous_dir / 'fixtures.json.gz']
    previous = prior_manifests(ROOT, extras)
    data = FoundationData(seed, previous)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'checkpoints').mkdir()
    started = time.perf_counter()
    source_files = [*sorted((ROOT / 'maze_evolution').glob('*.py')), ROOT / 'cellular_maze_lab.py',
                    ROOT / 'docs/FOUNDATION_REPAIR_V12B.md', ROOT / 'tests/test_foundation_repair.py']
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    inputs = {**prior_hashes(ROOT), **{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in [*extras, previous_dir / 'summary.json', previous_dir / 'verification.json']}}
    warm_runtime()
    warm_baselines()
    models = controls()
    write_json(out / 'controls.json', {k: v.save() for k, v in models.items()})
    validations = {r: validation(data, r, 'repair_validation') for r in range(3)}
    intact_validation_work = 0
    for pairs in validations.values():
        ev = evaluate(models['intact'], pairs, 'local', LIMITS)
        intact_validation_work += ev.work
        assert all(r['optimal'] for r in ev.rows)
    batches = {}
    for rep in range(3):
        for g in range(generations):
            level = 1 + g % 3
            family = 'perfect' if g % 2 == 0 else 'random'
            group = data.group('repair_train', rep, g, level, family, 9 if level < 3 else 17)
            start = 4 * (g % 2)
            batches[rep, g] = list(group.pairs[start:start + 4])
    states, timings = {}, {}
    for damage in DAMAGES:
        for rep in range(3):
            common_rng = random.Random(seed_for(seed, 'repair-paired-rng/' + damage, rep, 0)).getstate()
            for policy in ('wide', 'single'):
                key = f'{damage}/{policy}/r{rep}'
                slug = f'{damage}_{policy}_{rep}'
                config = dict(study='foundation_repair', topology='local', origin=f'{damage}/{policy}',
                    method='evolution', replicate=rep, seed=seed, population=population, immigrants=0,
                    limits=asdict(LIMITS), goal_pulse=True, validation_every=8, validation_nominees=4,
                    mutation_policy=policy)
                t = time.perf_counter()
                with gzip.open(out / f'{slug}.lineage.jsonl.gz', 'wt') as registry, \
                        gzip.open(out / f'{slug}.evaluations.jsonl.gz', 'wt') as log:
                    search = MutationSearch(config, [models[damage].genome] * population, registry, log,
                        out / 'checkpoints' / f'{slug}.json', references=[models[damage].identity] * population)
                    search.rng.setstate(common_rng)
                    search.initialize(validations[rep])
                    reason = 'generation_limit'
                    for g in range(generations):
                        search.step(batches[rep, g], validations[rep])
                        if search.champion_rank[1] == 2 * len(validations[rep]):
                            reason = 'complete_validation_repair'
                            break
                        if time.perf_counter() - t >= 60:
                            reason = 'wall_limit'
                            break
                    states[key] = search.state()
                timings[key] = dict(seconds=time.perf_counter() - t, reason=reason,
                    initial_rng_sha256=hashlib.sha256(json.dumps(common_rng).encode()).hexdigest())
                print(f'{key}: g{search.next_generation}, validation {search.champion_rank[:2]}, {reason}', flush=True)
    selection_ranks = {}
    for policy in ('wide', 'single'):
        chosen = [s for k, s in states.items() if f'/{policy}/' in k]
        selection_ranks[policy] = (sum(s['champion_rank'][1] == len(s['champion_rows']) for s in chosen),
            sum(s['champion_rank'][1] / len(s['champion_rows']) for s in chosen) / len(chosen), int(policy == 'single'))
    chosen_policy = max(selection_ranks, key=selection_ranks.get)
    frozen_packet = dict(states=states, selection_ranks=selection_ranks, chosen_policy=chosen_policy)
    write_json(out / 'frozen_selections.json', frozen_packet)
    frozen_sha = hashlib.sha256((out / 'frozen_selections.json').read_bytes()).hexdigest()
    tests = {r: validation(data, r, 'repair_test') for r in range(3)}
    confirmation = {}
    test_work = test_responses = 0
    with gzip.open(out / 'holdout.jsonl.gz', 'wt') as f:
        for key, state in states.items():
            rep = state['config']['replicate']
            for role in ('champion', 'frozen'):
                ev = evaluate(Individual.load(state[role]), tests[rep], 'local', LIMITS)
                confirmation[key + '/' + role] = dict(fitness=ev.fitness, outputs=len(ev.rows),
                    paired_optimal=sum(r['pair_optimal'] for r in ev.rows) // 2)
                test_work += ev.work
                test_responses += len(ev.rows)
                f.write(json.dumps(dict(key=key, role=role, id=state[role]['id'], cases=ev.rows), separators=(',', ':')) + '\n')
        for rep, pairs in tests.items():
            ev = evaluate(models['intact'], pairs, 'local', LIMITS)
            assert all(r['optimal'] for r in ev.rows)
            test_work += ev.work
            test_responses += len(ev.rows)
            f.write(json.dumps(dict(key=f'intact/r{rep}', role='reference', id=models['intact'].identity, cases=ev.rows), separators=(',', ':')) + '\n')
            for pair in pairs:
                for o in pair.cases:
                    m = o.maze
                    r = baseline('compiled_bfs', m.cells, m.w, m.h, m.start, m.goal)
                    assert assess(r, o).optimal
                    f.write(json.dumps(dict(key=f'bfs/r{rep}', case=m.case_id,
                        mask=np.packbits(r.mask, bitorder='little').tobytes().hex())) + '\n')
    success = {}
    for policy in ('wide', 'single'):
        success[policy] = {}
        for damage in DAMAGES:
            count = 0
            for rep in range(3):
                key = f'{damage}/{policy}/r{rep}'
                a, b = confirmation[key + '/champion'], confirmation[key + '/frozen']
                n = a['outputs']
                count += (a['fitness'][1] >= .95 * n and a['paired_optimal'] >= .95 * n / 2
                          and a['fitness'][1] - b['fitness'][1] >= .25 * n)
            success[policy][damage] = count
    data.save(out)
    summary = dict(seed=seed, source_sha256=sources, input_sha256=inputs, frozen_sha256=frozen_sha,
        chosen_policy=chosen_policy, validation_policy_ranks=selection_ranks, successful_replicates=success,
        repair_gate=sum(n >= 2 for n in success[chosen_policy].values()) >= 2,
        confirmations=confirmation, conditions=timings, population=population, max_generations=generations,
        per_condition_seconds=60, limits=asdict(LIMITS),
        repair_responses=sum(s['responses'] for s in states.values()), repair_work=sum(s['work'] for s in states.values()),
        intact_validation_responses=sum(2 * len(pairs) for pairs in validations.values()),
        intact_validation_work=intact_validation_work,
        holdout_responses=test_responses, holdout_work=test_work,
        excluded_layouts=data.previous_count, resulting_layouts=len(data.layouts),
        elapsed_seconds=time.perf_counter() - started, max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        parent_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        python=platform.python_version(), platform=platform.platform(),
        packages={name: version(name) for name in ('numpy', 'numba', 'llvmlite', 'pytest')})
    write_json(out / 'summary.json', summary)
    print(json.dumps({k: summary[k] for k in ('chosen_policy', 'successful_replicates', 'repair_gate', 'elapsed_seconds')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=2026101814)
    args = parser.parse_args()
    run(args.out, args.seed)
