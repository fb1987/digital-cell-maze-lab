"""V12J independent geometry, denominators, interventions and budget guardrails."""
from copy import deepcopy
import json
import numpy as np
import pytest

from maze_evolution.junction_distance import Budget, CAP_CALLS, selected, TARGETS, panel
from maze_evolution.junction_distance_data import FIXTURES, OUT, load
from maze_evolution.junction_distance_audit import geometry, compare_traces
from maze_evolution.junction_distance_analysis import pairs, transfer_gate
from maze_evolution.foundation_pair_confirm import normal_row
from maze_evolution.foundation_study import read_compressed
from maze_evolution.foundation_study_verify_core import Checker
from maze_evolution.routing_transfer_audit import synthetic
from maze_evolution.routing_transfer import canonical, organism, inference
from maze_evolution.route_confirmation_runtime import respond


def test_geometry_matched_downstream_unique_shortest_and_true_alternatives():
    cases,contexts,meta=load(FIXTURES)
    assert geometry(cases,contexts,meta)==dict(no_path_cases=160,reachable_cases=960,
        legal_longer_rasters=320,contexts=1,cases=1120,whole_layouts=512)


def test_corrupt_distance_alternative_and_second_junction_are_rejected():
    cases,contexts,meta=load(FIXTURES)
    cid=next(c for c,m in meta.items() if m['family']=='cycle_4')
    for key,value in [('prefix',3),('alternative',meta[cid]['path']),('second_junctions',{'2':0,'4':0})]:
        bad=deepcopy(meta);bad[cid][key]=value
        with pytest.raises(AssertionError):geometry(cases,contexts,bad)


def test_prespecified_coverage_and_no_success_adaptive_selection():
    _,_,meta=load(FIXTURES)
    assert sum(selected(m) for m in meta.values())==800
    assert sum(selected(m,True) for m in meta.values())==72
    assert len(TARGETS)==9
    # Twelve normal contexts, two intervention contexts and one trace context.
    assert 1120*12*14+800*2*9*6+72*9*4==277152


def test_panel_is_exact_saved_genomes_parents_and_no_solver_in_random_lineage():
    current,_=panel();saved=read_compressed(OUT/'panel.json.gz')
    assert canonical(current)==saved
    for name in ('branch_narrow','branch_broad'):
        assert saved[name]['item']['parent']==saved[name+'_parent']['item']['id']
    assert len(saved)==14 and saved['resampled']['genes']==68 and saved['resampled']['item']['parent'] is None
    assert all(not e['item']['id'].startswith('positive_control/') for n,e in saved.items() if n!='intact')


def test_corridors_and_legal_longer_paths_do_not_score_pairs():
    cases,_,meta=load(FIXTURES)
    ids=[c for c,m in meta.items() if m['shape']=='straight' and m['prefix']==1 and m['pose']==0]
    rows=[normal_row(synthetic(cases[c],meta[c]['alternative']),cases[c]) for c in ids if meta[c]['family']=='cycle_4']
    assert not any(pairs(rows,meta).values())
    rows=[normal_row(synthetic(cases[c],meta[c]['path']),cases[c]) for c in ids if meta[c]['family'].startswith('corridor')]
    assert pairs(rows,meta)=={}
    rows=[normal_row(synthetic(cases[c],meta[c]['path']),cases[c]) for c in ids if meta[c]['family']=='fork']
    assert sum(pairs(rows,meta).values())==1


def test_caps_stop_before_calling_candidate():
    budget=Budget();budget.seconds=716
    with pytest.raises(TimeoutError):budget.call('x',None)
    budget=Budget();budget.calls=CAP_CALLS
    with pytest.raises(TimeoutError):budget.call('x',None)


def test_transfer_screen_needs_contexts_all_poses_both_shapes_and_corridors():
    ps={(f'c{i}',shape,p,f,s):True for i in range(3) for shape in ('straight','bent')
        for p in (6,8) for f in ('fork','cycle_4') for s in range(8)}
    meta={f'c{i}':dict(base=f'c{i}',family='corridor_0',prefix=6) for i in range(3)}
    rows=[dict(case=c,optimal=True,reachable=True,status='solved') for c in meta]
    assert transfer_gate(ps,rows,meta)['passed']
    ps['c0','bent',8,'cycle_4',7]=False
    assert not transfer_gate(ps,rows,meta)['passed']
    ps['c0','bent',8,'cycle_4',7]=True;rows[0]['optimal']=False
    assert not transfer_gate(ps,rows,meta)['passed']


def test_goal_response_tick_axis_and_numpy_counts_serialize():
    cases,_,meta=load(FIXTURES);checker=Checker(cases)
    ids=[c for c,m in meta.items() if m['shape']=='straight' and m['prefix']==1 and m['pose']==0 and m['family']=='fork']
    oa,ob=[cases[c] for c in ids];a=np.zeros((7,8,625),np.uint16);b=a.copy()
    for o in (oa,ob):checker.row(normal_row(synthetic(o,o.path),o))
    b[3,2,oa.maze.start]=1
    r=compare_traces(a,b,oa,ob,meta[ids[0]],checker)
    assert r['first_source_difference']==r['first_output_away_difference']==4
    assert json.loads(json.dumps(r))==r


def test_native_parity_and_both_signal_off_goal_blind_forced_trajectory():
    cases,_,meta=load(FIXTURES);models=read_compressed(OUT/'panel.json.gz')
    ids=[c for c,m in meta.items() if m['shape']=='bent' and m['prefix']==8 and m['pose']==0 and m['family']=='cycle_4']
    a,b=[cases[c] for c in ids]
    for name in ('branch_narrow','fresh_evolved','resampled','intact'):
        org=organism(models[name]);m=a.maze
        assert canonical(normal_row(inference(org,m),a))==canonical(normal_row(respond(org,m.cells,m.w,m.h,m.start,m.goal).reaction,a))
        org=organism(models[name],'pulse_flag_off')
        assert np.array_equal(inference(org,a.maze,'pulse_flag_off',True).history,inference(org,b.maze,'pulse_flag_off',True).history)
