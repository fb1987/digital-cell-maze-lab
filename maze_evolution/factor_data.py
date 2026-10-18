"""V5 data: fresh layouts; Wilson trees for every size9 perfect split."""
import gzip,json,random
from .datasets import make_case,seed_for
from .evaluator import Maze,Oracle,distances
from .goal_data import GoalPair,layout_hash,prior_manifests as earlier_manifests
from .goal_recovery import FinalData,wilson_case


def prior_manifests(root):
    return earlier_manifests(root)+json.loads(gzip.open(root/'results/goal_conditioning/mazes.json.gz','rt').read())


class FactorData(FinalData):
    def pair(self,split,replicate,index,n,family,max_distance=32):
        key=(split,replicate,index,n,family,max_distance)
        if key in self.pairs:return self.pairs[key]
        group='train' if split.startswith('train') else split
        for salt in range(4000):
            base=wilson_case(self.seed,split,replicate,index*10000+salt) if n==9 and family=='perfect' else make_case(self.seed,split,replicate,index*10000+salt,n,family)
            m=base.maze;lh=layout_hash(m)
            if lh in self.layouts:self.rejections+=1;continue
            d=distances(m,m.start);possible=[p for p,v in enumerate(d) if 8<=v<=max_distance]
            rng=random.Random(seed_for(self.seed,split+'-goals',replicate,index*10000+salt));rng.shuffle(possible)
            chosen=None
            if family=='disconnected':
                outside=[p for p,v in enumerate(d) if v<0 and m.cells[p]]
                if possible and outside:chosen=(possible[0],rng.choice(outside))
            else:
                for first in possible[:32]:
                    between=distances(m,first)
                    second=next((p for p in possible if p!=first and between[p]>=max(d[first],d[p])),None)
                    if second is not None:chosen=(first,second);break
            if chosen is None:self.rejections+=1;continue
            cases=[]
            for label,goal in zip(('a','b'),chosen):
                case=f'{split}/r{replicate}/p{index}/s{salt}/{family}/{n}x{n}/{label}'
                cases.append(Oracle.build(Maze(m.cells,m.w,m.h,m.start,goal,family,m.seed,split,case)))
            pair=GoalPair(*cases,family=='disconnected');self.layouts[lh]=group;self.pairs[key]=pair
            for o in cases:self.cache[o.maze.case_id]=o;self.single.owners[o.maze.digest]=group
            return pair
        raise RuntimeError(f'Cannot construct an independent V5 pair: {key}')

    def paired_tests(self,replicate):
        specs=[(n,f) for n in (9,17,33) for f in ('perfect','random')]+[(9,'disconnected'),(17,'disconnected')]
        return [self.pair('test_pairs',replicate,i,n,f,64) for i,(n,f) in enumerate(specs)]
