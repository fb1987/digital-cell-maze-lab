from dataclasses import asdict
from io import StringIO
from pathlib import Path
import hashlib,json,random
import pytest
from maze_evolution.factor_data import FactorData,prior_manifests
from maze_evolution.factor_fitness import curriculum_alpha,factor_bonus,evaluate
from maze_evolution.factor_search import search
from maze_evolution.goal_data import layout_hash
from maze_evolution.goal_fitness import evaluate as old_evaluate
from maze_evolution.regulatory import Genome,Gene,random_genome
from maze_evolution.regulatory_search import Individual
from maze_evolution.runtime import Limits


def test_factor_schedule_bounded_and_converges_to_product():
    assert [curriculum_alpha('curriculum',g) for g in (0,15,16,23,31,32,191)]==[0.,0.,1/16,.5,1.,1.,1.]
    q=dict(quality=1.,specificity=0.,score=0.,aligned=True)
    assert factor_bonus(q,0)==1 and factor_bonus(q,1)==0
    q.update(specificity=1.,score=1.)
    assert all(factor_bonus(q,a)==2 for a in (0,.5,1))
    assert factor_bonus(q,0,False)==0
    q['aligned']=False;assert factor_bonus(q,0)==0
    with pytest.raises(ValueError):curriculum_alpha('bad',0)
    with pytest.raises(ValueError):factor_bonus(q,2)


def test_factor_probe_work_and_product_match_v4():
    item=Individual('unit',random_genome(random.Random(1056),True),None,0)
    pairs=FactorData(1056).batch(0,0);limits=Limits(max_steps=32)
    old=old_evaluate(item,pairs,'evolved',limits,'goal')
    product=evaluate(item,pairs,'evolved',limits,'product')
    dense=evaluate(item,pairs,'evolved',limits,'curriculum',generation=0)
    late=evaluate(item,pairs,'evolved',limits,'curriculum',generation=32)
    assert product.fitness==old.fitness==late.fitness
    assert dense.fitness[:3]==product.fitness[:3] and dense.normal_fitness==product.normal_fitness
    assert dense.work==product.work==old.work
    assert dense.fitness[3]>=product.fitness[3]


def test_v5_fresh_data_preflight_against_all_prior_layouts():
    d=FactorData(1057,prior_manifests(Path(__file__).resolve().parents[1]))
    for rep in range(3):
        d.validation(rep)
        for generation in range(192):d.batch(rep,generation)
        assert len(d.tests(rep,8))==88 and len(d.paired_tests(rep))==8
    assert len({layout_hash(o.maze) for o in d.cache.values() if o.maze.split=='test_goal'})==264
    for p in d.pairs.values():
        a,b=p.cases;assert len(a.path)-1>=8
        if p.mixed:assert not b.path
        else:assert a.to_goal[b.maze.goal]>=max(len(a.path)-1,len(b.path)-1)>=8


def test_v5_elite_protection_and_exact_curriculum_resume(tmp_path):
    rng=random.Random(1058);parents=[Individual(f'parent/{i}',random_genome(rng,True),None,40).save() for i in range(4)]
    learned=Individual('goal_variant',Genome((Gene(13,2,9),)),None,25).save()
    ancestor=dict(config=dict(search_version=4,origin='random',pressure='goal',topology='local'),
        population=parents,protected=parents[0],archives={'goal':{'individual':learned}},rng_state=rng.getstate())
    fork=tmp_path/'fork.json';fork.write_text(json.dumps(ancestor));limits=asdict(Limits(max_steps=16))
    config=dict(study='factor',topology='local',pressure='curriculum',replicate=0,population=4,generations=34,
        horizon=8,fork_sha256=hashlib.sha256(fork.read_bytes()).hexdigest(),train_limits=limits,eval_limits=limits)
    data=FactorData(1058);val=data.validation(0)[:1]
    def run(c,path,resume=None,deadline=None):
        return search(c,lambda g:data.batch(0,g),val,StringIO(),StringIO(),[],path,fork=fork,resume=resume,deadline=deadline,progress=False)
    # Small populations require room for fixed elites, niches and immigrants.
    # Both protected genomes are present and are never replaced by a validation archive.
    full=run(config,tmp_path/'full.json')
    run({**config,'generations':23},tmp_path/'part.json')
    assert run(config,tmp_path/'part.json',tmp_path/'part.json')==full
    checkpoint=json.loads((tmp_path/'full.json').read_text())
    assert len(checkpoint['population'])==4 and len(checkpoint['protected'])==2
    assert {p['id'] for p in checkpoint['protected']} <= {p['id'] for p in checkpoint['population']}
    other=run({**config,'pressure':'product','generations':1},tmp_path/'control.json')
    assert other['initial_digests']==full['initial_digests']
    assert full['fork_injection'][0]['replaced_parent']=='parent/3'
    with pytest.raises(ValueError,match='hash'):run({**config,'fork_sha256':'bad'},tmp_path/'bad.json')
