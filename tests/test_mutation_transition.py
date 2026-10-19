"""V12P graph controls, fixed ancestry, complete panels and bounded analysis."""
from copy import deepcopy
from collections import defaultdict
import pytest
from maze_evolution.mutation_transition_data import FIXTURES,OUT,load,mechanism_case,geometries
from maze_evolution.mutation_transition_study import make_panel,schedule,Budget,MODES
from maze_evolution.mutation_transition_audit import geometry
from maze_evolution.mutation_transition_analysis import bootstrap
from maze_evolution.foundation_study import read_compressed

@pytest.fixture(scope='module')
def data():return load(FIXTURES)


def test_fixture_graphs_and_full_pose_coverage(data):
    assert geometry(*data)==dict(cases=6240,templates=10,pairs=1040,cycles=96,whole_layouts=1232)


def test_saved_panel_is_exact_and_all_steps_present():
    p=make_panel();assert p==read_compressed(OUT/'panel.json.gz');assert len(p['models'])==62
    assert p['chains']['route']==[f'route/d{i}' for i in range(17)] and len(p['events'])==48
    for label in ('reach1','reach2'):assert p['chains'][label]==[f'{label}/d{i}' for i in (0,1,4,16)]
    for top in ('local','evolved'):
        for i in range(17):assert top+f'/route/d{i}' in p['aliases']
    assert len(p['mechanisms'])==10 and p['items']['resample']['parent'] is None


def test_source_motion_keeps_full_layout_fixed(data):
    cases,_,meta=data;groups=defaultdict(list)
    for cid,m in meta.items():
        if m['control']=='full' and m['family']=='paired':groups[m['template'],m['bend'],m['graph'],m['pose'],m['side']].append(cases[cid].maze)
    for ms in groups.values():assert len({m.cells for m in ms})==1 and len({m.start for m in ms}) in (3,4)


def test_degree_controls_and_bends(data):
    _,_,meta=data
    assert {m['source_degree'] for m in meta.values() if m['family']=='paired' and m['control']=='spur'}=={3}
    assert {m['source_degree'] for m in meta.values() if m['family']=='paired' and m['control']=='no_stem'}=={2}
    for shape in ('straight','turning'):
        gs=geometries(4,shape);b={g['bend']:g for g in gs if g['control']=='full' and g['prefix']==4}
        assert b['straight']['arms']==b['bent']['arms'] and len(b['straight']['paths'][0])==len(b['bent']['paths'][0])
        assert b['straight']['paths'][0]!=b['bent']['paths'][0]


def test_cycle_is_real_and_longer(data):
    cases,_,meta=data
    for cid,m in meta.items():
        if m['family']=='paired' and m['graph']=='cycle':assert len(m['alternative'])-len(m['path'])==12


def test_corrupt_path_label_rejected(data):
    cases,contexts,meta=data;bad=deepcopy(meta);cid=next(k for k,m in bad.items() if m['family']=='paired');bad[cid]['path']=bad[cid]['path'][:-1]
    with pytest.raises(AssertionError):geometry(cases,contexts,bad)


def test_schedule_normal_before_fixed_interventions(data):
    _,_,meta=data;p=make_panel();plan=list(schedule(p,meta));normal=[x for x in plan if x[1]=='normal'];interventions=[x for x in plan if x[1]!='normal']
    assert len(normal)==62 and len(interventions)==50 and plan[:62]==normal
    assert all(len(ids)==6240 for _,_,ids in normal)
    assert all(len(ids)==1312 and all(mechanism_case(meta[c]) for c in ids) for _,_,ids in interventions)
    assert sum(len(ids) for _,_,ids in schedule(p,meta,True))*16==904960


def test_all_on_no_genome_edit():
    p=make_panel()
    for alias,pid in p['aliases'].items():
        top,label=alias.split('/',1);model=p['models'][pid]
        assert model['genome']['exposure']==7 and model['genome']['genes']==p['items'][label]['genome']['genes'] and model['topology']==top


def test_budget_stops_before_call():
    b=Budget(calls=0)
    with pytest.raises(TimeoutError):b.call(lambda:None)
    assert b.calls==0


def test_context_bootstrap_uses_template_values():
    r=bootstrap([0.,0.]);assert (r['n'],r['mean'],r['lower'],r['upper'])==(2,0.,0.,0.)
    r=bootstrap([-1.,-1.]);assert (r['lower'],r['upper'])==(-1.,-1.)


def test_interventions_are_separate():
    assert MODES['normal']==(True,True,True,False)
    assert MODES['pulse_off']==(False,True,True,False)
    assert MODES['flag_off']==(True,False,True,False)
    assert MODES['both_off']==(False,False,True,False)
    assert MODES['endpoint_off']==(True,True,False,False)
    assert MODES['nonlocal_off']==(True,True,True,True)
