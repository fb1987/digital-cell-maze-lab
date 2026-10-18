from dataclasses import asdict
from io import StringIO
import json
import random

import numpy as np
import pytest

from maze_evolution.datasets import manifest
from maze_evolution.evaluator import distances, assess
from maze_evolution.foundation_calibration import fixtures, controls, LIMITS
from maze_evolution.foundation_data import FoundationData, transform_maze, transform_point, load_pairs
from maze_evolution.foundation_fitness import evaluate, partial
from maze_evolution.foundation_search import Search
from maze_evolution.goal_data import layout_hash
from maze_evolution.growth import Genome, Individual, random_genome, replay_mutation
from maze_evolution.growth_runtime import Organism, observe
from maze_evolution.regulatory import Gene


@pytest.fixture(scope='module')
def data():
    return fixtures()


def test_orbits_anchor_distances_and_independent_layout_exclusion(data, tmp_path):
    for group in data.groups.values():
        original = group.pairs[0]
        for symmetry, pair in enumerate(group.pairs):
            for base, o in zip(original.cases, pair.cases):
                assert len(base.path) == len(o.path)
                assert transform_point(base.maze.start, base.maze.w, symmetry) == o.maze.start
            label = pair.first._foundation_label
            if label:
                for o, allowed in zip(pair.cases, label['allowed']):
                    assert all(o.to_goal[p] == o.to_goal[label['vertex']] - 1 for p in allowed)
                assert not set(label['allowed'][0]) & set(label['allowed'][1])
            else:
                assert pair.mixed and bool(pair.first.path) and not pair.second.path
    reused = FoundationData(data.seed, manifest(data.cache.values()))
    replacement = reused.group('fixture', 0, 0, 0)
    assert reused.rejections > 0
    assert all(layout_hash(p.first.maze) not in data.layouts for p in replacement.pairs)
    data.save(tmp_path)
    cases, groups = load_pairs(tmp_path)
    assert set(cases) == set(data.cache)
    assert [g.identity for g in groups] == [g.identity for g in data.groups.values()]
    restored = FoundationData.restore(data.seed, tmp_path)
    assert restored.layouts == data.layouts
    assert restored.group('fixture', 0, 0, 0).identity == data.group('fixture', 0, 0, 0).identity
    fresh_a = data.group('resume_fixture', 0, 0, 1)
    fresh_b = restored.group('resume_fixture', 0, 0, 1)
    assert [p.first.maze.digest for p in fresh_a.pairs] == [p.first.maze.digest for p in fresh_b.pairs]


def test_current_solver_pulse_controls_and_normal_observer_parity(data):
    item = controls()['intact']
    pairs = [p for g in data.groups.values() for p in g.pairs]
    for topology in ('local', 'evolved'):
        for pulse in (False, True):
            ev = evaluate(item, pairs, topology, LIMITS, pulse)
            assert all(r['optimal'] or r['no_path'] for r in ev.rows)
    pair = next(g for g in data.groups.values() if g.level == 3).pairs[0]
    organism = Organism(item.genome, 'local', LIMITS, goal_pulse=True)
    for o in pair.cases:
        m = o.maze
        r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
        obs = observe(organism, m.cells, m.w, m.h, m.start, m.goal, 64, True, False)
        assert np.array_equal(r.mask, obs.state[2] > 0)
        assert (r.steps, r.status, r.dispatches, r.spatial_reads) == (obs.steps, obs.status, obs.dispatches, obs.reads)
        assert r.steps == 2 * (len(o.path) - 1) + 1


def test_endpoint_rule_succeeds_only_at_elementary_level_and_partial_is_symmetric(data):
    endpoint = Individual('unit/endpoint', Genome((Gene(10, 12, 9, 10), Gene(13, 2, 12), Gene(13, 7, 11))), None, 0)
    for group in data.groups.values():
        ev = evaluate(endpoint, group.pairs, 'local', LIMITS)
        if group.level == 0:
            assert all(r['optimal'] for r in ev.rows)
            pair = group.pairs[0]
            m = pair.first.maze
            mask = np.zeros(len(m.cells), np.uint8)
            mask[[m.start, m.goal]] = 1
            correct_score = partial(mask, pair.first)
            mask[pair.second.maze.goal] = 1
            assert partial(mask, pair.first) < correct_score
        elif group.level > 0:
            assert not any(r['valid'] for r in ev.rows)
        if group.level == 2:
            original = group.pairs[0].first
            mask = np.zeros(len(original.maze.cells), np.uint8)
            mask[original.path[-3:]] = 1
            score = partial(mask, original)
            assert 0 < score < .9
            for symmetry, pair in enumerate(group.pairs):
                rotated = np.zeros(len(mask), np.uint8)
                for p in np.flatnonzero(mask):
                    rotated[transform_point(int(p), original.maze.w, symmetry)] = 1
                assert partial(rotated, pair.first) == pytest.approx(score)
            walls = np.flatnonzero(np.asarray(list(original.maze.cells)) == 0)
            mask[walls[0]] = 1
            assert partial(mask, original) == 0


def test_search_resume_lineage_and_resampling_budgets(data, tmp_path):
    pairs = next(iter(data.groups.values())).pairs[:2]
    initial = [random_genome(random.Random(1200 + i)) for i in range(16)]
    config = dict(study='unit', topology='local', origin='random', method='evolution', replicate=0,
                  seed=1200, population=16, immigrants=1, limits=asdict(LIMITS), goal_pulse=True,
                  validation_every=1, validation_nominees=4)
    logs = {}
    def create(name, method='evolution', resume=False):
        registry, evaluations = StringIO(), StringIO()
        search = Search({**config, 'method': method}, initial, registry, evaluations,
                        tmp_path / f'{name}.json', resume)
        logs[name, resume] = (registry, evaluations)
        search.initialize(pairs)
        return search
    full = create('full')
    for _ in range(3):
        full.step(pairs, pairs)
    part = create('part')
    part.step(pairs, pairs)
    continued = create('part', resume=True)
    for _ in range(2):
        continued.step(pairs, pairs)
    # JSON canonicalization removes tuple/list differences after checkpoint loading.
    assert json.loads(json.dumps(full.state())) == json.loads(json.dumps(continued.state()))
    sampled = create('sampled', 'resample')
    for _ in range(3):
        sampled.step(pairs, pairs)
    assert sampled.responses == full.responses and sampled.serial == full.serial
    records = [json.loads(line) for line in logs['full', False][0].getvalue().splitlines()]
    genomes = {}
    for row in records:
        g = Genome.from_dict(row['genome'])
        if row['events'] is not None:
            assert replay_mutation(genomes[row['parent']], row['events'], 256) == g
        genomes[row['id']] = g
    sampled_records = [json.loads(line) for line in logs['sampled', False][0].getvalue().splitlines()]
    assert all(r['parent'] is None and r['events'] is None for r in sampled_records)
    assert all(h['mutations'] == 13 and h['resamples'] == 1 for h in full.history)


def test_graded_defects_are_explicit_and_do_not_include_intact_founders():
    models = controls()
    assert len({i.genome.digest for i in models.values()}) == len(models)
    base = models['intact'].genome.genes
    for name, count in (('west_return_gate', 1), ('output_register', 1), ('two_return_gates', 2)):
        assert sum(a != b for a, b in zip(base, models[name].genome.genes)) == count


def test_independent_raster_and_score_auditor_rejects_corruption(data):
    import copy
    from maze_evolution.foundation_calibration_audit import check_rows
    pairs = next(iter(data.groups.values())).pairs[:2]
    ev = evaluate(controls()['west_return_gate'], pairs, 'local', LIMITS)
    assert check_rows(ev.rows, data.cache) == (ev.fitness, ev.work)
    wrong = copy.deepcopy(ev.rows)
    wrong[0]['valid'] = not wrong[0]['valid']
    with pytest.raises(AssertionError):
        check_rows(wrong, data.cache)
    wrong = copy.deepcopy(ev.rows)
    wrong[0]['partial'] += .01
    with pytest.raises(AssertionError):
        check_rows(wrong, data.cache)
