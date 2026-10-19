from copy import deepcopy
import gzip
from io import StringIO
import json
import pytest

from maze_evolution.foundation_continuation_timecourse import boundary_aliases
from maze_evolution.foundation_continuation_audit import audit_ancestry
from maze_evolution.foundation_continuation import state_key
from maze_evolution.foundation_continuation_data import PARENT
from maze_evolution.foundation_study import read_compressed, restore_searches
from maze_evolution.foundation_calibration import fixtures


def test_continuation_timecourse_uses_absolute_history_and_checkpoint():
    cfg = dict(study='unit', topology='local', origin='fresh', method='evolution', replicate=0)
    state = dict(config=cfg, frozen={'id': 'initial'}, history=[{'champion': str(i)} for i in range(900)])
    aliases = boundary_aliases([state], 442, 800)
    assert [a['additional_generation'] for a in aliases] == [0, 48, 128, 256, 358]
    assert [a['id'] for a in aliases] == ['441', '489', '569', '697', '799']
    assert [a['generation'] for a in boundary_aliases([state], 442, 490)] == [442, 490]


def test_incremental_ancestry_starts_at_preserved_serial_and_rejects_corruption(tmp_path):
    state = read_compressed(PARENT / 'checkpoint.latest.json.gz')['states'][4]
    (tmp_path / 'checkpoints').mkdir()
    registry = StringIO()
    search = restore_searches([state], tmp_path, registry, StringIO())[0]
    pairs = [p for g in fixtures().groups.values() for p in g.pairs[:1]]
    search.step(pairs, pairs, 1)
    after = json.loads(json.dumps(search.state()))
    path = tmp_path / 'lineage.jsonl.gz'
    with gzip.open(path, 'wt') as f:
        f.write(registry.getvalue())
    key = state_key(state)
    counts, known = audit_ancestry([path], {key: after}, {key: state})
    assert counts['registered'] == 84 and counts['mutations'] == 75 and counts['immigrants'] == 9
    assert state['champion']['id'] in known
    corrupted = deepcopy(after)
    corrupted['frozen']['birth'] += 1
    with pytest.raises(AssertionError):
        audit_ancestry([path], {key: corrupted}, {key: state})
    rows = [json.loads(line) for line in registry.getvalue().splitlines()]
    rows[-1]['parent'] = 'unit/local/fresh/evolution/0/i0'
    with gzip.open(path, 'wt') as f:
        f.write('\n'.join(map(json.dumps, rows))+'\n')
    with pytest.raises(AssertionError):
        audit_ancestry([path], {key: after}, {key: state})
