"""Post-hoc diagnosis of saved M2 outputs and selected instructions; zero inference."""
import sys,json,hashlib
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.wave_accessibility import OUT,connect,entries,readz,writej
from maze_evolution.deep_campaign_store import packed,hashed
from tools.inspect_modular_dependencies import describe

aa=json.loads((OUT/'anchors.json').read_text());pool=readz(OUT/'pool.json.gz');db,data,_,_=connect()
def behavior(rr):return hashed(packed([(r['case'],r['status'],r['mask']) for r in rr]))
observed={}
for s,rr in entries(db):
    value=behavior(rr)
    for i in s['aliases']:observed[i]=value
db.close();counts={}
for k,a in enumerate(aa):
    for depth in (1,2):
        items=[i for i in pool['items'] if i.get('anchor')==a['id'] and i['depth']==depth]
        counts[f'a{k}/d{depth}']=dict(draws=len(items),distinct_terminal_behaviors=len({observed[i['id']] for i in items}),
            same_terminal_behavior_as_anchor=sum(observed[i['id']]==observed[a['id']] for i in items),
            changed_genotype_same_terminal_behavior=sum(i['changed'] and observed[i['id']]==observed[a['id']] for i in items))
selected={i['id']:i for i in aa}
for c in readz(OUT/'choices.json.gz'):selected[c['item']['id']]=c['item']
details={}
for i,item in selected.items():
    details[i]=dict(dependencies=describe(item['genome']),events=item.get('events',[]))
    if item.get('anchor'):
        before=next(a['genome'] for a in aa if a['id']==item['anchor'])
        details[i]['different_blocks']=[k for k in range(8) if before['blocks'][k]!=item['genome']['blocks'][k] or before['ports'][k]!=item['genome']['ports'][k]]
        if item.get('intermediate') is not None:details[i]['intermediate_dependencies']=describe(item['intermediate'])
writej(OUT/'posthoc_diagnosis.json',dict(label='Post-hoc saved-output and static-instruction analysis; zero new calls',
    cohorts=counts,selected=details,limitations=['Behavior identity means identical terminal statuses and rasters on the392 screening inputs; not all states, ticks or costs, and not global semantic equivalence.',
    'Static dependency cones overapproximate potential causal activity; no new interventions or forced traces.']))
print(json.dumps(counts,indent=2))
