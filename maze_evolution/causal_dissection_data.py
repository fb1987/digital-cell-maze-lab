"""V12V excluded-layout causal probe data; never passed into inference as an oracle."""
import json
from .lineage_mapping_data import (ROOT,MechanismData,SHAPES,ordinary,load,
    layout_hash,read_compressed,compressed_json,manifest,normal_case)
OUT=ROOT/'results/causal_dissection'
FIXTURES=ROOT/'results/causal_dissection_fixtures'
SEED=2026101917
FIXTURE_SEED=1364

def exclusions():
    p=read_compressed(ROOT/'results/lineage_mapping/whole_layout_exclusions.json.gz')
    assert p['count']==len(set(p['hashes']))==233432
    return set(p['hashes'])

def create(seed,split,previous,fixture=False):
    repeats=1 if fixture else json.loads((FIXTURES/'profile.json').read_text())['contexts_per_shape']
    assert repeats in (1,2,3)
    d=MechanismData(seed,previous)
    for shape in SHAPES:
        for variant in range(repeats):d.context(split,len(d.contexts),shape,variant)
    ordinary(d,split)
    return d

def mechanism_case(m):
    return normal_case(m) and (m['family'].startswith('ordinary_') or m['variant']==0)
