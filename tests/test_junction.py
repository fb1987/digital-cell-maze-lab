from dataclasses import asdict
from io import StringIO
from pathlib import Path
import copy,hashlib,json,random
import numpy as np
import pytest
from maze_evolution.junction_fitness import evaluate,decision,junction_metrics
from maze_evolution.junction_data import JunctionData,prior_manifests
from maze_evolution.junction_search import search
from maze_evolution.junction_study import extension_decision
from maze_evolution.balance_fitness import evaluate as control_evaluate
from maze_evolution.regulatory import Gene,Genome,random_genome
from maze_evolution.regulatory_search import Individual
from maze_evolution.runtime import Limits
from maze_evolution.goal_data import layout_hash


def test_junction_correct_choices_source_causality_and_suppression():
    pair=JunctionData(1081).validation(0)[0];label=decision(pair);n=pair.first.maze.w*pair.first.maze.h
    masks=[]
    for want in label['allowed']:
        mask=np.zeros(n,dtype=np.uint8);mask[label['prefix']+[want[0]]]=1;masks.append(mask)
    empty=[np.zeros(n,dtype=np.uint8)]*2
    rows=junction_metrics(masks,empty,pair,label)
    assert all(r['score']==1 and r['strict'] and r['pair_both'] for r in rows)
    assert not any(r['strict'] for r in junction_metrics(masks,masks,pair,label))
    assert all(r['score']==0 for r in junction_metrics(masks,masks,pair,label))
    flood=masks[0]|masks[1]
    rows=junction_metrics([flood,flood],empty,pair,label)
    assert not any(r['strict'] or r['pair_both'] for r in rows)
    cut=[m.copy() for m in masks]
    for m in cut:m[label['prefix'][1]]=0
    assert not any(r['strict'] for r in junction_metrics(cut,empty,pair,label))
    assert all(r['score']==0 for r in junction_metrics(masks,empty,pair,label,aligned=False))


def test_cyclic_shortest_ties_are_sets_not_arbitrary_bfs_choice():
    data=JunctionData(1084)
    pairs=[p for r in range(3) for p in data.validation(r)]
    pair=next(p for p in pairs if decision(p) and any(len(a)>1 for a in decision(p)['allowed']))
    label=decision(pair);assert not set(label['allowed'][0])&set(label['allowed'][1])
    for side in (0,1):
        for chosen in label['allowed'][side]:
            n=pair.first.maze.w*pair.first.maze.h;mask=np.zeros(n,dtype=np.uint8)
            mask[label['prefix']+[chosen]]=1
            rows=junction_metrics([mask,mask],[np.zeros(n,dtype=np.uint8)]*2,pair,label)
            assert rows[side]['strict'] and rows[side]['score']==1
            assert not rows[1-side]['strict']


def test_v8_pressure_changes_only_fitness_not_inference_or_probes():
    rng=random.Random(1082);pairs=JunctionData(1082).validation(0);limits=Limits(max_steps=32)
    for _ in range(3):
        item=Individual('unit',random_genome(rng,True),None,0)
        old=control_evaluate(item,pairs,'evolved',limits,'balanced')
        a=evaluate(item,pairs,'evolved',limits,'balanced');b=evaluate(item,pairs,'evolved',limits,'junction')
        assert a.fitness==old.fitness and a.case_values==old.case_values
        assert a.normal_fitness==b.normal_fitness and a.work==b.work==old.work
        for x,y,z in zip(old.rows,a.rows,b.rows):
            assert x=={k:v for k,v in y.items() if k!='junction'}
            assert {k:v for k,v in y.items() if k!='factor_bonus'}=={k:v for k,v in z.items() if k!='factor_bonus'}
        for i,p in enumerate(pairs):
            if p.mixed:assert [r['factor_bonus'] for r in a.rows[2*i:2*i+2]]==[r['factor_bonus'] for r in b.rows[2*i:2*i+2]]
    with pytest.raises(ValueError):evaluate(item,pairs,'local',limits,'unknown')


def test_v8_fresh_data_capacity_independent_preflight_seed():
    data=JunctionData(1084,prior_manifests(Path(__file__).resolve().parents[1]))
    for rep in range(3):
        data.validation(rep)
        for generation in range(192):data.batch(rep,generation)
        assert len(data.tests(rep))==88 and len(data.paired_tests(rep))==8
    assert len({layout_hash(o.maze) for o in data.cache.values() if o.maze.split=='test_goal'})==264
    for p in data.pairs.values():
        label=decision(p)
        if p.mixed:assert label is None;continue
        assert label and 2<=label['distance']<=8
        assert all(o.to_goal[label['vertex']]>=4 for o in p.cases)
        index=int(p.first.maze.case_id.split('/p')[1].split('/')[0])
        if index%2==0:assert any(label['detours'])
    assert any(len(a)>1 for p in data.pairs.values() if not p.mixed for a in decision(p)['allowed'])


def test_v7_common_fork_preservation_freeze_and_exact_resume(tmp_path):
    rng=random.Random(1083);forks=[]
    for mode in ('balanced','mean'):
        parents=[Individual(f'{mode}/p{i}',Genome((Gene(1,12,i+(mode=='mean')*100),)),None,48).save() for i in range(16)]
        saved=dict(config=dict(search_version=7,origin='random',pressure=mode,topology='local',replicate=0),
            population=parents,archives={k:{'individual':parents[i]} for i,k in enumerate(('task','balanced','goal','transmission'))},
            protected=[parents[4]],rng_state=rng.getstate())
        path=tmp_path/(mode+'.json');path.write_text(json.dumps(saved));forks.append(path)
    limits=asdict(Limits(max_steps=16));config=dict(study='junction',search_version=8,origin='random',seed=1083,
        topology='local',pressure='balanced',replicate=0,population=16,generations=3,horizon=8,
        fork_sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in forks],train_limits=limits,eval_limits=limits)
    data=JunctionData(1083);validation=data.validation(0)[:1]
    def run(c,name,resume=False):
        path=tmp_path/name
        return search(c,lambda g:data.batch(0,g),validation,StringIO(),StringIO(),[],path,
            fork=forks,resume=path if resume else None,progress=False)
    full=run(config,'full.json');run({**config,'generations':1},'part.json')
    assert run(config,'part.json',True)==full
    other=run({**config,'pressure':'junction','generations':1},'junction.json')
    assert other['initial_digests']==full['initial_digests']
    for label in ('task','goal','balanced','junction','transmission'):
        assert other['frozen'][label]['rank']==full['frozen'][label]['rank']
        assert other['frozen'][label]['individual']['genome']==full['frozen'][label]['individual']['genome']
    saved=json.loads((tmp_path/'full.json').read_text())
    assert len(saved['protected'])==10 and len(saved['population'])==16
    assert {i['id'] for i in saved['protected']}<={i['id'] for i in saved['population']}
    with pytest.raises(ValueError,match='hash'):run({**config,'fork_sha256':['bad','bad']},'bad.json')


def test_extension_requires_replicated_choices_or_routes_not_prefix_alone():
    champions={};base=dict(junction=.25,junction_both=0.,junction_families={'perfect':.25,'random':.25})
    for t in ('local','evolved'):
        for p in ('balanced','junction'):
            for r in range(3):
                a={'junction':dict(base),'task':{'optimal':0}}
                champions[f'junction/{t}/{p}/{r}']=dict(config=dict(topology=t,pressure=p,replicate=r),archives=copy.deepcopy(a),frozen=copy.deepcopy(a))
    assert not extension_decision(champions)['extend']
    for r in (0,1):champions[f'junction/local/junction/{r}']['archives']['junction'].update(junction=.5,junction_both=.5)
    assert extension_decision(champions)['goal_topologies']==['local']
    champions['junction/local/junction/1']['archives']['junction']['junction_both']=0
    assert not extension_decision(champions)['extend']
    for r in (0,1):champions[f'junction/local/junction/{r}']['archives']['task']['optimal']=1
    assert extension_decision(champions)['route_topologies']==['local']
