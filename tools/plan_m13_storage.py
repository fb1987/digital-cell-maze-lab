"""Read-only old-record compression calibration; no new candidate evaluations."""
import json,sqlite3,zlib,shutil,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_scope import ROOT,OUT,RUN,CONFIG,writej
from maze_evolution.referenced_campaign_store import sha

p=ROOT/'runs/retention_memory_m12/campaign.sqlite'
c=sqlite3.connect(f'file:{p}?mode=ro',uri=True);estimates={};start=time.monotonic()
for kind in ('train','assessment'):
    count,total=c.execute('select count(*),sum(length(t.spec)+length(t.result)) from tasks t join stages s on t.stage=s.n where s.kind=?',(kind,)).fetchone()
    stride=max(1,count//48);old=new=0;n=0
    for k,(spec,res) in enumerate(c.execute('select t.spec,t.result from tasks t join stages s on t.stage=s.n where s.kind=? order by t.stage,t.n',(kind,))):
        if k%stride:continue
        n+=1
        for b in (spec,res):old+=len(b);new+=len(zlib.compress(zlib.decompress(b),9))
    projected=total*new/old*(.5 if kind=='train' else 1.)
    estimates[kind]=dict(old_tasks=count,old_bytes=total,sample_tasks=n,sample_old=old,sample_new=new,projected_M13_task_bytes=projected)
c.close()
# 50% extra for broader-policy diversity, SQLite pages, deltas, states and task
# overhead; then double for a verified journal backup. Separate exports/fixtures/
# final/backup/log allowance is explicit. This is an estimate, not a safety guard.
projected_search=(sum(x['projected_M13_task_bytes'] for x in estimates.values())+20*2**20)*1.5
other=80*2**20
projected_total=2*projected_search+other
free=shutil.disk_usage(ROOT).free
result=dict(source_journal=str(p.relative_to(ROOT)),source_sha256=sha(p),sample=estimates,
 projected_search_bytes=round(projected_search),projected_including_backups_and_other_bytes=round(projected_total),
 other_allowance_bytes=other,free_bytes=free,headroom_above_floor=free-CONFIG['disk_free_floor_bytes'],
 configured_storage_cap=CONFIG['storage_bytes'],admission_reserve_satisfied=free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes'],
 projection_fits_cap=projected_total<CONFIG['storage_bytes'],wall_seconds=time.monotonic()-start,
 caveat='Prior M12 receipts are a planning extrapolation; broader genomes may increase diversity/bytes. Runtime guards remain mandatory. No old file modified; no new inference or cases.')
assert not (OUT/'storage_plan.json').exists();writej(OUT/'storage_plan.json',result)
print(json.dumps(result,indent=2))
