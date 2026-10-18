from dataclasses import asdict
from io import StringIO
import json
import random

from maze_evolution.foundation_calibration import fixtures, LIMITS
from maze_evolution.foundation_search import Search
from maze_evolution.foundation_repair_search import MutationSearch
from maze_evolution.growth import Genome, random_genome, replay_mutation


def test_wide_search_parity_single_trace_and_resumption(tmp_path):
    data = fixtures()
    pairs = next(g for g in data.groups.values() if g.level == 1).pairs[:4]
    initial = [random_genome(random.Random(1214 + i)) for i in range(16)]
    base = dict(study='unit-repair', topology='local', origin='random', method='evolution', replicate=0,
        seed=1214, population=16, immigrants=0, limits=asdict(LIMITS), goal_pulse=True,
        validation_every=1, validation_nominees=4, mutation_policy='wide')
    streams = {}
    def make(cls, name, policy='wide', resume=False):
        registry, log = StringIO(), StringIO()
        streams[name, resume] = registry, log
        search = cls({**base, 'mutation_policy': policy}, initial, registry, log,
                     tmp_path / f'{name}.json', resume)
        search.initialize(pairs)
        return search
    original, wide = make(Search, 'old'), make(MutationSearch, 'wide')
    single = make(MutationSearch, 'single', 'single')
    for _ in range(3):
        original.step(pairs, pairs)
        wide.step(pairs, pairs)
        single.step(pairs, pairs)
    assert original.state() == wide.state()
    assert single.responses == wide.responses and single.serial == wide.serial
    part = make(MutationSearch, 'part', 'single')
    part.step(pairs, pairs)
    resumed = make(MutationSearch, 'part', 'single', True)
    for _ in range(2):
        resumed.step(pairs, pairs)
    assert json.loads(json.dumps(single.state())) == json.loads(json.dumps(resumed.state()))
    genomes = {}
    for line in streams['single', False][0].getvalue().splitlines():
        row = json.loads(line)
        g = Genome.from_dict(row['genome'])
        if row['parent']:
            assert len(row['events']) == 1
            assert replay_mutation(genomes[row['parent']], row['events'], 256) == g
        genomes[row['id']] = g


def test_single_and_wide_resampling_are_identical(tmp_path):
    data = fixtures()
    pairs = next(iter(data.groups.values())).pairs[:1]
    initial = [random_genome(random.Random(1214 + i)) for i in range(16)]
    config = dict(study='unit-resampling', topology='local', origin='random', method='resample', replicate=0,
        seed=1214, population=16, immigrants=1, limits=asdict(LIMITS), goal_pulse=True,
        validation_every=1, validation_nominees=4)
    states = []
    for policy in ('wide', 'single'):
        search = MutationSearch({**config, 'mutation_policy': policy}, initial, StringIO(), StringIO(), tmp_path / f'{policy}.json')
        search.initialize(pairs)
        search.step(pairs, pairs)
        state = search.state()
        state['config'] = config
        states.append(state)
    assert states[0] == states[1]
