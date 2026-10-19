from dataclasses import replace
import json
import random

import numpy as np
import pytest

from maze_evolution.foundation_calibration import controls
from maze_evolution.foundation_data import load_pairs, transform_point
from maze_evolution.growth import Genome, random_genome
from maze_evolution.growth_runtime import Organism, observe
from maze_evolution.regulatory import Gene
from maze_evolution.runtime import Limits
from maze_evolution.route_confirmation_data import FIXTURES, BANDS, minimum_turns, cycle_rank, rim_distance
from maze_evolution.route_confirmation_runtime import respond
from maze_evolution.route_confirmation import pack_history, unpack_history


def fixture():
    cases, groups = load_pairs(FIXTURES)
    return cases,groups,next(iter(cases.values())).maze


def identical(a,b):
    assert a.__dict__.keys()==b.__dict__.keys()
    for key,value in vars(a).items():
        assert np.array_equal(value,vars(b)[key]),key


def test_adapter_exact_runtime_parity_across_modes_and_budget_interrupts():
    _,_,m=fixture();rng=random.Random(1205)
    genomes=[controls()['intact'].genome]+[random_genome(rng,True) for _ in range(8)]
    for g in genomes:
        for topology in ('local','fixed','evolved'):
            for pulse in (False,True):
                for limits in (Limits(max_steps=24),Limits(max_steps=20,reads_per_site=1,instructions_per_site=9)):
                    organism=Organism(g,topology,limits,goal_pulse=pulse)
                    native=organism.react(m.cells,m.w,m.h,m.start,m.goal)
                    adapter=respond(organism,m.cells,m.w,m.h,m.start,m.goal,trace=True,horizon=24)
                    identical(native,adapter.reaction)
                    if native.steps:
                        assert np.array_equal(native.mask,adapter.history[-1,2]>0)


def test_forced_trace_matches_established_observer_at_multiple_ticks():
    _,_,m=fixture();rng=random.Random(1206)
    for genome in [controls()['intact'].genome]+[random_genome(rng,True) for _ in range(3)]:
        organism=Organism(genome,'local',Limits(max_steps=96),goal_pulse=True)
        traced=respond(organism,m.cells,m.w,m.h,m.start,m.goal,halt_mode='forced',trace=True,horizon=64)
        for tick in (1,8,16,32,64):
            old=observe(organism,m.cells,m.w,m.h,m.start,m.goal,tick,force_horizon=True)
            assert np.array_equal(traced.history[old.steps-1],old.state)
        assert not traced.history.flags.writeable
        assert np.array_equal(unpack_history(pack_history(traced.history)),traced.history)


def test_goal_pulse_and_flag_controls_are_independent():
    _,_,m=fixture()
    genome=Genome((Gene(13,2,1),Gene(13,3,10)))
    for pulse in (False,True):
        organism=Organism(genome,goal_pulse=pulse)
        for flag in (False,True):
            r=respond(organism,m.cells,m.w,m.h,m.start,m.goal,goal_flag=flag,halt_mode='forced',horizon=1)
            assert r.state[2,m.goal]==int(pulse)
            assert r.state[3,m.goal]==int(flag)
            assert r.state[2].sum()==int(pulse) and r.state[3].sum()==int(flag)


def test_endpoint_control_and_forced_horizon_do_not_invent_normal_emission():
    _,_,m=fixture()
    g=Genome((Gene(13,2,9),Gene(13,7,9)))
    organism=Organism(g,limits=Limits(max_steps=12),goal_pulse=True)
    native=respond(organism,m.cells,m.w,m.h,m.start,m.goal)
    src=respond(organism,m.cells,m.w,m.h,m.start,m.goal,halt_mode='source_only')
    forced=respond(organism,m.cells,m.w,m.h,m.start,m.goal,halt_mode='forced',trace=True,horizon=12)
    assert native.reaction.status=='quiescent' and native.reaction.steps==5
    assert src.reaction.status=='emitted' and src.reaction.steps==1
    assert forced.reaction.status=='step_budget' and forced.reaction.steps==12
    assert not forced.reaction.mask[m.goal]


def test_no_goal_input_produces_identical_goal_switched_forced_trajectories():
    _,groups,_=fixture();a,b=groups[0].pairs[0].cases
    g=random_genome(random.Random(1207),True)
    organism=Organism(g,goal_pulse=False)
    outputs=[]
    for o in (a,b):
        m=o.maze
        outputs.append(respond(organism,m.cells,m.w,m.h,m.start,m.goal,goal_flag=False,
            halt_mode='forced',trace=True,horizon=16).history)
    assert np.array_equal(*outputs)


def test_fixture_constraints_and_transformed_labels():
    cases,groups,_=fixture()
    assert len(groups)==25 and len(cases)==400
    for group in groups:
        for symmetry,pair in enumerate(group.pairs):
            a,b=pair.cases;m=a.maze
            if group.level<0:
                assert not a.path and not b.path
                continue
            low,high,turns,n=BANDS[group.level]
            label=a._foundation_label
            original=group.pairs[0].first._foundation_label
            assert label['vertex']==transform_point(original['vertex'],n,symmetry)
            assert len(set(label['allowed'][0])&set(label['allowed'][1]))==0
            rank=cycle_rank(m,a._from_start)
            assert (rank==0)==(m.family=='tree')
            for side,o in enumerate((a,b)):
                assert low<=len(o.path)-1<=high
                assert minimum_turns(o.maze,o._from_start)[o.maze.goal]>=turns
                assert label['min_turns'][side]>=turns
                if group.key[4]=='interior':
                    assert min(rim_distance(m.start,n),rim_distance(o.maze.goal,n))>=3


def test_diagnostic_limits_and_corrupt_trajectory_fail_closed():
    _,_,m=fixture();organism=Organism(controls()['intact'].genome)
    for kwargs in (dict(horizon=97),dict(trace=True),dict(goal_flag=1),dict(halt_mode='oracle')):
        with pytest.raises(ValueError):respond(organism,m.cells,m.w,m.h,m.start,m.goal,**kwargs)
    h=pack_history(np.zeros((1,8,4),dtype=np.uint16));h['raw_sha256']='bad'
    with pytest.raises(AssertionError):unpack_history(h)


def test_new_runtime_has_no_oracle_or_dataset_imports():
    import ast
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'maze_evolution/route_confirmation_runtime.py'
    source=path.read_text();tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            assert node.module in ('dataclasses','numba','beacon_runtime','growth_runtime','runtime')
