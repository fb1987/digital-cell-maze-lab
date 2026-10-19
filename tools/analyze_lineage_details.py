"""Descriptive saved-output checks added after V12L registration; no inference."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from collections import defaultdict
import numpy as np
from maze_evolution.lineage_confirmation_data import *
from maze_evolution.lineage_confirmation_analysis import score
from maze_evolution.routing_transfer import lines
from maze_evolution.foundation_calibration import write_json

cases,contexts,meta=load(OUT/'confirmation');by=defaultdict(dict)
for rec in lines(OUT/'confirmation/responses.jsonl.gz'):by[rec['model'],rec['mode']][rec['row']['case']]=rec['row']
models=read_compressed(OUT/'panel.json.gz');results={};paired_contexts=defaultdict(list)
for c in contexts:paired_contexts[c['template']].append(c)
def maskset(r):return set(np.flatnonzero(np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:625]).tolist())
for name in models:
 rows=by[name,'normal'];translated=0;total=0
 for cs in paired_contexts.values():
  a,b=sorted(cs,key=lambda c:c['position'])
  for pose in range(8):
   for family in FAMILIES:
    for ca,cb in zip(a['poses'][pose]['cases'][family],b['poses'][pose]['cases'][family]):
     ja,jb=meta[ca]['junction'],meta[cb]['junction'];dx,dy=jb%25-ja%25,jb//25-ja//25
     aa={(p%25+dx,p//25+dy) for p in maskset(rows[ca])};bb={(p%25,p//25) for p in maskset(rows[cb])}
     translated+=aa==bb;total+=1
 results[name]=dict(translation_identical_masks=translated,translation_comparisons=total,
                    legal_nonshortest=sum(r['valid'] and not r['optimal'] for r in rows.values()))
lineages={}
for rep in (1,2):
 target=by[f'k{rep}_target','normal'];comparisons={}
 for other in ('entry','parent','frozen'):
  control=by[f'k{rep}_{other}','normal'];a=score(list(control.values()),meta);b=score(list(target.values()),meta)
  pa,pb={tuple(k) for k in a['pair_keys']},{tuple(k) for k in b['pair_keys']}
  comparisons[other]=dict(gained_pairs=len(pb-pa),lost_pairs=len(pa-pb),retained_pairs=len(pa&pb),
    gained_corridors=sum(r['optimal'] and not control[cid]['optimal'] for cid,r in target.items() if meta[cid]['family'].startswith('corridor')),
    lost_corridors=sum(not r['optimal'] and control[cid]['optimal'] for cid,r in target.items() if meta[cid]['family'].startswith('corridor')),
    identical_masks=sum(r['mask']==control[cid]['mask'] for cid,r in target.items()),
    identical_status_steps=sum(all(r[k]==control[cid][k] for k in ('status','steps')) for cid,r in target.items()),
    fewer_reads=sum(r['reads']<control[cid]['reads'] for cid,r in target.items()),
    fewer_active=sum(r['active']<control[cid]['active'] for cid,r in target.items()),
    total_read_difference=sum(r['reads']-control[cid]['reads'] for cid,r in target.items()),
    total_dispatch_difference=sum(r['dispatches']-control[cid]['dispatches'] for cid,r in target.items()),
    identical_status_steps_work=sum(all(r[k]==control[cid][k] for k in ('status','steps','reads','range_reads','dispatches','active')) for cid,r in target.items()))
 lineages[str(rep)]=comparisons
write_json(OUT/'descriptive_details.json',dict(post_registration_saved_output_analysis=True,no_candidate_calls=True,models=results,lineages=lineages))
print(json.dumps(dict(models=results,lineages=lineages),indent=2))
