from copy import deepcopy
from functools import lru_cache
import numpy as np
from maze_evolution.mutation_accessibility_data import OUT,FIXTURES,load,geometries
from maze_evolution.mutation_accessibility_study import make_pool,eligible,identities_for_models
from maze_evolution.mutation_accessibility_metrics import summary,compare,choose,selected
from maze_evolution.mutation_accessibility_audit import independent_scores
from maze_evolution.shared_prefix_audit import geometry
from maze_evolution.foundation_study import read_compressed

@lru_cache(None)
def fixture():return load(FIXTURES)

@lru_cache(None)
def pool():return read_compressed(OUT/'pool.json.gz')

def oracle_rows():
    cases,_,meta=fixture();rows=[]
    for cid,o in cases.items():
        mask=np.zeros(361,np.uint8);mask[o.path]=1
        rows.append(dict(case=cid,mask=np.packbits(mask,bitorder='little').tobytes().hex(),status='emitted' if o.path else 'no_path',optimal=bool(o.path),valid=bool(o.path),no_path=not o.path,reachable=bool(o.path),partial=.9 if o.path else 0.,steps=1,active=1,reads=1,dispatches=1,exposure_checks=1))
    return rows,meta

def test_all_asymmetric_and_bent_fixture_graphs():
    c,ctx,m=fixture();g=geometry(c,m);assert g['inputs']==1632 and len(ctx)==10
    assert len({tuple(v['arm']) for v in m.values()})==6
    assert {v['pose'] for v in m.values()}==set(range(8))

def test_full_confirmation_geometry_and_counts():
    c,ctx,m=load(OUT/'software_fixtures');g=geometry(c,m)
    assert g['inputs']==5184 and len(ctx)==28 and sum(bool(o.path) for o in c.values())==3456

def test_source_moves_without_layout_or_goal_change():
    c,_,m=fixture();pairs={}
    for cid,o in c.items():
        v=m[cid]
        if v['family']=='paired':pairs.setdefault((v['template'],v['pose'],v['side'],v['graph']),set()).add((o.maze.cells,o.maze.goal))
    assert all(len(v)==1 for v in pairs.values())

def test_full_board_not_legacy_81_cell_truncation():
    mask=np.zeros(361,np.uint8);mask[[80,180,360]]=1
    assert selected(dict(mask=np.packbits(mask,bitorder='little').tobytes().hex()))=={80,180,360}

def test_exact_paths_proxy_and_independent_math():
    rows,meta=oracle_rows();m=summary(rows,meta);independent_scores(rows,meta,m)
    assert m['positive']==64 and m['mean_score']==1 and all(d['spill']==d['missing']==0 for d in m['details'])

def test_flood_is_not_complete_or_full_proxy():
    rows,meta=oracle_rows();cases,_,_=fixture()
    for r in rows:
        if meta[r['case']]['family']=='paired':
            mask=np.frombuffer(cases[r['case']].maze.cells,np.uint8);r['mask']=np.packbits(mask,bitorder='little').tobytes().hex();r['optimal']=False;r['valid']=False
    m=summary(rows,meta);assert m['positive']==0 and m['mean_score']==0
    independent_scores(rows,meta,m)

def test_retention_and_partial_not_success():
    rows,meta=oracle_rows();best=summary(rows,meta);root=deepcopy(best)
    root['positive']=0;root['mean_score']=0
    for d in root['details']:
        if d['prefix']==1 and not d['stress']:d['complete']=False;d['score']=0
    assert compare(best,root)['correct'] and compare(best,root)['partial']
    child=deepcopy(best);child['corridors']=0
    assert not compare(child,root)['correct'] and not compare(child,root)['retained']
    child=deepcopy(best);child['positive']=0
    for d in child['details']:
        if d['prefix']==1:d['complete']=False
    assert not compare(child,root)['correct'] and compare(child,root)['partial']

def test_all_walk_events_rng_and_fresh_controls_reproduce():
    p=pool();assert make_pool()==p and len(p['events'])==3840
    assert len(p['roots'])==5
    for g in p['groups'].values():
        assert all(len(ids)==16 for ids in g.values())
        assert all(p['entries'][i]['item']['parent'] is None for i in g['resample'])
        for a in ('depth1','depth4','depth16'):
            assert all(p['entries'][i]['item']['parent'] is not None for i in g[a])
    assert all(sum(e['static_opcodes'])==len(e['item']['genome']['genes']) for e in p['entries'].values())

def test_budget_subsets_symmetric_and_known_control_separate():
    p=pool()
    for n in (4,8,16):
        ids=eligible(p,n);assert len(ids)==6+60*n
        assert p['control'] not in {p['entries'][i]['root'] for i in ids if i!=p['control']}
    assert eligible(p,4)<eligible(p,8)<eligible(p,16)
