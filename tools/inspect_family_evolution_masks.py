"""Retrospective raster diagnostics; no repair, selection, or new inference."""
from pathlib import Path
import gzip,json
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/family_evolution'
def read(path):
 with gzip.open(path,'rt') as f:return json.load(f)
c=read(OUT/'choices.json.gz');meta=read(OUT/'confirmation/metadata.json.gz')
aliases={a:p for a,p in c['aliases'].items() if a.startswith('fresh/') and a.endswith('/primary')}
metrics={};ordinary_metrics={}
with gzip.open(OUT/'confirmation/responses.jsonl.gz','rt') as f:
 for line in f:
  e=json.loads(line)
  if e['key'] not in aliases.values():continue
  lengths=Counter();ordinary_bases=set()
  by=defaultdict(lambda:dict(inputs=0,shortest=0,contains_oracle_path=0,path_plus_one=0,path_plus_multiple=0,exact_mask_wrong_status=0))
  for r in e['rows']:
   q=meta[r['case']]
   if q['family'].startswith('ordinary_') and r['optimal']:
    lengths[len(q['path'])-1]+=1;ordinary_bases.add(q['base'])
   if q['family']!='paired':continue
   group=by[q['graph']+'/p'+str(q['prefix'])];group['inputs']+=1;group['shortest']+=r['optimal']
   mask={8*i+b for i,byte in enumerate(bytes.fromhex(r['mask'])) for b in range(8) if byte&(1<<b)};path=set(q['path'])
   if path<=mask:
    extra=len(mask-path);group['contains_oracle_path']+=1;group['path_plus_one']+=extra==1;group['path_plus_multiple']+=extra>1
    group['exact_mask_wrong_status']+=extra==0 and not r['optimal']
  metrics[e['key']]=dict(by);ordinary_metrics[e['key']]=dict(shortest_by_edges=dict(lengths),independent_bases=sorted(ordinary_bases))
packet=dict(post_hoc=True,new_candidate_calls=0,outputs_repaired=False,ordinary_metrics=ordinary_metrics,aliases=aliases,metrics=metrics)
(OUT/'raster_diagnostics.json').write_text(json.dumps(packet,indent=2)+'\n')
for a,p in aliases.items():
 if 'current_mutation' in a or 'resample' in a:print(a,{k:v for k,v in metrics[p].items() if k.startswith('fork/')})
