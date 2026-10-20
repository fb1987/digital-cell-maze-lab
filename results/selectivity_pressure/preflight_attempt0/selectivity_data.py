"""V13B common curriculum, independent layouts and fixed paired validation."""
from .family_evolution_data import AccessData,ordinary,add_layouts
from .foundation_calibration import ROOT
from .foundation_study import read_compressed,compressed_json
from .foundation_data import layout_hash
from .branch_pressure_data import load
from .datasets import seed_for,manifest
OUT=ROOT/'results/selectivity_pressure'
FIXTURES=ROOT/'results/selectivity_pressure_fixtures'
SEED=2026102007
FIXTURE_SEED=1454
SPECS=(((2,3),'straight',False),((2,3),'turning',False),((3,4),'straight',False),((3,4),'turning',False),((4,6),'straight',True),((6,4),'straight',True))

def exclusions():
    p=read_compressed(ROOT/'results/branch_overgrowth/whole_layout_exclusions.json.gz')
    assert p['count']==len(set(p['hashes']))==275168
    return set(p['hashes'])

def create(seed,split,previous):
    d=AccessData(seed,previous)
    for rep in range(2 if split=='confirmation' else 1):
        for length,shape,stress in SPECS:d.context(split,len(d.contexts),length,shape,(0,1,2,4,8) if split=='confirmation' else (0,1,2),stress)
    if split=='confirmation':ordinary(d,split)
    return d

def training_batch(d,g):
    assert not d.cache and not d.metadata and not d.contexts
    length=((2,3),(3,4),(4,2),(4,6))[(g//16+g%4)%4];shape=('straight','turning')[(g//8+g//16)%2]
    d.context('train',2*g,length,shape,(0,))
    stress=g%8==7;prefix=1+g%2;hard=((4,6),(6,4))[(g//8)%2]
    d.context('train',2*g+1,hard if stress else length,'straight' if stress else shape,(prefix,),stress)
    pose=(g//2)%8;graph=('two_junction','cycle')[(g//8)%2] if stress else 'fork'
    ids=[c for c,m in d.metadata.items() if m['pose']==pose and (m['index']==2*g or m['graph']==graph)]
    assert len(ids)==12;return ids

def clear_batch(d):
    d.cache={};d.metadata={};d.contexts=[];d.previous_count=len(d.layouts)

def schedule_fixture(previous):
    d=AccessData(FIXTURE_SEED+1,previous);cache={};meta={};contexts=[]
    for g in range(16):
        ids=set(training_batch(d,g))
        for c,m in d.metadata.items():m['audit_generation']=g if c in ids else -1
        cache.update(d.cache);meta.update(d.metadata);contexts+=d.contexts;clear_batch(d)
    d.cache=cache;d.metadata=meta;d.contexts=contexts;return d

def validation_ids(meta):
    return [c for c,m in meta.items() if m['family']=='paired' or m['family']=='corridor' and m['prefix'] in (1,2) and m['pose']%2==0 or m['family']=='disconnected' and m['prefix']==0 and m['pose']==0]
