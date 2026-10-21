import json
from copy import deepcopy
from contextlib import nullcontext
from maze_evolution import retention_bank as m


def test_fixed_pool_exact_m10_sources_and_dedup():
 pool=m.readz(m.OUT/'pool.json.gz');assert pool==m.pool_models();old=m.readz(m.ROOT/'results/retention_pressure/choices.json.gz')
 assert len({x['digest'] for x in pool})==len(pool)
 assert sum(len(x['aliases']) for x in pool)==len(old['items'])+2
 for x in pool:
  for i in x['aliases']:
   if not i.startswith('control/'):assert x['model']['genome']==old['items'][i]['genome']
 assert not any(i.startswith('m11/') for x in pool for i in x['aliases'])


def test_reference_only_selection_order_and_shortfall():
 data=dict(strata=[dict(index=0,eligible_bases=[['a','b'],['c','d'],['e','f']])])
 rows=[dict(case=i,optimal=i!='b') for i in 'abcdef']
 x=m.select_bank(data,rows,2);assert x['complete'] and x['selected']==list('cdef')
 assert not m.select_bank(data,rows,3)['complete']
 rows[1]['optimal']=True
 assert m.select_bank(data,rows,2)['selected']==list('abcd')


def test_matched_queries_shared_nonordinary_and_source_reference_only():
 f=m.readz(m.OUT/'preflight.json.gz');d=f['panel'];meta=d['metadata']
 assert len(d['methods']['current'])==len(d['methods']['bank'])==392
 a=set(d['methods']['current']);b=set(d['methods']['bank'])
 assert len(a|b)==440
 assert all(meta[c]['family'] in ('ordinary_perfect','ordinary_random') for c in a^b)
 assert len(f['selection']['selected'])==48
 assert all(len(s['selected_bases'])==4 for s in f['selection']['strata'])
 for task in m.specs(f['draw'],f['models']):assert m.PARENT in task[0]['aliases']
 assert m.panel_metrics(d,m.merge_results(f['panel_results']),f['models'])==f['metrics']


def test_three_bank_criterion_and_nonvacuity():
 f=m.readz(m.OUT/'preflight.json.gz');data=f['panel'];rows=m.merge_results(f['panel_results']);models=f['models']
 freeze=dict(panels=[f['metrics']]*3)
 s=m.summary(data,rows,models,freeze)
 assert len(s['comparisons'])==3 and s==json.loads(json.dumps(s))
 # A matching source and both intact controls must not be mislabeled severe.
 for model in models:
  if m.PARENT in model['aliases'] or any(i.startswith('control/') for i in model['aliases']):assert not s['truth'][model['digest']]['severe_loss']
 bad=deepcopy(freeze)
 for panel in bad['panels']:panel['bank']['gated_ordinary_denominators'][m.GATED[0]]=0
 assert not m.summary(data,rows,models,bad)['ready_for_new_protocol']


def test_complete_durable_pipeline_and_all_native_audits_on_excluded_fixtures(tmp_path,monkeypatch):
 f=m.readz(m.OUT/'preflight.json.gz');out=tmp_path/'results';out.mkdir();run=tmp_path/'run'
 config=f['config'];models=f['models'];draw=f['draw'];panel=f['panel']
 m.writez(out/'pool.json.gz',models);m.writez(out/'exclusions.json.gz',dict(hashes=[]))
 monkeypatch.setattr(m,'ROOT',tmp_path);monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run);monkeypatch.setattr(m,'check',lambda:config)
 monkeypatch.setattr(m,'pushed',lambda _:None);monkeypatch.setattr(m,'ProcessPoolExecutor',lambda *a,**k:nullcontext(None))
 monkeypatch.setattr(m,'build_draws',lambda *a,**k:deepcopy(draw));monkeypatch.setattr(m,'build_panels',lambda *a,**k:deepcopy(panel))
 def saved(j,n,data,*a):
  receipts=f['draw_results'] if n==0 else f['panel_results']
  for k,r in enumerate(receipts):j.reserve(n,k,r['calls'],r['work']);j.receipt(n,k,r,r['work'])
  return None
 monkeypatch.setattr(m.shared,'run_stage',saved)
 m.calibrate();assert m.load_layouts(out/'calibration_exclusions.json')==set(draw['new_layouts'])|set(panel['new_layouts'])
 m.audit('calibration');assert json.loads((out/'calibration_audit.json').read_text())['status']=='PASS'
 final=deepcopy(panel);final['queries']={'all':final['queries']};final['new_layouts']=[]
 monkeypatch.setattr(m,'confirmation',lambda *a:deepcopy(final))
 m.final();m.analyze();m.audit('final')
 result=json.loads((out/'final_audit.json').read_text());assert result['all_native_replays']==len(models)*440
 assert result['conventional_calls']==3*440
 assert json.loads((out/'summary.json').read_text())['calibration_not_evolution']
 before=(out/'calibration_freeze.json.gz').read_bytes()
 import pytest
 with pytest.raises(AssertionError):m.calibrate()
 assert (out/'calibration_freeze.json.gz').read_bytes()==before


def test_primary_false_accept_rule_counts_genotypes_and_requires_two_improved_banks():
 models=[dict(digest=str(k),aliases=[i]) for k,i in enumerate([m.PARENT,'m10/reference/shared_child',m.GATED[0],'control/intact_flat','control/intact_modular'])]
 meta={};rs=[]
 for base in range(24):
  for pose in (0,4):
   cid=f'{base}/{pose}';meta[cid]=dict(family='ordinary_perfect',size=11,base=str(base),pose=pose,path=[1,2],graph='perfect',prefix=-1)
   rs.append(dict(case=cid,optimal=True,valid=True,no_path=False,reachable=True,status='solved',reads=0,dispatches=0,exposure_checks=0))
 rows={x['aliases'][0]:deepcopy(rs) for x in models}
 for k,limit in [('1',12),('2',18)]:
  for r in rows[models[int(k)]['aliases'][0]]:
   if int(r['case'].split('/')[0])>=limit:r.update(optimal=False,valid=False,status='timeout')
 def method(bank):
  return dict(models={x['digest']:dict(aliases=x['aliases'],ordinary_pass=not bank or x['digest'] not in ('1','2')) for x in models},
   parent_ordinary_total=24,gated_ordinary_denominators={i:8 for i in m.GATED},ranking=['0','1','2'])
 freeze=dict(panels=[dict(current=method(False),bank=method(True)) for _ in range(3)])
 s=m.summary(dict(metadata=meta),rows,models,freeze)
 assert s['descriptive_bank_support'] and s['ready_for_new_protocol']
 assert s['severe_loss_genotypes']==2 and all(x['difference']==2 for x in s['comparisons'])
 for p in freeze['panels'][1:]:p['bank']=method(False)
 s=m.summary(dict(metadata=meta),rows,models,freeze)
 assert not s['descriptive_bank_support'] and not s['ready_for_new_protocol']
