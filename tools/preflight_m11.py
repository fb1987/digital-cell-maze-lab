"""Discarded M11 wiring rehearsal. Parent alias intentionally uses intact CONTROL,
only in this fixture, to exercise bank completion independent of research success.
Scientific frozen pool remains unchanged. All generated layouts are excluded.
"""
import sys,time,multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import retention_bank as m

def main():
 assert not (m.OUT/'preflight.json.gz').exists()
 c=dict(m.CONFIG,seed=202610210127,validation_seed=202610210128,draws_per_stratum=64,replicates=1)
 previous=set(m.readz(m.OUT/'exclusions.json.gz')['hashes']);models=deepcopy(m.readz(m.OUT/'pool.json.gz'))
 intact=next(x for x in models if 'control/intact_modular' in x['aliases'])
 ref=next(x for x in models if m.PARENT in x['aliases']);ref['model']=deepcopy(intact['model']);ref['digest']=m.hashed(m.packed(ref['model']))
 # Merge the control's alias list into the fixture reference model, retaining one physical model.
 ref['aliases']+=intact['aliases'];models.remove(intact)
 def evaluate(data,ex):
  specs=m.specs(data,models);ids=set(data['queries']);mazes=[z for z in data['mazes'] if z['case_id'] in ids];h=m.hashed(m.packed(mazes))
  return list(ex.map(m.evaluate_task,specs,[mazes]*len(specs),[h]*len(specs)))
 start=time.monotonic()
 with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=m.shared.worker_init) as ex:
  draw=m.build_draws(0,previous,c);previous.update(draw['new_layouts']);dr=evaluate(draw,ex)
  selection=m.select_bank(draw,m.merge_results(dr)[m.PARENT],c['quota']);assert selection['complete']
  panel=m.build_panels(0,previous,draw,selection,c);previous.update(panel['new_layouts']);pr=evaluate(panel,ex)
  metrics=m.panel_metrics(panel,m.merge_results(pr),models)
  for receipt in pr:
   for e in receipt['entries']:
    if any(i.startswith('control/') for i in e['aliases']):assert all(r['optimal'] or r['no_path'] for r in e['rows'])
 m.writez(m.OUT/'preflight.json.gz',dict(config=c,models=models,draw=draw,draw_results=dr,selection=selection,panel=panel,panel_results=pr,metrics=metrics,
  warning='Fixture-only intact-control substitution at PARENT alias; never a scientific founder or new organism',scientific_calls=0))
 m.writez(m.OUT/'exclusions.json.gz',dict(count=len(previous),hashes=sorted(previous)))
 m.writej(m.OUT/'preflight_profile.json',dict(wall_seconds=time.monotonic()-start,calls=sum(r['calls'] for r in dr+pr),candidate_seconds=sum(r['candidate_seconds'] for r in dr+pr),
  fixture_layouts=len(draw['new_layouts'])+len(panel['new_layouts']),controls_correct=True,scientific_calls=0))
 print(m.readz(m.OUT/'preflight.json.gz')['warning'],flush=True)
if __name__=='__main__':main()
