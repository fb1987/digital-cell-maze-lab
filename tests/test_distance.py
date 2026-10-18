from dataclasses import asdict
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import copy,gzip,hashlib,json,random
import numpy as np
import pytest
from maze_evolution.distance_data import DistanceData,prior_manifests,cue_distances
from maze_evolution.distance_fitness import evaluate,decision
from maze_evolution.distance_search import search
from maze_evolution.distance_study import extension_decision
from maze_evolution.choice_fitness import evaluate as old_evaluate
from maze_evolution.junction_fitness import decision as old_decision,junction_metrics
from maze_evolution.regulatory_search import Individual
from maze_evolution.regulatory import Gene,Genome,random_genome
from maze_evolution.runtime import Limits
from maze_evolution.goal_data import layout_hash


def test_v9_supplement_ancestors_common_freeze_and_exact_resume(tmp_path):
    rng=random.Random(1093);forks=[];records={};extra=[]
    for mode in ('choice','prefix'):
        parents=[Individual(f'{mode}/p{i}',Genome((Gene(1,12,i+(mode=='prefix')*100),)),None,48).save() for i in range(32)]
        saved=dict(config=dict(search_version=9,origin='random',pressure=mode,topology='local',replicate=0),population=parents,
            archives={k:{'individual':parents[i]} for i,k in enumerate(('task','choice','junction','balanced','goal','transmission'))},protected=[parents[6]],rng_state=rng.getstate())
        path=tmp_path/(mode+'.json');path.write_text(json.dumps(saved));forks.append(path)
        records[f'choice/local/{mode}/0']={'individual':parents[7]}
        if mode=='choice':extra=[dict(condition='choice/local/choice/0',nodes=[dict(individual=p) for p in parents[8:10]])]
    supplement=tmp_path/'supplement.json';supplement.write_text(json.dumps(dict(records=records)))
    ancestry=tmp_path/'ancestry.json.gz'
    with gzip.open(ancestry,'wt') as f:json.dump(extra,f)
    limits=asdict(Limits(max_steps=16));config=dict(study='distance',search_version=10,origin='random',seed=1093,
        topology='local',pressure='fixed',replicate=0,population=32,generations=17,horizon=8,
        fork_sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in forks],
        supplement_sha256=hashlib.sha256(supplement.read_bytes()).hexdigest(),ancestry_sha256=hashlib.sha256(ancestry.read_bytes()).hexdigest(),
        train_limits=limits,eval_limits=limits)
    data=DistanceData(1093);validation=data.validation(0)[:1]
    def run(c,name,resume=False):
        path=tmp_path/name
        return search(c,lambda g:data.batch(0,g,c['pressure']),validation,StringIO(),StringIO(),[],path,
            fork=forks,supplement=supplement,ancestry=ancestry,resume=path if resume else None,progress=False)
    full=run(config,'full.json');run({**config,'generations':16},'part.json')
    assert run(config,'part.json',True)==full
    other=run({**config,'pressure':'curriculum','generations':1},'curriculum.json')
    assert other['initial_digests']==full['initial_digests']
    for label in ('task','goal','balanced','junction','choice','transmission'):
        assert other['frozen'][label]['rank']==full['frozen'][label]['rank']
        assert other['frozen'][label]['individual']['genome']==full['frozen'][label]['individual']['genome']
    saved=json.loads((tmp_path/'full.json').read_text())
    assert set(saved['phase_leaders'])=={'15'}
    assert len(saved['protected'])==18 and len(saved['population'])==32
    assert {i['id'] for i in saved['protected']}<={i['id'] for i in saved['population']}
    with pytest.raises(ValueError,match='hash'):run({**config,'ancestry_sha256':'bad'},'bad.json')


def test_v10_fresh_capacity_independent_preflight_seed():
    data=DistanceData(1104,prior_manifests(Path(__file__).resolve().parents[1]))
    for rep in range(3):
        data.validation(rep)
        for generation in range(192):
            fixed=data.batch(rep,generation,'fixed');near=data.batch(rep,generation,'curriculum')
            for a,b in zip(fixed,near):
                assert layout_hash(a.first.maze)==layout_hash(b.first.maze)
                assert a.first.maze.start==b.first.maze.start
                if a.mixed or generation>=32:assert a is b;continue
                x,y=decision(a),decision(b)
                assert all(x[k]==y[k] for k in ('vertex','prefix','incoming','distance','exits'))
                assert [o.to_goal[y['vertex']] for o in b.cases]==list(cue_distances(generation,rep))
                assert all(len(o.path)-1>=3 for o in b.cases)
                assert all(o.to_goal[x['vertex']]>=4 for o in a.cases)
        assert len(data.tests(rep))==88 and len(data.paired_tests(rep))==8
    assert len({layout_hash(o.maze) for o in data.cache.values() if o.maze.split=='test_goal'})==264


def test_short_cues_need_source_dependent_strict_exits_and_far_evaluation_matches():
    data=DistanceData(1103);far=data.batch(0,0,'fixed')[0];near=data.batch(0,0,'curriculum')[0]
    label=decision(near);assert label and old_decision(near) is None
    assert decision(far)==old_decision(far)
    masks=[]
    for want in label['allowed']:
        mask=np.zeros(len(near.first.maze.cells),dtype=np.uint8)
        mask[label['prefix']]=1;mask[want[0]]=1;masks.append(mask)
    off=[np.zeros_like(m) for m in masks]
    assert all(r['strict'] and r['score']==1 for r in junction_metrics(masks,off,near,label))
    assert not any(r['strict'] for r in junction_metrics(masks,masks,near,label))
    item=Individual('test',random_genome(random.Random(1103),True),None,0);limits=Limits(max_steps=16)
    a=old_evaluate(item,[far],'evolved',limits,'choice');b=evaluate(item,[far],'evolved',limits,'fixed')
    assert a==b and a.rows==b.rows
    c=evaluate(item,[near],'evolved',limits,'fixed');d=evaluate(item,[near],'evolved',limits,'curriculum')
    assert c==d and all(r['junction']['eligible'] for r in c.rows)
    with pytest.raises(ValueError):evaluate(item,[far],'local',limits,'bad')
    assert cue_distances(0,0)==(1,2) and cue_distances(16,0)==(2,3) and cue_distances(32,0) is None
    with pytest.raises(ValueError):cue_distances(-1,0)


def test_extension_uses_only_hard_validation_and_needs_replicated_transferring_choices_or_correct_routes():
    base=dict(junction=1.,junction_both=0.,choice_families={'perfect':0.,'random':0.})
    champions={}
    for t in ('local','evolved'):
        for p in ('fixed','curriculum'):
            for rep in range(3):
                a={'choice':dict(base),'task':{'optimal':0}}
                champions[f'distance/{t}/{p}/{rep}']=dict(config=dict(topology=t,pressure=p,replicate=rep),archives=copy.deepcopy(a),frozen=copy.deepcopy(a))
    assert not extension_decision(champions)['extend']
    for rep in (0,1):champions[f'distance/local/curriculum/{rep}']['archives']['choice'].update(junction_both=.5,choice_families={'perfect':.5,'random':.5})
    assert extension_decision(champions)['goal_topologies']==['local']
    champions['distance/local/curriculum/1']['archives']['choice']['choice_families']['random']=0
    assert not extension_decision(champions)['extend']
    for rep in (0,1):champions[f'distance/local/curriculum/{rep}']['archives']['task']['optimal']=1
    assert extension_decision(champions)['route_topologies']==['local']


def test_frozen_snapshot_includes_v10_protocol_and_tests():
    from maze_evolution.distance_study import source_snapshot
    root=Path(__file__).resolve().parents[1];snapshot=source_snapshot(root)
    for name in ('docs/DISTANCE_STUDY_V10.md','tests/test_distance.py','maze_evolution/distance_fitness.py'):
        assert snapshot[name]==hashlib.sha256((root/name).read_bytes()).hexdigest()
    assert not any('maze_evolution/distance_'+name+'.py' in snapshot for name in ('audit','report','diagnostics'))
