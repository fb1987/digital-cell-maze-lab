import random
from copy import deepcopy
from maze_evolution.wave_continuation import OUT,readz,task_specs
from maze_evolution.wave_continuation_search import transition,retain,rank
from maze_evolution.wave_continuation_analysis import complex_sets
from maze_evolution.deep_campaign_store import packed,unpacked,hashed


def test_matched_founders_and_exact_protection():
    states=readz(OUT/'founders.json.gz')
    assert len(states)==6
    for k in range(0,6,2):
        a,b=states[k:k+2];assert a['population']==b['population'] and a['protected']==b['protected']
        assert len(a['protected'])==6 and len(a['population'])==96
        assert all(i['origin']=='preserved_M2' and i['root']==i['id'] and i['parent'] is None for i in a['population'])
        assert all(not i['id'].startswith('control/') for i in a['population'])


def test_all_rehearsal_transitions_and_equal_allocations():
    states=readz(OUT/'fixture_founders.json.gz');steps=readz(OUT/'rehearsal.json.gz')
    assert len(steps)==5
    births=0
    for step in steps:
        data=step['data'];specs=task_specs(states,data);counts=[0]*6
        for task in specs:
            for e in task:
                for k,identity in e['aliases']:counts[k]+=len(e['queries'])
        assert len(set(counts))==1
        states,events=transition(unpacked(packed(states)),data,step['receipts'])
        assert events==step['decisions'] and hashed(packed(states))==step['state_hash']
        for s,e in zip(states,events):
            for i in s['protected']:assert next(p for p in s['population'] if p['id']==i['id'])==i
            if data['kind']=='train':
                bs=e['births'];births+=len(bs)
                assert len(bs)==52 and sum(not b['events'] for b in bs)==7
                counts=[len(b['events']) for b in bs]
                assert counts.count(2)==(22 if s['method']=='mixed' else 0)
                for b in bs:
                    assert b['item']['id'].startswith('m3-fixture/')
                    if len(b['events'])==2:assert b['events'][0]['after']==b['events'][1]['before'] and b['intermediate'] is not None
    assert births==1248


def test_longer_route_strata_and_rejected_layouts_preserved():
    step=readz(OUT/'rehearsal.json.gz')[1];data=step['data'];queries=data['queries']['long'];meta=data['metadata']
    assert len(queries)==48
    ordinary=[meta[c] for c in queries if meta[c]['family'] in ('ordinary_perfect','ordinary_random')]
    assert len(ordinary)==24 and all(len(m['path'])-1>=8 for m in ordinary)
    assert sum(m['length_bin']=='long' for m in ordinary)==6
    assert len(data['mazes'])>len(queries)
    assert any(v>1 for v in data['length_sampling_attempts'].values())


def test_neutral_reserve_is_genotype_distinct_and_protected():
    s=readz(OUT/'founders.json.gz')[0];items=s['population']
    row=dict(case='c',status='emitted',mask='01',optimal=True,valid=True,no_path=False,reachable=True,partial=1.)
    rows={i['id']:[dict(row)] for i in items};meta={'c':dict(family='ordinary_perfect',length_bin='medium')}
    chosen,neutral=retain(items,rows,meta,random.Random(42),s['protected'])
    assert len(chosen)==44 and len(neutral)==18
    assert len({i['id'] for i in chosen})==44
    assert all(i in chosen for i in s['protected'])
    from maze_evolution.modular_genome import Genome
    selected=[i for i in chosen if i['id'] in neutral]
    assert len({Genome.from_dict(i['genome']).digest for i in selected})==18


def test_complexity_metrics_exclude_easy_paths():
    meta={'p0':dict(family='paired',base='f0',pose=0,prefix=0,graph='fork'),
          'p2':dict(family='paired',base='f2',pose=0,prefix=2,graph='fork'),
          'c0':dict(family='paired',base='c0',pose=0,prefix=0,graph='cycle'),
          'o7':dict(family='ordinary_random',base='o7',path=list(range(8))),
          'o8':dict(family='ordinary_random',base='o8',path=list(range(9)))}
    cap=dict(pairs={('f0',0),('f2',0),('c0',0)},ordinary_bases={'o7','o8'})
    x=complex_sets(cap,meta)
    assert x['hard_pairs']=={('f2',0),('c0',0)} and x['multi_pairs']=={('c0',0)}
    assert x['long_bases']=={'o8'}


def test_report_gates_and_json_roundtrip_on_saved_software_responses(monkeypatch):
    import json
    from maze_evolution import wave_continuation_analysis as a
    data=readz(OUT/'fixture.json.gz');root=readz(OUT/'rehearsal.json.gz')[0]['receipts'][0]['entries'][0]['rows']
    control=readz(OUT/'control_fixture.json.gz')['entries'][0]['rows']
    comparisons=[];roles={'root':[]}
    for rep in range(3):
        for method in ('single','mixed'):
            name=f'modular/{rep}/{method}'
            roles['root'].append([name,'protected',0])
            for r in (0,1):
                roles['root'].append([name,'frozen',r])
                comparisons.append(dict(condition=name,rank=r,child='software_control_response',root='root',parent='root',mutations=1))
    choices=dict(comparisons=comparisons,roles=roles)
    monkeypatch.setattr(a,'readz',lambda path:choices)
    result=a.compute_summary(data,{'root':root,'software_control_response':control},{},'software')
    assert result==json.loads(json.dumps(result))
    assert all(c['hard_pair_acquisition'] and c['long_ordinary_acquisition'] and c['substantial_transfer'] for c in result['conditions'])
    assert result['mixed_replicate_screen']==[False,False,False]
    # A neutral descendant must not be credited for hard skills already present
    # in its exact M3 founder, even if protected anchors lack those skills.
    choices['roles']['root']=[r for r in choices['roles']['root'] if r[1]!='protected']
    choices['roles']['protected']=[[f'modular/{rep}/{method}','protected',0] for rep in range(3) for method in ('single','mixed')]
    result=a.compute_summary(data,{'root':control,'software_control_response':control,'protected':root},{},'software')
    assert all(not c['hard_pair_acquisition'] and not c['long_ordinary_acquisition'] for c in result['conditions'])


def test_runner_zero_round_boundary_freezes_and_stops_without_new_inference(tmp_path,monkeypatch):
    """Exercise real journal, initial assessment, clock, final freeze and no restart."""
    import json
    from contextlib import nullcontext
    from maze_evolution import wave_continuation as m
    fixture=readz(OUT/'rehearsal.json.gz')[0]
    founders=readz(OUT/'fixture_founders.json.gz')
    out=tmp_path/'results';out.mkdir();run=tmp_path/'run'
    m.writez(out/'founders.json.gz',founders);m.writez(out/'exclusions.json.gz',dict(hashes=[],count=0))
    monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run)
    monkeypatch.setattr(m,'check',lambda:dict(m.CONFIG,max_rounds=0))
    monkeypatch.setattr(m,'pushed',lambda _:None)
    monkeypatch.setattr(m,'ProcessPoolExecutor',lambda *a,**k:nullcontext(None))
    monkeypatch.setattr(m.data_builder,'validation',lambda *a:deepcopy(fixture['data']))
    def saved_stage(j,n,data,*args):
        assert n==0 and data==fixture['data']
        for k,r in enumerate(fixture['receipts']):
            j.reserve(n,k,r['calls'],r['work']);j.receipt(n,k,r,r['work'])
        return None
    monkeypatch.setattr(m.shared,'run_stage',saved_stage)
    m.run()
    result=json.loads((out/'session.json').read_text())
    assert result['status']=='complete' and result['stop']['reason']=='round_ceiling' and result['generation']==0
    assert result['usage']['calls']==sum(r['calls'] for r in fixture['receipts'])
    choices=m.readz(out/'choices.json.gz');assert len(choices['comparisons'])==12
    assert all(c['mutations']==0 for c in choices['comparisons'])
    before=(out/'choices.json.gz').read_bytes();m.run();assert (out/'choices.json.gz').read_bytes()==before
