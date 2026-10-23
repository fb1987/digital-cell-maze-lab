import random
from copy import deepcopy
from maze_evolution import repair_evolution_m32 as m

def fake_rows(items,data):
    rows={}
    for i in items:
        rs=[]
        for cid in data['queries']['all']:
            meta=data['metadata'][cid];reachable=bool(meta['path']);controlled=meta['family'].startswith('controlled_')
            good=reachable and (not controlled or ('/A/' in cid and i['entry']==m.RARE))
            rs.append(dict(case=cid,reachable=reachable,optimal=good,valid=good,no_path=not reachable,
                reads=0,dispatches=0,exposure_checks=0,status='emitted' if reachable else 'no_path',partial=0.,mask='00'))
        rows[i['id']]=rs
    return rows

def test_matched_founders_and_unchanged_models():
    s=m.sources();st=m.founders(s)
    for rep in range(3):
        a,b=st[2*rep:2*rep+2];assert a['population']==b['population'] and a['rng']==b['rng']
        assert len(a['population'])==96 and sum(i['protected'] for i in a['population'])==9
    models={i['id']:i['model'] for i in s['items']}
    assert all(i['model']==models[i['entry']] for state in st for i in state['population'])
    assert not set(s['entries'])&set(s['control_ids'])

def test_complete_rotating_units_and_replay():
    d=m.old_panel();assert len(d['queries']['all'])==811
    for g in range(32):
        t=m.training(g,d);assert t==m.training(g,d) and len(t['queries']['all'])==96
        assert set(t['queries']['all'])<=set(d['queries']['all']) and not t['new_layouts']
        ordinary={}
        for c,x in t['metadata'].items():
            if x['family'] in ('ordinary_perfect','ordinary_random'):ordinary.setdefault(x['base'],[]).append(c)
        assert len(ordinary)==16 and all(len(cs)==2 for cs in ordinary.values())
        assert len([c for c in t['contrasts'] if c['kind']=='route_swap'])==16

def test_bounded_niche_and_no_empty_output_reward():
    s=m.sources();st=m.founders(s)[1];d=m.training(0);rows=fake_rows(st['population'],d)
    survivors,niche,log=m.retain(st['population'],rows,d,random.Random(9),'niche')
    assert len(survivors)==44 and len(niche)<=8 and all(i['protected'] in (True,False) for i in survivors)
    for i in niche:assert i['entry']==m.RARE
    empty=deepcopy(rows)
    for rs in empty.values():
        for r in rs:r['optimal']=r['valid']=r['no_path']=False
    _,niche,_=m.retain(st['population'],empty,d,random.Random(9),'niche');assert not niche

def test_immigrant_is_not_extra_protected_and_entry_model_survives():
    s=m.sources();st=m.founders(s)[0];d=m.training(0);rows=fake_rows(st['population'],d)
    # A nonprotected immigrant entry has its own identity, but never becomes a
    # tenth protected slot just because depth is zero.
    i=st['population'][-1];i.update(id='test/immigrant',entry='test/immigrant',protected=False)
    rows[i['id']]=rows.pop('m32/initial/0/95')
    survivors,_,_=m.retain(st['population'],rows,d,random.Random(2),'shared')
    assert sum(x['protected'] for x in survivors)==9
    specs=m.task_specs([st],d,True,s)
    assert any(i['entry'] in e['aliases'] and e['model']==i['entry_model'] for spec in specs for e in spec)

def test_sequential_variation_is_existing_grammar():
    s=m.sources();g=m.Genome.from_dict(next(i['model']['genome'] for i in s['items'] if i['id']==m.RARE))
    from maze_evolution.connected_evolution_genome import ordinary
    a,b=random.Random(42),random.Random(42)
    for _ in range(30):
        x,e=m.ordinary(g,a);y,f=ordinary(g,b);assert x==y and e==f and a.getstate()==b.getstate()
        assert x.instructions<=256 and all(len(block)<=31 for block in x.body.blocks);g=x

def test_strict_vs_actual_parent_gate_not_conflated():
    c={k:set() for k in (*m.FIELDS,'false')};a=deepcopy(c);ancestor=deepcopy(c)
    c['correct_no_path']={'n'};a['correct_no_path']={'n'};ancestor['pairs']={'old'}
    assert m.gate(c,[a],a,True)['passes']
    assert not m.gate(c,[a,ancestor],a,True)['passes']
    assert not m.gate(c,[a],a,False)['passes']

def test_single_pose_not_complete_ordinary_or_controlled_pair():
    d=m.old_panel();cid=next(c for c,x in d['metadata'].items() if x['family']=='ordinary_perfect');mini=m.subset(d,[cid])
    i=dict(id='x',entry=m.RARE);rs=fake_rows([i],mini)['x'];cap=m.capabilities_plus(rs,mini['metadata']);assert not cap['ordinary_bases']
    swap=next(c for c in d['contrasts'] if c['kind']=='route_swap');assert m.controlled({'success':{swap['a']}},d)[0]==0
