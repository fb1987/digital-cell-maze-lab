"""New-phase maze construction. Oracles stay outside candidate inference."""
import random
from cellular_maze_lab import neighbors
from .datasets import make_case, seed_for, manifest
from .evaluator import Maze, Oracle, distances
from .family_evolution_data import AccessData
from .foundation_data import layout_hash, transform_maze
from .selectivity_data import SPECS


def wilson(root, split, index, n):
    assert n >= 5 and n % 2 == 1
    seed = seed_for(root, split + '/wilson', n, index)
    rng = random.Random(seed); side = (n-1)//2; count = side*side
    tree = {rng.randrange(count)}; edges = []
    def adjacent(p):
        return [q for q in (p-1,p+1,p-side,p+side) if 0 <= q < count
                and abs(p%side-q%side)+abs(p//side-q//side)==1]
    while len(tree) < count:
        path = [next(p for p in range(count) if p not in tree)]; positions = {path[0]:0}
        while path[-1] not in tree:
            q = rng.choice(adjacent(path[-1]))
            if q in positions:
                path = path[:positions[q]+1]; positions = {p:i for i,p in enumerate(path)}
            else:
                positions[q] = len(path); path.append(q)
        edges.extend(zip(path,path[1:])); tree.update(path)
    cells = bytearray(n*n)
    pixel = lambda p: (2*(p//side)+1)*n+2*(p%side)+1
    for p in tree: cells[pixel(p)] = 1
    for a,b in edges: cells[(pixel(a)+pixel(b))//2] = 1
    start, goal = rng.sample([p for p,v in enumerate(cells) if v],2)
    return Oracle.build(Maze(bytes(cells),n,n,start,goal,'perfect',seed,split,
                             f'{split}/{index}/perfect/{n}x{n}'))


def ordinary(d, split, specs, poses=(0,4)):
    queries = []
    for family,n,count in specs:
        for index in range(count):
            namespace = f'{split}/ordinary/{family}/{n}'
            for salt in range(4000):
                k = index*4000+salt
                o = wilson(d.seed,namespace,k,n) if family=='perfect' else make_case(d.seed,namespace,0,k,n,family)
                if family=='disconnected' and any(not any(o.maze.cells[q] for q in neighbors(p,n,n)) for p in (o.maze.start,o.maze.goal)):
                    d.rejections += 1; continue
                variants = [transform_maze(o.maze,p) for p in range(8)]
                orbit = {layout_hash(m) for m in variants}
                if orbit & d.layouts:
                    d.rejections += 1; continue
                for pose,m in enumerate(variants):
                    q = Oracle.build(m); q._from_start = distances(m,m.start)
                    assert bool(q.path) == (family!='disconnected')
                    d.cache[m.case_id] = q
                    d.metadata[m.case_id] = dict(family='ordinary_'+family,base=o.maze.case_id,
                        template=o.maze.case_id,index=index,pose=pose,path=q.path,prefix=-1,
                        graph=family,side=0,size=n)
                    if pose in poses: queries.append(m.case_id)
                d.layouts.update(orbit); break
            else: raise RuntimeError('New-phase ordinary construction exhausted')
    return queries


def confirmation(seed, previous, fixture=False):
    d = AccessData(seed,previous)
    specs = SPECS[:1] if fixture else SPECS*2
    for length,shape,stress in specs:
        d.context('fixture' if fixture else 'confirmation',len(d.contexts),length,shape,(0,1,2,4,8),stress)
    ids = [c for c,m in d.metadata.items() if
           (m['family']=='paired' and m['pose']%2==0) or
           (m['family']=='corridor' and m['pose']==0) or
           (m['family']=='disconnected' and m['prefix']==0 and m['pose']==0)]
    count = 2 if fixture else 32
    ids += ordinary(d,'fixture' if fixture else 'confirmation',
        [(f,n,count) for f,n in [('perfect',11),('perfect',15),('random',9),('random',15),('disconnected',9),('disconnected',15)]])
    return dict(kind='assessment',generation=0,mazes=manifest(d.cache.values()),metadata=d.metadata,
                contexts=d.contexts,queries=ids,new_layouts=sorted(d.layouts-set(previous)),
                seed=seed,fixture=fixture,rejections=d.rejections)
