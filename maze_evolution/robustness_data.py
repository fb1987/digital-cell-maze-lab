"""V12K small matched graphs with balanced straight/turning goal arms.

All labels/oracles belong to the evaluator. Every generated pose/control is saved
and excluded, including poses not queried during training.
"""
from dataclasses import replace
import random
from cellular_maze_lab import neighbors
from .datasets import seed_for, manifest
from .evaluator import Maze, Oracle, distances
from .foundation_calibration import ROOT
from .foundation_data import FoundationData, layout_hash, transform_point, transform_maze
from .foundation_study import read_compressed, compressed_json
from .junction_distance_data import exclusions as old_exclusions

OUT=ROOT/'results/robustness_pressure'
FIXTURES=ROOT/'results/robustness_pressure_fixtures'
SEED=2026101906
FIXTURE_SEED=1254
BRANCHES=('fork','two_junction','cycle')
FAMILIES=(*BRANCHES,'corridor_0','corridor_1','disconnected')


def exclusions():
    rows=old_exclusions()
    for p in ('junction_distance_fixtures/mazes.json.gz','junction_distance/confirmation/mazes.json.gz'):
        rows.extend(read_compressed(ROOT/'results'/p))
    return rows


def build(seed,namespace,index,salt,n,goal_shape,prefix,source_shape,long=False):
    actual=seed_for(seed,namespace,index,salt);rng=random.Random(actual)
    j=(n//2)*n+n//2
    tails=[rng.randint(6,9) if long else rng.randint(3,4) if goal_shape=='straight' else rng.randint(5,6) for _ in range(2)]
    arms=[]
    for sign,length in zip((-1,1),tails):
        if goal_shape=='straight':arm=[j+sign*k for k in range(length+1)]
        else:arm=[j+sign*k for k in range(5)]+[j+sign*4+k*n for k in range(1,length-3)]
        arms.append(arm)
    if source_shape=='straight':source_arm=[j-k*n for k in range(prefix+1)]
    else:
        assert prefix>=3
        sign=-1 if index%2==0 else 1
        source_arm=[j-k*n for k in range(3)]+[j-2*n+sign*k for k in range(1,prefix-1)]
    if any(not (0<p%n<n-1 and 0<p//n<n-1) for p in sum(arms,[])+source_arm):return None
    path_prefix=list(reversed(source_arm));paths=[path_prefix+a[1:] for a in arms]
    depth=rng.randint(3,4)
    alt=[j-2+k*n for k in range(depth+1)]+[j-2+depth*n+k for k in range(1,5)]+[j+2+k*n for k in range(depth-1,-1,-1)]
    fork=set(sum(paths,[]));cycle=fork|set(alt)
    alternatives=[path_prefix+arms[1][1:2]+list(reversed(alt))+arms[0][3:],
                  path_prefix+arms[0][1:2]+alt+arms[1][3:]]
    graphs=dict(fork=fork,two_junction=fork|{j-2+n,j-2+2*n},cycle=cycle,
        corridor_0=set(paths[0]),corridor_1=set(paths[1]),disconnected=fork-{j})
    noise=set();options=list(range(n*n));rng.shuffle(options)
    for p in options:
        if (0<p%n<n-1 and 0<p//n<n-1 and p not in cycle|noise and not any(q in cycle|noise for q in neighbors(p,n,n))):
            noise.add(p)
            if len(noise)==8:break
    if len(noise)!=8:return None
    return actual,dict(graphs={f:sorted(g|noise) for f,g in graphs.items()},paths=paths,
        alternatives=alternatives,junction=j,prefix_path=path_prefix,source=path_prefix[0],
        goals=[a[-1] for a in arms],tails=tails,depth=depth,clutter=sorted(noise))


class RobustnessData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous);self.contexts=[];self.metadata={}

    def context(self,split,index,goal_shape,prefix,source_shape,n=13,long=False):
        namespace=f'{split}/{goal_shape}/p{prefix}/{source_shape}/long{int(long)}'
        for salt in range(1000):
            result=build(self.seed,namespace,index,salt,n,goal_shape,prefix,source_shape,long)
            if result is None:continue
            actual,v=result;base=f'{namespace}/c{index}/s{salt}';pending={};meta={};poses=[]
            for pose in range(8):
                conv=lambda p:transform_point(p,n,pose);ids={}
                for family in FAMILIES:
                    ids[family]=[]
                    for side in ([int(family[-1])] if family.startswith('corridor') else (0,1)):
                        cid=f'{base}/{family}/{side}'
                        m=transform_maze(Maze(bytes(int(p in v['graphs'][family]) for p in range(n*n)),n,n,
                            v['source'],v['goals'][side],family,actual,split,cid),pose)
                        pending[m.case_id]=m;ids[family].append(m.case_id)
                        meta[m.case_id]=dict(base=base,index=index,goal_shape=goal_shape,source_shape=source_shape,
                            prefix=prefix,family=family,side=side,pose=pose,long=long,junction=conv(v['junction']),
                            path=list(map(conv,v['paths'][side])),alternative=list(map(conv,v['alternatives'][side])) if family=='cycle' else [],
                            tails=v['tails'],depth=v['depth'],clutter=list(map(conv,v['clutter'])))
                poses.append(dict(pose=pose,cases=ids))
            orbit={layout_hash(m) for m in pending.values()}
            if len(orbit)!=48 or orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start)
                assert (not o.path)==(m.family=='disconnected')
                if o.path:assert o.path==meta[cid]['path']
                self.cache[cid]=o
            self.metadata.update(meta);self.layouts.update(orbit)
            c=dict(id=base,index=index,goal_shape=goal_shape,prefix=prefix,source_shape=source_shape,long=long,n=n,poses=poses)
            self.contexts.append(c);return c
        raise RuntimeError(f'Cannot construct unseen context {namespace}/{index}')

    def save(self,out):
        out.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:
            compressed_json(out/f'{name}.json.gz',value)


def load(out):
    cases={}
    for r in read_compressed(out/'mazes.json.gz'):
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        o=Oracle.build(m);o._from_start=distances(m,m.start);cases[m.case_id]=o
    return cases,read_compressed(out/'contexts.json.gz'),read_compressed(out/'metadata.json.gz')


def inputs(context,families=BRANCHES,poses=range(8),corridors=()):
    ids=[cid for p in poses for f in families for cid in context['poses'][p]['cases'][f]]
    ids += [cid for p in corridors for f in ('corridor_0','corridor_1') for cid in context['poses'][p]['cases'][f]]
    return ids


def fixtures(data):
    for goal in ('straight','turning'):
        for p,shape in ((1,'straight'),(2,'straight'),(4,'straight'),(4,'bent')):
            data.context('fixture',len(data.contexts),goal,p,shape)


def validation(data,rep):
    ids=[]
    for goal in ('straight','turning'):
        for p,shape in ((1,'straight'),(4,'bent')):
            c=data.context(f'validation/r{rep}',len(data.contexts),goal,p,shape)
            ids+=inputs(c,corridors=(0,4))
    assert len(ids)==208
    return ids


def batch(data,rep,generation):
    p=(1 if generation%4<2 else 2 if generation%4==2 else 3+(generation//4)%2)
    shape='straight' if p<3 or (generation//4+rep)%2==0 else 'bent'
    family=BRANCHES[generation%3];ids=[]
    for k,goal in enumerate(('straight','turning')):
        c=data.context(f'train/r{rep}/g{generation}',k,goal,p,shape)
        poses=[(generation+rep+k)%2+2*x for x in range(4)]
        ids+=inputs(c,(family,),poses,(poses[0],))
    assert len(ids)==20
    return ids


def confirmation(data,split):
    for goal in ('straight','turning'):
        for p,shape in ((1,'straight'),(2,'straight'),(4,'straight'),(4,'bent'),(8,'straight'),(8,'bent')):
            for long in (False,True):
                data.context(split,len(data.contexts),goal,p,shape,n=21,long=long)
    assert len(data.contexts)==24
