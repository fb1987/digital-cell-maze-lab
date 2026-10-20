"""V12T bounded diagnostic adapter; no oracle imports, native normal inference unchanged."""
from dataclasses import dataclass
import numpy as np
from numba import njit
from .beacon_runtime import _neighbor,TOPOLOGIES,RegulatoryReaction
from .runtime import Limits,STATUSES
from .exposure_genome import Genome

ARMS=('active','neutral','zero','local')

@dataclass
class ExposureReaction(RegulatoryReaction):
    exposure_checks: int
    suppressed_reads: int

@njit(cache=True)
def _kernel(cells, w, start, goal, program, topology, exposure,
            max_steps, read_cap, dispatch_cap, goal_pulse, goal_flag, endpoint_check, ablate_nonlocal, feedback_off, halt_off, forced, record):
    n = len(cells)
    out = np.zeros(n, dtype=np.uint8)
    ranges = np.zeros(4, dtype=np.int64)
    exposure_stats = np.zeros(2, dtype=np.int64)
    old = np.zeros((8, n), dtype=np.uint16)
    new = np.zeros((8, n), dtype=np.uint16)
    registers = np.zeros(64, dtype=np.int32)
    memory = out.nbytes + cells.nbytes + old.nbytes + new.nbytes + registers.nbytes + program.nbytes + ranges.nbytes + n + exposure.nbytes + exposure_stats.nbytes
    history = np.zeros((max_steps if record else 0, 8, n), dtype=np.uint16)
    if not cells[start] or not cells[goal]:
        return out, 0, 0, 0, 0, 2, memory, ranges, exposure_stats, history
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
                registers[channel] = 0 if feedback_off and channel == 2 else old[channel, p]
                new[channel, p] = old[channel, p]
            registers[8], registers[9], registers[10], registers[11] = 1, int(p == start), int(p == goal and goal_flag), 1
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
                blocked = ablate_nonlocal and radius_id > 0
                if op == 14 or op == 15:
                    exposure_stats[0] += 1  # One charged exposure check per active remote opcode.
                    if radius_id > 0 and (int(exposure[0]) & (1 << (radius_id - 1))) == 0:
                        blocked = True
                        exposure_stats[1] += cost  # Requested lookup slots, including wall/off-board slots.
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
                        value = int(old[a, q]) if q >= 0 and cells[q] and not blocked and not (feedback_off and a == 2) else 0
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
                    value = int(old[a, q]) if q >= 0 and cells[q] and not blocked and not (feedback_off and a == 2) else 0
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
        if record:
            history[steps - 1] = old
        if not forced and not halt_off and old[7, start] > 0 and old[2, start] > 0 and (not endpoint_check or old[2, goal] > 0):
            reason = 0
            break
        quiet = 0 if changed else quiet + 1
        if not forced and quiet >= 4:  # All phases of the fixed schedule must have been quiet.
            reason = 0 if old[2, start] > 0 and (not endpoint_check or old[2, goal] > 0) else 2
            if reason != 0:
                for p in range(n):
                    if old[2, p] > 0:
                        reason = 1
                        break
            break
    for p in range(n):
        out[p] = int(old[2, p] > 0)
    return out, steps, reads, dispatches, active, reason, memory, ranges, exposure_stats, history


MODES = ('normal', 'pulse_off', 'flag_off', 'both_off', 'output_feedback_off', 'endpoint_off', 'halt_off')
TRACE_MODES = ('normal', 'both_off', 'output_feedback_off')

@dataclass
class Diagnostic:
    reaction: ExposureReaction
    history: np.ndarray
    instrumentation_bytes: int


def respond(model, maze, mode='normal', *, trace=False, forced=False, horizon=64):
    from .mutation_transition_runtime import Organism
    from .foundation_calibration import LIMITS
    if mode not in MODES or type(trace) is not bool or type(forced) is not bool:
        raise ValueError('Invalid diagnostic mode')
    if type(horizon) is not int or not 1 <= horizon <= 96:
        raise ValueError('Bounded trace horizon required')
    if forced and not trace:
        raise ValueError('Forced execution is diagnostic only')
    org=Organism(Genome.from_dict(model['genome']), 'active', model['topology'], LIMITS,
        mode not in ('pulse_off','both_off'), mode not in ('flag_off','both_off'), mode!='endpoint_off')
    if model['topology'] != 'local':
        raise ValueError('V12T common local topology only')
    cells,w,h,start,goal=maze.cells,maze.w,maze.h,maze.start,maze.goal
    if type(cells) is not bytes or len(cells)!=w*h or w*h>LIMITS.max_cells or not 0<=start<w*h or not 0<=goal<w*h:
        raise ValueError('Malformed maze')
    grid=np.frombuffer(cells,np.uint8)
    if np.any(grid>1):raise ValueError('Nonbinary maze')
    result=_kernel(grid,w,start,goal,org.program,TOPOLOGIES[org.topology],org.exposure,
        min(horizon,LIMITS.max_steps) if trace else LIMITS.max_steps,
        len(cells)*LIMITS.reads_per_site,len(cells)*LIMITS.instructions_per_site,
        org.goal_pulse,org.goal_flag,org.endpoint_check,False,
        mode=='output_feedback_off',mode=='halt_off',forced,trace)
    mask,steps,reads,dispatches,active,reason,memory,ranges,stats,history=result
    if memory>64*len(cells)+65536:raise RuntimeError('Substrate memory ceiling')
    reaction=ExposureReaction(mask,STATUSES[reason],steps,reads,dispatches,memory,dispatches,active,
        tuple(int(v) for v in ranges),int(stats[0]),int(stats[1]))
    history.flags.writeable=False
    return Diagnostic(reaction,history[:steps],history.nbytes)
