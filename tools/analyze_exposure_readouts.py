"""Post-registration saved-output diagnosis; no candidate calls or changed choices."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from collections import defaultdict,Counter
import numpy as np
from maze_evolution.exposure_data import OUT,load
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.route_confirmation_audit import graph_distances
from maze_evolution.foundation_calibration import write_json

aliases=read_compressed(OUT/'confirmation/aliases.json.gz');cases={};meta={}
for origin in ('carry','fresh'):cases[origin],_,meta[origin]=load(OUT/'confirmation'/origin)
by=defaultdict(dict)
for rec in lines(OUT/'confirmation/responses.jsonl.gz'):by[rec['origin']].setdefault(rec['model'],{})[rec['row']['case']]=rec['row']
def mask(r,n):return set(np.flatnonzero(np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:n]).tolist())
results={}
for key,aa in aliases.items():
 origin=key.split('/')[0];results[key]={}
 for label in ('selected_active','selected_neutral','selected_zero','selected_local'):
  entry=aa[label];rows=by[origin][entry['model']];pairs=defaultdict(list);nopath=Counter();fullcomponent=Counter();kindstats=defaultdict(lambda:Counter());successes=defaultdict(list)
  for cid,r in rows.items():
   m=meta[origin][cid];o=cases[origin][cid]
   if m['family'] in ('paired','fork','two_junction','cycle'):
    pairs[m['base'],m['family'],m['pose']].append(cid)
    component={p for p,d in enumerate(graph_distances(o.maze.cells,o.maze.w,o.maze.start)) if d>=0}
    fullcomponent['inputs']+=1;fullcomponent['entire_source_component']+=mask(r,len(o.maze.cells))==component
    kind=m.get('kind','prefix'+str(m['prefix']));kindstats[kind]['inputs']+=1;kindstats[kind]['optimal']+=r['optimal']
   if not r['reachable']:nopath[r['status']]+=1
  identical=0;good=0
  for (base,family,pose),ids in pairs.items():
   assert len(ids)==2;a,b=[rows[c] for c in ids];identical+=a['mask']==b['mask'];both=a['optimal'] and b['optimal'];good+=both
   if both:successes[(base,family)].append(pose)
   kind=meta[origin][ids[0]].get('kind','prefix'+str(meta[origin][ids[0]]['prefix']));kindstats[kind]['pairs']+=both
  results[key][label]=dict(id=entry['item']['id'],genes=len(entry['item']['genome']['genes']),mask=entry['item']['genome']['exposure'],
    pairs=len(pairs),complete_pairs=good,identical_two_goal_masks=identical,full_component=dict(fullcomponent),by_kind={k:dict(v) for k,v in kindstats.items()},
    successful_groups=[dict(base=k[0],family=k[1],poses=v) for k,v in successes.items()],no_path_statuses=dict(nopath),
    false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows.values()),legal_nonshortest=sum(r['valid'] and not r['optimal'] for r in rows.values()))
write_json(OUT/'readout_diagnosis.json',dict(post_registration=True,new_candidate_calls=0,results=results))
for k,v in results.items():
 if k.startswith('fresh'):print(k,json.dumps(v,indent=2))
