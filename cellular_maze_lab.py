#!/usr/bin/env python3
"""A tiny, reproducible laboratory for digital-cell maze solving.

Three solvers:
 - conventional breadth-first search (BFS): exact shortest path on all grids
 - bit-parallel excitation wave: exact shortest path on all grids
 - simultaneous dead-end retraction: exact only for tree/perfect mazes

An optional Numba-compiled BFS provides a stronger CPU baseline.

Usage:
    python -m pip install numpy numba pillow
    python cellular_maze_lab.py --sizes 33,65,129 --samples 10 --render

Only numpy is required; numba and pillow are optional. Timings exclude maze
creation, optional JIT compilation, and image rendering; input packing and path
reconstruction ARE included. Treat timings as illustrative microbenchmarks, not
hardware-independent algorithm rankings.
"""
import argparse
import functools
import random
import statistics
import time
from pathlib import Path
from collections import deque

import numpy as np

try:
    from numba import njit
except ImportError:
    njit = None


def neighbors(p, w, h):
    y, x = divmod(p, w)
    if x: yield p - 1
    if x + 1 < w: yield p + 1
    if y: yield p - w
    if y + 1 < h: yield p + w


def bfs(open_cells, w, h, start, goal):
    """Return actual shortest path as flat cell indices, or []."""
    if not open_cells[start] or not open_cells[goal]:
        return []
    prev = [-1] * (w * h)
    prev[start] = start
    q = deque([start])
    while q:
        p = q.popleft()
        if p == goal:
            break
        for n in neighbors(p, w, h):
            if open_cells[n] and prev[n] < 0:
                prev[n] = p
                q.append(n)
    if prev[goal] < 0:
        return []
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path


@functools.lru_cache(maxsize=32)
def edge_masks(w, h):
    left_edge = sum(1 << (y * w) for y in range(h))
    right_edge = left_edge << (w - 1)
    return left_edge, right_edge


def encode_grid(open_cells):
    """Pack each walkable tile into one bit; index y*w+x is bit index."""
    arr = np.frombuffer(open_cells, dtype=np.uint8)
    return int.from_bytes(np.packbits(arr, bitorder='little').tobytes(), 'little')


def adjacent_mask(mask, w, left_edge, right_edge):
    """Bit-parallel four-neighbor excitation, with no horizontal wrap."""
    return (((mask << 1) & ~left_edge) |
            ((mask >> 1) & ~right_edge) |
            (mask << w) | (mask >> w))


def wave_cell(open_cells, w, h, start, goal):
    """One biological-style excitation wave per synchronous cell cycle.

    Entire frontiers are represented by Python big ints and updated with
    native bitwise operations. Stores each arrival-time layer for backtracing.
    """
    open_mask = encode_grid(open_cells)
    left, right = edge_masks(w, h)
    source = 1 << start
    target = 1 << goal
    if not (open_mask & source) or not (open_mask & target):
        return []
    visited = source
    frontier = source
    layers = []
    while frontier:
        layers.append(frontier)
        if frontier & target:
            break
        frontier = adjacent_mask(frontier, w, left, right) & open_mask & ~visited
        visited |= frontier
    else:
        return []
    path = [goal]
    p = goal
    for previous_wave in reversed(layers[:-1]):
        p = next(n for n in neighbors(p, w, h) if (previous_wave >> n) & 1)
        path.append(p)
    path.reverse()
    return path


def retract_cell(open_cells, w, h, start, goal):
    """Repeatedly remove ALL unprotected leaves in parallel.

    For a tree (perfect maze), this leaves exactly the unique start->goal
    path, already encoded as lit pixels. For graphs containing cycles, the
    surviving mask often includes entire cycles and is NOT a path solution.
    """
    active = encode_grid(open_cells)
    left, right = edge_masks(w, h)
    protected = (1 << start) | (1 << goal)
    if (protected & active) != protected:
        return 0, 0
    rounds = 0
    while True:
        l = (active >> 1) & ~right
        r = (active << 1) & ~left
        u = active >> w
        d = active << w
        # Bits with degree at least two: OR over the six pairs of neighbors.
        degree2 = ((l & r) | (l & u) | (l & d) |
                   (r & u) | (r & d) | (u & d))
        removable = active & ~protected & ~degree2
        if not removable:
            return active, rounds
        active &= ~removable
        rounds += 1


def verify_path(path, open_cells, w, h, src, dst, ref_length):
    return bool(len(path) > 0 and path[0] == src and path[-1] == dst and
                len(path) == ref_length and len(set(path)) == len(path) and
                all(open_cells[p] for p in path) and
                all(b in neighbors(a, w, h) for a, b in zip(path, path[1:])))


def create_maze(w, family, seed):
    """Random obstacle grids, DFS perfect mazes, or long snaking corridors."""
    h = w
    rnd = random.Random(seed)
    cells = bytearray(w * h)
    if family == 'random':
        start, goal = 0, w * h - 1
        for attempt in range(500):
            cells = bytearray(1 if rnd.random() > .26 else 0 for _ in cells)
            cells[start] = cells[goal] = 1
            if bfs(cells, w, h, start, goal):
                return bytes(cells), start, goal
        raise RuntimeError('Could not make connected random maze')
    if family == 'perfect':
        assert w >= 5 and w % 2 == 1
        x, y = 1, 1
        start, goal = w + 1, (h - 2) * w + (w - 2)
        cells[start] = 1
        stack = [(x, y)]
        while stack:
            x, y = stack[-1]
            directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            rnd.shuffle(directions)
            choices = [(x + dx, y + dy, dx, dy) for dx, dy in directions
                       if 0 < x + dx < w - 1 and 0 < y + dy < h - 1 and
                       not cells[(y + dy) * w + (x + dx)]]
            if not choices:
                stack.pop()
                continue
            nx, ny, dx, dy = choices[0]
            cells[(y + dy // 2) * w + (x + dx // 2)] = 1
            cells[ny * w + nx] = 1
            stack.append((nx, ny))
        return bytes(cells), start, goal
    if family == 'comb':
        # A single long route with short side branches. Each 3rd row is a
        # horizontal corridor; two rows separate consecutive corridors.
        # The inward-pointing teeth retract in a single parallel update.
        assert w >= 9 and w % 2 == 1
        ys = list(range(0, h, 3))
        for k, y in enumerate(ys):
            for x in range(w):
                cells[y * w + x] = 1
            if k + 1 < len(ys):
                connector_x = w - 1 if k % 2 == 0 else 0
                cells[(y + 1) * w + connector_x] = 1
                cells[(y + 2) * w + connector_x] = 1
            if y + 1 < h:
                for x in range(3, w - 2, 4):
                    cells[(y + 1) * w + x] = 1
        last_k = len(ys) - 1
        end_x = w - 1 if last_k % 2 == 0 else 0
        return bytes(cells), 0, ys[-1] * w + end_x
    if family == 'snake':
        assert w >= 5 and w % 2 == 1
        for y in range(0, h, 2):
            for x in range(w):
                cells[y * w + x] = 1
            if y + 1 < h:
                cells[(y + 1) * w + (w - 1 if (y // 2) % 2 == 0 else 0)] = 1
        end_x = w - 1 if ((h - 1) // 2) % 2 == 0 else 0
        return bytes(cells), 0, (h - 1) * w + end_x
    raise ValueError(family)


if njit is not None:
    @njit(cache=True)
    def compiled_bfs(open_cells, w, h, start, goal):
        if not open_cells[start] or not open_cells[goal]:
            return np.empty(0, dtype=np.int32)
        n = w * h
        prev = np.full(n, -1, dtype=np.int32)
        q = np.empty(n, dtype=np.int32)
        head, tail = 0, 1
        prev[start] = start
        q[0] = start
        while head < tail:
            p = q[head]
            head += 1
            if p == goal:
                break
            x = p % w
            # Four explicit neighbors avoid allocating Python objects.
            for i in range(4):
                t = -1
                if i == 0 and x > 0: t = p - 1
                if i == 1 and x + 1 < w: t = p + 1
                if i == 2 and p >= w: t = p - w
                if i == 3 and p + w < n: t = p + w
                if t >= 0 and open_cells[t] and prev[t] < 0:
                    prev[t] = p
                    q[tail] = t
                    tail += 1
        if prev[goal] < 0:
            return np.empty(0, dtype=np.int32)
        steps = 1
        p = goal
        while p != start:
            p = prev[p]
            steps += 1
        path = np.empty(steps, dtype=np.int32)
        p = goal
        for k in range(steps - 1, -1, -1):
            path[k] = p
            if p != start:
                p = prev[p]
        return path
else:
    compiled_bfs = None


def measure(fn, *args):
    st = time.perf_counter_ns()
    result = fn(*args)
    return result, (time.perf_counter_ns() - st) * 1e-6


def render_maze(cells, n, src, dst, path, survivors, filename):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print('Pillow missing, skipped visual demo. Install with: pip install pillow')
        return
    pix = np.frombuffer(cells, dtype=np.uint8).reshape(n, n).astype(bool)
    path_mask = np.zeros((n, n), dtype=np.uint8)
    path_mask[np.array(path, dtype=np.int64) // n,
              np.array(path, dtype=np.int64) % n] = 1
    survivors_bits = np.unpackbits(np.frombuffer(
        survivors.to_bytes((n * n + 7) // 8, 'little'), dtype=np.uint8),
        bitorder='little')[:n * n].reshape(n, n)
    tile, pad, head = (5 if n <= 129 else 2), 16, 60
    width = 3 * (n * tile) + 4 * pad
    height = n * tile + 2 * pad + head
    image = Image.new('RGB', (width, height), '#111827')
    d = ImageDraw.Draw(image)
    names = ('Input maze', 'Cellular pruning', 'Shortest path (BFS)')
    for k, name in enumerate(names):
        ox, oy = pad + k * (n * tile + pad), pad + head
        d.text((ox, 14), name, fill='#f2f4f8')
        for y in range(n):
            for x in range(n):
                if not pix[y, x]:
                    color = '#182333'
                elif k == 1 and survivors_bits[y, x]:
                    color = '#5ae1bd'
                elif k == 2 and path_mask[y, x]:
                    color = '#ffcf6d'
                else:
                    color = '#3d4c60'
                d.rectangle((ox+x*tile, oy+y*tile,
                             ox+(x+1)*tile-1, oy+(y+1)*tile-1), fill=color)
        for p, color in [(src, '#72b6ff'), (dst, '#ff6584')]:
            y, x = divmod(p, n)
            d.rectangle((ox+x*tile, oy+y*tile,
                         ox+(x+1)*tile-1, oy+(y+1)*tile-1), fill=color)
    image.save(filename)
    print(f'Wrote {filename}')


def run(sizes, samples, seed, render, out_dir):
    if render:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    if njit is not None:
        # Warm up with the SAME Numba argument type as benchmark trials:
        # np.frombuffer(bytes, uint8) produces a READ-ONLY array, whereas
        # np.ones(...) is writable. Numba treats these as distinct compiled
        # signatures; without this, the first measured trial includes JIT.
        warm = np.frombuffer(bytes([1] * 25), dtype=np.uint8)
        compiled_bfs(warm, 5, 5, 0, 24)  # Exclude JIT compilation from timings
    print('CPU microbenchmark: all times median milliseconds; includes input packing/path extraction')
    print(f'Numba compiled baseline: {"available" if njit else "not installed"}')
    print(f'{"family":8} {"side":>5} {"trials":>6} {"path":>7} {"BFS-py":>10} '
          f'{"wave-bit":>10} {"retract":>10} {"BFS-JIT":>10} {"prune OK":>9}')
    for n in sizes:
        for family in ('random', 'perfect', 'snake', 'comb'):
            trials = 1 if family in ('snake', 'comb') else samples
            timings = {'py': [], 'wave': [], 'prune': [], 'jit': []}
            correct = 0
            lengths = []
            for i in range(trials):
                cells, src, dst = create_maze(n, family, seed + i*1009 + n*127)
                path, t = measure(bfs, cells, n, n, src, dst)
                assert path, 'Maze creation must guarantee connectivity'
                timings['py'].append(t)
                lengths.append(len(path))
                wave_path, t = measure(wave_cell, cells, n, n, src, dst)
                timings['wave'].append(t)
                assert verify_path(wave_path, cells, n, n, src, dst, len(path))
                (survivors, rounds), t = measure(retract_cell, cells, n, n, src, dst)
                timings['prune'].append(t)
                path_mask = sum(1 << p for p in path)
                correct += survivors == path_mask
                if njit is not None:
                    jit_path, t = measure(lambda: compiled_bfs(
                        np.frombuffer(cells, dtype=np.uint8), n, n, src, dst))
                    timings['jit'].append(t)
                    assert verify_path(jit_path, cells, n, n, src, dst, len(path))
                if render and i == 0 and n == sizes[min(1, len(sizes)-1)]:
                    render_maze(cells, n, src, dst, path, survivors,
                                str(Path(out_dir) / f'maze_{family}_{n}.png'))
            def med(key):
                return f'{statistics.median(timings[key]):10.3f}' if timings[key] else '       n/a'
            print(f'{family:8} {n:5} {trials:6} {statistics.median(lengths):7.0f} '
                  f'{med("py")} {med("wave")} {med("prune")} {med("jit")} '
                  f'{correct:3}/{trials:<5}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sizes', default='33,65,129')
    parser.add_argument('--samples', type=int, default=8)
    parser.add_argument('--seed', type=int, default=1729)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--out-dir', default='.', help='Where to save optional PNGs')
    args = parser.parse_args()
    run([int(v) for v in args.sizes.split(',')], args.samples, args.seed, args.render, args.out_dir)
