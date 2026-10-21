"""Guarded post-audit M6 backups/exclusions; reads old journals without inference."""
import sys,json,sqlite3,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.upstream_continuation import ROOT,OUT,RUN,check,readz,writez,writej,sha
from maze_evolution.deep_campaign_store import Journal,writer_lock

def size():return sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file())
def same_table(src,dst,table):
    a=src.execute(f'SELECT * FROM {table} ORDER BY 1,2');b=dst.execute(f'SELECT * FROM {table} ORDER BY 1,2')
    while True:
        x=a.fetchmany(128);y=b.fetchmany(128)
        assert x==y,table
        if not x:return

def main():
    config=check();assert not (OUT/'preservation.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    for name in ('search','final'):assert json.loads((OUT/f'{name}_audit.json').read_text())['status']=='PASS'
    initial=set(readz(OUT/'exclusions.json.gz')['hashes']);search=set(readz(OUT/'search_exclusions.json.gz')['hashes'])
    assert initial<=search
    data=readz(OUT/'confirmation.json.gz');new=set(data['new_layouts']);assert not search&new
    union=search|new;stages={}
    directories=[('search',RUN,search),('final',RUN/'final',union)]
    reserve=sum(sum(p.stat().st_size for p in d.glob('campaign.sqlite*')) for _,d,_ in directories)+400*2**20
    assert size()+reserve<config['storage_bytes'] and shutil.disk_usage(RUN).free-reserve>=config['disk_free_floor_bytes']
    for name,d,layouts in directories:
        source=d/'campaign.sqlite';backup=d/'backups/completed.sqlite';assert not backup.exists()
        with writer_lock(d):
            src=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
            assert src.execute('pragma integrity_check').fetchone()==('ok',)
            assert {r[0] for r in src.execute('select hash from layouts')}==layouts
            j=Journal.__new__(Journal);j.db=src;j.directory=d;chain=j.verify_chain();assert not j.pending()
            backup.parent.mkdir(exist_ok=True);dst=sqlite3.connect(backup);src.backup(dst)
            assert dst.execute('pragma integrity_check').fetchone()==('ok',)
            for table in ('settings','stages','tasks','states','layouts'):same_table(src,dst,table)
            dst.close();src.close()
        stages[name]=dict(layouts=len(layouts),chain=chain,
            journal=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),bytes=source.stat().st_size),
            backup=dict(path=str(backup.relative_to(ROOT)),sha256=sha(backup),bytes=backup.stat().st_size,integrity_check='ok',all_table_contents_match=True))
        print('Verified backup',name,flush=True)
    writez(OUT/'whole_layout_exclusions.json.gz',dict(count=len(union),initial_count=len(initial),search_new=len(search-initial),final_new=len(new),
        hashes=sorted(union),scope='All cumulative prior/setup and M6 search/final generated/rejected/unqueried whole layouts'))
    assert size()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status='verified',stages=stages,whole_layouts=len(union),initial_layouts=len(initial),search_new_layouts=len(search-initial),
        final_new_layouts=len(new),storage_bytes=size(),disk_free_bytes=shutil.disk_usage(RUN).free))
    print('M6 preserved',len(union),'whole layouts;',size(),'bytes',flush=True)
if __name__=='__main__':main()
