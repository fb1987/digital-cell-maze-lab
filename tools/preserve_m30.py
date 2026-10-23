"""Guarded SQLite-API backup plus existing-layout proof for M30."""
import json,shutil,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.information_flow_m30 import ROOT,OUT,RUN,PRIOR,check,prior_check,readz,writej,sha,storage
from maze_evolution.deep_campaign_store import writer_lock
from maze_evolution.referenced_campaign_store import load_layouts,write_reference
from maze_evolution.foundation_data import layout_hash,transform_maze
from maze_evolution.deep_campaign_data import cases_from_manifest


def main():
    config=check();assert not (OUT/'preservation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    assert json.loads((OUT/'audit.json').read_text())['status']=='PASS'
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes']
    previous=load_layouts(PRIOR/'whole_layout_exclusions.json');data=readz(OUT/'cases.json.gz');cases=cases_from_manifest(data['mazes'])
    observed={layout_hash(transform_maze(o.maze,p)) for o in cases.values() for p in range(8)}
    old={layout_hash(transform_maze(cases[cid].maze,p)) for cid in data['queries']['old'] for p in range(8)}
    assert old<=previous
    fixture=set(json.loads((ROOT/'results/information_flow_m30_preparation/tests.json').read_text())['algebra_only_fixture_layouts'])
    all_layouts=previous|observed|fixture|set(data['generated_layouts'])
    write_reference(OUT/'whole_layout_exclusions.json',PRIOR/'whole_layout_exclusions.json',all_layouts)
    directory=RUN/'evaluation';source=directory/'campaign.sqlite';backup=directory/'backups/completed.sqlite'
    with writer_lock(directory):
        src=sqlite3.connect(f'file:{source}?mode=ro',uri=True);src.execute('PRAGMA query_only=ON');src.execute('BEGIN')
        assert src.execute('PRAGMA integrity_check').fetchone()==('ok',)
        assert src.execute("select count(*) from jobs where status!='done'").fetchone()==(0,)
        rec=dict(source=dict(path=str(source.relative_to(ROOT)),bytes=source.stat().st_size,sha256=sha(source)))
        need=source.stat().st_size+16*2**20
        if storage()+need>=config['storage_bytes'] or shutil.disk_usage(RUN).free-need<config['disk_free_floor_bytes']:
            rec['backup']=dict(status='blocked_by_registered_bound',required_bytes=need)
        else:
            assert not backup.exists();backup.parent.mkdir(exist_ok=True);dst=sqlite3.connect(backup);src.backup(dst)
            assert dst.execute('PRAGMA integrity_check').fetchone()==('ok',);counts={}
            for table in ('settings','jobs'):
                aa=src.execute(f'select * from {table} order by 1,2');bb=dst.execute(f'select * from {table} order by 1,2');count=0
                while True:
                    a=aa.fetchmany(8);b=bb.fetchmany(8);assert a==b,table
                    if not a:break
                    count+=len(a)
                counts[table]=count
            dst.close();rec['backup']=dict(status='verified',path=str(backup.relative_to(ROOT)),bytes=backup.stat().st_size,sha256=sha(backup),all_tables_match=True,table_counts=counts)
        src.close()
    assert storage()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status=rec['backup']['status'],journal=rec,whole_layouts=len(all_layouts),new_layouts=len(all_layouts-previous),
        inherited_layouts=len(previous),all_old_case_pose_layouts_already_excluded=True,queried_orbit_hashes=len(observed),new_template_hashes=len(data['generated_layouts']),algebra_fixture_hashes=len(fixture),immutable_bases_required=True,
        storage_bytes=storage(),disk_free_bytes=shutil.disk_usage(RUN).free,source_priors=prior_check(),all_old_science_unchanged=True))


if __name__=='__main__':main()
