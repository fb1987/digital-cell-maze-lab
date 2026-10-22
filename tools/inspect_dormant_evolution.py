"""Read-only M23 journal status and same-panel development comparisons."""
import argparse,json,sqlite3,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.dormant_evolution import RUN,OUT,readz
from maze_evolution.dormant_evolution_checkpoint import lineage
from maze_evolution.exploration_allocation_analysis import complex_sets
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.breeding_allocation_metrics import capabilities_plus as capabilities,upstream_pairs
from maze_evolution.exploration_allocation_metrics import integration
from maze_evolution.dormant_evolution_search import PARENT,SPECIALIST

p=argparse.ArgumentParser();p.add_argument('--assessment',type=int);p.add_argument('--output');args=p.parse_args()
c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
c.execute('BEGIN')
settings={k:unpacked(v) for k,v in c.execute('select key,value from settings')}
result=dict(latest_stage=settings['latest'],usage=settings['usage'],stages=[list(r) for r in c.execute('select n,kind,generation,complete from stages order by n desc limit 3')],assessment_rounds=[r[0] for r in c.execute("select generation from stages where kind='assessment' and complete=1 order by n")])
result['start_generation']=0
result['new_rounds']=result['stages'][0][2] if result['stages'] else 0
result.update(finished=settings.get('finished',False),nomination_stop=settings.get('nomination_stop'),
 elapsed_search_seconds=settings.get('elapsed_search_seconds',0)+(max(0,time.time()-settings['active_session_epoch']) if settings.get('active_session_epoch') else 0),
 pending_task_counts=dict(c.execute("select status,count(*) from tasks where stage in (select n from stages where complete=0) group by status")),
 storage_bytes=sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file()))
if args.assessment is not None:
 row=c.execute("select n,input,decision from stages where kind='assessment' and complete=1 and generation=?",(args.assessment,)).fetchone()
 assert row,'Assessment not complete';n,blob,dec=row;data=unpacked(blob);decisions=unpacked(dec)
 states=unpacked(c.execute('select value from states where stage=?',(n,)).fetchone()[0]);rows=[{} for _ in states]
 for blob, in c.execute('select result from tasks where stage=? order by n',(n,)):
  for e in unpacked(blob)['entries']:
   for k,i in e['aliases']:rows[k][i]=e['rows']
 inherited=readz(OUT/'inherited_registry.json.gz');registry=dict(inherited)
 for blob, in c.execute('select decision from stages where complete=1 and n<=? order by n',(n,)):
  for decision in unpacked(blob):
   for birth in decision['births']:registry[birth['item']['id']]=dict(birth,phase='M23')
 summaries=[]
 for k,s in enumerate(states):
  caps={i:capabilities(rs,data['metadata']) for i,rs in rows[k].items()}
  protected_upstream=set().union(*(upstream_pairs(caps[i['id']],data['metadata']) for i in s['protected']))
  a0=caps['m14/reference/anchor/0']['correct_no_path']
  def describe(i):
   cap=caps[i['id']];history=lineage(i['id'],registry,inherited)
   return dict(id=i['id'],M23_mutation_births=history['phase_mutations'],inherited_mutation_births=history['inherited_mutations'],phase_entry=history['phase_entry'],mutation_depth=i['mutation_depth'],root=i['root'],metrics=cap['summary'],cumulative_integration_descriptive_only=integration(cap,caps[PARENT],caps[SPECIALIST],data['metadata'],i['mutation_depth']),target_upstream_pairs=len(upstream_pairs(cap,data['metadata'])),new_upstream_beyond_protected=len(upstream_pairs(cap,data['metadata'])-protected_upstream),a0_no_path_retention=len(cap['correct_no_path']&a0)/len(a0) if a0 else None,complexity={key:len(v) for key,v in complex_sets(cap,data['metadata']).items()})
  summaries.append(dict(condition=s['name'],nominees=[describe(i) for i in s['nominees']],frozen=[describe(i) for i in s['frozen']],protected=[describe(i) for i in s['protected']]))
 result['development_assessment']=dict(round=args.assessment,conditions=summaries,independent_confirmation=False,novelty_scope='14 protected references only; final novelty excludes full M22 historical comparison archive as well. No development result is confirmation.')
c.close()
text=json.dumps(result,indent=2)
if args.output:
 target=Path(args.output);assert not target.exists(),'Preserve existing assessment packets';target.write_text(text+'\n')
else:print(text)
