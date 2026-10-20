"""V12U: eight new structural contexts; fixed queried subset, all layouts sealed."""
from .routing_mechanism_data import (ROOT,MechanismData,SHAPES,load,layout_hash,
    read_compressed,compressed_json,manifest)
from .composition_data import ordinary

OUT=ROOT/'results/lineage_mapping'
FIXTURES=ROOT/'results/lineage_mapping_fixtures'
SEED=2026101916
FIXTURE_SEED=1354
PREFIXES={(0,'straight'),(1,'straight'),(2,'straight'),(4,'straight'),(4,'bent'),(8,'straight')}
GRAPHS={('fork',0),('two_junction',2),('cycle',2)}

def exclusions():
    p=read_compressed(ROOT/'results/routing_mechanism/whole_layout_exclusions.json.gz')
    assert p['count']==len(set(p['hashes']))==225592
    return set(p['hashes'])

def create(seed,split,previous,fixture=False):
    d=MechanismData(seed,previous)
    for shape in SHAPES:
        for variant in range(1 if fixture else 2):d.context(split,len(d.contexts),shape,variant)
    ordinary(d,split)
    return d

def normal_case(m):
    if m['family'].startswith('ordinary_'):return True
    return (m['prefix'],m['source_shape']) in PREFIXES and (m['family']!='paired' or (m['graph'],m['second']) in GRAPHS)

def mechanism_case(m):
    return (m['family']=='paired' and m['shape'] in ('straight','bend_one') and m['variant']==0
            and m['prefix'] in (1,2,4) and m['source_shape']=='straight'
            and (m['graph'],m['second']) in {('fork',0),('cycle',2)})
