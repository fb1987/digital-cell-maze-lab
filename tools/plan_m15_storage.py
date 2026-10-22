"""M15 prospective storage/admission calculation from audited M14 usage."""
import json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.exploration_continuation import ROOT,OUT,RUN,CONFIG,writej,sha
assert not (OUT/'storage_plan.json').exists()
source=ROOT/'runs/exploration_allocation_m14/campaign.sqlite'
# 1024 additional rounds vs 64 old rounds, 50% record growth margin, two
# complete search copies plus 512 MiB for fixtures/final/backups/logs/reports.
search=source.stat().st_size*(1024/64)*1.5
projected=search*2+512*2**20;free=shutil.disk_usage(ROOT).free
result=dict(prior_search=dict(path=str(source.relative_to(ROOT)),sha256=sha(source),bytes=source.stat().st_size),
 maximum_additional_rounds=1024,projected_search_with_50percent_margin_bytes=int(search),
 projected_including_backups_and_other_bytes=int(projected),free_bytes=free,configured_storage_cap=CONFIG['storage_bytes'],
 admission_reserve_satisfied=free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes'],
 projection_fits_cap=projected<CONFIG['storage_bytes'],scientific_cases_generated=0,
 caveat='Planning extrapolation at maximum rounds, not promised wall throughput. Runtime bounds still mandatory. Preserve originals if a backup cannot fit.')
writej(OUT/'storage_plan.json',result);print(json.dumps(result,indent=2))
