"""Post-hoc full-component and state-period summaries, using stored traces only."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collections import Counter
import numpy as np
from maze_evolution.branch_overgrowth_data import *
from maze_evolution.routing_transfer import lines,canonical
from maze_evolution.routing_mechanism_study import unpack_history
from maze_evolution.routing_mechanism_audit import component

p=read_compressed(OUT/'panel.json.gz');a=read_compressed(OUT/'analysis.json.gz');cases,_,meta=load(OUT/'confirmation');summary={}
for name,pid in p['aliases'].items():
    tasks=[v for t in a['trace_details'] if t['model']==pid and t['mode']=='normal' for v in t['tasks']]
    if not tasks:continue
    reps=[v['repeated_full_state'] for v in tasks if v['repeated_full_state']]
    summary[name]=dict(normal_traces=len(tasks),failed=sum(not v['normal_optimal'] for v in tasks),failed_ever_correct=sum(not v['normal_optimal'] and bool(v['shortest_ticks']) for v in tasks),failed_later_correct=sum(not v['normal_optimal'] and bool(v['after_normal_shortest']) for v in tasks),period_counts=dict(Counter(str(v['period']) for v in reps)),first_repeat_range=[min(v['again'] for v in reps),max(v['again'] for v in reps)] if reps else None,final_full_source_component=0)
reverse={pid:name for name,pid in p['aliases'].items() if name in summary}
for e in lines(OUT/'confirmation/responses.jsonl.gz'):
    if e['scope']!='trace' or e['mode']!='normal':continue
    m=cases[e['row']['case']].maze;h=unpack_history(e['history']);lit=set(np.flatnonzero(h[-1,2]>0));same=lit==set(component(m,m.start));summary[reverse[e['model']]]['final_full_source_component']+=same
packet=canonical(dict(post_hoc=True,new_candidate_calls=0,results=summary))
(OUT/'descriptive_summary.json').write_text(json.dumps(packet,indent=2)+'\n')
print(json.dumps(packet,indent=2))
