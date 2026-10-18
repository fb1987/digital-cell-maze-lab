"""V6 stimulus comparison; V2 primitive loop, with optional initial goal pulse."""
from dataclasses import dataclass
import numpy as np
from numba import njit

from .regulatory import Genome
from .runtime import Limits, Reaction, STATUSES

TOPOLOGIES = {'local': 0, 'fixed': 1, 'evolved': 2}


@dataclass
class RegulatoryReaction(Reaction):
    dispatches: int
    active_instructions: int
    range_reads: tuple


@njit(cache=True)
def _neighbor(p, direction, radius, w, n):
    if direction == 0:
        return p - radius if p % w >= radius else -1
    if direction == 1:
        return p + radius if p % w + radius < w else -1
    if direction == 2:
        return p - radius*w if p >= radius*w else -1
    return p + radius*w if p + radius*w < n else -1


@njit(cache=True)
def _kernel(cells, w, start, goal, program, topology, ablate,
            max_steps, read_cap, dispatch_cap, goal_pulse):
    n = len(cells)
    out = np.zeros(n, dtype=np.uint8)
    ranges = np.zeros(4, dtype=np.int64)
    old = np.zeros((8, n), dtype=np.uint16)
    new = np.zeros((8, n), dtype=np.uint16)
    registers = np.zeros(64, dtype=np.int32)
    memory = out.nbytes + cells.nbytes + old.nbytes + new.nbytes + registers.nbytes + program.nbytes + ranges.nbytes + n
    if not cells[start] or not cells[goal]:
        return out, 0, 0, 0, 0, 2, memory, ranges
    old[0, start] = 1
    old[1, goal] = int(goal_pulse)
    steps, reads, dispatches, active, quiet, reason = 0, 0, 0, 0, 0, 3
    for tick in range(max_steps):
        changed = False
        interrupted = False
        for p in range(n):
            if not cells[p]:
                continue
            for r in range(64):
                registers[r] = 0
            for channel in range(8):
                registers[channel] = old[channel, p]
                new[channel, p] = old[channel, p]
            registers[8], registers[9], registers[10], registers[11] = 1, int(p == start), int(p == goal), 1
            for i in range(len(program)):
                if dispatches >= dispatch_cap:
                    reason, interrupted = 5, True
                    break
                dispatches += 1
                op, dst, a, b, c, range_id, gate = program[i]
                if gate != 64 and registers[gate] == 0:
                    continue
                spatial = op in (4, 5, 6, 7, 14, 15, 17)
                cost = 4 if op in (4, 5, 15, 17) else 1 if spatial else 0
                if reads + cost > read_cap:
                    reason, interrupted = 4, True
                    break
                radius_id = 0
                if op == 14 or op == 15:
                    radius_id = (tick % 4) if topology == 1 else range_id if topology == 2 else 0
                radius = 1 << radius_id
                reads += cost
                ranges[radius_id] += cost
                active += 1
                if op == 0:
                    registers[dst] = registers[a]
                elif op == 1:
                    registers[dst] = a
                elif op == 2:
                    registers[dst] = min(65535, registers[a] + registers[b])
                elif op == 3:
                    registers[dst] = max(0, registers[a] - registers[b])
                elif op in (4, 5, 15, 17):
                    best, chosen, count = 65536, 0, 0
                    for direction in range(4):
                        q = _neighbor(p, direction, radius, w, n)
                        value = int(old[a, q]) if q >= 0 and cells[q] and not (ablate and radius > 1) else 0
                        count += int(value > 0)
                        if value > 0 and value < best:
                            best, chosen = value, direction + 1
                    if op == 17:
                        registers[dst] = count
                    elif op == 5:
                        registers[dst] = chosen
                    else:
                        registers[dst] = best if chosen else 0
                elif op in (6, 7, 14):
                    direction = c if op == 7 else b
                    q = _neighbor(p, direction, radius, w, n)
                    value = int(old[a, q]) if q >= 0 and cells[q] and not (ablate and radius > 1) else 0
                    registers[dst] = int(value == b) if op == 7 else value
                elif op == 8:
                    registers[dst] = int(registers[a] == registers[b])
                elif op == 9:
                    registers[dst] = int(registers[a] != 0 and registers[b] != 0)
                elif op == 10:
                    registers[dst] = int(registers[a] != 0 or registers[b] != 0)
                elif op == 11:
                    registers[dst] = int(registers[a] == 0)
                elif op == 12:
                    registers[dst] = registers[b] if registers[a] else registers[c]
                elif op == 13:
                    new[dst, p] = registers[a]
                elif op == 16:
                    registers[dst] = int((registers[a] != 0) != (registers[b] != 0))
            if interrupted:
                break
            for channel in range(8):
                changed |= new[channel, p] != old[channel, p]
        if interrupted:
            break  # Discard the incomplete tick; work spent is still charged.
        old, new = new, old
        steps += 1
        if old[7, start] > 0 and old[2, start] > 0 and old[2, goal] > 0:
            reason = 0
            break
        quiet = 0 if changed else quiet + 1
        if quiet >= 4:  # All phases of the fixed schedule must have been quiet.
            reason = 0 if old[2, start] > 0 and old[2, goal] > 0 else 2
            if reason != 0:
                for p in range(n):
                    if old[2, p] > 0:
                        reason = 1
                        break
            break
    for p in range(n):
        out[p] = int(old[2, p] > 0)
    return out, steps, reads, dispatches, active, reason, memory, ranges


class Organism:
    def __init__(self, genome, topology='local', limits=Limits(), ablate_nonlocal=False, goal_pulse=False):
        if not isinstance(genome, Genome) or topology not in TOPOLOGIES or not isinstance(limits, Limits):
            raise ValueError('Invalid V2 organism configuration')
        self.genome, self.topology, self.limits = genome, topology, limits
        self.program = genome.array()
        self.program.flags.writeable = False
        self.ablate_nonlocal = bool(ablate_nonlocal)
        if type(goal_pulse) is not bool:
            raise ValueError('Goal pulse must be Boolean')
        self.goal_pulse = goal_pulse

    def react(self, cells, w, h, start, goal):
        if (type(cells) is not bytes or type(w) is not int or type(h) is not int
                or w < 1 or h < 1 or len(cells) != w*h or w*h > self.limits.max_cells
                or not 0 <= start < len(cells) or not 0 <= goal < len(cells)):
            raise ValueError('Malformed or oversized input')
        grid = np.frombuffer(cells, dtype=np.uint8)
        if np.any(grid > 1):
            raise ValueError('Non-binary input')
        mask, steps, reads, dispatches, active, reason, memory, ranges = _kernel(
            grid, w, start, goal, self.program, TOPOLOGIES[self.topology], self.ablate_nonlocal,
            self.limits.max_steps, len(cells)*self.limits.reads_per_site,
            len(cells)*self.limits.instructions_per_site, self.goal_pulse)
        if memory > 64 * len(cells) + 65536:
            raise RuntimeError('Substrate memory ceiling exceeded')
        return RegulatoryReaction(mask, STATUSES[reason], steps, reads, dispatches, memory,
                                  dispatches, active, tuple(int(v) for v in ranges))


def warm_runtime():
    from .regulatory import seeded_genome
    for pulse in (False, True):
        for topology in TOPOLOGIES:
            Organism(seeded_genome(), topology, goal_pulse=pulse).react(bytes([1] * 9), 3, 3, 0, 8)
