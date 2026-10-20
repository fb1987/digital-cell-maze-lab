"""V13A: new layouts, fixed downstream geometry, Z-informed mechanism study."""
from .family_evolution_data import AccessData,ordinary,add_layouts
from .foundation_calibration import ROOT
from .foundation_study import read_compressed,compressed_json
from .foundation_data import layout_hash
from .branch_pressure_data import load
from .datasets import manifest

OUT=ROOT/'results/branch_overgrowth'
FIXTURES=ROOT/'results/branch_overgrowth_fixtures'
SEED=2026102006
FIXTURE_SEED=1444
SPECS=(((2,3),'straight',False),((2,3),'turning',False),
       ((3,4),'straight',False),((3,4),'turning',False),
       ((4,6),'straight',True),((6,4),'straight',True))

def exclusions():
    p=read_compressed(ROOT/'results/family_evolution/whole_layout_exclusions.json.gz')
    assert p['count']==len(set(p['hashes']))==272464
    return set(p['hashes'])

def create(seed,split,previous,repeats=1):
    d=AccessData(seed,previous)
    for rep in range(repeats):
        for lengths,shape,stress in SPECS:
            d.context(split,len(d.contexts),lengths,shape,(0,1,2,4,8),stress)
    ordinary(d,split)
    return d

def mechanism_case(m):
    return m['family'] in ('paired','corridor') and m['prefix'] in (0,1,4)

def trace_case(m,fixture=False):
    return m['family']=='paired' and m['index'] in (0,1,4) and m['prefix'] in (0,1,4) and m['pose'] in ((0,) if fixture else (0,4))
