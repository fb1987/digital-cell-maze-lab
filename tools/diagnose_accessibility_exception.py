"""Post-hoc saved-output diagnosis of R's final-only partial gain; no inference."""
import sys
from pathlib import Path
from collections import deque,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_accessibility_study import *
from maze_evolution.mutation_accessibility_metrics import selected

def goal_ball(m):
    # Independent deque graph traversal, outside candidate inference.
    ds={m.goal:0};q=deque([m.goal])
    while q:
        p=q.popleft();y,x=divmod(p,m.w)
        for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0<=yy<m.h and 0<=xx<m.w:
                v=yy*m.w+xx
                if m.cells[v] and v not in ds:ds[v]=ds[p]+1;q.append(v)
    if m.start not in ds:return None
    return {p for p,d in ds.items() if d<=ds[m.start]}

def main():
    pool=read_compressed(OUT/'pool.json.gz');root=pool['roots']['Qfresh0']['id']
    mutant='accessibility/Qfresh0/1/walk2/d16'
    assert read_compressed(OUT/'selections.json.gz')['Qfresh0/1']['depth16']['best']==mutant
    pids={pool['aliases'][i]:i for i in (root,mutant)};saved={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        if e['key'] in pids:saved[pids[e['key']]]=e['rows']
    cases,_,meta=load(OUT/'confirmation');waves={cid:goal_ball(o.maze) for cid,o in cases.items()}
    match={i:sum(selected(r)==waves[r['case']] for r in rows if waves[r['case']] is not None) for i,rows in saved.items()}
    changed=[]
    for r,s in zip(saved[root],saved[mutant]):
        assert r['case']==s['case']
        if (r['mask'],r['status'])!=(s['mask'],s['status']):changed.append((r,s))
    out=dict(post_hoc=True,selection_reason='Final-only partial gain; no new selection or candidate evaluation',candidate_calls=0,
        root=root,mutant=mutant,reachable_per_model=3456,goal_ball_matches=match,
        changed_responses=len(changed),changed_mutant_goal_ball_matches=sum(selected(s)==waves[s['case']] for r,s in changed),
        changed_status_pairs=dict(Counter(f'{r["status"]}->{s["status"]}' for r,s in changed)),
        changed_optimal_pairs=dict(Counter(f'{r["optimal"]}->{s["optimal"]}' for r,s in changed)),
        gains_by_family=dict(Counter(meta[s['case']]['family'] for r,s in changed if s['optimal'] and not r['optimal'])),
        statuses={i:dict(Counter(r['status'] for r in rows)) for i,rows in saved.items()},
        mutation_events=[e for e in pool['events'] if e['item'].startswith('accessibility/Qfresh0/1/walk2/')],
        interpretation='Exact saved-output comparison only; not proof of identical hidden dynamics or causal attribution to a particular edit.')
    write_json(OUT/'exception_diagnostic.json',out)
    print({k:v for k,v in out.items() if k!='mutation_events'})
if __name__=='__main__':main()
