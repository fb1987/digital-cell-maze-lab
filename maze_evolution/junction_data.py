"""V8: common decision-rich pairs; whole-layout exclusion through V7."""
import gzip,json,random
from .balance_data import BalanceData,prior_manifests as earlier_manifests
from .datasets import make_case,seed_for
from .evaluator import Maze,Oracle,distances
from .goal_data import GoalPair,layout_hash
from .goal_recovery import wilson_case
from .junction_fitness import decision


def prior_manifests(root):
    return earlier_manifests(root)+json.loads(gzip.open(root/'results/balanced_goal/mazes.json.gz','rt').read())


class JunctionData(BalanceData):
    def pair(self,split,replicate,index,n,family,max_distance=32):
        if family=='disconnected':return super().pair(split,replicate,index,n,family,max_distance)
        key=(split,replicate,index,n,family,max_distance)
        if key in self.pairs:return self.pairs[key]
        group='train' if split.startswith('train') else split
        # Half of pair indices explicitly require a misleading Manhattan bearing.
        require_detour=index%2==0
        for salt in range(4000):
            base=wilson_case(self.seed,split,replicate,index*10000+salt) if n==9 and family=='perfect' else make_case(self.seed,split,replicate,index*10000+salt,n,family)
            m=base.maze;lh=layout_hash(m)
            if lh in self.layouts:self.rejections+=1;continue
            d=distances(m,m.start);possible=[p for p,v in enumerate(d) if 8<=v<=max_distance]
            rng=random.Random(seed_for(self.seed,split+'-goals',replicate,index*10000+salt));rng.shuffle(possible)
            chosen=None
            for first in possible[:24]:
                between=distances(m,first)
                for second in [p for p in possible if p!=first and between[p]>=max(d[first],d[p])][:24]:
                    cases=[]
                    for label,goal in zip(('a','b'),(first,second)):
                        case=f'{split}/r{replicate}/p{index}/s{salt}/{family}/{n}x{n}/{label}'
                        cases.append(Oracle.build(Maze(m.cells,m.w,m.h,m.start,goal,family,m.seed,split,case)))
                    pair=GoalPair(*cases);label=decision(pair)
                    if label is not None and (not require_detour or any(label['detours'])):
                        chosen=pair;break
                if chosen is not None:break
            if chosen is None:self.rejections+=1;continue
            self.layouts[lh]=group;self.pairs[key]=chosen
            for o in chosen.cases:self.cache[o.maze.case_id]=o;self.single.owners[o.maze.digest]=group
            return chosen
        raise RuntimeError(f'Cannot construct independent V8 decision pair: {key}')

    def pair_manifest(self):
        return [{**r,'decision':decision(self.pairs[k])} for k,r in zip(self.pairs,super().pair_manifest())]
