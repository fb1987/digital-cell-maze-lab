"""Guarded M5 SQLite backups and whole-layout exclusions; no inference."""
import sys,json,sqlite3,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.holding_assay import ROOT,OUT,RUN,PRIOR,check,readz,writez,writej,sha
from maze_evolution.deep_campaign_store import Journal,writer_lock


def size():return sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())

def main():
    config=check();assert not (OUT/'preservation.json').exists()
    for name in ('screen','final'):assert json.loads((OUT/f'{name}_audit.json').read_text())['status']=='PASS'
    prior=json.loads((PRIOR/'completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    previous=set(readz(PRIOR/'whole_layout_exclusions.json.gz')['hashes']);union=set(previous);stages={}
    reserve=sum((RUN/name/'campaign.sqlite').stat().st_size for name in ('screen','final'))+400*2**20
    assert size()+reserve<config['storage_bytes'] and shutil.disk_usage(RUN).free-reserve>=config['disk_free_floor_bytes']
    for name in ('screen','final'):
        data=readz(OUT/f'{name}_cases.json.gz');new=set(data['new_layouts']);assert not union&new;union|=new
        directory=RUN/name;backup=directory/'backups/completed.sqlite';assert not backup.exists()
        with writer_lock(directory):
            source=directory/'campaign.sqlite';src=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
            assert src.execute('pragma integrity_check').fetchone()==('ok',)
            assert {r[0] for r in src.execute('select hash from layouts')}==union
            j=Journal.__new__(Journal);j.db=src;j.directory=directory;chain=j.verify_chain();assert not j.pending()
            backup.parent.mkdir(exist_ok=True);dst=sqlite3.connect(backup);src.backup(dst)
            assert dst.execute('pragma integrity_check').fetchone()==('ok',)
            for table in ('settings','stages','tasks','states'):
                assert src.execute(f'select * from {table} order by 1,2').fetchall()==dst.execute(f'select * from {table} order by 1,2').fetchall()
            assert {r[0] for r in dst.execute('select hash from layouts')}==union
            dst.close();src.close()
        stages[name]=dict(new_layouts=len(new),cumulative_layouts=len(union),chain=chain,
            journal=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),bytes=source.stat().st_size),
            backup=dict(path=str(backup.relative_to(ROOT)),sha256=sha(backup),bytes=backup.stat().st_size,integrity_check='ok',all_table_contents_match=True))
    writez(OUT/'whole_layout_exclusions.json.gz',dict(count=len(union),previous_count=len(previous),hashes=sorted(union),scope='All prior and M5 screen/final generated, rejected and unqueried whole layouts'))
    assert size()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status='verified',stages=stages,prior_completion_hashes=len(prior['files']),whole_layouts=len(union),storage_bytes=size(),disk_free_bytes=shutil.disk_usage(RUN).free))
    print('Preserved both journals and verified backups;',len(union),'excluded whole layouts.')

if __name__=='__main__':main()
