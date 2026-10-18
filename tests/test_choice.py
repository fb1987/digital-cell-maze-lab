from dataclasses import asdict
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import copy,gzip,hashlib,json,random
import pytest
from maze_evolution.choice_fitness import evaluate,priority_fitness,lexicase
from maze_evolution.choice_data import ChoiceData,prior_manifests
from maze_evolution.choice_search import search
from maze_evolution.choice_study import extension_decision
from maze_evolution.junction_fitness import evaluate as old_evaluate
from maze_evolution.regulatory_search import Individual,lexicase as old_lexicase
from maze_evolution.regulatory import Gene,Genome
from maze_evolution.runtime import Limits
from maze_evolution.evaluator import Maze,Oracle
from maze_evolution.goal_data import GoalPair,layout_hash


def test_choice_priority_cannot_override_normal_correctness_and_controls_match():
    flood=(0,0,0,100.,0);choice=(0,0,0,.1,0)
    assert priority_fitness(flood,0,'prefix')>priority_fitness(choice,1,'prefix')
    assert priority_fitness(choice,1,'choice')>priority_fitness(flood,0,'choice')
    for correct in ((1,0,0,0.,0),(0,1,0,0.,0),(0,0,1,0.,0)):
        assert priority_fitness(correct,0,'choice')>priority_fitness(flood,100,'choice')
    assert priority_fitness((1,1,1,2.,-10),0,'prefix')==(1,1,1,0,2.,-10)
    for args in ((flood,-1,'choice'),(flood,1,'bad'),((1,2),0,'prefix')):
        with pytest.raises(ValueError):priority_fitness(*args)


def test_strict_child_replay_is_nonzero_and_pressure_never_changes_inference():
    root=Path(__file__).resolve().parents[1];out=root/'results/junction_choice'
    record=next(r for r in json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read()) if r['condition']=='junction/evolved/junction/1')
    models=record['nodes'];by_id={r['case_id']:r for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read())}
    def oracle(case):
        r=by_id[case];return Oracle.build(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id']))
    pair=GoalPair(oracle(record['first']),oracle(record['second']));limits=Limits(max_steps=1024,reads_per_site=8192,instructions_per_site=131072)
    for node in models:
        item=Individual.load(node['individual']);old=old_evaluate(item,[pair],'evolved',limits,'junction')
        a=evaluate(item,[pair],'evolved',limits,'prefix');b=evaluate(item,[pair],'evolved',limits,'choice')
        assert a.fitness[:3]+a.fitness[4:]==old.fitness==a.smooth_fitness==b.smooth_fitness
        assert a.fitness[3]==0 and b.fitness[3]==b.strict_pairs
        assert a.case_values==[(x,y,0,z) for x,y,z in old.case_values]
        assert a.work==b.work==old.work and a.normal_fitness==b.normal_fitness
        assert a.rows==[{**r,'strict_pair_credit':0} for r in old.rows]
        assert [{k:v for k,v in r.items() if k!='strict_pair_credit'} for r in a.rows]==[{k:v for k,v in r.items() if k!='strict_pair_credit'} for r in b.rows]
    assert b.strict_pairs==1 and b.selection_credit==1 and b.choice_families=={'perfect':1.}
    assert all(row['strict_pair_credit']==1 for row in b.rows)


def test_four_field_lexicase_preserves_prefix_rng_and_prioritizes_choice():
    for seed in range(100):
        rng=random.Random(seed);ranked=[];old=[]
        for i in range(12):
            values=[(rng.randrange(2),rng.randrange(2),rng.random()) for _ in range(4)]
            old.append((SimpleNamespace(case_values=values),str(i)))
            ranked.append((SimpleNamespace(case_values=[(a,b,0,c) for a,b,c in values]),str(i)))
        r1=random.Random(seed);r2=random.Random(seed)
        assert old_lexicase(r1,old)==lexicase(r2,ranked) and r1.getstate()==r2.getstate()
    choices=[(SimpleNamespace(case_values=[(0,0,0,100.)]),'flood'),(SimpleNamespace(case_values=[(0,0,1,.1)]),'choice')]
    assert lexicase(random.Random(0),choices)=='choice'
    choices.append((SimpleNamespace(case_values=[(1,0,0,0.)]),'route'))
    assert lexicase(random.Random(0),choices)=='route'


def test_v9_fresh_capacity_independent_preflight_seed():
    data=ChoiceData(1094,prior_manifests(Path(__file__).resolve().parents[1]))
    for rep in range(3):
        data.validation(rep)
        for generation in range(192):data.batch(rep,generation)
        assert len(data.tests(rep))==88 and len(data.paired_tests(rep))==8
    assert len({layout_hash(o.maze) for o in data.cache.values() if o.maze.split=='test_goal'})==264


def test_v8_supplement_ancestors_common_freeze_and_exact_resume(tmp_path):
    rng=random.Random(1093);forks=[];records={};extra=[]
    for mode in ('junction','balanced'):
        parents=[Individual(f'{mode}/p{i}',Genome((Gene(1,12,i+(mode=='balanced')*100),)),None,48).save() for i in range(32)]
        saved=dict(config=dict(search_version=8,origin='random',pressure=mode,topology='local',replicate=0),population=parents,
            archives={k:{'individual':parents[i]} for i,k in enumerate(('task','junction','balanced','goal','transmission'))},protected=[parents[5]],rng_state=rng.getstate())
        path=tmp_path/(mode+'.json');path.write_text(json.dumps(saved));forks.append(path)
        records[f'junction/local/{mode}/0']={'individual':parents[6]}
        if mode=='junction':extra=[dict(condition='junction/local/junction/0',nodes=[dict(individual=p) for p in parents[7:9]])]
    supplement=tmp_path/'supplement.json';supplement.write_text(json.dumps(dict(records=records)))
    ancestry=tmp_path/'ancestry.json.gz'
    with gzip.open(ancestry,'wt') as f:json.dump(extra,f)
    limits=asdict(Limits(max_steps=16));config=dict(study='choice',search_version=9,origin='random',seed=1093,
        topology='local',pressure='prefix',replicate=0,population=32,generations=3,horizon=8,
        fork_sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in forks],
        supplement_sha256=hashlib.sha256(supplement.read_bytes()).hexdigest(),ancestry_sha256=hashlib.sha256(ancestry.read_bytes()).hexdigest(),
        train_limits=limits,eval_limits=limits)
    data=ChoiceData(1093);validation=data.validation(0)[:1]
    def run(c,name,resume=False):
        path=tmp_path/name
        return search(c,lambda g:data.batch(0,g),validation,StringIO(),StringIO(),[],path,
            fork=forks,supplement=supplement,ancestry=ancestry,resume=path if resume else None,progress=False)
    full=run(config,'full.json');run({**config,'generations':1},'part.json')
    assert run(config,'part.json',True)==full
    other=run({**config,'pressure':'choice','generations':1},'choice.json')
    assert other['initial_digests']==full['initial_digests']
    for label in ('task','goal','balanced','junction','choice','transmission'):
        assert other['frozen'][label]['rank']==full['frozen'][label]['rank']
        assert other['frozen'][label]['individual']['genome']==full['frozen'][label]['individual']['genome']
    saved=json.loads((tmp_path/'full.json').read_text())
    assert len(saved['protected'])==16 and len(saved['population'])==32
    assert {i['id'] for i in saved['protected']}<={i['id'] for i in saved['population']}
    with pytest.raises(ValueError,match='hash'):run({**config,'ancestry_sha256':'bad'},'bad.json')


def test_extension_needs_replicated_transferring_choices_or_correct_routes():
    base=dict(junction=1.,junction_both=0.,choice_families={'perfect':0.,'random':0.})
    champions={}
    for t in ('local','evolved'):
        for p in ('prefix','choice'):
            for rep in range(3):
                a={'choice':dict(base),'task':{'optimal':0}}
                champions[f'choice/{t}/{p}/{rep}']=dict(config=dict(topology=t,pressure=p,replicate=rep),archives=copy.deepcopy(a),frozen=copy.deepcopy(a))
    assert not extension_decision(champions)['extend']
    for rep in (0,1):champions[f'choice/local/choice/{rep}']['archives']['choice'].update(junction_both=.5,choice_families={'perfect':.5,'random':.5})
    assert extension_decision(champions)['goal_topologies']==['local']
    champions['choice/local/choice/1']['archives']['choice']['choice_families']['random']=0
    assert not extension_decision(champions)['extend']
    for rep in (0,1):champions[f'choice/local/choice/{rep}']['archives']['task']['optimal']=1
    assert extension_decision(champions)['route_topologies']==['local']
