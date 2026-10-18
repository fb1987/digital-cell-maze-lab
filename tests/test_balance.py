from dataclasses import asdict
from io import StringIO
from pathlib import Path
import copy,hashlib,json,random
import pytest
from maze_evolution.balance_fitness import evaluate,pair_bonuses
from maze_evolution.balance_data import BalanceData,prior_manifests
from maze_evolution.balance_search import search
from maze_evolution.balance_study import extension_decision
from maze_evolution.beacon_fitness import evaluate as old_evaluate
from maze_evolution.regulatory import Gene,Genome,random_genome
from maze_evolution.regulatory_search import Individual
from maze_evolution.runtime import Limits
from maze_evolution.goal_data import layout_hash


def test_balanced_reward_symmetry_maximum_and_weaker_goal_pressure():
    assert pair_bonuses((1.,1.),'mean')==pair_bonuses((1.,1.),'balanced')==(2.,2.)
    assert pair_bonuses((1.,0.),'mean')==(2.,0.)
    assert pair_bonuses((1.,0.),'balanced')==(1.,0.)
    for pressure in ('mean','balanced'):
        assert pair_bonuses((.8,.2),pressure)==tuple(reversed(pair_bonuses((.2,.8),pressure)))
        assert pair_bonuses((1.,0.),pressure,False)==(2.,0.)
    # Equal maximum, but only the balanced objective prefers moderate two-sided growth.
    assert sum(pair_bonuses((1.,0.),'mean'))>sum(pair_bonuses((.4,.4),'mean'))
    assert sum(pair_bonuses((1.,0.),'balanced'))<sum(pair_bonuses((.4,.4),'balanced'))
    for scores in ((-1,0),(0,2),(1,),(float('nan'),0)):
        with pytest.raises(ValueError):pair_bonuses(scores,'balanced')
    with pytest.raises(ValueError):pair_bonuses((0,0),'bad')


def test_mean_matches_v6_and_pressure_never_changes_normal_inference_or_probes():
    rng=random.Random(1071);data=BalanceData(1071);pairs=data.validation(0);limits=Limits(max_steps=32)
    for _ in range(3):
        item=Individual('unit',random_genome(rng,True),None,0)
        old=old_evaluate(item,pairs,'evolved',limits,'pulse')
        mean=evaluate(item,pairs,'evolved',limits,'mean');balanced=evaluate(item,pairs,'evolved',limits,'balanced')
        assert old.fitness==mean.fitness and old.case_values==mean.case_values
        for key in old.__dict__:
            if key!='rows':assert old.__dict__[key]==mean.__dict__[key]
        for a,b,c in zip(old.rows,mean.rows,balanced.rows):
            assert a=={k:v for k,v in b.items() if k!='pair_min_goal'}
            assert {k:v for k,v in b.items() if k!='factor_bonus'}=={k:v for k,v in c.items() if k!='factor_bonus'}
        assert mean.work==balanced.work==mean.inference_work+mean.probe_work
        assert mean.normal_fitness==balanced.normal_fitness
        assert balanced.fitness[3]<=mean.fitness[3]
        regular=[min(mean.rows[2*j+i]['goal']['score'] for i in (0,1)) for j,p in enumerate(pairs) if not p.mixed]
        assert mean.balanced_goal==balanced.balanced_goal==sum(regular)/len(regular)
        for j,p in enumerate(pairs):
            if p.mixed:assert all(mean.rows[2*j+i]['factor_bonus']==balanced.rows[2*j+i]['factor_bonus'] for i in (0,1))


def test_v7_fresh_data_capacity_uses_independent_preflight_seed():
    data=BalanceData(1074,prior_manifests(Path(__file__).resolve().parents[1]))
    for rep in range(3):
        data.validation(rep)
        for generation in range(192):data.batch(rep,generation)
        assert len(data.tests(rep))==88 and len(data.paired_tests(rep))==8
    assert len({layout_hash(o.maze) for o in data.cache.values() if o.maze.split=='test_goal'})==264


def test_v6_elites_supplement_common_freeze_and_exact_resume(tmp_path):
    rng=random.Random(1072);forks=[];records={}
    for mode in ('pulse','flag'):
        parents=[Individual(f'{mode}/p{i}',Genome((Gene(1,12,i+(mode=='flag')*100),)),None,48).save() for i in range(16)]
        archive={k:{'individual':parents[i]} for i,k in enumerate(('task','goal','transmission'))}
        saved=dict(config=dict(search_version=6,origin='random',pressure=mode,topology='local',replicate=0),
            population=parents,archives=archive,protected=[parents[3]],rng_state=rng.getstate())
        path=tmp_path/(mode+'.json');path.write_text(json.dumps(saved));forks.append(path)
        records[f'beacon/local/{mode}/0']={'individual':parents[4]}
    supplement=tmp_path/'supplement.json';supplement.write_text(json.dumps(dict(records=records)))
    limits=asdict(Limits(max_steps=16));config=dict(study='balance',search_version=7,origin='random',seed=1072,
        topology='local',pressure='mean',replicate=0,population=16,generations=3,horizon=8,
        fork_sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in forks],
        supplement_sha256=hashlib.sha256(supplement.read_bytes()).hexdigest(),train_limits=limits,eval_limits=limits)
    data=BalanceData(1072);validation=data.validation(0)[:1]
    def run(c,name,resume=False):
        path=tmp_path/name
        return search(c,lambda g:data.batch(0,g),validation,StringIO(),StringIO(),[],path,
            fork=forks,supplement=supplement,resume=path if resume else None,progress=False)
    full=run(config,'full.json');run({**config,'generations':1},'part.json')
    assert run(config,'part.json',True)==full
    other=run({**config,'pressure':'balanced','generations':1},'balanced.json')
    assert other['initial_digests']==full['initial_digests']
    for label in ('task','goal','balanced','transmission'):
        assert other['frozen'][label]['rank']==full['frozen'][label]['rank']
        assert other['frozen'][label]['individual']['genome']==full['frozen'][label]['individual']['genome']
    saved=json.loads((tmp_path/'full.json').read_text())
    assert len(saved['protected'])==10 and len(saved['population'])==16
    assert {i['id'] for i in saved['protected']}<={i['id'] for i in saved['population']}
    with pytest.raises(ValueError,match='hash'):run({**config,'supplement_sha256':'bad'},'bad.json')


def test_extension_requires_routes_or_replicated_balanced_quality_not_transmission():
    base=dict(balanced=0.,balanced_families={'perfect':0.,'random':0.},goal=0.,quality=0.,specificity=0.,
        both=0.,signal=.5,valid=0,optimal=0)
    champions={}
    for topology in ('local','evolved'):
        for pressure in ('mean','balanced'):
            for rep in range(3):
                archives={'balanced':dict(base),'task':{'optimal':0},'transmission':{'signal':.5}}
                champions[f'balance/{topology}/{pressure}/{rep}']=dict(
                    config=dict(topology=topology,pressure=pressure,replicate=rep),archives=copy.deepcopy(archives),frozen=copy.deepcopy(archives))
    assert not extension_decision(champions)['extend']
    for rep in (0,1):
        r=champions[f'balance/local/balanced/{rep}']['archives']['balanced']
        r.update(balanced=.1,balanced_families={'perfect':.1,'random':.1},quality=.2,specificity=.2,both=.5)
    assert extension_decision(champions)['goal_topologies']==['local']
    champions['balance/local/balanced/1']['archives']['balanced'].update(balanced=0.,signal=1.)
    assert not extension_decision(champions)['extend']
    for rep in (0,1):champions[f'balance/local/balanced/{rep}']['archives']['task']['optimal']=1
    assert extension_decision(champions)['route_topologies']==['local']
