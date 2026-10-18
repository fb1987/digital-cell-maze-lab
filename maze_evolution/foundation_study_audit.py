"""Independent V12C ancestry, grading, budget and fresh-output replay audit."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import resource
import statistics
import time

import numpy as np
from .baselines import baseline
from .evaluator import Maze, Oracle
from .foundation_calibration import ROOT, controls, write_json
from .foundation_calibration_audit import lines, unpack
from .foundation_data import load_pairs, layout_hash
from .foundation_study import read_compressed, slug
from .foundation_study_data import exclusions, founders
from .foundation_study_verify_core import Checker
from .growth import Genome, Individual, replay_mutation
from .growth_runtime import Organism
from .runtime import Limits


def rows_from(paths):
    for path in paths:
        yield from lines(path)


def condition(identity):
    return identity.rsplit('/i', 1)[0]


def archive_rank(rows):
    return (sum(r['valid'] for r in rows), sum(r['optimal'] for r in rows),
        sum(r['pair_optimal'] for r in rows) // 2,
        round(sum(r['partial'] + r['paired_partial'] for r in rows), 8),
        -sum(r['reads'] + r['dispatches'] for r in rows) if all(r['optimal'] for r in rows) else 0)


def audit_ancestry(paths, states):
    last_use = {}
    registered = Counter()
    for position, row in enumerate(rows_from(paths)):
        registered[condition(row['id'])] += 1
        if row['parent']:
            last_use[row['parent']] = position
    expected = {}
    initial = {}
    for key, state in states.items():
        cfg = state['config']
        initial[key] = founders(cfg['origin'], cfg['topology'], cfg['replicate'])[:2]
        items = [state['champion'], state['frozen'], *state['population']]
        items += [entry['item'] for name in ('skills', 'frozen_skills') for entry in state[name].values()]
        for item in items:
            genome = Genome.from_dict(item['genome'])
            if item['id'] in expected:
                assert genome == expected[item['id']]
            expected[item['id']] = genome
        assert registered[key] == state['serial']
    checked_expected, cache, maxima = set(), {}, defaultdict(int)
    mutations = immigrant_count = peak_cache = 0
    counters = Counter()
    for position, row in enumerate(rows_from(paths)):
        key = condition(row['id'])
        serial = int(row['id'].rsplit('/i', 1)[1])
        assert serial == counters[key]
        counters[key] += 1
        cfg = states[key]['config']
        g = Genome.from_dict(row['genome'])
        assert len(g.genes) <= 256
        maxima[key] = max(maxima[key], len(g.genes))
        if row['parent']:
            assert condition(row['parent']) == key and cfg['method'] == 'evolution'
            assert len(row['events']) == 1
            assert replay_mutation(cache[row['parent']], row['events'], 256) == g
            mutations += 1
            if last_use[row['parent']] == position:
                del cache[row['parent']]
        elif row['birth'] == 0:
            genomes, refs = initial[key]
            assert serial < cfg['population'] and g == genomes[serial] and row['founder'] == refs[serial]
            assert g.digest == states[key]['initial_digests'][serial]
        else:
            assert row['events'] is None and row['founder'] is None and 64 <= len(g.genes) <= 128
            immigrant_count += 1
        if row['id'] in expected:
            assert g == expected[row['id']]
            checked_expected.add(row['id'])
        if row['id'] in last_use:
            cache[row['id']] = g
        peak_cache = max(peak_cache, len(cache))
    assert checked_expected == set(expected)
    assert not cache
    return dict(registered=sum(registered.values()), mutations=mutations, immigrants=immigrant_count,
                peak_cached_parent_genomes=peak_cache, maximum_registered_genes=dict(maxima)), expected


def run(out):
    started = time.perf_counter()
    out = Path(out)
    summary = json.loads((out / 'search_summary.json').read_text())
    final = out / 'confirmation'
    confirmed = json.loads((final / 'summary.json').read_text())
    for path, sha in {**summary['source_sha256'], **summary['input_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
    assert hashlib.sha256((out / 'frozen_selections.json.gz').read_bytes()).hexdigest() == summary['frozen_sha256'] == confirmed['frozen_sha256']
    assert hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest() == confirmed['search_summary_sha256']
    assert hashlib.sha256((ROOT / 'maze_evolution/foundation_study_confirm.py').read_bytes()).hexdigest() == confirmed['source_sha256']
    software = ROOT / 'results/foundation_confirmation_fixtures/mazes.json.gz'
    assert hashlib.sha256(software.read_bytes()).hexdigest() == confirmed['software_fixture_sha256']
    checkpoint = read_compressed(out / 'checkpoint.latest.json.gz')
    assert checkpoint['generation'] == summary['rounds']
    assert checkpoint['segments'] == summary['segments']
    states = {}
    for state in checkpoint['states']:
        cfg = state['config']
        key = '/'.join(str(cfg[k]) for k in ('study', 'topology', 'origin', 'method', 'replicate'))
        states[key] = state
        assert state == json.loads((out / 'checkpoints' / (slug(cfg) + '.json')).read_text())
        assert state['next_generation'] == summary['rounds']
    frozen = read_compressed(out / 'frozen_selections.json.gz')
    for key, selection in frozen.items():
        for name in selection:
            assert selection[name] == states[key][name]
    cases, groups = load_pairs(out)
    new_cases, new_groups = load_pairs(final)
    with gzip.open(final / 'general_mazes.json.gz', 'rt') as f:
        general_manifest = json.load(f)
    for row in general_manifest:
        m = Maze(bytes.fromhex(row['cells_hex']), row['w'], row['h'], row['start'], row['goal'],
                 row['family'], row['seed'], row['split'], row['case_id'])
        new_cases[m.case_id] = Oracle.build(m)
    previous = exclusions()
    old = {layout_hash(Maze(bytes.fromhex(r['cells_hex']), r['w'], r['h'], r['start'], r['goal'])) for r in previous}
    assert len(old) == summary['excluded_layouts']
    owners = {}
    for group in groups:
        for pair in group.pairs:
            for o in pair.cases:
                h = layout_hash(o.maze)
                assert h not in old and owners.setdefault(h, group.identity) == group.identity
                label = o._foundation_label
                if label:
                    assert label['prefix'][0] == o.maze.start
                    assert label['distance'] + o.to_goal[label['vertex']] == len(o.path) - 1
    assert len(old) + len(owners) == summary['resulting_layouts']
    old.update(owners)
    with gzip.open(software, 'rt') as f:
        for r in json.load(f):
            old.add(layout_hash(Maze(bytes.fromhex(r['cells_hex']), r['w'], r['h'], r['start'], r['goal'])))
    assert len(old) == confirmed['excluded_layouts']
    final_owners = {}
    for o in new_cases.values():
        h = layout_hash(o.maze)
        owner = o.maze.case_id.rsplit('/d4-', 1)[0]
        if '/a' in owner[-2:] or '/b' in owner[-2:]:
            owner = owner[:-2]
        assert h not in old and final_owners.setdefault(h, owner) == owner
    assert len(old) + len(final_owners) == confirmed['resulting_layouts']
    lineage_paths = [out / s['files'][0] for s in summary['segments']]
    evaluation_paths = [out / s['files'][1] for s in summary['segments']]
    ancestry, known = audit_ancestry(lineage_paths, states)
    print('Ancestry verified', ancestry['registered'], 'programs', flush=True)
    checker = Checker(cases)
    totals, counts, by_generation, batches = defaultdict(Counter), Counter(), Counter(), {}
    best, initial_best, skills, initial_skills, competence = {}, {}, {}, {}, defaultdict(dict)
    verified_training, sampled_training = 0, 0
    for index, record in enumerate(rows_from(evaluation_paths)):
        key, rows = record['condition'], record['cases']
        cfg = states[key]['config']
        training = record['split'] == 'train'
        contains_success = any(r['valid'] or r['no_path'] for r in rows)
        verify = not training or contains_success or index % 512 == 0
        rank, work = checker.rows(rows, verify)
        assert rank == tuple(record['fitness']) and work == record['work']
        descriptor = [[int(r['valid']) for r in rows], [min(7, int(r['partial'] * 8)) for r in rows],
                      min(3, max(r['steps'] for r in rows) // 16), int(any(sum(r['range_reads'][1:]) for r in rows))]
        assert descriptor == record['descriptor']
        for row in rows:
            n = len(cases[row['case']].maze.cells)
            assert 0 <= row['steps'] <= cfg['limits']['max_steps']
            assert 0 <= row['reads'] <= n * cfg['limits']['reads_per_site']
            assert 0 <= row['active'] <= row['dispatches'] <= n * cfg['limits']['instructions_per_site']
            assert sum(row['range_reads']) == row['reads']
        totals[key]['work'] += work
        totals[key]['responses'] += len(rows)
        counts[record['split']] += 1
        by_generation[key, record['split'], record['generation']] += 1
        if training:
            assert len(rows) == 12
            task_key = cfg['replicate'], record['generation']
            ids = tuple(r['case'] for r in rows)
            assert batches.setdefault(task_key, ids) == ids
            verified_training += int(contains_success)
            sampled_training += int(not contains_success and verify)
            continue
        assert len(rows) == 144
        entry = (rank, record['id'])
        if key not in best or rank > best[key][0]:
            best[key] = entry
        if record['split'] == 'validation_initial' and (key not in initial_best or rank > initial_best[key][0]):
            initial_best[key] = entry
        rates = {}
        for level in range(4):
            subset = [r for r in rows if f'/level{level}/' in r['case']]
            srank = archive_rank(subset)
            slot = key, str(level)
            if slot not in skills or srank > skills[slot][0]:
                skills[slot] = (srank, record['id'])
            if record['split'] == 'validation_initial' and (slot not in initial_skills or srank > initial_skills[slot][0]):
                initial_skills[slot] = (srank, record['id'])
            rates[str(level)] = sum(r['pair_optimal'] for r in subset) / len(subset)
        for level in range(4):
            if rates[str(level)] >= .9 and all(rates[str(j)] >= .8 for j in range(level)):
                competence[key].setdefault(str(level), dict(id=record['id'], generation=record['generation'], rates=rates))
    for key, state in states.items():
        assert totals[key] == {'responses': state['responses'], 'work': state['work']}
        assert best[key] == (tuple(state['champion_rank']), state['champion']['id'])
        assert initial_best[key] == (tuple(state['frozen_rank']), state['frozen']['id'])
        assert competence[key] == state['competence']
        for level in range(4):
            for archive, source in ((skills, 'skills'), (initial_skills, 'frozen_skills')):
                saved = state[source][str(level)]
                assert archive[key, str(level)] == (tuple(saved['rank']), saved['item']['id'])
        assert by_generation[key, 'validation_initial', -1] == 96
        for g in range(summary['rounds']):
            assert by_generation[key, 'train', g] == 96
            assert by_generation[key, 'validation', g] == (4 if g % 8 == 0 else 0)
        cfg = state['config']
        sibling = key.replace('/evolution/', '/resample/') if cfg['method'] == 'evolution' else key.replace('/resample/', '/evolution/')
        assert state['initial_digests'] == states[sibling]['initial_digests']
        assert state['responses'] == states[sibling]['responses']
    assert sum(v['responses'] for v in totals.values()) == summary['responses']
    assert sum(v['work'] for v in totals.values()) == summary['work']
    assert len({s['responses'] for s in states.values()}) == 1
    print('Training and validation verified', sum(counts.values()), 'records;', checker.rasters, 'independently graded rasters', flush=True)
    final_checker = Checker(new_cases)
    known[controls()['intact'].identity] = controls()['intact'].genome
    replayed, model_cache = set(), {}
    replay_work = references = aliases = 0
    for record in lines(final / 'outputs.jsonl.gz'):
        rows = record['cases']
        if record['scope'] != 'general':
            final_checker.rows(rows)
        else:
            for row in rows:
                final_checker.row(row)
        is_reference = record['id'] in ('compiled_bfs', 'compiled_astar', 'wave_bit')
        for row in rows:
            o = new_cases[row['case']]
            m = o.maze
            if is_reference:
                result = baseline(record['id'], m.cells, m.w, m.h, m.start, m.goal)
                references += 1
            else:
                aliases += 1
                genome = known[record['id']]
                assert genome.digest == record['digest']
                key = genome.digest, record['topology'], tuple(record['limits'].values())
                if (key, row['case']) in replayed:
                    continue
                replayed.add((key, row['case']))
                if key not in model_cache:
                    model_cache[key] = Organism(genome, record['topology'], Limits(**record['limits']), goal_pulse=True)
                result = model_cache[key].react(m.cells, m.w, m.h, m.start, m.goal)
                replay_work += result.dispatches + result.spatial_reads
                assert (result.steps, result.spatial_reads, result.dispatches, result.active_instructions,
                        list(result.range_reads), result.array_bytes) == (row['steps'], row['reads'], row['dispatches'],
                        row['active'], row['range_reads'], row['array_bytes'])
            assert result.status == row['status'] and np.array_equal(result.mask, unpack(row, len(m.cells)))
    assert (len(replayed), replay_work, aliases) == (confirmed['distinct_inferences'], confirmed['inference_work'], confirmed['aliased_responses'])
    timings = json.loads((final / 'timings.json').read_text())
    for row in timings['records']:
        assert len(row['seconds']) == 30 and all(t > 0 for t in row['seconds'])
        assert row['median'] == statistics.median(row['seconds'])
        assert row['minimum'] == min(row['seconds']) and row['maximum'] == max(row['seconds'])
    result = dict(all_checks_passed=True, source_hashes=len(summary['source_sha256']), input_hashes=len(summary['input_sha256']),
        ancestry=ancestry, fitness_records=sum(counts.values()), record_kinds=dict(counts),
        graded_search_rasters=checker.rasters, training_success_records=verified_training,
        sampled_other_training_records=sampled_training, final_rasters=final_checker.rasters,
        distinct_final_replays=len(replayed), reference_replays=references, replay_work=replay_work,
        search_layouts=len(owners), final_layouts=len(final_owners), final_software_fixture_layouts=len(old)-summary['resulting_layouts'],
        elapsed_seconds=time.perf_counter() - started, max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        search_summary_sha256=hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest(),
        confirmation_summary_sha256=hashlib.sha256((final / 'summary.json').read_bytes()).hexdigest(),
        verifier_sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__), ROOT / 'maze_evolution/foundation_study_verify_core.py']})
    write_json(out / 'verification.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
