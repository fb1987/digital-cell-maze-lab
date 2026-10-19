"""Freeze a timing-only refinement after a closed original R preflight."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_accessibility_study import *
from maze_evolution.mutation_accessibility_budget import plans,verify_profile

def main():
    assert not (OUT/'discovery').exists() and not (OUT/'budget_amendment.json').exists()
    path=FIXTURES/'profile.json';original=json.loads(path.read_text());assert not original['passed']
    (FIXTURES/'profile_original.json').write_bytes(path.read_bytes());pool=read_compressed(OUT/'pool.json.gz');rates=read_compressed(FIXTURES/'rates.json.gz');bounds=plans(pool,rates);n=next(n for n in (16,8,4) if bounds[str(n)]['total']<600)
    profile=dict(original,passed=True,walks_per_root_block=n,bounds=bounds,projected_seconds=bounds[str(n)]['total'],planned_calls_upper=(6+60*n)*768+126*768+66*5184,budget_method='2x exact discovery rates + 2x per-group worst nominee rates',amendment='results/mutation_accessibility/budget_amendment.json');profile['original_global_planning_rate']=profile.pop('planning_rate');verify_profile(pool,rates,profile);write_json(path,profile)
    paths=[path,FIXTURES/'profile_original.json',FIXTURES/'rates.json.gz',ROOT/'maze_evolution/mutation_accessibility_budget.py',ROOT/'maze_evolution/mutation_accessibility_audit_amended.py',ROOT/'tests/test_mutation_accessibility_budget.py',Path(__file__)]
    write_json(OUT/'budget_amendment.json',dict(reason='Original preflight failed because a single slowest-group rate was applied to every evaluation. Original attempt remains closed with zero scientific calls. Revised bound retains2x safety factor,600s projected threshold,720s hard main cap,all8poses and exact frozen genomes; sums individual discovery costs and group-wise worst possible nominee costs. Only timing data used; no fixture scores inspected.',scientific_calls=0,original_attempt='stopped_at_profile',walks_per_root_block=n,hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}))
    print(dict(walks_per_root_block=n,bounds=bounds))
if __name__=='__main__':main()
