"""Prepare and calibrate the new campaign; never launch scientific evolution."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import json
import multiprocessing
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign import *
from maze_evolution.deep_campaign_search import initial_states
from maze_evolution.baselines import baseline
from maze_evolution.foundation_pair_confirm import normal_row
from maze_evolution.selectivity_study import prior_check


def write(name, value):
    (SETUP / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def prepare():
    if SETUP.exists():
        raise SystemExit('Setup exists; do not overwrite scientific inputs')
    SETUP.mkdir()
    old = read_compressed(ROOT / 'results/selectivity_pressure/next_states.json.gz')
    states = initial_states(old)
    compressed_json(SETUP / 'founders.json.gz', states)
    previous = set(read_compressed(ROOT / 'results/selectivity_pressure/whole_layout_exclusions.json.gz')['hashes'])
    assert len(previous) == 279824
    for name, kind, g, frontier in [
        ('train', 'train', 0, [1, 1, 1]),
        ('mixed', 'train', 34, [2, 4, 8]),
        ('assessment', 'assessment', 0, [1, 1, 1]),
    ]:
        data = batch(1474, kind, g, previous, frontier)
        compressed_json(SETUP / f'fixture_{name}.json.gz', data)
        previous.update(data['new_layouts'])
    compressed_json(SETUP / 'exclusions.json.gz', dict(count=len(previous), hashes=sorted(previous)))
    config = dict(
        phase='deep_v1', seed=2026102008, milestone=10000, islands=3,
        population=96, genes=256, topology='local', exposure=7, max_steps=256,
        reads_per_site=4096, instructions_per_site=32768,
        survivors=44, births=52, immigrants=7, protected_per_island=20,
        archive_size=32, archive_reinsertion=4, assessment_every=500,
        checkpoints_every=100, workers=10, session_wall_seconds=12*3600,
        memory_bytes=12*2**30, storage_bytes=20*2**30,
        disk_free_floor_bytes=16*2**30, call_cap=100_000_000, work_cap=10**15,
        sexual_recombination=False, discovery_not_policy_comparison=True)
    write('config.json', config)
    # Verify the completed B seal as well as every previous stage.
    count = prior_check()
    seal = json.loads((ROOT / 'results/selectivity_pressure/completion.json').read_text())
    for name, h in seal['source_and_artifact_sha256'].items():
        assert sha(ROOT / name) == h, name
        count += 1
    write('preparation.json', dict(prior_hashes_verified=count, historical_layouts=279824,
                                  excluded_with_fixtures=len(previous), scientific_calls=0))
    print(json.dumps(dict(prepared=True, exclusions=len(previous), prior_hashes=count)))


def benchmark():
    states = read_compressed(SETUP / 'founders.json.gz')
    data = read_compressed(SETUP / 'fixture_train.json.gz')
    specs = task_specs(states, data)
    ids = set(c for v in data['queries'].values() for c in v)
    mazes = [r for r in data['mazes'] if r['case_id'] in ids]
    key = hashed(packed(mazes))
    runs, reference = [], None
    for workers in (1, 4, 10):
        with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context('spawn'),
                                 initializer=worker_init) as pool:
            for trial in range(4):
                start = time.perf_counter()
                futures = [pool.submit(evaluate_task, spec, mazes, key) for spec in specs]
                results = [f.result() for f in futures]
                wall = time.perf_counter() - start
                # All warm/cold repetitions must produce identical raw responses.
                signature = hashed(packed([r['entries'] for r in results]))
                if reference is None:
                    reference = signature
                assert signature == reference
                new, event = transition(states, data, results)
                transition_hash = hashed(packed([new, event]))
                if trial == 0 and workers == 1:
                    expected_transition = transition_hash
                    compressed_json(SETUP / 'benchmark_receipts.json.gz', results)
                assert transition_hash == expected_transition
                row = dict(workers=workers, trial=trial, cold=trial==0, wall_seconds=wall,
                           calls=sum(r['calls'] for r in results),
                           cpu_seconds=sum(r['cpu_seconds'] for r in results),
                           candidate_seconds=sum(r['candidate_seconds'] for r in results),
                           work=sum(r['work'] for r in results),
                           tree_rss_bytes=process_resources(), response_hash=signature,
                           transition_hash=transition_hash)
                runs.append(row)
                print(json.dumps(row), flush=True)
    medians = {w:statistics.median(r['wall_seconds'] for r in runs if r['workers']==w and not r['cold'])
               for w in (1, 4, 10)}
    best = min(medians, key=medians.get)
    config = json.loads((SETUP / 'config.json').read_text())
    config['workers'] = best
    write('config.json', config)
    write('benchmark.json', dict(runs=runs, warm_median_seconds=medians, workers=best,
                                all_responses_and_reproduction_identical=True,
                                fixture_calls=sum(r['calls'] for r in runs)))


def rehearsal():
    """One complete broad screen + reproduction, split-session replay and baselines."""
    from tempfile import TemporaryDirectory
    config = json.loads((SETUP / 'config.json').read_text())
    states = read_compressed(SETUP / 'founders.json.gz')
    previous = set(read_compressed(ROOT / 'results/selectivity_pressure/whole_layout_exclusions.json.gz')['hashes'])
    start = time.monotonic()
    total, stages = 0, []
    with TemporaryDirectory(prefix='deep-rehearsal-') as temp:
        j = Journal(temp)
        j.initialize(config, states, previous)
        with ProcessPoolExecutor(config['workers'], mp_context=multiprocessing.get_context('spawn'),
                                 initializer=worker_init) as pool:
            for name in ('assessment', 'train'):
                data = read_compressed(SETUP / f'fixture_{name}.json.gz')
                # Fixture generations are isolated software evidence, never campaign state.
                n = j.prepare(data, task_specs(states, data))
                t = time.perf_counter()
                reason = run_stage(j, n, data, pool, config, start, [False])
                assert reason is None
                results = j.results(n)
                new, events = transition(states, data, results)
                chain = j.commit(n, new, events)
                assert j.verify_chain() == chain
                result_name = f'rehearsal_{name}.json.gz'
                compressed_json(SETUP / result_name, dict(data_file=f'fixture_{name}.json.gz',
                                before=states, after=new, results=results, decisions=events, chain=chain))
                calls = sum(r['calls'] for r in results)
                total += calls
                stages.append(dict(kind=name, calls=calls, wall_seconds=time.perf_counter()-t,
                                   candidate_seconds=sum(r['candidate_seconds'] for r in results),
                                   worker_cpu_seconds=sum(r['cpu_seconds'] for r in results),
                                   tree_rss_bytes=process_resources(),
                                   journal_bytes=sum(p.stat().st_size for p in Path(temp).iterdir() if p.is_file())))
                # Close/reopen is a session boundary. Durable state must be exact.
                j.close()
                j = Journal(temp)
                assert j.state() == new
                states = new
        j.close()
    data = read_compressed(SETUP / 'fixture_assessment.json.gz')
    cases = cases_from_manifest(data['mazes'])
    checker = Checker(cases)
    baseline_rows = []
    for name in ('compiled_bfs', 'compiled_astar', 'wave_bit'):
        for cid in data['queries']['0']:
            o = cases[cid]
            m = o.maze
            row = canonical(normal_row(baseline(name, m.cells, m.w, m.h, m.start, m.goal), o))
            checker.row(row)
            assert row['optimal'] or row['no_path']
            baseline_rows.append(dict(model=name, row=row))
    compressed_json(SETUP / 'rehearsal_baselines.json.gz', baseline_rows)
    write('rehearsal.json', dict(passed=True, scientific_generations=0,
                               discarded_generations=1, stages=stages, candidate_calls=total,
                               baseline_calls=len(baseline_rows), wall_seconds=time.monotonic()-start,
                               all_candidate_rasters_independently_graded=True))
    print(json.dumps(json.loads((SETUP / 'rehearsal.json').read_text())), flush=True)


def continuation():
    """Discarded 16-round pipeline rehearsal, including a deliberately interrupted stage."""
    from tempfile import TemporaryDirectory
    config = json.loads((SETUP / 'config.json').read_text())
    states = read_compressed(SETUP / 'rehearsal_assessment.json.gz')['after']
    previous = set(read_compressed(SETUP / 'exclusions.json.gz')['hashes'])
    initial_layouts = previous.copy()
    before_layouts = len(previous)
    started, cpu = time.monotonic(), total_cpu()
    stage_reports, all_data = [], []
    with TemporaryDirectory(prefix='deep-continuation-') as temp:
        j = Journal(temp)
        j.initialize(config, states, previous)
        with ProcessPoolExecutor(config['workers'], mp_context=multiprocessing.get_context('spawn'),
                                 initializer=worker_init) as pool:
            for g in range(16):
                t = time.perf_counter()
                data = batch(1475, 'train', g, previous, [s['frontier'] for s in states])
                all_data.append(data)
                previous.update(data['new_layouts'])
                specs = task_specs(states, data)
                n = j.prepare(data, specs)
                if g == 3:
                    sizes = {r['case_id']:r['w']*r['h'] for r in data['mazes']}
                    limited = dict(config, call_cap=j.get('usage')['calls']+
                                   sum(reservation(s, sizes)[0] for s in specs[:2]))
                    assert run_stage(j, n, data, pool, limited, started, [False]) == 'charged_work_or_calls'
                    done = sum(status == 'done' for _, _, status in j.tasks(n))
                    assert done == 2
                    j.close()
                    j = Journal(temp)
                    assert sum(status == 'done' for _, _, status in j.tasks(n)) == 2
                assert run_stage(j, n, data, pool, config, started, [False]) is None
                results = j.results(n)
                new, events = transition(states, data, results)
                chain = j.commit(n, new, events)
                stage_reports.append(dict(generation=g+1, wall_seconds=time.perf_counter()-t,
                                          candidate_seconds=sum(r['candidate_seconds'] for r in results),
                                          calls=sum(r['calls'] for r in results),
                                          tree_rss_bytes=process_resources()))
                states = new
                print(json.dumps(stage_reports[-1]), flush=True)
        audit = replay_journal(j)
        usage = j.get('usage')
        # A portable SQLite backup preserves every real receipt and mutation in this rehearsal.
        destination = SETUP / 'continuation_journal.sqlite'
        if destination.exists():
            raise RuntimeError('Do not overwrite the prior rehearsal')
        import sqlite3, gzip
        target = sqlite3.connect(destination)
        j.db.backup(target)
        target.close()
        j.close()
        size = destination.stat().st_size
        with destination.open('rb') as src, gzip.open(str(destination)+'.gz', 'wb', compresslevel=6) as dst:
            shutil.copyfileobj(src, dst)
        destination.unlink()
    compressed_json(SETUP / 'exclusions.json.gz', dict(count=len(previous), hashes=sorted(previous)))
    compressed_json(SETUP / 'continuation_layouts.json.gz', sorted(previous-initial_layouts))
    write('continuation.json', dict(passed=True, discarded_generations=16,
                                   stages=stage_reports, usage=usage, audit=audit,
                                   new_layouts=len(previous)-before_layouts, journal_bytes=size,
                                   wall_seconds=time.monotonic()-started,
                                   process_tree_cpu_seconds=total_cpu()-cpu,
                                   interrupted_stage_reused_two_completed_receipts=True))


def freeze():
    assert json.loads((SETUP / 'rehearsal.json').read_text())['passed']
    if (SETUP / 'registration.json').exists():
        raise SystemExit('Already registered')
    registration = source_manifest()
    paths = [*sorted(SETUP.rglob('*')), ROOT / 'tools/prepare_deep_campaign.py',
             ROOT / 'tests/test_deep_campaign.py', ROOT / 'docs/DEEP_CAMPAIGN.md']
    registration['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths
                                  if p.is_file() and p.suffix != '.log'})
    registration.update(scientific_calls=0, scientific_generations=0, status='prepared_not_launched')
    write('registration.json', registration)
    print(json.dumps(dict(frozen=True, files=len(registration['files']))))


if __name__ == '__main__':
    from maze_evolution.routing_transfer import canonical
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare', 'benchmark', 'rehearsal', 'continuation', 'freeze'))
    globals()[p.parse_args().action]()
