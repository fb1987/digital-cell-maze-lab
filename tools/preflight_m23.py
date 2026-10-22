"""M23 discarded selected-evolution rehearsal on ONLY already excluded layouts."""
import sys,time,random,multiprocessing
from copy import deepcopy
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import dormant_evolution as m
from maze_evolution.regulatory import Gene
from maze_evolution.modular_genome import Genome as Base
from maze_evolution.connected_genome import embed
from maze_evolution.dormant_evolution_checkpoint import founders
from maze_evolution.routing_transfer import canonical
from maze_evolution.deep_campaign_store import hashed,packed

def main():
 assert not (m.OUT/'registration.json').exists() and not (m.OUT/'profile.json').exists()
 ss=founders(m.CONFIG['fixture_seed'],namespace='m23-fixture');registry={}
 for s in ss:
  for i in s['population']:
   # All discarded anchors are simple constant zero writers. Same provenance
   # names exercise reference lookup; these are explicitly artificial genomes.
   g=embed(Base(tuple((Gene(1,12,0,0,0,0,64),) for _ in range(8)),(tuple(range(8)),)*8))
   i['genome']=g.to_dict();i['mutation_depth']=0
   if i['id'] in {x['id'] for x in s['protected']}:i.update(parent=None,root=i['id'])
  s['protected']=deepcopy(s['population'][:14])
  for i in s['population']:registry[i['id']]=dict(item=deepcopy(i),events=[],phase='M23_fixture_initial')
 m.writez(m.OUT/'fixture_founders.json.gz',ss);m.writez(m.OUT/'fixture_registry.json.gz',registry)
 old=m.readz(m.ROOT/'results/connected_evolution/rehearsal.json.gz');steps=[];started=time.monotonic()
 with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=m.shared.worker_init) as pool:
  for k,oldstep in enumerate(old):
   data=deepcopy(oldstep['data']);data['new_layouts']=[]
   data['queries']={f'{rep}/{a}':data['queries'][f'{rep}/{b}'] for rep in range(3) for a,b in zip(('ordinary','enabled','disabled'),('generic','disconnected','connected'))}
   if data['kind']=='train':data['persistent_queries']={f'{rep}/{a}':data['persistent_queries'][f'{rep}/{b}'] for rep in range(3) for a,b in zip(('ordinary','enabled','disabled'),('generic','disconnected','connected'))}
   specs=m.task_specs(ss,data);h=hashed(packed(data['mazes']));receipts=list(pool.map(m.evaluate_task,specs,[data['mazes']]*len(specs),[h]*len(specs)))
   nxt,events=m.transition(ss,data,receipts)
   assert m.transition(m.unpacked(packed(ss)),data,receipts)==(nxt,events)
   steps.append(dict(data=data,receipts=receipts,decisions=events,state_hash=hashed(packed(nxt))))
   ss=nxt;print('M23 discarded stage',k,data['kind'],sum(r['calls'] for r in receipts),flush=True)
 m.writez(m.OUT/'rehearsal.json.gz',steps)
 m.writej(m.OUT/'profile.json',dict(scientific_calls=0,new_layouts=0,artificial_founders=True,calls=sum(r['calls'] for st in steps for r in st['receipts']),candidate_seconds=sum(r['candidate_seconds'] for st in steps for r in st['receipts']),wall_seconds=time.monotonic()-started,births=1404,all_transition_rng_replay=True))
if __name__=='__main__':main()
