"""Regression gates for ancestry, honest controls and extended unseen geometry."""
from copy import deepcopy
from types import SimpleNamespace
import random
import pytest
from maze_evolution.family_evolution_search import *
from maze_evolution.family_evolution_study import make_pools
from maze_evolution.family_evolution_data import AccessData
from maze_evolution.family_evolution_audit import geometry

@pytest.fixture(scope='module')
def pools():return make_pools()

def ranking(s):
    return [(SimpleNamespace(rows=[dict(mask=str(k%7),status='path')],fitness=(0,0,0,0,k),case_values=[(0,0,0,k)]),Individual.load(r)) for k,r in enumerate(s['population'])]

@pytest.mark.parametrize('arm',ARMS)
def test_three_generation_exact_control_replay(pools,arm):
    s=init_state('carry/0/'+arm,pools['carry/0']);original=deepcopy(s);ever=set(r['id'] for r in s['population'])
    for g in range(3):
        before=deepcopy(s);rank=ranking(s);new,e=reproduce(s,rank,{})
        assert (new,e)==reproduce(s,rank,{}) and s==before
        assert_population(new)
        if arm=='frozen':assert new['population']==original['population'] and new['rng']==original['rng']
        else:
            assert len(e['elite'])==44 and len(e['births'])==52
            assert sum(x['mutation'] is not None for x in e['births'])==(0 if arm=='resample' else 45)
            for birth in e['births']:
                assert birth['item']['id'] not in ever;ever.add(birth['item']['id'])
                if birth['parents']:assert birth['family']==s['families'][birth['parents'][0]]
        s=new

def test_founders_random_and_homology_explicit(pools):
    assert pools==make_pools()
    for key,p in pools.items():
        assert len(p['items'])==96 and len(p['protected'])==(20 if key.startswith('carry') else 0)
        if key.startswith('fresh'):
            assert all(r['parent'] is None and 64<=len(r['genome']['genes'])<=128 and r['id'].startswith('family_z/') for r in p['items'])
    counts=Counter(pools['carry/0']['families'].values());assert counts['known_U_d07']==2

def test_extended_bent_and_cyclic_geometry():
    d=AccessData(23456789,())
    for i,(shape,stress) in enumerate([('straight',False),('turning',False),('straight',True)]):
        d.context('unit',i,(4,6),shape,(0,1,2,4,8),stress)
    report=geometry(d.cache,d.metadata);assert report['pairs']==200
    for cid,o in d.cache.items():
        m=d.metadata[cid]
        if m['family']=='paired':assert len(o.path)-1==m['prefix']+m['arm'][m['side']]

def test_archive_long_rank_and_retained_metadata(pools):
    m=dict(long=0,cycle=100,positive=100,pairs=100,corridors=100,ordinary=100,no_path=0,false_no_path=0,partial=1,zero=0)
    n=dict(m,long=1,cycle=0,positive=1)
    assert archive_rank(n,'primary')>archive_rank(m,'primary')
    i=Individual.load(pools['fresh/0']['items'][0]);aa={};line=dict(family='root',gene_ids=['a'])
    update_archives(aa,i,m,0,line);line['gene_ids'].append('b');assert aa['primary']['ancestry']['gene_ids']==['a']

def test_gate_requires_retaining_actual_cases():
    def met():return dict(prefix4=0,prefix4_keys=[],cycle_keys=[],all_keys=[],corridor_keys=[],ordinary_keys=[],false_no_path=0)
    f=met();f['corridor_keys']=['old'];t=met();t.update(prefix4=16,prefix4_keys=[[str(k),0] for k in range(16)],cycle_keys=[[str(k),0] for k in range(8)],corridor_keys=['replacement'])
    meta={str(k):dict(family='paired',base=str(k),pose=0,template='c'+str(k//8)) for k in range(16)}
    assert not gate(t,[f],f,meta)['passed']
    t['corridor_keys']=['old'];assert gate(t,[f],f,meta)['passed']
