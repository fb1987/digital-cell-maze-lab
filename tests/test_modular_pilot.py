import random
from copy import deepcopy
from maze_evolution.foundation_study import read_compressed as readz
from maze_evolution.modular_pilot_search import founders,rank,retain,values,lexicase
from maze_evolution.modular_pilot import evaluate_task,task_specs,transition
from maze_evolution.deep_campaign_store import packed,unpacked


def test_pairing_and_no_control_ancestors():
    states=founders(202610201010)
    assert len(states)==24
    for rep in ('flat','modular'):
        for r in range(3):
            group=[s for s in states if s['representation']==rep and s['replicate']==r]
            assert all(s['population']==group[0]['population'] for s in group)
            assert all(i['root']==i['id'] and i['parent'] is None for s in group for i in s['population'])
    assert len({i['id'] for s in states for i in s['population']})==576


def test_rewards_empty_flood_and_correct():
    meta={'a':dict(family='ordinary_perfect'),'b':dict(family='ordinary_disconnected')}
    bad=[dict(case='a',optimal=False,valid=False,no_path=False,reachable=True,status='no_path',partial=0),dict(case='b',optimal=False,valid=False,no_path=True,reachable=False,status='no_path',partial=0)]
    zero=deepcopy(bad);zero[0]['status']='invalid';zero[1]['no_path']=False
    good=deepcopy(bad);good[0].update(optimal=True,valid=True,status='emitted')
    assert rank(bad,meta)[0]==rank(zero,meta)[0]==0
    assert rank(good,meta)[0]==1
    assert values(bad)[0]<values(zero)[0]


def test_complete_generation_replay():
    states=readz('results/modular_pilot/fixture_founders.json.gz')
    fixture=readz('results/modular_pilot/fixture.json.gz');receipts=readz('results/modular_pilot/fixture_receipts.json.gz')
    assessed,decision=transition(states,fixture,receipts)
    assert assessed==transition(unpacked(packed(states)),unpacked(packed(fixture)),unpacked(packed(receipts)))[0]
    # Real training outputs on discarded fixture, all conditions and all 1,248 births.
    batch=readz('results/modular_pilot/fixture_train.json.gz')[0]
    ids=set(c for q in batch['queries'].values() for c in q)
    mazes=[m for m in batch['mazes'] if m['case_id'] in ids]
    results=[evaluate_task(s,mazes,'rehearsal') for s in task_specs(assessed,batch)]
    child,events=transition(assessed,batch,results)
    replay,revents=transition(unpacked(packed(assessed)),unpacked(packed(batch)),unpacked(packed(results)))
    assert child==replay and events==revents
    assert all(s['generation']==1 and len(s['population'])==96 for s in child)
    assert sum(len(e['births']) for e in events)==1248
    from maze_evolution.foundation_study import compressed_json as writez
    from pathlib import Path
    if not Path('results/modular_pilot/registration.json').exists():
        writez('results/modular_pilot/rehearsal.json.gz',dict(input_hash=__import__('hashlib').sha256(packed(assessed)).hexdigest(),results=results,states=child,decisions=events))
    else:
        saved=readz('results/modular_pilot/rehearsal.json.gz');assert saved['states']==child and saved['decisions']==events
