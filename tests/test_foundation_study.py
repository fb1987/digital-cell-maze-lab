from dataclasses import asdict
from io import StringIO
import json
import random

from maze_evolution.foundation_calibration import fixtures, LIMITS
from maze_evolution.foundation_study import compressed_json, read_compressed, restore_searches
from maze_evolution.foundation_study_data import founders, advance, batch
from maze_evolution.foundation_study_search import SkillSearch, certified_levels
from maze_evolution.growth import random_genome


def test_skill_archive_and_global_checkpoint_resume_match(tmp_path):
    data = fixtures()
    pairs = [p for g in data.groups.values() for p in g.pairs[:1]]
    initial = [random_genome(random.Random(1215 + i)) for i in range(16)]
    config = dict(study='unit', topology='local', origin='fresh', method='evolution', replicate=0,
        seed=1215, population=16, immigrants=1, limits=asdict(LIMITS), goal_pulse=True,
        validation_every=1, validation_nominees=4, mutation_policy='single', round_checkpoint=True)
    searches = []
    for name in ('whole', 'split'):
        s = SkillSearch(config, initial, StringIO(), StringIO(), tmp_path / f'{name}.json')
        s.initialize(pairs)
        s.step(pairs, pairs)
        searches.append(s)
    packet = tmp_path / 'checkpoint.json.gz'
    compressed_json(packet, dict(states=[searches[1].state()]))
    (tmp_path / 'checkpoints').mkdir()
    resumed = restore_searches(read_compressed(packet)['states'], tmp_path, StringIO(), StringIO())[0]
    for s in (searches[0], resumed):
        for _ in range(2):
            s.step(pairs, pairs)
    assert json.loads(json.dumps(searches[0].state())) == json.loads(json.dumps(resumed.state()))
    assert len(resumed.skills) == len(resumed.frozen_skills) == 4
    assert resumed.frozen is not None


def test_native_fresh_founder_identity_and_rng_pairing():
    for topology in ('local', 'evolved'):
        a, refs, rng = founders('native', topology, 0)
        b, refs_b, rng_b = founders('native', topology, 0)
        assert a == b and refs == refs_b and rng == rng_b and len(a) == 96
        assert all('capacity_growth' in r['path'] for r in refs)
    a, refs, rng = founders('fresh', 'local', 1)
    b, refs_b, rng_b = founders('fresh', 'evolved', 1)
    assert a == b and refs == refs_b and rng == rng_b


def test_curriculum_requires_same_candidate_retention_and_shared_rounds(tmp_path):
    from types import SimpleNamespace
    levels, entered = [0, 0, 0], [0, 0, 0]
    s = SimpleNamespace(config={'replicate': 0}, key='unit', competence={'0': {'id': 'a', 'rates': {'0': 1}}})
    assert not advance(levels, entered, 19, [s])
    assert advance(levels, entered, 20, [s])[0]['level'] == 1
    assert not advance(levels, entered, 40, [s])
    assert certified_levels({'0': 1}) == [0]
    assert certified_levels({'0': .79, '1': 1}) == []
    assert certified_levels({'0': .8, '1': .9}) == [1]
    # Replay schedule generation deterministically on an already excluded fixture seed.
    from maze_evolution.foundation_data import FoundationData
    a, b = FoundationData(1210), FoundationData(1210)
    for g in (0, 7):
        x, y = batch(a, 0, g, 0), batch(b, 0, g, 0)
        assert len(x) == len(y) == 6
        assert [o.maze.digest for p in x for o in p.cases] == [o.maze.digest for p in y for o in p.cases]
        assert sum(not o.path for p in x for o in p.cases) == (1 if g == 7 else 0)
