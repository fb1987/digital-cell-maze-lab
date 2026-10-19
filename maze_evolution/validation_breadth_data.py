"""V12I: fixed-pool selection on equal-sized, differently clustered validation.

The three graphs within a context and its eight poses are correlated. All poses,
including unqueried validation poses, are saved and excluded from later draws.
"""
from dataclasses import replace
import random

from cellular_maze_lab import neighbors
from .datasets import seed_for, manifest
from .evaluator import Maze, Oracle, distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData, layout_hash, transform_maze, transform_point
from .foundation_study import read_compressed
from .fork_data import induced_arm
from .routing_transfer_data import detour, exclusions as old_exclusions, TransferData, load

SEED = 2026101904
FIXTURE_SEED = 1234
N = 25
PREFIXES = ((1, 3), (4, 8))
TAILS = ((3, 4), (5, 9))
FAMILIES = ('fork', 'two_junction', 'alternate_cycle')
OUT = ROOT / 'results/validation_breadth'
FIXTURES = ROOT / 'results/validation_breadth_fixtures'


def exclusions():
    rows = old_exclusions()
    for path in ('routing_transfer_fixtures/mazes.json.gz',
                 'routing_transfer/confirmation/mazes.json.gz'):
        rows.extend(read_compressed(ROOT / 'results' / path))
    rejected = ROOT/'results/validation_breadth_preflight/mazes.json.gz'
    if rejected.exists():
        rows.extend(read_compressed(rejected))
    return rows


def build(seed, namespace, index, stratum, salt):
    actual = seed_for(seed, namespace, index, salt)
    rng = random.Random(actual)
    junction = rng.randrange(6, N-6)*N + rng.randrange(6, N-6)
    opened = {junction}
    lengths = [rng.randint(*PREFIXES[stratum//2])]
    lengths += [rng.randint(*TAILS[stratum % 2]) for _ in range(2)]
    arms = []
    for length in lengths:
        arm = induced_arm(rng, N, opened, junction, length)
        if arm is None:
            return None
        arms.append(arm)
    prefix = list(reversed(arms[0]))
    # Join internal vertices on DIFFERENT goal arms, possible even with a
    # one-edge source prefix. The original arm route through J stays shorter.
    cross = list(reversed(arms[1])) + arms[2][1:]
    alternate = None
    for _ in range(8):
        proposal = detour(rng, opened, cross, N)
        if proposal is not None:
            i, j, alt = proposal
            # At least two edges from J on each arm: otherwise the illuminated
            # alternative contains the skipped J--attachment edge as a chord.
            if cross[i] in arms[1][2:-1] and cross[j] in arms[2][2:-1]:
                alternate = proposal
                break
    if alternate is None:
        return None
    i, j, alt = alternate
    a, b = arms[1].index(alt[0]), arms[2].index(alt[-1])
    paths = [prefix + arm[1:] for arm in arms[1:]]
    alternatives = [prefix + arms[2][1:b] + list(reversed(alt)) + arms[1][a+1:],
                    prefix + arms[1][1:a] + alt + arms[2][b+1:]]
    stub = alt[1:1+rng.randint(1, min(4, len(alt)-3))]
    full = opened | set(alt)
    clutter = set()
    possible = list(range(N*N)); rng.shuffle(possible)
    for p in possible:
        if (0 < p % N < N-1 and 0 < p//N < N-1 and p not in full | clutter
                and not any(q in full | clutter for q in neighbors(p, N, N))):
            clutter.add(p)
            if len(clutter) == 8:
                break
    if len(clutter) != 8:
        return None
    label = dict(vertex=junction, prefix=prefix, incoming=prefix[-2],
                 exits=[arms[1][1], arms[2][1]],
                 allowed=[[arms[1][1]], [arms[2][1]]], distance=lengths[0])
    meta = dict(start=prefix[0], goals=[arm[-1] for arm in arms[1:]],
                paths=paths, alternatives=alternatives, detour=alt,
                attachment=alt[0], merge=alt[-1], stub=stub,
                gaps=[len(x)-len(y) for x, y in zip(alternatives, paths)],
                clutter=sorted(clutter), decision=label, lengths=lengths)
    assert all(g > 0 for g in meta['gaps'])
    return actual, dict(fork=opened, two_junction=opened | set(stub),
                        alternate_cycle=full), meta


def transform_meta(meta, symmetry):
    conv = lambda p: transform_point(p, N, symmetry)
    result = dict(meta)
    for name in ('start', 'attachment', 'merge'):
        result[name] = conv(meta[name])
    for name in ('goals', 'detour', 'stub', 'clutter'):
        result[name] = list(map(conv, meta[name]))
    for name in ('paths', 'alternatives'):
        result[name] = [list(map(conv, path)) for path in meta[name]]
    d = meta['decision']
    result['decision'] = dict(vertex=conv(d['vertex']), prefix=list(map(conv, d['prefix'])),
        incoming=conv(d['incoming']), exits=list(map(conv, d['exits'])),
        allowed=[list(map(conv, path)) for path in d['allowed']], distance=d['distance'])
    return result


class BreadthData(TransferData):
    def context(self, split, index, stratum, cut=False):
        namespace = f'{split}/stratum{stratum}'
        for salt in range(4000):
            built = build(self.seed, namespace, index, stratum, salt)
            if built is None:
                continue
            actual, graphs, meta = built
            graphs.update({f'corridor_{s}': set(path) for s, path in enumerate(meta['paths'])})
            if cut:
                graphs['disconnected'] = graphs['alternate_cycle'] - {meta['decision']['vertex']}
            originals = {name: Maze(bytes(int(p in opened | set(meta['clutter'])) for p in range(N*N)),
                N, N, meta['start'], meta['goals'][0], name, actual, split, '')
                for name, opened in graphs.items()}
            orbit = {layout_hash(transform_maze(m, s)) for m in originals.values() for s in range(8)}
            if len(orbit) != 8*len(originals) or orbit & self.layouts:
                self.rejections += 1
                continue
            base = f'{namespace}/g{index}/s{salt}'
            context = dict(id=base, index=index, stratum=stratum, salt=salt, cut=cut, poses=[])
            for symmetry in range(8):
                transformed = transform_meta(meta, symmetry)
                pose = dict(symmetry=symmetry, meta=transformed, cases={})
                for family, m in originals.items():
                    sides = [int(family[-1])] if family.startswith('corridor_') else [0, 1]
                    ids = []
                    for side in sides:
                        cid = f'{base}/{family}/{"ab"[side]}'
                        o = Oracle.build(transform_maze(replace(m, goal=meta['goals'][side], case_id=cid), symmetry))
                        o._foundation_label = transformed['decision'] if family in FAMILIES else None
                        o._from_start = distances(o.maze, o.maze.start)
                        self.cache[o.maze.case_id] = o; ids.append(o.maze.case_id)
                        self.metadata[o.maze.case_id] = dict(base=base, index=index, stratum=stratum,
                            family='corridor' if family.startswith('corridor_') else family,
                            side=side, symmetry=symmetry)
                        assert (not o.path) == (family == 'disconnected')
                        if o.path:
                            assert o.path == transformed['paths'][side]
                    pose['cases'][family] = ids
                context['poses'].append(pose)
            self.layouts.update(orbit); self.contexts.append(context)
            return context
        raise RuntimeError(f'No unseen context: {namespace}/{index}')


def pose_inputs(pose, controls=True):
    families = (*FAMILIES, 'corridor_0', 'corridor_1') if controls else FAMILIES
    return [cid for name in families for cid in pose['cases'][name]]


def validation(data):
    schedule = {}
    for rep in range(3):
        arms = dict(narrow=[], broad=[])
        for stratum in range(4):
            # The exact same four poses per stratum in BOTH arms; each draw
            # alternates parity to balance rotations and reflections globally.
            poses = [((rep+stratum) % 2)+2*k for k in range(4)]
            c = data.context(f'validation/r{rep}/narrow', 0, stratum)
            arms['narrow'].extend(cid for s in poses for cid in pose_inputs(c['poses'][s]))
            for index, s in enumerate(poses):
                c = data.context(f'validation/r{rep}/broad', index, stratum)
                arms['broad'].extend(pose_inputs(c['poses'][s]))
        assert len(arms['narrow']) == len(arms['broad']) == 128
        schedule[str(rep)] = arms
    return schedule


def final(data):
    for stratum in range(4):
        for index in range(16):
            data.context('final', index, stratum, cut=index < 2)
    assert len(data.cache) == 4224
    return data
