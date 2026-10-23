"""Preserve the M32 export failure, never resume or alter scientific history."""
import json,shutil,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_evolution_m32 import *

PACKET=OUT/'failures/export_001'

def main():
    config=check();assert not PACKET.exists();status=json.loads((RUN/'workflow_status.json').read_text())
    assert status['state']=='failed' and status['phase']=='search'
    assert all(not (OUT/n).exists() for n in ('choices.json.gz','ancestry.json.gz','final_states.json.gz','search_session.json','fresh_panel.json.gz','choice_freeze.json'))
    PACKET.mkdir(parents=True);copied={}
    paths=[RUN/'search_001.log',RUN/'workflow_001.log',RUN/'workflow_status.json',ROOT/'maze_evolution/repair_evolution_m32.py',ROOT/'tools/run_m32_workflow.py',ROOT/'docs/REPAIR_EVOLUTION_M32.md',OUT/'registration.json',OUT/'launch.json',OUT/'source_session.json',OUT/'source_audit.json',*OUT.glob('search_failure_*.json')]
    for k,p in enumerate(paths):
        target=PACKET/f'{k:02d}_{p.name}';shutil.copy2(p,target);copied[str(p.relative_to(ROOT))]=dict(copy=str(target.relative_to(ROOT)),sha256=sha(p))
        assert sha(target)==sha(p)
    initial=load_layouts(OUT/'exclusions.json');new=set(readz(OUT/'source_panel.json.gz')['new_layouts'])
    assert new==phase_observations('source')==phase_observations('source',True)
    write_reference(PACKET/'whole_layout_exclusions.json',OUT/'exclusions.json',initial|new)
    journals={}
    with writer_lock(RUN/'workflow'):
        for name in ('source','search'):
            directory=RUN/name;path=directory/'campaign.sqlite';backup=directory/'backups/failure_export_001.sqlite'
            with writer_lock(directory):
                assert not backup.exists();needed=path.stat().st_size+16*2**20
                assert storage()+needed<config['storage_bytes'] and shutil.disk_usage(RUN).free-needed>=config['disk_free_floor_bytes']
                before=sha(path);src=sqlite3.connect(f'file:{path}?mode=ro',uri=True);src.execute('PRAGMA query_only=ON');src.execute('BEGIN')
                assert src.execute('PRAGMA integrity_check').fetchone()==('ok',)
                j=Journal.__new__(Journal);j.db=src;j.directory=directory;chain=j.verify_chain();assert j.pending() is None
                assert src.execute("select count(*) from tasks where status!='done'").fetchone()[0]==0
                backup.parent.mkdir(exist_ok=True);dst=sqlite3.connect(backup);src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()==('ok',);tables={}
                for table in ('settings','stages','tasks','states','layouts'):
                    order='1' if table=='layouts' else '1,2';a=src.execute(f'select * from {table} order by {order}');b=dst.execute(f'select * from {table} order by {order}');count=0
                    while True:
                        aa=a.fetchmany(16);bb=b.fetchmany(16);assert aa==bb,table
                        if not aa:break
                        count+=len(aa)
                    tables[table]=count
                usage=j.get('usage');assert usage['uncertain_attempts']==0
                state=j.state();j.close();dst.close();assert sha(path)==before
                journals[name]=dict(original=dict(path=str(path.relative_to(ROOT)),sha256=before,bytes=path.stat().st_size),backup=dict(path=str(backup.relative_to(ROOT)),sha256=sha(backup),bytes=backup.stat().st_size),all_tables_match=True,tables=tables,chain=chain,usage=usage,generation=state[0]['generation'] if name=='search' else None)
    steps=status['steps'];search_started=steps[1]['ended_epoch'];upper=steps[2]['ended_epoch']-search_started
    writej(PACKET/'preservation.json',dict(status='verified_failure_preserved',copied_files=copied,journals=journals,all_completed_receipts_preserved=True,no_pending_tasks=True,prior_hashes=prior_check(),
        source_audit_PASS=True,search_audit_not_run=True,final_cases_generated=0,original_search_wall_upper_seconds=upper,original_search_last_completed_assessment_elapsed_seconds=1649.1994539169827,
        timing_note='Conservative parent workflow interval from completion of preceding source audit to observed search subprocess exit, including startup/export failure tail. No fabricated unrecorded internal timer.',
        search_hard_remaining_upper_charge_seconds=config['session_wall_seconds']-upper,initial_layouts=len(initial),source_new_layouts=len(new),all_layouts=len(initial|new),storage_bytes=storage(),disk_free_bytes=shutil.disk_usage(RUN).free))
    files={str(p.relative_to(ROOT)):sha(p) for p in PACKET.rglob('*') if p.is_file()}
    local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log','.jsonl') or p.name=='workflow_status.json')}
    writej(PACKET/'failure_seal.json',dict(status='failed_export_preserved_not_resumed',files=files,local_records=local,registered_files_unchanged=True,prior_hashes=prior_check()))
    print('Failure packet sealed; originals and ALL-table backups verified',len(files),len(local),flush=True)
if __name__=='__main__':main()
