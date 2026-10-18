"""Runtime-only V12C profile on already excluded calibration fixtures."""
import argparse
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import resource
import time

from .foundation_calibration import fixtures, LIMITS, write_json
from .foundation_study_data import founders
from .foundation_study_search import SkillSearch
from .growth_runtime import warm_runtime


def run(out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    warm_runtime()
    data = fixtures()
    validation = [p for g in data.groups.values() for p in g.pairs]
    current = next(g for g in data.groups.values() if g.level == 0).pairs[:4]
    recall = current[:1]
    preview = next(g for g in data.groups.values() if g.level == 1).pairs[:1]
    batch = [*current, *recall, *preview]
    results = []
    started = time.perf_counter()
    for origin in ('native', 'fresh'):
        for topology in ('local', 'evolved'):
            for method in ('evolution', 'resample'):
                name = f'{origin}_{topology}_{method}'
                config = dict(study='profile_only', origin=origin, topology=topology, method=method, replicate=0,
                    seed=2026101815, population=96, immigrants=9, limits=asdict(LIMITS), goal_pulse=True,
                    validation_every=8, validation_nominees=4, mutation_policy='single', round_checkpoint=True)
                initial, refs, rng = founders(origin, topology, 0)
                with gzip.open(out / f'{name}.lineage.jsonl.gz', 'wt') as reg, gzip.open(out / f'{name}.evaluations.jsonl.gz', 'wt') as log:
                    s = SkillSearch(config, initial, reg, log, out / f'{name}.json', references=refs)
                    s.rng.setstate(rng)
                    t = time.perf_counter()
                    s.initialize(validation)
                    init = time.perf_counter() - t
                    t = time.perf_counter()
                    for _ in range(3):
                        s.step(batch, validation)
                    search = time.perf_counter() - t
                    s.force_save()
                results.append(dict(condition=name, initial_seconds=init, three_generation_seconds=search,
                    responses=s.responses, work=s.work, selected_validation=s.champion_rank[:2]))
                print(name, round(init, 3), round(search, 3), flush=True)
    write_json(out / 'summary.json', dict(scope='Timing/throughput only; discarded profile descendants; excluded V12A fixtures',
        conditions=results, elapsed_seconds=time.perf_counter() - started,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        validation_inputs=2 * len(validation), training_inputs=2 * len(batch)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
