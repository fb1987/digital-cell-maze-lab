"""Seed namespaces, diverse endpoints and persistable maze identities."""
import hashlib
import random

from cellular_maze_lab import bfs, create_maze
from .evaluator import Maze, Oracle, distances


def seed_for(root, split, replicate, index):
    value = f'digital-cell-v1:{root}:{split}:{replicate}:{index}'.encode()
    return int.from_bytes(hashlib.sha256(value).digest()[:8], 'little')


def make_case(root, split, replicate, index, n, family, varied_endpoints=True):
    seed = seed_for(root, split, replicate, index)
    rng = random.Random(seed)
    w = h = n
    if family == 'disconnected':
        cells = bytearray(int(rng.random() > .15) for _ in range(n * n))
        for y in range(n):
            cells[y * n + n // 2] = 0
        start, goal = 0, n * n - 1
        cells[start] = cells[goal] = 1
        cells = bytes(cells)
    elif family == 'rectangular':
        w, h = 2 * n - 1, n
        start, goal = 0, w * h - 1
        for _ in range(500):
            cells = bytearray(int(rng.random() > .24) for _ in range(w * h))
            cells[start] = cells[goal] = 1
            cells = bytes(cells)
            if bfs(cells, w, h, start, goal):
                break
        else:
            raise RuntimeError('Failed to generate rectangular maze')
    else:
        cells, start, goal = create_maze(n, family, seed)
    case_id = f'{split}/r{replicate}/{index}/{family}/{w}x{h}'
    maze = Maze(cells, w, h, start, goal, family, seed, split, case_id)
    if varied_endpoints and family in ('perfect', 'random', 'rectangular'):
        reachable = [p for p, d in enumerate(distances(maze, start)) if d >= 0]
        if len(reachable) >= 2:
            start, goal = rng.sample(reachable, 2)
            maze = Maze(cells, w, h, start, goal, family, seed, split, case_id)
    return Oracle.build(maze)


def training_batches(root, replicate, generations, batch_size=4):
    result = []
    for generation in range(generations):
        batch = []
        for i in range(batch_size):
            n = 9 if i % 4 < 2 else 17
            family = 'perfect' if i % 2 == 0 else 'random'
            if i == batch_size - 1 and generation % 4 == 3:
                family = 'disconnected'
            batch.append(make_case(root, 'train', replicate,
                                   generation * batch_size + i, n, family))
        result.append(batch)
    return result


def validation_set(root, replicate):
    specs = [(n, family) for n in (9, 17) for family in ('perfect', 'random')
             for _ in range(3)] + [(9, 'disconnected'), (17, 'disconnected')]
    return [make_case(root, 'validation', replicate, i, n, family)
            for i, (n, family) in enumerate(specs)]


def final_test_set(root, replicate, samples=8):
    specs = [(n, family) for n in (9, 17, 33, 65) for family in ('perfect', 'random')
             for _ in range(samples)]
    specs += [(n, 'disconnected') for n in (9, 17, 33, 65) for _ in range(4)]
    specs += [(n, family) for n in (9, 17, 33, 65) for family in ('snake', 'comb')]
    specs += [(n, 'rectangular') for n in (9, 17) for _ in range(4)]
    return [make_case(root, 'test', replicate, i, n, family)
            for i, (n, family) in enumerate(specs)]


def manifest(oracles):
    return [dict(case_id=o.maze.case_id, split=o.maze.split, seed=o.maze.seed,
                 family=o.maze.family, w=o.maze.w, h=o.maze.h, start=o.maze.start,
                 goal=o.maze.goal, sha256=o.maze.digest, cells_hex=o.maze.cells.hex(),
                 oracle_length=len(o.path)) for o in oracles]


def check_split_overlap(groups):
    seen = {}
    for split, oracles in groups.items():
        for oracle in oracles:
            digest = oracle.maze.digest
            if digest in seen and seen[digest] != split:
                raise ValueError(f'Maze overlaps {split} and {seen[digest]}')
            seen[digest] = split
