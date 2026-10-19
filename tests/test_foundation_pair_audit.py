from copy import deepcopy
from io import StringIO
import json

import pytest

from maze_evolution.foundation_calibration import fixtures
from maze_evolution.foundation_pair import verified_parent, starting_states, state_key
from maze_evolution.foundation_pair_search import PairSearch, canonical
from maze_evolution.foundation_pair_replay import ReproductionAudit
from maze_evolution.foundation_pair_timecourse import boundary_aliases


def test_reproduction_replays_current_paired_resampling_and_detects_rng_corruption(tmp_path):
    parent, _ = verified_parent()
    states = starting_states(parent)
    pairs = [p for g in fixtures().groups.values() for p in g.pairs[:1]]
    for initial in [s for s in states if s['config']['topology'] == 'evolved' and s['config']['replicate'] == 0]:
        key = state_key(initial)
        path = tmp_path / 'state.json'
        path.write_text(json.dumps(initial))
        registry, evaluations = StringIO(), StringIO()
        search = PairSearch(initial['config'], [], registry, evaluations, path, resume=True)
        search.step(pairs, pairs, 1)
        final = canonical(search.state())
        lineage = [json.loads(line) for line in registry.getvalue().splitlines()]
        records = [json.loads(line) for line in evaluations.getvalue().splitlines()]
        train = [r for r in records if r['split'] == 'train']
        validated = [r for r in records if r['split'] == 'validation']
        replay = ReproductionAudit({key: initial}, {key: final}, lineage)
        replay.step(key, 865, train, validated, final['history'][-1])
        proof, _ = replay.finish()
        assert proof['registered'] == 84
        assert proof['mutations'] == (75 if initial['config']['method'] == 'evolution' else 0)
        corrupt = deepcopy(final)
        corrupt['history'][-1]['rng_sha256'] = '0' * 64
        replay = ReproductionAudit({key: initial}, {key: corrupt}, lineage)
        with pytest.raises(AssertionError):
            replay.step(key, 865, train, validated, corrupt['history'][-1])


def test_timecourse_zero_uses_checkpoint_and_later_common_archives():
    cfg = dict(study='foundation_pair_paired', topology='local', origin='fresh', method='evolution', replicate=0)
    key = '/'.join(str(cfg[k]) for k in ('study','topology','origin','method','replicate'))
    initial = {key: dict(common_archives={'paired': {'item': {'id': 'checkpoint'}}})}
    start, rounds = 865, 1005
    history = [{} for _ in range(rounds)]
    for generation in range(start, rounds):
        history[generation] = dict(common_archives={'paired': {'id': f'selection{generation}'}})
    aliases = boundary_aliases([dict(config=cfg, history=history)], start, rounds, initial)
    assert [a['additional_generation'] for a in aliases] == [0,48,128,140]
    assert [a['id'] for a in aliases] == ['checkpoint','selection912','selection992','selection1004']
