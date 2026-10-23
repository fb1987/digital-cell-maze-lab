"""Preserve the M25 export failure without resuming or modifying its journal."""
import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign_store import writer_lock, unpacked
from maze_evolution.referenced_campaign_store import Journal, load_layouts, write_reference
from maze_evolution.skill_integration import ROOT, OUT, RUN, readz


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def size():
    return sum(p.stat().st_size for base in (RUN, OUT)
               for p in base.rglob('*') if p.is_file())


def main():
    config = json.loads((OUT / 'config.json').read_text())
    packet = OUT / 'failures/export_001'
    backup = RUN / 'backups/export_failure_001.sqlite'
    assert not packet.exists() and not backup.exists()
    status = json.loads((RUN / 'workflow_status.json').read_text())
    assert status['state'] == 'failed' and status['phase'] == 'search_001'
    assert not (OUT / 'confirmation.json.gz').exists()
    assert not (OUT / 'session.json').exists()
    with writer_lock(RUN / 'workflow'), writer_lock(RUN):
        source = RUN / 'campaign.sqlite'
        reserve = source.stat().st_size + 64 * 2**20
        assert size() + reserve < config['storage_bytes']
        assert shutil.disk_usage(RUN).free - reserve >= config['disk_free_floor_bytes']
        registration = json.loads((OUT / 'registration.json').read_text())
        assert all(sha(ROOT / p) == h for p, h in registration['files'].items())
        src = sqlite3.connect(f'file:{source}?mode=ro', uri=True)
        assert src.execute('pragma integrity_check').fetchone() == ('ok',)
        settings = {k: unpacked(v) for k, v in src.execute('select key,value from settings')}
        assert not settings.get('finished') and settings['nomination_stop']['reason'] == 'wall_target'
        assert settings['active_session_epoch'] is None
        reference = settings['layout_base']
        assert sha(reference['path']) == reference['sha256']
        base = load_layouts(Path(reference['path']))
        assert len(base) == reference['count'] == 3742313
        j = Journal.__new__(Journal)
        j.db, j.directory, j.base = src, RUN, base
        chain = j.verify_chain()
        assert not j.pending()
        states = j.state()
        assert all(s['generation'] == 562 and s['assessment_generation'] == 562 for s in states)
        assert readz(OUT / 'final_states.json.gz') == states
        choices = readz(OUT / 'choices.json.gz')
        assert choices['chain'] == chain and len(choices['comparisons']) == 18
        for comparison in choices['comparisons']:
            state = next(s for s in states if s['name'] == comparison['condition'])
            assert comparison['child'] == state['nominees'][comparison['rank']]['id']
        source_before = sha(source)
        backup.parent.mkdir(exist_ok=True)
        with backup.open('xb'):
            pass
        dst = sqlite3.connect(backup)
        src.backup(dst)
        assert dst.execute('pragma integrity_check').fetchone() == ('ok',)
        tables = [r[0] for r in src.execute("select name from sqlite_master where type='table' order by name")]
        assert tables == [r[0] for r in dst.execute("select name from sqlite_master where type='table' order by name")]
        counts = {}
        for table in tables:
            assert table in ('settings', 'stages', 'tasks', 'states', 'layouts')
            order = '1' if table == 'layouts' else '1,2'
            a = src.execute(f'SELECT * FROM {table} ORDER BY {order}')
            b = dst.execute(f'SELECT * FROM {table} ORDER BY {order}')
            count = 0
            while True:
                x, y = a.fetchmany(128), b.fetchmany(128)
                assert x == y, table
                count += len(x)
                if not x:
                    break
            counts[table] = count
        dst.close()
        assert sha(source) == source_before
        packet.mkdir(parents=True)
        copied = {}
        paths = [RUN / n for n in ('workflow_status.json', 'workflow_001.log', 'search_001.log')]
        paths += [OUT / n for n in ('choices.json.gz', 'ancestry.json.gz', 'final_states.json.gz',
                                   'registration.json', 'registered_exclusions.json')]
        for path in paths:
            target = packet / path.name
            with target.open('xb') as f:
                f.write(path.read_bytes())
            assert sha(target) == sha(path)
            copied[str(path.relative_to(ROOT))] = sha(target)
        layouts = j.layouts()
        write_reference(packet / 'search_exclusions.json', ROOT / config['layout_base_manifest'], layouts)
        assert load_layouts(packet / 'search_exclusions.json') == layouts
        stages = list(src.execute('select n,kind,generation,complete from stages order by n desc limit 3'))
        task_status = dict(src.execute('select status,count(*) from tasks group by status'))
        src.close()
        assert size() < config['storage_bytes']
        assert shutil.disk_usage(RUN).free >= config['disk_free_floor_bytes']
        evidence = dict(
            status='preserved_failed_export_not_repaired', phase='M25',
            generations=dict(start=243, ending=562, new=319), stage_chain=chain,
            latest_stages=stages, task_status_counts=task_status, pending_tasks=0,
            usage=settings['usage'], nomination_stop=settings['nomination_stop'],
            charged_elapsed_seconds=settings['elapsed_search_seconds'],
            original_finished_flag=settings.get('finished', False),
            original_journal=dict(path=str(source.relative_to(ROOT)), sha256=source_before,
                                  bytes=source.stat().st_size, unchanged=True, integrity_check='ok'),
            backup=dict(path=str(backup.relative_to(ROOT)), sha256=sha(backup),
                        bytes=backup.stat().st_size, integrity_check='ok',
                        all_table_contents_match=True, table_row_counts=counts,
                        requires_immutable_layout_base=True),
            layout_reference=reference, initial_layouts=len(base), all_layouts=len(layouts),
            search_delta_layouts=len(layouts - base), copied_files=copied,
            source_hashes_verified=len(registration['files']),
            frozen_states_match_checkpoint=True, all_18_choices_match_assessment=True,
            selection_mutation_rng_native_audit_completed=False,
            independent_confirmation_generated=False, search_resumed=False,
            diagnosis='Registered config/journal use registered_exclusions.json; write_layouts expects absent exclusions.json. Rehearsals explicitly created that compatibility manifest, production did not.',
            proposed_scope='Export-only compatibility manifest and completion from exact stage339; preserve failed records/partial exports, no evolution or reselection, publish choices then existing audits/confirmation only after protocol approval.',
            storage_bytes=size(), disk_free_bytes=shutil.disk_usage(RUN).free)
        with (packet / 'preservation.json').open('x') as f:
            json.dump(evidence, f, indent=2)
            f.write('\n')
        print(json.dumps(evidence, indent=2), flush=True)


if __name__ == '__main__':
    main()
