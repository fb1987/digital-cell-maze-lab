"""Regression checks for the A1 domain change and exact continuation boundary."""
from copy import deepcopy
import json
import time

import pytest

from maze_evolution import deep_campaign as old
from maze_evolution import deep_campaign_a1 as new
from maze_evolution import deep_campaign_amendment as amendment
from maze_evolution.deep_campaign_data_a1 import cases_from_manifest
from maze_evolution.deep_campaign_store import Journal, packed, unpacked, hashed
from maze_evolution.foundation_study import read_compressed, compressed_json
from maze_evolution.routing_transfer import sha


def test_candidate_evaluation_selection_budget_and_replay_functions_are_unchanged():
    import inspect
    for name in ('evaluate_task', 'task_specs', 'reservation', 'run_stage',
                 'transition', 'replay_journal', 'worker_init'):
        assert inspect.getsource(getattr(old, name)) == inspect.getsource(getattr(new, name))


def test_generator_only_changes_perfect_domain():
    import inspect
    from maze_evolution import deep_campaign_data as d0
    from maze_evolution import deep_campaign_data_a1 as d1
    from maze_evolution.family_evolution_data import ordinary
    for name in ('batch', 'ordinary_training', 'cases_from_manifest'):
        assert inspect.getsource(getattr(d0, name)) == inspect.getsource(getattr(d1, name))
    # Assessment body matches after removing docstrings and normalizing its import.
    import ast
    a, b = ast.parse(inspect.getsource(ordinary)), ast.parse(inspect.getsource(d1.ordinary))
    a.body[0].body = a.body[0].body[1:]
    b.body[0].body = b.body[0].body[1:]
    for node in ast.walk(a):
        if isinstance(node, ast.ImportFrom) and node.module == 'goal_recovery':
            node.module = 'deep_campaign_perfect11'
    assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)


def test_capacity_cases_deterministic_trees_and_uniform_endpoint_construction():
    from cellular_maze_lab import neighbors
    from maze_evolution.deep_campaign_perfect11 import wilson_case
    from maze_evolution.foundation_data import layout_hash, transform_maze
    from maze_evolution.evaluator import distances
    cases = read_compressed(amendment.SETUP_A1 / 'capacity.json.gz')
    seen = set()
    assert len(cases) == 962
    for c in cases:
        m = wilson_case(1491, 'a1-capacity', 0, c['index']*4000+c['salt']).maze
        assert (m.cells.hex(), m.start, m.goal, m.seed) == (
            c['cells_hex'], c['start'], c['goal'], c['seed'])
        assert (m.w, m.h) == (11, 11) and sum(m.cells) == 49
        assert sum(sum(m.cells[q] for q in neighbors(p, 11, 11))
                   for p in range(121) if m.cells[p]) == 96
        assert sum(x >= 0 for x in distances(m, m.start)) == 49
        assert m.start != m.goal and m.cells[m.start] and m.cells[m.goal]
        orbit = {layout_hash(transform_maze(m, p)) for p in range(8)}
        assert orbit == set(c['layouts']) and not orbit & seen
        seen.update(orbit)


def test_fixture_domains_queries_orbits_and_exclusions():
    from maze_evolution.foundation_data import layout_hash
    extra = set(read_compressed(amendment.SETUP_A1 / 'additional_exclusions.json.gz')['hashes'])
    seen = set()
    for k in range(17):
        data = read_compressed(amendment.SETUP_A1 / f'fixture_{k:02d}.json.gz')
        cases = cases_from_manifest(data['mazes'])
        layouts = {layout_hash(c.maze) for c in cases.values()}
        assert layouts == set(data['new_layouts']) and not layouts & seen
        assert layouts <= extra
        seen.update(layouts)
        for cid, c in cases.items():
            f = data['metadata'][cid]['family']
            if f.startswith('ordinary_'):
                n = 11 if f == 'ordinary_perfect' else 9
                assert (c.maze.w, c.maze.h) == (n, n)
        if k == 16:
            ids = data['queries']['0']
            assert len(ids) == 648
            assert sum(data['metadata'][c]['family'] == 'ordinary_perfect' for c in ids) == 48
            assert sum(data['metadata'][c]['family'] == 'ordinary_random' for c in ids) == 48
        else:
            assert len(data['queries']['0']) == (18 if data['generation'] % 4 == 0 else 12)


def small_boundary(tmp_path, monkeypatch):
    monkeypatch.setattr(amendment, 'SETUP_A1', tmp_path)
    name = 'additional_exclusions.json.gz'
    compressed_json(tmp_path / name, {'hashes':['extra']})
    j = Journal(tmp_path)
    states = [{'generation':8268, 'rng':'unchanged'}]
    config = {'milestone':10000}
    j.initialize(config, states, {'old'})
    n = j.prepare({'kind':'train', 'generation':8267, 'new_layouts':[]}, [])
    chain = j.commit(n, states, [])
    reg = dict(registration_sha256='registered', original_config=config,
               boundary=dict(latest_stage=n, generation=8268, chain=chain,
                             state_sha256=hashed(packed(states)), usage=j.get('usage'),
                             layouts_sha256=hashed(packed(['old']))),
               files={'results/deep_campaign_amendment_a1/'+name:sha(tmp_path / name)})
    return j, reg, states


def test_atomic_binding_and_idempotent_resume_keep_exact_state_and_usage(tmp_path, monkeypatch):
    j, reg, states = small_boundary(tmp_path, monkeypatch)
    usage = j.get('usage')
    amendment.bind_amendment(j, reg)
    amendment.bind_amendment(j, reg)
    assert j.state() == states and j.get('usage') == usage
    assert j.layouts() == {'old', 'extra'}
    j.close()
    j = Journal(tmp_path)
    amendment.verify_amendment(j, reg)
    assert j.state() == states and j.get('usage') == usage
    bad = deepcopy(reg)
    bad['registration_sha256'] = 'different'
    with pytest.raises(ValueError, match='binding'):
        amendment.bind_amendment(j, bad)
    j.close()


@pytest.mark.parametrize('field', ['chain', 'state_sha256', 'usage', 'layouts_sha256'])
def test_wrong_initial_boundary_rejected_without_mutation(tmp_path, monkeypatch, field):
    j, reg, _ = small_boundary(tmp_path, monkeypatch)
    reg['boundary'][field] = {} if field == 'usage' else 'wrong'
    with pytest.raises(ValueError):
        amendment.bind_amendment(j, reg)
    assert j.get(amendment.KEY) is None and j.layouts() == {'old'}
    j.close()


def test_old_generator_or_wrong_phase_pending_stage_rejected(tmp_path, monkeypatch):
    j, reg, _ = small_boundary(tmp_path, monkeypatch)
    amendment.bind_amendment(j, reg)
    n = j.prepare(dict(kind='train', generation=8268, new_layouts=[],
                       mazes=[], metadata={}), [])
    with pytest.raises(ValueError, match='provenance'):
        amendment.verify_amendment(j, reg)
    j.db.execute('DELETE FROM stages WHERE n=?', (n,))
    j.db.commit()
    data = dict(kind='train', generation=8268, new_layouts=[], amendment='registered',
                mazes=[dict(case_id='x', w=9, h=9)],
                metadata={'x':{'family':'ordinary_perfect'}})
    j.prepare(data, [])
    with pytest.raises(ValueError, match='dimensions'):
        amendment.verify_amendment(j, reg)
    j.close()


def test_nested_backup_counts_against_storage_guard(tmp_path):
    config = json.loads((old.SETUP / 'config.json').read_text())
    (tmp_path / 'backups').mkdir()
    (tmp_path / 'backups' / 'copy').write_bytes(b'x'*1024)
    assert new.resource_reason(tmp_path, dict(config, storage_bytes=1000),
                               time.monotonic()) == 'storage'


def test_rehearsal_all_births_rng_and_recovery_are_verified():
    p = json.loads((amendment.SETUP_A1 / 'preflight.json').read_text())
    assert p['passed'] and p['resumed_after_two_receipts']
    assert p['replay']['transitions'] == 17
    assert p['replay']['births_replayed'] == 2496
    assert p['added_usage']['uncertain_attempts'] == 0
    assert p['scientific_rounds'] == 0 and p['discarded_rounds'] == 16
