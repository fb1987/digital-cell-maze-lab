"""V12N elementary choice calibration, disjoint from every whole layout through M."""
import random
from cellular_maze_lab import neighbors
from .datasets import seed_for,manifest
from .evaluator import Maze,Oracle,distances
from .foundation_data import FoundationData,layout_hash,transform_point,transform_maze
from .foundation_calibration import ROOT
from .foundation_study import read_compressed,compressed_json
from .exposure_data import exclusions as through_L,load
from .exposure_study import all_manifests

OUT=ROOT/'results/branch_pressure_calibration'
FIXTURES=ROOT/'results/branch_pressure_calibration_fixtures'
SEED=2026101909
FIXTURE_SEED=1284
KINDS=('adjacent','two_edge','fork','three_edge','three_fork')
SHAPES=('straight','turning')


def exclusions():
    rows=through_L()
    for p in ('exposure_calibration_fixtures','exposure_calibration/calibration','exposure_calibration/validation','exposure_calibration/confirmation'):
        rows+=all_manifests(ROOT/'results'/p)
    return rows


class ChoiceData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous);self.contexts=[];self.metadata={}

    def context(self,split,index,kind,shape):
        n=9;j=40
        if kind=='adjacent':paths=[[j,j-1],[j,j+1 if shape=='straight' else j+n]];prefix=0
        elif kind=='two_edge':paths=[[j,j-1,j-2 if shape=='straight' else j-1-n],[j,j+1,j+2 if shape=='straight' else j+1+n]];prefix=0
        elif kind=='fork':
            source=j-n if shape=='straight' else j+n;paths=[[source,j,j-1],[source,j,j+1]];prefix=1
        elif kind=='three_edge':
            paths=[[j,j-1,j-2,j-3 if shape=='straight' else j-2-n],[j,j+1,j+2,j+3 if shape=='straight' else j+2+n]];prefix=0
        else:
            assert kind=='three_fork';source=j-n
            paths=[[source,j,j-1,j-2 if shape=='straight' else j-1+n],[source,j,j+1,j+2 if shape=='straight' else j+1+n]];prefix=1
        namespace=f'{split}/{kind}/{shape}'
        for salt in range(4000):
            actual=seed_for(self.seed,namespace,index,salt);rng=random.Random(actual);fork=set(sum(paths,[]));noise=set();opts=list(range(81));rng.shuffle(opts)
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
                        m=transform_maze(Maze(bytes(int(p in cells) for p in range(81)),n,n,paths[side][0],goal,family,actual,split,f'{base}/{family}/{side}'),pose)
                        pending[m.case_id]=m;ids[family].append(m.case_id)
                        meta[m.case_id]=dict(base=base,template=base,index=index,pose=pose,family=family,side=side,kind=kind,goal_shape=shape,prefix=prefix,
                            junction=conv(j),path=list(map(conv,paths[side])),clutter=list(map(conv,sorted(noise))))
                poses.append(dict(pose=pose,cases=ids))
            orbit={layout_hash(m) for m in pending.values()}
            if len(orbit)!=24 or orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start);assert (not o.path)==(m.family=='disconnected')
                if o.path:assert o.path==meta[cid]['path']
                self.cache[cid]=o
            self.metadata.update(meta);self.layouts.update(orbit);self.contexts.append(dict(id=base,index=index,kind=kind,goal_shape=shape,n=n,poses=poses));return
        raise RuntimeError('No unseen elementary geometry')

    def save(self,path):
        path.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:compressed_json(path/f'{name}.json.gz',value)


def create(seed,split,previous,repeats=1):
    d=ChoiceData(seed,previous)
    for kind in KINDS:
        for shape in SHAPES:
            for _ in range(repeats):d.context(split,len(d.contexts),kind,shape)
    return d


def query(data,full=False):return [cid for cid,m in data.metadata.items() if full or m['pose'] in (0,2,4,6)]
