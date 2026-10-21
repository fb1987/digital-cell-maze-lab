"""Guarded M4 SQLite backup and cumulative whole-layout exclusions; no inference."""
import json
import shutil
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mechanism_retention import ROOT,OUT,RUN,check,readz,writez,writej,sha
from maze_evolution.deep_campaign_store import writer_lock,Journal,unpacked


def size():
    return sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())


def main():
    config=check()
    assert json.loads((OUT/'audit.json').read_text())['status']=='PASS'
    assert not (OUT/'preservation.json').exists()
    prior=json.loads((ROOT/'results/wave_continuation/completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    previous=set(readz(ROOT/'results/wave_continuation/whole_layout_exclusions.json.gz')['hashes'])
    data=readz(OUT/'cases.json.gz');new=set(data['new_layouts']);assert not previous&new
    union=previous|new
    assert not (OUT/'whole_layout_exclusions.json.gz').exists()
    writez(OUT/'whole_layout_exclusions.json.gz',dict(count=len(union),hashes=sorted(union),previous_count=len(previous),new_count=len(new),
        scope='All prior M3 exclusions plus all M4 generated, rejected and unqueried layouts'))
    backup=RUN/'backups'/'completed.sqlite';assert not backup.exists()
    db=RUN/'campaign.sqlite';reserve=db.stat().st_size+400*2**20
    assert size()+reserve<config['storage_bytes']
    assert shutil.disk_usage(RUN).free-reserve>=config['disk_free_floor_bytes']
    with writer_lock(RUN):
        src=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
        assert src.execute('pragma integrity_check').fetchone()==('ok',)
        assert {r[0] for r in src.execute('select hash from layouts')}==union
        j=Journal.__new__(Journal);j.db=src;j.directory=RUN;chain=j.verify_chain();assert not j.pending()
        backup.parent.mkdir(exist_ok=True)
        dst=sqlite3.connect(backup);src.backup(dst)
        assert dst.execute('pragma integrity_check').fetchone()==('ok',)
        for table in ('settings','stages','tasks','states'):
            assert src.execute(f'select * from {table} order by 1,2').fetchall()==dst.execute(f'select * from {table} order by 1,2').fetchall(),table
        assert dst.execute('select count(*) from layouts').fetchone()[0]==len(union)
        assert {r[0] for r in dst.execute('select hash from layouts')}==union
        dst.close();src.close()
    assert size()<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'preservation.json',dict(status='verified',prior_completion_hashes=len(prior['files']),
        journal=dict(path=str(db.relative_to(ROOT)),sha256=sha(db),bytes=db.stat().st_size,chain=chain),
        backup=dict(path=str(backup.relative_to(ROOT)),sha256=sha(backup),bytes=backup.stat().st_size,integrity_check='ok',all_table_contents_match=True),
        previous_layouts=len(previous),new_layouts=len(new),whole_layouts=len(union),storage_bytes=size(),disk_free_bytes=shutil.disk_usage(RUN).free))
    print('Preserved journal, verified backup and',len(union),'whole-layout exclusions.')


if __name__=='__main__':main()
