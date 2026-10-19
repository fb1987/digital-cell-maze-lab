from copy import deepcopy
import random
from maze_evolution.shared_prefix_data import PrefixData,create,training_ids
from maze_evolution.shared_prefix_search import summary,gate,ranked,nominees,reproduce,update_archives,ARMS
from maze_evolution.shared_prefix_study import make_pools,init_state
from maze_evolution.shared_prefix_audit import geometry
from maze_evolution.exposure_genome import Individual
from maze_evolution.foundation_data import layout_hash

def small():
    d=PrefixData(1314);d.context('fixture',0,2,'straight');d.context('fixture',1,2,'straight');return d

def rows_for(d):
    return [dict(case=c,optimal=m['family']!='disconnected',valid=m['family']!='disconnected',no_path=m['family']=='disconnected',status='no_path' if m['family']=='disconnected' else 'path',reachable=m['family']!='disconnected',partial=.9,reads=1,dispatches=1,exposure_checks=1,mask='00',steps=1) for c,m in d.metadata.items()]

def test_matched_source_graph_and_pair_geometry():
    d=small();g=geometry(d.cache,d.metadata);assert g['inputs']==192 and g['pairs']==32

def test_only_curriculum_forks_change_controls_equal():
    d=small();a=training_ids(d.metadata,0,'current');b=training_ids(d.metadata,0,'mixed')
    controls=lambda ids:{c for c in ids if d.metadata[c]['family']!='paired'}
    assert controls(a)==controls(b)
    assert [d.metadata[c]['prefix'] for c in a if d.metadata[c]['family']=='paired']==[0]*4
    assert sorted(d.metadata[c]['prefix'] for c in b if d.metadata[c]['family']=='paired')==[0,0,1,1]
    assert b==training_ids(d.metadata,0,'resample')

def test_pose_schedule_covers_all_shapes():
    coverage={}
    for g in range(32):coverage.setdefault(g%4,set()).add((g//4)%8)
    assert all(v==set(range(8)) for v in coverage.values())

def test_corpus_counts_and_true_cycle_paths():
    d=create(1,'confirmation',[]);g=geometry(d.cache,d.metadata)
    assert g['inputs']==4032 and g['pairs']==672 and g['contexts']==20
    assert sum(bool(o.path) for o in d.cache.values())==2688

def test_exclusions_include_whole_orbit():
    from maze_evolution.datasets import manifest
    d=small();n=PrefixData(1314,manifest(d.cache.values()));n.context('fixture',0,2,'straight')
    assert not {layout_hash(o.maze) for o in d.cache.values()} & {layout_hash(o.maze) for o in n.cache.values()}
    assert n.rejections>=1

def test_pair_metric_needs_both_correct_goals():
    d=small();rows=rows_for(d);s=summary(rows,d.metadata);assert s['positive']==16 and s['zero']==16
    first=next(r for r in rows if d.metadata[r['case']]['family']=='paired' and d.metadata[r['case']]['prefix']==1);first['optimal']=False
    assert summary(rows,d.metadata)['positive']==15

def test_strict_gate_controls_retention_and_contexts():
    base=dict(positive=0,positive_keys=[],positive_contexts=[],positive_poses=[],zero=16,corridors=64,false_no_path=0)
    win=dict(base,positive=8,positive_keys=[[f'c{i//4}',i%4] for i in range(8)],positive_contexts=['a','b'],positive_poses=[0,1,2,3])
    assert gate(win,base,base,base)
    assert not gate(dict(win,corridors=60),base,base,base)
    assert not gate(win,dict(base,positive=1),base,base)
    assert not gate(dict(win,false_no_path=1),base,base,base)
    assert not gate(dict(win,positive_contexts=['a']),base,base,base)

def test_pools_repeat_and_origins_separate():
    p=make_pools();assert p==make_pools()
    for key,pool in p.items():
        assert len(pool['items'])==96
        if key.startswith('fresh'):
            assert not pool['protected'] and all(i['parent'] is None and i['id'].startswith('shared_prefix/fresh') for i in pool['items'])
        else:assert len(pool['protected'])==9

def test_reproduction_exact_rng_mutation_and_protection():
    d=small();rr=rows_for(d);pool=make_pools()['carry/0'];pop=[Individual.load(i) for i in pool['items']];rows={i.identity:rr for i in pop};rank=ranked(pop,rows,d.metadata);aa={}
    for i in pop:update_archives(aa,i,summary(rr,d.metadata),0)
    s=init_state('carry/0/mixed',pool,aa);new,event=reproduce(s,rank,aa)
    assert (new,event)==reproduce(s,rank,aa)
    assert len(new['population'])==96 and len(event['births'])==72
    assert sum(e['events'] is not None for e in event['births'])==63
    assert {i['id'] for i in pool['protected']} <= {i['id'] for i in new['population']}
    assert all(len(i['genome']['genes'])<=256 for i in new['population'])
    assert len(nominees(rank))==2
    s['arm']='resample';s['key']='carry/0/resample';n,e=reproduce(s,rank,aa)
    assert all(b['events'] is None and b['item']['parent'] is None for b in e['births'])

def test_initial_arms_have_identical_pool_rng():
    pool=make_pools()['fresh/0'];states=[init_state('fresh/0/'+a,pool,{}) for a in ARMS]
    assert all(s['population']==states[0]['population'] and s['rng']==states[0]['rng'] for s in states)
