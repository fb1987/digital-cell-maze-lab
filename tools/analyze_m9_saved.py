"""Post-audit saved-record M9 diagnostics; no new cases, inference or selection."""
import sys,json,sqlite3
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.conditional_regulation import ROOT,OUT,RUN,check,readz,writej
from maze_evolution.conditional_regulation_metrics import capabilities_plus,comparison,upstream_pairs,integration
from maze_evolution.modular_genome import Genome
from tools.inspect_modular_dependencies import describe
from maze_evolution.deep_campaign_store import unpacked
check();assert not (OUT/'saved_diagnostics.json').exists()
for n in ('search','final'):assert json.loads((OUT/f'{n}_audit.json').read_text())['status']=='PASS'
data=readz(OUT/'confirmation.json.gz');responses=readz(OUT/'final_responses.json.gz');rows=responses['rows'];meta=data['metadata']
choices=readz(OUT/'choices.json.gz');ancestry=readz(OUT/'ancestry.json.gz');summary=json.loads((OUT/'summary.json').read_text())
caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
protected=[i for i,roles in choices['roles'].items() if any(r[1]=='protected' for r in roles)]
union={k:set().union(*(caps[i][k] for i in protected)) for k in ('pairs','corridors','ordinary_bases','correct_no_path','success')}
queried=set(data['queries']['all'])
om={m['base']:m for cid,m in meta.items() if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random')}
pm={(m['base'],m['pose']):m for cid,m in meta.items() if cid in queried and m['family']=='paired'}
nominees=sorted({c['child'] for c in choices['comparisons']});diagnostics={};model_details={}
for i,cap in caps.items():
 lengths=defaultdict(list)
 for b in sorted(cap['ordinary_bases']):
  m=om[b];lengths[m['family']+'/'+str(m['size'])].append(len(m['path'])-1)
 model_details[i]=dict(summary=cap['summary'],ordinary_success_lengths=dict(lengths),
  length16plus_successes=sum(len(om[b]['path'])-1>=16 for b in cap['ordinary_bases']),
  length16plus_bases=sum(len(m['path'])-1>=16 for m in om.values()),
  target_pairs=len(upstream_pairs(cap,meta)),target_pair_opportunities=sum(m['graph']!='fork' and m['prefix']>=2 for m in pm.values()),
  beyond_protected_union={k:len(cap[k]-union[k]) for k in union})
for identity in nominees:
 i=choices['items'][identity];c=caps[identity];root=caps[i['root']];chain=[];cursor=identity
 while True:
  b=ancestry[cursor];chain.append(b)
  if not b['item']['parent']:break
  cursor=b['item']['parent']
 assert chain[-1]['item']['id']==i['root']
 mutated=[b for b in chain if b.get('events')];assert len(mutated)==i['mutation_depth']
 new=c['pairs']-root['pairs'];lost=root['pairs']-c['pairs'];nb=c['ordinary_bases']-root['ordinary_bases']
 diagnostics[identity]=dict(root=i['root'],parent=i['parent'],instructions=Genome.from_dict(i['genome']).instructions,
  c6_final_node=i['genome']['blocks'][6][-1],c6_ports=i['genome']['ports'][6],static_dependencies=describe(i['genome']),
  M9_mutation_births=len(mutated),M9_mutation_opportunities=sum(len(b['events']) for b in mutated),last_birth=ancestry[identity],
  versus_root=comparison(c,root,meta),versus_parent=comparison(c,caps[i['parent']],meta) if i['parent'] else None,
  new_corridors=len(c['corridors']-root['corridors']),lost_corridors=len(root['corridors']-c['corridors']),
  new_pairs_by_graph_prefix=dict(Counter(pm[k]['graph']+'/'+str(pm[k]['prefix']) for k in new)),
  lost_pairs_by_graph_prefix=dict(Counter(pm[k]['graph']+'/'+str(pm[k]['prefix']) for k in lost)),
  new_ordinary_details=[dict(base=b,family=om[b]['family'],size=om[b]['size'],edges=len(om[b]['path'])-1,beyond_protected_union=b not in union['ordinary_bases']) for b in sorted(nb)])
# Parent depth and persistence distinguish repeated root sampling from sustained lineage progress.
con=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);con.execute('BEGIN')
states=unpacked(con.execute('select value from states where stage=-1').fetchone()[0]);registry={i['id']:i for s in states for i in s['population']}
counts=defaultdict(Counter);parent_depth=defaultdict(Counter);snapshots={};births=Counter();logical=defaultdict(Counter)
for n,kind,g,blob in con.execute('select n,kind,generation,decision from stages where complete=1 order by n'):
 for d in unpacked(blob):
  for b in d['births']:
   i=b['item'];births['mutation' if b['events'] else 'immigrant']+=1
   if b['events']:
    root=i['root'] if i['root'].startswith('m9/reference/') else 'new_random_origin';key=d['name']+'|'+root
    par=registry[i['parent']];assert par['mutation_depth']+1==i['mutation_depth']
    counts[key]['births']+=1;counts[key]['genotype_noop']+=int(all(e['before']==e['after'] for e in b['events']));counts[key]['parent_depth_zero']+=int(par['mutation_depth']==0)
    counts[key]['parent_is_protected_root']+=int(par['id']==i['root']);parent_depth[key][par['mutation_depth']]+=1
   registry[i['id']]=i
 if kind=='assessment':
  ss=unpacked(con.execute('select value from states where stage=?',(n,)).fetchone()[0]);snapshots[str(g)]={}
  for s in ss:
   roots={i['root'] for i in s['population']+s['archive']};desc={}
   for root in sorted(roots):
    live=[i for i in s['population'] if i['root']==root];archive=[i for i in s['archive'] if i['root']==root]
    key=root if root.startswith('m9/reference/') else 'new_random_origin'
    entry=desc.setdefault(key,dict(live=0,archive=0,max_mutation_depth=0))
    entry['live']+=len(live);entry['archive']+=len(archive);entry['max_mutation_depth']=max(entry['max_mutation_depth'],*(i['mutation_depth'] for i in live+archive))
   snapshots[str(g)][s['name']]=desc
 for blob, in con.execute('select spec from tasks where stage=? order by n',(n,)):
  for e in unpacked(blob):
   for k,i in e['aliases']:logical[states[k]['name']][kind]+=len(e['queries'])
con.close();audit=json.loads((OUT/'search_audit.json').read_text());assert sum(births.values())==audit['births_replayed']==6*52*json.loads((OUT/'session.json').read_text())['generation']
assert {k:dict(v) for k,v in logical.items()}==audit['logical_query_counts']
reference_integration={i:integration(caps[i],caps['m9/reference/quota_parent'],caps['m9/reference/quota_child'],meta,1) for i in protected}
result=dict(reference_integration_capability_only=reference_integration,scope='Saved-record analysis only; no fresh inference, cases, reselection or temporal tracing.',nominees=diagnostics,
 model_details=model_details,nominee_aliases=len(choices['comparisons']),nominee_identities=len(nominees),
 nominee_genotypes=len({Genome.from_dict(choices['items'][i]['genome']).digest for i in nominees}),
 physical_final_models=len(responses['models']),birth_counts=dict(births),
 parent_allocation={k:dict(**v,parent_depth_histogram=dict(parent_depth[k])) for k,v in counts.items()},
 population_root_snapshots=snapshots,logical_query_counts={k:dict(v) for k,v in logical.items()})
writej(OUT/'saved_diagnostics.json',result)
print('Saved diagnostics:',len(nominees),'identities;',result['nominee_genotypes'],'genotypes;',dict(births),flush=True)
