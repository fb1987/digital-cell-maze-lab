"""V12 small paired tasks and D4 orbits; all graph oracles stay outside inference."""
from dataclasses import dataclass, replace
import gzip
import hashlib
import json
import random
from pathlib import Path

from cellular_maze_lab import neighbors
from .datasets import make_case, seed_for, manifest
from .evaluator import Maze, Oracle, distances
from .goal_data import GoalPair, layout_hash
from .goal_recovery import wilson_case
from .growth_data import prior_manifests as earlier_manifests


def prior_hashes(root):
    names = ('first_evolution', 'range_and_regulation', 'source_pressure', 'goal_conditioning',
             'factor_curriculum', 'goal_beacon', 'balanced_goal', 'junction_choice',
             'junction_confirmation', 'choice_priority', 'distance_curriculum',
             'distance_confirmation', 'capacity_growth')
    result = {}
    for name in names:
        path = root / 'results' / name / ('mazes.json' if name == 'first_evolution' else 'mazes.json.gz')
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def prior_manifests(root, extra=()):
    rows = earlier_manifests(root)
    for path in [root / 'results/capacity_growth/mazes.json.gz', *extra]:
        path = Path(path)
        with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as f:
            rows.extend(json.load(f))
    return rows


def transform_point(p, n, symmetry):
    if not 0 <= symmetry < 8:
        raise ValueError('Expected one of eight square symmetries')
    y, x = divmod(p, n)
    if symmetry >= 4:
        x = n - 1 - x
    for _ in range(symmetry % 4):
        x, y = n - 1 - y, x
    return y * n + x


def transform_maze(m, symmetry):
    if m.w != m.h:
        raise ValueError('Square D4 fixture required')
    cells = bytearray(len(m.cells))
    for p, value in enumerate(m.cells):
        cells[transform_point(p, m.w, symmetry)] = value
    return replace(m, cells=bytes(cells), start=transform_point(m.start, m.w, symmetry),
                   goal=transform_point(m.goal, m.w, symmetry), case_id=m.case_id + f'/d4-{symmetry}')


# (source-goal minimum, maximum, common prefix minimum, maximum, goal tail minimum)
LEVELS = ((1, 1, 0, 0, 1), (2, 4, 0, 1, 1), (4, 8, 1, 3, 2), (8, 16, 2, 6, 3))


def decision(pair, level=None):
    a, b = pair.cases
    if not a.path or not b.path:
        return None
    m = a.maze
    low, high, prefix_low, prefix_high, tail = LEVELS[level] if level is not None else (1, 100000, 0, 100000, 1)
    if not all(low <= len(o.path) - 1 <= high for o in pair.cases):
        return None
    for k, (v, other) in enumerate(zip(a.path, b.path)):
        if v != other:
            break
        if not prefix_low <= k <= prefix_high or v in (m.goal, b.maze.goal):
            continue
        incoming = a.path[k - 1] if k else None
        exits = [q for q in neighbors(v, m.w, m.h) if m.cells[q] and q != incoming]
        allowed = [[q for q in exits if o.to_goal[q] == o.to_goal[v] - 1] for o in pair.cases]
        if (all(allowed) and not set(allowed[0]) & set(allowed[1])
                and all(o.to_goal[v] >= tail for o in pair.cases)):
            return dict(vertex=v, prefix=a.path[:k + 1], incoming=incoming, exits=exits,
                        allowed=allowed, distance=k)
    return None


@dataclass
class Group:
    identity: str
    level: int
    pairs: tuple
    key: tuple = ()


class FoundationData:
    def __init__(self, seed, previous=()):
        self.seed = seed
        self.layouts = {layout_hash(Maze(bytes.fromhex(r['cells_hex']), r['w'], r['h'], r['start'], r['goal']))
                        for r in previous}
        self.previous_count = len(self.layouts)
        self.groups = {}
        self.cache = {}
        self.rejections = 0

    def group(self, split, replicate, index, level, family='perfect', n=9):
        if level not in range(4) or family not in ('perfect', 'random'):
            raise ValueError('Unknown elementary task')
        key = (split, replicate, index, level, family, n)
        if key in self.groups:
            return self.groups[key]
        low, high, *_ = LEVELS[level]
        namespace = f'{split}/level{level}/{family}/{n}'
        for salt in range(4000):
            serial = index * 10000 + salt
            base = (wilson_case(self.seed, namespace, replicate, serial) if n == 9 and family == 'perfect'
                    else make_case(self.seed, namespace, replicate, serial, n, family))
            m = base.maze
            orbit = {layout_hash(transform_maze(m, s)) for s in range(8)}
            if orbit & self.layouts:
                self.rejections += 1
                continue
            rng = random.Random(seed_for(self.seed, namespace + '/endpoints', replicate, serial))
            sources = [p for p, value in enumerate(m.cells) if value]
            rng.shuffle(sources)
            chosen = None
            for source in sources[:24]:
                d = distances(m, source)
                goals = [p for p, value in enumerate(d) if low <= value <= high]
                rng.shuffle(goals)
                candidates = [Oracle.build(replace(m, start=source, goal=g)) for g in goals[:24]]
                for i, a in enumerate(candidates):
                    for b in candidates[i + 1:]:
                        pair = GoalPair(a, b)
                        if decision(pair, level) is not None:
                            chosen = pair
                            break
                    if chosen:
                        break
                if chosen:
                    break
            if chosen is None:
                self.rejections += 1
                continue
            group_id = f'{namespace}/r{replicate}/g{index}/s{salt}'
            pairs = []
            original_label = decision(chosen, level)
            for symmetry in range(8):
                cases = []
                for label, oracle in zip(('a', 'b'), chosen.cases):
                    original = replace(oracle.maze, split=split, case_id=group_id + '/' + label)
                    o = Oracle.build(transform_maze(original, symmetry))
                    # Transform the anchor as well; do not let BFS tie order change it.
                    conv = lambda p: transform_point(p, n, symmetry)
                    o._foundation_label = dict(vertex=conv(original_label['vertex']),
                        prefix=[conv(p) for p in original_label['prefix']],
                        incoming=None if original_label['incoming'] is None else conv(original_label['incoming']),
                        exits=[conv(p) for p in original_label['exits']],
                        allowed=[[conv(p) for p in xs] for xs in original_label['allowed']],
                        distance=original_label['distance'])
                    o._from_start = distances(o.maze, o.maze.start)
                    self.cache[o.maze.case_id] = o
                    cases.append(o)
                pairs.append(GoalPair(*cases))
            self.layouts.update(orbit)
            group = Group(group_id, level, tuple(pairs), key)
            self.groups[key] = group
            return group
        raise RuntimeError(f'Could not generate independent elementary group: {key}')

    def disconnected_group(self, split, replicate, index, n=9):
        key = (split, replicate, index, -1, 'disconnected', n)
        if key in self.groups:
            return self.groups[key]
        for salt in range(4000):
            serial = index * 10000 + salt
            m = make_case(self.seed, split + '/disconnected', replicate, serial, n, 'disconnected').maze
            orbit = {layout_hash(transform_maze(m, s)) for s in range(8)}
            if orbit & self.layouts:
                self.rejections += 1
                continue
            rng = random.Random(seed_for(self.seed, split + '/mixed-endpoints', replicate, serial))
            left = [p for p, value in enumerate(m.cells) if value and p % n < n // 2]
            source = rng.choice(left)
            d = distances(m, source)
            reachable = [p for p, value in enumerate(d) if 1 <= value <= 16]
            unreachable = [p for p, value in enumerate(d) if value < 0 and m.cells[p]]
            if not reachable or not unreachable:
                continue
            goals = [rng.choice(reachable), rng.choice(unreachable)]
            group_id = f'{split}/disconnected/{n}/r{replicate}/g{index}/s{salt}'
            pairs = []
            for symmetry in range(8):
                cases = []
                for label, goal in zip(('a', 'b'), goals):
                    original = replace(m, start=source, goal=goal, split=split, case_id=group_id + '/' + label)
                    o = Oracle.build(transform_maze(original, symmetry))
                    o._foundation_label = None
                    o._from_start = distances(o.maze, o.maze.start)
                    self.cache[o.maze.case_id] = o
                    cases.append(o)
                pairs.append(GoalPair(*cases, mixed=True))
            self.layouts.update(orbit)
            self.groups[key] = Group(group_id, -1, tuple(pairs), key)
            return self.groups[key]
        raise RuntimeError('Could not generate independent disconnected group')

    def save(self, out):
        out = Path(out)
        with gzip.open(out / 'mazes.json.gz', 'wt') as f:
            json.dump(manifest(self.cache.values()), f, separators=(',', ':'))
        groups = [dict(id=g.identity, level=g.level, key=g.key, pairs=[dict(first=p.first.maze.case_id,
            second=p.second.maze.case_id, decision=p.first._foundation_label) for p in g.pairs])
            for g in self.groups.values()]
        (out / 'groups.json').write_text(json.dumps(groups, separators=(',', ':')) + '\n')

    @classmethod
    def restore(cls, seed, out, previous=()):
        data = cls(seed, previous)
        data.cache, groups = load_pairs(out)
        for group in groups:
            orbit = {layout_hash(p.first.maze) for p in group.pairs}
            if orbit & data.layouts:
                raise ValueError('Restored groups overlap excluded layouts or another group')
            data.layouts.update(orbit)
            data.groups[group.key] = group
        return data


def load_pairs(out):
    out = Path(out)
    with gzip.open(out / 'mazes.json.gz', 'rt') as f:
        manifest_rows = json.load(f)
    cases = {}
    for m in manifest_rows:
        o = Oracle.build(Maze(bytes.fromhex(m['cells_hex']), m['w'], m['h'], m['start'], m['goal'],
                              m['family'], m['seed'], m['split'], m['case_id']))
        o._from_start = distances(o.maze, o.maze.start)
        cases[m['case_id']] = o
    groups = []
    for g in json.loads((out / 'groups.json').read_text()):
        pairs = []
        for p in g['pairs']:
            a, b = cases[p['first']], cases[p['second']]
            a._foundation_label = b._foundation_label = p['decision']
            pairs.append(GoalPair(a, b, mixed=not (a.path and b.path)))
        groups.append(Group(g['id'], g['level'], tuple(pairs), tuple(g['key'])))
    return cases, groups
