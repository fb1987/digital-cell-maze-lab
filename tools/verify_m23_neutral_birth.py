"""Pre-registration embedding/cost gate, old excluded inputs, not new skill evidence."""
import sys,time,multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
import random,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import dormant_evolution as m
from maze_evolution.dormant_evolution_genome import extension,Genome
from maze_evolution.deep_campaign_store import hashed,packed
from maze_evolution.connected_trace import respond
from maze_evolution.deep_campaign_data import cases_from_manifest

def main():
 assert not (m.OUT/'registration.json').exists() and not (m.OUT/'neutral_birth.json').exists()
 t=time.monotonic();sources=m.readz(m.OUT/'sources.json.gz');items=[];comparisons=[]
 for anchor in ('parent','child','threshold'):
  g=Genome.from_dict(sources['anchors'][anchor]['genome']);items.append(dict(id=anchor,model=dict(representation='connected',genome=g.to_dict())))
  for block in range(8):
   for reuse in (False,True):
    child,event=extension(g,random.Random(m.CONFIG['fixture_seed']+block*7+int(reuse)),True,block,reuse)
    assert event['kind']=='disabled_extension' and child.instructions==g.instructions+3<=128
    identity=f'{anchor}/disabled/{block}/{int(reuse)}';items.append(dict(id=identity,model=dict(representation='connected',genome=child.to_dict())))
    comparisons.append(dict(source=anchor,child=identity,event=event))
 panel=m.readz(m.ROOT/'results/connected_evolution/final_fixture.json.gz');ids=panel['queries']['all'];models={}
 for item in items:
  key=hashed(packed(item['model']));models.setdefault(key,dict(model=item['model'],queries=ids,aliases=[]))['aliases'].append(item['id'])
 specs=[[v] for _,v in sorted(models.items())];h=hashed(packed(panel['mazes']))
 with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=m.shared.worker_init) as pool:
  receipts=list(pool.map(m.evaluate_task,specs,[panel['mazes']]*len(specs),[h]*len(specs)))
 m.writez(m.OUT/'neutral_birth_raw.json.gz',dict(items=items,comparisons=comparisons,receipts=receipts,cases_source='results/connected_evolution/final_fixture.json.gz'))
 rows={a:e['rows'] for r in receipts for e in r['entries'] for a in e['aliases']};costs={}
 for c in comparisons:
  old,new=rows[c['source']],rows[c['child']]
  assert all(all(x[k]==y[k] for k in ('case','mask','status','steps','reads')) for x,y in zip(old,new)),c
  costs[c['child']]=dict(old_work=sum(x['reads']+x['dispatches'] for x in old),new_work=sum(x['reads']+x['dispatches'] for x in new),memory_delta_range=[min(y['array_bytes']-x['array_bytes'] for x,y in zip(old,new)),max(y['array_bytes']-x['array_bytes'] for x,y in zip(old,new))])
 # Passive all-state histories on six cases chosen by metadata order, never outcome.
 cases=cases_from_manifest([z for z in panel['mazes'] if z['case_id'] in set(ids)]);chosen=sorted(cases)[:6];traces=0
 lookup={x['id']:x['model'] for x in items}
 for c in comparisons:
  for cid in chosen:
   maze=cases[cid].maze;r,a,_=respond(lookup[c['source']],maze);s,b,_=respond(lookup[c['child']],maze)
   assert np.array_equal(a,b) and r.status==s.status and r.steps==s.steps;traces+=2
 m.writez(m.OUT/'neutral_birth_receipts.json.gz',dict(items=items,comparisons=comparisons,receipts=receipts,cases_source='results/connected_evolution/final_fixture.json.gz'))
 m.writej(m.OUT/'neutral_birth.json',dict(status='PASS',scope='Existing three focal entries, every active original writer, random and reused payload; old excluded 1680-input panel. Not confirmation or a speed benchmark.',comparisons=len(comparisons),input_comparisons=len(comparisons)*len(ids),all_masks_status_steps_reads_equal=True,passive_full_state_history_checks=traces//2,passive_executions=traces,embedding_costs=costs,calls=sum(r['calls'] for r in receipts),candidate_seconds=sum(r['candidate_seconds'] for r in receipts),wall_seconds=time.monotonic()-t,unchanged_runtime=True,admission_proof='Extension admitted only at <=128 total instructions, so <=256*128=32768 dispatches per open site across complete ticks. Disabled activation and payload add zero reads and leave all channel writes unchanged; read interruption discards same incomplete tick. Repeated additions may be bounded no-ops; ordinary edits can exceed128 up to original256 and are not neutral guarantees.',new_layouts=0))
 print('M23 neutral insertion PASS',len(comparisons)*len(ids),'old-input comparisons',flush=True)
if __name__=='__main__':main()
