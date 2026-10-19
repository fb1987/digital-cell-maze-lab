"""V12P new matched source-position, degree, bend and genuine-cycle corpus."""
import random
from cellular_maze_lab import neighbors
from .foundation_calibration import ROOT
from .foundation_data import FoundationData,layout_hash,transform_maze,transform_point
from .foundation_study import read_compressed,compressed_json
from .datasets import seed_for,manifest
from .evaluator import Maze,Oracle,distances
from .mutation_depth_data import exclusions as through_N
from .branch_pressure_data import load

OUT=ROOT/'results/mutation_transition'
FIXTURES=ROOT/'results/mutation_transition_fixtures'
SEED=2026101911
FIXTURE_SEED=1304
N=19
PREFIXES=(0,1,2,4)
ARMS=(2,3,4,6)
SHAPES=('straight','turning')


def exclusions():
    rows=through_N()
    for p in ('mutation_depth_fixtures','mutation_depth/discovery','mutation_depth/validation','mutation_depth/confirmation'):
        rows+=read_compressed(ROOT/'results'/p/'mazes.json.gz')
    return rows


def geometries(length,shape,stress=False):
    j=(N//2)*N+N//2
    arms=[[j+sign*k for k in range(length+1)] if shape=='straight' else
          [j+sign*k for k in range(length)]+[j+sign*(length-1)+N] for sign in (-1,1)]
    result=[]
    for bend in (('straight',) if stress else ('straight','bent')):
        stem=[j-k*N for k in range(6)] if bend=='straight' else [j,j-N,j-2*N]+[j-2*N-k for k in range(1,4)]
        variants=[('full',p) for p in (0,2,4) if stress] if stress else [('full',p) for p in PREFIXES]+[('no_stem',0),('spur',2),('spur',4)]
        for control,prefix in variants:
            upstream=[] if control=='no_stem' else stem[1:]
            tree=set(sum(arms,[]))|set(upstream)
            if control=='spur':
                q=stem[prefix]+(1 if bend=='bent' and prefix==2 else -N if bend=='bent' else -1)
                tree.add(q)
            pref=list(reversed(stem[:prefix+1]));paths=[pref+a[1:] for a in arms]
            for graph in (('fork','two_junction','cycle') if stress else ('fork',)):
                cells=set(tree);alternative=[[],[]]
                if graph=='two_junction':cells|={j-2+N,j-2+2*N}
                if graph=='cycle':
                    bridge=[j-2+k*N for k in range(5)]+[j-2+4*N+k for k in range(1,5)]+[j+2+k*N for k in range(3,-1,-1)]
                    cells|=set(bridge)
                    alternative=[pref+arms[1][1:2]+list(reversed(bridge))+arms[0][3:],pref+arms[0][1:2]+bridge+arms[1][3:]]
                assert all(0<q%N<N-1 and 0<q//N<N-1 for q in cells)
                result.append(dict(control=control,prefix=prefix,bend=bend,graph=graph,cells=sorted(cells),paths=paths,
                    alternatives=alternative,junction=j,source=stem[prefix],goals=[a[-1] for a in arms],stem=stem,arms=arms))
    return result


class TransitionData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed,previous);self.contexts=[];self.metadata={}

    def context(self,split,index,length,shape,stress):
        specs=geometries(length,shape,stress);occupied=set(q for g in specs for q in g['cells'])
        namespace=f'{split}/{"stress" if stress else "core"}/a{length}/{shape}'
        for salt in range(4000):
            actual=seed_for(self.seed,namespace,index,salt);rng=random.Random(actual);noise=set();options=list(range(N*N));rng.shuffle(options)
            for p in options:
                if 1<p%N<N-2 and 1<p//N<N-2 and p not in occupied|noise and not any(q in occupied|noise for q in neighbors(p,N,N)):
                    noise.add(p)
                    if len(noise)==8:break
            assert len(noise)==8
            template=f'{namespace}/c{index}/s{salt}';pending={};metadata={};configs=[]
            for g in specs:
                config=f'{template}/{g["bend"]}/{g["control"]}/p{g["prefix"]}/{g["graph"]}'
                for pose in range(8):
                    conv=lambda p:transform_point(p,N,pose)
                    for family in ('paired','corridor','disconnected'):
                        for side in (0,1):
                            points=set(g['paths'][side]) if family=='corridor' else set(g['cells'])
                            points|=noise;goal=sorted(noise)[side] if family=='disconnected' else g['goals'][side]
                            m=transform_maze(Maze(bytes(int(p in points) for p in range(N*N)),N,N,g['source'],goal,family,actual,split,f'{config}/{family}/{side}'),pose)
                            pending[m.case_id]=m
                            metadata[m.case_id]=dict(template=template,config=config,index=index,arm=length,shape=shape,stress=stress,
                                bend=g['bend'],control=g['control'],prefix=g['prefix'],graph=g['graph'],family=family,side=side,pose=pose,
                                junction=conv(g['junction']),path=list(map(conv,g['paths'][side])),alternative=list(map(conv,g['alternatives'][side])) if family=='paired' else [],
                                source_degree=sum(q in points for q in neighbors(g['source'],N,N)),clutter=list(map(conv,sorted(noise))))
                configs.append(config)
            orbit={layout_hash(m) for m in pending.values()}
            if orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start)
                assert (not o.path)==(m.family=='disconnected'),cid
                if o.path:assert o.path==metadata[cid]['path'],cid
                self.cache[cid]=o
            self.layouts.update(orbit);self.metadata.update(metadata)
            self.contexts.append(dict(id=template,index=index,arm=length,shape=shape,stress=stress,configs=configs,seed=actual,clutter=sorted(noise),new_layouts=len(orbit)));return
        raise RuntimeError('Could not generate unseen V12P context')

    def save(self,path):
        path.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:compressed_json(path/f'{name}.json.gz',value)


def create(seed,split,previous,repeats):
    d=TransitionData(seed,previous)
    for length in ARMS:
        for shape in SHAPES:
            for rep in range(repeats):d.context(split,len(d.contexts),length,shape,False)
    for length in (4,6):
        for rep in range(repeats):d.context(split,len(d.contexts),length,'straight',True)
    return d


def mechanism_case(m):
    return m['family']=='paired' and (m['stress'] or (m['arm'] in (2,3,4,6) and m['control'] in ('full','no_stem') and m['prefix'] in (0,2,4)))
