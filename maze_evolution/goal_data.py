"""V4 paired-goal environments. Oracles are confined to data/evaluation."""
from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path
import random
from .datasets import make_case, seed_for
from .evaluator import Maze, Oracle, distances
from .range_study import StudyData


def layout_hash(maze):
    return hashlib.sha256(f'{maze.w},{maze.h}:'.encode()+maze.cells).hexdigest()


def prior_manifests(root):
    paths=[root/'results/first_evolution/mazes.json',root/'results/range_and_regulation/mazes.json.gz',
           root/'results/source_pressure/mazes.json.gz']
    rows=[]
    for p in paths:
        with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f:
            rows.extend(json.load(f))
    return rows


@dataclass(frozen=True)
class GoalPair:
    first: Oracle
    second: Oracle
    mixed: bool=False

    @property
    def cases(self):
        return (self.first,self.second)

    def __post_init__(self):
        a,b=self.first.maze,self.second.maze
        if (a.cells,a.w,a.h,a.start)!=(b.cells,b.w,b.h,b.start) or a.goal==b.goal:
            raise ValueError('A goal pair must differ only in its goal')


class GoalData:
    def __init__(self,seed,previous=()):
        self.seed=seed
        self.cache={}; self.pairs={}; self.layouts={}; self.rejections=0
        hashes=[]
        for r in previous:
            m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'])
            self.layouts[layout_hash(m)]='previous'; hashes.append(r['sha256'])
        self.single=StudyData(seed,hashes)

    def pair(self,split,replicate,index,n,family,max_distance=32):
        key=(split,replicate,index,n,family,max_distance)
        if key in self.pairs:return self.pairs[key]
        group='train' if split.startswith('train') else split
        for salt in range(4000):
            base=make_case(self.seed,split,replicate,index*10000+salt,n,family)
            m=base.maze; lh=layout_hash(m)
            if lh in self.layouts:
                self.rejections+=1;continue
            d=distances(m,m.start)
            possible=[p for p,v in enumerate(d) if 8<=v<=max_distance]
            rng=random.Random(seed_for(self.seed,split+'-goals',replicate,index*10000+salt))
            rng.shuffle(possible)
            chosen=None
            if family=='disconnected':
                other=[p for p,v in enumerate(d) if v<0 and m.cells[p]]
                if possible and other:chosen=(possible[0],rng.choice(other))
            else:
                for first in possible[:32]:
                    between=distances(m,first)
                    second=next((p for p in possible if p!=first and between[p]>=max(d[first],d[p])),None)
                    if second is not None:
                        chosen=(first,second);break
            if chosen is None:
                self.rejections+=1;continue
            cases=[]
            for label,goal in zip(('a','b'),chosen):
                case_id=f'{split}/r{replicate}/p{index}/s{salt}/{family}/{n}x{n}/{label}'
                maze=Maze(m.cells,m.w,m.h,m.start,goal,family,m.seed,split,case_id)
                if maze.digest in self.single.owners:break
                cases.append(Oracle.build(maze))
            if len(cases)!=2:
                self.rejections+=1;continue
            result=GoalPair(*cases,family=='disconnected')
            self.layouts[lh]=group
            for case in cases:
                self.cache[case.maze.case_id]=case
                self.single.owners[case.maze.digest]=group
            self.pairs[key]=result
            return result
        raise RuntimeError(f'Cannot construct independent divergent goal pair: {key}')

    def batch(self,replicate,generation):
        n=9 if generation<24 else 17
        maximum=16 if n==9 else 32
        return [self.pair('train_goal',replicate,generation*2+i,n,
                         'disconnected' if i==1 and generation%4==3 else 'perfect' if i==0 else 'random',maximum)
                for i in range(2)]

    def validation(self,replicate):
        specs=[(n,f) for n in (9,17) for f in ('perfect','random','disconnected')]
        return [self.pair('validation_goal',replicate,i,n,f,32) for i,(n,f) in enumerate(specs)]

    def tests(self,replicate,samples=8):
        # A single endpoint per maze, without a minimum-distance condition.
        specs=[(n,f) for n in (9,17,33,65) for f in ('perfect','random') for _ in range(samples)]
        specs += [(n,'disconnected') for n in (9,17,33,65) for _ in range(4)]
        specs += [(n,'rectangular') for n in (9,17) for _ in range(4)]
        cases=[]
        for i,(n,family) in enumerate(specs):
            for salt in range(4000):
                oracle=self.single.case('test_goal',replicate,i*10000+salt,n,family)
                lh=layout_hash(oracle.maze)
                if lh in self.layouts:
                    # Rejected generated cases were never evaluated and are not
                    # added to the study manifest; their seeds remain deterministic.
                    self.rejections+=1;continue
                self.layouts[lh]='test_goal'
                self.cache[oracle.maze.case_id]=oracle; cases.append(oracle);break
            else:raise RuntimeError('Cannot generate an independent primary test')
        return cases

    def paired_tests(self,replicate):
        specs=[(n,f) for n in (9,17,33) for f in ('perfect','random')]+[(9,'disconnected'),(17,'disconnected')]
        return [self.pair('test_pairs',replicate,i,n,f,64) for i,(n,f) in enumerate(specs)]

    def pair_manifest(self):
        return [dict(first=p.first.maze.case_id,second=p.second.maze.case_id,mixed=p.mixed,
                     layout_sha256=layout_hash(p.first.maze)) for p in self.pairs.values()]
