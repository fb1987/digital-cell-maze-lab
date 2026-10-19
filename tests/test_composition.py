import json,random
from copy import deepcopy
from pathlib import Path
import pytest
from maze_evolution.composition_operator import interface,rows,sites,splice,replay_splice
from maze_evolution.growth import Genome as Program
from maze_evolution.regulatory import Gene
from maze_evolution.composition_data import OUT,FIXTURES,load,training_batch,clear_batch,AccessData,SEED
from maze_evolution.composition_search import donor_choice,reproduce,ranked,summary,gate
from maze_evolution.composition_study import make_pools,init_state
from maze_evolution.foundation_study import read_compressed
from maze_evolution.composition_audit import geometry,sample
from maze_evolution.exposure_genome import Individual,Genome
from maze_evolution.regulatory_search import Evaluation

def programs():
    a=Program((Gene(1,12,1),Gene(0,13,12),Gene(2,14,12,13),Gene(0,15,14),Gene(13,2,15)))
    b=Program((Gene(1,12,1),Gene(0,13,12),Gene(3,14,12,13),Gene(0,15,14),Gene(13,2,15)))
    return a,b

def test_splice_replays_two_parent_segment_exactly():
    a,b=programs();assert sites(rows(a),rows(b))==((2,3,2,3),)
    c,e=splice(a,b,random.Random(1));assert c==b and c!=a and replay_splice(a,b,e)==c
    bad=deepcopy(e);bad['donor_rows'][0][0]=2
    with pytest.raises(AssertionError):replay_splice(a,b,bad)

def test_live_in_accounts_for_gates_and_conditional_definitions():
    i=interface([(1,12,1,0,0,0,20),(0,13,12,0,0,0,64)])
    assert i['live_in']==[12,20]
    assert interface([(1,12,1,0,0,0,64),(0,13,12,0,0,0,64)])['live_in']==[]

def test_incompatible_register_or_store_contract_rejected():
    a,b=programs();g=list(b.genes);g[2]=Gene(3,16,12,13);assert not sites(rows(a),rows(Program(tuple(g))))
    g[2]=Gene(3,14,31,13);assert not sites(rows(a),rows(Program(tuple(g))))
    assert splice(a,a,random.Random(1))==(None,None)

def test_bounded_splice_never_truncates():
    a,b=programs();a=Program(a.genes+(Gene(1,20,0),)*251)
    extra=b.genes[:3]+(Gene(1,14,1),)+b.genes[3:]+(Gene(1,20,0),)*250
    b=Program(extra);assert len(a.genes)==len(b.genes)==256
    for x,y,u,v in sites(rows(a),rows(b)):assert 1<=len(a.genes)-(y-x)+(v-u)<=256

def test_preserved_panel_diversity_and_new_fresh_origins():
    p=make_pools();panel=read_compressed('results/research_reset/panel.json.gz')
    ids={v['item']['id'] for v in panel.values()};assert len(ids)==16
    for key,v in p.items():
        assert len(v['items'])==96 and len({r['id'] for r in v['items']})==96
        assert all('intact' not in r['id'] for r in v['items'])
        if key.startswith('carry'):assert {r['id'] for r in v['protected']}==ids
        else:assert not v['protected'] and all(r['parent'] is None and r['id'].startswith('composition/fresh') for r in v['items'])

def test_fixtures_cover_positive_prefix_stress_and_ordinary():
    c,_,m=load(FIXTURES);g=geometry(c,m)
    assert len(c)==3968 and g['ordinary_inputs']==512 and g['pairs']==576
    assert {x['prefix'] for x in m.values() if x['family']=='paired'}=={0,1,2,4}
    assert {x['pose'] for x in m.values()}==set(range(8))

def test_common_training_schedule_queries_both_goals():
    # Constructed fixtures are persisted separately and excluded before search.
    c,_,m=load(OUT/'schedule_fixtures')
    for g in range(96):
        ids=[cid for cid,q in m.items() if q['audit_generation']==g]
        assert len(ids)==12
        for base in {m[cid]['base'] for cid in ids}:
            rr=[m[cid] for cid in ids if m[cid]['base']==base and m[cid]['family']=='paired']
            assert {x['side'] for x in rr}=={0,1}
    assert {x['pose'] for x in m.values()}==set(range(8))

def test_readiness_requires_both_new_correctness_and_retention():
    b=dict(positive_keys=[],positive=0,positive_full_groups=0,stress_positive=0,positive_contexts=[],zero=16,corridors=100,false_no_path=0)
    t=dict(b,positive_keys=[[str(i),0] for i in range(16)],positive=16,positive_full_groups=2,stress_positive=8,positive_contexts=['a','b','c','d'])
    assert gate(t,b,b,b)
    assert not gate(dict(t,corridors=94),b,b,b)
    assert not gate(dict(t,stress_positive=0),b,b,b)

def test_audit_sample_deterministic_and_not_outcome_dependent():
    a=[sample('x',0,'p',str(i)) for i in range(10000)];assert a==[sample('x',0,'p',str(i)) for i in range(10000)]
    assert 10<sum(a)<80

def test_complementary_mating_and_two_parent_births_are_reproducible():
    a,b=programs();rank=[]
    for k in range(96):
        i=Individual(str(k),Genome(a if k%2==0 else b,7),None,0)
        values=[(1,1,1,.9),(0,0,0,0.)] if k%2==0 else [(0,0,0,0.),(1,1,1,.9)]
        ev=Evaluation((1,1),values,(),[dict(mask=str(k%2),status='emitted')],0)
        rank.append((ev,i))
    donor,event=donor_choice(random.Random(3),rank,rank[0][1])
    assert donor is not None and event['gains'][0]>0
    aa={name:dict(item=rank[0][1].save()) for name in ('primary','choice','corridor')}
    state=dict(key='synthetic/recombination',arm='recombination',protected=[],rng=random.Random(11).getstate(),serial=0,generation=0,archives=aa)
    new,event=reproduce(state,rank,aa);assert (new,event)==reproduce(state,rank,aa)
    sexual=[b for b in event['births'] if b['crossover'] is not None]
    assert sexual and all(len(b['parents'])==2 and b['parents'][0]==b['item']['parent'] for b in sexual)
    assert all(b['mutation'] is not None for b in sexual)
