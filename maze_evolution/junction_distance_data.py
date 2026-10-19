"""V12J matched first/second-junction distances; no candidate-dependent generation."""
from dataclasses import replace
import random

from cellular_maze_lab import neighbors
from .datasets import manifest, seed_for
from .evaluator import Maze, Oracle, distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData, layout_hash, transform_maze, transform_point
from .foundation_study import compressed_json, read_compressed
from .validation_breadth_data import exclusions as old_exclusions

OUT = ROOT/'results/junction_distance'
FIXTURES = ROOT/'results/junction_distance_fixtures'
SEED, FIXTURE_SEED, N = 2026101905, 1244, 25
PREFIXES = (1, 2, 4, 6, 8)
BRANCHES = ('fork', 'two_2', 'two_4', 'cycle_2', 'cycle_4')
FAMILIES = (*BRANCHES, 'corridor_0', 'corridor_1', 'disconnected')


def exclusions():
    rows = old_exclusions()
    for path in ('validation_breadth_fixtures/mazes.json.gz',
                 'validation_breadth/validation/mazes.json.gz',
                 'validation_breadth/confirmation/mazes.json.gz'):
        rows.extend(read_compressed(ROOT/'results'/path))
    return rows


def build(seed, split, index, salt):
    actual = seed_for(seed, split, index, salt)
    rng = random.Random(actual)
    x, y = rng.randint(10, 14), rng.randint(10, 14)
    j = y*N+x
    tails = [rng.randint(6, 9), rng.randint(6, 9)]
    depth = rng.randint(3, 5)
    bend = -1 if index % 2 == 0 else 1
    arms = [[j+sign*k for k in range(t+1)] for sign,t in zip((-1,1), tails)]
    prefixes = dict(straight=[j-k*N for k in range(9)],
        bent=[j-k*N for k in range(4)] + [j-3*N+bend*k for k in range(1,6)])
    detours = {}
    for d in (2,4):
        detours[d] = ([j-d+k*N for k in range(depth+1)]
            + [j-d+depth*N+k for k in range(1,2*d+1)]
            + [j+d+k*N for k in range(depth-1,-1,-1)])
    union = set(sum(arms, []) + sum(prefixes.values(), []) + sum(detours.values(), []))
    clutter = set(); possible = list(range(N*N)); rng.shuffle(possible)
    for p in possible:
        if (0 < p % N < N-1 and 0 < p//N < N-1 and p not in union|clutter
                and not any(q in union|clutter for q in neighbors(p,N,N))):
            clutter.add(p)
            if len(clutter) == 10: break
    assert len(clutter)==10
    variants = []
    for shape,arm in prefixes.items():
        for length in PREFIXES:
            prefix = list(reversed(arm[:length+1]))
            paths = [prefix+a[1:] for a in arms]
            fork = set(sum(paths, []))
            graphs = dict(fork=fork, corridor_0=set(paths[0]), corridor_1=set(paths[1]),
                          disconnected=fork-{j})
            alternatives = {}
            for d,alt in detours.items():
                graphs[f'two_{d}'] = fork | {j-d+N,j-d+2*N}
                graphs[f'cycle_{d}'] = fork | set(alt)
                alternatives[f'cycle_{d}'] = [prefix+arms[1][1:d]+list(reversed(alt))+arms[0][d+1:],
                                              prefix+arms[0][1:d]+alt+arms[1][d+1:]]
            variants.append(dict(shape=shape, prefix=length, paths=paths,
                graphs={f:sorted(graphs[f]|clutter) for f in FAMILIES}, alternatives=alternatives,
                junction=j, goals=[a[-1] for a in arms], source=prefix[0],
                clutter=sorted(clutter), tails=tails, depth=depth, bend=bend,
                prefix_path=prefix, second_junctions={str(d):j-d for d in (2,4)}))
    return actual, variants


class DistanceData(FoundationData):
    def __init__(self, seed, previous=()):
        super().__init__(seed,previous)
        self.metadata = {}; self.contexts = []

    def context(self, split, index):
        for salt in range(100):
            actual, variants = build(self.seed,split,index,salt)
            base = f'{split}/c{index}/s{salt}'
            pending = {}; metadata = {}; saved = []
            for v in variants:
                for pose in range(8):
                    conv = lambda p: transform_point(p,N,pose)
                    ids = {}
                    for family in FAMILIES:
                        sides = [int(family[-1])] if family.startswith('corridor') else [0,1]
                        ids[family] = []
                        for side in sides:
                            cid = f'{base}/{v["shape"]}/p{v["prefix"]}/{family}/{side}'
                            m = transform_maze(Maze(bytes(int(p in v['graphs'][family]) for p in range(N*N)),
                                N,N,v['source'],v['goals'][side],family,actual,split,cid),pose)
                            pending[m.case_id] = m; ids[family].append(m.case_id)
                            metadata[m.case_id] = dict(base=base,index=index,shape=v['shape'],prefix=v['prefix'],
                                family=family,side=side,pose=pose,junction=conv(v['junction']),
                                second_junctions={d:conv(p) for d,p in v['second_junctions'].items()},
                                path=list(map(conv,v['paths'][side])),
                                alternative=list(map(conv,v['alternatives'][family][side])) if family in v['alternatives'] else [],
                                clutter=list(map(conv,v['clutter'])),tails=v['tails'],depth=v['depth'],bend=v['bend'])
                    saved.append(dict(shape=v['shape'],prefix=v['prefix'],pose=pose,cases=ids))
            orbit = {layout_hash(m) for m in pending.values()}
            if orbit & self.layouts:
                self.rejections+=1; continue
            # Straight and bent prefixes of length 1/2 deliberately coincide.
            for cid,m in pending.items():
                o = Oracle.build(m); o._from_start=distances(m,m.start)
                assert (not o.path)==(m.family=='disconnected')
                if o.path: assert o.path==metadata[cid]['path']
                self.cache[cid]=o
            self.metadata.update(metadata);self.layouts.update(orbit)
            self.contexts.append(dict(id=base,index=index,salt=salt,variants=saved))
            return
        raise RuntimeError('Could not construct unseen context')

    def save(self,out):
        out.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('metadata',self.metadata),('contexts',self.contexts)]:
            compressed_json(out/f'{name}.json.gz',value)


def load(out):
    cases = {}
    for r in read_compressed(out/'mazes.json.gz'):
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        o=Oracle.build(m);o._from_start=distances(m,m.start);cases[m.case_id]=o
    return cases,read_compressed(out/'contexts.json.gz'),read_compressed(out/'metadata.json.gz')
