from copy import deepcopy
from io import StringIO
import json

from maze_evolution.foundation_calibration import fixtures
from maze_evolution.foundation_continuation import verified_parent
from maze_evolution.foundation_continuation_data import environments, PARENT
from maze_evolution.foundation_continuation_screen import replicate_screen, level_metrics
from maze_evolution.foundation_study import read_compressed, restore_searches
from maze_evolution.foundation_study_data import validation
from maze_evolution.foundation_study_search import SkillSearch


def canonical(value):
    return json.loads(json.dumps(value))


def test_all_parent_states_preserved_and_next_steps_match(tmp_path):
    parent, _ = verified_parent()
    (tmp_path / 'checkpoints').mkdir()
    restored = restore_searches(parent['states'], tmp_path, StringIO(), StringIO())
    assert [canonical(s.state()) for s in restored] == parent['states']
    pairs = [p for g in fixtures().groups.values() for p in g.pairs[:1]]
    # Exercise evolution/resampling and both topologies without new environments.
    for i in (0, 1, 2, 3, 4):
        state = parent['states'][i]
        path = tmp_path / f'direct{i}.json'
        path.write_text(json.dumps(state))
        direct = SkillSearch(state['config'], [], StringIO(), StringIO(), path, resume=True)
        direct.step(pairs, pairs, 1)
        restored[i].step(pairs, pairs, 1)
        assert canonical(direct.state()) == canonical(restored[i].state())
        assert direct.frozen.identity == state['frozen']['id']
        assert direct.next_generation == 443


def test_borrowed_validation_is_exact_and_restore_uses_no_new_cases():
    data = environments()
    assert data.previous_count == 52424 and len(data.groups) == 27 and len(data.cache) == 432
    parent_groups = json.loads((PARENT / 'groups.json').read_text())
    wanted = [g for g in parent_groups if g['key'][0] == 'validation']
    for g, old in zip(data.groups.values(), wanted):
        assert list(g.key) == old['key']
        assert [p.first.maze.case_id for p in g.pairs] == [p['first'] for p in old['pairs']]
        assert [p.first._foundation_label for p in g.pairs] == [p['decision'] for p in old['pairs']]
    before = set(data.layouts)
    for rep in range(3):
        assert len(validation(data, rep)) == 72
    assert data.layouts == before
    resumed = environments(saved_keys=list(map(list, data.groups)))
    assert resumed.layouts == data.layouts
    assert [o.maze for o in resumed.cache.values()] == [o.maze for o in data.cache.values()]


def test_stronger_screen_requires_gain_retention_and_robust_transfer():
    blank = {str(i): dict(pairs=0, groups_any=0, groups_all=0) for i in range(4)}
    c, old, random = deepcopy(blank), deepcopy(blank), deepcopy(blank)
    c['0']['pairs'] = 44
    c['1'].update(pairs=8, groups_any=1, groups_all=1)
    assert replicate_screen(c, old, random)['passes']
    c['0']['pairs'] = 43
    assert not replicate_screen(c, old, random)['passes']
    c['0']['pairs'] = 44
    c['1']['groups_all'] = 0
    assert not replicate_screen(c, old, random)['passes']
    c['2'].update(pairs=2, groups_any=2)
    assert replicate_screen(c, old, random)['passes']
    old['2']['pairs'] = 2
    assert not replicate_screen(c, old, random)['passes']
    old['2']['pairs'] = 0
    random['1']['pairs'] = 10
    assert not replicate_screen(c, old, random)['passes']  # ties do not pass


def test_screen_groups_count_paired_poses_not_individual_routes():
    rows = []
    for level in range(4):
        for group in range(6):
            for symmetry in range(8):
                for goal in ('a', 'b'):
                    rows.append(dict(case=f'confirmation/level{level}/g{group}/{goal}/d4-{symmetry}',
                        optimal=(goal == 'a' or group == 0), pair_optimal=(group == 0)))
    m = level_metrics(rows)
    assert all(v == dict(optimal=56, pairs=8, groups_any=1, groups_all=1) for v in m.values())
