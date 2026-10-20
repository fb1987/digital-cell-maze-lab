"""V12Z matched geometry with extended stems and nonisolated disconnected goals."""
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

OUT=ROOT/'results/family_evolution'
FIXTURES=ROOT/'results/family_evolution_fixtures'
SEED=2026102004
FIXTURE_SEED=1434
LENGTHS=((2,2),(2,3),(3,4),(4,2),(4,6),(6,4))

def exclusions():
    packet=read_compressed(ROOT/'results/linkage_restart/whole_layout_exclusions.json.gz')
    assert packet['count']==len(set(packet['hashes']))==255356
    return set(packet['hashes'])

class AccessData(FoundationData):
    def __init__(self,seed,previous=()):
        FoundationData.__init__(self,seed);self.layouts=set(previous);self.previous_count=len(self.layouts);self.contexts=[];self.metadata={}

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
                    q=p+1
                    if q not in occupied|noise and not any(v in occupied|noise for v in neighbors(q,N,N)):
                        noise.update((p,q))
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
    stem=[j-k*N for k in range(9)] if shape=='straight' else [j,j-N]+[j-2*N+k for k in range(7)]
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
    repeats=2 if split=='confirmation' else 1
    for length in LENGTHS[:4]:
        for shape in ('straight','turning'):
            for _ in range(repeats):d.context(split,len(d.contexts),length,shape,(0,1,2,4,8))
    for length in ((4,6),(6,4)):
        for _ in range(repeats):d.context(split,len(d.contexts),length,'straight',(0,1,2,4,8),True)
    ordinary(d,split)
    return d

# Pure schedule helper uses this object's context method; no old output paths.
from .composition_data import training_batch,clear_batch

def schedule_fixture(previous):
    d=AccessData(FIXTURE_SEED+1,previous);cache={};meta={};contexts=[]
    for g in range(96):
        ids=set(training_batch(d,g))
        for cid,m in d.metadata.items():m['audit_generation']=g if cid in ids else -1
        cache.update(d.cache);meta.update(d.metadata);contexts+=d.contexts;clear_batch(d)
    d.cache=cache;d.metadata=meta;d.contexts=contexts;return d

def add_layouts(previous,path):
    from .evaluator import Maze
    cases,_,_=load(path)
    previous.update(layout_hash(o.maze) for o in cases.values())
    return previous

def ordinary(d,split):
    """Final-only ordinary transfer:48 reachable/16 disconnected bases,all8poses.

Fixtures cover the same software construction.9x9 prevents ordinary path lengths
alone exceeding the native256tick limit of the separate intact control.
Disconnected controls have a partition construction bias, explicitly reported.
"""
    from .datasets import make_case
    from .foundation_data import layout_hash,transform_maze
    from .evaluator import Oracle,distances
    for family,count in (('perfect',24),('random',24),('disconnected',16)):
        for index in range(count):
            for salt in range(4000):
                if family=='perfect':
                    from .goal_recovery import wilson_case
                    o=wilson_case(d.seed,split+'/ordinary/'+family,0,index*4000+salt)
                else:o=make_case(d.seed,split+'/ordinary/'+family,0,index*4000+salt,9,family)
                if family=='disconnected' and (not any(o.maze.cells[q] for q in neighbors(o.maze.start,9,9)) or not any(o.maze.cells[q] for q in neighbors(o.maze.goal,9,9))):
                    d.rejections+=1;continue
                orbit={layout_hash(transform_maze(o.maze,pose)) for pose in range(8)}
                if orbit&d.layouts:d.rejections+=1;continue
                for pose in range(8):
                    m=transform_maze(o.maze,pose);q=Oracle.build(m);q._from_start=distances(m,m.start)
                    assert bool(q.path)==(family!='disconnected')
                    d.cache[m.case_id]=q;d.metadata[m.case_id]=dict(family='ordinary_'+family,
                        base=o.maze.case_id,template=o.maze.case_id,index=index,pose=pose,
                        path=q.path,prefix=-1,stress=False,graph=family,side=0)
                d.layouts.update(orbit);break
            else:raise RuntimeError('No unseen ordinary case')


def software_fixture(previous):
    d=AccessData(23456789,previous)
    for i,(shape,stress) in enumerate([('straight',False),('turning',False),('straight',True)]):
        d.context('unit',i,(4,6),shape,(0,1,2,4,8),stress)
    return d
