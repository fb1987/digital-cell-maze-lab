"""V12E training keeps V12C tasks; new final bands separate two-edge retention."""
from dataclasses import replace
import gzip
import json
import random

from cellular_maze_lab import neighbors
from .datasets import make_case, seed_for
from .evaluator import Oracle, distances
from .foundation_calibration import ROOT
from .foundation_continuation_data import exclusions as previous_exclusions, borrowed_validation
from .foundation_data import FoundationData, Group, layout_hash, transform_maze, transform_point
from .goal_data import GoalPair
from .goal_recovery import wilson_case

SEED = 2026101817
CONSTRUCTION_SEED = 1194
PARENT = ROOT / 'results/foundation_continuation'
FIXTURES = ROOT / 'results/foundation_pair_fixtures'
EXTRA_MANIFESTS = (PARENT / 'mazes.json.gz', PARENT / 'confirmation/mazes.json.gz',
                   PARENT / 'confirmation/general_mazes.json.gz', FIXTURES / 'mazes.json.gz')
# min/max route, min/max common prefix, minimum remaining tail at fork.
BANDS = ((1, 1, 0, 0, 1), (2, 2, 0, 1, 1), (3, 4, 0, 2, 1),
         (5, 8, 1, 3, 2), (9, 16, 2, 6, 3))


def exclusions(include_fixtures=True):
    rows = previous_exclusions()
    for path in EXTRA_MANIFESTS:
        if path == FIXTURES / 'mazes.json.gz' and not include_fixtures:
            continue
        with gzip.open(path, 'rt') as f:
            rows.extend(json.load(f))
    return rows


def environments(previous=None, saved_keys=None):
    data = borrowed_validation(FoundationData(SEED, exclusions() if previous is None else previous))
    if saved_keys is not None:
        for key in saved_keys:
            if key[3] == -1:
                data.disconnected_group(key[0], key[1], key[2], key[5])
            else:
                data.group(*key)
        assert list(map(list, data.groups)) == saved_keys
    return data


def band_decision(pair, band):
    a, b = pair.cases
    low, high, prefix_low, prefix_high, tail = BANDS[band]
    if not all(o.path and low <= len(o.path) - 1 <= high for o in pair.cases):
        return None
    m = a.maze
    for k, (vertex, other) in enumerate(zip(a.path, b.path)):
        if vertex != other:
            break
        if not prefix_low <= k <= prefix_high or vertex in (m.goal, b.maze.goal):
            continue
        incoming = a.path[k - 1] if k else None
        exits = [q for q in neighbors(vertex, m.w, m.h) if m.cells[q] and q != incoming]
        allowed = [[q for q in exits if o.to_goal[q] == o.to_goal[vertex] - 1] for o in pair.cases]
        if (all(allowed) and not set(allowed[0]) & set(allowed[1])
                and all(o.to_goal[vertex] >= tail for o in pair.cases)):
            return dict(vertex=vertex, prefix=a.path[:k + 1], incoming=incoming, exits=exits,
                        allowed=allowed, distance=k)
    return None


class ConfirmationData(FoundationData):
    def group(self, split, replicate, index, level, family='perfect', n=9):
        if level not in range(5) or family not in ('perfect', 'random'):
            raise ValueError('Unknown V12E confirmation band')
        key = (split, replicate, index, level, family, n)
        if key in self.groups:
            return self.groups[key]
        low, high, *_ = BANDS[level]
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
                ds = distances(m, source)
                goals = [p for p, value in enumerate(ds) if low <= value <= high]
                rng.shuffle(goals)
                candidates = [Oracle.build(replace(m, start=source, goal=g)) for g in goals[:24]]
                for i, a in enumerate(candidates):
                    for b in candidates[i + 1:]:
                        pair = GoalPair(a, b)
                        if band_decision(pair, level) is not None:
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
            original_label = band_decision(chosen, level)
            pairs = []
            for symmetry in range(8):
                cases = []
                for label, oracle in zip(('a', 'b'), chosen.cases):
                    original = replace(oracle.maze, split=split, case_id=group_id + '/' + label)
                    o = Oracle.build(transform_maze(original, symmetry))
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
        raise RuntimeError(f'Could not generate independent confirmation group: {key}')
