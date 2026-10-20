"""A1 continuation of the sealed deep campaign, preserving all original history.

Runner copied from deep_campaign.py; changes are amendment verification/binding,
versioned generator, phase tags, recursive storage accounting and audit checks.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
import json
import multiprocessing
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import sqlite3
import subprocess
import time

from .deep_campaign_data_a1 import batch, cases_from_manifest
from .deep_campaign_amendment import check_amendment, bind_amendment, verify_amendment
from .deep_campaign_search import initial_states, candidates, assess_state, reproduce
from .deep_campaign_store import Journal, packed, unpacked, hashed, writer_lock
from .exposure_selection import physical, organism, record
from .foundation_calibration import ROOT
from .foundation_study import read_compressed, compressed_json
from .foundation_study_verify_core import Checker
from .routing_transfer import sha

SETUP = ROOT / 'results/deep_campaign_setup'
DEFAULT_RUN = ROOT / 'runs/deep_campaign_v1'
_cache = {}
_peak_rss = 0


def worker_init():
    # Native candidate kernels are serial. Avoid unrelated numerical thread pools.
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS'):
        os.environ[name] = '1'


def evaluate_task(spec, maze_rows, data_hash):
    global _cache
    cpu = time.process_time()
    if _cache.get('hash') != data_hash:
        cases = cases_from_manifest(maze_rows)
        _cache = dict(hash=data_hash, cases=cases, checker=Checker(cases))
    cases, checker = _cache['cases'], _cache['checker']
    out, seconds, work, calls = [], 0., 0, 0
    for entry in spec:
        org = organism(entry['model'])
        rows = []
        for cid in entry['queries']:
            o = cases[cid]
            m = o.maze
            t = time.perf_counter()
            response = org.react(m.cells, m.w, m.h, m.start, m.goal)
            seconds += time.perf_counter() - t
            r = record(response, o)
            checker.row(r)
            rows.append(r)
            work += r['reads'] + r['dispatches'] + r['exposure_checks']
            calls += 1
        out.append(dict(aliases=entry['aliases'], rows=rows))
    return dict(entries=out, candidate_seconds=seconds, work=work, calls=calls,
                cpu_seconds=time.process_time() - cpu, independently_graded=calls)


def task_specs(states, data, chunk=8):
    models = {}
    for island, s in enumerate(states):
        queries = data['queries'][str(island)]
        for i in candidates(s, data['kind'] == 'assessment'):
            pid, model = physical(i, 'neutral', 'local')
            key = pid + '/' + hashed(packed(queries))
            if key not in models:
                models[key] = dict(model=model, queries=queries, aliases=[])
            models[key]['aliases'].append([island, i.identity])
    ordered = [models[k] for k in sorted(models)]
    return [ordered[k:k+chunk] for k in range(0, len(ordered), chunk)]


def reservation(spec, sizes):
    calls = sum(len(e['queries']) for e in spec)
    # Reads and dispatches have native caps; exposure checks <= dispatches.
    work = sum(sizes[c] * (4096 + 2 * 32768) for e in spec for c in e['queries'])
    return calls, work


def process_resources():
    """Current process tree RSS/CPU; no extra dependency and no system-wide sampling."""
    text = subprocess.check_output(['ps', '-axo', 'pid=,ppid=,rss=,time='], text=True)
    rows = []
    for line in text.splitlines():
        pid, parent, rss, cpu = line.split()
        rows.append((int(pid), int(parent), int(rss), cpu))
    pids = {os.getpid()}
    for _ in range(8):
        pids |= {p for p, parent, _, _ in rows if parent in pids}
    global _peak_rss
    rss = sum(rss * 1024 for p, _, rss, _ in rows if p in pids)
    _peak_rss = max(_peak_rss, rss)
    return rss


def resource_reason(directory, config, started):
    if time.monotonic() - started >= config['session_wall_seconds']:
        return 'session_wall'
    if process_resources() >= config['memory_bytes']:
        return 'memory'
    disk = shutil.disk_usage(directory)
    if disk.free < config['disk_free_floor_bytes']:
        return 'disk_free'
    size = sum(p.stat().st_size for p in Path(directory).rglob('*') if p.is_file())
    if size >= config['storage_bytes']:
        return 'storage'
    return None


def run_stage(journal, n, data, executor, config, started, stopping):
    queries = set(c for ids in data['queries'].values() for c in ids)
    maze_rows = [r for r in data['mazes'] if r['case_id'] in queries]
    sizes = {r['case_id']:r['w'] * r['h'] for r in maze_rows}
    data_hash = hashed(packed(maze_rows))
    todo = [(k, spec) for k, spec, status in journal.tasks(n) if status != 'done']
    pending = {}
    reason = None
    while todo or pending:
        reason = reason or ('signal' if stopping[0] else resource_reason(journal.directory, config, started))
        while todo and len(pending) < config['workers'] and not reason:
            k, spec = todo[0]
            calls, work = reservation(spec, sizes)
            usage = journal.get('usage')
            if usage['calls'] + calls > config['call_cap'] or usage['work'] + work > config['work_cap']:
                reason = 'charged_work_or_calls'
                break
            journal.reserve(n, k, calls, work)
            future = executor.submit(evaluate_task, spec, maze_rows, data_hash)
            pending[future] = (k, work)
            todo.pop(0)
        if not pending:
            break
        done, _ = wait(pending, timeout=1, return_when=FIRST_COMPLETED)
        for future in done:
            k, reserved = pending.pop(future)
            journal.receipt(n, k, future.result(), reserved)
    if todo:
        return reason
    return None


def transition(states, data, results):
    rows = [{} for _ in states]
    for result in results:
        for entry in result['entries']:
            for island, identity in entry['aliases']:
                assert identity not in rows[island]
                rows[island][identity] = entry['rows']
    new, decisions = [], []
    for island, s in enumerate(states):
        fn = assess_state if data['kind'] == 'assessment' else reproduce
        value, decision = fn(s, rows[island], data['metadata'])
        new.append(value)
        decisions.append(decision)
    return new, decisions


def source_manifest():
    from importlib.metadata import version
    files = [ROOT / 'cellular_maze_lab.py', *sorted((ROOT / 'maze_evolution').glob('*.py'))]
    return dict(files={str(p.relative_to(ROOT)):sha(p) for p in files},
                python=platform.python_version(), platform=platform.platform(),
                dependencies={n:version(n) for n in ('numpy', 'numba', 'llvmlite')})


def check_setup():
    config = json.loads((SETUP / 'config.json').read_text())
    registration = json.loads((SETUP / 'registration.json').read_text())
    for name, h in registration['files'].items():
        if sha(ROOT / name) != h:
            raise ValueError(f'Frozen source/input changed: {name}')
    current = source_manifest()
    for field in ('python', 'dependencies'):
        if current[field] != registration[field]:
            raise ValueError(f'Runtime differs: {field}; document a new phase')
    return config


def run(directory, max_rounds=None):
    global _peak_rss
    _peak_rss = 0
    config = check_setup()
    amendment = check_amendment()
    if not (Path(directory) / 'campaign.sqlite').exists():
        raise ValueError('A1 requires the existing campaign journal')
    if max_rounds is not None:
        if not 0 <= max_rounds <= config['milestone']:
            raise ValueError('Round ceiling outside frozen milestone')
    ceiling = config['milestone'] if max_rounds is None else max_rounds
    stopping = [False]
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_:stopping.__setitem__(0, True))
    started = time.monotonic()
    start_epoch = time.time()
    cpu_start = total_cpu()
    with writer_lock(directory):
        journal = Journal(directory)
        founders = read_compressed(SETUP / 'founders.json.gz')
        previous = set(read_compressed(SETUP / 'exclusions.json.gz')['hashes'])
        journal.initialize(config, founders, previous)
        journal.verify_chain()
        bind_amendment(journal, amendment)
        previous = journal.layouts()
        reason = None
        context = multiprocessing.get_context('spawn')
        with ProcessPoolExecutor(config['workers'], mp_context=context, initializer=worker_init) as pool:
            while not reason:
                states = journal.state()
                g = states[0]['generation']
                assert all(s['generation'] == g for s in states)
                pending = journal.pending()
                if pending:
                    n, data = pending
                    assert data.get('amendment') == amendment['registration_sha256']
                    # A pending task cannot silently change its models or query list.
                    assert [s for _, s, _ in journal.tasks(n)] == task_specs(states, data)
                else:
                    if g % config['assessment_every'] == 0 and states[0]['assessment_generation'] != g:
                        kind = 'assessment'
                    elif g >= ceiling:
                        reason = 'milestone' if g >= config['milestone'] else 'requested_session_round_ceiling'
                        break
                    else:
                        kind = 'train'
                    reason = 'signal' if stopping[0] else resource_reason(directory, config, started)
                    if reason:
                        break
                    data = batch(config['seed'], kind, g, previous, [s['frontier'] for s in states])
                    data['amendment'] = amendment['registration_sha256']
                    n = journal.prepare(data, task_specs(states, data))
                    previous.update(data['new_layouts'])
                reason = run_stage(journal, n, data, pool, config, started, stopping)
                if reason:
                    break
                new, decisions = transition(states, data, journal.results(n))
                chain = journal.commit(n, new, decisions)
                print(json.dumps(dict(stage=n, kind=data['kind'], generation=new[0]['generation'],
                                      frontier=[s['frontier'] for s in new], chain=chain,
                                      usage=journal.get('usage'),
                                      wall_seconds=time.monotonic()-started)), flush=True)
                if stopping[0]:
                    reason = 'signal'
        states = journal.state()
        if reason == 'milestone':
            # Immutable choice packet BEFORE any independent final cases are generated.
            choices = dict(amendment=amendment['registration_sha256'],
                           generation=states[0]['generation'], chain=journal.verify_chain(),
                           items=[s['coverage_archive'][:1] + s['coverage_archive'][4:7]
                                  for s in states],
                           frozen_references=[s['frozen_references'] for s in states],
                           confirmation_not_generated=True)
            target = Path(directory) / 'milestone_choices.json.gz'
            if target.exists():
                assert read_compressed(target) == choices
            else:
                compressed_json(target, choices)
        status = dict(reason=reason, generation=states[0]['generation'],
                      pending=journal.pending()[0] if journal.pending() else None,
                      usage=journal.get('usage'), wall_seconds=time.monotonic()-started,
                      session_process_tree_cpu_seconds=total_cpu()-cpu_start,
                      sampled_peak_tree_rss_bytes=_peak_rss, started_epoch=start_epoch,
                      ended_epoch=time.time())
        journal.put('last_session', status)
        journal.put('sessions', (journal.get('sessions') or []) + [status])
        journal.db.commit()
        journal.close()
        print(json.dumps(status), flush=True)
        return status


def total_cpu():
    return sum(r.ru_utime + r.ru_stime for r in (
        resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


def replay_journal(j):
    """Replay every selection, concrete mutation and RNG transition, not inference."""
    chain = j.verify_chain()
    states = unpacked(j.db.execute('SELECT value FROM states WHERE stage=-1').fetchone()[0])
    births, count = 0, 0
    for n, raw, decision, state_hash in j.db.execute(
            'SELECT n,input,decision,state_hash FROM stages WHERE complete=1 ORDER BY n'):
        data = unpacked(raw)
        assert [s for _, s, _ in j.tasks(n)] == task_specs(states, data)
        states, events = transition(states, data, j.results(n))
        assert packed(events) == decision
        assert hashed(packed(states)) == state_hash
        births += sum(len(e.get('births', [])) for e in events)
        count += 1
    assert states == j.state()
    return dict(chain=chain, transitions=count, births_replayed=births,
                inference_replayed=False, independent_raster_grading='at evaluation time')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('run', 'status', 'audit'))
    parser.add_argument('--directory', type=Path, default=DEFAULT_RUN)
    parser.add_argument('--through-round', type=int)
    args = parser.parse_args()
    if args.action == 'run':
        run(args.directory, args.through_round)
    else:
        if not (args.directory / 'campaign.sqlite').exists():
            raise SystemExit('Campaign has not been launched')
        if args.action == 'status':
            db = sqlite3.connect(f'file:{args.directory / "campaign.sqlite"}?mode=ro', uri=True)
            # One read transaction gives a consistent snapshot during live WAL writes.
            db.execute('BEGIN')
            values = {k:unpacked(v) for k, v in db.execute('SELECT key,value FROM settings')}
            states = unpacked(db.execute('SELECT value FROM states WHERE stage=?',
                                        (values['latest'],)).fetchone()[0])
            pending = db.execute('SELECT n,kind,generation FROM stages WHERE complete=0').fetchone()
            out = dict(generation=states[0]['generation'], frontier=[s['frontier'] for s in states],
                       usage=values['usage'], pending=pending, last_session=values.get('last_session'))
            db.close()
            print(json.dumps(out, indent=2))
            return
        with writer_lock(args.directory):
            check_setup()
            amendment = check_amendment()
            j = Journal(args.directory)
            verify_amendment(j, amendment)
            out = dict(generation=j.state()[0]['generation'], usage=j.get('usage'),
                       session=j.get('last_session'))
            if args.action == 'audit':
                out['replay'] = replay_journal(j)
            print(json.dumps(out, indent=2))
            j.close()


if __name__ == '__main__':
    main()
