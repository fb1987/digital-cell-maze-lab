from collections import Counter
import pytest
from maze_evolution.compatibility_map_data import *
from maze_evolution.compatibility_map_study import make_panel,schedules,projection,label,construct
from maze_evolution.compatibility_map_audit import independent_panel
from maze_evolution.compatibility_map_analysis import mobius,compute
from maze_evolution.exposure_genome import Individual
from maze_evolution.exposure_selection import organism,record
from maze_evolution.routing_mechanism_audit import geometry

@pytest.fixture(scope='module')
def panel():return read_compressed(OUT/'panel.json.gz')
@pytest.fixture(scope='module')
def data():return load(FIXTURES)

def test_all_factorial_programs_independently_reconstructed(panel):
    assert panel==make_panel() and len(panel['models'])==40 and len(panel['items'])==41
    assert independent_panel(panel)==32
    assert panel['aliases']['d07']==panel['aliases'][label(0,True)]

def test_output_and_replacement_loci_survive_deletion(panel):
    for name,c in panel['conditions'].items():
        genes=Individual.load(panel['items'][name]).genome.genes;shift=int(10 in c['edits'])
        assert genes[222-shift].row()==([13,2,58,0,0,0,18] if c['store'] else [0,34,34,0,0,0,64])
        assert genes[207-shift].row()==([10,51,63,54,0,0,39] if 12 in c['edits'] else [0,18,25,0,0,0,12])

def test_native_historical_endpoints_exact(panel):
    v=read_compressed(ROOT/'results/causal_dissection/panel.json.gz')
    for mask,store,name in ((0,True,'d07'),(0,False,'d07_no_store'),(15,True,'d12_restore_store'),(15,False,'d12_no_store')):
        assert Individual.load(panel['items'][label(mask,store)]).genome==Individual.load(v['items'][name]).genome
    assert panel['aliases']['d08']!=panel['aliases'][label(0,False)]
    assert panel['aliases']['d12']!=panel['aliases'][label(15,False)]

def test_full_fixture_geometry_and_exclusion(data):
    cases,ctx,meta=data;g=geometry(cases,ctx,meta)
    assert g['contexts']==4 and len(cases)==4480
    layouts={layout_hash(o.maze) for o in cases.values()}
    assert g['whole_layouts']==len(layouts) and not layouts&exclusions()

def test_schedule_every_model_same_normal_cases(data,panel):
    plans=list(schedules(panel,data[2],True))
    assert len(plans)==80 and sum(len(x[-1]) for x in plans)==11840
    assert all(s==mode=='normal' for s,p,mode,k,ids in plans)
    sets={p:set(i for s,p2,m,k,ids in plans if p2==p for i in ids) for p in panel['models']}
    assert len({tuple(sorted(v)) for v in sets.values()})==1

def test_poses_and_control_balance(data):
    chosen=[m for m in data[2].values() if query_case(m)]
    assert len(chosen)==1440
    assert Counter(m['family'] for m in chosen)==dict(paired=576,corridor=192,disconnected=160,ordinary_perfect=192,ordinary_random=192,ordinary_disconnected=128)
    assert {m['pose'] for m in chosen if m['family']=='paired'}==set(POSES)
    assert {m['pose'] for m in chosen if m['family']=='ordinary_perfect'}==set(range(8))

def test_time_projection_independent_of_scores():
    p={'profiles':{'normal|x|normal|structured':{'seconds':2},'normal|x|normal|ordinary':{'seconds':3}}}
    assert projection(p,3)==2*(2*12+3*8)
    assert projection(p,2)==2*(2*8+3*8)

def test_higher_order_decomposition_detects_three_factor_dependency():
    v=[7-3*bool(m&1)+11*bool(m&2 and m&4)-19*bool(m&1 and m&2 and m&8) for m in range(16)]
    c=mobius(v)
    assert {i:x for i,x in enumerate(c) if x}=={0:7,1:-3,6:11,11:-19}
    for m in range(16):assert sum(c[s] for s in range(16) if s&m==s)==v[m]

def test_analysis_complete_and_self_consistent_on_fixture_slice(data,panel):
    cases,_,meta=data
    ids=[cid for cid,m in meta.items() if query_case(m,True) and (m['family']!='paired' or m['prefix']==1)]
    events=[]
    for pid,model in panel['models'].items():
        org=organism(model)
        for cid in ids:
            o=cases[cid];m=o.maze
            events.append(dict(scope='normal',mode='normal',model=pid,row=record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)))
    metrics,a=compute(panel,meta,events)
    assert len(a['store_effects'])==16 and len(a['edit_toggles'])==64 and len(a['conditional_interactions'])==32
    for context,v in a['context_store_effects'].items():
        c=a['context_anchored_higher_order'][context]
        for m in range(16):assert sum(c[s] for s in range(16) if s&m==s)==v[str(m)]
    assert all(m['full_groups']==m['positive_full_queried_pose_groups']==0 for m in metrics.values())
