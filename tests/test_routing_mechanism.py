import numpy as np
import pytest
from maze_evolution.routing_mechanism_data import *
from maze_evolution.routing_mechanism_runtime import respond
from maze_evolution.routing_mechanism_study import schedules,pack_history,unpack_history
from maze_evolution.routing_mechanism_audit import geometry,independent_predictor
from maze_evolution.routing_mechanism_analysis import predictions
from maze_evolution.regulatory import Gene
from maze_evolution.growth import Genome as Program
from maze_evolution.exposure_genome import Genome
from maze_evolution.exposure_selection import organism,record

@pytest.fixture(scope='module')
def data():return load(FIXTURES)

@pytest.fixture(scope='module')
def panel():return read_compressed(OUT/'panel.json.gz')

def model(*genes):return dict(genome=Genome(Program(tuple(genes)),7).to_dict(),topology='local')

def test_geometry_and_all_poses(data):
    c,ctx,m=data;g=geometry(c,ctx,m)
    assert g['inputs']==4480 and g['pairs']==1440 and g['nonisolated_no_path']==512
    assert {v['shape'] for v in ctx}==set(SHAPES)

def test_all_prior_layouts_excluded(data):
    c,_,_=data;assert not exclusions()&{layout_hash(o.maze) for o in c.values()}

def test_panel_exact_random_roots_and_mixed_sexual_ancestry(panel):
    assert len(panel['models'])==12
    for name,root,steps in [('fresh0','fresh0_root',96),('fresh2','fresh2_root',75)]:
        assert panel['chains'][name]['roots']==[panel['items'][root]['id']]
        assert len(panel['chains'][name]['nodes'])==steps+1
        assert not panel['events'][panel['items'][root]['id']]['parents']
    assert len(panel['chains']['spliced']['roots'])==3

def test_schedule_normal_first_and_no_success_filter(data,panel):
    _,_,m=data;s=list(schedules(panel,m));n=len(panel['models'])
    assert all(x[0]=='normal' for x in s[:n]) and all(x[0]!='normal' for x in s[n:])
    assert {len(ids) for scope,_,_,ids in s if scope=='intervention'}=={1280}
    assert sum(len(ids) for scope,_,_,ids in s if scope=='trace')==2304

def test_normal_parity_with_trace_at_native_emission(data,panel):
    c,_,m=data;o=next(o for cid,o in c.items() if m[cid]['family']=='paired');maze=o.maze
    for name in ('fresh0','fresh2','carry0','intact'):
        mod=panel['models'][panel['aliases'][name]];native=organism(mod).react(maze.cells,maze.w,maze.h,maze.start,maze.goal)
        assert record(respond(mod,maze).reaction,o)==record(native,o)
        trace=respond(mod,maze,trace=True,forced=True)
        if native.steps<=len(trace.history):assert np.array_equal((trace.history[native.steps-1,2]>0).astype(np.uint8),native.mask)

def test_feedback_ablation_preserves_writes_and_emission(data):
    o=next(iter(data[0].values()));m=o.maze
    # Persist output1, copy previous output into channel3. Ablation must change
    # channel3 without deleting output or changing the available store opcode.
    mod=model(Gene(1,12,1),Gene(13,2,12),Gene(13,3,2))
    a=respond(mod,m,trace=True,forced=True,horizon=3);b=respond(mod,m,'output_feedback_off',trace=True,forced=True,horizon=3)
    assert np.array_equal(a.history[:,2],b.history[:,2]) and a.history[-1,3].any() and not b.history[-1,3].any()
    assert a.reaction.dispatches==b.reaction.dispatches

def test_feedback_ablation_covers_spatial_output_reads(data):
    m=next(iter(data[0].values())).maze
    mod=model(Gene(1,12,1),Gene(13,2,12),Gene(4,13,2),Gene(13,3,13))
    a=respond(mod,m,trace=True,forced=True,horizon=3);b=respond(mod,m,'output_feedback_off',trace=True,forced=True,horizon=3)
    assert a.history[-1,3].any() and not b.history[-1,3].any()
    assert a.reaction.spatial_reads==b.reaction.spatial_reads and np.array_equal(a.reaction.mask,b.reaction.mask)

def test_halt_request_and_endpoint_interventions_distinct(data):
    m=next(iter(data[0].values())).maze
    # All outputs lit, request immediate halt. Request-off waits for quiescence.
    mod=model(Gene(1,12,1),Gene(13,2,12),Gene(13,7,12))
    a=respond(mod,m).reaction;b=respond(mod,m,'halt_off').reaction
    assert a.steps==1 and b.steps==5 and np.array_equal(a.mask,b.mask)
    # Source-only output satisfies endpoint-off but never normal endpoint check.
    mod=model(Gene(13,2,9),Gene(1,12,1),Gene(13,7,12))
    assert respond(mod,m,'endpoint_off').reaction.steps==1 and respond(mod,m).reaction.steps==5

def test_both_off_forced_goal_switch_identical(data,panel):
    c,_,meta=data;cid=next(k for k,m in meta.items() if trace_case(m));q=meta[cid]
    ids=[k for k,m in meta.items() if m['base']==q['base'] and m['pose']==q['pose']];assert len(ids)==2
    mod=panel['models'][panel['aliases']['fresh2']]
    a,b=[respond(mod,c[i].maze,'both_off',trace=True,forced=True,horizon=8).history for i in ids]
    assert np.array_equal(a,b) and np.array_equal(unpack_history(pack_history(a)),a)

def test_predictor_is_independently_reproducible(data):
    c,_,meta=data
    for cid,o in c.items():
        if meta[cid]['pose']==0 and meta[cid]['family']=='paired':assert predictions(o)==[independent_predictor(o,k) for k in range(7)]

def test_forced_requires_explicit_bounded_trace(data,panel):
    m=next(iter(data[0].values())).maze;mod=panel['models'][panel['aliases']['fresh2']]
    with pytest.raises(ValueError):respond(mod,m,forced=True)
    with pytest.raises(ValueError):respond(mod,m,trace=True,horizon=10000)
