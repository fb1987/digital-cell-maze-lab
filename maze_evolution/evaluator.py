"""Independent oracle and strict raster validation, never imported by runtime."""
from collections import deque
from dataclasses import dataclass
import hashlib

import numpy as np

from cellular_maze_lab import bfs, neighbors
from .runtime import Reaction


@dataclass(frozen=True)
class Maze:
    cells: bytes
    w: int
    h: int
    start: int
    goal: int
    family: str = 'custom'
    seed: int = 0
    split: str = 'test'
    case_id: str = 'custom'

    def __post_init__(self):
        if (type(self.cells) is not bytes or self.w < 1 or self.h < 1
                or len(self.cells) != self.w * self.h or any(v > 1 for v in self.cells)
                or not 0 <= self.start < len(self.cells) or not 0 <= self.goal < len(self.cells)):
            raise ValueError('Malformed maze')

    @property
    def digest(self):
        header = f'{self.w},{self.h},{self.start},{self.goal}:'.encode()
        return hashlib.sha256(header + self.cells).hexdigest()


def distances(maze, source):
    result = [-1] * len(maze.cells)
    if not maze.cells[source]:
        return result
    result[source] = 0
    queue = deque([source])
    while queue:
        p = queue.popleft()
        for q in neighbors(p, maze.w, maze.h):
            if maze.cells[q] and result[q] < 0:
                result[q] = result[p] + 1
                queue.append(q)
    return result


@dataclass
class Oracle:
    maze: Maze
    path: list[int]
    to_goal: list[int]

    @classmethod
    def build(cls, maze):
        return cls(maze, bfs(maze.cells, maze.w, maze.h, maze.start, maze.goal),
                   distances(maze, maze.goal))


@dataclass
class Assessment:
    reachable: bool
    valid_path: bool
    optimal: bool
    no_path_correct: bool
    path_length: int
    oracle_length: int
    partial: float
    failure: str


def assess(result: Reaction, oracle: Oracle):
    maze = oracle.maze
    n = len(maze.cells)
    reachable = bool(oracle.path)
    mask = np.asarray(result.mask)
    def failed(reason, partial=0.):
        return Assessment(reachable, False, False, False, 0, len(oracle.path), partial, reason)
    if mask.shape != (n,) or not np.all((mask == 0) | (mask == 1)):
        return failed('malformed_raster')
    selected = set(np.flatnonzero(mask).tolist())
    if not selected:
        correct = not reachable and result.status == 'no_path'
        return Assessment(reachable, False, False, correct, 0, len(oracle.path), 0.,
                          '' if correct else ('budget_exhausted' if 'budget' in result.status else 'empty_output'))
    if any(not maze.cells[p] for p in selected):
        return failed('wall_crossing')
    component = set()
    if maze.start in selected:
        component.add(maze.start)
        queue = deque([maze.start])
        while queue:
            for q in neighbors(queue.popleft(), maze.w, maze.h):
                if q in selected and q not in component:
                    component.add(q)
                    queue.append(q)
    degrees = {p: sum(q in selected for q in neighbors(p, maze.w, maze.h)) for p in selected}
    branches = sum(max(0, degree - 2) for degree in degrees.values())
    progress = 0.
    if reachable and component:
        remaining = [oracle.to_goal[p] for p in component if oracle.to_goal[p] >= 0]
        if remaining:
            progress = 1. - min(remaining) / max(1, len(oracle.path) - 1)
    # Bounded shaping, independent of a particular oracle route or pixel overlap.
    # A full-frame activation must not beat a coherent growing filament just
    # because it touches the goal. Excess branches divide the progress reward.
    partial = max(0., (.1 * (maze.start in selected) + .8 * progress) / (1 + 2 * branches)
                  - .2 * (len(selected) - len(component)) / n)
    partial = min(.99, partial)
    if result.status != 'emitted':
        return failed('budget_exhausted' if 'budget' in result.status else 'not_emitted', partial)
    if maze.start not in selected or maze.goal not in selected:
        return failed('missing_endpoint', partial)
    if component != selected:
        return failed('disconnected_output', partial)
    if maze.start == maze.goal:
        legal = selected == {maze.start}
    else:
        legal = all(degrees[p] == (1 if p in (maze.start, maze.goal) else 2) for p in selected)
    if not legal:
        return failed('branch_or_cycle', partial)
    optimal = reachable and len(selected) == len(oracle.path)
    return Assessment(reachable, True, optimal, False, len(selected), len(oracle.path), 0., '')


def score(organism, oracles):
    assessments, reactions = [], []
    for oracle in oracles:
        maze = oracle.maze
        reaction = organism.react(maze.cells, maze.w, maze.h, maze.start, maze.goal)
        reactions.append(reaction)
        assessments.append(assess(reaction, oracle))
    # Deterministic cost: no noisy timing is used to select genomes.
    fitness = (sum(a.valid_path for a in assessments),
               sum(a.optimal for a in assessments),
               sum(a.no_path_correct for a in assessments)
               - sum(a.reachable and r.status == 'no_path'
                     for a, r in zip(assessments, reactions)),
               round(sum(a.partial for a in assessments), 8),
               -sum(r.instructions + r.spatial_reads for r in reactions))
    return fitness, assessments, reactions
