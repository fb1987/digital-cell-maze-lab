from collections import Counter
import pytest
from maze_evolution.lineage_mapping_data import *
from maze_evolution.lineage_mapping_study import make_panel,schedules,CHAIN,TARGETS,projection
from maze_evolution.lineage_mapping_analysis import comparison
from maze_evolution.routing_mechanism_audit import geometry
from maze_evolution.exposure_genome import Individual
from maze_evolution.exposure_selection import organism,record
from maze_evolution.routing_mechanism_runtime import respond

@pytest.fixture(scope='module')
def data():return load(FIXTURES)

@pytest.fixture(scope='module')
def panel():return read_compressed(OUT/'panel.json.gz')

def test_exact_twelve_historical_edits(panel):
    assert make_panel()==panel and len(panel['models'])==19 and len(panel['events'])==12
    assert panel['items']['d00']['id'].endswith('/i5140') and panel['items']['d12']['id'].endswith('/i3776')
    assert [len(Individual.load(panel['items'][n]).genome.program.genes) for n in CHAIN]==[254,253,253,256,256,256,256,256,256,256,255,255,255]

def test_geometry_including_unqueried_variants(data):
    c,ctx,m=data;g=geometry(c,ctx,m)
    assert g['inputs']==4480 and g['contexts']==4 and g['whole_layouts']==2784
    assert not exclusions()&{layout_hash(o.maze) for o in c.values()}

def test_query_balancing_and_symmetric_pairs(data):
    _,_,m=data
    counts=Counter(x['family'] for x in m.values() if normal_case(x))
    assert counts==dict(paired=1152,corridor=384,disconnected=320,ordinary_perfect=192,ordinary_random=192,ordinary_disconnected=128)
    pairs=Counter((x['base'],x['pose']) for x in m.values() if normal_case(x) and x['family']=='paired')
    assert set(pairs.values())=={2} and len(pairs)==576

def test_schedule_native_precedes_diagnostics_and_parity(data,panel):
    m=data[2];plan=list(schedules(panel,m,True));n=2*len(panel['models'])
    assert all(x[0]=='normal' for x in plan[:n]) and all(x[0]!='normal' for x in plan[n:])
    assert sum(len(x[-1]) for x in plan)==12784
    assert {pid for s,pid,mode,k,ids in plan if s=='intervention'}=={panel['aliases'][n] for n in TARGETS}
    assert {len(ids) for s,pid,mode,k,ids in plan if s=='intervention'}=={24}

def test_mechanism_subset_and_all_poses(data):
    m=data[2];ids=[c for c,x in m.items() if mechanism_case(x)]
    assert len(ids)==192 and all(normal_case(m[c]) for c in ids)
    assert {m[c]['pose'] for c in ids}==set(range(8))
    assert {m[c]['shape'] for c in ids}=={'straight','bend_one'}

def test_projection_excludes_parity_and_separates_categories():
    packet={'profiles':{'normal|a|normal|structured':{'seconds':2},'normal|a|normal|ordinary':{'seconds':3},'intervention|a|pulse_off|mechanism':{'seconds':4},'parity|a|normal|parity':{'seconds':1000}}}
    assert projection(packet)==2*(2*16+3*8+4*8)

def test_comparison_retains_gain_loss_and_work_changes():
    a={'details':{'one':{'complete':True,'template':'ctx','prefix':1},'two':{'complete':False,'template':'ctx','prefix':1}},'positive':1}
    b={'details':{'one':{'complete':False,'template':'ctx','prefix':1},'two':{'complete':True,'template':'ctx','prefix':1}},'positive':1}
    r=dict(mask='00',status='emitted',steps=1,reads=3,dispatches=4,exposure_checks=2,optimal=True)
    s=dict(r,steps=2,optimal=False)
    out=comparison('a','b',{'pa|normal':a,'pb|normal':b},{'pa':{'x':r},'pb':{'x':s}},{'a':'pa','b':'pb'},{'x':{'family':'corridor'}})
    assert out['gained']==['two'] and out['lost']==['one'] and out['changed_responses']['steps']==1
    assert out['by_family']['corridor']['lost_shortest']==1

def test_intermediate_native_adapter_parity(data,panel):
    c,_,meta=data;o=next(o for cid,o in c.items() if mechanism_case(meta[cid]));m=o.maze
    for name in CHAIN:
        model=panel['models'][panel['aliases'][name]]
        assert record(organism(model).react(m.cells,m.w,m.h,m.start,m.goal),o)==record(respond(model,m).reaction,o)
