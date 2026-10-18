"""Run a small CPU experiment: python -m maze_evolution.experiment --help."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import statistics
import subprocess
import time
from importlib.metadata import version
from zoneinfo import ZoneInfo

import numpy as np

from .baselines import baseline, warm_baselines
from .datasets import (check_split_overlap, final_test_set, manifest, seed_for,
                       training_batches, validation_set)
from .evaluator import assess, score
from .genome import Genome, mutate, random_genome, wavefront_genome, Op
from .runtime import Limits, Organism, warm_runtime


@dataclass
class Individual:
    identity: str
    parent: str | None
    birth: int
    genome: Genome
    organism: Organism


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def write_csv(path, rows):
    import csv
    if not rows:
        return
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def evolve(regime, replicate, batches, validation, config, logs):
    rng = random.Random(seed_for(config['seed'], 'mutation', replicate, 0))
    population_size = config['population']
    limits = Limits(**config['limits'])
    registry, evaluations, history = logs
    serial = 0

    def individual(genome, parent, birth, edits):
        nonlocal serial
        identity = f'{regime}/r{replicate}/i{serial}'
        serial += 1
        item = Individual(identity, parent, birth, genome, Organism(genome, limits))
        registry.write(json.dumps(dict(id=identity, parent=parent, generation=birth,
                                       requested_edits=edits, digest=genome.digest,
                                       **genome.to_dict())) + '\n')
        return item

    population = []
    for i in range(population_size):
        if regime == 'random':
            genome, edits = random_genome(rng), 0
        else:
            edits = 0 if i == 0 else rng.randint(1, 3)
            genome = mutate(wavefront_genome(), rng, edits)
        population.append(individual(genome, None, 0, edits))
    initial = [(score(item.organism, validation)[0], item) for item in population]
    frozen_fitness, frozen = max(initial, key=lambda pair: pair[0])
    champion, champion_fitness = frozen, frozen_fitness
    initial_hashes = [item.genome.digest for item in population]
    for generation, batch in enumerate(batches):
        ranked = []
        for item in population:
            fitness, _, reactions = score(item.organism, batch)
            ranked.append((fitness, item))
            evaluations.write(json.dumps(dict(regime=regime, replicate=replicate,
                generation=generation, individual=item.identity, digest=item.genome.digest,
                fitness=fitness, cases=[o.maze.case_id for o in batch],
                steps=[r.steps for r in reactions], statuses=[r.status for r in reactions])) + '\n')
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        validation_fitness = score(ranked[0][1].organism, validation)[0]
        if validation_fitness > champion_fitness:
            champion, champion_fitness = ranked[0][1], validation_fitness
        history.append(dict(regime=regime, replicate=replicate, generation=generation,
            unique_genomes=len({i.genome.digest for i in population}),
            train_valid=ranked[0][0][0], train_optimal=ranked[0][0][1],
            train_partial=ranked[0][0][3], train_work=-ranked[0][0][4],
            mean_train_valid=statistics.mean(pair[0][0] for pair in ranked),
            champion_valid=champion_fitness[0], champion_optimal=champion_fitness[1],
            champion_no_path_utility=champion_fitness[2], champion_partial=champion_fitness[3],
            champion_work=-champion_fitness[4], champion_id=champion.identity,
            champion_digest=champion.genome.digest))
        if generation % 5 == 0 or generation == len(batches) - 1:
            print(f'{regime} r{replicate} generation {generation:02}: '
                  f'validation paths {champion_fitness[0]}/12, '
                  f'partial {champion_fitness[3]:.3f}, genes {len(champion.genome.genes)}', flush=True)
        if generation + 1 < len(batches):
            elite_count = max(1, population_size // 8)
            population = [item for _, item in ranked[:elite_count]]
            pool = ranked[:max(2, population_size // 2)]
            while len(population) < population_size:
                _, parent = max(rng.choices(pool, k=3), key=lambda pair: pair[0])
                edits = rng.randint(1, 3)
                child = mutate(parent.genome, rng, edits)
                population.append(individual(child, parent.identity, generation + 1, edits))
    return {
        'evolved': dict(individual=champion.identity, digest=champion.genome.digest,
                        genome=champion.genome.to_dict(), validation_fitness=champion_fitness,
                        initial_digests=initial_hashes),
        'frozen': dict(individual=frozen.identity, digest=frozen.genome.digest,
                       genome=frozen.genome.to_dict(), validation_fitness=frozen_fitness),
    }


def category(maze):
    if maze.family == 'disconnected':
        return 'no_path'
    if maze.family in ('snake', 'comb', 'rectangular'):
        return 'structure_shift'
    return 'larger' if maze.w > 17 else 'same_size'


def evaluate_call(call, oracle):
    maze = oracle.maze
    start_ns = time.perf_counter_ns()
    reaction = call(maze.cells, maze.w, maze.h, maze.start, maze.goal)
    elapsed = time.perf_counter_ns() - start_ns
    return reaction, assess(reaction, oracle), elapsed


def solver_calls(champions, replicate, limits):
    calls = {}
    for regime in ('random', 'seeded'):
        for treatment in ('evolved', 'frozen'):
            saved = champions[f'{regime}/r{replicate}'][treatment]
            organism = Organism(Genome.from_dict(saved['genome']), limits)
            calls[f'{regime}_{treatment}'] = organism.react
    for name in ('compiled_bfs', 'compiled_astar', 'wave_bit'):
        calls[name] = lambda cells, w, h, start, goal, name=name: baseline(name, cells, w, h, start, goal)
    return calls


def benchmark(calls, oracles, repeats, rng):
    selected = {}
    for oracle in oracles:
        if oracle.maze.family in ('perfect', 'random'):
            selected.setdefault((oracle.maze.w, oracle.maze.family), oracle)
    rows, raw = [], []
    for oracle in selected.values():
        timings = defaultdict(list)
        correctness = defaultdict(list)
        for call in calls.values():
            evaluate_call(call, oracle)  # Warm production shape and representation.
        for _ in range(repeats):
            names = list(calls)
            rng.shuffle(names)
            for name in names:
                _, assessed, elapsed = evaluate_call(calls[name], oracle)
                timings[name].append(elapsed)
                correctness[name].append(assessed.optimal or assessed.no_path_correct)
        for name, values in timings.items():
            row = dict(arm=name, case_id=oracle.maze.case_id, side=oracle.maze.w,
                       family=oracle.maze.family, repeats=repeats,
                       correct_repetitions=sum(correctness[name]),
                       median_us=statistics.median(values) / 1000,
                       p95_us=float(np.percentile(values, 95)) / 1000,
                       min_us=min(values) / 1000, max_us=max(values) / 1000)
            rows.append(row)
            raw.append(dict(**row, latency_ns=values, correctness=correctness[name]))
    return rows, raw


def summary(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['arm'], row['category'])].append(row)
        grouped[(row['arm'], 'all')].append(row)
    result = []
    for (arm, group), values in sorted(grouped.items()):
        reachable = [r for r in values if r['reachable']]
        no_path = [r for r in values if not r['reachable']]
        result.append(dict(arm=arm, category=group, cases=len(values),
            reachable=len(reachable), valid=sum(r['valid_path'] for r in reachable),
            optimal=sum(r['optimal'] for r in reachable),
            unreachable=len(no_path), no_path_correct=sum(r['no_path_correct'] for r in no_path),
            budget_failures=sum('budget' in r['status'] for r in values),
            median_steps=float(statistics.median(r['steps'] for r in values)),
            max_array_bytes=max(r['array_bytes'] for r in values),
            failures=dict(Counter(r['failure'] for r in values if r['failure']))))
    return result


def render_samples(out, champions, cases_by_replicate, config):
    from PIL import Image, ImageDraw
    directory = out / 'visuals'
    directory.mkdir()
    cases = cases_by_replicate[0]
    selected = [next(o for o in cases if o.maze.family == family and o.maze.w == n)
                for n, family in ((17, 'perfect'), (33, 'random'), (65, 'perfect'))]
    images = []
    calls = solver_calls(champions, 0, Limits(**config['limits']))
    for oracle in selected:
        maze = oracle.maze
        tile = max(3, min(10, 260 // maze.w))
        panel_w, panel_h = maze.w * tile + 28, maze.h * tile + 70
        picture = Image.new('RGB', (3 * panel_w, 2 * panel_h), '#111827')
        draw = ImageDraw.Draw(picture)
        panels = [('Input', None), ('BFS oracle', 'compiled_bfs'),
                  ('Random evolved', 'random_evolved'), ('Random frozen', 'random_frozen'),
                  ('Seeded evolved', 'seeded_evolved'), ('Seeded frozen', 'seeded_frozen')]
        for k, (title, name) in enumerate(panels):
            ox, oy = (k % 3) * panel_w + 14, (k // 3) * panel_h + 58
            if name:
                reaction, assessed, _ = evaluate_call(calls[name], oracle)
                mask = reaction.mask
                detail = 'shortest path' if assessed.optimal else assessed.failure
                steps = '' if reaction.steps < 0 else f'; {reaction.steps} ticks'
                detail += steps
            else:
                mask = np.zeros(len(maze.cells))
                detail = f'{maze.family}, {maze.w}x{maze.h}'
            draw.text((ox, oy - 44), title, fill='#f9fafb')
            draw.text((ox, oy - 26), detail, fill='#b8c4d6')
            for p, opened in enumerate(maze.cells):
                x, y = p % maze.w, p // maze.w
                color = '#172235' if not opened else ('#5ae1bd' if mask[p] else '#45536a')
                if p == maze.start:
                    color = '#72b6ff'
                elif p == maze.goal:
                    color = '#ff6584'
                draw.rectangle((ox + x*tile, oy + y*tile,
                                ox + (x+1)*tile - 1, oy + (y+1)*tile - 1), fill=color)
        filename = f'{maze.family}_{maze.w}.png'
        picture.save(directory / filename)
        images.append(f'{out.name}/visuals/{filename}')
    return images


def report(out, config, champions, summaries, history, benchmarks, environment, images):
    by_arm = {row['arm']: row for row in summaries if row['category'] == 'all'}
    lines = ['# First local-rule evolution experiment', '',
        'This CPU pilot compares two initialization regimes and their frozen initial champions. '
        'It tests local rules only; multi-distance signalling is not implemented yet.', '',
        f"Run: {environment['recorded_at']}; {environment['cpu']}; Python {environment['python']}. "
        f"{config['replicates']} independent evolutionary seeds, {config['population']} organisms, "
        f"{config['generations']} generations, four rotating training mazes per generation.", '',
        '## Unseen results', '',
        '| Arm | Legal routes / reachable | Shortest / reachable | Correct no-path | Budget failures |',
        '| --- | ---: | ---: | ---: | ---: |']
    for arm in ('random_evolved', 'random_frozen', 'seeded_evolved', 'seeded_frozen',
                'compiled_bfs', 'compiled_astar', 'wave_bit'):
        r = by_arm[arm]
        lines.append(f"| {arm} | {r['valid']}/{r['reachable']} | {r['optimal']}/{r['reachable']} | "
                     f"{r['no_path_correct']}/{r['unreachable']} | {r['budget_failures']} |")
    lines += ['', 'Same-size tests use new 9x9/17x17 perfect and cyclic random mazes with '
              'new endpoints. Larger tests use 33x33/65x65. Structural shifts include '
              'snake/comb and rectangular grids. Disconnected cases are counted separately. '
              'No-path accuracy is not substituted for reachable-maze solving.', '',
              '| Arm / category | Shortest / reachable | No-path correct |',
              '| --- | ---: | ---: |']
    for r in summaries:
        if r['arm'] in ('random_evolved', 'random_frozen', 'seeded_evolved', 'seeded_frozen') and r['category'] != 'all':
            lines.append(f"| {r['arm']} / {r['category']} | {r['optimal']}/{r['reachable']} | "
                         f"{r['no_path_correct']}/{r['unreachable']} |")
    lines += ['', '## What changed during evolution', '',
              '| Regime / replicate | Initial → final genes | Validation work change | New genotype? |',
              '| --- | ---: | ---: | --- |']
    for key, arms in champions.items():
        old, new = arms['frozen'], arms['evolved']
        old_work, new_work = -old['validation_fitness'][4], -new['validation_fitness'][4]
        improvement = (old_work - new_work) / max(1, old_work) * 100
        new_genotype = new['digest'] not in new['initial_digests']
        lines.append(f"| {key} | {len(old['genome']['genes'])} → {len(new['genome']['genes'])} | "
                     f"{improvement:.1f}% fewer instruction+read units | {new_genotype} |")
    random_solves = by_arm['random_evolved']['valid']
    lines += ['', f'Random initialization produced {random_solves} legal held-out routes. '
              'A useful partial phenotype or shorter genome is not evidence of a general solver. '
              'The seeded regime starts with a hand-designed shortest-path algorithm; its '
              'success is not discovery from scratch. Changes to it must be interpreted as '
              'program optimization or altered behaviour, not invention of wavefront search.', '',
              '## Timing, work and memory', '',
              '| Arm | Median of successful 17x17 instance medians (µs) | Successful timed instances |',
              '| --- | ---: | ---: |']
    for arm in by_arm:
        values = [r['median_us'] for r in benchmarks if r['arm'] == arm and r['side'] == 17
                  and r['correct_repetitions'] == r['repeats']]
        lines.append(f"| {arm} | {statistics.median(values):.2f} | {len(values)} |" if values
                     else f'| {arm} | n/a | 0 |')
    lines += ['', f"Each selected instance uses {config['benchmark_repeats']} warm repetitions, "
              'with randomized solver order. Times include raw-byte input handling, reaction/search, '
              'termination and binary-raster emission. JIT, maze generation, oracle/validation, '
              'rendering and one-time per-genome program encoding are excluded. Individual '
              'medians/p95/min/max and all samples are saved. Failed outputs never count as '
              'fast solutions. These are implementation comparisons, not state-of-the-art claims.', '',
              'Candidate work is deterministic site-instruction evaluations plus attempted spatial '
              'channel reads. MIN/ARGMIN charge four reads, neighbour/match one. Every executed '
              'gene is charged at every open site; full-grid scans and register resets additionally '
              'cost time and are not included in this proxy. Counts are not CPU instructions or energy.', '',
              f"Limits: {config['limits']}. All arms share them. A read cap can bind before the "
              'tick cap, especially on long corridors. Budget-exhausted empty output is never '
              'labelled a correct no-path answer. A quiescent empty raster predicts no path and '
              'is scored against the oracle; quiescence is not a proof for arbitrary programs.', '']
    for arm in ('random_evolved', 'seeded_evolved'):
        r = by_arm[arm]
        lines.append(f"- {arm}: largest accounted array payload {r['max_array_bytes']:,} bytes; "
                     f"failure counts {r['failures']}.")
    lines += ['', 'Memory accounting includes double-buffered four-channel uint16 state, uint8 '
              'input/output, int32 genome and scratch registers, plus a conservative input-check '
              'temporary. It excludes Python/Numba object/allocator overhead and the external '
              'evaluator/datasets. BFS is a conservative array bound; A* counts logical heap '
              'payload without spare capacity; bit-wave history is not instrumented. These '
              'are not fully comparable measured process peaks. Whole-run maximum RSS, including '
              f"JIT and evaluator, was {environment['max_rss_bytes'] / 2**20:.1f} MiB.", '',
              '## Experimental contract and reproducibility', '',
              'The genome has 1–32 typed instructions (14 operations) and four uint16 state '
              'channels. Output is channel 2 > 0. Scratch registers are local to one site. '
              'Spatial reads see only the previous tick; walls hold zero. Start stimulus '
              'initializes channel 0 to 1 once for every genotype. Seed channels encode '
              'first-arrival distance and one parent direction, then trace from goal to source '
              'using neighbour matches. These hidden values are computed locally by the genome; '
              'the independent evaluator supplies neither distances nor routes to inference.', '',
              f"Initialization: {config['population']} random typed programs versus one exact 29-gene seed and "
              f"{config['population'] - 1} independently perturbed seeds (1–3 edits). The initial champion of each "
              'population is selected on validation and frozen. Evolution ranks each batch '
              'lexicographically by legal paths, shortest paths, no-path utility (correct '
              'no-path predictions minus false no-path claims on reachable mazes), '
              'bounded partial connectivity score, then lower instruction+read work. Latency '
              'does not drive selection. The top 1/8 survive; three-way tournaments from the '
              'top half produce mutation-only offspring with 1–3 requested edits. Edits may '
              'be neutral. No crossover or arbitrary generated-code execution is used.', '',
              'Partial score for invalid outputs is clipped to [0, 0.99]: '
              '(0.1 for containing source + 0.8 × graph-distance progress of its lit component '
              'toward goal) / (1 + 2 × total excess degree above 2) − 0.2 × isolated-lit fraction. '
              'Wall leaks get zero. '
              'Legal paths receive zero shaping; their higher primary rank always dominates. '
              'This deliberately allows evaluator-derived graph distance for training feedback '
              'only. Empty masks get no reachable-maze credit.', '',
              'Rotating training namespaces are paired between regimes. Validation selects '
              'the initial champion and archives the best of each generation’s training '
              'champions. All champions are saved before generating the final test mazes. '
              'SHA256 input+endpoint identities are checked for cross-split overlap. Final '
              'tests never influence selection. Frozen controls receive less search compute '
              'than evolution; this is an improvement-over-initialization ablation, not a '
              'matched-budget comparison with random search.', '',
              'Raw files: config/environment, all newly created genomes and parent IDs, every '
              'training fitness, generation history, maze manifests with exact input bytes, '
              'frozen champions, every holdout output bitmask, and benchmark samples. Source '
              'hashes identify uncommitted code independently of the parent Git revision.', '',
              '```bash',
              f".venv/bin/python -m maze_evolution.experiment --out results/repeat_evolution "
              f"--seed {config['seed']} --replicates {config['replicates']} "
              f"--population {config['population']} --generations {config['generations']} "
              f"--samples {config['samples']} --benchmark-repeats {config['benchmark_repeats']}",
              '```', '', '## Visual samples', '',
              'Samples are the first test cases at 17x17 perfect, 33x33 random and 65x65 '
              'perfect in replicate 0, not chosen by success. Blue = source; red = goal; '
              'green = emitted pixels, including invalid partial outputs.', '']
    for image in images:
        lines += [f'![Unseen responses]({image})', '']
    lines += ['## Next experiment', '',
              'Hold this local runtime as a control, then add fixed and evolvable radii '
              '1/2/4/8 under the same work accounting. First run a frozen-genome budget '
              'sweep on a separate diagnostic set to distinguish propagation limits from '
              'rule errors. Add matched-budget random search before attributing an advantage '
              'specifically to evolutionary selection. Expand training seeds and optimized '
              'conventional baselines before making any competitive claim.', '']
    out.with_suffix('.md').write_text('\n'.join(lines))


def run(config, out):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Choose a fresh output directory to preserve prior experiments')
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'config.json', config)
    t0 = time.perf_counter()
    warm_runtime()
    warm_baselines()
    setup_seconds = time.perf_counter() - t0
    print(f'JIT warm-up complete ({setup_seconds:.2f}s). Test mazes remain ungenerated.', flush=True)
    history, champions, datasets = [], {}, {}
    with (out / 'genomes.jsonl').open('w') as registry, (out / 'training.jsonl').open('w') as evaluations:
        for replicate in range(config['replicates']):
            batches = training_batches(config['seed'], replicate, config['generations'])
            validation = validation_set(config['seed'], replicate)
            datasets[replicate] = (batches, validation)
            check_split_overlap({'train': [o for b in batches for o in b], 'validation': validation})
            for regime in ('random', 'seeded'):
                champions[f'{regime}/r{replicate}'] = evolve(regime, replicate, batches, validation,
                    config, (registry, evaluations, history))
    write_json(out / 'champions.json', champions)
    frozen_hash = hashlib.sha256((out / 'champions.json').read_bytes()).hexdigest()
    print(f'Champions frozen ({frozen_hash[:12]}). Generating final unseen test mazes.', flush=True)
    write_csv(out / 'history.csv', history)
    all_manifests, rows, benchmark_rows, benchmark_raw, cases_by_replicate = [], [], [], [], {}
    for replicate, (batches, validation) in datasets.items():
        tests = final_test_set(config['seed'], replicate, config['samples'])
        cases_by_replicate[replicate] = tests
        train = [o for batch in batches for o in batch]
        check_split_overlap({'train': train, 'validation': validation, 'test': tests})
        all_manifests.extend(manifest(train + validation + tests))
        calls = solver_calls(champions, replicate, Limits(**config['limits']))
        for oracle in tests:
            for arm, call in calls.items():
                reaction, assessment, elapsed = evaluate_call(call, oracle)
                rows.append(dict(arm=arm, replicate=replicate, case_id=oracle.maze.case_id,
                    family=oracle.maze.family, w=oracle.maze.w, h=oracle.maze.h,
                    category=category(oracle.maze), **asdict(assessment),
                    status=reaction.status, steps=reaction.steps,
                    instructions=reaction.instructions, spatial_reads=reaction.spatial_reads,
                    array_bytes=reaction.array_bytes, single_inference_ns=elapsed,
                    mask_packbits_hex=np.packbits(reaction.mask, bitorder='little').tobytes().hex()))
        br, raw = benchmark(calls, tests, config['benchmark_repeats'],
                            random.Random(seed_for(config['seed'], 'benchmark', replicate, 0)))
        benchmark_rows.extend(dict(replicate=replicate, **row) for row in br)
        benchmark_raw.extend(dict(replicate=replicate, **row) for row in raw)
    # Also audit overlap across evolutionary replicates, not just within each run.
    all_groups = defaultdict(list)
    for replicate, (batches, validation) in datasets.items():
        all_groups['train'].extend(o for batch in batches for o in batch)
        all_groups['validation'].extend(validation)
        all_groups['test'].extend(cases_by_replicate[replicate])
    check_split_overlap(all_groups)
    write_json(out / 'mazes.json', all_manifests)
    write_csv(out / 'holdout.csv', rows)
    write_csv(out / 'benchmark.csv', benchmark_rows)
    write_json(out / 'benchmark_raw.json', benchmark_raw)
    summaries = summary(rows)
    write_json(out / 'summary.json', summaries)
    write_csv(out.with_suffix('.csv'), [{**row, 'failures': json.dumps(row['failures'])} for row in summaries])
    images = render_samples(out, champions, cases_by_replicate, config)
    root = Path(__file__).resolve().parents[1]
    sources = (sorted((root / 'maze_evolution').glob('*.py'))
               + sorted((root / 'tests').glob('*.py')) + [root / 'cellular_maze_lab.py'])
    environment = dict(recorded_at=datetime.now(ZoneInfo('America/Toronto')).isoformat(),
        cpu=subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
            if platform.system() == 'Darwin' else platform.processor(),
        os=platform.platform(), python=platform.python_version(),
        packages={name: version(name) for name in ('numpy', 'numba', 'llvmlite', 'pillow', 'pytest')},
        parent_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        source_sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == 'Darwin' else 1024),
        jit_setup_seconds=setup_seconds, elapsed_seconds=time.perf_counter() - t0,
        frozen_champions_sha256=frozen_hash, split_overlap='none',
        operations={op.name: int(op) for op in Op})
    write_json(out / 'environment.json', environment)
    report(out, config, champions, summaries, history, benchmark_rows, environment, images)
    print(f"Finished in {environment['elapsed_seconds']:.1f}s; report: {out.with_suffix('.md')}", flush=True)
    return champions, history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='results/first_evolution')
    parser.add_argument('--seed', type=int, default=1729)
    parser.add_argument('--replicates', type=int, default=3)
    parser.add_argument('--population', type=int, default=32)
    parser.add_argument('--generations', type=int, default=25)
    parser.add_argument('--samples', type=int, default=8)
    parser.add_argument('--benchmark-repeats', type=int, default=30)
    args = parser.parse_args()
    for name, maximum in (('replicates', 10), ('population', 128), ('generations', 200),
                          ('samples', 100), ('benchmark_repeats', 200)):
        if not 1 <= getattr(args, name) <= maximum:
            parser.error(f'{name} must be within 1..{maximum}')
    if args.population < 4:
        parser.error('population must be at least 4')
    config = dict(seed=args.seed, replicates=args.replicates, population=args.population,
                  generations=args.generations, samples=args.samples,
                  benchmark_repeats=args.benchmark_repeats, batch_size=4,
                  limits=asdict(Limits()), topology='local_radius_1', genome_schema=1,
                  fitness_version='lexicographic-v1-branch-penalty-2')
    run(config, args.out)


if __name__ == '__main__':
    main()
