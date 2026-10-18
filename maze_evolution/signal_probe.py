"""Developmental observer for V3; V2 inference and genome grammar stay frozen.

The primitive loop is a literal V2 copy with source presence and stopping controls.
No evaluator, distance, route or oracle enters this module. Probes force an aligned
horizon; source ablation removes both public source inputs. Never used for output
inference or inference latency claims.
"""
from dataclasses import dataclass
import numpy as np
from numba import njit
from .regulatory_runtime import Organism, TOPOLOGIES, _neighbor
from .runtime import STATUSES

@dataclass
class Observation:
    state: np.ndarray
    steps: int
    reads: int
    dispatches: int
    active: int
    status: str
    array_bytes: int
    range_reads: tuple

@njit(cache=True)
def _probe_kernel(cells, w, start, goal, program, topology, ablate,
            max_steps, read_cap, dispatch_cap, source_present, force_horizon):
    n = len(cells)
    out = np.zeros(n, dtype=np.uint8)
    ranges = np.zeros(4, dtype=np.int64)
    old = np.zeros((8, n), dtype=np.uint16)
    new = np.zeros((8, n), dtype=np.uint16)
    registers = np.zeros(64, dtype=np.int32)
    memory = out.nbytes + cells.nbytes + old.nbytes + new.nbytes + registers.nbytes + program.nbytes + ranges.nbytes + n
    if not cells[start] or not cells[goal]:
        return old, 0, 0, 0, 0, 2, memory, ranges
    old[0, start] = int(source_present)
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
            registers[8], registers[9], registers[10], registers[11] = 1, int(source_present and p == start), int(p == goal), 1
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
        if not force_horizon and old[7, start] > 0 and old[2, start] > 0 and old[2, goal] > 0:
            reason = 0
            break
        quiet = 0 if changed else quiet + 1
        if not force_horizon and quiet >= 4:  # All phases of the fixed schedule must have been quiet.
            reason = 0 if old[2, start] > 0 and old[2, goal] > 0 else 2
            if reason != 0:
                for p in range(n):
                    if old[2, p] > 0:
                        reason = 1
                        break
            break
    for p in range(n):
        out[p] = int(old[2, p] > 0)
    return old, steps, reads, dispatches, active, reason, memory, ranges


def observe(organism, cells, w, h, start, goal, horizon=16, source_present=True,
            force_horizon=True):
    if not isinstance(organism, Organism) or type(horizon) is not int or not 1 <= horizon <= 64:
        raise ValueError('Invalid bounded observation')
    if (type(cells) is not bytes or type(w) is not int or type(h) is not int
            or w < 1 or h < 1 or len(cells) != w*h or w*h > organism.limits.max_cells
            or not 0 <= start < len(cells) or not 0 <= goal < len(cells)):
        raise ValueError('Malformed or oversized observation')
    grid = np.frombuffer(cells, dtype=np.uint8)
    if np.any(grid > 1):
        raise ValueError('Non-binary input')
    state, steps, reads, dispatches, active, reason, memory, ranges = _probe_kernel(
        grid, w, start, goal, organism.program, TOPOLOGIES[organism.topology],
        organism.ablate_nonlocal, min(horizon, organism.limits.max_steps),
        len(cells)*organism.limits.reads_per_site,
        len(cells)*organism.limits.instructions_per_site, bool(source_present), bool(force_horizon))
    if memory > 64*len(cells) + 65536:
        raise RuntimeError('Substrate memory ceiling exceeded')
    state.flags.writeable = False
    return Observation(state, steps, reads, dispatches, active, STATUSES[reason], memory,
                       tuple(int(v) for v in ranges))
