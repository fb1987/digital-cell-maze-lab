"""Recovery, provenance and selection failures that would invalidate a long campaign."""
from copy import deepcopy
import json
import sqlite3

import pytest

from maze_evolution.deep_campaign import (
    SETUP, task_specs, transition, reservation, run_stage, resource_reason,
    replay_journal)
from maze_evolution.deep_campaign_data import cases_from_manifest
from maze_evolution.deep_campaign_search import initial_states, coverage_select, assess_state, reproduce
from maze_evolution.deep_campaign_store import Journal, packed, hashed, writer_lock
from maze_evolution.exposure_genome import Individual
from maze_evolution.foundation_calibration import ROOT
from maze_evolution.foundation_data import layout_hash
from maze_evolution.foundation_study import read_compressed
from maze_evolution.selectivity_search import assert_population


@pytest.fixture(scope='module')
def founders():
    return read_compressed(SETUP / 'founders.json.gz')


@pytest.fixture(scope='module')
def fixture():
    return read_compressed(SETUP / 'fixture_train.json.gz')


@pytest.fixture(scope='module')
def receipts():
    return read_compressed(SETUP / 'benchmark_receipts.json.gz')


def journal(path, founders, data, specs):
    j = Journal(path)
    j.initialize(dict(phase='test'), founders, set())
    n = j.prepare(data, specs)
    return j, n


def fill(j, n, data, specs, receipts, start=0):
    sizes = {r['case_id']:r['w']*r['h'] for r in data['mazes']}
    for k in range(start, len(specs)):
        calls, work = reservation(specs[k], sizes)
        j.reserve(n, k, calls, work)
        assert receipts[k]['calls'] == calls
        j.receipt(n, k, receipts[k], work)


def test_exact_continued_populations_and_rng(founders):
    old = read_compressed(ROOT / 'results/selectivity_pressure/next_states.json.gz')
    assert initial_states(old) == founders
    for k, s in enumerate(founders):
        for field in ('population', 'rng', 'gene_ids', 'families', 'protected'):
            assert s[field] == old[f'carry/{k}/current'][field]
        assert s['generation'] == 0
        assert len(s['protected']) == 20
        assert_population(s)


def test_resume_rejects_a_different_founder_history_or_exclusion_set(tmp_path, founders):
    j = Journal(tmp_path)
    j.initialize({'phase':'test'}, founders, {'a'})
    j.initialize({'phase':'test'}, founders, {'a'})
    changed = deepcopy(founders)
    changed[0]['assessment_generation'] = 0
    with pytest.raises(ValueError, match='Initial population'):
        j.initialize({'phase':'test'}, changed, {'a'})
    with pytest.raises(ValueError, match='exclusion'):
        j.initialize({'phase':'test'}, founders, {'b'})
    j.close()


def test_fixtures_exclude_all_prior_layouts_and_each_other():
    previous = set(read_compressed(ROOT / 'results/selectivity_pressure/whole_layout_exclusions.json.gz')['hashes'])
    assert len(previous) == 279824
    for name in ('train', 'mixed', 'assessment'):
        d = read_compressed(SETUP / f'fixture_{name}.json.gz')
        cases = cases_from_manifest(d['mazes'])
        layouts = {layout_hash(o.maze) for o in cases.values()}
        assert layouts == set(d['new_layouts'])
        assert not layouts & previous
        previous.update(layouts)
        for ids in d['queries'].values():
            pairs = {}
            for c in ids:
                m = d['metadata'][c]
                if m['family'] == 'paired':
                    pairs.setdefault((m['base'], m['pose']), []).append(c)
            assert all(len(v) == 2 for v in pairs.values())
    if (SETUP / 'continuation_layouts.json.gz').exists():
        extra = set(read_compressed(SETUP / 'continuation_layouts.json.gz'))
        assert not extra & previous
        previous.update(extra)
    assert previous == set(read_compressed(SETUP / 'exclusions.json.gz')['hashes'])


def test_resume_keeps_completed_receipts_and_exact_reproduction(tmp_path, founders, fixture, receipts):
    specs = task_specs(founders, fixture)
    expected, event = transition(founders, fixture, receipts)
    j, n = journal(tmp_path, founders, fixture, specs)
    fill(j, n, fixture, specs[:2], receipts[:2])
    saved_usage = j.get('usage')
    j.close()
    j = Journal(tmp_path)
    assert j.pending() == (n, fixture)
    assert sum(status == 'done' for _, _, status in j.tasks(n)) == 2
    assert j.get('usage') == saved_usage
    fill(j, n, fixture, specs, receipts, 2)
    resumed, events = transition(j.state(), fixture, j.results(n))
    assert (resumed, events) == (expected, event)
    chain = j.commit(n, resumed, events)
    j.close()
    j = Journal(tmp_path)
    assert j.pending() is None and j.state() == expected
    assert j.verify_chain() == chain
    for s, before, e in zip(resumed, founders, events):
        assert_population(s)
        assert s['protected'] == before['protected']
        assert len(e['births']) == 52
        assert sum(b['mutation'] is not None for b in e['births']) == 45
        assert all(b['item']['id'].startswith(s['key'] + '/') for b in e['births'])
    j.close()


def test_incomplete_or_corrupt_receipts_cannot_commit(tmp_path, founders, fixture, receipts):
    specs = task_specs(founders, fixture)
    j, n = journal(tmp_path, founders, fixture, specs)
    with pytest.raises(ValueError):
        j.commit(n, founders, [])
    fill(j, n, fixture, specs, receipts)
    j.db.execute("UPDATE tasks SET result=? WHERE stage=? AND n=0", (packed({'corrupt':True}), n))
    j.db.commit()
    with pytest.raises(ValueError):
        j.commit(n, founders, [])
    assert j.state() == founders
    j.close()


def test_crash_reservations_are_not_erased(tmp_path, founders, fixture, receipts):
    specs = task_specs(founders, fixture)
    j, n = journal(tmp_path, founders, fixture, specs)
    sizes = {r['case_id']:r['w']*r['h'] for r in fixture['mazes']}
    calls, work = reservation(specs[0], sizes)
    j.reserve(n, 0, calls, work)
    j.close()
    j = Journal(tmp_path)
    j.reserve(n, 0, calls, work)
    j.receipt(n, 0, receipts[0], work)
    usage = j.get('usage')
    assert usage['calls'] == 2*calls
    assert usage['work'] == work + receipts[0]['work']
    assert usage['uncertain_attempts'] == 1
    j.close()


def test_uncommitted_publication_rolls_back_and_single_writer(tmp_path, founders, fixture):
    specs = task_specs(founders, fixture)
    j, n = journal(tmp_path, founders, fixture, specs)
    j.put('latest', 1234)
    j.close()  # SQLite rolls back an interrupted transaction.
    j = Journal(tmp_path)
    assert j.state() == founders
    j.close()
    with writer_lock(tmp_path):
        with pytest.raises(BlockingIOError):
            with writer_lock(tmp_path):
                pass


def test_coverage_archive_preserves_complementary_ordinary_success(founders):
    items = []
    seen = set()
    for raw in founders[0]['population']:
        i = Individual.load(raw)
        if i.genome.digest not in seen:
            items.append(i)
            seen.add(i.genome.digest)
        if len(items) == 8:
            break
    meta = {f'c{k}':dict(family='corridor') for k in range(10)}
    meta['ordinary'] = dict(family='ordinary_perfect')
    rows = {}
    for n, i in enumerate(items):
        rows[i.identity] = [
            dict(case=c, optimal=(n < 7 and c != 'ordinary') or (n == 7 and c == 'ordinary'),
                 valid=(n < 7 and c != 'ordinary') or (n == 7 and c == 'ordinary'),
                 no_path=False, reachable=True, status='emitted', partial=0.,
                 reads=0, dispatches=0, exposure_checks=0, mask='00')
            for c in meta]
    chosen, _ = coverage_select(items, rows, meta, limit=5)
    assert items[-1] in chosen  # Low aggregate fitness, complementary real capability.
    assert len(chosen) == 5


def test_parallel_reproduction_identical_at_all_worker_counts():
    p = json.loads((SETUP / 'benchmark.json').read_text())
    assert len({r['response_hash'] for r in p['runs']}) == 1
    assert len({r['transition_hash'] for r in p['runs']}) == 1
    assert {r['workers'] for r in p['runs']} == {1, 4, 10}


def test_saved_sixteen_round_rehearsal_replays_every_birth_and_rng(tmp_path):
    import gzip
    import shutil
    with gzip.open(SETUP / 'continuation_journal.sqlite.gz', 'rb') as source:
        with (tmp_path / 'campaign.sqlite').open('wb') as destination:
            shutil.copyfileobj(source, destination)
    j = Journal(tmp_path)
    result = replay_journal(j)
    assert result['transitions'] == 16
    assert result['births_replayed'] == 16 * 3 * 52
    assert j.state()[0]['generation'] == 16
    j.close()


def test_budget_stops_before_dispatch_and_preserves_pending(tmp_path, founders, fixture):
    import time
    config = json.loads((SETUP / 'config.json').read_text())
    specs = task_specs(founders, fixture)
    j, n = journal(tmp_path, founders, fixture, specs)
    # No executor is supplied: a budget violation must never submit a task.
    reason = run_stage(j, n, fixture, None, dict(config, call_cap=0),
                       time.monotonic(), [False])
    assert reason == 'charged_work_or_calls'
    assert j.get('usage')['calls'] == 0 and j.pending() == (n, fixture)
    assert resource_reason(tmp_path, dict(config, session_wall_seconds=0),
                           time.monotonic()) == 'session_wall'
    assert resource_reason(tmp_path, dict(config, memory_bytes=0),
                           time.monotonic()) == 'memory'
    assert resource_reason(tmp_path, dict(config, disk_free_floor_bytes=10**30),
                           time.monotonic()) == 'disk_free'
    assert resource_reason(tmp_path, dict(config, storage_bytes=0),
                           time.monotonic()) == 'storage'
    j.close()


def test_assessment_replays_archive_and_inactive_reinsertion_keeps_loci(founders):
    packet = read_compressed(SETUP / 'rehearsal_assessment.json.gz')
    data = read_compressed(SETUP / 'fixture_assessment.json.gz')
    states, decisions = transition(founders, data, packet['results'])
    assert states == packet['after']
    assert all(len(s['coverage_archive']) == 32 for s in states)
    # Force an actually archived nonprotected individual out of a synthetic live
    # state, then exercise the recovery path without making a biological claim.
    s = deepcopy(states[0])
    protected = {r['id'] for r in s['protected']}
    a = next(a for a in s['coverage_archive'] if a['item']['id'] not in protected)
    identity = a['item']['id']
    replacement = deepcopy(a['item'])
    replacement['id'] = 'synthetic/replacement'
    s['population'] = [replacement if r['id'] == identity else r for r in s['population']]
    s['gene_ids'][replacement['id']] = s['gene_ids'].pop(identity)
    s['families'][replacement['id']] = s['families'].pop(identity)
    s['reinject'] = [identity]
    r = dict(case='empty', optimal=False, valid=False, no_path=False, reachable=True,
             status='quiescent', partial=0., reads=0, dispatches=0,
             exposure_checks=0, mask='00')
    rows = {i['id']:[r] for i in s['population']}
    new, event = reproduce(s, rows, {'empty':dict(family='corridor')})
    assert_population(new)
    assert new['gene_ids'][identity] == a['gene_ids']
    assert new['families'][identity] == a['family']
    assert [identity, 'assessed_coverage_archive'] in event['survivors']
