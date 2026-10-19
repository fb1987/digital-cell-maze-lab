"""Posthoc final emitted-wave comparison and size breakdown; no candidate calls."""
import sys,json
from pathlib import Path
from collections import defaultdict,deque
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.shared_prefix_study import *
from cellular_maze_lab import neighbors

def main():
    cases,contexts,meta=load(OUT/'confirmation');details={}
    expected={}
    for cid,o in cases.items():
        m=o.maze;ds={m.goal:0};q=deque([m.goal])
        while q:
            p=q.popleft()
            for x in neighbors(p,m.w,m.h):
                if m.cells[x] and x not in ds:ds[x]=ds[p]+1;q.append(x)
        cap=ds.get(m.start,float('inf'));mask=np.asarray([p in ds and ds[p]<=cap for p in range(len(m.cells))],np.uint8)
        expected[cid]=np.packbits(mask,bitorder='little').tobytes().hex()
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        failures=defaultdict(int);groups=defaultdict(list);wave=0;reach=0
        for r in e['rows']:
            m=meta[r['case']]
            if r['reachable']:reach+=1;wave+=r['mask']==expected[r['case']]
            if m['family']=='paired':failures[r['failure'] or 'correct']+=1;groups[m['base'],m['pose']].append(r)
        by=defaultdict(lambda:dict(pairs=0,opportunities=0,contexts=set(),poses=set()))
        for rs in groups.values():
            m=meta[rs[0]['case']];v=by[f'{"stress" if m["stress"] else "core"}/{m["graph"]}/a{m["arm"]}/p{m["prefix"]}'];v['opportunities']+=1
            if all(r['optimal'] for r in rs):v['pairs']+=1;v['contexts'].add(m['template']);v['poses'].add(m['pose'])
        for v in by.values():v['contexts']=sorted(v['contexts']);v['poses']=sorted(v['poses'])
        details[e['key']]=dict(reachable=reach,goal_distance_ball_matches=wave,branched_failure_counts=dict(failures),by=dict(by))
    write_json(OUT/'output_diagnostics.json',dict(candidate_calls=0,posthoc=True,scope='Emitted rasters only; not an internal algorithm identification or causal mechanism intervention.',models=details))
if __name__=='__main__':main()
