"""V12F construction-only sampling; labels never enter candidate inference."""
from dataclasses import replace
import gzip
import json
import random
from pathlib import Path

from cellular_maze_lab import neighbors
from .datasets import seed_for
from .evaluator import Maze, Oracle, distances
from .foundation_data import FoundationData, Group, layout_hash, transform_maze, transform_point
from .foundation_pair_data import exclusions as earlier_exclusions
from .foundation_calibration import ROOT
from .goal_data import GoalPair

SEED = 2026101901
CONSTRUCTION_SEED = 1204
BANDS = ((4, 8, 1, 17), (9, 16, 2, 17), (17, 32, 3, 33))
OUT = ROOT / 'results/route_confirmation'
FIXTURES = ROOT / 'results/route_confirmation_fixtures'


def exclusions():
    rows = earlier_exclusions()
    for relative in ('mazes.json.gz', 'confirmation/mazes.json.gz', 'confirmation/general_mazes.json.gz'):
        with gzip.open(ROOT / 'results/foundation_pair' / relative, 'rt') as f:
            rows.extend(json.load(f))
    return rows


def rim_distance(p, n):
    return min(p % n, p // n, n - 1 - p % n, n - 1 - p // n)


def make_layout(seed, namespace, serial, n, family):
    """Wilson trees, or independent p(open)=.72 obstacle grids; closed outer rim."""
    actual = seed_for(seed, namespace, 0, serial)
    rng = random.Random(actual)
    cells = bytearray(n * n)
    if family == 'tree':
        side = (n - 1) // 2
        tree = {rng.randrange(side * side)}
        edges = []
        while len(tree) < side * side:
            path = [next(p for p in range(side * side) if p not in tree)]
            positions = {path[0]: 0}
            while path[-1] not in tree:
                q = rng.choice(list(neighbors(path[-1], side, side)))
                if q in positions:
                    path = path[:positions[q] + 1]
                    positions = {p: i for i, p in enumerate(path)}
                else:
                    positions[q] = len(path)
                    path.append(q)
            edges.extend(zip(path, path[1:]))
            tree.update(path)
        pixel = lambda p: (2 * (p // side) + 1) * n + 2 * (p % side) + 1
        for p in tree:
            cells[pixel(p)] = 1
        for a, b in edges:
            cells[(pixel(a) + pixel(b)) // 2] = 1
    elif family == 'cyclic':
        for y in range(1, n - 1):
            for x in range(1, n - 1):
                cells[y * n + x] = int(rng.random() < .72)
    else:
        raise ValueError(family)
    return Maze(bytes(cells), n, n, n + 1, n + 1, family, actual, namespace, namespace)


def minimum_turns(m, ds):
    """Minimum turns across ALL shortest paths, via the distance DAG."""
    cost = [[100000] * 4 for _ in m.cells]
    result = [100000] * len(ds)
    cost[m.start] = [0] * 4
    result[m.start] = 0
    for p in sorted((p for p, d in enumerate(ds) if d >= 0), key=ds.__getitem__):
        for q in neighbors(p, m.w, m.h):
            if ds[q] != ds[p] + 1:
                continue
            direction = (0 if q == p - 1 else 1 if q == p + 1 else 2 if q == p - m.w else 3)
            cost[q][direction] = min(cost[q][direction], min(v + int(k != direction) for k, v in enumerate(cost[p])))
            result[q] = min(cost[q])
    return result


def cycle_rank(m, ds):
    vertices = sum(d >= 0 for d in ds)
    edges = sum(sum(ds[q] >= 0 for q in neighbors(p, m.w, m.h)) for p, d in enumerate(ds) if d >= 0) // 2
    return edges - vertices + 1


def manhattan(p, q, n):
    return abs(p % n - q % n) + abs(p // n - q // n)


def label_pair(a, b, misleading):
    m = a.maze
    for k, (vertex, other) in enumerate(zip(a.path, b.path)):
        if vertex != other:
            break
        if not 1 <= k <= 6 or vertex in (m.goal, b.maze.goal):
            continue
        incoming = a.path[k - 1]
        exits = [q for q in neighbors(vertex, m.w, m.h) if m.cells[q] and q != incoming]
        allowed = [[q for q in exits if o.to_goal[q] == o.to_goal[vertex] - 1] for o in (a, b)]
        if not all(allowed) or set(allowed[0]) & set(allowed[1]) or min(a.to_goal[vertex], b.to_goal[vertex]) < 2:
            continue
        away = [all(manhattan(q, o.maze.goal, m.w) > manhattan(vertex, o.maze.goal, m.w) for q in xs)
                for o, xs in zip((a, b), allowed)]
        if any(away) != misleading:
            continue
        return dict(vertex=vertex, prefix=a.path[:k + 1], incoming=incoming, exits=exits,
                    allowed=allowed, distance=k, misleading=away)
    return None


class RouteData(FoundationData):
    def group(self, split, index, band, family, placement, misleading):
        key = (split, index, band, family, placement, misleading)
        if key in self.groups:
            return self.groups[key]
        low, high, turns, n = BANDS[band]
        namespace = f'{split}/{family}/band{band}/{placement}/away{int(misleading)}'
        for salt in range(2000):
            serial = index * 10000 + salt
            m = make_layout(self.seed, namespace, serial, n, family)
            orbit = {layout_hash(transform_maze(m, s)) for s in range(8)}
            if orbit & self.layouts:
                self.rejections += 1
                continue
            rng = random.Random(seed_for(self.seed, namespace + '/endpoints', 0, serial))
            sources = [p for p, v in enumerate(m.cells) if v and
                       (rim_distance(p, n) == 1 if placement == 'rim_source' else rim_distance(p, n) >= 3)]
            rng.shuffle(sources)
            chosen = None
            for source in sources[:32]:
                sm = replace(m, start=source)
                ds = distances(sm, source)
                rank = cycle_rank(sm, ds)
                if (family == 'tree' and rank != 0) or (family == 'cyclic' and rank < 1):
                    continue
                mt = minimum_turns(sm, ds)
                goals = [p for p, d in enumerate(ds) if low <= d <= high and mt[p] >= turns and
                         (placement == 'rim_source' or rim_distance(p, n) >= 3)]
                rng.shuffle(goals)
                candidates = [Oracle.build(replace(sm, goal=g)) for g in goals[:32]]
                for i, a in enumerate(candidates):
                    for b in candidates[i + 1:]:
                        label = label_pair(a, b, misleading)
                        if label is not None:
                            chosen = (a, b, label, rank, [mt[a.maze.goal], mt[b.maze.goal]])
                            break
                    if chosen:
                        break
                if chosen:
                    break
            if not chosen:
                self.rejections += 1
                continue
            a, b, label, rank, min_turns = chosen
            group_id = f'{namespace}/g{index}/s{salt}'
            pairs = []
            for symmetry in range(8):
                conv = lambda p: transform_point(p, n, symmetry)
                transformed = dict(vertex=conv(label['vertex']), prefix=[conv(p) for p in label['prefix']],
                    incoming=conv(label['incoming']), exits=[conv(p) for p in label['exits']],
                    allowed=[[conv(p) for p in xs] for xs in label['allowed']], distance=label['distance'],
                    misleading=label['misleading'], min_turns=min_turns, cycle_rank=rank)
                cases = []
                for name, o in zip(('a', 'b'), (a, b)):
                    maze = transform_maze(replace(o.maze, split=split, case_id=group_id + '/' + name), symmetry)
                    current = Oracle.build(maze)
                    current._foundation_label = transformed
                    current._from_start = distances(maze, maze.start)
                    self.cache[maze.case_id] = current
                    cases.append(current)
                pairs.append(GoalPair(*cases))
            group = Group(group_id, band, tuple(pairs), key)
            self.groups[key] = group
            self.layouts.update(orbit)
            return group
        raise RuntimeError(f'Construction exhausted without candidate inference: {key}')

    def matrix(self, split, per_cell):
        for band in range(3):
            for family in ('tree', 'cyclic'):
                for placement in ('rim_source', 'interior'):
                    for misleading in (False, True):
                        for index in range(per_cell):
                            self.group(split, index, band, family, placement, misleading)
        return self

    def disconnected(self, split, index):
        key = (split, index, -1, 'disconnected', 'interior', False)
        n = 17
        namespace = f'{split}/disconnected'
        for salt in range(2000):
            serial = index * 10000 + salt
            m = make_layout(self.seed, namespace, serial, n, 'cyclic')
            cells = bytearray(m.cells)
            for y in range(n):
                cells[y*n+n//2] = 0
            m = replace(m, cells=bytes(cells), family='disconnected')
            orbit = {layout_hash(transform_maze(m, s)) for s in range(8)}
            if orbit & self.layouts:
                continue
            rng = random.Random(seed_for(self.seed, namespace + '/endpoints', 0, serial))
            left = [p for p, v in enumerate(m.cells) if v and rim_distance(p, n) >= 3 and p % n < n//2]
            right = [p for p, v in enumerate(m.cells) if v and rim_distance(p, n) >= 3 and p % n > n//2]
            if not left or len(right) < 2:
                continue
            start = rng.choice(left)
            goals = rng.sample(right, 2)
            group_id = f'{namespace}/g{index}/s{salt}'
            pairs = []
            for symmetry in range(8):
                cases = []
                for name, goal in zip(('a', 'b'), goals):
                    current = Oracle.build(transform_maze(replace(m, start=start, goal=goal,
                        split=split, case_id=group_id+'/'+name), symmetry))
                    assert not current.path
                    current._foundation_label = None
                    current._from_start = distances(current.maze, current.maze.start)
                    self.cache[current.maze.case_id] = current
                    cases.append(current)
                pairs.append(GoalPair(*cases, mixed=True))
            self.layouts.update(orbit)
            group = Group(group_id, -1, tuple(pairs), key)
            self.groups[key] = group
            return group
        raise RuntimeError('Cannot generate independent disconnected controls')
