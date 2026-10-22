"""Describe actual explorer survival/breeding from audited saved decisions only."""
import sys,json,sqlite3
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.exploration_continuation import ROOT,RUN,OUT,check,writej
from maze_evolution.deep_campaign_store import unpacked
check();target=OUT/'allocation_persistence.json';assert not target.exists()
assert all(json.loads((OUT/(n+'_audit.json')).read_text())['status']=='PASS' for n in ('search','final'))
c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);c.execute('BEGIN')
initial=unpacked(c.execute('select value from states where stage=-1').fetchone()[0]);registry={i['id']:i for s in initial for i in s['population']}
counts=defaultdict(Counter);seen=defaultdict(Counter);last={};depths=defaultdict(Counter);last_reserved={};stage_rows=[]
for n,g,blob in c.execute("select n,generation,decision from stages where kind='train' and complete=1 order by n"):
 for d in unpacked(blob):
  name=d['name'];explorers=d['explorer_ids'];survivors=set(d['survivors']);r=counts[name]
  r['train_stages']+=1;r['explorer_presentations']+=len(explorers);r['stages_with_explorers']+=bool(explorers)
  r['eligible_cell_presentations']+=d['exploration'].get('quality_eligible_distinct_cells',0)
  if name in last:
   r['prior_explorer_presentations_with_next_train']+=len(last[name]);r['prior_explorers_surviving_next_train']+=len(last[name]&survivors)
   r['reserved_children_with_next_train']+=len(last_reserved[name]);r['reserved_children_surviving_next_train']+=len(last_reserved[name]&survivors)
  last[name]=set(explorers);reserved=set()
  for i in explorers:seen[name][i]+=1;depths[name][registry[i]['mutation_depth']]+=1
  for b in d['births']:
   r[b['parent_policy']]+=1;registry[b['item']['id']]=b['item']
   if b['parent_policy']=='exploration_cycle':reserved.add(b['item']['id'])
  last_reserved[name]=reserved
  stage_rows.append(dict(round=g,condition=name,explorers=len(explorers),reserved_children=len(reserved),eligible_cells=d['exploration'].get('quality_eligible_distinct_cells',0)))
c.close()
result={name:dict(**r,distinct_explorer_identities=len(seen[name]),max_repeated_explorer_presentations=max(seen[name].values(),default=0),explorer_mutation_depth_histogram=dict(depths[name])) for name,r in counts.items()}
audit=json.loads((OUT/'search_audit.json').read_text())
for name,r in result.items():
 a=audit['exploration_allocation_counts'][name]
 assert r['explorer_presentations']==a['selected_explorer_presentations']
 for k in ('random_immigrant','shared_lexicase','exploration_cycle'):assert r.get(k,0)==a.get(k,0)
writej(target,dict(scope='Saved audited training decisions only; presentations are repeated, not independent evidence. Final-round births have no next training survival observation. No new cases/inference/reselection.',populations=result,stages=stage_rows))
print(json.dumps(result,indent=2))
