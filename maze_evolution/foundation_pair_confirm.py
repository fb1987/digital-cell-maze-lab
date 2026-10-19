"""Fresh confirmation of already frozen V12E selections; no training or reselection."""
import argparse
from collections import defaultdict
from dataclasses import asdict, replace
import gzip
import hashlib
import json
from pathlib import Path
import random
import resource
import statistics
import time

import numpy as np
from .baselines import baseline, warm_baselines
from .datasets import make_case, seed_for, manifest
from .evaluator import Maze, Oracle, assess, distances
from .foundation_calibration import ROOT, LIMITS, controls, write_json
from .foundation_data import FoundationData, layout_hash, load_pairs
from .foundation_fitness import evaluate, partial
from .foundation_study import read_compressed
from .foundation_pair_data import SEED, exclusions, ConfirmationData, FIXTURES
from .goal_data import GoalPair
from .goal_recovery import wilson_case
from .growth import Individual
from .growth_runtime import Organism, warm_runtime
from .runtime import Limits


GENERAL_LIMITS = Limits(max_steps=1024, reads_per_site=8192, instructions_per_site=131072)
BASELINES = ('compiled_bfs', 'compiled_astar', 'wave_bit')


def rectangular_transform(m, symmetry):
    if symmetry not in range(8):
        raise ValueError('Expected square/rectangle dihedral symmetry')
    def coordinate(p):
        y, x = divmod(p, m.w)
        w, h = m.w, m.h
        if symmetry >= 4:
            x = w - 1 - x
        for _ in range(symmetry % 4):
            x, y, w, h = h - 1 - y, x, h, w
        return y * w + x, w, h
    cells = bytearray(len(m.cells))
    for p, value in enumerate(m.cells):
        q, w, h = coordinate(p)
        cells[q] = value
    return replace(m, cells=bytes(cells), w=w, h=h, start=coordinate(m.start)[0],
                   goal=coordinate(m.goal)[0], case_id=m.case_id + f'/d4-{symmetry}')


def general_cases(data, rep):
    specs = [(n, family) for n in (9, 17, 33, 65) for family in ('perfect', 'random') for _ in range(8)]
    specs += [(n, 'disconnected') for n in (9, 17, 33, 65) for _ in range(4)]
    specs += [(n, 'rectangular') for n in (9, 17) for _ in range(4)]
    primary, all_orbits = [], []
    for index, (n, family) in enumerate(specs):
        for salt in range(4000):
            serial = index * 10000 + salt
            base = (wilson_case(SEED, 'pair_general_confirmation', rep, serial) if n == 9 and family == 'perfect'
                    else make_case(SEED, 'pair_general_confirmation', rep, serial, n, family))
            m = replace(base.maze, case_id=f'general/r{rep}/c{index}/{family}/{n}/s{salt}', split='pair_general_confirmation')
            orbit = [rectangular_transform(m, s) for s in range(8)]
            hashes = {layout_hash(o) for o in orbit}
            if hashes & data.layouts:
                continue
            data.layouts.update(hashes)
            oracles = [Oracle.build(o) for o in orbit]
            for o in oracles:
                o._from_start = distances(o.maze, o.maze.start)
            primary.append(oracles[0])
            all_orbits.extend(oracles)
            break
        else:
            raise RuntimeError('No unseen ordinary generalization layout')
    return primary, all_orbits


def normal_row(result, oracle):
    a = assess(result, oracle)
    return dict(case=oracle.maze.case_id, status=result.status, steps=result.steps, valid=a.valid_path,
        optimal=a.optimal, no_path=a.no_path_correct, reachable=a.reachable, failure=a.failure,
        partial=partial(result.mask, oracle), reads=result.spatial_reads,
        range_reads=getattr(result, 'range_reads', ()), dispatches=getattr(result, 'dispatches', result.instructions),
        active=getattr(result, 'active_instructions', -1), array_bytes=result.array_bytes,
        mask=np.packbits(result.mask, bitorder='little').tobytes().hex())


def statistics_for(rows):
    return dict(outputs=len(rows), reachable=sum(r['reachable'] for r in rows),
        valid=sum(r['valid'] for r in rows), optimal=sum(r['optimal'] for r in rows),
        no_path=sum(r['no_path'] for r in rows),
        paired_optimal=sum(r.get('pair_optimal', False) for r in rows) // 2,
        budget_failures=sum('budget' in r['status'] for r in rows),
        work=sum(max(0, r['dispatches']) + max(0, r['reads']) for r in rows))


def run(out):
    out = Path(out)
    summary = json.loads((out / 'search_summary.json').read_text())
    freeze = out / 'frozen_selections.json.gz'
    assert hashlib.sha256(freeze.read_bytes()).hexdigest() == summary['frozen_sha256']
    for path, sha in {**summary['source_sha256'], **summary['input_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
    target = out / 'confirmation'
    if target.exists():
        raise FileExistsError('Confirmation is immutable; choose a separately labelled diagnostic')
    started = time.perf_counter()
    frozen = read_compressed(freeze)
    checkpoint_path = out / 'checkpoint_selections.json.gz'
    assert hashlib.sha256(checkpoint_path.read_bytes()).hexdigest() == summary['checkpoint_selections_sha256']
    checkpoint_controls = read_compressed(checkpoint_path)
    timecourse_freeze = json.loads((out / 'timecourse/freeze.json').read_text())
    assert hashlib.sha256((out / 'timecourse/selections.json.gz').read_bytes()).hexdigest() == timecourse_freeze['selection_sha256']
    assert hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest() == timecourse_freeze['search_summary_sha256']
    assert hashlib.sha256((ROOT / 'maze_evolution/foundation_pair_timecourse.py').read_bytes()).hexdigest() == timecourse_freeze['source_sha256']
    target.mkdir()
    with gzip.open(out / 'mazes.json.gz', 'rt') as f:
        previous = exclusions() + json.load(f)
    software_fixtures = FIXTURES / 'mazes.json.gz'
    with gzip.open(software_fixtures, 'rt') as f:
        previous.extend(json.load(f))
    data = ConfirmationData(SEED, previous)
    micro = {}
    for rep in range(3):
        for level in range(5):
            micro[rep, level] = [p for family in ('perfect', 'random') for index in range(3)
                for p in data.group('pair_confirmation', rep, index, level, family, 17 if level == 4 else 9).pairs]
    general, general_orbits = {}, []
    for rep in range(3):
        general[rep], orbit = general_cases(data, rep)
        general_orbits.extend(orbit)
    data.save(target)
    with gzip.open(target / 'general_mazes.json.gz', 'wt') as f:
        json.dump(manifest(general_orbits), f, separators=(',', ':'))
    write_json(target / 'general_primary.json', {str(r): [o.maze.case_id for o in os] for r, os in general.items()})
    cases = {**data.cache, **{o.maze.case_id: o for o in general_orbits}}
    warm_runtime()
    warm_baselines()
    cached, models, result_stats, micro_success, general_success = {}, {}, {}, defaultdict(dict), defaultdict(dict)
    actual_responses = actual_work = aliases = 0
    model_setup_seconds = 0.

    def model(item, topology, limits):
        nonlocal model_setup_seconds
        key = (item.genome.digest, topology, tuple(asdict(limits).values()))
        if key not in models:
            t = time.perf_counter()
            models[key] = Organism(item.genome, topology, limits, goal_pulse=True)
            model_setup_seconds += time.perf_counter() - t
        return key, models[key]

    with gzip.open(target / 'outputs.jsonl.gz', 'wt', compresslevel=1) as log:
        def emit(key, role, item, topology, rep, level=None, ordinary=False):
            nonlocal actual_responses, actual_work, aliases
            limits = GENERAL_LIMITS if ordinary else LIMITS
            mk, organism = model(item, topology, limits)
            if ordinary:
                oracles = general[rep]
                for o in oracles:
                    ck = mk, o.maze.case_id
                    if ck not in cached:
                        m = o.maze
                        r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
                        cached[ck] = normal_row(r, o)
                        actual_responses += 1
                        actual_work += r.dispatches + r.spatial_reads
                rows = [cached[mk, o.maze.case_id] for o in oracles]
                scope = 'general'
            else:
                pairs = micro[rep, level] if level is not None else [p for l in range(5) for p in micro[rep, l]]
                missing = [p for p in pairs if (mk, p.first.maze.case_id) not in cached]
                if missing:
                    ev = evaluate(item, missing, topology, limits, goal_pulse=True)
                    for row in ev.rows:
                        cached[mk, row['case']] = row
                    actual_responses += len(ev.rows)
                    actual_work += ev.work
                rows = [cached[mk, o.maze.case_id] for p in pairs for o in p.cases]
                scope = 'micro' if level is None else f'level{level}'
            result_key = key + '/' + role + '/' + scope
            aliases += len(rows)
            result_stats[result_key] = statistics_for(rows)
            log.write(json.dumps(dict(key=key, role=role, scope=scope, id=item.identity, digest=item.genome.digest,
                topology=topology, replicate=rep, limits=asdict(limits), cases=rows), separators=(',', ':')) + '\n')
            for row in rows:
                o = cases[row['case']]
                if row['optimal']:
                    if ordinary:
                        general_success[mk][row['case']] = row
                    elif len(o.path) > 2:
                        micro_success[mk][row['case']] = row
            return rows

        for key, state in frozen.items():
            cfg = state['config']
            rep, topology = cfg['replicate'], cfg['topology']
            for role in ('champion', 'original_rank', 'checkpoint', 'frozen'):
                value = (state['common_archives']['paired']['item'] if role == 'champion' else
                         state['common_archives']['current']['item'] if role == 'original_rank' else
                         checkpoint_controls[key]['champion'] if role == 'checkpoint' else state['frozen'])
                item = Individual.load(value)
                emit(key, role, item, topology, rep)
                emit(key, role, item, topology, rep, ordinary=True)
            print('Confirmed', key, flush=True)
        intact = controls()['intact']
        for rep in range(3):
            rows = emit(f'control/r{rep}', 'intact', intact, 'local', rep)
            assert all(r['optimal'] for r in rows)
            emit(f'control/r{rep}', 'intact', intact, 'local', rep, ordinary=True)
            for name in BASELINES:
                rows = []
                for o in general[rep]:
                    m = o.maze
                    r = baseline(name, m.cells, m.w, m.h, m.start, m.goal)
                    row = normal_row(r, o)
                    assert row['optimal'] if o.path else row['no_path']
                    rows.append(row)
                key = f'control/r{rep}/{name}/general'
                result_stats[key] = statistics_for(rows)
                log.write(json.dumps(dict(key=f'control/r{rep}', role=name, scope='general', replicate=rep,
                    topology=None, id=name, cases=rows), separators=(',', ':')) + '\n')

    # Choose benchmark cases by the preregistered fixed-order rule, not latency.
    timing_tasks = {}
    for rep in range(3):
        for n in (17, 33):
            for family in ('perfect', 'random'):
                o = next(o for o in general[rep] if o.maze.w == n and o.maze.family == family)
                for name in BASELINES:
                    timing_tasks[name, o.maze.case_id] = (name, o)
                for mk in models:
                    if o.maze.case_id in general_success[mk]:
                        timing_tasks[mk, o.maze.case_id] = (mk, o)
    for mk, successes in micro_success.items():
        if successes:
            case = sorted(successes)[0]
            timing_tasks[mk, case] = (mk, cases[case])
            for name in BASELINES:
                timing_tasks[name, case] = (name, cases[case])

    def timed_call(key, o):
        m = o.maze
        return (baseline(key, m.cells, m.w, m.h, m.start, m.goal) if isinstance(key, str)
                else models[key].react(m.cells, m.w, m.h, m.start, m.goal))

    timing = {str(key): dict(model=value[0], case=value[1].maze.case_id, seconds=[]) for key, value in timing_tasks.items()}
    timing_started = time.perf_counter()
    timing_responses = timing_work = timing_input_bytes = 0
    for key, o in timing_tasks.values():
        for _ in range(2):
            result = timed_call(key, o)
            assert assess(result, o).optimal
            timing_responses += 1
            timing_input_bytes += len(o.maze.cells)
            if not isinstance(key, str):
                timing_work += result.dispatches + result.spatial_reads
    rng = random.Random(seed_for(SEED, 'warm-timing-order', 0, 0))
    order = list(timing_tasks)
    for _ in range(30):
        rng.shuffle(order)
        for task in order:
            key, o = timing_tasks[task]
            t = time.perf_counter_ns()
            r = timed_call(key, o)
            elapsed = (time.perf_counter_ns() - t) / 1e9
            assert assess(r, o).optimal
            timing_responses += 1
            timing_input_bytes += len(o.maze.cells)
            if not isinstance(key, str):
                timing_work += r.dispatches + r.spatial_reads
            timing[str(task)]['seconds'].append(elapsed)
            timing[str(task)]['array_bytes'] = r.array_bytes
    for row in timing.values():
        row.update(median=statistics.median(row['seconds']), minimum=min(row['seconds']), maximum=max(row['seconds']))
    write_json(target / 'timings.json', dict(scope='Per-maze bytes input through emitted raster; static model setup separate',
        repetitions=30, records=list(timing.values()), elapsed_seconds=time.perf_counter() - timing_started,
        model_setup_seconds=model_setup_seconds, responses_including_warmups=timing_responses,
        candidate_work_including_warmups=timing_work, input_bytes_presented=timing_input_bytes))
    result = dict(search_summary_sha256=hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest(),
        checkpoint_sha256=summary['checkpoint_selections_sha256'],
        timecourse_selection_sha256=timecourse_freeze['selection_sha256'],
        frozen_sha256=summary['frozen_sha256'], source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        software_fixture_sha256=hashlib.sha256(software_fixtures.read_bytes()).hexdigest(),
        excluded_layouts=data.previous_count, resulting_layouts=len(data.layouts), elementary_groups=len(data.groups),
        general_primary_inputs=sum(map(len, general.values())), general_orbit_inputs=len(general_orbits),
        elementary_limits=asdict(LIMITS), general_limits=asdict(GENERAL_LIMITS),
        distinct_inferences=actual_responses, inference_work=actual_work, aliased_responses=aliases,
        elapsed_seconds=time.perf_counter() - started, max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        results=result_stats)
    write_json(target / 'summary.json', result)
    print(json.dumps({k: result[k] for k in ('distinct_inferences', 'elapsed_seconds', 'resulting_layouts')}, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
