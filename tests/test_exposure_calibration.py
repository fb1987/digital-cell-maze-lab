from dataclasses import replace
import random
import numpy as np
import pytest
from maze_evolution.exposure_genome import Genome,Individual,mutate,replay
from maze_evolution.growth import Genome as Program,random_genome
from maze_evolution.regulatory import Gene
from maze_evolution.exposure_runtime import Organism
from maze_evolution.growth_runtime import Organism as Old
from maze_evolution.foundation_calibration import LIMITS
from maze_evolution.exposure_data import *
from maze_evolution.exposure_audit import geometry,independent_rank
from maze_evolution.exposure_selection import record,evaluate,physical

@pytest.fixture(scope='module')
def fixtures():return {o:load(FIXTURES/o) for o in ('carry','fresh')}

def test_geometry(fixtures):
    assert geometry(*fixtures['carry'],'carry')['independent_templates']==9
    assert geometry(*fixtures['fresh'],'fresh')['independent_templates']==6

def test_serialization_digest_bounds():
    p=random_genome(random.Random(128),True)
    assert len({Genome(p,k).digest for k in range(8)})==8
    for k in range(8):
        g=Genome(p,k);assert Genome.from_dict(g.to_dict())==g
        i=Individual('test',g,None,0);assert Individual.load(i.save())==i
    for k in (-1,8,True,1.5):
        with pytest.raises(ValueError):Genome(p,k)

def test_coupled_mutation_replay():
    g=Genome(random_genome(random.Random(2),True),7);a=random.Random(123);b=random.Random(123);kinds=set()
    for _ in range(200):
        x,e=mutate(g,a);y,f=mutate(g,b);assert x==y==replay(g,e) and e==f and a.getstate()==b.getstate();kinds.add(e['kind']);g=x
    assert kinds=={'exposure','program'}

def test_exact_endpoints_and_caps(fixtures):
    panel=read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')
    from maze_evolution.growth import Individual as OldItem
    cases=fixtures['carry'][0];o=next(iter(cases.values()));m=o.maze
    for name in ('branch_broad','k2_target','local_long','intact'):
        p=OldItem.load(panel[name]['item']).genome;top=panel[name]['topology']
        for limits in (LIMITS,replace(LIMITS,max_steps=1),replace(LIMITS,reads_per_site=1),replace(LIMITS,instructions_per_site=1)):
            for mask in (0,7):
                a=Organism(Genome(p,mask),'active',top,limits).react(m.cells,m.w,m.h,m.start,m.goal)
                b=Old(p,top,limits,ablate_nonlocal=mask==0,goal_pulse=True).react(m.cells,m.w,m.h,m.start,m.goal)
                assert np.array_equal(a.mask,b.mask)
                for field in ('status','steps','spatial_reads','dispatches','active_instructions','range_reads'):assert getattr(a,field)==getattr(b,field)
                assert a.array_bytes==b.array_bytes+17

def test_each_bit_and_remote_opcode_independently(fixtures):
    o=next(iter(fixtures['carry'][0].values()));m=o.maze;n=len(m.cells);w=m.w
    for op in (14,15):
        for radius_id in range(4):
            p=Program((Gene(op,12,1,0,0,radius_id),Gene(13,2,12)))
            for bits in range(8):
                r=Organism(Genome(p,bits),'active','evolved',replace(LIMITS,max_steps=1)).react(m.cells,m.w,m.h,m.start,m.goal)
                expected=np.zeros(n,np.uint8);radius=1<<radius_id;enabled=radius_id==0 or bits&(1<<(radius_id-1))
                if enabled:
                    for q in range(n):
                        if not m.cells[q]:continue
                        directions=[(-radius,0)] if op==14 else [(-radius,0),(radius,0),(0,-radius),(0,radius)]
                        expected[q]=any((q%w+dx,q//w+dy)==(m.goal%w,m.goal//w) for dx,dy in directions)
                assert np.array_equal(r.mask,expected)
                cost=1 if op==14 else 4
                assert r.spatial_reads==sum(m.cells)*cost and r.exposure_checks==sum(m.cells)
                assert r.suppressed_reads==(0 if enabled else sum(m.cells)*cost)

def test_neutral_and_fixed_controls_share_storage_cost(fixtures):
    p=random_genome(random.Random(6),True);o=next(iter(fixtures['fresh'][0].values()));m=o.maze
    for arm in ('neutral','zero','local'):
        a=Organism(Genome(p,0),arm,'evolved',LIMITS).react(m.cells,m.w,m.h,m.start,m.goal)
        b=Organism(Genome(p,7),arm,'evolved',LIMITS).react(m.cells,m.w,m.h,m.start,m.goal)
        assert np.array_equal(a.mask,b.mask)
        for k in ('steps','spatial_reads','dispatches','exposure_checks','suppressed_reads','array_bytes'):assert getattr(a,k)==getattr(b,k)

def test_no_known_founders_and_common_arm_pool():
    pools=read_compressed(OUT/'pools.json.gz');aliases=read_compressed(OUT/'aliases.json.gz')
    assert len(pools)==19 and sum(p['origin']=='fresh' for p in pools.values())==3
    for key,p in pools.items():
        assert all('positive_control' not in i['id'] for i in p['items'])
        assert all(set(aliases[key][arm])=={i['id'] for i in p['items']} for arm in aliases[key])

def test_pair_rank_and_no_corridor_pair_credit(fixtures):
    _,_,meta=fixtures['fresh'];rows=[]
    for cid,m in meta.items():rows.append(dict(case=cid,optimal=m['family']!='disconnected',valid=m['family']!='disconnected',no_path=m['family']=='disconnected',reachable=m['family']!='disconnected',status='emitted',partial=.4,reads=2,dispatches=2,exposure_checks=1))
    ev=evaluate(rows,meta);assert list(ev.fitness)==independent_rank(rows,meta)
    assert ev.fitness[0]==48
    assert evaluate([r for r in rows if meta[r['case']]['family'].startswith('corridor')],meta).fitness[0]==0

def test_budget_closes_without_call():
    from maze_evolution.exposure_study import Budget
    with pytest.raises(TimeoutError):Budget(10,0).call(lambda:None)

def test_revised_calibration_query_counts(fixtures):
    from types import SimpleNamespace
    from maze_evolution.exposure_study import ids_for,revised_profile
    import json
    data={o:SimpleNamespace(metadata=value[2]) for o,value in fixtures.items()}
    assert len(ids_for(data['carry'],'carry',selection=True))==180
    assert len(ids_for(data['carry'],'carry'))==360
    assert len(ids_for(data['fresh'],'fresh',selection=True))==144
    assert len(ids_for(data['fresh'],'fresh'))==144
    old=json.loads((FIXTURES/'calibration.json').read_text());new=revised_profile(old)
    assert not old['passed'] and new['passed'] and new['new_candidate_calls']==0
    assert new==json.loads((FIXTURES/'calibration_revised.json').read_text())
