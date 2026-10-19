"""V12M new selection/validation/final corpora; excludes every layout through L."""
import random
from collections import defaultdict
from cellular_maze_lab import neighbors
from .datasets import seed_for,manifest
from .evaluator import Maze,Oracle,distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData,layout_hash,transform_point,transform_maze
from .foundation_study import read_compressed,compressed_json
from .lineage_confirmation_data import LineageData,exclusions as old_exclusions,load as load_carry

OUT=ROOT/'results/exposure_calibration'
FIXTURES=ROOT/'results/exposure_calibration_fixtures'
SEED=2026101908
FIXTURE_SEED=1274


def exclusions():
    rows=old_exclusions()
    for p in ('lineage_confirmation_fixtures/mazes.json.gz','lineage_confirmation/confirmation/mazes.json.gz'):
        rows+=read_compressed(ROOT/'results'/p)
    return rows


def carry_corpus(data,split,final=False):
    specs=((1,'straight'),(2,'straight'),(4,'bent'))+(((8,'straight'),) if final else ())
    for shape in ('straight','turning','asymmetric'):
        for prefix,source in specs:data.template(split,len(data.contexts)//2,shape,prefix,source,True)


def carry_ids(data,final=False,profile=False):
    return [cid for cid,m in data.metadata.items() if (final or m['position']==0) and m['pose'] in ((0,) if profile else (0,2,4,6))]


class ElementaryData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous);self.contexts=[];self.metadata={}

    def context(self,split,index,kind,shape):
        n=9;namespace=f'{split}/{kind}/{shape}'
        for salt in range(1000):
            actual=seed_for(self.seed,namespace,index,salt);rng=random.Random(actual);j=4*n+4
            if kind=='adjacent':paths=[[j,j-1],[j,j+1 if shape=='straight' else j+n]];prefix=0
            elif kind=='two_edge':paths=[[j,j-1,j-2 if shape=='straight' else j-1-n],[j,j+1,j+2 if shape=='straight' else j+1+n]];prefix=0
            else:
                assert kind=='fork';source=j-n if shape=='straight' else j+n
                paths=[[source,j,j-1],[source,j,j+1]];prefix=1
            fork=set(sum(paths,[]));noise=set();opts=list(range(n*n));rng.shuffle(opts)
            for p in opts:
                if 0<p%n<n-1 and 0<p//n<n-1 and p not in fork|noise and not any(q in fork|noise for q in neighbors(p,n,n)):
                    noise.add(p)
                    if len(noise)==6:break
            if len(noise)<6:continue
            base=f'{namespace}/c{index}/s{salt}';pending={};meta={};poses=[];goals=[p[-1] for p in paths];unreachable=sorted(noise)[:2]
            for pose in range(8):
                conv=lambda p:transform_point(p,n,pose);ids={}
                for family in ('paired','corridor_0','corridor_1','disconnected'):
                    ids[family]=[]
                    for side in ([int(family[-1])] if family.startswith('corridor') else (0,1)):
                        cells=(set(paths[side]) if family.startswith('corridor') else fork)|noise
                        goal=unreachable[side] if family=='disconnected' else goals[side]
                        m=transform_maze(Maze(bytes(int(p in cells) for p in range(n*n)),n,n,paths[side][0],goal,family,actual,split,f'{base}/{family}/{side}'),pose)
                        pending[m.case_id]=m;ids[family].append(m.case_id)
                        meta[m.case_id]=dict(base=base,template=base,index=index,position=0,pose=pose,family=family,side=side,
                            kind=kind,goal_shape=shape,source_shape='straight',prefix=prefix,long=False,junction=conv(j),
                            path=list(map(conv,paths[side])),clutter=list(map(conv,sorted(noise))))
                poses.append(dict(pose=pose,cases=ids))
            orbit={layout_hash(m) for m in pending.values()}
            if len(orbit)!=24 or orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start)
                assert (not o.path)==(m.family=='disconnected')
                if o.path:assert o.path==meta[cid]['path']
                self.cache[cid]=o
            self.metadata.update(meta);self.layouts.update(orbit)
            c=dict(id=base,template=base,index=index,kind=kind,goal_shape=shape,n=n,poses=poses);self.contexts.append(c);return c
        raise RuntimeError('Could not construct elementary context')

    def save(self,path):
        path.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:compressed_json(path/f'{name}.json.gz',value)


def fresh_corpus(data,split,final=False):
    for kind in ('adjacent','two_edge','fork'):
        for shape in ('straight','turning'):
            for _ in range(4 if final else 1):data.context(split,len(data.contexts),kind,shape)


def fresh_ids(data,final=False,profile=False):
    return [cid for cid,m in data.metadata.items() if final or m['pose'] in ((0,) if profile else (0,2,4,6))]


def load(path):return load_carry(path)
