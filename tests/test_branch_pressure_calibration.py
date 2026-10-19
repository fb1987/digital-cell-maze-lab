"""V12N tests reuse saved fixtures; synthetic masks never enter candidate pools."""
import random
import numpy as np
import pytest
from maze_evolution.branch_pressure_data import FIXTURES,load,query
from maze_evolution.branch_pressure_study import loaded,make_pools
from maze_evolution.branch_pressure_fitness import pair_score,choose
from maze_evolution.branch_pressure_audit import geometry,independent_proxy
from maze_evolution.exposure_selection import choose as old_choose


def fixture_pair(kind='three_edge'):
    cases,contexts,meta=load(FIXTURES)
    c=next(c for c in contexts if c['kind']==kind and c['goal_shape']=='straight');ids=c['poses'][0]['cases']['paired']
    return cases,meta,ids


def row(cid,points,status='emitted',optimal=False):
    mask=np.zeros(81,np.uint8);mask[list(points)]=1
    return dict(case=cid,mask=np.packbits(mask,bitorder='little').tobytes().hex(),status=status,optimal=optimal,valid=optimal,no_path=False,reachable=True,partial=0.,reads=0,dispatches=0,exposure_checks=0)


def test_geometry_and_pose_queries():
    d=loaded(FIXTURES);assert geometry(d)==480;assert len(query(d))==240 and len(query(d,True))==480;assert len(d.contexts)==10


@pytest.mark.parametrize('behavior',['flood','markers','constant','reversed'])
def test_nonchoices_score_zero(behavior):
    cases,meta,ids=fixture_pair();paths=[set(meta[i]['path']) for i in ids]
    if behavior=='flood':masks=[paths[0]|paths[1]]*2
    elif behavior=='markers':masks=[{cases[i].maze.start,cases[i].maze.goal} for i in ids]
    elif behavior=='constant':masks=[paths[0]]*2
    else:masks=paths[::-1]
    rs=[row(i,m) for i,m in zip(ids,masks)];assert pair_score(rs,meta)['score']==0;assert pair_score(rs,meta)==independent_proxy(rs,meta)


def test_partial_correct_exclusion_order():
    _,meta,ids=fixture_pair();paths=[set(meta[i]['path']) for i in ids]
    full=[row(i,p) for i,p in zip(ids,paths)];partial=[row(ids[0],paths[0]),row(ids[1],paths[0]|paths[1])]
    assert pair_score(full,meta)['score']==1 and pair_score(full,meta)['strict_both']
    assert 0<pair_score(partial,meta)['score']<1 and not pair_score(partial,meta)['strict_both']


def test_nonemitted_ordinary_output_gets_no_choice_credit():
    _,meta,ids=fixture_pair();rs=[row(i,meta[i]['path']) for i in ids];rs[0]['status']='step_budget';assert pair_score(rs,meta)['score']==0


@pytest.mark.parametrize('kind',['adjacent','fork'])
def test_marker_only_arms_ineligible(kind):
    _,meta,ids=fixture_pair(kind);rs=[row(i,meta[i]['path'],optimal=True) for i in ids];assert not pair_score(rs,meta)['eligible']


def test_current_selection_exact_M_parity_and_protected_anchors():
    pools,_,_,_,_=make_pools();pool=dict(items=pools['0']['items'][:4],anchors=[]);_,meta,ids=fixture_pair();rows={}
    for k,i in enumerate(pool['items']):rows[i['id']]=[row(cid,meta[cid]['path'] if k==0 else {meta[cid]['path'][0]},optimal=k==0) for cid in ids]
    a=choose(pool,rows,meta,198,'current');b=old_choose(pool,rows,meta,198)
    for key in ('parents','elite','nominees','rng_before','rng_after'):assert a[key]==b[key]
    pool['anchors']=[pool['items'][-1]['id']]
    for p in ('current','choice'):assert pool['anchors'][0] in choose(pool,rows,meta,198,p)['elite']


def test_neighborhoods_reproduce_and_exposure_is_unchanged():
    a=make_pools();b=make_pools();assert a==b
    pools,events,_,models,aliases=a;assert len(events)==576
    for pool in pools.values():
        assert len(pool['items'])==288
        by={i['id']:i for i in pool['items']}
        for child in pool['items'][96:]:assert child['genome']['exposure']==by[child['parent']]['genome']['exposure']
    assert all(m['genome']['exposure']==7 for m in models.values())
