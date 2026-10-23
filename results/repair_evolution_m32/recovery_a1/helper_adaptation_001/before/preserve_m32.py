"""M32 verified backups and complete exclusions, never overwrite closed artifacts."""
import json,shutil,sqlite3,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_evolution_m32 import *

def main():
    config=check();assert not (OUT/'preservation.json').exists();assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    for name in ('source','search','final'):assert json.loads((OUT/(name+'_audit.json')).read_text())['status']=='PASS'
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes']
    previous=load_layouts(OUT/'exclusions.json');source=readz(OUT/'source_panel.json.gz');final=readz(OUT/'fresh_panel.json.gz')
    for name,d in (('source',source),('final',final)):assert set(d['new_layouts'])==phase_observations(name)==phase_observations(name,True)
    source_new=set(source['new_layouts']);final_new=set(final['new_layouts']);assert not previous&source_new and not (previous|source_new)&final_new
    write_reference(OUT/'whole_layout_exclusions.json',OUT/'exclusions.json',previous|source_new|final_new);records={}
    for name in ('source','search','final'):
        directory=RUN/name;path=directory/'campaign.sqlite';backup=directory/'backups/completed.sqlite'
        with writer_lock(directory):
            src=sqlite3.connect(f'file:{path}?mode=ro',uri=True);src.execute('PRAGMA query_only=ON');src.execute('BEGIN');assert src.execute('PRAGMA integrity_check').fetchone()==('ok',)
            expected=source_new if name=='source' else final_new if name=='final' else set()
            assert {r[0] for r in src.execute('select hash from layouts')}==expected
            ref=unpacked(src.execute("select value from settings where key='layout_base'").fetchone()[0]);assert sha(Path(ref['path']))==ref['sha256']
            base=load_layouts(Path(ref['path']));assert len(base)==ref['count']
            j=Journal.__new__(Journal);j.db=src;j.directory=directory;j.base=base;chain=j.verify_chain();assert not j.pending()
            rec=dict(journal=dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=sha(path)),chain=chain)
            needed=path.stat().st_size+16*2**20
            if storage()+needed>=config['storage_bytes'] or shutil.disk_usage(RUN).free-needed<config['disk_free_floor_bytes']:rec['backup']=dict(status='blocked_by_registered_bound',required_bytes=needed)
            else:
                assert not backup.exists();backup.parent.mkdir(exist_ok=True);dst=sqlite3.connect(backup);src.backup(dst);assert dst.execute('PRAGMA integrity_check').fetchone()==('ok',);counts={}
                for table in ('settings','stages','tasks','states','layouts'):
                    order='1' if table=='layouts' else '1,2';a=src.execute(f'select * from {table} order by {order}');b=dst.execute(f'select * from {table} order by {order}');count=0
                    while True:
                        x=a.fetchmany(16);y=b.fetchmany(16);assert x==y,table
                        if not x:break
                        count+=len(x)
                    counts[table]=count
                dst.close();rec['backup']=dict(status='verified',path=str(backup.relative_to(ROOT)),bytes=backup.stat().st_size,sha256=sha(backup),all_tables_match=True,table_counts=counts)
            src.close();records[name]=rec
    assert load_layouts(OUT/'whole_layout_exclusions.json')==previous|source_new|final_new
    assert storage()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status='verified' if all(r['backup']['status']=='verified' for r in records.values()) else 'backup_blocked',journals=records,whole_layouts=len(previous|source_new|final_new),initial_layouts=len(previous),source_layouts=len(source_new),final_layouts=len(final_new),source_priors=prior_check(),immutable_bases_required=True,all_generated_rejected_unqueried_orbits_preserved=True,storage_bytes=storage(),disk_free_bytes=shutil.disk_usage(RUN).free))
if __name__=='__main__':
    try:main()
    except BaseException:
        writej(OUT/f'preservation_failure_{time.time_ns()}.json',dict(traceback=traceback.format_exc()));raise
