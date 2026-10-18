import random
import numpy as np
import pytest

from maze_evolution.regulatory import (Gene, Genome, REMOTE, REMOTE_MIN, ALWAYS,
                                      mutate, random_genome, seeded_genome)
from maze_evolution.regulatory_runtime import Organism
from maze_evolution.runtime import Limits, Organism as V1Organism
from maze_evolution.genome import wavefront_genome
from maze_evolution.datasets import make_case
from maze_evolution.evaluator import assess, Oracle, Maze


def test_larger_typed_genome_and_mutations_stay_bounded():
    rng = random.Random(833)
    genome = random_genome(rng, rich=True)
    for _ in range(200):
        genome = mutate(genome, rng, 6)
        assert Genome.from_dict(genome.to_dict()) == genome
        assert genome.array().nbytes <= 4096
    for factory in (lambda: Gene(6, 12, 0, 4), lambda: Gene(14, 12, 0, radius=4),
                    lambda: Gene(13, 0, 99), lambda: Gene(0, 12, 1, gate=65),
                    lambda: Genome((Gene(0, 12, 1),)*129)):
        with pytest.raises(ValueError):
            factory()


@pytest.mark.parametrize('topology', ['local', 'fixed', 'evolved'])
@pytest.mark.parametrize('family', ['perfect', 'random', 'rectangular', 'disconnected'])
def test_seed_port_keeps_legal_local_algorithm(topology, family, monkeypatch):
    oracle = make_case(834, 'unit-v2', 0, 1, 17, family)
    m = oracle.maze
    old = V1Organism(wavefront_genome()).react(m.cells, m.w, m.h, m.start, m.goal)
    def forbidden(*args, **kwargs):
        raise AssertionError('Solver shortcut')
    monkeypatch.setattr('cellular_maze_lab.bfs', forbidden)
    monkeypatch.setattr('cellular_maze_lab.wave_cell', forbidden)
    result = Organism(seeded_genome(), topology).react(m.cells, m.w, m.h, m.start, m.goal)
    np.testing.assert_array_equal(old.mask, result.mask)
    assert assess(result, oracle).optimal if oracle.path else assess(result, oracle).no_path_correct
    assert result.range_reads[1:] == (0, 0, 0)


def test_nonlocal_information_does_not_create_movement_edges():
    genome = Genome((Gene(REMOTE, 12, 0, 0, radius=1), Gene(13, 2, 12)))
    cells = bytes([1, 0, 1])
    local = Organism(genome, 'local', Limits(max_steps=1)).react(cells, 3, 1, 0, 2)
    remote = Organism(genome, 'evolved', Limits(max_steps=1)).react(cells, 3, 1, 0, 2)
    ablated = Organism(genome, 'evolved', Limits(max_steps=1), True).react(cells, 3, 1, 0, 2)
    assert local.mask.tolist() == [0, 0, 0]
    assert remote.mask.tolist() == [0, 0, 1]
    assert not ablated.mask.any()
    assert remote.spatial_reads == ablated.spatial_reads == 2
    assert not assess(remote, Oracle.build(Maze(cells, 3, 1, 0, 2))).valid_path


def test_fixed_schedule_is_not_stopped_by_one_quiet_phase():
    genome = Genome((Gene(REMOTE, 12, 0, 0), Gene(13, 2, 12)))
    result = Organism(genome, 'fixed', Limits(max_steps=2)).react(bytes([1, 0, 1]), 3, 1, 0, 2)
    assert result.steps == 2 and result.mask.tolist() == [0, 0, 1]
    assert result.range_reads == (2, 2, 0, 0)


def test_false_regulatory_gate_skips_reads_but_still_charges_dispatch():
    genome = Genome((Gene(REMOTE_MIN, 12, 0, gate=13), Gene(13, 2, 12)))
    result = Organism(genome, 'evolved').react(bytes([1]*9), 3, 3, 0, 8)
    assert result.spatial_reads == 0
    assert result.active_instructions == result.dispatches // 2
    assert result.dispatches == 4 * 9 * 2


def test_discard_partial_tick_and_count_its_work():
    genome = Genome((Gene(REMOTE, 12, 0, 0), Gene(13, 2, 12), Gene(REMOTE, 12, 0, 1)))
    result = Organism(genome, 'local', Limits(reads_per_site=1)).react(bytes([1]*3), 3, 1, 0, 2)
    assert result.status == 'read_budget' and result.steps == 0
    assert result.spatial_reads == 3 and not result.mask.any()


def test_broad_output_can_develop_before_halt():
    # First tick lights everything; later ticks clear it. No implicit early stop.
    genome = Genome((Gene(11, 12, 3), Gene(13, 2, 12),
                     Gene(2, 13, 3, 11), Gene(13, 3, 13)))
    result = Organism(genome, limits=Limits(max_steps=3)).react(bytes([1]*9), 3, 3, 0, 8)
    assert result.steps == 3 and result.status == 'step_budget' and not result.mask.any()
    halted = Genome(genome.genes + (Gene(13, 7, 11),))
    result = Organism(halted).react(bytes([1]*9), 3, 3, 0, 8)
    assert result.steps == 1 and result.status == 'emitted'
    assert not assess(result, Oracle.build(Maze(bytes([1]*9), 3, 3, 0, 8))).valid_path


def test_neighbor_count_saturating_state_and_memory():
    genome = Genome((Gene(17, 12, 0), Gene(13, 2, 12)))
    result = Organism(genome, limits=Limits(max_steps=1)).react(bytes([1]*9), 3, 3, 4, 8)
    assert np.flatnonzero(result.mask).tolist() == [1, 3, 5, 7]
    assert result.array_bytes <= 64 * 9 + 65536


def test_checkpoint_resume_matches_uninterrupted_search(tmp_path):
    from dataclasses import asdict
    from io import StringIO
    import json
    from maze_evolution.regulatory_search import search
    from maze_evolution.range_study import StudyData
    config=dict(seed=835,study='rich',topology='evolved',origin='random',method='evolution',
                replicate=0,population=4,generations=4,rich=True,
                train_limits=asdict(Limits(max_steps=32)),eval_limits=asdict(Limits(max_steps=64)),search_version=2)
    data=StudyData(835)
    batch=lambda g:data.batch('rich',0,g)
    validation=data.validation(0)
    def execute(settings,path,resume=None):
        registry,evaluations,history=StringIO(),StringIO(),[]
        result=search(settings,batch,validation,registry,evaluations,history,path,resume,False)
        return result,history
    whole,_=execute(config,tmp_path/'whole.json')
    short=dict(config,generations=2)
    execute(short,tmp_path/'short.json')
    continued,_=execute(config,tmp_path/'continued.json',tmp_path/'short.json')
    assert whole==continued
    a=json.loads((tmp_path/'whole.json').read_text())
    b=json.loads((tmp_path/'continued.json').read_text())
    assert a==b


def test_unfinished_phenotypes_have_no_cost_tie_break():
    from maze_evolution.regulatory_search import Individual,evaluate
    case=Oracle.build(Maze(bytes([1]*25),5,5,0,24))
    short=Genome((Gene(13,2,9),))
    long=Genome((Gene(0,12,11),)*60+short.genes)
    a=evaluate(Individual('a',short,None,0),[case],'local',Limits())
    b=evaluate(Individual('b',long,None,0),[case],'local',Limits())
    assert a.fitness==b.fitness and a.work<b.work


def test_new_test_namespace_excludes_previous_input_hashes():
    from maze_evolution.range_study import StudyData
    old=make_case(836,'test',0,0,9,'perfect')
    data=StudyData(836,[old.maze.digest])
    fresh=data.case('test',0,0,9,'perfect')
    assert fresh.maze.digest!=old.maze.digest
