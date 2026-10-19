"""Audit the explicit pre-scientific schedule amendment, counts and pose coverage."""
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.shared_prefix_study import *

def main():
    amendment=json.loads((OUT/'schedule_amendment.json').read_text());old=json.loads((FIXTURES/'profile_original.json').read_text());active=json.loads((FIXTURES/'profile.json').read_text())
    assert sha(FIXTURES/'profile_original.json')==amendment['original_profile_sha256']
    assert sha(FIXTURES/'profile.json')==amendment['active_profile_sha256']
    assert sha(OUT/'preregistration.json')==amendment['registration_sha256']
    assert sha(ROOT/'tools/register_shared_prefix_schedule.py')==amendment['tool_sha256']
    assert old['generations']==16 and active['generations']==32 and amendment['scientific_calls']==0
    assert active['planning_rate']==1.5*max(old['pool_rates'])
    fixed=576*768+78*4032
    assert active['projected_calls']==fixed+32*18*96*12+4*18*2*768
    assert active['projected_seconds']==active['planning_rate']*active['projected_calls']<600
    generation=json.loads((OUT/'train/generation.json').read_text());rev=generation['revision']
    for path in (OUT/'schedule_amendment.json',FIXTURES/'profile.json',FIXTURES/'profile_original.json'):
        assert subprocess.check_output(['git','show',f'{rev}:{path.relative_to(ROOT)}'])==path.read_bytes()
    s=json.loads((OUT/'search_execution.json').read_text());f=json.loads((OUT/'confirmation/execution.json').read_text());g=s['generations'];assert g==32
    assert s['budget']['calls']==576*768+g*18*96*12+(g//8)*18*2*768
    models=read_compressed(OUT/'choices.json.gz')['models'];assert f['budget']['calls']==s['budget']['calls']+len(models)*4032
    meta=read_compressed(OUT/'train/metadata.json.gz');coverage={}
    for arm in ARMS:
        ids=[c for n in range(g) for c in training_ids(meta,n,arm)]
        coverage[arm]=sorted({meta[c]['pose'] for c in ids});assert coverage[arm]==list(range(8))
    seconds=sum(e['seconds'] for e in lines(OUT/'initial.jsonl.gz'))+sum(e['seconds'] for e in lines(OUT/'search_responses.jsonl.gz'))+sum(e['seconds'] for e in lines(OUT/'confirmation/responses.jsonl.gz'))
    assert abs(seconds-f['budget']['seconds'])<1e-7
    write_json(OUT/'schedule_audit.json',dict(passed=True,original_generation_plan=16,amended_generations=32,training_generation_revision=rev,coverage=coverage,logical_initial_calls=3*576*768,physical_initial_calls=576*768,main_physical_calls=f['budget']['calls'],main_logical_calls=f['budget']['calls']+2*576*768+(len(read_compressed(OUT/'choices.json.gz')['aliases'])-len(models))*4032,final_alias_calls=len(read_compressed(OUT/'choices.json.gz')['aliases'])*4032,final_physical_calls=len(models)*4032,seconds=seconds,source_runtime_unchanged=True))
if __name__=='__main__':main()
