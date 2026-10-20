import numpy as np
import pytest
from maze_evolution.branch_overgrowth_data import *
from maze_evolution.branch_overgrowth_study import schedules,TARGETS,projection,HORIZON
from maze_evolution.branch_overgrowth_audit import geometry
from maze_evolution.branch_overgrowth_analysis import frame_details
from maze_evolution.routing_mechanism_runtime import respond
from maze_evolution.exposure_selection import organism,record

@pytest.fixture(scope='module')
def data():return load(FIXTURES)

@pytest.fixture(scope='module')
def panel():return read_compressed(OUT/'panel.json.gz')

def test_all_contexts_poses_cycles_and_matched_cells(data):
    c,contexts,m=data;g=geometry(c,contexts,m)
    assert g['total_inputs']==2912 and g['pairs']==400 and len(contexts)==6
    assert {x['prefix'] for x in m.values() if x['family']=='paired'}=={0,1,2,4,8}

def test_whole_layout_exclusion(data):
    assert not exclusions()&{layout_hash(o.maze) for o in data[0].values()}

def test_exact_root_parent_and_random_draw_controls(panel):
    for name,n in [('mutation0',29),('mutation1',7),('mutation2',11),('family0',13),('family1',16),('family2',12)]:
        c=panel['chains'][name];assert c['mutation_births']==n
        assert c['nodes'][1]==panel['items'][name+'_parent']['id'] and c['root']==panel['items'][name+'_root']['id']
        assert not panel['events'].get(c['root'],{}).get('parents')
    assert all(panel['chains'][f'resample{r}']['mutation_births']==0 for r in range(3))

def test_normal_first_fixed_schedule_no_success_filter(data,panel):
    s=list(schedules(panel,data[2]));scopes=[x[0] for x in s]
    assert scopes==sorted(scopes,key={'normal':0,'intervention':1,'trace':2}.get)
    assert len({pid for scope,pid,_,_ in s if scope=='normal'})==len(panel['models'])
    assert sum(scope=='trace' for scope,_,_,_ in s)==3120
    assert sum(scope=='intervention' for scope,_,_,_ in s)==62400
    assert all(data[2][cid]['pose'] in (0,4) for scope,_,_,cid in s if scope=='trace')

def test_native_and_forced_tick_parity(data,panel):
    c,_,meta=data;o=next(o for cid,o in c.items() if trace_case(meta[cid],True));m=o.maze
    for name in ('mutation0','family1','resample2','historical_long','intact'):
        mod=panel['models'][panel['aliases'][name]];r=organism(mod).react(m.cells,m.w,m.h,m.start,m.goal)
        assert record(respond(mod,m).reaction,o)==record(r,o)
        h=respond(mod,m,trace=True,forced=True,horizon=HORIZON).history
        if 0<r.steps<=len(h):assert np.array_equal((h[r.steps-1,2]>0).astype(np.uint8),r.mask)

def test_both_off_goal_states_identical(data,panel):
    c,_,meta=data;cid=next(cid for cid,m in meta.items() if trace_case(m,True));md=meta[cid]
    ids=[cid for cid,m in meta.items() if m['base']==md['base'] and m['pose']==md['pose'] and m['family']=='paired'];assert len(ids)==2
    model=panel['models'][panel['aliases']['mutation0']]
    a,b=[respond(model,c[cid].maze,'both_off',trace=True,forced=True,horizon=8).history for cid in ids]
    assert np.array_equal(a,b)

def test_extra_cell_never_counted_as_a_path(data):
    c,_,meta=data;o=next(o for cid,o in c.items() if meta[cid]['family']=='paired' and meta[cid]['prefix']==1)
    h=np.zeros((3,8,len(o.maze.cells)),np.uint16);h[:,2,o.path]=1
    extra=next(i for i,x in enumerate(o.maze.cells) if x and i not in o.path);h[0,2,extra]=1
    native=dict(steps=1,optimal=False,mask=np.packbits(h[0,2]>0,bitorder='little').tobytes().hex())
    d=frame_details(h,o,native)
    assert d['shortest_ticks']==[2,3] and d['later_shortest_ticks']==[2,3]
    assert d['extra_cells']==[1,0,0] and d['missing_cells']==[0,0,0]
    assert d['native_mask_at_tick_matches'] and d['repeated_full_state']==dict(first=2,again=3,period=1)

def test_profile_projection_keeps_trace_subset_and_ordinary_fixed():
    rates={k:dict(seconds=1) for k in ('normal|structured','normal|ordinary','parity|structured','intervention|structured','trace|structured')}
    assert projection(rates,2)==84 and projection(rates,1)==52

def test_forced_execution_remains_bounded(data,panel):
    m=next(iter(data[0].values())).maze;mod=panel['models'][panel['aliases']['mutation0']]
    with pytest.raises(ValueError):respond(mod,m,forced=True)
    with pytest.raises(ValueError):respond(mod,m,trace=True,forced=True,horizon=97)
