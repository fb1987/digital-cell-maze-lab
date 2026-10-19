"""V12G minimal induced forks and matched pruned corridors, labels for fitness only."""
from dataclasses import dataclass, replace
import gzip
import json
import random

from cellular_maze_lab import neighbors
from .datasets import seed_for, manifest
from .evaluator import Maze, Oracle, distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData, Group, layout_hash, transform_maze, transform_point
from .goal_data import GoalPair
from .route_confirmation_data import exclusions as old_exclusions

SEED=2026101902
CONSTRUCTION_SEED=1214
OUT=ROOT/'results/fork_pressure'
FIXTURES=ROOT/'results/fork_pressure_fixtures'


def exclusions():
    rows=old_exclusions()
    for path in ('route_confirmation_fixtures/mazes.json.gz','route_confirmation/confirmation/mazes.json.gz'):
        with gzip.open(ROOT/'results'/path,'rt') as f:rows.extend(json.load(f))
    return rows


@dataclass(frozen=True)
class CorridorControls:
    """Matched single-route controls; these are NOT goal-switch pairs."""
    first: Oracle
    second: Oracle
    @property
    def cases(self):return self.first,self.second


def induced_arm(rng,n,opened,junction,length):
    path=[junction]
    for _ in range(length):
        possible=[q for q in neighbors(path[-1],n,n) if 1<q%n<n-2 and 1<q//n<n-2
            and q not in opened and sum(v in opened for v in neighbors(q,n,n))==1]
        if not possible:return None
        q=rng.choice(possible);path.append(q);opened.add(q)
    return path


def build(seed,namespace,rep,serial,stage,family,n):
    rng=random.Random(seed_for(seed,namespace,rep,serial))
    j=rng.randrange(4,n-4)*n+rng.randrange(4,n-4)
    opened={j};lo,hi=((1,2) if stage==0 else (2,4) if stage==1 else (4,7))
    lengths=[rng.randint(1,2 if stage==0 else 3),rng.randint(lo,hi),rng.randint(lo,hi)]
    arms=[]
    for length in lengths:
        path=induced_arm(rng,n,opened,j,length)
        if path is None:return None
        arms.append(path)
    if family=='cyclic':
        # Attach a one-cell-wide square loop to an existing arm by one edge.
        # The two shortest exits at the main decision junction remain disjoint.
        options=[]
        for p in sorted(opened):
            for direction in ((1,0),(-1,0),(0,1),(0,-1)):
                dx,dy=direction;px,py=-dy,dx;x,y=p%n,p//n
                loopcoords=[(x+dx*2,y+dy*2),(x+dx*3,y+dy*3),
                    (x+dx*4,y+dy*4),(x+dx*4+px,y+dy*4+py),
                    (x+dx*4+2*px,y+dy*4+2*py),(x+dx*3+2*px,y+dy*3+2*py),
                    (x+dx*2+2*px,y+dy*2+2*py),(x+dx*2+px,y+dy*2+py)]
                coords=[(x+dx,y+dy)]+loopcoords
                if not all(1<a<n-2 and 1<b<n-2 for a,b in coords):continue
                add={b*n+a for a,b in coords}
                if add&opened:continue
                contacts=[(q,v) for q in add for v in neighbors(q,n,n) if v in opened]
                if contacts!=[(coords[0][1]*n+coords[0][0],p)] and set(contacts)!={(coords[0][1]*n+coords[0][0],p)}:continue
                options.append(add)
        if not options:return None
        opened.update(rng.choice(options))
    # Eight isolated background cells prevent a finite catalogue of tiny path
    # shapes from exhausting whole-layout exclusions. Identical clutter is kept
    # in each pruned control; it carries no endpoint or route information.
    noise=set();possible=list(range(n*n));rng.shuffle(possible)
    for p in possible:
        if 0<p%n<n-1 and 0<p//n<n-1 and p not in opened|noise and not any(q in opened|noise for q in neighbors(p,n,n)):
            noise.add(p)
            if len(noise)==8:break
    if len(noise)!=8:return None
    cells=bytes(int(p in opened|noise) for p in range(n*n))
    m=Maze(cells,n,n,arms[0][-1],arms[1][-1],family,seed_for(seed,namespace,rep,serial),namespace,namespace)
    oracles=[Oracle.build(replace(m,goal=arm[-1])) for arm in arms[1:]]
    exits=[q for q in neighbors(j,n,n) if cells[q] and q!=arms[0][1]]
    allowed=[[q for q in exits if o.to_goal[q]+1==o.to_goal[j]] for o in oracles]
    if not all(allowed) or set(allowed[0])&set(allowed[1]):return None
    label=dict(vertex=j,prefix=list(reversed(arms[0])),incoming=arms[0][1],exits=exits,
        allowed=allowed,distance=len(arms[0])-1)
    return m,oracles,label,noise


class ForkData(FoundationData):
    def group(self,split,rep,index,stage,family='tree'):
        key=(split,rep,index,stage,family)
        if key in self.groups:return self.groups[key]
        n=13 if stage<2 else 21
        namespace=f'{split}/r{rep}/stage{stage}/{family}'
        for salt in range(4000):
            base=build(self.seed,namespace,rep,index*10000+salt,stage,family,n)
            if base is None:continue
            m,oracles,label,noise=base
            # The two pruned controls retain exactly each full shortest route.
            # They share the generator, endpoints and path with the corresponding fork.
            corridors=[replace(o.maze,cells=bytes(int(p in set(o.path)|noise) for p in range(n*n)),family='corridor') for o in oracles]
            orbit={layout_hash(transform_maze(x,s)) for x in [m,*corridors] for s in range(8)}
            if orbit&self.layouts:
                self.rejections+=1;continue
            identity=namespace+f'/g{index}/s{salt}';pairs=[];corridor_pairs=[]
            for symmetry in range(8):
                conv=lambda p:transform_point(p,n,symmetry)
                lab=dict(vertex=conv(label['vertex']),prefix=[conv(p) for p in label['prefix']],
                    incoming=conv(label['incoming']),exits=[conv(p) for p in label['exits']],
                    allowed=[[conv(p) for p in xs] for xs in label['allowed']],distance=label['distance'])
                group_cases=[];corridor_cases=[]
                for side,name in enumerate(('a','b')):
                    for original,suffix,decision,destination in ((oracles[side].maze,'',lab,group_cases),(corridors[side],'/corridor',None,corridor_cases)):
                        o=Oracle.build(transform_maze(replace(original,split=split,case_id=identity+suffix+'/'+name),symmetry))
                        o._foundation_label=decision;o._from_start=distances(o.maze,o.maze.start)
                        self.cache[o.maze.case_id]=o;destination.append(o)
                pairs.append(GoalPair(*group_cases));corridor_pairs.append(CorridorControls(*corridor_cases))
            self.groups[key]=Group(identity,stage,tuple(pairs),key)
            self.groups[key+('corridor',)]=Group(identity+'/corridor',stage,tuple(corridor_pairs),key+('corridor',))
            self.layouts.update(orbit)
            return self.groups[key]
        raise RuntimeError(f'No independent minimal-fork layout: {key}')

    def corridor(self,group):return self.groups[group.key+('corridor',)]


def validation(data,rep,split='validation'):
    pairs=[]
    for stage in (0,1):
        for family in ('tree','cyclic'):
            group=data.group(split,rep,0,stage,family)
            pairs.extend(group.pairs)
            pairs.extend(data.corridor(group).pairs[::2])
    return pairs


def batch(data,rep,generation):
    stage=0 if generation%4<3 else 1
    family='cyclic' if generation%4==2 else 'tree'
    g=data.group('train',rep,generation,stage,family)
    pose=(generation+rep)%8
    return [g.pairs[pose],g.pairs[(pose+4)%8],data.corridor(g).pairs[pose]]


def load(out):
    """Restore exact saved cases; never regenerate inspected test cases."""
    from pathlib import Path
    out=Path(out)
    with gzip.open(out/'mazes.json.gz','rt') as f:rows=json.load(f)
    cases={}
    for m in rows:
        o=Oracle.build(Maze(bytes.fromhex(m['cells_hex']),m['w'],m['h'],m['start'],m['goal'],m['family'],m['seed'],m['split'],m['case_id']))
        o._from_start=distances(o.maze,o.maze.start);cases[m['case_id']]=o
    groups=[]
    for g in json.loads((out/'groups.json').read_text()):
        pairs=[]
        for p in g['pairs']:
            a,b=cases[p['first']],cases[p['second']]
            a._foundation_label=b._foundation_label=p['decision']
            cls=CorridorControls if a.maze.cells!=b.maze.cells else GoalPair
            pairs.append(cls(a,b))
        groups.append(Group(g['id'],g['level'],tuple(pairs),tuple(g['key'])))
    return cases,groups


def cut_group(data,group):
    """Remove the labelled junction, disconnecting the source from both goals."""
    key=group.key+('cut',)
    if key in data.groups:return data.groups[key]
    pairs=[];orbit=set()
    for pair in group.pairs:
        cases=[]
        for o in pair.cases:
            cells=bytearray(o.maze.cells);cells[o._foundation_label['vertex']]=0
            c=Oracle.build(replace(o.maze,cells=bytes(cells),case_id=o.maze.case_id+'/cut',family='disconnected'))
            c._foundation_label=None;c._from_start=distances(c.maze,c.maze.start)
            assert not c.path
            orbit.add(layout_hash(c.maze));data.cache[c.maze.case_id]=c;cases.append(c)
        pairs.append(GoalPair(*cases))
    assert not orbit&data.layouts
    data.layouts.update(orbit);data.groups[key]=Group(group.identity+'/cut',-1,tuple(pairs),key)
    return data.groups[key]
