"""V12R Q-informed asymmetric matched forks; new whole layouts at every stage."""
import random
from copy import deepcopy
from cellular_maze_lab import neighbors
from .mutation_transition_data import N
from .shared_prefix_data import exclusions as through_P
from .foundation_data import FoundationData,layout_hash,transform_maze,transform_point
from .foundation_calibration import ROOT
from .foundation_study import read_compressed,compressed_json
from .datasets import seed_for,manifest
from .evaluator import Maze,Oracle,distances
from .branch_pressure_data import load

OUT=ROOT/'results/mutation_accessibility'
FIXTURES=ROOT/'results/mutation_accessibility_fixtures'
SEED=2026101913
FIXTURE_SEED=1324

def exclusions():
    rows=through_P()
    for p in ('shared_prefix/software_fixtures','shared_prefix_fixtures','shared_prefix/validation','shared_prefix/train','shared_prefix/confirmation'):
        rows+=read_compressed(ROOT/'results'/p/'mazes.json.gz')
    return rows

class AccessData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous);self.contexts=[];self.metadata={}

    def context(self,split,index,length,shape,prefixes=(0,1),stress=False):
        base=geometries(length,shape,stress)
        specs=[]
        for g0 in base:
            for prefix in prefixes:
                g=deepcopy(g0);g['prefix']=prefix;g['source']=g['stem'][prefix];pref=list(reversed(g['stem'][:prefix+1]))
                g['paths']=[pref+a[1:] for a in g['arms']]
                g['alternatives']=[pref+a[1:] if a else [] for a in g['alternatives']]
                specs.append(g)
        occupied=set(q for g in specs for q in g['cells'])
        namespace=f'{split}/{"stress" if stress else "core"}/a{length}/{shape}'
        for salt in range(4000):
            actual=seed_for(self.seed,namespace,index,salt);rng=random.Random(actual);noise=set();opts=list(range(N*N));rng.shuffle(opts)
            for p in opts:
                if 1<p%N<N-2 and 1<p//N<N-2 and p not in occupied|noise and not any(q in occupied|noise for q in neighbors(p,N,N)):
                    noise.add(p)
                    if len(noise)==8:break
            assert len(noise)==8
            template=f'{namespace}/c{index}/s{salt}';pending={};meta={}
            for g in specs:
                config=f'{template}/{g["graph"]}/p{g["prefix"]}'
                for pose in range(8):
                    conv=lambda p:transform_point(p,N,pose)
                    for family in ('paired','corridor','disconnected'):
                        for side in (0,1):
                            points=(set(g['paths'][side]) if family=='corridor' else set(g['cells']))|noise
                            goal=sorted(noise)[side] if family=='disconnected' else g['goals'][side]
                            m=transform_maze(Maze(bytes(int(p in points) for p in range(N*N)),N,N,g['source'],goal,family,actual,split,f'{config}/{family}/{side}'),pose)
                            pending[m.case_id]=m
                            meta[m.case_id]=dict(base=config,template=template,index=index,arm=list(length),shape=shape,stress=stress,prefix=g['prefix'],graph=g['graph'],family=family,side=side,pose=pose,junction=conv(g['junction']),path=list(map(conv,g['paths'][side])),alternative=list(map(conv,g['alternatives'][side])) if family=='paired' else [],clutter=list(map(conv,sorted(noise))))
            orbit={layout_hash(m) for m in pending.values()}
            if orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start)
                assert (not o.path)==(m.family=='disconnected'),cid
                if o.path:assert o.path==meta[cid]['path'],cid
                self.cache[cid]=o
            self.metadata.update(meta);self.layouts.update(orbit);self.contexts.append(dict(id=template,index=index,arm=list(length),shape=shape,stress=stress,prefixes=list(prefixes),seed=actual,clutter=sorted(noise),new_layouts=len(orbit)));return
        raise RuntimeError('No unseen R context')

    def save(self,path):
        path.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:compressed_json(path/f'{name}.json.gz',value)


def geometries(lengths,shape,stress=False):
    left,right=lengths;j=9*N+9
    arms=[]
    for sign,length in ((-1,left),(1,right)):
        arms.append([j+sign*k for k in range(length+1)] if shape=='straight' else [j+sign*k for k in range(length)]+[j+sign*(length-1)+N])
    stem=[j-k*N for k in range(6)] if shape=='straight' else [j,j-N,j-2*N,j-2*N+1,j-2*N+2,j-2*N+3]
    result=[]
    for graph in (('fork','two_junction','cycle') if stress else ('fork',)):
        cells=set(stem+arms[0]+arms[1]);alternative=[[],[]]
        if graph=='two_junction':cells|={j-2+N,j-2+2*N}
        if graph=='cycle':
            bridge=[j-2+k*N for k in range(5)]+[j-2+4*N+k for k in range(1,5)]+[j+2+k*N for k in range(3,-1,-1)]
            cells|=set(bridge);alternative=[[j]+arms[1][1:2]+list(reversed(bridge))+arms[0][3:],[j]+arms[0][1:2]+bridge+arms[1][3:]]
        result.append(dict(graph=graph,cells=sorted(cells),paths=arms,alternatives=alternative,junction=j,source=j,goals=[a[-1] for a in arms],stem=stem,arms=arms))
    return result


def create(seed,split,previous):
    d=AccessData(seed,previous)
    lengths=((2,2),(2,3),(3,4),(4,2))
    if split=='confirmation':lengths+=((4,6),(6,4))
    for pair in lengths:
        for shape in ('straight','turning'):
            for _ in range(2 if split=='confirmation' else 1):d.context(split,len(d.contexts),pair,shape,(0,1,2) if split=='confirmation' else (0,1))
    if split in ('fixture','confirmation'):
        for pair in ((4,6),(6,4)):
            for _ in range(2 if split=='confirmation' else 1):d.context(split,len(d.contexts),pair,'straight',(0,1,2),True)
    return d
