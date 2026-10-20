"""V12W excluded-layout causal probe data; never passed into inference as an oracle."""
import json
from .lineage_mapping_data import (ROOT,MechanismData,SHAPES,ordinary,load,
    layout_hash,read_compressed,compressed_json,manifest,normal_case)
OUT=ROOT/'results/compatibility_map'
FIXTURES=ROOT/'results/compatibility_map_fixtures'
SEED=2026101918
FIXTURE_SEED=1374

def exclusions():
    p=read_compressed(ROOT/'results/causal_dissection/whole_layout_exclusions.json.gz')
    assert p['count']==len(set(p['hashes']))==243540
    return set(p['hashes'])

def create(seed,split,previous,fixture=False):
    repeats=1 if fixture else json.loads((FIXTURES/'profile.json').read_text())['contexts_per_shape']
    assert repeats in (1,2,3)
    d=MechanismData(seed,previous)
    for shape in SHAPES:
        for variant in range(repeats):d.context(split,len(d.contexts),shape,variant)
    ordinary(d,split)
    return d

# Fixed before calibration: two rotations crossed with reflected/unreflected poses.
POSES=(0,1,4,5)
def query_case(m,fixture=False):
    return normal_case(m) and (m['pose']==0 if fixture else
        m['family'].startswith('ordinary_') or m['pose'] in POSES)
