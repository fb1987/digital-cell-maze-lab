"""V12 ordinary-output fitness; no forced probe or oracle inside inference."""
from collections import deque
import numpy as np
from cellular_maze_lab import neighbors
from .evaluator import assess, distances
from .growth_runtime import Organism
from .regulatory_search import Evaluation


def component(selected, root, maze):
    seen = {root} if root in selected else set()
    queue = deque(seen)
    while queue:
        for q in neighbors(queue.popleft(), maze.w, maze.h):
            if q in selected and q not in seen:
                seen.add(q)
                queue.append(q)
    return seen


def partial(mask, oracle):
    """Bidirectional thin output growth, independently of oracle route tie choices."""
    m = oracle.maze
    selected = set(np.flatnonzero(mask).tolist())
    if not oracle.path or not selected or any(not m.cells[p] for p in selected):
        return 0.
    a, b = component(selected, m.start, m), component(selected, m.goal, m)
    ds = getattr(oracle, '_from_start', None)
    if ds is None:
        ds = distances(m, m.start)
    length = max(1, len(oracle.path) - 1)
    values = []
    for reached, to_other in ((a, oracle.to_goal), (b, ds)):
        left = [to_other[p] for p in reached if to_other[p] >= 0]
        progress = 1. - min(left) / length if left else 0.
        values.append(.1 * bool(reached) + .8 * progress)
    branches = sum(max(0, sum(q in selected for q in neighbors(p, m.w, m.h))
                       - (1 if p in (m.start, m.goal) else 2)) for p in selected)
    stray = len(selected - a - b) / len(m.cells)
    return max(0., min(.99, sum(values) / (2 * (1 + 2 * branches)) - .2 * stray))


def correct_exit(mask, oracle, side):
    label = getattr(oracle, '_foundation_label', None)
    if label is None:
        return False
    selected = set(np.flatnonzero(mask).tolist())
    connected = component(selected, oracle.maze.start, oracle.maze)
    allowed = set(label['allowed'][side])
    wrong = set(label['exits']) - allowed
    return label['vertex'] in connected and len(allowed & selected) == 1 and not wrong & selected


def evaluate(individual, pairs, topology, limits, goal_pulse=True):
    organism = Organism(individual.genome, topology, limits, goal_pulse=goal_pulse)
    rows, reactions = [], []
    for pair in pairs:
        pair_rows = []
        for side, oracle in enumerate(pair.cases):
            m = oracle.maze
            r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
            a = assess(r, oracle)
            row = dict(case=m.case_id, status=r.status, steps=r.steps, valid=a.valid_path,
                optimal=a.optimal, no_path=a.no_path_correct, reachable=a.reachable,
                partial=partial(r.mask, oracle), old_partial=a.partial, failure=a.failure,
                correct_exit=bool(correct_exit(r.mask, oracle, side)),
                reads=r.spatial_reads, range_reads=r.range_reads, dispatches=r.dispatches,
                active=r.active_instructions, array_bytes=r.array_bytes,
                mask=np.packbits(r.mask, bitorder='little').tobytes().hex())
            pair_rows.append(row)
            reactions.append(r)
        both = all(r['valid'] for r in pair_rows)
        both_optimal = all(r['optimal'] for r in pair_rows)
        weaker = min(r['partial'] for r in pair_rows)
        for row in pair_rows:
            row.update(pair_valid=both, pair_optimal=both_optimal, paired_partial=weaker)
        rows.extend(pair_rows)
    work = sum(r.dispatches + r.spatial_reads for r in reactions)
    complete = all(r['valid'] or r['no_path'] for r in rows)
    # Entire valid routes and optimality precede paired success and all shaping.
    fitness = (sum(r['valid'] for r in rows), sum(r['optimal'] for r in rows),
        sum(r['no_path'] for r in rows) - sum(r['reachable'] and r['status'] == 'no_path' for r in rows),
        sum(r['pair_optimal'] for r in rows) // 2,
        round(sum(r['partial'] + r['paired_partial'] for r in rows), 8), -work if complete else 0)
    values = [(int(r['valid'] or r['no_path']), int(r['optimal'] or r['no_path']),
               int(r['pair_optimal']), r['partial'] + r['paired_partial']) for r in rows]
    descriptor = (tuple(int(r['valid']) for r in rows), tuple(min(7, int(r['partial'] * 8)) for r in rows),
                  min(3, max(r['steps'] for r in rows) // 16),
                  int(any(sum(r['range_reads'][1:]) for r in rows)))
    return Evaluation(fitness, values, descriptor, rows, work)


def lexicase(rng, ranked, epsilon=.02):
    survivors = list(ranked)
    cases = list(range(len(survivors[0][0].case_values)))
    rng.shuffle(cases)
    for case in cases:
        for field in range(4):
            best = max(ev.case_values[case][field] for ev, _ in survivors)
            tolerance = epsilon if field == 3 else 0.
            survivors = [(ev, item) for ev, item in survivors if ev.case_values[case][field] >= best - tolerance]
            if len(survivors) == 1:
                return survivors[0][1]
    return rng.choice(survivors)[1]
