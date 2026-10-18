"""Source-dependent precursor fitness; all distance/oracle use stays here."""
from dataclasses import dataclass
import numpy as np
from .evaluator import distances
from .regulatory_runtime import Organism
from .regulatory_search import Evaluation, evaluate as route_evaluate
from .signal_probe import observe

HIDDEN = (0, 1, 3, 4, 5, 6)  # Exclude emitted raster (2) and stop request (7).


def signal_metrics(normal, ablated, oracle, horizon):
    # Cached only on evaluator objects, never passed to either interpreter.
    if not hasattr(oracle, '_source_distances'):
        oracle._source_distances = np.array(distances(oracle.maze, oracle.maze.start))
    d = oracle._source_distances
    reached = np.zeros(len(d), dtype=bool)
    for channel in HIDDEN:
        reached |= (normal.state[channel] > 0) & (normal.state[channel] != ablated.state[channel])
    bands = {str(k): float(np.mean(reached[d >= k])) for k in (2, 4, 8) if np.any(d >= k)}
    outside = (d < 0) & (np.frombuffer(oracle.maze.cells, dtype=np.uint8) > 0)
    leakage = float(np.mean(reached[outside])) if np.any(outside) else 0.
    aligned = normal.steps == ablated.steps == horizon
    score = max(0., float(np.mean(list(bands.values()))) - leakage) if bands and aligned else 0.
    return dict(score=score, bands=bands, leakage=leakage, aligned=aligned,
        distal_sites=int(np.sum(reached & (d >= 2))),
        max_distance=int(np.max(d[reached])) if np.any(reached & (d >= 0)) else -1,
        goal_signal=bool(reached[oracle.maze.goal] and d[oracle.maze.goal] >= 2),
        steps=[normal.steps, ablated.steps], reads=[normal.reads, ablated.reads],
        dispatches=[normal.dispatches, ablated.dispatches],
        active=[normal.active, ablated.active],
        range_reads=[normal.range_reads, ablated.range_reads],
        # While the second probe runs, the first retains one 16-byte/site state.
        pair_array_bytes=max(normal.array_bytes, ablated.array_bytes + normal.state.nbytes))


@dataclass
class PressureEvaluation(Evaluation):
    signal: float
    long_signal: float
    family_signals: dict
    inference_work: int
    probe_work: int


def evaluate(individual, cases, topology, limits, pressure, horizon=16):
    if pressure not in ('current', 'causal'):
        raise ValueError('Unknown selection pressure')
    base = route_evaluate(individual, cases, topology, limits)
    organism = Organism(individual.genome, topology, limits)
    signals, long_signals, family, probe_work = [], [], {}, 0
    for oracle, row in zip(cases, base.rows):
        m = oracle.maze
        normal = observe(organism, m.cells, m.w, m.h, m.start, m.goal, horizon, True)
        ablated = observe(organism, m.cells, m.w, m.h, m.start, m.goal, horizon, False)
        metrics = signal_metrics(normal, ablated, oracle, horizon)
        row['signal'] = metrics
        signals.append(metrics['score'])
        if len(oracle.path)-1 >= 8:
            long_signals.append(metrics['score'])
            family.setdefault(m.family, []).append(metrics['score'])
        probe_work += normal.dispatches + normal.reads + ablated.dispatches + ablated.reads
        del normal, ablated
    fitness = list(base.fitness)
    if pressure == 'causal':
        fitness[3] = round(fitness[3] + sum(signals), 8)
    # Successful-inference cost tie-break remains V2's cost, not probe overhead.
    values = [(valid, optimal, partial + (s if pressure == 'causal' else 0.))
              for (valid, optimal, partial), s in zip(base.case_values, signals)]
    return PressureEvaluation(tuple(fitness), values, base.descriptor, base.rows,
        base.work + probe_work, float(np.mean(signals)),
        float(np.mean(long_signals)) if long_signals else 0.,
        {k:float(np.mean(v)) for k,v in family.items()}, base.work, probe_work)
