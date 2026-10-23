"""Approved M25 A1: finish exports from stage339; never run evolution."""
import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution import skill_integration as m
from maze_evolution.deep_campaign_store import writer_lock, unpacked, packed
from maze_evolution.referenced_campaign_store import Journal, load_layouts, write_reference
from maze_evolution.routing_transfer import canonical

A1 = m.OUT / 'recovery_a1'
FAILURE = m.OUT / 'failures/export_001'
STATUS = m.RUN / 'recovery_a1_workflow_status.json'
ARTIFACTS = ('choices.json.gz', 'ancestry.json.gz', 'final_states.json.gz')


def json_x(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')


def verify_files(files):
    for p, h in files.items():
        assert m.sha(m.ROOT / p) == h, p


def check_a1():
    config = m.check()
    registration = json.loads((A1 / 'registration.json').read_text())
    assert registration['user_approved'] and registration['additional_evolution_rounds'] == 0
    verify_files(registration['files'])
    m.pushed(A1 / 'registration.json')
    return config


def check_failed_packet():
    seal = json.loads((FAILURE / 'failure_seal.json').read_text())
    verify_files(seal['files'])
    backup = seal['local_records']
    assert m.sha(m.ROOT / backup['path']) == backup['sha256']
    evidence = json.loads((FAILURE / 'preservation.json').read_text())
    for name in ARTIFACTS:
        assert m.sha(m.OUT / name) == m.sha(FAILURE / name)
    assert m.sha(m.RUN / 'workflow_status.json') == evidence['copied_files']['runs/skill_integration_m25/workflow_status.json']
    return evidence


def captured_checkpoint(guard):
    """Replay serialization into memory and verify the already written exports."""
    db = sqlite3.connect(f'file:{m.RUN}/campaign.sqlite?mode=ro', uri=True)
    db.execute('BEGIN')
    settings = {k: unpacked(v) for k, v in db.execute('select key,value from settings')}
    ref = settings['layout_base']
    assert m.sha(Path(ref['path'])) == ref['sha256']
    base = load_layouts(Path(ref['path']))
    assert len(base) == ref['count'] == 3742313
    j = Journal.__new__(Journal)
    j.db, j.directory, j.base = db, m.RUN, base
    chain = j.verify_chain()
    assert settings['latest'] == 339 and not settings.get('finished') and not j.pending()
    assert settings['active_session_epoch'] is None
    assert settings['nomination_stop']['generation'] == 562
    assert settings['nomination_stop']['reason'] == 'wall_target'
    states = j.state()
    assert all(s['generation'] == s['assessment_generation'] == 562 for s in states)
    frozen = {}
    original_z, original_layouts = m.writez, m.write_layouts
    try:
        m.writez = lambda path, value: frozen.__setitem__(Path(path), canonical(value))
        m.write_layouts = lambda name, values: frozen.__setitem__(m.OUT / (name + '.json'), set(values))
        m.freeze(j, guard=guard)
    finally:
        m.writez, m.write_layouts = original_z, original_layouts
    assert set(frozen) == {m.OUT / n for n in ARTIFACTS} | {m.OUT / 'search_exclusions.json'}
    for name in ARTIFACTS:
        assert m.readz(m.OUT / name) == frozen[m.OUT / name], name
    layouts = frozen[m.OUT / 'search_exclusions.json']
    assert layouts == j.layouts() and len(layouts) == 3951225 and base <= layouts
    db.close()
    return settings, chain, base, layouts


def create_layout_exports(target, base, layouts):
    assert not (target / 'exclusions.json').exists()
    assert not (target / 'search_exclusions.json').exists()
    write_reference(target / 'exclusions.json', m.ROOT / m.CONFIG['layout_base_manifest'], base)
    assert load_layouts(target / 'exclusions.json') == base
    old = m.OUT
    try:
        m.OUT = target
        m.write_layouts('search_exclusions', layouts)
    finally:
        m.OUT = old
    assert load_layouts(target / 'search_exclusions.json') == layouts


def completion_values(settings, recovery_elapsed, config):
    assert not settings.get('finished') and settings['active_session_epoch'] is None
    charged = settings['elapsed_search_seconds'] + recovery_elapsed
    assert 0 <= recovery_elapsed and charged < config['session_wall_seconds']
    return dict(finished=True, elapsed_search_seconds=charged)


def rehearse():
    config = m.check()
    evidence = check_failed_packet()
    assert m.sha(m.RUN / 'campaign.sqlite') == evidence['original_journal']['sha256']
    target = A1 / 'rehearsal'
    assert not target.exists()
    target.mkdir(parents=True)
    started = m.clock()
    remaining = config['session_wall_seconds'] - evidence['charged_elapsed_seconds']
    guard = lambda: m.resource_reason(m.RUN, dict(config, session_wall_seconds=remaining), started)
    with writer_lock(m.RUN / 'workflow'), writer_lock(m.RUN):
        settings, chain, base, layouts = captured_checkpoint(guard)
        create_layout_exports(target, base, layouts)
        good = completion_values(settings, m.elapsed(started), config)
        rejected = []
        for name, value, elapsed in (
            ('already_finished', dict(settings, finished=True), 0),
            ('active_session', dict(settings, active_session_epoch=1), 0),
            ('exhausted_original_allowance', settings, remaining + 1),
        ):
            try:
                completion_values(value, elapsed, config)
            except AssertionError:
                rejected.append(name)
            else:
                raise AssertionError(name)
        try:
            create_layout_exports(target, base, layouts)
        except AssertionError:
            rejected.append('existing_exports')
        else:
            raise AssertionError('Existing export overwritten')
        assert guard() is None
    assert m.sha(m.RUN / 'campaign.sqlite') == evidence['original_journal']['sha256']
    json_x(A1 / 'rehearsal.json', dict(status='PASS', chain=chain,
        exact_existing_exports=True, layouts=len(layouts), base_layouts=len(base),
        journal_byte_hash_unchanged=True, new_inference_calls=0, cases_generated=0,
        metadata_only_fixture=good, rejected=rejected, wall_seconds=m.elapsed(started)))
    print('A1 rehearsal PASS; journal unchanged; zero inference/case generation', flush=True)


def complete_export():
    started = m.clock()
    config = check_a1()
    evidence = check_failed_packet()
    before_hash = m.sha(m.RUN / 'campaign.sqlite')
    assert before_hash == evidence['original_journal']['sha256']
    assert not (A1 / 'export_receipt.json').exists() and not (m.OUT / 'session.json').exists()
    remaining = config['session_wall_seconds'] - evidence['charged_elapsed_seconds']
    guard = lambda: m.resource_reason(m.RUN, dict(config, session_wall_seconds=remaining), started)
    settings, chain, base, layouts = captured_checkpoint(guard)
    assert chain == evidence['stage_chain'] and settings['usage'] == evidence['usage']
    assert guard() is None
    create_layout_exports(m.OUT, base, layouts)
    # Compare every scientific row with the frozen failure backup before changing
    # the two completion/accounting settings. No state/receipt/layout edits occur.
    src = sqlite3.connect(m.RUN / 'campaign.sqlite')
    old = sqlite3.connect(f"file:{m.ROOT / evidence['backup']['path']}?mode=ro", uri=True)
    tables = []
    for table in ('stages', 'tasks', 'states', 'layouts'):
        order = '1' if table == 'layouts' else '1,2'
        a = src.execute(f'SELECT * FROM {table} ORDER BY {order}')
        b = old.execute(f'SELECT * FROM {table} ORDER BY {order}')
        while True:
            x, y = a.fetchmany(128), b.fetchmany(128)
            assert x == y, table
            if not x:
                break
        tables.append(table)
    old.close()
    assert {k: unpacked(v) for k, v in src.execute('select key,value from settings')} == settings
    assert guard() is None
    updates = completion_values(settings, m.elapsed(started), config)
    with src:
        for key, value in updates.items():
            src.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, packed(value)))
    after = {k: unpacked(v) for k, v in src.execute('select key,value from settings')}
    assert after == dict(settings, **updates)
    src.close()
    assert guard() is None
    session = dict(status='complete', reason=None, stop=settings['nomination_stop'],
        generation=562, new_rounds=319, usage=settings['usage'], chain=chain,
        rss_peak_bytes=max(3512418304, m.shared._peak_rss),
        wall_seconds=updates['elapsed_search_seconds'],
        recovery='User-approved export-only A1; no evolutionary continuation',
        original_recorded_elapsed_seconds=evidence['charged_elapsed_seconds'],
        recovery_elapsed_at_metadata_commit=m.elapsed(started),
        paused_interval_excluded='Original active_session_epoch is None; user decision interval is not active computation',
        monotonic_seconds=None, calendar_seconds=None,
        clock_limitation='Original separate clocks were not exported before failure; charged original MAX elapsed plus recovery MAX elapsed, with full recovery tail in export_receipt.json')
    json_x(m.OUT / 'session.json', session)
    for name in ARTIFACTS:
        assert m.sha(m.OUT / name) == m.sha(FAILURE / name)
    after_hash = m.sha(m.RUN / 'campaign.sqlite')
    assert guard() is None
    json_x(A1 / 'export_receipt.json', dict(status='complete',
        original_journal_sha256=before_hash, completed_journal_sha256=after_hash,
        stage_chain=chain, scientific_tables_compared=tables,
        unchanged_scientific_tables=True, changed_settings=updates,
        frozen_exports_unchanged={n:m.sha(m.OUT / n) for n in ARTIFACTS},
        layouts=len(layouts), base_layouts=len(base),
        recovery_wall_seconds=m.elapsed(started),
        total_original_plus_recovery_seconds=evidence['charged_elapsed_seconds'] + m.elapsed(started),
        rss_peak_bytes=m.shared._peak_rss, new_inference_calls=0, cases_generated=0,
        evolution_rounds_added=0, independently_confirmed=False))
    print('A1 exports complete; choices unchanged; search not rerun', flush=True)


def ready_status():
    """Postprocessing accepts only the separately audited approved recovery."""
    verify_files(json.loads((A1 / 'registration.json').read_text())['files'])
    status = json.loads(STATUS.read_text())
    assert status['state'] == 'audited_ready_for_report'
    assert json.loads((m.RUN / 'workflow_status.json').read_text())['state'] == 'failed'
    assert json.loads((A1 / 'export_receipt.json').read_text())['evolution_rounds_added'] == 0
    for name in ('search', 'final'):
        assert json.loads((m.OUT / (name + '_audit.json')).read_text())['status'] == 'PASS'
    return STATUS, status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['rehearse', 'export', 'audit_search', 'final', 'analyze', 'audit_final'])
    action = parser.parse_args().action
    if action == 'rehearse':
        rehearse()
        return
    with writer_lock(m.RUN):
        if action == 'export':
            complete_export()
        else:
            check_a1()
            from maze_evolution import skill_integration_analysis as analysis
            getattr(analysis, action)()


if __name__ == '__main__':
    main()
