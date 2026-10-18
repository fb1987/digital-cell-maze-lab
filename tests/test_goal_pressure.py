from dataclasses import asdict
from io import StringIO
import hashlib,json,random
import numpy as np
import pytest
from maze_evolution.evaluator import Maze,Oracle,distances
from maze_evolution.goal_data import GoalData,GoalPair,layout_hash
from maze_evolution.goal_fitness import goal_metrics,evaluate
from maze_evolution.regulatory import Genome,Gene,random_genome
from maze_evolution.regulatory_search import Individual
from maze_evolution.runtime import Limits


def cross_pair():
    cells=bytes([1]*17)
    return GoalPair(Oracle.build(Maze(cells,17,1,8,0)),Oracle.build(Maze(cells,17,1,8,16)))


def test_goal_shaping_rewards_causal_correct_paths_but_not_source_only_or_markers():
    pair=cross_pair();a=np.array([1]*9+[0]*8,dtype=np.uint8);b=a[::-1].copy();zero=np.zeros(17,dtype=np.uint8)
    good=goal_metrics([a,b],[zero,zero],pair)
    assert all(r['score']==1 and r['pair_both'] for r in good)
    fixed=goal_metrics([a,a],[zero,zero],pair)
    assert all(r['score']==0 for r in fixed)
    goal_only=goal_metrics([a,b],[a,b],pair)
    assert all(r['score']==0 for r in goal_only)
    dots=[]
    for goal in (0,16):
        mask=zero.copy();mask[8]=mask[goal]=1;dots.append(mask)
    assert all(r['score']==0 for r in goal_metrics(dots,[zero,zero],pair))
    floods=[np.ones(17,dtype=np.uint8)]*2
    assert all(r['score']==0 for r in goal_metrics(floods,[zero,zero],pair))


def test_detached_goal_changes_cannot_fake_specificity():
    pair=cross_pair();a=np.zeros(17,dtype=np.uint8);a[5:9]=1
    b=a.copy();a[0]=1;b[16]=1
    assert all(r['specificity']==r['score']==0 for r in goal_metrics([a,b],[a*0,b*0],pair))


def test_goal_pair_geometry_distance_and_whole_layout_split_exclusion():
    d=GoalData(1048)
    for rep in range(3):
        for pair in d.validation(rep):
            a,b=pair.cases
            assert a.maze.cells==b.maze.cells and a.maze.start==b.maze.start
            assert len(a.path)-1>=8
            if pair.mixed:assert not b.path
            else:
                assert len(b.path)-1>=8
                assert a.to_goal[b.maze.goal]>=max(len(a.path)-1,len(b.path)-1)
    train=d.batch(0,0);val=d.validation(0)
    assert {layout_hash(p.first.maze) for p in train}.isdisjoint(layout_hash(p.first.maze) for p in val)
    tests=d.tests(0,1);paired=d.paired_tests(0)
    assert len(tests)==32
    assert len({layout_hash(o.maze) for o in d.cache.values() if o.maze.split=='test_goal'})==32
    assert all(not(set((p.first.maze.digest,p.second.maze.digest)) & set(o.maze.digest for o in tests)) for p in paired)


def test_new_objective_preserves_earlier_priorities_and_charges_same_probes():
    item=Individual('unit',random_genome(random.Random(1049),True),None,0)
    pairs=GoalData(1049).batch(0,0);limits=Limits(max_steps=32)
    a=evaluate(item,pairs,'local',limits,'transmission')
    b=evaluate(item,pairs,'local',limits,'goal')
    assert a.fitness[:3]==b.fitness[:3] and a.work==b.work
    assert a.work==a.inference_work+a.probe_work
    assert abs((b.fitness[3]-a.fitness[3])-2*sum(r['goal']['score'] for r in b.rows))<1e-7


def test_goal_fork_protects_signal_archive_and_resumes_exactly(tmp_path):
    from maze_evolution.goal_search import search
    rng=random.Random(1050)
    parents=[Individual(f'parent/{i}',random_genome(rng,True),None,160).save() for i in range(4)]
    learned=Individual('learned',Genome((Gene(13,0,9),)),None,130).save()
    ancestor=dict(config=dict(search_version=3,origin='random',pressure='causal',topology='local'),
                  population=parents,transmission=learned,rng_state=rng.getstate())
    fork=tmp_path/'fork.json';fork.write_text(json.dumps(ancestor))
    config=dict(study='goal',topology='local',pressure='goal',replicate=0,population=4,generations=4,horizon=8,
        fork_sha256=hashlib.sha256(fork.read_bytes()).hexdigest(),train_limits=asdict(Limits(max_steps=16)),eval_limits=asdict(Limits(max_steps=16)))
    d=GoalData(1050);val=d.validation(0)[:1]
    def run(c,path,resume=None,deadline=None):
        return search(c,lambda g:d.batch(0,g),val,StringIO(),StringIO(),[],path,
                      fork=fork,resume=resume,deadline=deadline,progress=False)
    full=run(config,tmp_path/'full.json')
    run({**config,'generations':2},tmp_path/'part.json')
    resumed=run(config,tmp_path/'part.json',tmp_path/'part.json')
    assert full==resumed
    assert full['fork_injection']['injected'] and full['initial_digests'][-1]==Genome.from_dict(learned['genome']).digest
    saved=json.loads((tmp_path/'full.json').read_text())
    assert saved['protected']['id'] in {i['id'] for i in saved['population']}
    stopped=run(config,tmp_path/'wall.json',deadline=0)
    assert stopped['next_generation']==1
    assert run(config,tmp_path/'wall.json',tmp_path/'wall.json')==full
    other=run({**config,'pressure':'transmission'},tmp_path/'control.json')
    assert other['initial_digests']==full['initial_digests']
    with pytest.raises(ValueError,match='hash'):
        run({**config,'fork_sha256':'bad'},tmp_path/'bad.json')


def test_extension_requires_replicated_goal_output_or_correct_long_routes():
    import copy
    from maze_evolution.goal_study import extension_decision
    record=dict(goal=0.,signal=.5,quality=0.,specificity=0.,both=0.,optimal=0,
                goal_families={'perfect':0.,'random':0.})
    champions={f'goal/{t}/{p}/{r}':dict(archives={k:copy.deepcopy(record) for k in ('task','goal','transmission')},
                frozen={k:copy.deepcopy(record) for k in ('task','goal','transmission')})
                for t in ('local','evolved') for p in ('goal','transmission') for r in range(3)}
    assert not extension_decision(champions)['extend']
    for r in range(2):
        champions[f'goal/evolved/goal/{r}']['archives']['goal'].update(goal=.06,quality=.11,
            specificity=.06,both=.25,goal_families={'perfect':.06,'random':.06})
        assert extension_decision(champions)['extend']==(r==1)
    champions['goal/evolved/goal/1']['archives']['goal']['signal']=.1
    assert not extension_decision(champions)['extend']
    champions['goal/local/goal/0']['archives']['task']['optimal']=2
    assert extension_decision(champions)['route_topologies']==['local']
