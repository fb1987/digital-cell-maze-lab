"""V12C: preregistered 75-minute random-origin study with shared task rounds."""
import argparse
from contextlib import ExitStack
from dataclasses import asdict
import gzip
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import resource
import subprocess
import time

from .foundation_calibration import ROOT, LIMITS, write_json
from .foundation_data import FoundationData, prior_hashes
from .foundation_study_data import SEED, exclusions, founders, validation, batch, advance
from .foundation_study_search import SkillSearch
from .growth_runtime import warm_runtime


def compressed_json(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    with gzip.open(temp, 'wt', compresslevel=1) as f:
        json.dump(value, f, separators=(',', ':'), allow_nan=False)
    temp.replace(path)


def read_compressed(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


def configurations(seed=SEED):
    return [dict(study='foundation_study', origin=origin, topology=topology, method=method,
        replicate=rep, seed=seed, population=96, immigrants=9, limits=asdict(LIMITS),
        goal_pulse=True, validation_every=8, validation_nominees=4, mutation_policy='single',
        round_checkpoint=True)
        for rep in range(3) for origin in ('native', 'fresh')
        for topology in ('local', 'evolved') for method in ('evolution', 'resample')]


def slug(config):
    return '_'.join(str(config[k]) for k in ('origin', 'topology', 'method', 'replicate'))


def restore_searches(states, out, registry, evaluations):
    searches = []
    for state in states:
        path = Path(out) / 'checkpoints' / (slug(state['config']) + '.json')
        path.write_text(json.dumps(state, separators=(',', ':')) + '\n')
        searches.append(SkillSearch(state['config'], [], registry, evaluations, path, resume=True))
    return searches


def run(out, resume=False, seconds=4500, max_generations=4096):
    out = Path(out)
    if seconds != 4500 or max_generations != 4096:
        raise ValueError('Production study uses the preregistered bounds')
    if (out / 'search_summary.json').exists():
        raise FileExistsError('Search is already frozen; use its separate confirmation command')
    if out.exists() and any(out.iterdir()) and not resume:
        raise FileExistsError('Choose a fresh output directory or resume its checkpoint')
    proof_dir = ROOT / 'results/foundation_repair'
    proof = json.loads((proof_dir / 'verification.json').read_text())
    repair = json.loads((proof_dir / 'summary.json').read_text())
    assert proof['all_checks_passed'] and repair['repair_gate'] and repair['chosen_policy'] == 'single'
    assert hashlib.sha256((proof_dir / 'summary.json').read_bytes()).hexdigest() == proof['summary_sha256']
    out.mkdir(parents=True, exist_ok=True)
    (out / 'checkpoints').mkdir(exist_ok=True)
    (out / 'segments').mkdir(exist_ok=True)
    warm_runtime()
    started = time.perf_counter()
    previous = exclusions()
    data = FoundationData(SEED, previous)
    configurations_ = configurations()
    sources = [*sorted((ROOT / 'maze_evolution').glob('*.py')), ROOT / 'cellular_maze_lab.py',
               ROOT / 'docs/FOUNDATION_STUDY_V12C.md', ROOT / 'tests/test_foundation_study.py']
    source_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    inputs = [ROOT / 'results/foundation_calibration/mazes.json.gz', ROOT / 'results/foundation_calibration/fixtures.json.gz',
              proof_dir / 'mazes.json.gz', proof_dir / 'summary.json', proof_dir / 'verification.json',
              ROOT / 'results/foundation_study_profile/unit_fixtures/mazes.json.gz',
              ROOT / 'results/foundation_study_profile/summary.json']
    inputs += [ROOT / f'results/capacity_growth/checkpoints/growth_{topology}_cap256_{rep}.json'
               for rep in range(3) for topology in ('local', 'evolved')]
    input_hashes = {**prior_hashes(ROOT), **{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    metadata = dict(seed=SEED, source_sha256=source_hashes, input_sha256=input_hashes,
        parent_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        python=platform.python_version(), platform=platform.platform(),
        packages={name: version(name) for name in ('numpy', 'numba', 'llvmlite', 'pytest')},
        seconds_budget=seconds, generation_limit=max_generations, excluded_layouts=data.previous_count)
    offset = 0.
    levels, entered, progress, segments = [0] * 3, [0] * 3, [], []
    generation = 0
    saved = None
    if resume:
        saved = read_compressed(out / 'checkpoint.latest.json.gz')
        metadata = saved['metadata']
        for path, sha in {**metadata['source_sha256'], **metadata['input_sha256']}.items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
        offset, levels, entered = saved['elapsed_seconds'], saved['levels'], saved['entered']
        progress, segments, generation = saved['progress'], saved['segments'], saved['generation']
        for key in saved['group_keys']:
            if key[3] == -1:
                data.disconnected_group(key[0], key[1], key[2], key[5])
            else:
                data.group(*key)
        assert list(map(list, data.groups)) == saved['group_keys']
        # Preserve uncommitted partial segments for diagnosis; never count them twice.
        for path in (out / 'segments').glob('*.jsonl.gz'):
            if str(path.relative_to(out)) not in {p for s in segments for p in s['files']}:
                path.rename(path.with_name(path.name + f'.orphaned-{time.time_ns()}'))
    validations = {r: validation(data, r) for r in range(3)}
    searches = []

    def elapsed():
        return offset + time.perf_counter() - started

    def snapshot():
        compressed_json(out / 'checkpoint.latest.json.gz', dict(metadata=metadata, generation=generation,
            levels=levels, entered=entered, progress=progress, segments=segments,
            elapsed_seconds=elapsed(), group_keys=list(data.groups), states=[s.state() for s in searches]))

    def open_segment(stack):
        number = len(segments)
        names = [f'segments/{number:04d}.{kind}.jsonl.gz' for kind in ('lineage', 'evaluations')]
        streams = [stack.enter_context(gzip.open(out / name, 'wt', compresslevel=1)) for name in names]
        return names, streams

    if saved is None:
        with ExitStack() as stack:
            names, (reg, log) = open_segment(stack)
            for config in configurations_:
                initial, refs, rng = founders(config['origin'], config['topology'], config['replicate'])
                s = SkillSearch(config, initial, reg, log, out / 'checkpoints' / (slug(config) + '.json'), references=refs)
                s.rng.setstate(rng)
                s.initialize(validations[config['replicate']])
                searches.append(s)
                print(f"Initialized {slug(config)}; validation shortest {s.champion_rank[1]}/136 reachable", flush=True)
        segments.append(dict(files=names, first_generation=-1, last_generation=-1))
        snapshot()
    else:
        from io import StringIO
        searches = restore_searches(saved['states'], out, StringIO(), StringIO())
    reason = 'wall_limit'
    while generation < max_generations and elapsed() < seconds:
        first = generation
        with ExitStack() as stack:
            names, (reg, log) = open_segment(stack)
            for s in searches:
                s.registry, s.evaluations = reg, log
            for _ in range(10):
                batches = {r: batch(data, r, generation, levels[r]) for r in range(3)}
                # Rotate execution order without consuming a candidate's RNG.
                shift = generation % len(searches)
                for s in searches[shift:] + searches[:shift]:
                    rep = s.config['replicate']
                    s.step(batches[rep], validations[rep], levels[rep])
                generation += 1
                changes = advance(levels, entered, generation, searches)
                progress.extend(changes)
                stats = {key: [s.champion_rank[1] for s in searches if s.config['method'] == key]
                         for key in ('evolution', 'resample')}
                print(json.dumps(dict(round=generation, minutes=round(elapsed()/60, 2), levels=levels,
                                      validation_shortest=stats, advances=changes)), flush=True)
                if generation >= max_generations or elapsed() >= seconds:
                    break
        segments.append(dict(files=names, first_generation=first, last_generation=generation - 1))
        snapshot()
        disk = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
        if disk >= 4 * 2**30 or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 8 * 2**30:
            reason = 'resource_limit'
            break
    if generation >= max_generations:
        reason = 'generation_limit'
    for s in searches:
        # The streams are now closed; save the same final full state directly.
        s.checkpoint.write_text(json.dumps(s.state(), separators=(',', ':')) + '\n')
    compressed_json(out / 'frozen_selections.json.gz', {s.key: s.selection() for s in searches})
    frozen_sha = hashlib.sha256((out / 'frozen_selections.json.gz').read_bytes()).hexdigest()
    data.save(out)
    summary = dict(**metadata, reason=reason, rounds=generation, levels=levels, progress=progress, segments=segments,
        frozen_sha256=frozen_sha, elapsed_seconds=elapsed(), resulting_layouts=len(data.layouts),
        groups=len(data.groups), responses=sum(s.responses for s in searches), work=sum(s.work for s in searches),
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        conditions={s.key: dict(responses=s.responses, work=s.work, generations=s.next_generation,
            champion_rank=s.champion_rank, frozen_rank=s.frozen_rank, competence=s.competence) for s in searches})
    write_json(out / 'search_summary.json', summary)
    print(json.dumps({k: summary[k] for k in ('reason', 'rounds', 'elapsed_seconds', 'responses', 'work')}, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--resume', action='store_true')
    a = p.parse_args()
    run(a.out, a.resume)
