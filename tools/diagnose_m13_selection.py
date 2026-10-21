"""Post-hoc first-training-exposure diagnosis from saved M13 records only."""
import json,sqlite3,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_scope import ROOT,OUT,RUN,check,writej
from maze_evolution.deep_campaign_store import unpacked,packed,hashed
from maze_evolution.mutation_scope_metrics import capabilities_plus,FIELDS,PARENT
check();assert not (OUT/'selection_diagnostics.json').exists()
assert all(json.loads((OUT/(n+'_audit.json')).read_text())['status']=='PASS' for n in ('search','final'))
c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
states=unpacked(c.execute('select value from states where stage=-1').fetchone()[0]);registry={i['id']:i for s in states for i in s['population']};events={};totals=defaultdict(Counter);seen=set()
for n,kind,g,inp,dec in c.execute('select n,kind,generation,input,decision from stages where complete=1 order by n'):
 decisions=unpacked(dec)
 if kind=='train' and g>0:
  data=unpacked(inp);rs=[{} for _ in states]
  for blob, in c.execute('select result from tasks where stage=? order by n',(n,)):
   for e in unpacked(blob)['entries']:
    for k,i in e['aliases']:rs[k][i]=e['rows']
  for k,d in enumerate(decisions):
   stats=totals[d['name']];protected=[i['id'] for i in states[k]['protected']]
   def signature(rows):return hashed(packed([(r['case'],r['status'],r['mask']) for r in rows]))
   signatures={signature(rs[k][i]) for i in protected}
   caps={i:capabilities_plus(rs[k][i],data['metadata']) for i in protected}
   union=set().union(*(caps[i]['success'] for i in protected));parent=caps[PARENT]
   survivors=set(d['survivors'])
   for identity,rows in rs[k].items():
    i=registry[identity]
    if i['birth']!=g or not events.get(identity):continue
    assert identity not in seen;seen.add(identity);stats['newborn_mutants_first_train_exposure']+=1
    if i['root'] not in caps:stats['excluded_unprotected_immigrant_root']+=1;continue
    stats['protected_root_descendants']+=1;child=capabilities_plus(rows,data['metadata'])
    flags=dict(survived=identity in survivors,
     different_terminal_behavior_from_root=signature(rows)!=signature(rs[k][i['root']]),
     terminal_behavior_unmatched_by_any_protected=signature(rows) not in signatures,
     any_successful_input_beyond_protected_union=bool(child['success']-union),
     retains_all_fixed_parent_skills=all(parent[f] and parent[f]<=child[f] for f in FIELDS) and not child['false'])
    for label,flag in flags.items():
     if flag:
      stats[label]+=1
      if identity in survivors:stats[label+'_and_survived']+=1
    if flags['terminal_behavior_unmatched_by_any_protected'] and flags['retains_all_fixed_parent_skills']:
     stats['novel_behavior_and_full_parent_retention']+=1
     if identity in survivors:stats['novel_behavior_and_full_parent_retention_and_survived']+=1
 for d in decisions:
  for b in d['births']:registry[b['item']['id']]=b['item'];events[b['item']['id']]=b['events']
c.close()
byarm=defaultdict(Counter)
for name,x in totals.items():byarm[name.split('/')[-1]].update(x)
result=dict(scope='Exploratory saved development records, not registered primary or fresh confirmation. No inference, new cases, reselection or training.',
 definition='Each newborn mutant counted once on its first train panel (birth rounds1..63). Round64 newborns have assessment only, not included. Root comparisons restrict to descendants of protected references; immigrant-root descendants separately counted/excluded. Behavior means identical status+terminal mask on that finite panel, not semantic equivalence. Successful input is individual case, not complete paired/both-pose capability. Survival is into the next population after that panel.',
 by_population={k:dict(v) for k,v in totals.items()},by_arm={k:dict(v) for k,v in byarm.items()},unique_newborn_mutants=len(seen))
writej(OUT/'selection_diagnostics.json',result);print(json.dumps(result,indent=2))
