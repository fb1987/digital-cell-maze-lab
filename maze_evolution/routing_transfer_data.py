"""V12H matched branching/alternative-route graphs; all oracles are external.

One independently sampled context has the SAME endpoints, unique shortest paths,
clutter, board and poses under three graph complexities. A real alternate route
joins two internal prefix vertices and is at least two edges longer. Its truncated
arm supplies the two-junction tree. These three graphs are correlated controls,
not three independent discoveries.
"""
from collections import deque
from dataclasses import replace
import gzip
import json
import random

from cellular_maze_lab import neighbors
from .datasets import seed_for, manifest
from .evaluator import Maze, Oracle, distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData, layout_hash, transform_maze, transform_point
from .fork_data import induced_arm, exclusions as earlier_exclusions

SEED = 2026101903
CONSTRUCTION_SEED = 1224
N = 25
BANDS = ((5, 9), (10, 18))
FAMILIES = ('fork', 'two_junction', 'alternate_cycle')
OUT = ROOT / 'results/routing_transfer'
FIXTURES = ROOT / 'results/routing_transfer_fixtures'


def exclusions():
    rows = earlier_exclusions()
    for p in ('fork_pressure_fixtures/mazes.json.gz', 'fork_pressure/mazes.json.gz',
              'fork_pressure/confirmation/mazes.json.gz'):
        with gzip.open(ROOT/'results'/p, 'rt') as f:
            rows.extend(json.load(f))
    return rows


def detour(rng, opened, prefix, n):
    """Shortest induced free-space connection, strictly longer than its prefix.

    Used ONLY to generate stimuli, never at inference. Prohibiting contact with
    the rest of the graph makes a single chordless cycle; both alternatives have
    legal path rasters. Endpoints are internal (never source or goal junction).
    """
    candidates = [(i, j) for i in range(1, len(prefix)-3)
                  for j in range(i+2, min(len(prefix)-1, i+5))]
    rng.shuffle(candidates)
    for i, j in candidates:
        a, b = prefix[i], prefix[j]
        entries = [p for p in neighbors(a, n, n) if p not in opened
                   and {v for v in neighbors(p,n,n) if v in opened} == {a}]
        exits = [p for p in neighbors(b, n, n) if p not in opened
                 and {v for v in neighbors(p,n,n) if v in opened} == {b}]
        rng.shuffle(entries); rng.shuffle(exits)
        for entry in entries:
            for end in exits:
                if entry == end:
                    continue
                allowed = {p for p in range(n*n) if 1 < p%n < n-2 and 1 < p//n < n-2
                           and p not in opened and not any(v in opened for v in neighbors(p,n,n))}
                if not all(1 < p%n < n-2 and 1 < p//n < n-2 for p in (entry,end)):
                    continue
                allowed.update((entry,end))
                parent = {entry: None}; queue = deque([entry])
                while queue and end not in parent:
                    p = queue.popleft(); options = list(neighbors(p,n,n)); rng.shuffle(options)
                    for q in options:
                        if q in allowed and q not in parent:
                            parent[q] = p; queue.append(q)
                if end not in parent:
                    continue
                path = [end]
                while path[-1] != entry:
                    path.append(parent[path[-1]])
                path = [a, *reversed(path), b]
                gap = (len(path)-1) - (j-i)
                if 2 <= gap <= 12:
                    return i, j, path
    return None


def build(seed, namespace, index, band, salt):
    actual = seed_for(seed, namespace, index, salt)
    rng = random.Random(actual); n = N
    junction = rng.randrange(6,n-6)*n + rng.randrange(6,n-6)
    opened = {junction}
    source_length = rng.randint(4,5) if band == 0 else rng.randint(5,8)
    low,high = BANDS[band]
    lengths = [source_length] + [rng.randint(max(1,low-source_length),high-source_length) for _ in range(2)]
    arms = []
    for length in lengths:
        arm = induced_arm(rng,n,opened,junction,length)
        if arm is None:
            return None
        arms.append(arm)
    prefix = list(reversed(arms[0])); alternate = detour(rng,opened,prefix,n)
    if alternate is None:
        return None
    i,j,alt = alternate
    # Keep at least one missing cell between the truncated arm and its merge.
    stub = alt[1:1+rng.randint(1,min(4,len(alt)-3))]
    full = opened | set(alt)
    clutter = set(); possible = list(range(n*n)); rng.shuffle(possible)
    for p in possible:
        if (0 < p%n < n-1 and 0 < p//n < n-1 and p not in full|clutter
                and not any(q in full|clutter for q in neighbors(p,n,n))):
            clutter.add(p)
            if len(clutter) == 8:
                break
    if len(clutter) != 8:
        return None
    paths = [prefix + arm[1:] for arm in arms[1:]]
    alternatives = [path[:i] + alt + path[j+1:] for path in paths]
    graphs = dict(fork=opened, two_junction=opened|set(stub), alternate_cycle=full)
    goals = [arm[-1] for arm in arms[1:]]
    label = dict(vertex=junction, prefix=prefix, incoming=prefix[-2],
                 exits=[arms[1][1],arms[2][1]], allowed=[[arms[1][1]],[arms[2][1]]],
                 distance=source_length)
    meta = dict(start=prefix[0],goals=goals,paths=paths,alternatives=alternatives,
                detour=alt,attachment=prefix[i],merge=prefix[j],stub=stub,
                gap=len(alt)-1-(j-i),clutter=sorted(clutter),decision=label)
    return actual,graphs,meta


def transform_meta(meta,symmetry):
    conv = lambda p: transform_point(p,N,symmetry)
    label = meta['decision']
    return dict(start=conv(meta['start']),goals=list(map(conv,meta['goals'])),
        paths=[list(map(conv,x)) for x in meta['paths']],
        alternatives=[list(map(conv,x)) for x in meta['alternatives']],
        detour=list(map(conv,meta['detour'])),attachment=conv(meta['attachment']),
        merge=conv(meta['merge']),stub=list(map(conv,meta['stub'])),gap=meta['gap'],
        clutter=list(map(conv,meta['clutter'])),decision=dict(vertex=conv(label['vertex']),
        prefix=list(map(conv,label['prefix'])),incoming=conv(label['incoming']),
        exits=list(map(conv,label['exits'])),allowed=[list(map(conv,x)) for x in label['allowed']],
        distance=label['distance']))


class TransferData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous)
        self.contexts = []
        self.metadata = {}

    def context(self,split,index,band,cut=False):
        namespace = f'{split}/band{band}'
        for salt in range(4000):
            built = build(self.seed,namespace,index,band,salt)
            if built is None:
                continue
            actual,graphs,meta = built
            all_graphs = dict(graphs)
            all_graphs.update({f'corridor_{s}':set(path) for s,path in enumerate(meta['paths'])})
            if cut:
                all_graphs['disconnected'] = graphs['alternate_cycle'] - {meta['decision']['vertex']}
            originals = {name:Maze(bytes(int(p in cells|set(meta['clutter'])) for p in range(N*N)),
                N,N,meta['start'],meta['goals'][0],name,actual,split,'') for name,cells in all_graphs.items()}
            orbit = {layout_hash(transform_maze(m,s)) for m in originals.values() for s in range(8)}
            # No duplicated layout across families, controls, poses or old studies.
            if len(orbit) != 8*len(originals) or orbit & self.layouts:
                self.rejections += 1
                continue
            base = f'{namespace}/g{index}/s{salt}'
            context = dict(id=base,index=index,band=band,salt=salt,cut=cut,poses=[])
            for symmetry in range(8):
                transformed = transform_meta(meta,symmetry)
                pose = dict(symmetry=symmetry,meta=transformed,cases={})
                for family,m in originals.items():
                    sides = [int(family[-1])] if family.startswith('corridor_') else [0,1]
                    ids = []
                    for side in sides:
                        cid = f'{base}/{family}/{"ab"[side]}'
                        o = Oracle.build(transform_maze(replace(m,goal=meta['goals'][side],case_id=cid),symmetry))
                        o._foundation_label = transformed['decision'] if family in FAMILIES else None
                        o._from_start = distances(o.maze,o.maze.start)
                        self.cache[o.maze.case_id] = o; ids.append(o.maze.case_id)
                        self.metadata[o.maze.case_id] = dict(base=base,index=index,band=band,
                            family='corridor' if family.startswith('corridor_') else family,
                            side=side,symmetry=symmetry)
                        assert (not o.path) == (family=='disconnected')
                        if o.path:
                            assert o.path == transformed['paths'][side]
                    pose['cases'][family] = ids
                context['poses'].append(pose)
            self.layouts.update(orbit);self.contexts.append(context)
            return context
        raise RuntimeError(f'No independent context after 4000 attempts: {namespace}/{index}')

    def matrix(self,split,per_band,cut_per_band):
        for band in range(2):
            for index in range(per_band):
                self.context(split,index,band,index<cut_per_band)
        return self

    def save(self,out):
        out.mkdir(parents=True,exist_ok=True)
        for name,rows in (('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)):
            with gzip.open(out/f'{name}.json.gz','wt') as f:
                json.dump(rows,f,separators=(',',':'))


def load(out):
    def read(name):
        with gzip.open(out/f'{name}.json.gz','rt') as f:
            return json.load(f)
    cases = {}
    for m in read('mazes'):
        o = Oracle.build(Maze(bytes.fromhex(m['cells_hex']),m['w'],m['h'],m['start'],m['goal'],
            m['family'],m['seed'],m['split'],m['case_id']))
        o._from_start = distances(o.maze,o.maze.start)
        o._foundation_label = None
        cases[o.maze.case_id] = o
    contexts = read('contexts')
    for c in contexts:
        for p in c['poses']:
            for family,ids in p['cases'].items():
                for cid in ids:
                    cases[cid]._foundation_label = p['meta']['decision'] if family in FAMILIES else None
    return cases,contexts,read('metadata')
