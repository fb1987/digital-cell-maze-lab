"""Scientific guardrails for V12I fixed-pool equal-budget selection."""
from copy import deepcopy
import json

import pytest

from maze_evolution.foundation_calibration import ROOT
from maze_evolution.foundation_study import read_compressed
from maze_evolution.growth import Individual
from maze_evolution.routing_transfer_audit import synthetic
from maze_evolution.foundation_pair_confirm import normal_row
from maze_evolution.validation_breadth_data import FIXTURES, OUT, FAMILIES, load, validation
from maze_evolution.validation_breadth import summarize, choose, Budget, committed
from maze_evolution.validation_breadth_audit import geometry, schedule_check
from maze_evolution.validation_breadth_analysis import gate


def test_fixture_geometry_shortest_unique_and_real_longer_rasters():
    cases,contexts,metadata=load(FIXTURES)
    assert geometry(cases,contexts,metadata)==dict(no_path_cases=64,decision_labels=192,
        legal_longer_masks=64,reachable_cases=256,contexts=4,whole_layouts=192,cases=320)


def test_geometry_rejects_alternative_chord_and_wrong_distance():
    cases,contexts,metadata=load(FIXTURES)
    bad=deepcopy(contexts); bad[0]['poses'][0]['meta']['alternatives'][0]=bad[0]['poses'][0]['meta']['paths'][0]
    with pytest.raises(AssertionError): geometry(cases,bad,metadata)
    bad=deepcopy(contexts); bad[0]['poses'][0]['meta']['lengths'][0]+=1
    with pytest.raises(AssertionError): geometry(cases,bad,metadata)


def test_schedule_exactly_matches_input_strata_and_poses_without_new_fixture_generation():
    class LabelsOnly:
        def __init__(self): self.metadata={}
        def context(self,split,index,stratum):
            base=f'{split}/s{stratum}/{index}'; poses=[]
            for symmetry in range(8):
                cases={}
                for family in (*FAMILIES,'corridor_0','corridor_1'):
                    sides=[int(family[-1])] if family.startswith('corridor') else [0,1]
                    cases[family]=[]
                    for side in sides:
                        cid=f'{base}/{symmetry}/{family}/{side}'; cases[family].append(cid)
                        self.metadata[cid]=dict(base=base,stratum=stratum,symmetry=symmetry,
                            family='corridor' if family.startswith('corridor') else family,side=side)
                poses.append(dict(cases=cases))
            return dict(poses=poses)
    d=LabelsOnly(); schedule=validation(d); schedule_check(schedule,d.metadata)
    schedule['0']['broad'][0]=schedule['0']['broad'][1]
    with pytest.raises(AssertionError): schedule_check(schedule,d.metadata)


def test_pool_contains_every_initial_individual_nominee_and_protected_anchor_only():
    p=read_compressed(OUT/'pool.json.gz')
    initial=read_compressed(ROOT/'results/fork_pressure/initial_states.json.gz')
    states={s['key']:s for s in read_compressed(ROOT/'results/fork_pressure/checkpoint.latest.json.gz')['states']}
    assert len(p['conditions'])==30
    for s in initial:
        expected={i['id'] for i in s['population']}|{i for h in states[s['key']]['history'] for i in h['nominees']}
        c=p['conditions'][s['key']]
        assert {m['id'] for m in c['members']}==expected
        assert {i['id'] for i in s['protected']}<=expected
        assert all(p['models'][m]['topology']==s['config']['topology'] for m in c['models'])
    assert all(1<=len(Individual.load(m['item']).genome.genes)<=256 for m in p['models'].values())
    assert not any(m['item']['id'].startswith('positive_control/') for m in p['models'].values())


def test_corridor_outputs_and_longer_legal_routes_cannot_score_shortest_pairs():
    cases,contexts,metadata=load(FIXTURES); pose=contexts[0]['poses'][0]
    rows=[normal_row(synthetic(cases[cid],cases[cid].path),cases[cid]) for f in ('corridor_0','corridor_1') for cid in pose['cases'][f]]
    assert summarize(rows,metadata)['rank'][:5]==[0,0,0,0,2]
    rows=[normal_row(synthetic(cases[cid],pose['meta']['alternatives'][i]),cases[cid]) for i,cid in enumerate(pose['cases']['alternate_cycle'])]
    assert summarize(rows,metadata)['rank'][:4]==[0,0,0,2]
    rows=[normal_row(synthetic(cases[cid],cases[cid].path),cases[cid]) for cid in pose['cases']['fork']]
    assert summarize(rows,metadata)['rank'][0]==1


def test_selection_pairs_first_and_digest_ties_are_order_independent():
    scores={'b':dict(rank=[1,0,2,2,0,0,0]),'a':dict(rank=[1,0,2,2,0,0,0]),'c':dict(rank=[0,0,48,48,32,0,100])}
    assert choose(['b','c','a'],scores)==choose(['a','b','c'],scores)=='a'


def test_time_and_call_caps_prevent_additional_candidate_invocation():
    budget=Budget(); budget.seconds=716
    with pytest.raises(TimeoutError): budget.call('test',None,None)
    budget=Budget(max_calls=0)
    with pytest.raises(TimeoutError): budget.call('test',None,None)
    assert budget.calls==0


def test_uncommitted_selection_is_rejected_before_holdout(monkeypatch):
    monkeypatch.setattr('maze_evolution.validation_breadth.subprocess.check_output',lambda *a,**k:b'not the saved bytes')
    with pytest.raises(AssertionError,match='Uncommitted freeze'): committed(OUT/'pool.json.gz')


def test_gate_requires_context_cycle_harder_stratum_and_corridor_retention():
    n=dict(pairs=10,contexts=['a'],cycle_contexts=[],stratum_pairs=[10,0,0,0],corridor_shortest=100,false_no_path=0)
    b=dict(pairs=18,contexts=['a','b','c'],cycle_contexts=['b'],stratum_pairs=[17,1,0,0],corridor_shortest=95,false_no_path=0)
    assert all(gate(n,b).values())
    for key,value in [('pairs',17),('contexts',['a','b']),('cycle_contexts',[]),('stratum_pairs',[18,0,0,0]),('corridor_shortest',94),('false_no_path',1)]:
        assert not all(gate(n,{**b,key:value}).values())


def test_audit_summary_roundtrips_native_counts_without_numpy_serialization():
    cases,contexts,metadata=load(FIXTURES)
    r=geometry(cases,contexts,metadata)
    assert json.loads(json.dumps(r))==r
