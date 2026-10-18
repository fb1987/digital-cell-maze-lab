"""Range comparison and a larger random-origin continuation track, CPU only."""
import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import statistics
import subprocess
import time
from zoneinfo import ZoneInfo

import numpy as np

from .baselines import baseline, warm_baselines
from .datasets import make_case, manifest, seed_for
from .experiment import write_json, write_csv, category
from .regulatory import Genome
from .regulatory_runtime import Organism, warm_runtime
from .regulatory_search import search
from .runtime import Limits
from .evaluator import assess


class StudyData:
    def __init__(self, seed, previous=()):
        self.seed = seed
        self.cache, self.owners = {}, {value: 'previous' for value in previous}
        self.rejections = 0

    def case(self, split, replicate, index, n, family):
        key = (split, replicate, index, n, family)
        if key in self.cache:
            return self.cache[key]
        group = 'train' if split.startswith('train') else split
        for salt in range(1000):
            oracle = make_case(self.seed, split, replicate, index*1000 + salt, n, family)
            owner = self.owners.get(oracle.maze.digest)
            if owner is None or (owner == group == 'train'):
                self.cache[key] = oracle
                self.owners[oracle.maze.digest] = group
                return oracle
            self.rejections += 1
        raise RuntimeError('Cannot create an independent maze case')

    def batch(self, study, replicate, generation):
        if study == 'rich' and generation < 40:
            sizes = (5, 5, 9, 9)
        elif study == 'rich' and generation >= 80:
            sizes = (17, 17, 17, 17)
        else:
            sizes = (9, 9, 17, 17)
        return [self.case('train_' + study, replicate, generation*4+i, n,
                         'disconnected' if i == 3 and generation % 4 == 3
                         else 'perfect' if i % 2 == 0 else 'random')
                for i, n in enumerate(sizes)]

    def validation(self, replicate):
        specs = [(n, f) for n in (9, 17) for f in ('perfect', 'random') for _ in range(3)]
        specs += [(9, 'disconnected'), (17, 'disconnected')]
        return [self.case('validation', replicate, i, n, f) for i, (n, f) in enumerate(specs)]

    def tests(self, replicate, samples):
        # Deterministic snakes/combs from V1 are excluded from this fresh test.
        specs = [(n, f) for n in (9, 17, 33, 65) for f in ('perfect', 'random') for _ in range(samples)]
        specs += [(n, 'disconnected') for n in (9, 17, 33, 65) for _ in range(4)]
        specs += [(n, 'rectangular') for n in (9, 17) for _ in range(4)]
        return [self.case('test', replicate, i, n, f) for i, (n, f) in enumerate(specs)]


def calls_for(champions, replicate, eval_limits):
    calls = {}
    for key, saved in champions.items():
        config = saved['config']
        if config['replicate'] != replicate:
            continue
        label = '/'.join(str(config[k]) for k in ('study', 'topology', 'origin', 'method'))
        genome = Genome.from_dict(saved['champion']['genome'])
        calls[label] = Organism(genome, config['topology'], eval_limits).react
        if config['method'] == 'evolution':
            frozen = Genome.from_dict(saved['frozen']['genome'])
            calls[label.rsplit('/', 1)[0] + '/frozen'] = Organism(frozen, config['topology'], eval_limits).react
            if config['topology'] != 'local':
                calls[label + '/ablate'] = Organism(genome, config['topology'], eval_limits, True).react
            if config['study'] == 'control' and config['origin'] == 'seeded' and config['topology'] == 'local':
                calls['diagnostic/local_seed_old_budget'] = Organism(frozen, 'local', Limits()).react
    for name in ('compiled_bfs', 'compiled_astar', 'wave_bit'):
        calls[name] = lambda cells, w, h, start, goal, name=name: baseline(name, cells, w, h, start, goal)
    return calls


def output_row(arm, replicate, oracle, reaction, assessment):
    return dict(arm=arm, replicate=replicate, case_id=oracle.maze.case_id,
        family=oracle.maze.family, w=oracle.maze.w, h=oracle.maze.h,
        category=category(oracle.maze), edges=len(oracle.path)-1,
        **asdict(assessment), status=reaction.status, steps=reaction.steps,
        reads=reaction.spatial_reads, dispatches=reaction.instructions,
        active=getattr(reaction, 'active_instructions', -1),
        range_reads=list(getattr(reaction, 'range_reads', ())),
        array_bytes=reaction.array_bytes,
        mask=np.packbits(reaction.mask, bitorder='little').tobytes().hex())


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['arm'], 'all')].append(row)
        groups[(row['arm'], row['category'])].append(row)
    result = []
    for (arm, group), values in sorted(groups.items()):
        reachable = [r for r in values if r['reachable']]
        valid = [r for r in reachable if r['valid_path']]
        long = [r for r in reachable if r['edges'] >= 8]
        result.append(dict(arm=arm, group=group, reachable=len(reachable), valid=len(valid),
            optimal=sum(r['optimal'] for r in reachable),
            long_cases=len(long), long_optimal=sum(r['optimal'] for r in long),
            unreachable=len(values)-len(reachable), no_path=sum(r['no_path_correct'] for r in values),
            budget_failures=sum('budget' in r['status'] for r in values),
            nonlocal_reads=sum(sum(r['range_reads'][1:]) for r in values),
            all_reads=sum(max(0,r['reads']) for r in values),
            active=sum(max(0,r['active']) for r in values),
            dispatches=sum(max(0,r['dispatches']) for r in values),
            largest_array_bytes=max(r['array_bytes'] for r in values)))
    return result


def benchmark(calls, tests, repeats, rng, replicate):
    # One new perfect/random instance per dimension; same tasks for every solver.
    selected = {}
    for oracle in tests:
        if oracle.maze.family in ('perfect', 'random') and oracle.maze.w in (17, 33):
            selected.setdefault((oracle.maze.w, oracle.maze.family), oracle)
    rows = []
    # Ablations/budget diagnostics have separate correctness, not headline speed.
    calls = {name: call for name, call in calls.items() if not name.endswith('/ablate')
             and not name.startswith('diagnostic/')}
    for oracle in selected.values():
        m = oracle.maze
        measurements, correct = defaultdict(list), defaultdict(list)
        for call in calls.values():
            call(m.cells, m.w, m.h, m.start, m.goal)
        for _ in range(repeats):
            order = list(calls)
            rng.shuffle(order)
            for name in order:
                start = time.perf_counter_ns()
                r = calls[name](m.cells, m.w, m.h, m.start, m.goal)
                elapsed = time.perf_counter_ns() - start
                a = assess(r, oracle)
                measurements[name].append(elapsed)
                correct[name].append(bool(a.optimal))
        for name, values in measurements.items():
            rows.append(dict(arm=name, replicate=replicate, case_id=m.case_id, n=m.w,
                family=m.family, median_us=statistics.median(values)/1000,
                p95_us=float(np.percentile(values, 95))/1000,
                min_us=min(values)/1000, max_us=max(values)/1000,
                correct=sum(correct[name]), repeats=repeats,
                latency_ns=values, correctness=correct[name]))
    return rows


def render(out, champions, data, test_rows, limits):
    from PIL import Image, ImageDraw
    cases = [oracle for key, oracle in data.cache.items() if key[0] == 'test' and key[1] == 0]
    selected = next(o for o in cases if o.maze.w == 17 and o.maze.family == 'perfect')
    calls = calls_for(champions, 0, limits)
    arms = ['compiled_bfs', 'control/local/seeded/evolution',
            'control/fixed/seeded/evolution', 'control/evolved/seeded/evolution',
            'rich/local/random/evolution', 'rich/evolved/random/evolution']
    arms = [name for name in arms if name in calls]
    m = selected.maze
    tile, pw, ph = 9, 205, 218
    image = Image.new('RGB', (3*pw, 2*ph), '#111827')
    draw = ImageDraw.Draw(image)
    for k, arm in enumerate(arms):
        r = calls[arm](m.cells, m.w, m.h, m.start, m.goal)
        a = assess(r, selected)
        ox, oy = (k % 3)*pw+16, (k//3)*ph+56
        label = arm.replace('control/', '').replace('/evolution', '').replace('/random', '')
        draw.text((ox, oy-42), label, fill='#f9fafb')
        draw.text((ox, oy-24), 'shortest path' if a.optimal else a.failure, fill='#b8c4d6')
        for p, opened in enumerate(m.cells):
            color = '#172235' if not opened else '#5ae1bd' if r.mask[p] else '#45536a'
            if p == m.start:
                color = '#72b6ff'
            elif p == m.goal:
                color = '#ff6584'
            x, y = p%m.w, p//m.w
            draw.rectangle((ox+x*tile, oy+y*tile, ox+(x+1)*tile-1, oy+(y+1)*tile-1), fill=color)
    (out/'visuals').mkdir()
    image.save(out/'visuals'/'unseen_17.png')


def run(out, config):
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Choose a fresh output directory')
    out.mkdir(parents=True, exist_ok=True)
    (out/'checkpoints').mkdir()
    write_json(out/'config.json', config)
    root = Path(__file__).resolve().parents[1]
    sources = sorted((root/'maze_evolution').glob('*.py')) + sorted((root/'tests').glob('*.py'))
    source_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    previous_manifest = root/'results/first_evolution/mazes.json'
    previous = [row['sha256'] for row in json.loads(previous_manifest.read_text())]
    data = StudyData(config['seed'], previous)
    started = time.perf_counter()
    warm_runtime()
    warm_baselines()
    champions, history = {}, []
    with gzip.open(out/'genomes.jsonl.gz', 'wt', compresslevel=3) as registry, \
            gzip.open(out/'evaluations.jsonl.gz', 'wt', compresslevel=3) as evaluations:
        for study in ('control', 'rich'):
            for replicate in range(config['replicates']):
                validation = data.validation(replicate)
                settings = config[study]
                for topology in settings['topologies']:
                    for origin in settings['origins']:
                        for method in ('evolution', 'resample'):
                            condition = dict(seed=config['seed'], study=study, topology=topology,
                                origin=origin, method=method, replicate=replicate,
                                population=settings['population'], generations=settings['generations'],
                                rich=study=='rich', train_limits=config['train_limits'],
                                eval_limits=config['eval_limits'], search_version=2)
                            key = '/'.join(str(condition[k]) for k in ('study','topology','origin','method','replicate'))
                            checkpoint = out/'checkpoints'/(key.replace('/', '_')+'.json')
                            champions[key] = search(condition,
                                lambda g, study=study, rep=replicate: data.batch(study, rep, g),
                                validation, registry, evaluations, history, checkpoint)
    write_json(out/'champions.json', champions)
    freeze = hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    print(f'ALL CHAMPIONS FROZEN {freeze[:16]}; now generating fresh final tests.', flush=True)
    write_csv(out/'history.csv', history)
    rows, timings = [], []
    limits = Limits(**config['eval_limits'])
    for replicate in range(config['replicates']):
        tests = data.tests(replicate, config['samples'])
        calls = calls_for(champions, replicate, limits)
        for oracle in tests:
            m = oracle.maze
            for arm, call in calls.items():
                r = call(m.cells, m.w, m.h, m.start, m.goal)
                rows.append(output_row(arm, replicate, oracle, r, assess(r, oracle)))
        timings.extend(benchmark(calls, tests, config['benchmark_repeats'],
                                random.Random(seed_for(config['seed'], 'timing', replicate, 0)), replicate))
        print(f'Final evaluation/timing complete for replicate {replicate}.', flush=True)
    with gzip.open(out/'holdout.jsonl.gz','wt',compresslevel=3) as handle:
        for row in rows:
            handle.write(json.dumps(row,separators=(',',':'))+'\n')
    with gzip.open(out/'mazes.json.gz','wt',compresslevel=3) as handle:
        json.dump(manifest(data.cache.values()),handle,separators=(',',':'))
    write_json(out/'timings.json', timings)
    summaries = summarize(rows)
    write_json(out/'summary.json',summaries)
    write_csv(out.with_suffix('.csv'),summaries)
    tests = [o for key,o in data.cache.items() if key[0]=='test']
    environment = dict(recorded_at=datetime.now(ZoneInfo('America/Toronto')).isoformat(),
        elapsed_seconds=time.perf_counter()-started, source_sha256=source_hashes,
        parent_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=root).strip(),
        python=platform.python_version(), os=platform.platform(),
        cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip()
            if platform.system()=='Darwin' else platform.processor(),
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024),
        champions_sha256=freeze, fresh_tests=len(tests), unique_tests=len({o.maze.digest for o in tests}),
        prior_hash_rejections=data.rejections, previous_cases=len(previous),
        packages={name:__import__('importlib.metadata',fromlist=['version']).version(name)
                  for name in ('numpy','numba','llvmlite','pillow','pytest')})
    write_json(out/'environment.json',environment)
    render(out,champions,data,rows,limits)
    # A separate reader prepares the report from immutable raw results.
    from .range_report import report
    report(out)
    print(f'Study complete in {environment["elapsed_seconds"]:.1f}s: {out.with_suffix(".md")}',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='results/range_and_regulation')
    parser.add_argument('--seed',type=int,default=2026101751)
    parser.add_argument('--replicates',type=int,default=3)
    parser.add_argument('--control-population',type=int,default=24)
    parser.add_argument('--control-generations',type=int,default=30)
    parser.add_argument('--rich-population',type=int,default=96)
    parser.add_argument('--rich-generations',type=int,default=120)
    parser.add_argument('--samples',type=int,default=8)
    parser.add_argument('--benchmark-repeats',type=int,default=30)
    args=parser.parse_args()
    for name, maximum in [('replicates',5),('control_population',128),('control_generations',200),
                          ('rich_population',256),('rich_generations',1000),('samples',30),('benchmark_repeats',100)]:
        if not 1<=getattr(args,name)<=maximum:
            parser.error(f'{name} outside 1..{maximum}')
    if min(args.control_population,args.rich_population)<4:
        parser.error('Population must be at least four')
    config=dict(seed=args.seed,replicates=args.replicates,samples=args.samples,
        benchmark_repeats=args.benchmark_repeats,genome_version=2,
        control=dict(population=args.control_population,generations=args.control_generations,
                     topologies=['local','fixed','evolved'],origins=['random','seeded']),
        rich=dict(population=args.rich_population,generations=args.rich_generations,
                  topologies=['local','evolved'],origins=['random']),
        train_limits=asdict(Limits(max_steps=256,reads_per_site=4096,instructions_per_site=32768)),
        eval_limits=asdict(Limits(max_steps=1024,reads_per_site=8192,instructions_per_site=131072)),
        fitness='v2: validity/optimality/no-path/partial; cost tie-break only when all batch cases correct',
        curriculum='rich: g0-39 sizes5/9; g40-79 sizes9/17; g80+ size17; control always9/17',
        expression='64 registers, 8 uint16 channels, max128 genes/4096 bytes; gates charged dispatch',
        stopping='source channel7 request with endpoints, or four unchanged full-state ticks')
    run(args.out,config)


if __name__=='__main__':
    main()
