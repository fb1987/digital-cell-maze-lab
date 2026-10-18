"""Full raster emission from conventional compiled reference implementations."""
from heapq import heappop, heappush

import numpy as np
from numba import njit

from cellular_maze_lab import compiled_bfs, wave_cell
from .runtime import Reaction


@njit(cache=True)
def compiled_astar(cells, w, h, start, goal):
    n = w * h
    if not cells[start] or not cells[goal]:
        return np.empty(0, dtype=np.int32), 0
    cost = np.full(n, 2147483647, dtype=np.int32)
    parent = np.full(n, -1, dtype=np.int32)
    closed = np.zeros(n, dtype=np.uint8)
    cost[start] = 0
    parent[start] = start
    heuristic = abs(start % w - goal % w) + abs(start // w - goal // w)
    heap = [(heuristic, heuristic, start)]
    peak_heap = 1
    while heap:
        _, _, p = heappop(heap)
        if closed[p]:
            continue
        closed[p] = 1
        if p == goal:
            break
        for direction in range(4):
            q = -1
            if direction == 0 and p % w > 0:
                q = p - 1
            elif direction == 1 and p % w + 1 < w:
                q = p + 1
            elif direction == 2 and p >= w:
                q = p - w
            elif direction == 3 and p + w < n:
                q = p + w
            if q >= 0 and cells[q] and not closed[q] and cost[p] + 1 < cost[q]:
                cost[q] = cost[p] + 1
                parent[q] = p
                heuristic = abs(q % w - goal % w) + abs(q // w - goal // w)
                heappush(heap, (int(cost[q]) + heuristic, heuristic, q))
                peak_heap = max(peak_heap, len(heap))
    if parent[goal] < 0:
        return np.empty(0, dtype=np.int32), peak_heap
    path = np.empty(cost[goal] + 1, dtype=np.int32)
    p = goal
    for i in range(len(path) - 1, -1, -1):
        path[i] = p
        p = parent[p]
    return path, peak_heap


def baseline(name, cells, w, h, start, goal):
    array = np.frombuffer(cells, dtype=np.uint8)
    if name == 'compiled_bfs':
        path = compiled_bfs(array, w, h, start, goal)
        # Conservative array-payload bound: input + prev + queue + path + mask.
        memory = 10 * len(cells) + path.nbytes
    elif name == 'compiled_astar':
        path, peak_heap = compiled_astar(array, w, h, start, goal)
        # Logical payload estimate; excludes heap capacity/allocator overhead.
        memory = 11 * len(cells) + path.nbytes + 24 * peak_heap
    elif name == 'wave_bit':
        path = wave_cell(cells, w, h, start, goal)
        memory = -1  # Python integer history/object allocations not instrumented.
    else:
        raise ValueError(name)
    mask = np.zeros(len(cells), dtype=np.uint8)
    if len(path):
        mask[np.asarray(path, dtype=np.int64)] = 1
    return Reaction(mask, 'emitted' if len(path) else 'no_path', -1, -1, -1, memory)


def warm_baselines():
    for name in ('compiled_bfs', 'compiled_astar', 'wave_bit'):
        baseline(name, bytes([1] * 9), 3, 3, 0, 8)
