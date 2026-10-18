"""Independent raster grader for V12C auditing; never used in candidate selection."""
import numpy as np
from numba import njit

from .evaluator import distances
from .runtime import STATUSES


FAILURES = ('', 'budget_exhausted', 'empty_output', 'wall_crossing', 'not_emitted',
            'missing_endpoint', 'disconnected_output', 'branch_or_cycle')


@njit(cache=True)
def grade(cells, width, start, goal, goal_distance, start_distance, oracle_length, mask, status):
    size = len(cells)
    count = 0
    wall = False
    degrees = np.zeros(size, np.int8)
    reached = np.zeros((2, size), np.uint8)
    queue = np.empty(size, np.int32)
    for p in range(size):
        if mask[p]:
            count += 1
            wall = wall or cells[p] == 0
            if p % width and mask[p - 1]:
                degrees[p] += 1
            if p % width < width - 1 and mask[p + 1]:
                degrees[p] += 1
            if p >= width and mask[p - width]:
                degrees[p] += 1
            if p + width < size and mask[p + width]:
                degrees[p] += 1
    if not count:
        no_path = oracle_length == 0 and status == 2
        return False, False, no_path, (0 if no_path else (1 if status >= 3 else 2)), 0., 0., reached[0]
    counts = np.zeros(2, np.int32)
    progress = np.zeros(2, np.float64)
    for side in range(2):
        root = start if side == 0 else goal
        ds = goal_distance if side == 0 else start_distance
        head = tail = 0
        if mask[root]:
            queue[tail] = root
            tail += 1
            reached[side, root] = 1
        while head < tail:
            p = queue[head]
            head += 1
            counts[side] += 1
            if oracle_length > 0 and ds[p] >= 0:
                progress[side] = max(progress[side], 1 - ds[p] / max(1, oracle_length - 1))
            for direction in range(4):
                q = -1
                if direction == 0 and p % width:
                    q = p - 1
                elif direction == 1 and p % width < width - 1:
                    q = p + 1
                elif direction == 2 and p >= width:
                    q = p - width
                elif direction == 3 and p + width < size:
                    q = p + width
                if q >= 0 and mask[q] and not reached[side, q]:
                    reached[side, q] = 1
                    queue[tail] = q
                    tail += 1
    branches = old_branches = stray = 0
    legal_degrees = True
    for p in range(size):
        if mask[p]:
            expected = 1 if p == start or p == goal else 2
            branches += max(0, degrees[p] - expected)
            old_branches += max(0, degrees[p] - 2)
            stray += not reached[0, p] and not reached[1, p]
            legal_degrees = legal_degrees and degrees[p] == expected
    new_partial = 0.
    if oracle_length:
        value = .1 * (counts[0] > 0) + .8 * progress[0] + .1 * (counts[1] > 0) + .8 * progress[1]
        new_partial = max(0., min(.99, value / (2 * (1 + 2 * branches)) - .2 * stray / size))
    old_partial = max(0., min(.99, (.1 * (mask[start] > 0) + .8 * progress[0]) / (1 + 2 * old_branches)
                               - .2 * (count - counts[0]) / size))
    if wall:
        return False, False, False, 3, 0., 0., reached[0]
    failure = 0
    if status != 0:
        failure = 1 if status >= 3 else 4
    elif not mask[start] or not mask[goal]:
        failure = 5
    elif counts[0] != count:
        failure = 6
    elif not ((start == goal and count == 1) or (start != goal and legal_degrees)):
        failure = 7
    valid = failure == 0
    return valid, valid and oracle_length > 0 and count == oracle_length, False, failure, new_partial, (0. if valid else old_partial), reached[0]


class Checker:
    def __init__(self, cases):
        self.cases = cases
        self.prepared = {}
        self.rasters = 0

    def row(self, row, side=None):
        oracle = self.cases[row['case']]
        m = oracle.maze
        if row['case'] not in self.prepared:
            self.prepared[row['case']] = (np.frombuffer(m.cells, np.uint8), m.w, m.start, m.goal,
                np.asarray(oracle.to_goal, np.int32), np.asarray(distances(m, m.start), np.int32), len(oracle.path))
        raw = bytes.fromhex(row['mask'])
        assert len(raw) == (len(m.cells) + 7) // 8
        mask = np.unpackbits(np.frombuffer(raw, np.uint8), bitorder='little')[:len(m.cells)]
        valid, optimal, no_path, failure, score, old_score, reached = grade(*self.prepared[row['case']], mask, STATUSES.index(row['status']))
        assert (bool(valid), bool(optimal), bool(no_path), FAILURES[failure]) == (row['valid'], row['optimal'], row['no_path'], row['failure'])
        assert abs(score - row['partial']) < 1e-10
        assert row['reachable'] == bool(oracle.path)
        if 'old_partial' in row:
            assert abs(old_score - row['old_partial']) < 1e-10
        if 'correct_exit' in row:
            label = getattr(oracle, '_foundation_label', None)
            correct = False
            if label is not None:
                allowed = set(label['allowed'][side])
                correct = (bool(reached[label['vertex']]) and sum(mask[p] > 0 for p in allowed) == 1
                           and all(not mask[p] for p in set(label['exits']) - allowed))
            assert row['correct_exit'] == correct
        self.rasters += 1
        return mask

    def rows(self, rows, verify_masks=True):
        if verify_masks:
            for index, row in enumerate(rows):
                self.row(row, index % 2)
        for i in range(0, len(rows), 2):
            a, b = rows[i:i + 2]
            assert all(r['pair_valid'] == (a['valid'] and b['valid']) for r in (a, b))
            assert all(r['pair_optimal'] == (a['optimal'] and b['optimal']) for r in (a, b))
            assert all(abs(r['paired_partial'] - min(a['partial'], b['partial'])) < 1e-10 for r in (a, b))
        work = sum(r['reads'] + r['dispatches'] for r in rows)
        complete = all(r['valid'] or r['no_path'] for r in rows)
        fitness = (sum(r['valid'] for r in rows), sum(r['optimal'] for r in rows),
            sum(r['no_path'] for r in rows) - sum(r['reachable'] and r['status'] == 'no_path' for r in rows),
            sum(r['pair_optimal'] for r in rows) // 2,
            round(sum(r['partial'] + r['paired_partial'] for r in rows), 8), -work if complete else 0)
        return fitness, work
