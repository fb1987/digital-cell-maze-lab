"""Correctness tests, deliberately independent of timing results."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from cellular_maze_lab import (
    bfs, compiled_bfs, create_maze, encode_grid, retract_cell,
    verify_path, wave_cell,
)


@pytest.mark.parametrize("family", ["random", "perfect", "comb", "snake"])
@pytest.mark.parametrize("n", [9, 17, 33])
def test_bfs_and_wave_return_shortest_path(family, n):
    for seed in [7, 97]:
        grid, start, goal = create_maze(n, family, seed)
        reference = bfs(grid, n, n, start, goal)
        assert reference
        wave = wave_cell(grid, n, n, start, goal)
        assert verify_path(wave, grid, n, n, start, goal, len(reference))
        assert len(wave) == len(reference)


@pytest.mark.parametrize("n", [9, 17, 33])
def test_tree_pruning_leaves_exactly_unique_path(n):
    for seed in [11, 29, 101]:
        grid, start, goal = create_maze(n, "perfect", seed)
        solution = bfs(grid, n, n, start, goal)
        survivors, rounds = retract_cell(grid, n, n, start, goal)
        assert rounds >= 0
        assert survivors == sum(1 << p for p in solution)


def test_pruning_is_not_a_shortest_path_solver_on_cycles():
    # Open 3x3 square has multiple routes and cycles.
    n = 3
    grid = bytes([1] * 9)
    start, goal = 0, 8
    optimal = bfs(grid, n, n, start, goal)
    survivors, _ = retract_cell(grid, n, n, start, goal)
    assert len(optimal) == 5
    assert survivors != sum(1 << p for p in optimal)


def test_unreachable_has_no_bfs_or_wave_route():
    n = 5
    grid = bytearray(25)
    grid[0] = 1
    grid[24] = 1
    assert bfs(grid, n, n, 0, 24) == []
    assert wave_cell(grid, n, n, 0, 24) == []


def test_grid_pack_and_start_equals_goal():
    n = 5
    grid = bytes([1] * 25)
    packed = encode_grid(grid)
    assert packed.bit_count() == 25
    assert bfs(grid, n, n, 12, 12) == [12]
    assert wave_cell(grid, n, n, 12, 12) == [12]


@pytest.mark.parametrize("start,goal,blocked", [(0, 3, 0), (0, 3, 3), (0, 0, 0)])
def test_blocked_endpoints_have_no_route(start, goal, blocked):
    grid = bytearray([1] * 4)
    grid[blocked] = 0
    grid = bytes(grid)
    assert bfs(grid, 2, 2, start, goal) == []
    assert wave_cell(grid, 2, 2, start, goal) == []
    assert retract_cell(grid, 2, 2, start, goal) == (0, 0)
    if compiled_bfs is not None:
        path = compiled_bfs(np.frombuffer(grid, dtype=np.uint8), 2, 2, start, goal)
        assert path.size == 0


@pytest.mark.skipif(compiled_bfs is None, reason="Numba optional")
def test_numba_baseline_matches_reference():
    n = 17
    grid, start, goal = create_maze(n, "random", 404)
    shortest = bfs(grid, n, n, start, goal)
    compiled = compiled_bfs(np.frombuffer(grid, dtype=np.uint8), n, n, start, goal)
    assert verify_path(compiled, grid, n, n, start, goal, len(shortest))
