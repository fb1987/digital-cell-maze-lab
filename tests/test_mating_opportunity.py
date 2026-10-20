import random
from pathlib import Path
import json
from maze_evolution.mating_opportunity_operator import gate_groups, options, virtual, RULES
from maze_evolution.mating_opportunity_independent import gate_groups as independent_gate, options as independent_options
from maze_evolution.linkage_restart_operator import candidates as old_candidates, mutate_ids
from maze_evolution.growth import random_genome, mutate
from maze_evolution.composition_operator import rows
from maze_evolution.mating_opportunity_study import node, family_row, possible, build_stats, decision


def test_gate_retains_conditional_and_previous_unconditional_writer():
    p=((1,18,2,0,0,0,64),(0,18,25,0,0,0,12),(13,2,58,0,0,0,18))
    assert gate_groups(p)==independent_gate(p)==((0,1,2),)
    q=(p[0],(*p[1][:6],64),p[2])
    assert gate_groups(q)==((1,2),)


def test_gate_does_not_recursively_include_value_or_writer_operands():
    p=((1,25,2,0,0,0,64),(0,18,25,0,0,0,64),(1,58,2,0,0,0,64),(13,2,58,0,0,0,18))
    assert gate_groups(p)==independent_gate(p)==((1,3),)


def test_gate_unconditional_store_and_initial_gate_value():
    p=((13,2,18,0,0,0,64),(13,2,18,0,0,0,12))
    assert gate_groups(p)==((0,),(1,))


def test_independent_pool_and_old_cap_parity_random_programs():
    rng=random.Random(7723)
    for n in range(60):
        p=random_genome(rng,True)
        ids=[f'family{n}/g{i}' for i in range(len(p.genes))]
        if n<30:
            a=rows(p);b=list(a)
            for _ in range(8):
                i=rng.randrange(len(b));r=list(b[i]);r[2]=rng.randrange(8) if r[0] in (4,5,6,7,14,15,17) else rng.randrange(64);b[i]=tuple(r)
            b=tuple(b);ai=bi=tuple(ids)
        else:
            mom,events=mutate(p,rng,3,256,True);ai=tuple(mutate_ids(ids,events,f'mom{n}'))
            dad,events=mutate(p,rng,4,256,True);bi=tuple(mutate_ids(ids,events,f'dad{n}'))
            a,b=rows(mom),rows(dad)
        got=options(a,b,ai,bi)
        assert got==independent_options(a,b,ai,bi)
        if a!=b:
            assert tuple(v[:6] for v in got[0] if v[1]-v[0]<=16)==old_candidates(a,b,ai,bi)
        assert all(not v[5] or v[6] for v in got[0])


def test_parent_union_prevents_store_replacement_from_evading_gate():
    a=((1,24,0,0,0,0,64),(1,18,0,0,0,0,64),(13,2,58,0,0,0,18),(0,30,0,0,0,0,64),(1,21,3,0,0,0,64))
    b=list(a);b[1]=(1,51,0,0,0,0,64);b[2]=(8,34,40,39,0,0,64);b=tuple(b)
    ids=tuple(str(i) for i in range(len(a)))
    pool,_=options(a,b,ids,ids)
    assert any(v[:4]==(1,3,1,3) and v[6] for v in pool)
    assert any(v[:4]==(2,4,2,4) and not v[6] for v in pool)


def test_unrelated_and_inverted_and_identical_are_not_eligible():
    a=tuple((1,20,i,0,0,0,64) for i in range(8));b=list(a);b[2]=(1,20,3,0,0,0,64);b=tuple(b)
    ids=tuple(map(str,range(8)))
    assert options(a,b,ids,tuple('new'+i for i in ids))[1]=='no_shared_anchors'
    assert options(a,b,ids,ids[::-1])[1]=='inverted_shared_order'
    assert options(a,a,ids,ids)[1]=='identical_program'


def test_32_common_cap_adds_long_intervals_without_changing_small_ones():
    a=tuple((1,20,i%8,0,0,0,64) for i in range(40));b=list(a)
    b[5]=(1,21,1,0,0,0,64);b[25]=(1,21,1,0,0,0,64);b=tuple(b)
    ids=tuple(map(str,range(40)));pool,_=options(a,b,ids,ids)
    assert any(v[1]-v[0]==32 and v[4]==2 for v in pool)
    assert tuple(v[:6] for v in pool if v[1]-v[0]<=16)==old_candidates(a,b,ids,ids)


def test_virtual_exact_expectations_and_same_ticket_feasibility():
    pool=((1,3,1,3,1,True,True),(2,4,2,4,2,False,True))
    for s in range(10):
        r=virtual(pool,16,s)
        assert r['transitive']['expected_multi']==0
        assert all(r[k]['expected_multi']==.5 for k in ('unlinked','gate','sham_gate','sham_transitive'))
        assert len({r[k]['length'] for k in RULES})==1
        assert r['transitive']['accepted']==r['sham_transitive']['accepted']
        assert r['gate']['accepted']==r['sham_gate']['accepted']
        assert virtual(pool,16,s)==r


def test_empty_proposals_remain_in_denominator():
    for r in virtual((),32,1).values():
        assert not r['multi'] and r['expected_multi']==0 and not r['accepted']


def test_sham_multi_opportunity_requires_admissible_count_at_same_length():
    pool=((1,3,1,3,1,True,True),(1,5,1,5,2,False,False))
    stats=build_stats(pool)
    assert possible(stats,16,'unlinked')
    assert not possible(stats,16,'sham_gate')
    assert not possible(stats,16,'gate')


def test_family_fractional_membership_does_not_double_count():
    raw=lambda identity:dict(id=identity,genome=dict(genes=[[1,20,0,0,0,0,64]],exposure=7))
    p={'a':node(raw('a'),['g'],['r1']),'b':node(raw('b'),['g'],['r1','r2'])}
    f=family_row('test',0,p,{'a':raw('a')})
    assert sum(f['root_membership_weights'].values())==2
    assert sum(f['mutable_root_weights'].values())==1 and f['mutable_roots']==2
    assert f['effective_mutable_roots']==2


def test_static_screen_cannot_authorize_long_run():
    data={f'historical/{o}/{r}/{arm}/union/{cap}/{rule}':dict(expected_fraction=.5)
          for o in ('carry','fresh') for r in range(3) for arm in ('linked','unlinked','sham')
          for cap in (16,32) for rule in ('gate','sham_gate','unlinked')}
    d=decision(data)
    assert d['selected_cap']==16 and not d['long_efficacy_run_authorized']
    for e in data.values():e['expected_fraction']=.119
    assert decision(data)['next_step']=='design_related_lineage_diversity'
