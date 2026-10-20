import json,copy,random
import numpy as np
import pytest
from maze_evolution.selectivity_study import *
from maze_evolution.selectivity_calibration import synthetic
from maze_evolution.selectivity_audit import geometry,independent_selectivity
from maze_evolution.foundation_study_verify_core import Checker

@pytest.fixture(scope='module')
def data():return load(FIXTURES)

@pytest.fixture(scope='module')
def pools():return read_compressed(OUT/'pools.json.gz')

def test_objective_distinguishes_excess_without_counting_solutions(data):
    c,_,m=data;v=synthetic(c,m);checker=Checker(c)
    assert v['rows']['one_extra']['partial']==v['rows']['four_extra']['partial']
    for r in v['rows'].values():
        mask=checker.row(r);assert independent_selectivity(r,c[r['case']],mask)==r['selectivity']
    assert sum(r['optimal'] for r in v['rows'].values())==1

def test_equal_hard_correctness_fields_and_single_shaping_change(data,pools):
    c,_,m=data;v=synthetic(c,m);raw=pools['fresh/0']['items'][0];first=Individual.load(raw)
    second=Individual(first.identity+'/other',first.genome,None,0)
    # Duplicate each synthetic mask on a distinct corridor label: no artificial paired-case grouping.
    cid=v['case'];meta={cid:dict(m[cid],family='corridor')};rr={first.identity:[v['rows']['one_extra']],second.identity:[v['rows']['four_extra']]}
    cur=ranked([first,second],rr,meta,'current');sel=ranked([first,second],rr,meta,'selective')
    assert cur[0][0].fitness==cur[1][0].fitness
    assert sel[0][1].identity==first.identity and sel[0][0].fitness>sel[1][0].fitness
    for ev,i in sel:
        original=next(e for e,x in cur if x.identity==i.identity)
        assert ev.fitness[:-1]==original.fitness[:-1]
        assert ev.case_values[0][:3]==original.case_values[0][:3]
        assert ev.rows==rr[i.identity]

def test_validation_coverage_and_all_layout_exclusion(data):
    c,_,m=data;ids=validation_ids(m);assert len(ids)==340
    assert {m[i]['pose'] for i in ids if m[i]['family']=='paired'}=={0,2,4,6}
    assert len({m[i]['template'] for i in ids})==6
    assert not exclusions()&{layout_hash(o.maze) for o in c.values()}
    assert geometry(c,m)['pairs']==240

def test_curriculum_complete_pose_prefix_cycle():
    c,_,m=load(OUT/'schedule_fixtures');ids=[i for i,q in m.items() if q['audit_generation']>=0]
    assert len(ids)==16*12
    assert {(m[i]['pose'],m[i]['prefix']) for i in ids if m[i]['family']=='paired' and m[i]['prefix']>0}=={(p,k) for p in range(8) for k in (1,2)}

def test_carried_populations_and_rng_exact_fork(pools):
    old=read_compressed(ROOT/'results/family_evolution/next_states.json.gz')
    for r in range(3):
        p=pools[f'carry/{r}'];o=old[f'carry/{r}/current_mutation']
        assert p['items']==o['population'] and p['search_rng']==o['rng'] and p['gene_ids']==o['gene_ids'] and p['protected']==o['protected']
    assert all(pools[f'fresh/{r}']['protected']==[] for r in range(3))

def test_common_fresh_protection_uses_only_own_founders(pools):
    p=pools['fresh/0'];aa={name:dict(item=p['items'][k]) for k,name in enumerate(ARCHIVES)}
    states=[init_state('fresh/0/'+a,p,aa) for a in ARMS]
    assert all(s['protected']==p['items'][:3] for s in states)
    assert all(s['population']==p['items'] and s['rng']==p['search_rng'] for s in states)

def test_reproduction_namespace_and_exact_events(pools,data):
    p=pools['fresh/0'];c,_,m=data;v=synthetic(c,m);cid=v['case'];meta={cid:dict(m[cid],family='corridor')}
    pop=[Individual.load(r) for r in p['items']];rr={i.identity:[v['rows']['empty']] for i in pop}
    for arm in ('current','selective','resample'):
        s=init_state('fresh/0/'+arm,p);rank=ranked(pop,rr,meta,arm);n,e=reproduce(s,rank,{})
        assert reproduce(s,rank,{})==(n,e)
        assert len(e['births'])==52 and len(e['elite'])==44
        assert all(b['item']['id'].startswith('selectivity_v13b/fresh/0/'+arm+'/') for b in e['births'])
        assert sum(b['mutation'] is not None for b in e['births'])==(0 if arm=='resample' else 45)

def test_separate_positive_control_refinement():
    p=read_compressed(FIXTURES/'positive_controls.json.gz');assert p['inputs']==40
    assert p['optimal']['intact']==40 and p['optimal']['output_register']<40
    for identity in p['best'].values():
        name=next(k for k,v in p['items'].items() if v['id']==identity);assert p['optimal'][name]==40


def test_gate_checks_case_retention_not_just_counts(data):
    _,_,meta=data
    pairs=list(dict.fromkeys((m['base'],m['pose']) for m in meta.values() if m['family']=='paired' and m['prefix'] in (1,2)))
    target=dict(upstream_keys=pairs[:16],p2_keys=pairs[8:16],all_keys=pairs[:16],corridor_keys=['x'],upstream=16,false_no_path=0)
    frozen=dict(upstream_keys=[],p2_keys=[],all_keys=[('old',0)],corridor_keys=['y'],upstream=0,false_no_path=0)
    g=gate(target,[frozen],frozen,meta);assert not g['passed'] and not g['checks']['retention']
