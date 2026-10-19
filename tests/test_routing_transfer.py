"""Scientific guardrails for the fixed V12H transfer/mechanism assay."""
from dataclasses import replace
import json
import random

import numpy as np
import pytest

from maze_evolution.foundation_calibration import controls, LIMITS
from maze_evolution.foundation_study import read_compressed
from maze_evolution.growth import Genome, random_genome, Individual
from maze_evolution.growth_runtime import Organism
from maze_evolution.regulatory import Gene
from maze_evolution.runtime import Limits
from maze_evolution.route_confirmation_runtime import respond
from maze_evolution.routing_transfer_data import FIXTURES, FAMILIES, load
from maze_evolution.routing_transfer import MODES, organism, inference, canonical, record, summarize, Budget
from maze_evolution.routing_transfer_audit import audit_geometry, reaction_fields, synthetic
from maze_evolution.evaluator import assess


def fixtures():
    return load(FIXTURES)


def test_matched_graphs_unique_shortest_and_real_longer_alternatives():
    cases,contexts,metadata=fixtures();r=audit_geometry(cases,contexts,metadata)
    assert r==dict(no_path_cases=64,shortest_masks=256,decision_labels=192,
        reachable_cases=256,legal_longer_masks=64,contexts=4,whole_layouts=192,cases=320)


def test_geometry_audit_rejects_mislabeled_alternative_and_missing_branch():
    cases,contexts,metadata=fixtures()
    changed=json.loads(json.dumps(contexts));changed[0]['poses'][0]['meta']['gap']+=1
    with pytest.raises(AssertionError):audit_geometry(cases,changed,metadata)
    changed=json.loads(json.dumps(contexts));changed[0]['poses'][0]['meta']['stub']=[]
    with pytest.raises(AssertionError):audit_geometry(cases,changed,metadata)


def test_longer_legal_route_is_not_scored_shortest():
    cases,contexts,metadata=fixtures();p=contexts[0]['poses'][0];cid=p['cases']['alternate_cycle'][0]
    o=cases[cid];r=synthetic(o,p['meta']['alternatives'][0]);row=record(r,o,metadata[cid])
    assert row['valid'] and not row['optimal'] and row['failure']==''
    summary=summarize([row],metadata)
    assert summary['strata']['alternate_cycle/band0']['complete_pairs']==0


def test_corridors_never_count_as_goal_switch_pairs():
    cases,contexts,metadata=fixtures();rows=[]
    for cid,o in cases.items():
        if metadata[cid]['family']=='corridor':rows.append(record(synthetic(o,o.path),o,metadata[cid]))
    stats=summarize(rows,metadata)
    assert sum(s['optimal'] for s in stats['strata'].values())==64
    assert all(s['complete_pairs']==s['any_contexts']==0 for s in stats['strata'].values())


def test_exact_native_adapter_parity_for_topologies_pulses_and_caps():
    cases,contexts,metadata=fixtures();m=cases[contexts[2]['poses'][3]['cases']['alternate_cycle'][0]].maze
    rng=random.Random(1225)
    for genome in [controls()['intact'].genome]+[random_genome(rng,True) for _ in range(4)]:
        for topology in ('local','evolved'):
            for pulse in (False,True):
                for limits in (LIMITS,Limits(max_steps=32,reads_per_site=1,instructions_per_site=9)):
                    org=Organism(genome,topology,limits,goal_pulse=pulse)
                    native=org.react(m.cells,m.w,m.h,m.start,m.goal)
                    adapted=respond(org,m.cells,m.w,m.h,m.start,m.goal).reaction
                    for key,value in vars(native).items():assert np.array_equal(value,vars(adapted)[key])


def test_goal_controls_remove_distinct_inputs_and_stopping_checks():
    cases,contexts,metadata=fixtures();m=next(iter(cases.values())).maze
    genome=Genome((Gene(13,2,1),Gene(13,3,10)))
    for pulse in (False,True):
        org=Organism(genome,limits=Limits(max_steps=1),goal_pulse=pulse)
        for flag in (False,True):
            r=respond(org,m.cells,m.w,m.h,m.start,m.goal,goal_flag=flag,halt_mode='forced',horizon=1)
            assert r.state[2,m.goal]==int(pulse) and r.state[3,m.goal]==int(flag)
    genome=Genome((Gene(13,2,9),Gene(13,7,9)))
    org=Organism(genome,limits=Limits(max_steps=12),goal_pulse=False)
    normal=respond(org,m.cells,m.w,m.h,m.start,m.goal,goal_flag=False).reaction
    blind=respond(org,m.cells,m.w,m.h,m.start,m.goal,goal_flag=False,halt_mode='source_only').reaction
    assert normal.status=='quiescent' and normal.steps==5
    assert blind.status=='emitted' and blind.steps==1


def test_all_goal_off_pair_reactions_and_forced_states_identical():
    cases,contexts,metadata=fixtures();pair=[cases[c] for c in contexts[0]['poses'][0]['cases']['alternate_cycle']]
    rng=random.Random(1226)
    for genome in [controls()['intact'].genome]+[random_genome(rng,True) for _ in range(4)]:
        entry=dict(item=Individual('fixture-only',genome,None,0).save(),topology='evolved')
        org=organism(entry,'all_goal_off');rows=[];histories=[]
        for o in pair:
            r=inference(org,o.maze,'all_goal_off');rows.append(record(r,o,metadata[o.maze.case_id]))
            histories.append(inference(org,o.maze,'pulse_flag_off',True).history)
        assert canonical(reaction_fields(rows[0]))==canonical(reaction_fields(rows[1]))
        assert np.array_equal(*histories)


def test_budget_reserve_fails_before_more_inference():
    budget=Budget();budget.seconds=596.;calls=[]
    with pytest.raises(TimeoutError):budget.call('guard',lambda:calls.append(True))
    assert not calls


def test_model_screen_requires_both_harder_families_and_multiple_poses():
    # Synthetic complete emissions exercise aggregation, not candidate performance.
    cases,contexts,metadata=fixtures();rows=[]
    for cid,o in cases.items():
        if metadata[cid]['family'] in FAMILIES:
            rows.append(record(synthetic(o,o.path),o,metadata[cid]))
    stats=summarize(rows,metadata)
    assert all(s['all_pose_contexts']==2 and s['complete_pairs']==16 for s in stats['strata'].values())
    # Two contexts cannot pass thresholds intended for a 24-context long band.
    assert not stats['screen_pass']
