"""V12S new geometry; all old layouts and unqueried poses remain excluded."""
from .mutation_accessibility_data import AccessData,ROOT,seed_for,manifest,load,read_compressed
from .mutation_accessibility_data import exclusions as through_Q
from .foundation_study import compressed_json

OUT=ROOT/'results/composition_study'
FIXTURES=ROOT/'results/composition_fixtures'
SEED=2026101914
FIXTURE_SEED=1334
LENGTHS=((2,2),(2,3),(3,4),(4,2),(4,6),(6,4))

def exclusions():
    rows=through_Q()
    for part in ('mutation_accessibility_fixtures','mutation_accessibility/software_fixtures','mutation_accessibility/discovery','mutation_accessibility/validation','mutation_accessibility/confirmation'):
        rows+=read_compressed(ROOT/'results'/part/'mazes.json.gz')
    return rows

def create(seed,split,previous):
    d=AccessData(seed,previous)
    repeats=2 if split=='confirmation' else 1
    for length in LENGTHS:
        for shape in ('straight','turning'):
            for _ in range(repeats):d.context(split,len(d.contexts),length,shape,(0,1,2,4))
    for length in ((4,6),(6,4)):
        for _ in range(repeats):d.context(split,len(d.contexts),length,'straight',(0,1,2,4),True)
    if split in ('fixture','confirmation'):ordinary(d,split)
    return d

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

def training_batch(d,g):
    assert not d.cache and not d.metadata and not d.contexts
    length=LENGTHS[g%6];shape=('straight','turning')[(g//6)%2]
    d.context('train',2*g,length,shape,(0,))
    stress=g%4==3;hard_length=((4,6),(6,4))[(g//4)%2] if stress else length
    prefix=(1,2,4)[g%3]
    d.context('train',2*g+1,hard_length,'straight' if stress else shape,(prefix,),stress)
    pose=(g//12)%8;graph=('two_junction','cycle')[(g//4)%2] if stress else 'fork'
    ids=[cid for cid,m in d.metadata.items() if m['pose']==pose and (m['index']==2*g or m['graph']==graph)]
    assert len(ids)==12
    return ids

def clear_batch(d):
    d.cache={};d.metadata={};d.contexts=[];d.previous_count=len(d.layouts)

def schedule_fixture(previous):
    d=AccessData(FIXTURE_SEED+1,previous);cache={};meta={};contexts=[]
    for g in range(96):
        ids=set(training_batch(d,g))
        for cid,m in d.metadata.items():m['audit_generation']=g if cid in ids else -1
        cache.update(d.cache);meta.update(d.metadata);contexts+=d.contexts;clear_batch(d)
    d.cache=cache;d.metadata=meta;d.contexts=contexts;return d
