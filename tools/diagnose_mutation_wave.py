"""Posthoc goal-distance-ball comparison on saved P rasters only; zero inference."""
import sys,json
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from maze_evolution.foundation_study import read_compressed
from maze_evolution.mutation_transition_data import OUT,load
from maze_evolution.routing_transfer import lines
p=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(OUT/'confirmation');models={p['aliases']['local/route/d9']:'depth9',p['aliases']['local/route/d16']:'depth16'};totals=defaultdict(Counter);exceptions=[]
for rec in lines(OUT/'confirmation/responses.jsonl.gz'):
    if rec['mode']!='normal' or rec['model'] not in models:continue
    row=rec['row'];o=cases[row['case']];m=meta[row['case']];name=models[rec['model']];key=f'{name}/{m["family"]}';c=totals[key];c['inputs']+=1
    bits=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:o.maze.w*o.maze.h].astype(bool)
    ds=np.asarray(o.to_goal);radius=len(o.path)-1
    expected=(ds>=0)&(ds<=radius) if o.path else ds>=0
    same=bool(np.array_equal(bits,expected));c['exact_goal_ball_masks']+=same;c['optimal']+=row['optimal'];c['normal_emitted']+=row['status']=='emitted'
    if not same:exceptions.append(dict(model=name,case=row['case'],radius=radius,extra=int(np.sum(bits&~expected)),missing=int(np.sum(expected&~bits))))
result=dict(post_registration=True,new_candidate_calls=0,hypothesis='Reachable mask equals all open sites at goal distance <= shortest source-goal distance. Disconnected mask equals goal component.',
    interpretation='An output-equivalence diagnosis, not an observed internal algorithm, training label, or candidate-side BFS.',counts={k:dict(v) for k,v in totals.items()},exceptions=exceptions)
(OUT/'wave_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='exceptions'},indent=2));print('exceptions',len(exceptions))
