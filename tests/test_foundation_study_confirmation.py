from dataclasses import replace
import random

import numpy as np

from maze_evolution.evaluator import Oracle, assess, distances
from maze_evolution.foundation_calibration import fixtures
from maze_evolution.foundation_fitness import correct_exit
from maze_evolution.foundation_study_confirm import rectangular_transform, normal_row
from maze_evolution.foundation_study_verify_core import Checker
from maze_evolution.runtime import Reaction, STATUSES


def test_independent_grader_matches_python_across_masks_statuses_and_endpoints():
    data = fixtures()
    cases = list(data.cache.values())[::11]
    cases.append(Oracle.build(replace(cases[0].maze, goal=cases[0].maze.start, case_id='same-endpoint')))
    checker = Checker({o.maze.case_id: o for o in cases})
    rng = np.random.default_rng(1215)
    for o in cases:
        route = np.zeros(len(o.maze.cells), np.uint8)
        route[o.path] = 1
        masks = [route, route * 0, np.frombuffer(o.maze.cells, np.uint8)]
        endpoint = route * 0
        endpoint[o.maze.goal] = 1
        masks.append(endpoint)
        for density in (.01, .1, .5, .9):
            masks.append((rng.random(len(route)) < density).astype(np.uint8))
        for mask in masks:
            for status in STATUSES:
                reaction = Reaction(mask, status, 2, 3, 4, 5)
                row = normal_row(reaction, o)
                row['old_partial'] = assess(reaction, o).partial
                side = int('/b/' in o.maze.case_id)
                row['correct_exit'] = bool(correct_exit(mask, o, side))
                checker.row(row, side)
    assert checker.rasters == len(cases) * 8 * 6


def test_rectangle_transform_preserves_distances_and_routes():
    o = next(iter(fixtures().cache.values()))
    # Crop a known excluded fixture's wall row; no fresh maze is generated.
    m = replace(o.maze, cells=o.maze.cells[:-o.maze.w], h=o.maze.h - 1)
    assert m.start < len(m.cells) and m.goal < len(m.cells)
    for s in range(8):
        transformed = rectangular_transform(m, s)
        assert len(Oracle.build(transformed).path) == len(Oracle.build(m).path)
        assert sorted(transformed.cells) == sorted(m.cells)
        current = transformed
        for _ in range(4):
            current = rectangular_transform(current, 1)
        assert (current.cells, current.w, current.h, current.start, current.goal) == (transformed.cells, transformed.w, transformed.h, transformed.start, transformed.goal)
