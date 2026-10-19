"""V12Q P-informed matched forks; new whole layouts at every stage."""
import random
from copy import deepcopy
from cellular_maze_lab import neighbors
from .mutation_transition_data import geometries,N,exclusions as through_O
from .foundation_data import FoundationData,layout_hash,transform_maze,transform_point
from .foundation_calibration import ROOT
from .foundation_study import read_compressed,compressed_json
from .datasets import seed_for,manifest
from .evaluator import Maze,Oracle,distances
from .branch_pressure_data import load

OUT=ROOT/'results/shared_prefix'
FIXTURES=ROOT/'results/shared_prefix_fixtures'
SEED=2026101912
FIXTURE_SEED=1314

def exclusions():
    rows=through_O()
    for p in ('mutation_transition_fixtures','mutation_transition/confirmation'):
        rows+=read_compressed(ROOT/'results'/p/'mazes.json.gz')
    return rows

class PrefixData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous);self.contexts=[];self.metadata={}

    def context(self,split,index,length,shape,prefixes=(0,1),stress=False):
        base=[g for g in geometries(length,shape,stress) if g['control']=='full' and g['bend']=='straight' and g['prefix']==0]
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
                            meta[m.case_id]=dict(base=config,template=template,index=index,arm=length,shape=shape,stress=stress,prefix=g['prefix'],graph=g['graph'],family=family,side=side,pose=pose,junction=conv(g['junction']),path=list(map(conv,g['paths'][side])),alternative=list(map(conv,g['alternatives'][side])) if family=='paired' else [],clutter=list(map(conv,sorted(noise))))
            orbit={layout_hash(m) for m in pending.values()}
            if orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start)
                assert (not o.path)==(m.family=='disconnected'),cid
                if o.path:assert o.path==meta[cid]['path'],cid
                self.cache[cid]=o
            self.metadata.update(meta);self.layouts.update(orbit);self.contexts.append(dict(id=template,index=index,arm=length,shape=shape,stress=stress,prefixes=list(prefixes),seed=actual,clutter=sorted(noise),new_layouts=len(orbit)));return
        raise RuntimeError('No unseen Q context')

    def save(self,path):
        path.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:compressed_json(path/f'{name}.json.gz',value)

def create(seed,split,previous,generations=0):
    d=PrefixData(seed,previous)
    if split=='train':
        for g in range(generations):
            length,shape=((2,'straight'),(2,'turning'),(3,'straight'),(3,'turning'))[g%4]
            for slot in range(2):d.context(split,2*g+slot,length,shape)
    else:
        final=split=='confirmation'
        for length in ((2,3,4,6) if final else (2,3)):
            for shape in ('straight','turning'):
                for rep in range(2 if split in ('validation','confirmation') else 1):
                    d.context(split,len(d.contexts),length,shape,(0,1,2) if final else (0,1))
        if final:
            for length in (4,6):
                for rep in range(2):d.context(split,len(d.contexts),length,'straight',(0,1,2),True)
    return d

def training_ids(meta,generation,arm):
    pose=(generation//4)%8;ids=[]
    for cid,m in meta.items():
        if m['index']//2!=generation or m['pose']!=pose:continue
        prefix=(m['index']%2) if arm!='current' and m['family']=='paired' else 0
        if m['prefix']==prefix:ids.append(cid)
    assert len(ids)==12
    return ids

def software_fixture_manifest():
    """All additional geometry-only test inputs, including rejected-overlap test."""
    d=PrefixData(FIXTURE_SEED);d.context('fixture',0,2,'straight');d.context('fixture',1,2,'straight')
    rows=manifest(d.cache.values());n=PrefixData(FIXTURE_SEED,rows);n.context('fixture',0,2,'straight')
    rows+=manifest(n.cache.values());rows+=manifest(create(1,'confirmation',[]).cache.values())
    return rows

def software_fixtures():return read_compressed(OUT/'software_fixtures/mazes.json.gz')
