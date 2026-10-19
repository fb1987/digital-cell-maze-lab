"""V12E: matched completed-pair priority comparison from six random-origin populations."""
import argparse
from contextlib import ExitStack
import hashlib
from importlib.metadata import version
from io import StringIO
import json
from pathlib import Path
import platform
import resource
import subprocess
import time
import gzip

from .foundation_calibration import ROOT, write_json
from .foundation_pair_data import PARENT, SEED, EXTRA_MANIFESTS, environments
from .foundation_pair_search import PairSearch, fork_state
from .foundation_study import compressed_json, read_compressed
from .foundation_study_data import batch, validation, advance
from .growth_runtime import warm_runtime


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def state_key(state):
    return '/'.join(str(state['config'][k]) for k in ('study', 'topology', 'origin', 'method', 'replicate'))


def verified_parent():
    summary = json.loads((PARENT / 'search_summary.json').read_text())
    proof = json.loads((PARENT / 'verification.json').read_text())
    assert proof['all_checks_passed'] and sha(PARENT / 'search_summary.json') == proof['search_summary_sha256']
    assert sha(PARENT / 'confirmation/summary.json') == proof['confirmation_summary_sha256']
    assert sha(PARENT / 'frozen_selections.json.gz') == summary['frozen_sha256']
    for path, digest in {**summary['source_sha256'], **summary['input_sha256']}.items():
        assert sha(ROOT / path) == digest, path
    saved = read_compressed(PARENT / 'checkpoint.latest.json.gz')
    assert saved['generation'] == summary['rounds'] == 865 and len(saved['states']) == 24
    freeze = read_compressed(PARENT / 'frozen_selections.json.gz')
    for state in saved['states']:
        assert state['next_generation'] == 865
        for k, value in freeze[state_key(state)].items():
            assert state[k] == value, k
    return saved, summary


def starting_states(parent):
    result = []
    for state in parent['states']:
        if state['config']['origin'] != 'fresh':
            continue
        policies = ('current', 'paired') if state['config']['method'] == 'evolution' else ('current',)
        result.extend(fork_state(state, policy) for policy in policies)
    assert len(result) == 18
    return result


def slug(config):
    return '_'.join(str(config[k]) for k in ('selection_policy', 'topology', 'method', 'replicate'))


def restore_searches(states, out, registry, evaluations):
    searches = []
    for state in states:
        path = Path(out) / 'checkpoints' / (slug(state['config']) + '.json')
        path.write_text(json.dumps(state, separators=(',', ':')) + '\n')
        searches.append(PairSearch(state['config'], [], registry, evaluations, path, resume=True))
    return searches


def run(out, resume=False, seconds=4500, max_generations=4096):
    out = Path(out)
    if seconds != 4500 or max_generations != 4096:
        raise ValueError('Production continuation uses the preregistered bounds')
    if (out / 'search_summary.json').exists():
        raise FileExistsError('Search is already frozen')
    if out.exists() and any(out.iterdir()) and not resume:
        raise FileExistsError('Choose a fresh directory or resume its checkpoint')
    warm_runtime()
    started = time.perf_counter()
    parent, parent_summary = verified_parent()
    initial_states = starting_states(parent)
    start_generation = parent['generation']
    baseline = {state_key(s): {k: s[k] for k in ('work', 'responses', 'serial')} for s in initial_states}
    out.mkdir(parents=True, exist_ok=True)
    (out / 'checkpoints').mkdir(exist_ok=True)
    (out / 'segments').mkdir(exist_ok=True)
    sources = [*sorted((ROOT / 'maze_evolution').glob('*.py')), ROOT / 'cellular_maze_lab.py',
               ROOT / 'docs/FOUNDATION_PAIR_V12E.md', ROOT / 'tests/test_foundation_pair.py']
    inputs = [PARENT / name for name in ('checkpoint.latest.json.gz', 'frozen_selections.json.gz',
        'search_summary.json', 'verification.json', 'groups.json', 'confirmation/summary.json')]
    inputs += list(EXTRA_MANIFESTS)
    metadata = dict(seed=SEED, ancestral_seed=parent['states'][0]['config']['seed'], start_generation=start_generation,
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
        input_sha256={**parent_summary['input_sha256'], **{str(p.relative_to(ROOT)): sha(p) for p in inputs}},
        parent_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        python=platform.python_version(), platform=platform.platform(),
        packages={name: version(name) for name in ('numpy', 'numba', 'llvmlite', 'pytest')},
        seconds_budget=seconds, additional_generation_limit=max_generations, baseline_counts=baseline,
        borrowed_validation_responses=432, parent_search_seconds=parent_summary['elapsed_seconds'],
        design='local/evolved × current-evolution/paired-evolution/current-resample × three replicates',
        primary_selection='common_archives/paired; identical validation rank in every arm')
    saved = None
    offset = 0.
    generation = start_generation
    levels, entered = list(parent['levels']), list(parent['entered'])
    progress, segments = [], []
    if resume:
        saved = read_compressed(out / 'checkpoint.latest.json.gz')
        metadata = saved['metadata']
        for path, digest in {**metadata['source_sha256'], **metadata['input_sha256']}.items():
            assert sha(ROOT / path) == digest, path
        offset, levels, entered = saved['elapsed_seconds'], saved['levels'], saved['entered']
        progress, segments, generation = saved['progress'], saved['segments'], saved['generation']
        for path in (out / 'segments').glob('*.jsonl.gz'):
            if str(path.relative_to(out)) not in {p for s in segments for p in s['files']}:
                path.rename(path.with_name(path.name + f'.orphaned-{time.time_ns()}'))
    data = environments(saved_keys=saved['group_keys'] if saved else None)
    assert data.previous_count == 85628
    metadata['excluded_layouts'] = data.previous_count
    if saved is None:
        # These are controls outside the search. Never replace the original frozen founders.
        compressed_json(out / 'initial_states.json.gz', initial_states)
        compressed_json(out / 'checkpoint_selections.json.gz', {state_key(s): dict(config=s['config'], champion=s['common_archives']['current']['item']) for s in initial_states})
    else:
        assert metadata['checkpoint_selections_sha256'] == sha(out / 'checkpoint_selections.json.gz')
    metadata['checkpoint_selections_sha256'] = sha(out / 'checkpoint_selections.json.gz')
    searches = restore_searches(saved['states'] if saved else initial_states, out, StringIO(), StringIO())
    validations = {r: validation(data, r) for r in range(3)}
    for s, state in zip(searches, saved['states'] if saved else initial_states):
        assert json.loads(json.dumps(s.state())) == state

    def elapsed():
        return offset + time.perf_counter() - started

    def snapshot():
        compressed_json(out / 'checkpoint.latest.json.gz', dict(metadata=metadata, generation=generation,
            levels=levels, entered=entered, progress=progress, segments=segments,
            elapsed_seconds=elapsed(), group_keys=list(data.groups), states=[s.state() for s in searches]))

    if saved is None:
        snapshot()
    print(json.dumps(dict(resumed_generation=generation, levels=levels, prior_layouts=data.previous_count,
        borrowed_validation=len(data.cache), populations=len(searches), minutes=elapsed()/60)), flush=True)
    reason = 'wall_limit'
    while generation - start_generation < max_generations and elapsed() < seconds:
        first = generation
        with ExitStack() as stack:
            number = len(segments)
            names = [f'segments/{number:04d}.{kind}.jsonl.gz' for kind in ('lineage', 'evaluations')]
            reg, log = [stack.enter_context(gzip.open(out / name, 'wt', compresslevel=1)) for name in names]
            for s in searches:
                s.registry, s.evaluations = reg, log
            for _ in range(10):
                batches = {r: batch(data, r, generation, levels[r]) for r in range(3)}
                shift = generation % len(searches)
                for s in searches[shift:] + searches[:shift]:
                    rep = s.config['replicate']
                    s.step(batches[rep], validations[rep], levels[rep])
                generation += 1
                changes = advance(levels, entered, generation, searches)
                progress.extend(changes)
                stats = {key: [s.common_archives['paired']['rank'][0] for s in searches
                         if s.config['selection_policy'] + '/' + s.config['method'] == key]
                         for key in ('current/evolution', 'paired/evolution', 'current/resample')}
                print(json.dumps(dict(round=generation, additional_rounds=generation-start_generation,
                    minutes=round(elapsed()/60, 2), levels=levels, common_validation_pairs=stats, advances=changes)), flush=True)
                if generation - start_generation >= max_generations or elapsed() >= seconds:
                    break
        segments.append(dict(files=names, first_generation=first, last_generation=generation - 1))
        snapshot()
        disk = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
        if disk >= 4 * 2**30 or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 8 * 2**30:
            reason = 'resource_limit'
            break
    if generation - start_generation >= max_generations:
        reason = 'generation_limit'
    for s in searches:
        s.checkpoint.write_text(json.dumps(s.state(), separators=(',', ':')) + '\n')
    compressed_json(out / 'frozen_selections.json.gz', {s.key: s.selection() for s in searches})
    data.save(out)
    summary = dict(**metadata, reason=reason, rounds=generation, additional_rounds=generation-start_generation,
        levels=levels, progress=progress, segments=segments, frozen_sha256=sha(out / 'frozen_selections.json.gz'),
        elapsed_seconds=elapsed(), resulting_layouts=len(data.layouts), groups=len(data.groups),
        responses=sum(s.responses-baseline[s.key]['responses'] for s in searches),
        work=sum(s.work-baseline[s.key]['work'] for s in searches),
        # Parent histories are duplicated across forks, so do not sum them as project compute.
        inherited_counts_are_duplicated_across_forks=True,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        conditions={s.key: dict(responses=s.responses-baseline[s.key]['responses'],
            work=s.work-baseline[s.key]['work'], cumulative_responses=s.responses, cumulative_work=s.work,
            generations=s.next_generation, additional_generations=s.next_generation-start_generation,
            champion_rank=s.champion_rank, frozen_rank=s.frozen_rank, competence=s.competence,
            common_archive_ranks={name: value['rank'] for name, value in s.common_archives.items()}) for s in searches})
    write_json(out / 'search_summary.json', summary)
    print(json.dumps({k: summary[k] for k in ('reason', 'rounds', 'additional_rounds', 'elapsed_seconds', 'responses', 'work')}, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--resume', action='store_true')
    a = p.parse_args()
    run(a.out, a.resume)
