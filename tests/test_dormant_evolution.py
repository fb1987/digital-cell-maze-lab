"""M23 neutral birth, mutable activation, fair allocation and durable audit tests."""
import json,random
from pathlib import Path
from copy import deepcopy
from contextlib import nullcontext
import numpy as np
from maze_evolution import dormant_evolution as m
from maze_evolution.dormant_evolution_genome import Genome,extension,tune,vary,wrappers,ARMS
from maze_evolution.dormant_evolution_checkpoint import founders,lineage
from maze_evolution.deep_campaign_store import hashed,packed
from maze_evolution import dormant_evolution_metrics as metrics

def test_neutral_scalar_semantics_and_matched_material():
 from maze_evolution.guarded_extension_observer import frame
 from maze_evolution.datasets import make_case
 sources=m.readz(m.OUT/'sources.json.gz');maze=make_case(1,'old-fixture',0,0,9,'random').maze
 rng=random.Random(23);old=np.array([[rng.randrange(25) for _ in maze.cells] for _ in range(10)],dtype=np.uint16)
 for a in sources['anchors'].values():
  g=Genome.from_dict(a['genome'])
  for block in range(8):
   for reuse in (False,True):
    ra=random.Random(2300+block);rb=random.Random(2300+block)
    x,e=extension(g,ra,True,block,reuse);y,f=extension(g,rb,False,block,reuse)
    assert ra.getstate()==rb.getstate() and x.instructions==y.instructions==g.instructions+3<=128
    assert e['payload']==f['payload'] and wrappers(x)==wrappers(y)
    n=len(g.body.blocks[block]);assert x.body.blocks[block][:n]==g.body.blocks[block]
    for p,c in enumerate(maze.cells):
     if not c:continue
     before=frame(g.body.blocks[block],g.body.ports[block],old,maze,p)
     after=frame(x.body.blocks[block],x.body.ports[block],old,maze,p)
     assert before[11+n]==after[14+n]

def test_operator_replay_activation_access_and_bounds():
 ss=founders(m.CONFIG['seed']);g=Genome.from_dict(ss[0]['population'][0]['genome'])
 x,_=extension(g,random.Random(4),True);assert wrappers(x)
 activation_seen=False;payload_seen=False
 for n in range(100):
  (y,event),used=tune(x,random.Random(n));assert used
  activation_seen|=event['kind']=='activation_expression_edit';payload_seen|=event['kind']=='payload_expression_edit'
  assert Genome.from_dict(y.to_dict())==y
 assert activation_seen and payload_seen
 for arm in ARMS:
  rng=random.Random(24);a=x
  for _ in range(400):
   state=rng.getstate();b,e=vary(a,rng,arm);end=rng.getstate();rng.setstate(state);c,f=vary(a,rng,arm)
   assert b==c and e==f and rng.getstate()==end and b.instructions<=256
   if e['kind']=='disabled_extension':assert b.instructions<=128
   a=b
 # Repeated append is bounded even though ordinary genome cap remains256.
 while True:
  y,e=extension(x,random.Random(8),True,0,True)
  if e['kind']=='bounded_noop':assert y==x;break
  x=y

def test_matched_founders_and_phase_attribution():
 ss=founders(m.CONFIG['seed']);reg=m.readz(m.OUT/'inherited_registry.json.gz')
 assert ss==m.readz(m.OUT/'founders.json.gz') and len(reg)==752
 for n in range(3):
  trio=ss[n*3:n*3+3]
  for s in trio:
   assert len(s['population'])==96 and len(s['protected'])==14 and s['rng']==trio[0]['rng']
   assert [i['genome'] for i in s['population']]==[i['genome'] for i in trio[0]['population']]
   for i in s['population']:assert lineage(i['id'],reg,reg)['phase_mutations']==0
 assert reg['m14/modular/1/explore/g320/b48']['phase']=='M15'

def test_endpoint_gates_and_no_role_substitution():
 from tests.test_exploration_allocation import gate_fixture
 child,root,union,a0,meta=gate_fixture()
 yes,_=metrics.acquisition(child,root,root,union,a0,meta,1);assert yes['upstream_acquisition']
 for entry,mutations in ((child,1),(root,0)):
  no,_=metrics.acquisition(child,root,entry,union,a0,meta,mutations);assert not no['upstream_acquisition']
 cs=[dict(replicate=r,arm=a,rank=k,child=f'{r}/{a}/{k}',retention_and_disconnection_gate=k!=0,beyond_root_and_protected_union=dict(new_upstream_pairs=10 if a=='disabled' else 0)) for r in range(3) for a in ARMS for k in range(3)]
 assert not metrics.policy_comparison(cs)['descriptive_support_both']
 for c in cs:
  if c['arm']=='disabled' and c['rank']==0:c['retention_and_disconnection_gate']=True
 assert metrics.policy_comparison(cs)['descriptive_support_both']

def test_complete_discarded_durable_pipeline(tmp_path,monkeypatch):
 from maze_evolution import dormant_evolution_analysis as a
 steps=m.readz(m.OUT/'rehearsal.json.gz');ss=m.readz(m.OUT/'fixture_founders.json.gz');reg=m.readz(m.OUT/'fixture_registry.json.gz');source=m.readz(m.OUT/'sources.json.gz')
 out=tmp_path/'out';out.mkdir();run=tmp_path/'run'
 m.writez(out/'founders.json.gz',ss);m.writez(out/'inherited_registry.json.gz',reg)
 # Artificial archive identities, no historical intervention queries required.
 for value in source['protected'].values():value['genome']=ss[0]['population'][0]['genome']
 m.writez(out/'sources.json.gz',source)
 def export(name,hashes):
  part=out/(name+'.part.json.gz');m.writez(part,dict(hashes=sorted(hashes)));m.writej(out/(name+'.json'),dict(count=len(hashes),parts=[dict(path=str(part),count=len(hashes),sha256=m.sha(part))]))
 export('exclusions',set());config=dict(m.CONFIG,max_rounds=3,storage_bytes=512*2**20,layout_base_manifest=str(out/'exclusions.json'))
 monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run);monkeypatch.setattr(m,'check',lambda:config);monkeypatch.setattr(m,'pushed',lambda _:None);monkeypatch.setattr(m,'write_layouts',export)
 monkeypatch.setattr(m.data_builder,'validation',lambda *args:deepcopy(steps[0]['data']));monkeypatch.setattr(m.data_builder,'training',lambda seed,g,previous:deepcopy(steps[g+1]['data']))
 monkeypatch.setattr(m,'ProcessPoolExecutor',lambda *args,**kwargs:nullcontext(None))
 def saved(j,n,data,*args):
  for k,spec,status in j.tasks(n):
   receipt=steps[n]['receipts'][k];j.reserve(n,k,receipt['calls'],receipt['work']);j.receipt(n,k,receipt,receipt['work'])
  return None
 monkeypatch.setattr(m.shared,'run_stage',saved)
 m.run();session=json.loads((out/'session.json').read_text());assert session['generation']==3
 frozen=(out/'choices.json.gz').read_bytes();m.run();assert (out/'choices.json.gz').read_bytes()==frozen
 monkeypatch.setattr(a,'OUT',out);monkeypatch.setattr(a,'RUN',run);monkeypatch.setattr(a,'check',lambda:config);monkeypatch.setattr(a,'pushed',lambda _:None);monkeypatch.setattr(a,'founders',lambda seed:ss)
 a.audit_search();search=json.loads((out/'search_audit.json').read_text());assert search['births_replayed']==1404 and len(set(tuple(sorted(v.items())) for v in search['logical_query_counts'].values()))==1
 monkeypatch.undo();monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run)
 monkeypatch.setattr(a,'OUT',out);monkeypatch.setattr(a,'RUN',run);monkeypatch.setattr(a,'check',lambda:config);monkeypatch.setattr(a,'pushed',lambda _:None)
 monkeypatch.setattr(a,'confirmation',lambda *args:deepcopy(m.readz(m.ROOT/'results/connected_evolution/final_fixture.json.gz')))
 a.final();a.analyze();a.audit_final()
 summary=json.loads((out/'summary.json').read_text());final=json.loads((out/'final_audit.json').read_text())
 assert summary['phase']=='M23' and len(summary['conditions'])==27 and final['native_replays']==summary['usage']['calls']
 m.writej(m.ROOT/'results/dormant_evolution/discarded_pipeline.json',dict(search_session=session,search_audit=search,final_session=json.loads((out/'final_session.json').read_text()),final_audit=final,not_scientific=True,new_layouts=0))
