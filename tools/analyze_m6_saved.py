"""Retrospective M6 evidence from saved records only: no inference or selection."""
import sys,json,sqlite3
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.upstream_continuation import ROOT,OUT,RUN,check,readz,writej
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.upstream_continuation_metrics import capabilities_plus,comparison
from maze_evolution.modular_genome import Genome

check();target=OUT/'saved_diagnostics.json';assert not target.exists()
data=readz(OUT/'confirmation.json.gz');rows=readz(OUT/'final_responses.json.gz')['rows'];meta=data['metadata']
choices=readz(OUT/'choices.json.gz');ancestry=readz(OUT/'ancestry.json.gz')
child='m6/modular/0/single/g900/b17';item=choices['items'][child];root=item['root'];parent=item['parent']
caps={i:capabilities_plus(r,meta) for i,r in rows.items()}
protected=[i for i,roles in choices['roles'].items() if any(r[1]=='protected' for r in roles)]
union={k:set().union(*(caps[i][k] for i in protected)) for k in ('pairs','corridors','ordinary_bases','correct_no_path','false','success')}
pm={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
om={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
route_lengths={}
for i in (child,parent,root,'m6/reference/a1/standard/0191','m6/reference/a0/standard/0434'):
 cc=caps[i];by=defaultdict(list)
 for b in sorted(cc['ordinary_bases']):
  m=om[b];by[m['family']+'/'+str(m['size'])].append(len(m['path'])-1)
 route_lengths[i]=dict(ordinary_success_lengths_by_domain=dict(by),ordinary_success_bases=sorted(cc['ordinary_bases']),
  pairs_by_pose=dict(Counter(str(k[1]) for k in cc['pairs'])),
  beyond_protected={k:len(cc[k]-union[k]) for k in ('pairs','corridors','ordinary_bases','correct_no_path','success')})
new=caps[child]['pairs']-caps[root]['pairs']
newpairrows=[r for r in rows[child] if meta[r['case']]['family']=='paired' and (meta[r['case']]['base'],meta[r['case']]['pose']) in new]
line=[];cursor=child
while True:
 b=ancestry[cursor];line.append(b)
 if not b['item']['parent']:break
 cursor=b['item']['parent']
assert line[-1]['item']['id']==root
actual=[b for b in line if b.get('events')]
assert len(actual)==item['mutation_depth']
con=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);con.execute('BEGIN')
births=Counter();per=defaultdict(Counter);snapshots={};logical=defaultdict(Counter)
for n,kind,g,blob in con.execute('select n,kind,generation,decision from stages where complete=1 order by n'):
 for d in unpacked(blob):
  for b in d['births']:
   i=b['item'];category=i['root'] if i['root'].startswith('m6/reference/') else 'new_random_origin'
   key=('immigrant/' if not b['events'] else 'mutation/')+category
   births[key]+=1;per[d['name']][key]+=1
 if kind=='assessment' and g in (0,100,400,800,900,1200,1796):
  states=unpacked(con.execute('select value from states where stage=?',(n,)).fetchone()[0])
  snapshots[str(g)]={s['name']:dict(Counter(i['root'] if i['root'].startswith('m6/reference/') else 'new_random_origin' for i in s['population'])) for s in states}
 for spec, in con.execute('select spec from tasks where stage=? order by n',(n,)):
  for e in unpacked(spec):
   for k,i in e['aliases']:logical[str(k)][kind]+=len(e['queries'])
con.close()
assert sum(births.values())==280176
r=dict(scope='Retrospective saved-record analysis; no new inference, cases, selection or tracing.',
 nominee=dict(id=child,root=root,parent=parent,instructions=Genome.from_dict(item['genome']).instructions,
  M6_mutation_births=len(actual),M6_mutation_opportunities=sum(len(b['events']) for b in actual),
  last_birth=ancestry[child],new_pairs_vs_root=len(new),new_pairs_by_graph_prefix=dict(Counter(pm[k]['graph']+'/'+str(pm[k]['prefix']) for k in new)),
  new_pair_poses=sorted({k[1] for k in new}),new_pair_contexts=len({pm[k]['template'] for k in new}),
  new_pair_route_lengths=dict(Counter(str(len(meta[r['case']]['path'])-1) for r in newpairrows)),
  versus_root=comparison(caps[child],caps[root],meta),versus_parent=comparison(caps[child],caps[parent],meta)),
 route_lengths=route_lengths,birth_counts=dict(births),birth_counts_per_population={k:dict(v) for k,v in per.items()},
 population_root_snapshots=snapshots,logical_query_counts={k:dict(v) for k,v in logical.items()},
 physical_final_models=len(readz(OUT/'final_responses.json.gz')['models']),
 nominee_aliases=len(choices['comparisons']),nominee_identities=len({c['child'] for c in choices['comparisons']}),
 nominee_genotypes=len({Genome.from_dict(choices['items'][c['child']]['genome']).digest for c in choices['comparisons']}))
writej(target,r)
print(json.dumps({k:r[k] for k in ('birth_counts','logical_query_counts','physical_final_models','nominee_genotypes')},indent=2))
print('Final roots',json.dumps(snapshots['1796'],indent=2))
print('Route lengths',json.dumps(route_lengths,indent=2))
print('Last events',ancestry[child]['events'])
