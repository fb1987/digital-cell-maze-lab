"""Pre-scientific Q timing-only amendment; preserves original fixture profile."""
import json
from pathlib import Path
from maze_evolution.shared_prefix_study import OUT,FIXTURES,sha,write_json

def main():
    assert not (OUT/'train').exists() and not (OUT/'validation').exists()
    path=FIXTURES/'profile.json';original=FIXTURES/'profile_original.json'
    if not original.exists():original.write_bytes(path.read_bytes())
    old=json.loads(original.read_text());assert old['generations']==16 and old['passed']
    rate=1.5*max(old['pool_rates']);fixed=576*768+78*4032
    options=[g for g in (128,96,64,32) if rate*(fixed+g*18*96*12+(g//8)*18*2*768)<600]
    assert options and options[0]==32
    p=dict(old,generations=32,planning_rate=rate,projected_calls=fixed+32*18*96*12+4*18*2*768)
    p['projected_seconds']=p['planning_rate']*p['projected_calls'];p['schedule_amendment']='results/shared_prefix/schedule_amendment.json'
    write_json(path,p)
    write_json(OUT/'schedule_amendment.json',dict(reason='Original timing rule allows16 generations but query schedule needs32 for all8poses. Before any research evaluation, replace factor2 by1.5, retain600s projection ceiling,720s hard main cap and100s reserve rule. No fixture score inspected or used. No source/runtime/population/scoring changes.',scientific_calls=0,original_profile_sha256=sha(FIXTURES/'profile_original.json'),active_profile_sha256=sha(path),registration_sha256=sha(OUT/'preregistration.json'),generations=32,projected_seconds=p['projected_seconds'],tool_sha256=sha(Path(__file__))))
    print(json.dumps(p,indent=2))
if __name__=='__main__':main()
