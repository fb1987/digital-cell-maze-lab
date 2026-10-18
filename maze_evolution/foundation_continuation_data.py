"""V12D environment stream; borrow V12C validation without rebuilding or retuning it."""
import gzip
import json
from .evaluator import Maze, Oracle, distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData, Group, layout_hash
from .foundation_study_data import exclusions as previous_exclusions
from .goal_data import GoalPair

SEED = 2026101816
PARENT = ROOT / 'results/foundation_study'
EXTRA_MANIFESTS = (
    PARENT / 'mazes.json.gz', PARENT / 'confirmation/mazes.json.gz',
    PARENT / 'confirmation/general_mazes.json.gz',
    ROOT / 'results/foundation_confirmation_fixtures/mazes.json.gz',
)


def exclusions():
    rows = previous_exclusions()
    for path in EXTRA_MANIFESTS:
        with gzip.open(path, 'rt') as f:
            rows.extend(json.load(f))
    return rows


def borrowed_validation(data, parent=PARENT):
    """Install only old validation, already excluded from every new layout stream."""
    groups = [g for g in json.loads((parent / 'groups.json').read_text()) if g['key'][0] == 'validation']
    wanted = {p[k] for g in groups for p in g['pairs'] for k in ('first', 'second')}
    with gzip.open(parent / 'mazes.json.gz', 'rt') as f:
        rows = [r for r in json.load(f) if r['case_id'] in wanted]
    assert len(rows) == len(wanted) == 432
    for r in rows:
        m = Maze(bytes.fromhex(r['cells_hex']), r['w'], r['h'], r['start'], r['goal'],
                 r['family'], r['seed'], r['split'], r['case_id'])
        assert layout_hash(m) in data.layouts
        o = Oracle.build(m)
        o._from_start = distances(m, m.start)
        data.cache[m.case_id] = o
    for g in groups:
        pairs = []
        for p in g['pairs']:
            a, b = data.cache[p['first']], data.cache[p['second']]
            a._foundation_label = b._foundation_label = p['decision']
            pairs.append(GoalPair(a, b, mixed=not (a.path and b.path)))
        key = tuple(g['key'])
        assert key not in data.groups
        data.groups[key] = Group(g['id'], g['level'], tuple(pairs), key)
    return data


def environments(previous=None, saved_keys=None):
    data = borrowed_validation(FoundationData(SEED, exclusions() if previous is None else previous))
    if saved_keys is not None:
        for key in saved_keys:
            if key[3] == -1:
                data.disconnected_group(key[0], key[1], key[2], key[5])
            else:
                data.group(*key)
        assert list(map(list, data.groups)) == saved_keys
    return data
