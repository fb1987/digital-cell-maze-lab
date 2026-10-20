from collections import Counter
import numpy as np
import pytest
from maze_evolution.causal_dissection_data import *
from maze_evolution.causal_dissection_study import make_panel,schedules,projection,EARLY
from maze_evolution.causal_dissection_runtime import respond
from maze_evolution.causal_dissection_analysis import equality,PREDICTIONS
from maze_evolution.exposure_selection import organism,record
from maze_evolution.exposure_genome import Individual
from maze_evolution.routing_mechanism_audit import geometry

@pytest.fixture(scope='module')
def data():return load(FIXTURES)
@pytest.fixture(scope='module')
def panel():return read_compressed(OUT/'panel.json.gz')

def test_probe_changes_exactly_one_recorded_gene(panel):
    assert panel==make_panel() and len(panel['models'])==16
    assert sum(v=='synthetic_mechanistic_probe' for v in panel['kinds'].values())==4
    for name,e in panel['synthetic_events'].items():
        parent=Individual.load(panel['items'][e['parent_alias']]);probe=Individual.load(panel['items'][name]);a=parent.genome.genes;b=probe.genome.genes
        assert len(a)==len(b)<=256 and [i for i,(g,h) in enumerate(zip(a,b)) if g!=h]==[e['index']]
        assert a[e['index']].row()==e['before'] and b[e['index']].row()==e['after']
        assert probe.parent==parent.identity and probe.birth==-1

def test_early_factorial_is_exact(panel):
    g={n:Individual.load(panel['items'][n]).genome.genes for n in EARLY}
    assert g['d01']==g['d00'][:251]+g['d00'][252:]
    assert g['d02']==g['dest_only'][:251]+g['dest_only'][252:]

def test_noop_reversion_positions_preserve_capacity(panel):
    g={n:Individual.load(r).genome.genes for n,r in panel['items'].items()}
    assert g['d07_no_store'][222].row()==g['d12_no_store'][221].row()==[0,34,34,0,0,0,64]
    assert g['d12_restore_store'][221]==g['d07'][222]

def test_full_geometry_and_unqueried_layouts_excluded(data):
    c,ctx,meta=data;g=geometry(c,ctx,meta)
    assert g['contexts']==4 and g['inputs']==4480
    # Ordinary disconnected layouts may have fewer than eight unique rotations.
    assert g['whole_layouts']==len({layout_hash(o.maze) for o in c.values()})
    assert not exclusions()&{layout_hash(o.maze) for o in c.values()}

def test_schedule_normal_first_no_success_filter(data,panel):
    plan=list(schedules(panel,data[2],True))
    assert all(p[0]=='normal' for p in plan[:32]) and all(p[0]!='normal' for p in plan[32:])
    assert sum(len(x[-1]) for x in plan)==11840
    assert {len(ids) for s,pid,mode,k,ids in plan if s=='intervention'}=={296}
    assert {pid for s,pid,mode,k,ids in plan if s=='intervention'}=={panel['aliases'][n] for n in EARLY}

def test_diagnostic_subset_has_all_poses_and_controls(data):
    meta=data[2];q=[m for m in meta.values() if mechanism_case(m)]
    assert len(q)==2368 and {m['pose'] for m in q}==set(range(8))
    assert Counter(m['family'] for m in q)==dict(paired=1152,corridor=384,disconnected=320,ordinary_perfect=192,ordinary_random=192,ordinary_disconnected=128)

def test_projection_rule_does_not_scale_fixed_diagnostics():
    p={'profiles':{'normal|x|normal|structured':{'seconds':2},'normal|x|normal|ordinary':{'seconds':3},'intervention|x|channel4_zero|mechanism':{'seconds':4},'parity|x|normal|parity':{'seconds':1000}}}
    assert projection(p,3)==2*(2*24+3*8+4*8)
    assert projection(p,2)==2*(2*16+3*8+4*8)

def test_normal_adapter_exact_native_parity(data,panel):
    c,_,meta=data;o=next(o for cid,o in c.items() if meta[cid]['family']=='paired' and meta[cid]['prefix']==2);m=o.maze
    for model in panel['models'].values():
        assert record(respond(model,m).reaction,o)==record(organism(model).react(m.cells,m.w,m.h,m.start,m.goal),o)

def test_channel4_signal_and_overwritten_state_semantics(data,panel):
    c,_,meta=data;m=next(o.maze for cid,o in c.items() if meta[cid]['family']=='paired' and meta[cid]['prefix']==1)
    get=lambda n:panel['models'][panel['aliases'][n]]
    parent=respond(get('d01'),m,trace=True,forced=True,horizon=16)
    child=respond(get('d02'),m,trace=True,forced=True,horizon=16)
    zero=respond(get('d01'),m,'channel4_zero',trace=True,forced=True,horizon=16)
    restored=respond(get('d02'),m,'channel4_restore',trace=True,forced=True,horizon=16)
    assert parent.history[:,4].any() and not child.history[:,4].any()
    assert np.array_equal(zero.history,child.history) and np.array_equal(restored.history,parent.history)
    # No additional neighbor call or erased charge: each trace matches its native proxy.
    for a,b in ((zero,child),(restored,parent)):
        for field in ('spatial_reads','dispatches','exposure_checks','range_reads'):
            assert getattr(a.reaction,field)==getattr(b.reaction,field)

def test_sham_modes_and_target_guards(data,panel):
    o=next(iter(data[0].values()));m=o.maze
    for name,mode in (('d00','channel4_restore'),('d02','channel4_zero')):
        model=panel['models'][panel['aliases'][name]]
        assert record(respond(model,m,mode).reaction,o)==record(respond(model,m).reaction,o)
    with pytest.raises(ValueError):respond(panel['models'][panel['aliases']['intact']],m,'channel4_zero')
    with pytest.raises(ValueError):respond(panel['models'][panel['aliases']['d01']],m,forced=True)

def test_equality_does_not_hide_counter_exceptions():
    r=dict(mask='00',status='emitted',steps=2,reads=3)
    e=equality({'a':r},{'a':dict(r,reads=4)})
    assert e['counts']['behavior_equal']==1 and e['counts']['full_record_equal']==0
    assert e['mismatches']==[dict(case='a',fields=['reads'])]
    assert len(PREDICTIONS)==8
