"""M11 fixed-pool retention calibration. No evolution, mutation or nominee selection."""
import argparse,json,time,sqlite3,subprocess,shutil,multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from .retention_pressure import ROOT,readz,writez,writej,sha,controls,organism,evaluate_task
from .retention_pressure_data import validation,confirmation
from .retention_pressure_metrics import capabilities_plus,integration,FIELDS,PARENT,SPECIALIST
from .retention_pressure_search import integration_rank
from .family_evolution_data import AccessData
from .reboot_data import ordinary
from .datasets import manifest
from .deep_campaign_store import Journal,writer_lock,packed,unpacked,hashed
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .foundation_pair_confirm import normal_row
from .baselines import baseline
from .routing_transfer import canonical
from . import deep_campaign as shared

OUT=ROOT/'results/retention_bank';RUN=ROOT/'runs/retention_bank_m11'
STRATA=[('perfect',11,1,7),('perfect',15,1,7),('random',9,1,7),('random',15,1,7),('perfect',11,8,15),('perfect',15,8,15)]
CONFIG=dict(phase='M11',seed=2026102130,validation_seed=2026102140,confirmation_seed=2026102150,
 workers=10,replicates=3,draws_per_stratum=1024,quota=4,session_wall_seconds=1200,
 call_cap=2000000,work_cap=10**13,memory_bytes=8*2**30,storage_bytes=4*2**30,disk_free_floor_bytes=16*2**30)
GATED=['m10/reference/gated_partial','m10/reference/gated_specialist']

def resource_reason(directory,config,started):
 if time.monotonic()-started>=config['session_wall_seconds']:return 'wall'
 if shared.process_resources()>=config['memory_bytes']:return 'memory'
 if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
 if sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file())>=config['storage_bytes']:return 'storage'

def check():
 r=json.loads((OUT/'registration.json').read_text())
 for p,h in r['files'].items():assert sha(ROOT/p)==h,p
 prior=json.loads((ROOT/'results/retention_pressure/completion.json').read_text())
 for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
 now=shared.source_manifest();assert all(r[k]==now[k] for k in ('python','dependencies'))
 return json.loads((OUT/'config.json').read_text())

def pushed(path):
 assert not subprocess.check_output(['git','status','--porcelain','--',str(path)],cwd=ROOT,text=True)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)==subprocess.check_output(['git','rev-parse','@{u}'],cwd=ROOT)

def pool_models():
 old=readz(ROOT/'results/retention_pressure/choices.json.gz');models={}
 for i,item in old['items'].items():
  m=dict(representation=old['representations'][i],genome=item['genome']);key=hashed(packed(m))
  models.setdefault(key,dict(model=m,aliases=[]))['aliases'].append(i)
 for c in controls():
  m=dict(representation=c['representation'],genome=c['genome']);key=hashed(packed(m));assert key not in models
  models[key]=dict(model=m,aliases=[c['id']])
 return [dict(models[k],digest=k) for k in sorted(models)]

def build_draws(rep,previous,config=CONFIG,guard=None):
 d=AccessData(config['seed']+rep,previous);strata=[];ids=[]
 for index,(family,size,lo,hi) in enumerate(STRATA):
  if guard:guard()
  qq=ordinary(d,f'm11bank/{rep}/stratum{index}',[(family,size,config['draws_per_stratum'])])
  bases=[]
  for j in range(0,len(qq),2):
   a,b=qq[j:j+2];edges=len(d.metadata[a]['path'])-1
   if lo<=edges<=hi:bases.append([a,b]);ids.extend([a,b])
  strata.append(dict(index=index,family=family,size=size,lo=lo,hi=hi,raw_draws=config['draws_per_stratum'],eligible_bases=bases))
 return dict(kind='draw',generation=rep,mazes=manifest(d.cache[c] for c in ids),
  metadata={c:d.metadata[c] for c in ids},queries=ids,strata=strata,new_layouts=sorted(d.layouts-set(previous)),rejections=d.rejections)

def select_bank(data,rows,quota):
 rs={r['case']:r for r in rows};strata=[];selected=[]
 for s in data['strata']:
  good=[q for q in s['eligible_bases'] if all(rs[c]['optimal'] for c in q)]
  chosen=good[:quota];selected.extend(c for q in chosen for c in q)
  strata.append(dict(index=s['index'],successful_bases=len(good),selected_bases=chosen,required=quota))
 return dict(complete=all(len(s['selected_bases'])==quota for s in strata),selected=selected,strata=strata,
  selection='first quota reference-successful pairs in generated order; only fixed parent outputs used')

def build_panels(rep,previous,draw,selection,config=CONFIG):
 assert selection['complete']
 base=validation(config['validation_seed']+rep,previous);old=base['queries']['all']
 ordinary_ids={c for c in old if base['metadata'][c]['family'] in ('ordinary_perfect','ordinary_random')}
 assert len(ordinary_ids)==48 and len(selection['selected'])==48
 bank=[c for c in old if c not in ordinary_ids]+selection['selected'];allids=list(dict.fromkeys(old+bank))
 meta={c:base['metadata'][c] for c in old};meta.update({c:draw['metadata'][c] for c in selection['selected']})
 for m in meta.values():
  length=len(m['path'])-1;m['length_bin']='none' if length<0 else 'short' if length<8 else 'medium' if length<16 else 'long'
 mazes={m['case_id']:m for m in base['mazes']+draw['mazes']}
 return dict(kind='panel',generation=rep,mazes=[mazes[c] for c in allids],metadata=meta,queries=allids,
  methods=dict(current=old,bank=bank),new_layouts=base['new_layouts'],selection=selection)

def specs(data,models):
 chosen=[m for m in models if PARENT in m['aliases']] if data['kind']=='draw' else models
 assert chosen
 tasks=[]
 for m in chosen:
  for start in range(0,len(data['queries']),256):
   tasks.append([dict(model=m['model'],aliases=m['aliases'],queries=data['queries'][start:start+256])])
 return tasks

def merge_results(results):
 rows={}
 for result in results:
  for e in result['entries']:
   for i in e['aliases']:rows.setdefault(i,[]).extend(e['rows'])
 return rows

def panel_metrics(data,rows,models):
 result={}
 for method,ids in data['methods'].items():
  wanted=set(ids);rs={i:[r for r in rr if r['case'] in wanted] for i,rr in rows.items()}
  assert all(len(v)==392 for v in rs.values())
  caps={i:capabilities_plus(v,data['metadata']) for i,v in rs.items()};parent=caps[PARENT]
  metrics={}
  for m in models:
   i=m['aliases'][0];c=caps[i];keep=len(c['ordinary_bases']&parent['ordinary_bases'])
   metrics[m['digest']]=dict(aliases=m['aliases'],parent_ordinary_total=len(parent['ordinary_bases']),parent_ordinary_retained=keep,
    ordinary_retention=keep/len(parent['ordinary_bases']) if parent['ordinary_bases'] else None,
    ordinary_pass=bool(parent['ordinary_bases'] and keep==len(parent['ordinary_bases']) and not c['false']),
    metrics=c['summary'],integration_capability=integration(c,parent,caps[SPECIALIST],data['metadata'],1),
    rank=integration_rank(dict(id=i),rs,data['metadata'],caps))
  diagnostic=[m for m in models if not m['aliases'][0].startswith('control/')]
  rank=sorted(diagnostic,key=lambda m:(tuple(-x for x in metrics[m['digest']]['rank']),m['aliases'][0]))
  result[method]=dict(queries=392,models=metrics,parent_ordinary_total=len(parent['ordinary_bases']),
   gated_ordinary_denominators={i:len(caps[i]['ordinary_bases']) for i in GATED},ranking=[m['digest'] for m in rank])
 return canonical(result)

def stage(j,data,models,executor,started,config):
 assert resource_reason(RUN,config,started) is None,'M11 stage entry guard'
 n=j.prepare(data,specs(data,models));reason=shared.run_stage(j,n,dict(data,queries={'all':data['queries']}),executor,config,started,[False])
 if reason:raise RuntimeError('M11 resource guard: '+reason)
 assert resource_reason(RUN,config,started) is None,'M11 stage completion guard'
 rows=merge_results(j.results(n))
 decision=select_bank(data,rows[PARENT],config['quota']) if data['kind']=='draw' else panel_metrics(data,rows,models) if data['kind']=='panel' else dict(frozen_pool_no_selection=True)
 j.commit(n,j.state(),decision);print(json.dumps(dict(stage=n,kind=data['kind'],rep=data['generation'],usage=j.get('usage'))),flush=True)
 return decision

def calibrate():
 config=check();pushed(OUT/'registration.json');RUN.mkdir(exist_ok=True);start=time.monotonic()
 shared.evaluate_task=evaluate_task;shared.resource_reason=resource_reason
 with writer_lock(RUN):
  j=Journal(RUN);assert j.get('config') is None,'Never silently resume'
  previous=set(readz(OUT/'exclusions.json.gz')['hashes']);models=readz(OUT/'pool.json.gz')
  j.initialize(config,dict(pool_sha=sha(OUT/'pool.json.gz')),previous);banks=[];panels=[]
  def guard():assert resource_reason(RUN,config,start) is None,'M11 generation guard'
  try:
   with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
    for rep in range(config['replicates']):
     guard();draw=build_draws(rep,previous,config,guard);selection=stage(j,draw,models,ex,start,config);previous.update(draw['new_layouts']);banks.append(selection)
     if not selection['complete']:
      writej(OUT/'construction_shortfall.json',dict(rep=rep,selection=selection,usage=j.get('usage'),not_extended=True))
      raise RuntimeError('Declared reference-success quota not filled; scientific shortfall, no extra draws')
     data=build_panels(rep,previous,draw,selection,config);panels.append(stage(j,data,models,ex,start,config));previous.update(data['new_layouts'])
   j.put('calibration_complete',True);j.db.commit()
   writez(OUT/'calibration_freeze.json.gz',dict(banks=banks,panels=panels,chain=j.verify_chain(),pool_sha=sha(OUT/'pool.json.gz'),no_model_selection=True))
   write_layouts('calibration_exclusions',previous)
   writej(OUT/'calibration_session.json',dict(status='complete',usage=j.get('usage'),wall_seconds=time.monotonic()-start,rss_peak_bytes=shared._peak_rss))
  finally:j.close()

def final():
 config=check();pushed(OUT/'calibration_freeze.json.gz');assert json.loads((OUT/'calibration_audit.json').read_text())['status']=='PASS'
 start=time.monotonic();shared.evaluate_task=evaluate_task;shared.resource_reason=resource_reason
 with writer_lock(RUN):
  j=Journal(RUN);assert j.get('calibration_complete') and not j.get('final_complete') and not j.pending()
  before=j.get('usage');data=confirmation(config['confirmation_seed'],j.layouts());data['queries']=data['queries']['all'];data['kind']='final';data['generation']=3
  with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:stage(j,data,readz(OUT/'pool.json.gz'),ex,start,config)
  writez(OUT/'confirmation.json.gz',data);j.put('final_complete',True);j.db.commit()
  usage={k:j.get('usage')[k]-v for k,v in before.items()};writej(OUT/'final_session.json',dict(status='complete',usage=usage,wall_seconds=time.monotonic()-start,rss_peak_bytes=shared._peak_rss));j.close()

def summary(data,rows,models,freeze):
 caps={i:capabilities_plus(rs,data['metadata']) for i,rs in rows.items()};parent=caps[PARENT];den=len(parent['ordinary_bases']);truth={}
 for m in models:
  i=m['aliases'][0];c=caps[i];ret=len(c['ordinary_bases']&parent['ordinary_bases'])/den if den else None
  truth[m['digest']]=dict(aliases=m['aliases'],ordinary_retention=ret,severe_loss=ret is not None and ret<.9,
    parent_retained=len(c['ordinary_bases']&parent['ordinary_bases']),parent_total=den,metrics=c['summary'])
 diag=[m['digest'] for m in models if not m['aliases'][0].startswith('control/')];severe={k for k in diag if truth[k]['severe_loss']}
 shared_key=next(m['digest'] for m in models if 'm10/reference/shared_child' in m['aliases']);comparisons=[]
 for rep,panel in enumerate(freeze['panels']):
  methods={}
  for method,p in panel.items():
   accepted={k for k in diag if p['models'][k]['ordinary_pass']};falses=accepted&severe
   positive_ids=[PARENT,'control/intact_flat','control/intact_modular']
   controls_ok=all(next(v for v in p['models'].values() if i in v['aliases'])['ordinary_pass'] for i in positive_ids)
   false_rejections={k for k in diag if truth[k]['ordinary_retention']==1 and k not in accepted}
   methods[method]=dict(false_rejections=len(false_rejections),false_reject_genotypes=sorted(false_rejections),false_accepts=len(falses),false_accept_genotypes=sorted(falses),accepted_genotypes=sorted(accepted),positive_controls_pass=controls_ok,
    top_rank_genotype=p['ranking'][0],top_rank_confirmation=truth[p['ranking'][0]])
  nonvacuous=den>=16 and len(severe)>=2 and shared_key in severe and panel['current']['parent_ordinary_total']>0 and panel['bank']['parent_ordinary_total']==24 and all(v>=8 for v in panel['bank']['gated_ordinary_denominators'].values())
  comparisons.append(dict(rep=rep,methods=methods,nonvacuous=nonvacuous,difference=methods['current']['false_accepts']-methods['bank']['false_accepts'],
   bank_ready=nonvacuous and methods['bank']['false_accepts']==0 and all(m['positive_controls_pass'] for m in methods.values())))
 ds=[c['difference'] for c in comparisons]
 return canonical(dict(status='evaluated',calibration_not_evolution=True,truth_parent_ordinary_denominator=den,diagnostic_genotypes=len(diag),severe_loss_genotypes=len(severe),
  comparisons=comparisons,descriptive_bank_support=all(c['nonvacuous'] for c in comparisons) and sum(x>0 for x in ds)>=2 and sum(ds)>0,
  ready_for_new_protocol=all(c['bank_ready'] for c in comparisons),truth=truth,
  limitation='Related fixed genomes; three banks are not independent evolutionary origins. Reference-conditioned bank is biased fitness design. No universal sensitivity, general solving, speed or new acquisition claim.'))

def analyze():
 check();assert not (OUT/'summary.json').exists()
 j=Journal(RUN);assert j.get('final_complete');n=j.get('latest');data=unpacked(j.db.execute('select input from stages where n=?',(n,)).fetchone()[0]);rows=merge_results(j.results(n))
 result=summary(data,rows,readz(OUT/'pool.json.gz'),readz(OUT/'calibration_freeze.json.gz'));writej(OUT/'summary.json',result);writez(OUT/'final_responses.json.gz',rows);j.close()

def audit(which):
 config=check();target=OUT/(which+'_audit.json');assert not target.exists();start=time.monotonic();cpu_start=shared.total_cpu();models=readz(OUT/'pool.json.gz')
 with writer_lock(RUN):
  j=Journal(RUN);chain=j.verify_chain();previous=set(readz(OUT/'exclusions.json.gz')['hashes']);draws={};selections={};panels=[];grades=0;stages=0
  for n,blob,decision in j.db.execute('select n,input,decision from stages where complete=1 order by n'):
   data=unpacked(blob);saved=unpacked(decision);kind=data['kind'];rep=data['generation']
   if which=='calibration' and kind=='final':continue
   if which=='final' and kind!='final':previous.update(data['new_layouts']);continue
   assert resource_reason(RUN,dict(config,session_wall_seconds=1800),start) is None,'Audit guard'
   if kind=='draw':expected=build_draws(rep,previous,config);draws[rep]=data
   elif kind=='panel':expected=build_panels(rep,previous,draws[rep],selections[rep],config)
   else:
    expected=confirmation(config['confirmation_seed'],previous);expected['queries']=expected['queries']['all'];expected.update(kind='final',generation=3)
   assert canonical(expected)==data,(n,'corpus');previous.update(data['new_layouts'])
   assert [s for _,s,_ in j.tasks(n)]==specs(data,models)
   wanted=set(data['queries']);cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in wanted]);checker=Checker(cases)
   for spec,result,h in j.db.execute('select spec,result,result_hash from tasks where stage=? order by n',(n,)):
    assert hashed(result)==h;e=unpacked(spec)[0];r=unpacked(result)['entries'][0]
    assert e['aliases']==r['aliases'] and e['queries']==[x['case'] for x in r['rows']];org=organism(e['model'])
    for row in r['rows']:
     checker.row(row);o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;grades+=1
   rows=merge_results(j.results(n))
   if kind=='draw':actual=select_bank(data,rows[PARENT],config['quota']);selections[rep]=actual
   elif kind=='panel':actual=panel_metrics(data,rows,models);panels.append(actual)
   else:
    actual=dict(frozen_pool_no_selection=True)
    assert summary(data,rows,models,readz(OUT/'calibration_freeze.json.gz'))==json.loads((OUT/'summary.json').read_text())
    baseline_rows={}
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
     rr=[]
     for o in cases.values():
      m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];rr.append(r)
     baseline_rows[name]=rr
    writez(OUT/'baselines.json.gz',baseline_rows)
   assert actual==saved,(n,'selection/metrics')
   if kind!='draw':
    for i,rr in rows.items():
     if i.startswith('control/'):assert all(r['optimal'] or r['no_path'] for r in rr)
   stages+=1;print('AUDIT',which,n,grades,flush=True)
  if which=='calibration':
   frozen=readz(OUT/'calibration_freeze.json.gz');assert panels==frozen['panels'] and [selections[i] for i in range(config['replicates'])]==frozen['banks'] and chain==frozen['chain']
  else:assert previous==j.layouts()
  session=json.loads((OUT/(which+'_session.json')).read_text());assert session['usage']['calls']==grades
  writej(target,dict(status='PASS',stages=stages,all_native_replays=grades,all_independent_grades=grades,selection_corpus_metrics_replayed=True,
   source_hashes_verified=True,chain=chain,wall_seconds=time.monotonic()-start,cpu_seconds=shared.total_cpu()-cpu_start,rss_peak_bytes=shared._peak_rss,conventional_calls=3*len(cases) if which=='final' else 0,
   limitation='Shared native VM and selection implementation with independent raster grader, not independent full interpreter.'));j.close()

def write_layouts(name,hashes):
 directory=OUT/(name+'_parts');assert not directory.exists();directory.mkdir();ordered=sorted(hashes);parts=[]
 for n,start in enumerate(range(0,len(ordered),1000000)):
  path=directory/f'part{n:03}.json.gz';values=ordered[start:start+1000000];writez(path,dict(hashes=values))
  parts.append(dict(path=str(path.relative_to(ROOT)),count=len(values),sha256=sha(path)))
 writej(OUT/(name+'.json'),dict(format='chunked-layout-hashes-v1',count=len(ordered),parts=parts))

def load_layouts(path):
 index=json.loads(Path(path).read_text());result=set()
 for part in index['parts']:
  p=ROOT/part['path'];assert sha(p)==part['sha256'];values=readz(p)['hashes'];assert len(values)==part['count'] and not result.intersection(values);result.update(values)
 assert len(result)==index['count'];return result


def prepare():
 assert not OUT.exists();OUT.mkdir();old=json.loads((ROOT/'results/retention_pressure/completion.json').read_text())
 for p,h in old['files'].items():assert sha(ROOT/p)==h,p
 writej(OUT/'config.json',CONFIG);writez(OUT/'pool.json.gz',pool_models())
 # Already-excluded M10 fixtures: software-only inputs, no new scientific cases.
 fixture=readz(ROOT/'results/retention_pressure/fixture.json.gz');writez(OUT/'fixture.json.gz',fixture)
 previous=readz(ROOT/'results/retention_pressure/whole_layout_exclusions.json.gz');writez(OUT/'exclusions.json.gz',previous)
 writej(OUT/'preparation.json',dict(frozen_models=len(pool_models()),old_hashes_verified=len(old['files']),scientific_cases_generated=0,scientific_calls=0,fixture_origin='M10 excluded fixture'))

def register():
 assert not (OUT/'registration.json').exists();r=shared.source_manifest()
 paths=[*OUT.glob('*'),ROOT/'docs/RETENTION_BANK.md',ROOT/'tests/test_retention_bank.py',ROOT/'tools/run_m11_workflow.py',ROOT/'tools/preflight_m11.py',ROOT/'results/retention_pressure/completion.json']
 r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()});r.update(phase='M11',scientific_calls=0,scientific_cases_generated=0)
 writej(OUT/'registration.json',r)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','calibrate','final','analyze','audit_calibration','audit_final']);a=p.parse_args()
 if a.action.startswith('audit_'):audit(a.action[6:])
 else:globals()[a.action]()
