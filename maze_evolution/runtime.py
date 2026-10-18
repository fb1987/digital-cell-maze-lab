"""Synchronous, budgeted local interpreter. No evaluator/solver imports."""
from dataclasses import dataclass

import numpy as np
from numba import njit

from .genome import Genome, Op


@dataclass(frozen=True)
class Limits:
    max_steps: int = 512
    reads_per_site: int = 2048
    instructions_per_site: int = 16384
    max_cells: int = 65536

    def __post_init__(self):
        for value in vars(self).values():
            if type(value) is not int or value < 1:
                raise ValueError('Budgets must be positive integers')
        if self.max_steps > 4096 or self.max_cells > 65536:
            raise ValueError('Hard runtime ceiling exceeded')
        if self.reads_per_site > 65536 or self.instructions_per_site > 131072:
            raise ValueError('Hard work ceiling exceeded')


@dataclass
class Reaction:
    mask: np.ndarray
    status: str
    steps: int
    spatial_reads: int
    instructions: int
    array_bytes: int


STATUSES = ('emitted', 'quiescent', 'no_path', 'step_budget',
            'read_budget', 'instruction_budget')


@njit(cache=True)
def _neighbor(p, direction, w, n):
    if direction == 0:
        return p - 1 if p % w > 0 else -1
    if direction == 1:
        return p + 1 if p % w + 1 < w else -1
    if direction == 2:
        return p - w if p >= w else -1
    return p + w if p + w < n else -1


@njit(cache=True)
def _kernel(cells, w, start, goal, program, max_steps, max_reads, max_instructions):
    n = len(cells)
    output = np.zeros(n, dtype=np.uint8)
    if not cells[start] or not cells[goal]:
        return output, 0, 0, 0, 2, output.nbytes + cells.nbytes + program.nbytes
    old = np.zeros((4, n), dtype=np.uint16)
    new = np.zeros((4, n), dtype=np.uint16)
    registers = np.zeros(24, dtype=np.int32)
    old[0, start] = 1  # Public stimulus convention, identical for every genome.
    reads_per_tick = 0
    open_count = 0
    for p in range(n):
        open_count += int(cells[p] != 0)
    for i in range(len(program)):
        op = program[i, 0]
        if op == 4 or op == 5:
            reads_per_tick += 4 * open_count
        elif op == 6 or op == 7:
            reads_per_tick += open_count
    instructions_per_tick = open_count * len(program)
    reads = 0
    instructions = 0
    steps = 0
    reason = 3
    for _ in range(max_steps):
        if reads + reads_per_tick > max_reads:
            reason = 4
            break
        if instructions + instructions_per_tick > max_instructions:
            reason = 5
            break
        changed = False
        for p in range(n):
            if not cells[p]:
                continue
            for r in range(24):
                registers[r] = 0
            for channel in range(4):
                registers[channel] = old[channel, p]
                new[channel, p] = old[channel, p]  # Missing STORE means HOLD.
            registers[4] = 1
            registers[5] = int(p == start)
            registers[6] = int(p == goal)
            registers[7] = 1
            for i in range(len(program)):
                op, dst, a, b, c = program[i]
                if op == 0:
                    registers[dst] = registers[a]
                elif op == 1:
                    registers[dst] = a
                elif op == 2:
                    registers[dst] = min(65535, registers[a] + registers[b])
                elif op == 3:
                    registers[dst] = max(0, registers[a] - registers[b])
                elif op == 4 or op == 5:
                    best, chosen = 65536, 0
                    for direction in range(4):
                        q = _neighbor(p, direction, w, n)
                        if q >= 0 and cells[q]:
                            value = old[a, q]
                            if value > 0 and value < best:
                                best, chosen = value, direction + 1
                    registers[dst] = (0 if chosen == 0 else best) if op == 4 else chosen
                elif op == 6 or op == 7:
                    direction = b if op == 6 else c
                    q = _neighbor(p, direction, w, n)
                    value = int(old[a, q]) if q >= 0 and cells[q] else 0
                    registers[dst] = value if op == 6 else int(value == b)
                elif op == 8:
                    registers[dst] = int(registers[a] == registers[b])
                elif op == 9:
                    registers[dst] = int(registers[a] != 0 and registers[b] != 0)
                elif op == 10:
                    registers[dst] = int(registers[a] != 0 or registers[b] != 0)
                elif op == 11:
                    registers[dst] = int(registers[a] == 0)
                elif op == 12:
                    registers[dst] = registers[b] if registers[a] != 0 else registers[c]
                elif op == 13:
                    new[dst, p] = registers[a]
            for channel in range(4):
                changed |= new[channel, p] != old[channel, p]
        old, new = new, old
        steps += 1
        reads += reads_per_tick
        instructions += instructions_per_tick
        # This is a stop proposal, not a validity test; the evaluator may reject it.
        if old[2, start] > 0 and old[2, goal] > 0:
            reason = 0
            break
        if not changed:
            reason = 2
            for p in range(n):
                if old[2, p] > 0:
                    reason = 1
                    break
            break
    for p in range(n):
        output[p] = int(old[2, p] > 0)
    memory = old.nbytes + new.nbytes + registers.nbytes + output.nbytes + cells.nbytes + program.nbytes
    return output, steps, reads, instructions, reason, memory


class Organism:
    def __init__(self, genome: Genome, limits=Limits()):
        if not isinstance(genome, Genome) or not isinstance(limits, Limits):
            raise ValueError('Expected a validated genome and limits')
        self.genome = genome
        self.limits = limits
        self.program = genome.array()

    def react(self, cells: bytes, w: int, h: int, start: int, goal: int):
        n = w * h
        if type(cells) is not bytes or w < 1 or h < 1 or n != len(cells):
            raise ValueError('Expected an immutable rectangular byte grid')
        if n > self.limits.max_cells or not 0 <= start < n or not 0 <= goal < n:
            raise ValueError('Grid bounds exceeded')
        grid = np.frombuffer(cells, dtype=np.uint8)
        if np.any(grid > 1):
            raise ValueError('Maze values must be binary')
        mask, steps, reads, instructions, reason, memory = _kernel(
            grid, w, start, goal, self.program, self.limits.max_steps,
            n * self.limits.reads_per_site, n * self.limits.instructions_per_site)
        # The temporary binary-input check uses at most one additional byte/site.
        if memory + n > 64 * n + 65536:
            raise RuntimeError('Substrate memory ceiling exceeded')
        return Reaction(mask, STATUSES[reason], steps, reads, instructions, memory + n)


def warm_runtime():
    from .genome import wavefront_genome
    Organism(wavefront_genome()).react(bytes([1] * 9), 3, 3, 0, 8)
