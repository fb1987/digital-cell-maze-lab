"""Preserve completed M11 journal and all layouts; no new inference."""
import sys,json,sqlite3,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.retention_bank import ROOT,OUT,RUN,check,readz,writej,sha,write_layouts,load_layouts
from maze_evolution.deep_campaign_store import writer_lock,Journal

def size():return sum(p.stat().st_size for b in (OUT,RUN) for p in b.rglob('*') if p.is_file())
def main():
 c=check();assert not (OUT/'preservation.json').exists();assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
 for name in ('calibration','final'):assert json.loads((OUT/f'{name}_audit.json').read_text())['status']=='PASS'
 initial=set(readz(OUT/'exclusions.json.gz')['hashes']);cal=load_layouts(OUT/'calibration_exclusions.json');final=set(readz(OUT/'confirmation.json.gz')['new_layouts'])
 assert initial<=cal and not cal&final;layouts=cal|final
 source=RUN/'campaign.sqlite';backup=RUN/'backups/completed.sqlite';reserve=source.stat().st_size+300*2**20
 assert size()+reserve<c['storage_bytes'] and shutil.disk_usage(RUN).free-reserve>=c['disk_free_floor_bytes']
 with writer_lock(RUN):
  src=sqlite3.connect(f'file:{source}?mode=ro',uri=True);assert src.execute('pragma integrity_check').fetchone()==('ok',)
  j=Journal.__new__(Journal);j.db=src;j.directory=RUN;chain=j.verify_chain();assert j.get('final_complete') and not j.pending() and j.layouts()==layouts
  backup.parent.mkdir(exist_ok=True);assert not backup.exists();dst=sqlite3.connect(backup);src.backup(dst)
  assert dst.execute('pragma integrity_check').fetchone()==('ok',)
  for table in ('settings','stages','tasks','states','layouts'):
   order='1' if table=='layouts' else '1,2';a=src.execute(f'select * from {table} order by {order}');b=dst.execute(f'select * from {table} order by {order}')
   while True:
    x=a.fetchmany(128);y=b.fetchmany(128);assert x==y,table
    if not x:break
  usage=j.get('usage');dst.close();src.close()
 write_layouts('whole_layout_exclusions',layouts);assert load_layouts(OUT/'whole_layout_exclusions.json')==layouts
 assert size()<c['storage_bytes'] and shutil.disk_usage(RUN).free>=c['disk_free_floor_bytes']
 writej(OUT/'preservation.json',dict(status='verified',chain=chain,usage=usage,initial_layouts=len(initial),calibration_new_layouts=len(cal-initial),final_new_layouts=len(final),whole_layouts=len(layouts),
  journal=dict(path=str(source.relative_to(ROOT)),bytes=source.stat().st_size,sha256=sha(source)),backup=dict(path=str(backup.relative_to(ROOT)),bytes=backup.stat().st_size,sha256=sha(backup),all_tables_match=True,integrity='ok'),
  storage_bytes=size(),disk_free_bytes=shutil.disk_usage(RUN).free))
 print('Verified M11 backup;',len(layouts),'layouts preserved;',size(),'bytes',flush=True)
if __name__=='__main__':main()
