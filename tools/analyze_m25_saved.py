"""M25 saved-only ancestry, novel-unit and cost accounting; no new evaluation."""
import sys,json,sqlite3
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.skill_integration import ROOT,OUT,RUN,check,readz,writej
from maze_evolution.skill_integration_analysis import final_load
from maze_evolution.dormant_evolution_genome import Genome,wrappers
from maze_evolution.breeding_allocation_metrics import capabilities_plus,comparison,upstream_pairs
from maze_evolution.deep_campaign_store import unpacked,hashed,packed

def main():
 check();assert not (OUT/'saved_diagnostics.json').exists() and not (OUT/'allocation_persistence.json').exists()
 assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
 audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('search','final')};assert all(v['status']=='PASS' for v in audits.values())
 choices=readz(OUT/'choices.json.gz');data,rows,models,usage,chain=final_load();queried=set(data['queries']['all']);meta={k:v for k,v in data['metadata'].items() if k in queried};assert len(meta)==1680
 s=json.loads((OUT/'summary.json').read_text());caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()};comparators=s['comparison_identities']
 union={k:set().union(*(caps[i][k] for i in comparators)) for k in ('pairs','corridors','ordinary_bases','correct_no_path','success')}
 ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')};assert len(ordinary)==256
 lengths={b:len(m['path'])-1 for b,m in ordinary.items()};long16={b for b,v in lengths.items() if v>=16}
 details={i:dict(length16plus_bases=len(long16),length16plus_successes=len(c['ordinary_bases']&long16),max_correct_ordinary_edges=max((lengths[b] for b in c['ordinary_bases']),default=None)) for i,c in caps.items()}
 ancestry=readz(OUT/'ancestry.json.gz');nominees={}
 def describe(g):
  ws=wrappers(g);return dict(instructions=g.instructions,recognized_wrappers=len(ws),recognized_const_zero_wrappers=sum(g.body.blocks[m][i].op==1 and g.body.blocks[m][i].a==0 and g.body.blocks[m][i].gate==64 for m,i in ws),append_instruction_headroom=max(0,128-g.instructions))
 archive_genomes={hashed(packed(e['genome'])) for e in choices['comparison_archive']}
 for c in s['conditions']:
  identity=c['child']
  if identity in nominees:continue
  hist=[];cur=identity
  while cur:
   assert cur not in hist;hist.append(cur);cur=ancestry[cur]['item']['parent']
  edits=[e for i in hist if ancestry[i]['phase']=='M25' for e in ancestry[i]['events']];assert len(edits)==c['mutations']
  cap=caps[identity];newordinary=cap['ordinary_bases']-union['ordinary_bases']-caps[c['phase_entry']]['ordinary_bases']
  g=Genome.from_dict(choices['items'][identity]['genome'])
  nominees[identity]=dict(phase_entry=c['phase_entry'],root=c['root'],parent=c['parent'],M25_mutation_births=c['mutations'],inherited_source_study_mutations=c['inherited_mutations'],chain=hist,phase_edit_kinds=dict(Counter(e['kind'] for e in edits)),structure=describe(g),root_comparison=comparison(cap,caps[c['root']],meta),entry_comparison=comparison(cap,caps[c['phase_entry']],meta),new_individual_inputs_beyond_archive=sorted(cap['success']-union['success']),new_upstream_pairs_beyond_archive=len(upstream_pairs(cap,meta)-upstream_pairs(union,meta)),new_ordinary_details=[dict(base=b,family=ordinary[b]['family'],size=ordinary[b]['size'],edges=lengths[b]) for b in sorted(newordinary)],exact_archive_genotype=hashed(packed(g.to_dict())) in archive_genomes,exact_archive_terminal_profiles=[i for i in comparators if all(all(a[k]==b[k] for k in ('mask','status','steps')) for a,b in zip(rows[identity],rows[i]))],archive_correct_set_matches=[i for i in comparators if cap['success']==caps[i]['success']])
 con=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True);con.execute('BEGIN');initial=readz(OUT/'founders.json.gz');labels=[s['policy'] for s in initial];inherited=readz(OUT/'inherited_registry.json.gz');phase_depth={i:0 for i in inherited};extension_depth={i:0 for i in inherited};births=Counter();kinds=defaultdict(Counter);structures=defaultdict(Counter);buckets={}
 for blob, in con.execute("select decision from stages where kind='train' and complete=1 order by n"):
  for event in unpacked(blob):
   name=event['name']
   for b in event['births']:
    item=b['item'];identity=item['id'];parent=item['parent'];edits=b['events'];assert identity not in phase_depth
    phase_depth[identity]=phase_depth[parent]+1 if parent else 0
    extension_depth[identity]=(extension_depth[parent] if parent else 0)+sum(e['kind'] in ('disabled_extension','enabled_extension') for e in edits)
    births['mutation' if edits else 'immigrant']+=1
    if edits:kinds[name][edits[0]['kind']]+=1
    d=describe(Genome.from_dict(item['genome']));structures[name]['wrappers/'+str(d['recognized_wrappers'])]+=1;structures[name]['instructions/'+str(d['instructions'])]+=1
 for spec,result in con.execute('select spec,result from tasks order by stage,n'):
  for e,r in zip(unpacked(spec),unpacked(result)['entries']):
   label='|'.join(sorted({labels[k] for k,identity in e['aliases']}));bucket=buckets.setdefault(label,dict(calls=0,work=0,candidate_seconds=0.))
   for k in bucket:bucket[k]+=r[k]
 latest=unpacked(con.execute('select value from states where stage=(select max(stage) from states)').fetchone()[0]);con.close();persistence={}
 for state in latest:
  pool={i['id']:i for group in ('population','archive') for i in state[group]};persistence[state['name']]=dict(live_archive_identities=len(pool),max_M25_mutation_depth=max(phase_depth[i] for i in pool),max_extension_births_on_chain=max(extension_depth[i] for i in pool),extension_descendants=sum(extension_depth[i]>0 for i in pool),current_structures={i:describe(Genome.from_dict(v['genome'])) for i,v in pool.items()})
 session=json.loads((OUT/'session.json').read_text());assert sum(births.values())==6*52*session['new_rounds']==audits['search']['births_replayed'];assert births['mutation']==6*45*session['new_rounds']
 assert sum(v['calls'] for v in buckets.values())==session['usage']['calls'];assert sum(v['work'] for v in buckets.values())==session['usage']['work']
 writej(OUT/'saved_diagnostics.json',dict(scope='Saved audited data only. Recognized syntax/extension ancestry does not establish active or causal contribution. Exact profile matches describe this panel only.',nominees=nominees,nominee_aliases=len(s['conditions']),nominee_identities=len(nominees),nominee_genotypes=len({hashed(packed(choices['items'][i]['genome'])) for i in nominees}),model_details=details,birth_counts=dict(births)))
 writej(OUT/'allocation_persistence.json',dict(phase_edit_kinds={k:dict(v) for k,v in kinds.items()},born_structures={k:dict(v) for k,v in structures.items()},final_persistence=persistence,search_physical_cost_buckets=buckets,variation_counts=audits['search']['variation_counts'],immediate_birth_survival=audits['search']['immediate_birth_survival'],logical_query_counts=audits['search']['logical_query_counts']))
 print('M25 saved diagnostics PASS',len(nominees),dict(births))
if __name__=='__main__':main()
