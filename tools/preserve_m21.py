"""M21 guarded SQLiteAPI backup and immutable ledger reference; originals untouched."""
import sys,sqlite3,shutil,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.readout_causality import ROOT,OUT,RUN,check,readz,writej,sha,load_layouts
from maze_evolution.deep_campaign_store import writer_lock,unpacked
from maze_evolution.referenced_campaign_store import Journal,write_reference

def size():return sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file())

def main():
    config=check();assert not (OUT/'preservation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    for f in ('audit.json','trace_audit.json'):assert json.loads((OUT/f).read_text())['status']=='PASS'
    assert not readz(OUT/'panel.json.gz')['new_layouts']
    layouts=load_layouts(OUT/'exclusions.json')
    assert size()+16*2**20<config['storage_bytes'] and shutil.disk_usage(RUN).free-16*2**20>=config['disk_free_floor_bytes']
    write_reference(OUT/'whole_layout_exclusions.json',OUT/'exclusions.json',layouts)
    d=RUN/'evaluation';source=d/'campaign.sqlite';backup=d/'backups/completed.sqlite'
    with writer_lock(d):
        src=sqlite3.connect(f'file:{source}?mode=ro',uri=True);assert src.execute('pragma integrity_check').fetchone()==('ok',)
        assert not src.execute('select hash from layouts').fetchall()
        reference=unpacked(src.execute("select value from settings where key='layout_base'").fetchone()[0])
        assert sha(Path(reference['path']))==reference['sha256'] and len(layouts)==reference['count']
        j=Journal.__new__(Journal);j.db=src;j.directory=d;j.base=layouts;chain=j.verify_chain();assert not j.pending()
        needed=source.stat().st_size+16*2**20
        entry=dict(journal=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),bytes=source.stat().st_size),chain=chain)
        if size()+needed>=config['storage_bytes'] or shutil.disk_usage(RUN).free-needed<config['disk_free_floor_bytes']:
            entry['backup']=dict(status='blocked_by_registered_bound',required_bytes=needed)
        else:
            backup.parent.mkdir(exist_ok=True);assert not backup.exists();dst=sqlite3.connect(backup);src.backup(dst)
            assert dst.execute('pragma integrity_check').fetchone()==('ok',)
            for table in ('settings','stages','tasks','states','layouts'):
                order='1' if table=='layouts' else '1,2'
                a=src.execute(f'select * from {table} order by {order}');b=dst.execute(f'select * from {table} order by {order}')
                while True:
                    x=a.fetchmany(64);y=b.fetchmany(64);assert x==y,table
                    if not x:break
            dst.close();entry['backup']=dict(status='verified',path=str(backup.relative_to(ROOT)),sha256=sha(backup),bytes=backup.stat().st_size,all_table_contents_match=True)
        src.close()
    assert load_layouts(OUT/'whole_layout_exclusions.json')==layouts
    assert size()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status=entry['backup']['status'],evaluation=entry,new_layouts=0,whole_layouts=len(layouts),
        storage_bytes=size(),disk_free_bytes=shutil.disk_usage(RUN).free,immutable_base_ledgers_required=True))

if __name__=='__main__':main()
