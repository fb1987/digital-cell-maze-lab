"""Independent V12E grading, exact reproduction replay, archive and final-output audit."""
import argparse
from collections import Counter, defaultdict
from itertools import groupby
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
from .foundation_data import load_pairs, layout_hash, FoundationData
from .foundation_study import read_compressed
from .foundation_pair_data import exclusions, PARENT, FIXTURES, BANDS
from .foundation_continuation_data import borrowed_validation
from .foundation_pair import verified_parent, starting_states, state_key, slug, sha as file_sha
from .foundation_pair_replay import ReproductionAudit, ranked_fitness
from .foundation_study_data import batch, validation
from .foundation_study_verify_core import Checker
from .growth_runtime import Organism
from .runtime import Limits


def rows_from(paths):
    for path in paths:
        yield from lines(path)


def archive_rank(rows):
    return (sum(r['valid'] for r in rows), sum(r['optimal'] for r in rows),
        sum(r['pair_optimal'] for r in rows) // 2,
        round(sum(r['partial'] + r['paired_partial'] for r in rows), 8),
        -sum(r['reads'] + r['dispatches'] for r in rows) if all(r['optimal'] for r in rows) else 0)


def audit_search(evaluation_paths, lineage_paths, states, parents, cases, schedule,
                 summary, checkpoint, parent_checkpoint):
    checker = Checker(cases)
    totals, counts, by_generation, batches = defaultdict(Counter), Counter(), Counter(), {}
    best, best_rows, skills, skill_rows, common, competence = {}, {}, {}, {}, {}, {}
    changes = []
    for key, parent in parents.items():
        best[key] = (tuple(parent['champion_rank']), parent['champion']['id'])
        best_rows[key] = parent['champion_rows']
        competence[key] = dict(parent['competence'])
        for level, entry in parent['skills'].items():
            skills[key, level] = (tuple(entry['rank']), entry['item']['id'])
            skill_rows[key, level] = entry
        for name, entry in parent['common_archives'].items():
            common[key, name] = dict(rank=tuple(entry['rank']), id=entry['item']['id'],
                                     rows=entry['rows'], generation=entry['generation'])
    levels, entered = list(parent_checkpoint['levels']), list(parent_checkpoint['entered'])
    progress, completed_keys = [], []
    reproduction = ReproductionAudit(parents, states, rows_from(lineage_paths))
    verified_training = sampled_training = index = 0
    previous_generation = None

    def finish_round(generation):
        assert len(completed_keys) == len(states) and set(completed_keys) == set(states)
        order = list(states)
        shift = (generation - 1) % len(order)
        assert completed_keys == order[shift:] + order[:shift]
        completed_keys.clear()
        for rep in range(3):
            level = levels[rep]
            eligible = [key for key, state in states.items()
                        if state['config']['replicate'] == rep and str(level) in competence[key]]
            if level < 3 and generation - entered[rep] >= 20 and eligible:
                key = eligible[0]
                levels[rep] += 1
                entered[rep] = generation
                progress.append(dict(replicate=rep, generation=generation, level=level + 1,
                    condition=key, certificate=competence[key][str(level)]))

    for (generation, key), chunk in groupby(rows_from(evaluation_paths),
                                           key=lambda r: (r['generation'], r['condition'])):
        records = list(chunk)
        if previous_generation is not None and generation != previous_generation:
            assert generation == previous_generation + 1
            finish_round(generation)
        previous_generation = generation
        assert key not in completed_keys
        completed_keys.append(key)
        cfg = states[key]['config']
        assert summary['start_generation'] <= generation < summary['rounds']
        train, validated = [], []
        for record in records:
            rows = record['cases']
            training = record['split'] == 'train'
            assert record['split'] in ('train', 'validation')
            success = any(r['valid'] or r['no_path'] for r in rows)
            verify = not training or success or index % 512 == 0
            raw, work = checker.rows(rows, verify)
            rank = ranked_fitness(raw, cfg['selection_policy'])
            assert raw == tuple(record['raw_fitness']) and rank == tuple(record['fitness'])
            assert work == record['work']
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
            by_generation[key, record['split'], generation] += 1
            index += 1
            if training:
                assert not validated and len(rows) == 12
                task_key = cfg['replicate'], generation
                if task_key not in batches:
                    pairs = batch(schedule, cfg['replicate'], generation, levels[cfg['replicate']])
                    batches[task_key] = tuple(o.maze.case_id for pair in pairs for o in pair.cases)
                assert tuple(r['case'] for r in rows) == batches[task_key]
                verified_training += int(success)
                sampled_training += int(not success and verify)
                train.append(record)
                continue
            assert len(train) == 96 and len(rows) == 144
            assert [r['case'] for r in rows] == [o.maze.case_id for pair in validation(schedule, cfg['replicate']) for o in pair.cases]
            validated.append(record)
            if rank > best[key][0]:
                best[key] = rank, record['id']
                best_rows[key] = rows
            for name in ('current', 'paired'):
                shared_rank = ranked_fitness(raw, name)
                old = common[key, name]
                if shared_rank > old['rank']:
                    pair_counts = lambda values: [sum(r['pair_optimal'] for r in values
                        if f'/level{level}/' in r['case']) // 2 for level in range(4)]
                    before, after = pair_counts(old['rows']), pair_counts(rows)
                    changes.append(dict(condition=key, archive=name, generation=generation,
                        old_id=old['id'], new_id=record['id'], old_rank=old['rank'], new_rank=shared_rank,
                        old_level_pairs=before, new_level_pairs=after,
                        lost_adjacent=after[0] < before[0], lost_nonadjacent=sum(after[1:]) < sum(before[1:])))
                    common[key, name] = dict(rank=shared_rank, id=record['id'], rows=rows, generation=generation)
            rates = {}
            for level in range(4):
                level_key = str(level)
                subset = [r for r in rows if f'/level{level}/' in r['case']]
                srank = archive_rank(subset)
                if srank > skills[key, level_key][0]:
                    skills[key, level_key] = srank, record['id']
                    skill_rows[key, level_key] = dict(rows=subset, generation=generation)
                rates[level_key] = sum(r['pair_optimal'] for r in subset) / len(subset)
            for level in range(4):
                if rates[str(level)] >= .9 and all(rates[str(j)] >= .8 for j in range(level)):
                    competence[key].setdefault(str(level), dict(id=record['id'], generation=generation, rates=rates))
        history = states[key]['history'][generation]
        assert history['generation'] == generation and history['level'] == levels[cfg['replicate']]
        assert tuple(history['champion_rank']) == best[key][0] and history['champion'] == best[key][1]
        assert history['responses'] == parents[key]['responses'] + totals[key]['responses']
        assert history['work'] == parents[key]['work'] + totals[key]['work']
        for name in ('current', 'paired'):
            actual = history['common_archives'][name]
            expected = common[key, name]
            assert actual['id'] == expected['id'] and tuple(actual['rank']) == expected['rank']
            assert actual['generation'] == expected['generation']
        reproduction.step(key, generation, train, validated, history)
    finish_round(summary['rounds'])
    assert levels == summary['levels'] == checkpoint['levels'] and entered == checkpoint['entered']
    assert progress == summary['progress'] == checkpoint['progress']
    for key, state in states.items():
        assert totals[key] == {'responses': state['responses'] - parents[key]['responses'],
                               'work': state['work'] - parents[key]['work']}
        assert state['champion_rows'] == best_rows[key]
        assert best[key] == (tuple(state['champion_rank']), state['champion']['id'])
        assert state['competence'] == competence[key]
        for level in range(4):
            entry = state['skills'][str(level)]
            assert (tuple(entry['rank']), entry['item']['id']) == skills[key, str(level)]
            for field in ('rows','generation'):
                assert entry[field] == skill_rows[key, str(level)][field]
        for name, entry in state['common_archives'].items():
            expected = common[key, name]
            assert tuple(entry['rank']) == expected['rank'] and entry['item']['id'] == expected['id']
            assert entry['rows'] == expected['rows'] and entry['generation'] == expected['generation']
        for g in range(summary['start_generation'], summary['rounds']):
            assert by_generation[key, 'train', g] == 96
            assert by_generation[key, 'validation', g] == (4 if g % 8 == 0 else 0)
    assert len({v['responses'] for v in totals.values()}) == 1
    assert sum(v['responses'] for v in totals.values()) == summary['responses']
    assert sum(v['work'] for v in totals.values()) == summary['work']
    reproduction_result, known = reproduction.finish()
    print('Search verified', sum(counts.values()), 'records;', checker.rasters, 'rasters;', reproduction_result['registered'], 'reproduced programs', flush=True)
    return dict(fitness_records=sum(counts.values()), record_kinds=dict(counts),
        graded_search_rasters=checker.rasters, training_success_records=verified_training,
        sampled_other_training_records=sampled_training), reproduction_result, changes, known

def run(out):
    started = time.perf_counter()
    out = Path(out)
    summary = json.loads((out / 'search_summary.json').read_text())
    parent_checkpoint, parent_summary = verified_parent()
    initial = starting_states(parent_checkpoint)
    assert read_compressed(out / 'initial_states.json.gz') == initial
    parents = {state_key(state): state for state in initial}
    assert summary['start_generation'] == parent_checkpoint['generation']
    final = out / 'confirmation'
    confirmed = json.loads((final / 'summary.json').read_text())
    for path, sha in {**summary['source_sha256'], **summary['input_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
    assert hashlib.sha256((out / 'frozen_selections.json.gz').read_bytes()).hexdigest() == summary['frozen_sha256'] == confirmed['frozen_sha256']
    assert hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest() == confirmed['search_summary_sha256']
    assert hashlib.sha256((ROOT / 'maze_evolution/foundation_pair_confirm.py').read_bytes()).hexdigest() == confirmed['source_sha256']
    software = FIXTURES / 'mazes.json.gz'
    assert hashlib.sha256(software.read_bytes()).hexdigest() == confirmed['software_fixture_sha256']
    assert file_sha(out / 'checkpoint_selections.json.gz') == summary['checkpoint_selections_sha256'] == confirmed['checkpoint_sha256']
    assert read_compressed(out / 'checkpoint_selections.json.gz') == {key: dict(config=s['config'], champion=s['common_archives']['current']['item']) for key, s in parents.items()}
    timecourse = json.loads((out / 'timecourse/freeze.json').read_text())
    assert file_sha(out / 'timecourse/selections.json.gz') == timecourse['selection_sha256'] == confirmed['timecourse_selection_sha256']
    assert timecourse['search_summary_sha256'] == file_sha(out / 'search_summary.json')
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
        parent = parents[key]
        for field in ('config', 'frozen', 'frozen_rank', 'frozen_rows', 'frozen_skills', 'initial_digests'):
            assert state[field] == parent[field], (key, field)
        assert state['history'][:summary['start_generation']] == parent['history']
        assert len(state['history']) == summary['rounds']
        assert state['serial'] == parent['serial'] + 84 * summary['additional_rounds']
        assert state['validation_events'] == parent['validation_events'] + sum(g % 8 == 0 for g in range(summary['start_generation'], summary['rounds']))
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
    for group in new_groups:
        low, high, prefix_low, prefix_high, tail = BANDS[group.level]
        for pair in group.pairs:
            for side, o in enumerate(pair.cases):
                label = o._foundation_label
                assert low <= len(o.path) - 1 <= high
                assert prefix_low <= label['distance'] <= prefix_high
                assert label['prefix'][0] == o.maze.start
                assert label['distance'] + o.to_goal[label['vertex']] == len(o.path) - 1
                assert o.to_goal[label['vertex']] >= tail
                assert all(o.to_goal[q] == o.to_goal[label['vertex']] - 1 for q in label['allowed'][side])
                assert not set(label['allowed'][0]) & set(label['allowed'][1])
    previous = exclusions()
    old = {layout_hash(Maze(bytes.fromhex(r['cells_hex']), r['w'], r['h'], r['start'], r['goal'])) for r in previous}
    assert len(old) == summary['excluded_layouts']
    owners = {}
    borrowed_cases = borrowed_validation(FoundationData(summary['seed'], previous)).cache
    schedule = FoundationData(summary['seed'])
    schedule.cache = cases
    schedule.groups = {g.key: g for g in groups}
    for group in groups:
        for pair in group.pairs:
            for o in pair.cases:
                h = layout_hash(o.maze)
                if group.key[0] == 'validation':
                    assert h in old and o.maze == borrowed_cases[o.maze.case_id].maze
                    assert o._foundation_label == borrowed_cases[o.maze.case_id]._foundation_label
                else:
                    assert h not in old
                assert owners.setdefault(h, group.identity) == group.identity
                label = o._foundation_label
                if label:
                    assert label['prefix'][0] == o.maze.start
                    assert label['distance'] + o.to_goal[label['vertex']] == len(o.path) - 1
    new_training_layouts = len(set(owners) - old)
    assert len(old | set(owners)) == summary['resulting_layouts']
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
    search_checks, reproduction, selection_changes, known = audit_search(evaluation_paths, lineage_paths, states, parents, cases, schedule, summary, checkpoint, parent_checkpoint)
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
        reproduction={k: v for k, v in reproduction.items() if k not in ('conditions', 'differing_parent_examples')}, **search_checks, final_rasters=final_checker.rasters,
        distinct_final_replays=len(replayed), reference_replays=references, replay_work=replay_work,
        search_layouts=new_training_layouts, borrowed_validation_layouts=len(owners)-new_training_layouts, final_layouts=len(final_owners), final_software_fixture_layouts=len(old)-summary['resulting_layouts'],
        elapsed_seconds=time.perf_counter() - started, max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        search_summary_sha256=hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest(),
        confirmation_summary_sha256=hashlib.sha256((final / 'summary.json').read_bytes()).hexdigest(),
        verifier_sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__), ROOT / 'maze_evolution/foundation_pair_replay.py', ROOT / 'maze_evolution/foundation_study_verify_core.py']})
    write_json(out / 'reproduction.json', reproduction)
    write_json(out / 'primary_selection_changes.json', dict(
        scope='Post-hoc descriptive analysis of logged validation selection; no new inference or tuning',
        events=selection_changes, changes=len(selection_changes),
        losing_adjacent_pairs=sum(v['lost_adjacent'] for v in selection_changes),
        losing_nonadjacent_pairs=sum(v['lost_nonadjacent'] for v in selection_changes)))
    write_json(out / 'verification.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
