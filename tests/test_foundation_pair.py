from copy import deepcopy
from io import StringIO
import json
import random

from maze_evolution.foundation_calibration import fixtures
from maze_evolution.foundation_fitness import lexicase
from maze_evolution.foundation_pair import verified_parent, starting_states, restore_searches
from maze_evolution.foundation_pair_data import environments, BANDS, ConfirmationData, CONSTRUCTION_SEED
from maze_evolution.foundation_pair_screen import replicate_screen, level_metrics
from maze_evolution.foundation_pair_search import PairSearch, canonical, priority
from maze_evolution.foundation_study_search import SkillSearch
from maze_evolution.regulatory_search import Evaluation


def test_matched_forks_preserve_all_genomes_rng_and_archives(tmp_path):
    parent, _ = verified_parent()
    states = starting_states(parent)
    (tmp_path / 'checkpoints').mkdir()
    restored = restore_searches(states, tmp_path, StringIO(), StringIO())
    assert [canonical(s.state()) for s in restored] == states
    for p in parent['states']:
        if p['config']['origin'] != 'fresh':
            continue
        matches = [s for s in states if s['config']['parent_condition'] == '/'.join(str(p['config'][k])
            for k in ('study', 'topology', 'origin', 'method', 'replicate'))]
        assert len(matches) == (2 if p['config']['method'] == 'evolution' else 1)
        for s in matches:
            for field in ('population', 'rng_state', 'serial', 'history', 'skills', 'frozen_skills',
                          'competence', 'initial_digests', 'champion', 'frozen', 'champion_rows', 'frozen_rows'):
                assert s[field] == p[field]
            assert s['common_archives']['current']['item'] == s['common_archives']['paired']['item'] == p['champion']


def test_current_arm_reproduces_old_search_and_resume(tmp_path):
    parent, _ = verified_parent()
    states = starting_states(parent)
    pairs = [p for g in fixtures().groups.values() for p in g.pairs[:1]]
    for state in [s for s in states if s['config']['selection_policy'] == 'current' and s['config']['replicate'] == 0]:
        state = deepcopy(state)
        # Include a nomination/validation event on already excluded software inputs.
        state['next_generation'] = 872
        path = tmp_path / 'same.json'
        path.write_text(json.dumps(state))
        old = SkillSearch(state['config'], [], StringIO(), StringIO(), path, resume=True)
        fresh = PairSearch(state['config'], [], StringIO(), StringIO(), path, resume=True)
        old.step(pairs, pairs, 1)
        fresh.step(pairs, pairs, 1)
        a, b = canonical(old.state()), canonical(fresh.state())
        b.pop('common_archives')
        for key in set(b['history'][-1]) - set(a['history'][-1]):
            b['history'][-1].pop(key)
        assert a == b
        # PairSearch checkpoint round trip must continue with the same exact RNG/DNA.
        saved = canonical(fresh.state())
        path.write_text(json.dumps(saved))
        resumed = PairSearch(saved['config'], [], StringIO(), StringIO(), path, resume=True)
        fresh.step(pairs, pairs, 1)
        resumed.step(pairs, pairs, 1)
        assert canonical(fresh.state()) == canonical(resumed.state())


def test_pair_priority_changes_actual_recorded_tradeoff_order():
    from pathlib import Path
    packet = json.loads(Path('results/foundation_continuation/primary_selection_changes.json').read_text())
    changes = packet if isinstance(packet, list) else packet['events']
    reversed_count = 0
    for row in changes:
        if row['lost_nonadjacent'] and not row['lost_adjacent']:
            before, after = tuple(row['old_rank']), tuple(row['new_rank'])
            assert after > before
            assert priority(before, 'paired') > priority(after, 'paired')
            reversed_count += 1
    assert reversed_count == 4


def test_paired_arm_resume_preserves_population_and_rng(tmp_path):
    parent, _ = verified_parent()
    states = starting_states(parent)
    pairs = [p for g in fixtures().groups.values() for p in g.pairs[:1]]
    for state in [s for s in states if s['config']['selection_policy'] == 'paired' and s['config']['replicate'] == 0]:
        path = tmp_path / 'paired.json'
        path.write_text(json.dumps(state))
        first = PairSearch(state['config'], [], StringIO(), StringIO(), path, resume=True)
        first.step(pairs, pairs, 1)
        saved = canonical(first.state())
        path.write_text(json.dumps(saved))
        resumed = PairSearch(saved['config'], [], StringIO(), StringIO(), path, resume=True)
        first.step(pairs, pairs, 1)
        resumed.step(pairs, pairs, 1)
        assert canonical(first.state()) == canonical(resumed.state())


def test_case_priority_is_logically_redundant_given_complete_pair_implication():
    # P=1 entails both per-case correctness fields=1; changing their order alone
    # must not be mistaken for a new parent-filtering mechanism.
    rows = []
    for index, values in enumerate([[(1,1,0,.4),(0,0,0,.2)], [(1,1,1,1.),(1,1,1,1.)],
                                      [(0,0,0,0.),(1,1,0,.5)], [(1,0,0,.6),(1,0,0,.6)]]):
        ev = Evaluation((0,), values, (), [], 0)
        rows.append((ev, index))
    paired = [(Evaluation(ev.fitness, [(p,v,o,s) for v,o,p,s in ev.case_values], (), [], 0), item)
              for ev, item in rows]
    for seed in range(64):
        assert lexicase(random.Random(seed), rows) == lexicase(random.Random(seed), paired)


def test_borrowed_validation_and_new_exclusion_total():
    data = environments()
    assert data.previous_count == 85628 and len(data.cache) == 432 and len(data.groups) == 27
    resumed = environments(saved_keys=list(map(list, data.groups)))
    assert resumed.layouts == data.layouts
    assert [o.maze for o in resumed.cache.values()] == [o.maze for o in data.cache.values()]


def test_confirmation_fixture_bands_and_pose_labels():
    from maze_evolution.foundation_data import load_pairs
    from maze_evolution.foundation_pair_data import FIXTURES
    cases, groups = load_pairs(FIXTURES)
    assert len(groups) == 10 and len(cases) == 160
    for group in groups:
        low, high, p_low, p_high, tail = BANDS[group.level]
        for pair in group.pairs:
            for side, o in enumerate(pair.cases):
                label = o._foundation_label
                assert low <= len(o.path)-1 <= high
                assert p_low <= label['distance'] <= p_high
                assert o.to_goal[label['vertex']] >= tail
                assert label['distance'] + o.to_goal[label['vertex']] == len(o.path)-1
                assert all(o.to_goal[q] == o.to_goal[label['vertex']]-1 for q in label['allowed'][side])
            assert not set(pair.first._foundation_label['allowed'][0]) & set(pair.first._foundation_label['allowed'][1])


def test_gate_requires_longer_transfer_gain_and_same_model_retention():
    blank = {str(i): dict(pairs=0, groups_any=0, groups_all=0) for i in range(5)}
    current, old, resample, treatment = [deepcopy(blank) for _ in range(4)]
    old['1']['pairs'] = 20
    treatment['0']['pairs'] = 44
    treatment['1']['pairs'] = 18
    treatment['2'].update(pairs=9, groups_any=2, groups_all=1)
    assert replicate_screen(treatment, current, old, resample)['passes']
    for key, field, value in [('0','pairs',43), ('1','pairs',17), ('2','groups_any',1), ('2','groups_all',0)]:
        changed = deepcopy(treatment)
        changed[key][field] = value
        assert not replicate_screen(changed, current, old, resample)['passes']
    current['3']['pairs'] = 9
    assert not replicate_screen(treatment, current, old, resample)['passes']
    rows = [dict(case=f'confirmation/level{l}/g{g}/{goal}/d4-{s}', optimal=True, pair_optimal=True)
            for l in range(5) for g in range(6) for s in range(8) for goal in ('a','b')]
    assert all(v == dict(optimal=96, pairs=48, groups_any=6, groups_all=6) for v in level_metrics(rows).values())
