from copy import deepcopy
import pytest
from maze_evolution.lineage_confirmation_data import *
from maze_evolution.lineage_confirmation_audit import geometry
from maze_evolution.lineage_confirmation import wanted,MODES
from maze_evolution.lineage_confirmation_analysis import score

@pytest.fixture(scope='module')
def data():return load(FIXTURES)

def test_full_geometry_and_translations(data):
    cases,contexts,meta=data;g=geometry(cases,contexts,meta)
    assert g['independent_templates']==36 and g['cases']==5760 and g['whole_layouts']==3456

def test_protocol_balanced_strata(data):
    cases,contexts,meta=data
    assert {m['goal_shape'] for m in meta.values()}==set(SHAPES)
    for shape in SHAPES:
        assert sum(m['goal_shape']==shape for m in meta.values())==1920
    assert sum(mechanism_case(m) for m in meta.values())==1440
    assert sum(wanted(m,mode) for m in meta.values() for mode in MODES)==11520
    assert sum(wanted(m,mode,True) for m in meta.values() for mode in MODES)==1440

def test_wrong_translation_detected(data):
    cases,contexts,meta=data;broken=deepcopy(contexts);broken[1]['translation']=[-2,-2]
    with pytest.raises(AssertionError):geometry(cases,broken,meta)

def test_fixture_regeneration_excludes_old():
    d=LineageData(FIXTURE_SEED,exclusions());assert d.previous_count==163928
    corpus(d,'fixture');assert manifest(d.cache.values())==read_compressed(FIXTURES/'mazes.json.gz')

def fabricated(data,failed=None):
    cases,_,meta=data
    return [dict(case=cid,optimal=m['family']!='disconnected' and cid!=failed,valid=m['family']!='disconnected' and cid!=failed,
                 no_path=m['family']=='disconnected',reachable=m['family']!='disconnected',status='no_path' if m['family']=='disconnected' else 'emitted',reads=1,dispatches=1)
            for cid,m in meta.items()]

def test_pairs_require_both_goals_and_all_poses(data):
    cases,contexts,meta=data;rows=fabricated(data);a=score(rows,meta)
    assert a['pairs']==1728 and a['all16_groups']==108 and a['corridors']==1152 and a['no_path']==1152
    cid=contexts[0]['poses'][0]['cases']['fork'][0];b=score(fabricated(data,cid),meta)
    assert b['pairs']==1727 and b['all16_groups']==107

def test_corridors_never_count_as_pairs(data):
    _,_,meta=data;rows=[r for r in fabricated(data) if meta[r['case']]['family'].startswith('corridor')]
    assert score(rows,meta)['pairs']==0

def test_mechanism_subset_is_predeclared(data):
    _,_,meta=data;part=[m for m in meta.values() if mechanism_case(m)]
    assert len({m['template'] for m in part})==9
    assert all(m['long'] and m['prefix'] in (1,2,8) for m in part)

def test_panel_random_origins_and_parents():
    panel=read_compressed(OUT/'panel.json.gz')
    assert len(panel)==22
    for rep in (1,2):assert panel[f'k{rep}_target']['item']['parent']==panel[f'k{rep}_parent']['item']['id']
    assert [n for n,e in panel.items() if 'positive_control' in e['item']['id']]==['intact']
