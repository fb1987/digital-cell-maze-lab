"""Scientific invariants for V12G, using saved construction fixtures only."""
import json,random
import numpy as np
import pytest
from maze_evolution.fork_data import FIXTURES,load,CorridorControls
from maze_evolution.fork_fitness import branch_score,evaluate,ranks,lexicase
from maze_evolution.fork_search import archive_rank
from maze_evolution.fork_confirm import evaluate_model,stats
from maze_evolution.foundation_calibration import controls,LIMITS
from maze_evolution.foundation_data import transform_maze
from maze_evolution.growth import mutate,replay_mutation
from maze_evolution.regulatory_search import Evaluation


@pytest.fixture(scope='module')
def data():return load(FIXTURES)


def test_calibration_passes():
    s=json.loads((FIXTURES/'calibration_summary.json').read_text())
    assert s['passed'] and s['controls']['intact']['optimal']==192
    assert s['controls']['intact']['no_path']==32
    assert s['controls']['two_return_gates']['optimal']<192


def test_corridors_are_not_goal_switch_pairs(data):
    for g in data[1]:
        if 'corridor' in g.key:
            for p in g.pairs:
                assert isinstance(p,CorridorControls)
                assert p.first.maze.cells!=p.second.maze.cells
                assert all(o._foundation_label is None for o in p.cases)


def test_all_d4_poses_are_exact(data):
    for g in data[1]:
        for s,p in enumerate(g.pairs):
            for o,base in zip(p.cases,g.pairs[0].cases):
                m=transform_maze(base.maze,s)
                assert (m.cells,m.start,m.goal)==(o.maze.cells,o.maze.start,o.maze.goal)


def test_pruning_retains_route_and_clutter(data):
    groups={g.key:g for g in data[1]}
    for g in data[1]:
        if 'corridor' in g.key or 'cut' in g.key:continue
        for p,c in zip(g.pairs,groups[g.key+('corridor',)].pairs):
            for o,k in zip(p.cases,c.cases):
                assert o.path==k.path
                extra=[x for x,v in enumerate(k.maze.cells) if v and x not in k.path]
                assert len(extra)==8 and all(k._from_start[x]<0 for x in extra)


def test_suppression_ordering_all_fixtures(data):
    for g in data[1]:
        if 'corridor' in g.key or 'cut' in g.key:continue
        for p in g.pairs:
            for side,o in enumerate(p.cases):
                lab=o._foundation_label;mask=np.zeros(len(o.maze.cells),np.uint8);mask[lab['prefix']]=1
                prefix=branch_score(mask,o,side)
                mask[lab['exits']]=1;leaking=branch_score(mask,o,side)
                mask[list(set(lab['exits'])-set(lab['allowed'][side]))]=0;choice=branch_score(mask,o,side)
                assert prefix['score']<leaking['score']<choice['score']
                assert choice['strict'] and not leaking['strict']


def test_missing_incoming_is_not_strict(data):
    g=next(g for g in data[1] if g.level==1 and 'corridor' not in g.key)
    o=g.pairs[0].first;lab=o._foundation_label
    mask=np.zeros(len(o.maze.cells),np.uint8);mask[o.path]=1;mask[lab['incoming']]=0
    assert not branch_score(mask,o,0)['strict']


def test_confirmation_runtime_adapter_parity(data):
    pairs=[p for g in data[1] if g.key[0]=='construction' for p in g.pairs]
    item=controls()['two_return_gates']
    old=evaluate(item,pairs,'evolved',LIMITS,'current');new=evaluate_model(item,pairs,'evolved')
    assert old.rows==new.rows and old.work==new.work and old.fitness==new.fitness


def test_corridor_pairs_cannot_count_as_fork_success(data):
    g=next(g for g in data[1] if 'corridor' in g.key)
    rows=evaluate(controls()['intact'],g.pairs,'local',LIMITS,'current').rows
    assert all(r['pair_optimal'] for r in rows) and ranks(rows,'current')[3]==0
    assert stats(rows)['complete_pairs']==0 and stats(rows)['corridor_optimal']==16


def test_common_primary_archive_independent_of_pressure(data):
    g=next(g for g in data[1] if g.key[0]=='construction')
    a=evaluate(controls()['two_return_gates'],g.pairs,'local',LIMITS,'current')
    b=evaluate(controls()['two_return_gates'],g.pairs,'local',LIMITS,'branch')
    assert a.rows==b.rows
    assert archive_rank(a.rows,'pair')==archive_rank(b.rows,'pair')


def test_branch_field_changes_reproduction():
    a=Evaluation((),[(0,0,0,0,.8)],(),[],0);b=Evaluation((),[(0,0,0,1,.7)],(),[],0)
    assert lexicase(random.Random(1),[(a,'leak'),(b,'choice')])=='choice'
    b.case_values=[(0,0,0,0,.7)]
    assert lexicase(random.Random(1),[(a,'leak'),(b,'choice')])=='leak'


def test_single_edit_replay_and_ceiling():
    genome=controls()['intact'].genome;rng=random.Random(1214)
    for _ in range(100):
        child,events=mutate(genome,rng,1,256,True)
        assert len(events)==1 and replay_mutation(genome,events,256)==child
        genome=child


def test_cut_controls_have_no_route(data):
    cuts=[g for g in data[1] if 'cut' in g.key]
    assert len(cuts)==2 and all(not o.path for g in cuts for p in g.pairs for o in p.cases)
