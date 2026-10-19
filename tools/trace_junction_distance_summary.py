"""Read-only trace summary using exact unique-path bitmap equality, not VM reruns."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.junction_distance_data import OUT
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.route_confirmation import unpack_history

def run():
 meta=read_compressed(OUT/'confirmation/metadata.json.gz');native={}
 for e in lines(OUT/'normal.jsonl.gz'):native[e['model'],e['row']['case']]=e['row']
 summaries=defaultdict(Counter);certificates=[];paired=defaultdict(list)
 for e in lines(OUT/'traces.jsonl.gz'):
  n,mode=e['model'],e['mode'];r=e['row'];cid=r['case'];m=meta[cid];h=unpack_history(e['history'])
  expected=np.zeros(625,bool);expected[m['path']]=True
  ticks=(np.flatnonzero(np.all((h[:,2]>0)==expected,axis=1))+1).tolist()
  s=summaries[n+'/'+mode];s['traces']+=1;s['frames']+=len(h);s['full_horizon']+=len(h)==64
  s['shortest_frames']+=len(ticks);s['traces_with_shortest_frame']+=bool(ticks)
  if mode=='normal':
   normal=native[n,cid];s['normal_shortest']+=normal['optimal']
   if not normal['optimal'] and ticks:
    s['failed_normals_with_shortest_frame']+=1
    s['failed_normals_with_later_shortest_frame']+=any(t>normal['steps'] for t in ticks)
  if ticks:certificates.append(dict(model=n,mode=mode,case=cid,shortest_ticks=ticks,native_steps=native[n,cid]['steps'],native_optimal=native[n,cid]['optimal']))
  paired[n,mode,m['base'],m['shape'],m['prefix'],m['family'],m['pose']].append(set(ticks))
 for key,sets in paired.items():
  assert len(sets)==2
  if sets[0]&sets[1]:summaries[key[0]+'/'+key[1]]['pairs_with_simultaneous_shortest_frame']+=1
 (OUT/'saved_trace_diagnostics.json').write_text(json.dumps(dict(summary={k:dict(v) for k,v in summaries.items()},certificates=certificates,
   method='Exact expected unique-path bitmap equality on saved forced histories; no additional inference.'),indent=2)+'\n')
 print(json.dumps({k:dict(v) for k,v in summaries.items()}))

if __name__=='__main__':run()
