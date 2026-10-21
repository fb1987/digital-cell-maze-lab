"""Post-audit M13 backup/exclusion export; never overwrites records or guards."""
import sys,json,sqlite3,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_scope import ROOT,OUT,RUN,check,readz,writej,sha,load_layouts,write_layouts
from maze_evolution.deep_campaign_store import writer_lock
from maze_evolution.referenced_campaign_store import Journal

def size():return sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file())
def same_table(src,dst,table):
    order='1' if table=='layouts' else '1,2'
    a=src.execute(f'SELECT * FROM {table} ORDER BY {order}');b=dst.execute(f'SELECT * FROM {table} ORDER BY {order}')
    while True:
        x=a.fetchmany(128);y=b.fetchmany(128);assert x==y,table
        if not x:return

def main():
    config=check();assert not (OUT/'preservation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    for name in ('search','final'):assert json.loads((OUT/f'{name}_audit.json').read_text())['status']=='PASS'
    initial=load_layouts(OUT/'exclusions.json');search=load_layouts(OUT/'search_exclusions.json');assert initial<=search
    new=set(readz(OUT/'confirmation.json.gz')['new_layouts']);assert not search&new;union=search|new
    stages={};directories=[('search',RUN,search),('final',RUN/'final',union)]
    # Reserve export/report room before any backup; missing space blocks backup,
    # not preservation of original scientific records.
    reserve=24*2**20
    assert size()+reserve<config['storage_bytes'] and shutil.disk_usage(RUN).free-reserve>=config['disk_free_floor_bytes'],'No room for exclusion export; preserve originals and report'
    write_layouts('whole_layout_exclusions',union)
    for name,d,layouts in directories:
        source=d/'campaign.sqlite';backup=d/'backups/completed.sqlite'
        with writer_lock(d):
            src=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
            assert src.execute('pragma integrity_check').fetchone()==('ok',)
            base=load_layouts(Path(json.loads(__import__('zlib').decompress(src.execute("select value from settings where key='layout_base'").fetchone()[0]))['path']))
            assert base|{r[0] for r in src.execute('select hash from layouts')}==layouts
            j=Journal.__new__(Journal);j.db=src;j.directory=d;j.base=base;chain=j.verify_chain();assert not j.pending()
            entry=dict(layouts=len(layouts),chain=chain,journal=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),bytes=source.stat().st_size))
            needed=sum(p.stat().st_size for p in d.glob('campaign.sqlite*'))+32*2**20
            if size()+needed>=config['storage_bytes'] or shutil.disk_usage(RUN).free-needed<config['disk_free_floor_bytes']:
                entry['backup']=dict(status='blocked_by_registered_storage_or_free_disk_bound',required_bytes=needed)
            else:
                backup.parent.mkdir(exist_ok=True);assert not backup.exists()
                dst=sqlite3.connect(backup);src.backup(dst);assert dst.execute('pragma integrity_check').fetchone()==('ok',)
                for table in ('settings','stages','tasks','states','layouts'):same_table(src,dst,table)
                dst.close();entry['backup']=dict(status='verified',path=str(backup.relative_to(ROOT)),sha256=sha(backup),bytes=backup.stat().st_size,all_table_contents_match=True,integrity_check='ok',requires_immutable_base_ledger=True)
            src.close();stages[name]=entry
        print(name,entry['backup']['status'],flush=True)
    assert load_layouts(OUT/'whole_layout_exclusions.json')==union
    assert size()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status='verified' if all(s['backup']['status']=='verified' for s in stages.values()) else 'originals_verified_backups_partially_blocked',
        stages=stages,whole_layouts=len(union),initial_layouts=len(initial),search_new_layouts=len(search-initial),final_new_layouts=len(new),storage_bytes=size(),disk_free_bytes=shutil.disk_usage(RUN).free))
if __name__=='__main__':main()
