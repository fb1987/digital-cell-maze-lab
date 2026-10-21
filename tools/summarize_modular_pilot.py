"""Post-run descriptive reporting from frozen M1 receipts; no new inference."""
import json,sqlite3,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.modular_pilot import OUT,RUN,readz,writej
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.deep_confirmation_analysis import capabilities


def costs():
 c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);physical=Counter();logical=Counter();cpu=Counter();work=Counter();cand=Counter();nominal=Counter()
 for n,kind,g in c.execute('select n,kind,generation from stages where complete=1 order by n'):
  for rep in ('flat','modular'):
   for replicate in range(3):
    for curriculum in ('familiar','broad'):
     for method in ('mutation','resample'):
      condition=f'{rep}/{replicate}/{curriculum}/{method}'
      nominal[condition]+=96*24 if kind=='train' else (96 if g==0 else 114)*200
  for spec,blob in c.execute('select spec,result from tasks where stage=? order by n',(n,)):
   spec=unpacked(spec);r=unpacked(blob)
   # Tasks may mix representations; receipt candidate/CPU time cannot be honestly
   # split among them. Total time is reported, per-model exact work can be split.
   for e,entry in zip(spec,r['entries']):
    rep=e['model']['representation'];physical[rep]+=len(entry['rows'])
    work[rep]+=sum(x['reads']+x['dispatches']+x['exposure_checks'] for x in entry['rows'])
    for k,i in e['aliases']:logical[str(k)]+=len(entry['rows'])
 c.close();return dict(physical_calls_by_representation=dict(physical),physical_work_by_representation=dict(work),unique_identity_logical_calls_by_condition_index=dict(logical),nominal_evaluation_slots_by_condition=dict(nominal),timing_limitation='Mixed-model task receipts time the whole task; no defensible per-condition candidate-time allocation. Use total measured CPU/candidate/wall times, and exact per-model calls/work.')


def diagnostics():
 data=readz(OUT/'confirmation.json.gz');meta=data['metadata'];responses=readz(OUT/'final_responses.json.gz')['rows'];choices=readz(OUT/'choices.json.gz')
 results={}
 for identity,roles in choices['roles'].items():
  if not any(r[1]=='nominee' for r in roles):continue
  groups=defaultdict(Counter)
  for row in responses[identity]:
   m=meta[row['case']];key=m['family']+('/'+str(m['size']) if 'size' in m else '')
   groups[key]['inputs']+=1;groups[key]['optimal']+=int(row['optimal']);groups[key]['valid']+=int(row['valid']);groups[key]['budget']+=int(row['status'].endswith('budget') or row['failure']=='budget_exhausted')
   if m['family']=='paired' and not row['optimal']:
    raw=bytes.fromhex(row['mask']);pixels={p for p in range(361) if raw[p//8]>>(p%8)&1};path=set(m['path'])
    groups[key]['failed_full_designated_route_plus_extras']+=int(path<=pixels and bool(pixels-path))
   if row['optimal'] and m['path']:groups[key]['max_correct_path_edges']=max(groups[key]['max_correct_path_edges'],len(m['path'])-1)
  results[identity]=dict(roles=roles,by_domain={k:dict(v) for k,v in groups.items()})
 return dict(label='Retrospective saved-raster diagnosis; zero new calls or cases. Structured designated-path coverage is descriptive, not repaired output or causal intervention.',items=results)


if __name__=='__main__':
 writej(OUT/'cost_breakdown.json',costs())
 if (OUT/'final_responses.json.gz').exists():writej(OUT/'raster_diagnostics.json',diagnostics())
