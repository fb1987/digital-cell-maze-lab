"""V12L matched translations and goal-bend confirmation; evaluator-only labels."""
import random
from cellular_maze_lab import neighbors
from .datasets import seed_for,manifest
from .evaluator import Maze,Oracle,distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData,layout_hash,transform_maze,transform_point
from .foundation_study import read_compressed,compressed_json
from .robustness_data import exclusions as prior_exclusions,load,BRANCHES,FAMILIES

OUT=ROOT/'results/lineage_confirmation'
FIXTURES=ROOT/'results/lineage_confirmation_fixtures'
SEED=2026101907
FIXTURE_SEED=1264
SPECS=((1,'straight'),(2,'straight'),(4,'straight'),(4,'bent'),(8,'straight'),(8,'bent'))
SHAPES=('straight','turning','asymmetric')


def exclusions():
    rows=prior_exclusions()
    for p in ('robustness_pressure_fixtures/mazes.json.gz','robustness_pressure_fixtures/geometry_test_mazes.json.gz',
              'robustness_pressure/diagnostic/mazes.json.gz','robustness_pressure/search/mazes.json.gz','robustness_pressure/final/mazes.json.gz'):
        rows.extend(read_compressed(ROOT/'results'/p))
    return rows


def build(seed,namespace,index,salt,goal_shape,prefix,source_shape,long,n=25):
    actual=seed_for(seed,namespace,index,salt);rng=random.Random(actual);j=(n//2)*n+n//2
    tails=[rng.randint(6,9) if long else rng.randint(3,4) if goal_shape=='straight' else rng.randint(5,6) for _ in range(2)]
    arms=[]
    for side,(sign,length) in enumerate(zip((-1,1),tails)):
        down=-1 if goal_shape=='asymmetric' and side==1 else 1
        arms.append([j+sign*k for k in range(length+1)] if goal_shape=='straight' else
                    [j+sign*k for k in range(5)]+[j+sign*4+down*k*n for k in range(1,length-3)])
    sign=-1 if goal_shape=='asymmetric' or index%2==0 else 1
    source=[j-k*n for k in range(prefix+1)] if source_shape=='straight' else [j,j-n,j-2*n]+[j-2*n+sign*k for k in range(1,prefix-1)]
    pref=list(reversed(source));paths=[pref+a[1:] for a in arms];depth=rng.randint(3,4)
    alt=[j-2+k*n for k in range(depth+1)]+[j-2+depth*n+k for k in range(1,5)]+[j+2+k*n for k in range(depth-1,-1,-1)]
    alternatives=[pref+arms[1][1:2]+list(reversed(alt))+arms[0][3:],pref+arms[0][1:2]+alt+arms[1][3:]]
    fork=set(sum(paths,[]));cycle=fork|set(alt)
    graphs=dict(fork=fork,two_junction=fork|{j-2+n,j-2+2*n},cycle=cycle,
                corridor_0=set(paths[0]),corridor_1=set(paths[1]),disconnected=fork-{j})
    noise=set();options=list(range(n*n));rng.shuffle(options)
    for p in options:
        if 3<=p%n<n-3 and 3<=p//n<n-3 and p not in cycle|noise and not any(q in cycle|noise for q in neighbors(p,n,n)):
            noise.add(p)
            if len(noise)==8:break
    assert len(noise)==8
    return actual,dict(graphs={f:sorted(g|noise) for f,g in graphs.items()},paths=paths,alternatives=alternatives,
                       junction=j,source=pref[0],goals=[a[-1] for a in arms],tails=tails,depth=depth,clutter=sorted(noise))


class LineageData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous);self.contexts=[];self.metadata={}

    def template(self,split,index,goal_shape,prefix,source_shape,long):
        n=25;namespace=f'{split}/{goal_shape}/p{prefix}/{source_shape}/long{int(long)}'
        for salt in range(1000):
            actual,v=build(self.seed,namespace,index,salt,goal_shape,prefix,source_shape,long)
            template=f'{namespace}/t{index}/s{salt}';pending={};meta={};contexts=[]
            for position,(dx,dy) in enumerate(((0,0),(2,-2) if index%2==0 else (-2,2))):
                shift=lambda p:p+dx+dy*n
                base=f'{template}/position{position}';poses=[]
                for pose in range(8):
                    conv=lambda p:transform_point(shift(p),n,pose);ids={}
                    for family in FAMILIES:
                        ids[family]=[]
                        for side in ([int(family[-1])] if family.startswith('corridor') else (0,1)):
                            cells=set(map(shift,v['graphs'][family]));assert all(0<p%n<n-1 and 0<p//n<n-1 for p in cells)
                            m=transform_maze(Maze(bytes(int(p in cells) for p in range(n*n)),n,n,shift(v['source']),shift(v['goals'][side]),family,actual,split,f'{base}/{family}/{side}'),pose)
                            pending[m.case_id]=m;ids[family].append(m.case_id)
                            meta[m.case_id]=dict(base=base,template=template,index=index,position=position,translation=[dx,dy],
                                goal_shape=goal_shape,prefix=prefix,source_shape=source_shape,long=long,family=family,side=side,pose=pose,
                                junction=conv(v['junction']),path=list(map(conv,v['paths'][side])),
                                alternative=list(map(conv,v['alternatives'][side])) if family=='cycle' else [],
                                tails=v['tails'],depth=v['depth'],clutter=list(map(conv,v['clutter'])))
                    poses.append(dict(pose=pose,cases=ids))
                contexts.append(dict(id=base,template=template,index=index,position=position,translation=[dx,dy],goal_shape=goal_shape,
                    prefix=prefix,source_shape=source_shape,long=long,n=n,poses=poses))
            orbit={layout_hash(m) for m in pending.values()}
            if len(orbit)!=96 or orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start)
                assert (not o.path)==(m.family=='disconnected')
                if o.path:assert o.path==meta[cid]['path']
                self.cache[cid]=o
            self.layouts.update(orbit);self.metadata.update(meta);self.contexts.extend(contexts);return contexts
        raise RuntimeError(f'Cannot construct unseen template {namespace}/{index}')

    def save(self,out):
        out.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:
            compressed_json(out/f'{name}.json.gz',value)


def corpus(data,split):
    for shape in SHAPES:
        for prefix,source in SPECS:
            for long in (False,True):data.template(split,len(data.contexts)//2,shape,prefix,source,long)
    assert len(data.contexts)==72 and len(data.cache)==5760


def mechanism_case(meta):
    return meta['long'] and (meta['prefix'],meta['source_shape']) in ((1,'straight'),(2,'straight'),(8,'bent'))
