import ast
from pathlib import Path
import random

import numpy as np
import pytest

from maze_evolution.baselines import baseline
from maze_evolution.datasets import make_case, check_split_overlap
from maze_evolution.evaluator import Maze, Oracle, assess, score
from maze_evolution.genome import Gene, Genome, Op, mutate, random_genome, wavefront_genome
from maze_evolution.runtime import Limits, Organism, Reaction


def test_genome_validation_and_portable_mutation():
    with pytest.raises(ValueError):
        Gene(99, 8)
    with pytest.raises(ValueError):
        Gene(Op.COPY, 0, 1)  # Frozen registers cannot be overwritten.
    with pytest.raises(ValueError):
        Genome((Gene(Op.COPY, 8, 0),) * 33)
    rng = random.Random(101)
    genome = random_genome(rng)
    original = genome.digest
    for _ in range(100):
        genome = mutate(genome, rng, 3)
        assert genome == Genome.from_dict(genome.to_dict())
        assert genome.array().nbytes <= 1024
    assert original == random_genome(random.Random(101)).digest


@pytest.mark.parametrize('family', ['perfect', 'random', 'snake', 'comb'])
@pytest.mark.parametrize('n', [9, 17])
def test_seed_solves_without_reference_calls(family, n, monkeypatch):
    oracle = make_case(701, 'unit', 0, n, n, family)
    # Explicitly give the stress corridors enough reads; default-limit failures
    # are assessed separately rather than changing experiment limits silently.
    organism = Organism(wavefront_genome(), Limits(reads_per_site=8192))
    def forbidden(*args, **kwargs):
        raise AssertionError('Oracle called during inference')
    monkeypatch.setattr('cellular_maze_lab.bfs', forbidden)
    monkeypatch.setattr('cellular_maze_lab.wave_cell', forbidden)
    maze = oracle.maze
    reaction = organism.react(maze.cells, maze.w, maze.h, maze.start, maze.goal)
    assessment = assess(reaction, oracle)
    assert assessment.valid_path and assessment.optimal
    assert reaction.array_bytes <= 64 * n * n + 65536


def test_synchronous_reads_do_not_chain_within_tick_or_wrap():
    # Copy west D into D; doing it twice still moves the stimulus only one cell.
    genome = Genome((Gene(Op.NEIGHBOR, 8, 0, 0), Gene(Op.STORE, 0, 8),
                     Gene(Op.NEIGHBOR, 9, 0, 0), Gene(Op.STORE, 2, 9)))
    organism = Organism(genome, Limits(max_steps=1))
    result = organism.react(bytes([1] * 6), 3, 2, 2, 5)
    assert not result.mask.any()  # Site 3 is not site 2's east neighbour.
    result = organism.react(bytes([1] * 6), 6, 1, 0, 5)
    assert np.flatnonzero(result.mask).tolist() == [1]
    assert result.status == 'step_budget'


def test_no_path_blocked_endpoints_start_equals_goal_and_rectangles():
    organism = Organism(wavefront_genome())
    for maze in (Maze(bytes([1, 0, 1]), 3, 1, 0, 2),
                 Maze(bytes([0, 1]), 2, 1, 0, 1),
                 Maze(bytes([1] * 15), 5, 3, 7, 7),
                 Maze(bytes([1] * 15), 5, 3, 0, 14)):
        oracle = Oracle.build(maze)
        reaction = organism.react(maze.cells, maze.w, maze.h, maze.start, maze.goal)
        result = assess(reaction, oracle)
        assert result.optimal if oracle.path else result.no_path_correct


def test_validator_rejects_full_grid_islands_and_malformed_outputs():
    maze = Maze(bytes([1] * 9), 3, 3, 0, 8)
    oracle = Oracle.build(maze)
    for mask in (np.ones(9), np.array([1, 0, 0, 0, 0, 0, 0, 0, 1]),
                 np.array([2] * 9), np.ones((3, 3))):
        result = assess(Reaction(mask, 'emitted', 1, 0, 0, 0), oracle)
        assert not result.valid_path
    # An alternative shortest path is accepted; no equality to oracle raster.
    mask = np.zeros(9, dtype=np.uint8)
    mask[[0, 3, 6, 7, 8]] = 1
    assert assess(Reaction(mask, 'emitted', 1, 0, 0, 0), oracle).optimal
    source_only = np.zeros(9, dtype=np.uint8)
    source_only[0] = 1
    filament = assess(Reaction(source_only, 'quiescent', 1, 0, 0, 0), oracle)
    full = assess(Reaction(np.ones(9), 'emitted', 1, 0, 0, 0), oracle)
    assert filament.partial > full.partial


def test_timeout_is_not_a_no_path_answer_and_limits_are_hard():
    oracle = Oracle.build(Maze(bytes([1, 0, 1]), 3, 1, 0, 2))
    reaction = Reaction(np.zeros(3), 'step_budget', 1, 0, 0, 0)
    assert not assess(reaction, oracle).no_path_correct
    organism = Organism(wavefront_genome(), Limits(reads_per_site=1))
    reaction = organism.react(bytes([1] * 25), 5, 5, 0, 24)
    assert reaction.status == 'read_budget' and reaction.spatial_reads <= 25
    with pytest.raises(ValueError):
        Limits(max_steps=1000000)
    with pytest.raises(ValueError):
        organism.react(bytes([1, 2]), 2, 1, 0, 1)


@pytest.mark.parametrize('name', ['compiled_bfs', 'compiled_astar', 'wave_bit'])
def test_normalized_baselines(name):
    for i, family in enumerate(('random', 'perfect', 'disconnected', 'rectangular')):
        oracle = make_case(202, 'unit', 0, i, 9, family)
        maze = oracle.maze
        result = assess(baseline(name, maze.cells, maze.w, maze.h, maze.start, maze.goal), oracle)
        assert result.optimal if oracle.path else result.no_path_correct


def test_seed_split_overlap_is_rejected():
    oracle = make_case(202, 'train', 0, 1, 9, 'perfect')
    with pytest.raises(ValueError):
        check_split_overlap({'train': [oracle], 'test': [oracle]})


def test_runtime_has_no_evaluator_dependency_or_dynamic_execution():
    tree = ast.parse((Path(__file__).parents[1] / 'maze_evolution/runtime.py').read_text())
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any(name and ('evaluator' in name or 'cellular_maze_lab' in name) for name in imports)
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id in ('exec', 'eval', 'compile') for node in ast.walk(tree))


def test_evolution_replays_deterministically_and_freezes_controls():
    from io import StringIO
    from dataclasses import asdict
    from maze_evolution.experiment import evolve
    from maze_evolution.datasets import training_batches, validation_set
    config = dict(seed=503, population=4, limits=asdict(Limits()))
    batches, validation = training_batches(503, 0, 2), validation_set(503, 0)
    outputs = []
    for _ in range(2):
        registry, evaluations, history = StringIO(), StringIO(), []
        champions = evolve('seeded', 0, batches, validation, config, (registry, evaluations, history))
        assert tuple(champions['evolved']['validation_fitness']) >= tuple(champions['frozen']['validation_fitness'])
        assert champions['frozen']['digest'] in champions['evolved']['initial_digests']
        outputs.append((champions, history, registry.getvalue(), evaluations.getvalue()))
    assert outputs[0] == outputs[1]
