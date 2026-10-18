from dataclasses import asdict
from io import StringIO
import json
import random
import numpy as np
import pytest
from maze_evolution.regulatory import Gene, Genome, random_genome
from maze_evolution.regulatory_runtime import Organism
from maze_evolution.runtime import Limits
from maze_evolution.signal_probe import observe
from maze_evolution.signal_fitness import evaluate, signal_metrics
from maze_evolution.regulatory_search import Individual
from maze_evolution.datasets import make_case
from maze_evolution.evaluator import Maze, Oracle


@pytest.mark.parametrize('topology', ['local','fixed','evolved'])
def test_observer_matches_unmodified_inference_when_stopping_enabled(topology, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Oracle in interpreter')
    monkeypatch.setattr('cellular_maze_lab.bfs', forbidden)
    rng = random.Random(1042)
    cells = bytes([1,1,1,0,1,1,1,1,1])
    for _ in range(20):
        organism = Organism(random_genome(rng, True), topology, Limits(max_steps=24))
        normal = organism.react(cells,3,3,0,8)
        probe = observe(organism,cells,3,3,0,8,24,True,False)
        assert normal.status == probe.status
        assert (normal.steps,normal.dispatches,normal.spatial_reads,normal.range_reads) == (
            probe.steps,probe.dispatches,probe.reads,probe.range_reads)
        np.testing.assert_array_equal(normal.mask, probe.state[2] > 0)


def test_constants_and_source_only_cannot_earn_distal_reward():
    oracle=Oracle.build(Maze(bytes([1]*17),17,1,0,16))
    for genome in (Genome((Gene(13,3,11),)), Genome((Gene(13,3,9),))):
        o=Organism(genome)
        a=observe(o,oracle.maze.cells,17,1,0,16,16,True)
        b=observe(o,oracle.maze.cells,17,1,0,16,16,False)
        assert a.steps == b.steps == 16
        assert signal_metrics(a,b,oracle,16)['score']==0
        assert not np.any(b.state[0])
        assert not np.any(b.state[3]) if genome.genes[0].a==9 else True


def test_generic_source_transmission_is_measurable_without_output_reward():
    # Positive diagnostic only; never inserted into a random-origin population.
    genome=Genome((Gene(4,12,0),Gene(10,13,12,9),Gene(13,0,13)))
    oracle=Oracle.build(Maze(bytes([1]*17),17,1,0,16))
    item=Individual('unit',genome,None,0)
    current=evaluate(item,[oracle],'local',Limits(max_steps=32),'current')
    causal=evaluate(item,[oracle],'local',Limits(max_steps=32),'causal')
    assert current.signal==causal.signal==1
    assert current.rows[0]['signal']['max_distance']==16
    assert current.rows[0]['signal']['goal_signal']
    assert not current.rows[0]['valid']
    assert causal.fitness[:3]==current.fitness[:3]
    assert causal.fitness[3]==current.fitness[3]+1
    assert causal.work==current.work==causal.inference_work+causal.probe_work


def test_source_dependent_stopping_does_not_create_fake_hidden_signal():
    genome=Genome((Gene(13,2,11),Gene(13,7,9),Gene(2,12,3,11),Gene(13,3,12)))
    o=Organism(genome)
    oracle=Oracle.build(Maze(bytes([1]*9),9,1,0,8))
    assert o.react(oracle.maze.cells,9,1,0,8).steps==1
    a=observe(o,oracle.maze.cells,9,1,0,8,16,True)
    b=observe(o,oracle.maze.cells,9,1,0,8,16,False)
    assert a.steps==b.steps==16
    assert signal_metrics(a,b,oracle,16)['score']==0


def test_interrupted_probes_are_charged_but_not_rewarded():
    genome=Genome((Gene(4,12,0),Gene(13,0,12)))
    oracle=Oracle.build(Maze(bytes([1]*9),9,1,0,8))
    item=Individual('unit',genome,None,0)
    ev=evaluate(item,[oracle],'local',Limits(reads_per_site=1),'causal')
    assert not ev.rows[0]['signal']['aligned'] and ev.signal==0
    assert ev.probe_work>0
    assert ev.rows[0]['signal']['pair_array_bytes'] <= 80*9+65536


def test_pressure_fork_resets_scores_and_resume_is_exact(tmp_path):
    from maze_evolution.signal_search import search
    rng=random.Random(1043)
    ancestor=dict(config=dict(origin='random',method='evolution',rich=True,topology='local'),
        rng_state=rng.getstate(),population=[Individual('ancestor/'+str(i),random_genome(rng,True),None,120).save()
        for i in range(4)],champion_fitness=[999,999])
    fork=tmp_path/'ancestor.json'; fork.write_text(json.dumps(ancestor))
    config=dict(seed=1043,study='signal',topology='local',origin='random',pressure='causal',
        replicate=0,population=4,generations=4,rich=True,horizon=8,
        train_limits=asdict(Limits(max_steps=16)),eval_limits=asdict(Limits(max_steps=24)))
    val=[make_case(1043,'signal-validation-unit',0,0,9,'random')]
    batches=lambda g:[make_case(1043,'signal-train-unit',0,g,5,'perfect')]
    def execute(c,path,resume=None):
        return search(c,batches,val,StringIO(),StringIO(),[],path,fork=fork,resume=resume,progress=False)
    full=execute(config,tmp_path/'full.json')
    execute({**config,'generations':2},tmp_path/'part.json')
    resumed=execute(config,tmp_path/'part.json',tmp_path/'part.json')
    assert full==resumed
    assert full['fitness'][0]<=len(val)
    assert full['initial_digests']==[Genome.from_dict(v['genome']).digest for v in ancestor['population']]
    for pressure in ('current','causal'):
        result=execute({**config,'pressure':pressure,'generations':1},tmp_path/(pressure+'.json'))
        assert result['initial_digests']==full['initial_digests']
    ancestor['config']['origin']='seeded'; fork.write_text(json.dumps(ancestor))
    with pytest.raises(ValueError,match='random-origin'):
        execute(config,tmp_path/'bad.json')


def test_extension_gate_requires_replicated_paired_gain():
    from maze_evolution.signal_study import extension_decision
    champions={f'signal/{t}/{p}/{r}':dict(transmission_fitness=[.1,0,0],
        frozen_transmission_fitness=[.1,0,0],transmission_families={'perfect':.1,'random':.1},
        fitness=[0,0],frozen_fitness=[0,0]) for t in ('local','evolved')
        for p in ('current','causal') for r in range(3)}
    assert not extension_decision(champions)['extend']
    champions['signal/local/causal/0']['transmission_fitness'][0]=.5
    assert not extension_decision(champions)['extend']
    champions['signal/local/causal/1']['transmission_fitness'][0]=.4
    decision=extension_decision(champions)
    assert decision['extend'] and decision['signal_topologies']==['local']
