"""Discarded A1 capacity, native-runtime and durable-recovery preflight."""
import gzip
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import shutil
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution import deep_campaign_a1 as runner
from maze_evolution.deep_campaign_amendment import SETUP_A1
from maze_evolution.deep_campaign_data_a1 import batch
from maze_evolution.deep_campaign_perfect11 import wilson_case
from maze_evolution.deep_campaign_store import Journal, packed, unpacked, hashed, writer_lock
from maze_evolution.foundation_data import layout_hash, transform_maze
from maze_evolution.foundation_study import compressed_json, read_compressed
from maze_evolution.routing_transfer import sha


def write(name, value):
    (SETUP_A1 / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    config = runner.check_setup()
    if SETUP_A1.exists():
        raise RuntimeError('Preserve existing preparation; never overwrite a preflight')
    SETUP_A1.mkdir()
    started = time.monotonic()
    # The real writer lock is held only for a read-only exact boundary snapshot.
    with writer_lock(runner.DEFAULT_RUN):
        db = sqlite3.connect(f'file:{runner.DEFAULT_RUN / "campaign.sqlite"}?mode=ro', uri=True)
        db.execute('BEGIN')
        settings = {k:unpacked(v) for k, v in db.execute('SELECT key,value FROM settings')}
        assert settings['latest'] == 8284
        assert db.execute('SELECT COUNT(*) FROM stages WHERE complete=0').fetchone()[0] == 0
        raw, sh = db.execute('SELECT value,hash FROM states WHERE stage=?',
                            (settings['latest'],)).fetchone()
        assert hashed(raw) == sh
        states = unpacked(raw)
        original = {h for h, in db.execute('SELECT hash FROM layouts')}
        chain = db.execute('SELECT chain_hash FROM stages WHERE n=?',
                           (settings['latest'],)).fetchone()[0]
        db.close()
    assert sh == 'a91b916899351935a5927c5d2c6f4c8830ccef03b949d060d463d89d31fb82a0'
    assert chain == '1f06d3a2ecdf38224c017b0fa23737cca142bef5678e6bdc62fe8939a3550da5'
    assert all(s['generation'] == 8268 for s in states)
    boundary = dict(latest_stage=settings['latest'], generation=8268, chain=chain,
                    state_sha256=sh, usage=settings['usage'], layouts_count=len(original),
                    layouts_sha256=hashed(packed(sorted(original))))
    write('boundary.json', boundary)
    compressed_json(SETUP_A1 / 'checkpoint_copy.json.gz', states)
    prior = original | set(read_compressed(
        runner.ROOT / 'results/deep_campaign_run/failure_08268/all_diagnostic_exclusions.json.gz')['hashes'])
    assert len(prior) == 828687
    capacity = []
    for index in range(962):
        for salt in range(4000):
            o = wilson_case(1491, 'a1-capacity', 0, index * 4000 + salt)
            orbit = {layout_hash(transform_maze(o.maze, p)) for p in range(8)}
            if orbit & prior:
                continue
            prior.update(orbit)
            capacity.append(dict(index=index, salt=salt, seed=o.maze.seed,
                                 cells_hex=o.maze.cells.hex(), start=o.maze.start,
                                 goal=o.maze.goal, layouts=sorted(orbit)))
            break
        else:
            raise RuntimeError('Capacity fixture exhausted')
    compressed_json(SETUP_A1 / 'capacity.json.gz', capacity)
    write('capacity.json', dict(passed=True, accepted_bases=len(capacity),
                                draws=sum(c['salt']+1 for c in capacity),
                                layouts=sum(len(c['layouts']) for c in capacity),
                                candidate_calls=0))
    # Prepare every fixture first and seal its exclusions before any inference.
    fixtures = []
    for g in range(8268, 8284):
        d = batch(1491, 'train', g, prior, [s['frontier'] for s in states])
        fixtures.append(d)
        prior.update(d['new_layouts'])
    d = batch(1491, 'assessment', 8284, prior, [2, 2, 2])
    fixtures.append(d)
    prior.update(d['new_layouts'])
    for k, d in enumerate(fixtures):
        compressed_json(SETUP_A1 / f'fixture_{k:02d}.json.gz', d)
    compressed_json(SETUP_A1 / 'additional_exclusions.json.gz',
                    dict(count=len(prior-original), hashes=sorted(prior-original)))
    # The rehearsal has its own journal; its initial state is never a founder.
    directory = SETUP_A1 / 'discarded_rehearsal'
    directory.mkdir()
    j = Journal(directory)
    # Novelty against the full history was checked above. Keep only fixture layouts
    # in this portable software journal; it is not the scientific journal.
    j.initialize(config, states, set())
    # Exercise preservation of nonzero cumulative counters on recovery.
    j.put('usage', boundary['usage'])
    j.db.commit()
    rehearsal_config = dict(config, session_wall_seconds=900,
                            call_cap=boundary['usage']['calls']+1_000_000)
    reports = []
    with ProcessPoolExecutor(10, mp_context=multiprocessing.get_context('spawn'),
                             initializer=runner.worker_init) as pool:
        for k, data in enumerate(fixtures):
            if j.get('usage')['candidate_seconds']-boundary['usage']['candidate_seconds'] >= 600:
                raise RuntimeError('Preflight candidate allowance reached')
            specs = runner.task_specs(states, data)
            n = j.prepare(data, specs)
            if k == 3:
                sizes = {r['case_id']:r['w']*r['h'] for r in data['mazes']}
                limited = dict(rehearsal_config, call_cap=j.get('usage')['calls']+
                               sum(runner.reservation(s, sizes)[0] for s in specs[:2]))
                assert runner.run_stage(j, n, data, pool, limited, started, [False]) == 'charged_work_or_calls'
                saved = j.get('usage')
                assert sum(s == 'done' for _, _, s in j.tasks(n)) == 2
                j.close()
                j = Journal(directory)
                assert j.get('usage') == saved
                assert sum(s == 'done' for _, _, s in j.tasks(n)) == 2
            assert runner.run_stage(j, n, data, pool, rehearsal_config, started, [False]) is None
            results = j.results(n)
            new, decisions = runner.transition(states, data, results)
            j.commit(n, new, decisions)
            states = new
            report = dict(fixture=k, kind=data['kind'],
                          calls=sum(r['calls'] for r in results),
                          candidate_seconds=sum(r['candidate_seconds'] for r in results),
                          tree_rss_bytes=runner.process_resources())
            reports.append(report)
            print(json.dumps(report), flush=True)
    audit_started = time.monotonic()
    audit = runner.replay_journal(j)
    assert audit['transitions'] == 17 and audit['births_replayed'] == 2496
    usage = j.get('usage')
    assert usage['candidate_seconds']-boundary['usage']['candidate_seconds'] < 600
    assert time.monotonic()-started < 900
    # Preserve the exact rehearsal journal and all receipts in a portable gzip.
    j.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    j.close()
    with (directory / 'campaign.sqlite').open('rb') as source:
        with gzip.open(SETUP_A1 / 'rehearsal.sqlite.gz', 'wb') as target:
            shutil.copyfileobj(source, target)
    # This is explicitly discarded software data; compressed bytes are preserved.
    (directory / 'campaign.sqlite').unlink()
    directory.rmdir()
    runner.check_setup()
    write('preflight.json', dict(
        passed=True, scientific_rounds=0, discarded_rounds=16,
        broad_fixture_queries_per_model=len(fixtures[-1]['queries']['0']),
        stages=reports, replay=audit, replay_seconds=time.monotonic()-audit_started,
        added_usage={k:usage[k]-v for k, v in boundary['usage'].items()},
        additional_exclusions=len(prior-original), total_exclusions=len(prior),
        wall_seconds=time.monotonic()-started, original_seal_verified=True,
        environment=runner.source_manifest(),
        all_candidate_rasters_independently_graded=True,
        resumed_after_two_receipts=True, scientific_state_unchanged=True))


if __name__ == '__main__':
    main()
