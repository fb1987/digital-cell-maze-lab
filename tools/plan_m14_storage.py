"""Prospective M14 storage estimate from unchanged M13 journal sizes."""
import argparse,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.exploration_allocation import ROOT,OUT,RUN,CONFIG,writej,sha
p=argparse.ArgumentParser();p.add_argument('--output',default='storage_plan.json');args=p.parse_args()
target=OUT/args.output;assert not target.exists()
source=ROOT/'runs/mutation_scope_m13/campaign.sqlite';final=ROOT/'runs/mutation_scope_m13/final/campaign.sqlite'
# Same declared population, rounds and assessment allocations as M13. Reserve
# 50% larger new search journal, its matching backup, and 80MiB for fixture,
# final, final backup, compact reports, deltas and logs. No old record changed.
search=source.stat().st_size*1.5
projected=search*2+80*2**20
free=shutil.disk_usage(ROOT).free
result=dict(prior_search=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),bytes=source.stat().st_size),
 prior_final=dict(path=str(final.relative_to(ROOT)),sha256=sha(final),bytes=final.stat().st_size),
 projected_search_with_50percent_margin_bytes=int(search),projected_including_backups_and_other_bytes=int(projected),
 other_allowance_bytes=80*2**20,free_bytes=free,headroom_above_floor=free-CONFIG['disk_free_floor_bytes'],
 configured_storage_cap=CONFIG['storage_bytes'],admission_reserve_satisfied=free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes'],
 projection_fits_cap=projected<CONFIG['storage_bytes'],scientific_cases_generated=0,
 caveat='Prior run is a planning extrapolation. Exploration may raise diversity/record size. Hard runtime guards remain mandatory; no migration, deletion or old inference.')
writej(target,result);print(json.dumps(result,indent=2))
