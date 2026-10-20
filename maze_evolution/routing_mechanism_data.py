"""V12T matched structural transfer. Oracles and explanatory predictors stay here."""
import random,json
from cellular_maze_lab import neighbors
from .foundation_data import FoundationData,layout_hash,transform_maze,transform_point
from .evaluator import Maze,Oracle,distances
from .datasets import seed_for,manifest
from .foundation_calibration import ROOT
from .foundation_study import read_compressed,compressed_json
from .branch_pressure_data import load

OUT=ROOT/'results/routing_mechanism'
FIXTURES=ROOT/'results/routing_mechanism_fixtures'
SEED=2026101915
FIXTURE_SEED=1344
N=33
PREFIXES=((0,'straight'),(1,'straight'),(2,'straight'),(4,'straight'),(4,'bent'),
          (6,'straight'),(6,'bent'),(8,'straight'),(8,'bent'))
SHAPES=('straight','bend_both','bend_one','hook')
GRAPHS=(('fork',0),('two_junction',1),('two_junction',2),('cycle',2),('cycle',3))

def exclusions():
    p=read_compressed(ROOT/'results/composition_study/whole_layout_exclusions.json.gz')
    assert p['count']==len(set(p['hashes']))==217240
    hashes=set(p['hashes'])
    rejected=OUT/'preparation_rejected/mazes.json.gz'
    if rejected.exists():
        for r in read_compressed(rejected):hashes.add(layout_hash(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'])))
    return hashes

def walk(start,directions,n=N):
    out=[start]
    for direction,length in directions:
        for _ in range(length):out.append(out[-1]+direction)
    return out

class MechanismData(FoundationData):
    def __init__(self,seed,previous=()):
        super().__init__(seed)
        self.layouts=set(previous);self.previous_count=len(self.layouts)
        self.metadata={};self.contexts=[]

    def context(self,split,index,shape,variant):
        namespace=f'{split}/{shape}/v{variant}'
        for salt in range(4000):
            actual=seed_for(self.seed,namespace,index,salt);rng=random.Random(actual)
            # Downstream lengths/turn locations are drawn once per context, shared
            # across every source prefix and junction-position intervention.
            j=(11+rng.randrange(3))*N+16+rng.randrange(-1,2)
            arms=[]
            for side,sign in enumerate((-1,1)):
                length=rng.randint(4,6)
                bends=shape in ('bend_both','hook') or shape=='bend_one' and side==variant%2
                if bends:
                    horizontal=rng.randint(5,6);vertical=rng.randint(2,4)
                    directions=[(sign,horizontal),(N,vertical)]
                    if shape=='hook':directions.append((sign,rng.randint(2,3)))
                else:directions=[(sign,length)]
                arms.append(walk(j,directions))
            depth=rng.randint(2,4);branch_length=rng.randint(2,4)
            variants=[]
            for prefix,source_shape in PREFIXES:
                stem=walk(j,[(-N,prefix)]) if source_shape=='straight' else walk(j,[(-N,2),((-1 if variant%2 else 1),prefix-2)])
                pref=stem[::-1];paths=[pref+a[1:] for a in arms];fork=set(sum(paths,[]))
                for graph,second in GRAPHS:
                    cells=set(fork);alt=[[],[]]
                    if graph=='two_junction':cells.update(walk(j-second,[(N,branch_length)]))
                    if graph=='cycle':
                        bridge=walk(j-second,[(N,depth),(1,2*second),(-N,depth)])
                        cells.update(bridge)
                        alt=[pref+arms[1][1:second]+bridge[::-1]+arms[0][second+1:],
                             pref+arms[0][1:second]+bridge+arms[1][second+1:]]
                    variants.append((prefix,source_shape,graph,second,cells,paths,alt))
                for side in range(2):variants.append((prefix,source_shape,'corridor',side,set(paths[side]),paths,[[],[]]))
                # Both goal arms remain connected internally; neither goal is isolated.
                variants.append((prefix,source_shape,'disconnected',0,fork-{j},paths,[[],[]]))
            occupied=set().union(*(v[4] for v in variants));noise=set()
            options=list(range(N*N));rng.shuffle(options)
            for p in options:
                if 2<p%N<N-3 and 2<p//N<N-3 and p not in occupied|noise and not any(q in occupied|noise for q in neighbors(p,N,N)):
                    noise.add(p)
                    if len(noise)==8:break
            template=f'{namespace}/c{index}/s{salt}';pending={};metadata={}
            for prefix,source_shape,graph,second,cells,paths,alt in variants:
                # Prefix zero disconnected removes source: omit that invalid control.
                if graph=='disconnected' and prefix==0:continue
                base=f'{template}/p{prefix}-{source_shape}/{graph}{second}'
                for side in ([second] if graph=='corridor' else (0,1)):
                    original=Maze(bytes(int(p in cells|noise) for p in range(N*N)),N,N,paths[side][0],arms[side][-1],graph,actual,split,f'{base}/goal{side}')
                    for pose in range(8):
                        m=transform_maze(original,pose);conv=lambda p:transform_point(p,N,pose)
                        pending[m.case_id]=m
                        metadata[m.case_id]=dict(template=template,base=base,index=index,shape=shape,variant=variant,
                            family='paired' if graph in ('fork','two_junction','cycle') else graph,graph=graph,
                            prefix=prefix,source_shape=source_shape,second=second,pose=pose,side=side,
                            junction=conv(j),path=list(map(conv,paths[side])),alternative=list(map(conv,alt[side])),
                            arm_lengths=[len(a)-1 for a in arms],depth=depth,branch_length=branch_length,clutter=list(map(conv,noise)))
            orbit={layout_hash(m) for m in pending.values()}
            if orbit&self.layouts:self.rejections+=1;continue
            for cid,m in pending.items():
                o=Oracle.build(m);o._from_start=distances(m,m.start)
                assert bool(o.path)==(m.family!='disconnected')
                if o.path:assert o.path==metadata[cid]['path'],cid
                self.cache[cid]=o
            self.metadata.update(metadata);self.layouts.update(orbit)
            self.contexts.append(dict(id=template,index=index,shape=shape,variant=variant,arm_lengths=[len(a)-1 for a in arms],depth=depth,branch_length=branch_length,salt=salt))
            return
        raise RuntimeError('No unseen matched context')

    def save(self,out):
        out.mkdir(parents=True,exist_ok=True)
        for name,value in [('mazes',manifest(self.cache.values())),('contexts',self.contexts),('metadata',self.metadata)]:compressed_json(out/f'{name}.json.gz',value)

def create(seed,split,previous):
    d=MechanismData(seed,previous)
    repeats=1 if split=='fixture' else json.loads((FIXTURES/'profile.json').read_text())['contexts_per_shape']
    for shape in SHAPES:
        for variant in range(repeats):d.context(split,len(d.contexts),shape,variant)
    # Same ordinary supplier as S, independently seeded and excluded.
    from .composition_data import ordinary
    ordinary(d,split)
    return d

def mechanism_case(m):
    return m['family']=='paired' and m['variant']==0 and (m['prefix'],m['source_shape']) in ((1,'straight'),(2,'straight'),(4,'straight'),(4,'bent'))

def trace_case(m):
    return mechanism_case(m) and m['shape'] in ('straight','bend_one') and m['source_shape']=='straight' and m['prefix'] in (1,4) and (m['graph'],m['second']) in (('fork',0),('cycle',2))
