"""New M31 postprocessing helper; never rewrites a scientific output or old seal."""
import json,shutil,sqlite3,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import ROOT,OUT,RUN,check,prior_check,readz,writej,sha,storage
from maze_evolution.deep_campaign_store import writer_lock,unpacked
from maze_evolution.referenced_campaign_store import Journal,load_layouts,write_reference
from maze_evolution.transfer_retention_data import observed_hashes


def main():
    config=check();assert not (OUT/'preservation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    for name in ('development','trace','final'):assert json.loads((OUT/(name+'_audit.json')).read_text())['status']=='PASS'
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes']
    previous=load_layouts(OUT/'exclusions.json');fresh=readz(OUT/'fresh_panel.json.gz');new=set(fresh['new_layouts'])
    assert new==observed_hashes(RUN/'science_generation_layouts.jsonl')==observed_hashes(RUN/'audit_generation_layouts.jsonl')
    assert not new&previous
    assert storage()+16*2**20<config['storage_bytes'] and shutil.disk_usage(RUN).free-16*2**20>=config['disk_free_floor_bytes']
    write_reference(OUT/'whole_layout_exclusions.json',OUT/'exclusions.json',previous|new)
    records={}
    for name in ('development','trace','final'):
        directory=RUN/name;source=directory/'campaign.sqlite';backup=directory/'backups/completed.sqlite'
        with writer_lock(directory):
            src=sqlite3.connect(f'file:{source}?mode=ro',uri=True);src.execute('PRAGMA query_only=ON');src.execute('BEGIN')
            assert src.execute('PRAGMA integrity_check').fetchone()==('ok',)
            assert {r[0] for r in src.execute('select hash from layouts')}==(new if name=='final' else set())
            ref=unpacked(src.execute("select value from settings where key='layout_base'").fetchone()[0]);assert sha(Path(ref['path']))==ref['sha256'] and ref['count']==len(previous)
            j=Journal.__new__(Journal);j.db=src;j.directory=directory;j.base=previous
            chain=j.verify_chain();assert not j.pending() and j.get('latest')==0
            rec=dict(journal=dict(path=str(source.relative_to(ROOT)),bytes=source.stat().st_size,sha256=sha(source)),chain=chain)
            needed=source.stat().st_size+16*2**20
            if storage()+needed>=config['storage_bytes'] or shutil.disk_usage(RUN).free-needed<config['disk_free_floor_bytes']:
                rec['backup']=dict(status='blocked_by_registered_bound',required_bytes=needed)
            else:
                assert not backup.exists();backup.parent.mkdir(exist_ok=True);dst=sqlite3.connect(backup);src.backup(dst)
                assert dst.execute('PRAGMA integrity_check').fetchone()==('ok',);counts={}
                for table in ('settings','stages','tasks','states','layouts'):
                    order='1' if table=='layouts' else '1,2';a=src.execute(f'select * from {table} order by {order}');b=dst.execute(f'select * from {table} order by {order}');count=0
                    while True:
                        x=a.fetchmany(32);y=b.fetchmany(32);assert x==y,table
                        if not x:break
                        count+=len(x)
                    counts[table]=count
                dst.close();rec['backup']=dict(status='verified',path=str(backup.relative_to(ROOT)),bytes=backup.stat().st_size,sha256=sha(backup),all_tables_match=True,table_counts=counts)
            src.close();records[name]=rec
    assert load_layouts(OUT/'whole_layout_exclusions.json')==previous|new
    assert storage()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status='verified' if all(r['backup']['status']=='verified' for r in records.values()) else 'backup_blocked',journals=records,
        initial_layouts=len(previous),new_layouts=len(new),whole_layouts=len(previous|new),immutable_bases_required=True,
        all_generated_rejected_unqueried_orbits_preserved=True,old_histories_unchanged=True,source_priors=prior_check(),storage_bytes=storage(),disk_free_bytes=shutil.disk_usage(RUN).free))
    print('M31 preservation complete',len(previous|new),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException:
        with (OUT/f'preservation_failure_{time.time_ns()}.json').open('x') as f:json.dump(dict(traceback=traceback.format_exc()),f,indent=2)
        raise
