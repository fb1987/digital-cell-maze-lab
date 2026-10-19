"""Descriptive saved-raster diagnostics and certificates; no new inference."""
import json
from pathlib import Path
import sys
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_study import compressed_json,read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.junction_distance_data import OUT,BRANCHES,load
from maze_evolution.junction_distance_analysis import pairs,pair_key

def run():
 cases,contexts,meta=load(OUT/'confirmation');models=read_compressed(OUT/'panel.json.gz')
 rows=defaultdict(dict)
 for e in lines(OUT/'normal.jsonl.gz'):rows[e['model']][e['row']['case']]=e['row']
 certificates=[];summary={};pairids=defaultdict(list)
 for cid,m in meta.items():
  if m['family'] in BRANCHES:pairids[pair_key(m)].append(cid)
 for name,rs in rows.items():
  ps=pairs(rs.values(),meta);unique=set();long=[];corridor={}
  for key,passed in ps.items():
   if not passed:continue
   ids=pairids[key];a,b=[cases[c].maze for c in ids]
   unique.add((a.cells,a.start,tuple(sorted((a.goal,b.goal)))))
   if name!='intact':
    record=dict(model=name,base=key[0],shape=key[1],prefix=key[2],family=key[3],pose=key[4],cases=ids,
      shortest_edges=[len(cases[c].path)-1 for c in ids],alternative_edges=[len(meta[c]['alternative'])-1 if meta[c]['alternative'] else None for c in ids])
    certificates.append(record)
    if key[2]==8:long.append(record)
  for shape in ('straight','bent'):
   for p in (1,2,4,6,8):
    rr=[r for c,r in rs.items() if meta[c]['shape']==shape and meta[c]['prefix']==p and meta[c]['family'].startswith('corridor')]
    corridor[f'{shape}/{p}']=dict(optimal=sum(r['optimal'] for r in rr),inputs=len(rr))
  summary[name]=dict(unique_completed_input_pairs=len(unique),complete_pairs=sum(ps.values()),corridors=corridor,
    longest_paired_edges=max((max(len(cases[c].path)-1 for c in pairids[k]) for k,v in ps.items() if v),default=0),
    prefix8_pairs=long,optimal=sum(r['optimal'] for r in rs.values()),legal=sum(r['valid'] for r in rs.values()),
    no_path=sum(r['no_path'] for r in rs.values()),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rs.values()),
    status_counts=dict(Counter(r['status'] for r in rs.values())),step_counts=dict(Counter(r['steps'] for r in rs.values())),
    goal_aware_complete_pairs_by_pose={str(s):sum(v for k,v in ps.items() if k[4]==s) for s in range(8)})
 parent={}
 for n in ('branch_narrow','branch_broad'):
  a=rows[n];b=rows[n+'_parent'];fields=('mask','status','steps','reads','dispatches','active','array_bytes','range_reads')
  parent[n]={field:sum(a[c][field]!=b[c][field] for c in a) for field in fields}
 interventions=defaultdict(list)
 for e in lines(OUT/'interventions.jsonl.gz'):interventions[e['model'],e['mode']].append(e['row'])
 effects={}
 for (name,mode),rr in interventions.items():
  ps=pairs(rr,meta);normal=pairs(rows[name].values(),meta);success=[k for k in ps if normal[k]]
  effects[f'{name}/{mode}']=dict(normal_success_pairs=len(success),retained=sum(ps[k] for k in success),
   gained=sum(v and not normal[k] for k,v in ps.items()),changed_masks=sum(r['mask']!=rows[name][r['case']]['mask'] for r in rr))
 compressed_json(OUT/'successful_pair_certificates.json.gz',certificates)
 (OUT/'saved_raster_diagnostics.json').write_text(json.dumps(dict(models=summary,parent_comparisons=parent,interventions=effects,
  provenance='Descriptive analysis of saved fixed-panel normal/intervention outputs; no additional candidate calls.'),indent=2)+'\n')
 print(json.dumps(dict(pairs={n:s['complete_pairs'] for n,s in summary.items()},parent_comparisons=parent)))

if __name__=='__main__':run()
