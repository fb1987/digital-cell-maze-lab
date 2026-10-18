from dataclasses import asdict
from io import StringIO
from pathlib import Path
import copy,gzip,hashlib,json,random
import numpy as np
import pytest
from maze_evolution.growth import Genome,Individual,mutate,random_genome,replay_mutation
from maze_evolution.regulatory import Genome as OldGenome,Gene,mutate as old_mutate,random_genome as old_random
from maze_evolution.beacon_runtime import Organism as OldOrganism
from maze_evolution.growth_runtime import Organism,observe
from maze_evolution.growth_data import GrowthData,prior_manifests
from maze_evolution.growth_fitness import evaluate
from maze_evolution.choice_fitness import evaluate as old_evaluate
from maze_evolution.growth_search import search
from maze_evolution.growth_study import extension_decision,source_snapshot
from maze_evolution.runtime import Limits
from maze_evolution.goal_data import layout_hash


def test_v3_capacity_roundtrip_mutation_control_rng_and_trace():
    for seed in range(100):
        a=random.Random(seed);b=random.Random(seed);g=random_genome(a);old=old_random(b,True)
        assert g.digest==old.digest and a.getstate()==b.getstate()
        assert isinstance(g,OldGenome) and np.array_equal(g.array(),old.array())
        assert Genome.from_dict(old.to_dict())==g==Genome.from_dict(g.to_dict())
        for _ in range(6):
            x,events=mutate(g,a,6,128,True);y=old_mutate(old,b,6)
            assert x.digest==y.digest and a.getstate()==b.getstate()
            assert replay_mutation(g,events,128)==x
            g,old=x,y
    g=Genome(tuple(Gene(1,12,1) for _ in range(128)));rng=random.Random(1113);above=False
    for _ in range(200):
        child,events=mutate(g,rng,6,256,True);assert replay_mutation(g,events,256)==child
        above|=len(child.genes)>128;g=child
    assert above
    with pytest.raises(ValueError):Genome(tuple(Gene(1,12,1) for _ in range(257)))
    with pytest.raises(ValueError):OldGenome(g.genes)
    with pytest.raises(ValueError):Organism(g,gene_limit=128)
    with pytest.raises(ValueError):mutate(g,rng,7,256)
    for bad in (0,257):
        with pytest.raises(ValueError):mutate(Genome((Gene(1,12),)),rng,1,bad)


def test_lifted_runtime_full_state_and_fitness_equivalence():
    data=GrowthData(1113);pairs=data.validation(0)[:2];g=random_genome(random.Random(1113));old=OldGenome(g.genes)
    for topology in ('local','fixed','evolved'):
        for limits in (Limits(max_steps=16),Limits(max_steps=8,reads_per_site=1,instructions_per_site=1)):
            for pulse,ablate in ((True,False),(False,False),(True,True)):
                a=Organism(g,topology,limits,ablate,pulse);b=OldOrganism(old,topology,limits,ablate,pulse)
                for o in pairs[0].cases:
                    m=o.maze;x=a.react(m.cells,m.w,m.h,m.start,m.goal);y=b.react(m.cells,m.w,m.h,m.start,m.goal)
                    assert vars(x).keys()==vars(y).keys()
                    for k in vars(x):
                        if k=='mask':assert np.array_equal(x.mask,y.mask)
                        else:assert getattr(x,k)==getattr(y,k)
                    for source in (True,False):
                        x=observe(a,m.cells,m.w,m.h,m.start,m.goal,8,source);y=observe(b,m.cells,m.w,m.h,m.start,m.goal,8,source)
                        assert np.array_equal(x.state,y.state)
                        assert {k:v for k,v in vars(x).items() if k!='state'}=={k:v for k,v in vars(y).items() if k!='state'}
    item=Individual('test',g,None,0);limits=Limits(max_steps=32)
    assert evaluate(item,pairs,'evolved',limits,'cap128')==old_evaluate(item,pairs,'evolved',limits,'choice')==evaluate(item,pairs,'evolved',limits,'cap256')


def test_v11_fresh_capacity_independent_preflight_seed():
    data=GrowthData(1114,prior_manifests(Path(__file__).resolve().parents[1]))
    for rep in range(3):
        data.validation(rep)
        for generation in range(192):data.batch(rep,generation)
        assert len(data.tests(rep))==88 and len(data.paired_tests(rep))==8
    assert len({layout_hash(o.maze) for o in data.cache.values() if o.maze.split=='test_goal'})==264


def test_common_native_primitive_cohort_and_exact_growth_resume(tmp_path):
    rng=random.Random(1113);forks=[];records={};extra=[]
    for mode in ('fixed','curriculum'):
        parents=[Individual(f'{mode}/p{i}',OldGenome((Gene(1,12,i+(mode=='curriculum')*100),)),None,48).save() for i in range(32)]
        saved=dict(config=dict(search_version=10,origin='random',pressure=mode,topology='evolved',replicate=2),population=parents,
            archives={k:{'individual':parents[i]} for i,k in enumerate(('task','choice','junction','balanced','goal','transmission'))},protected=[parents[6]],rng_state=rng.getstate())
        path=tmp_path/(mode+'.json');path.write_text(json.dumps(saved));forks.append(path)
        records[f'distance/evolved/{mode}/2']={'individual':parents[7]}
        if mode=='curriculum':extra=[dict(condition='distance/evolved/curriculum/2',nodes=[dict(individual=p) for p in parents[8:12]])]
    supplement=tmp_path/'supplement.json';supplement.write_text(json.dumps(dict(records=records)))
    ancestry=tmp_path/'training.json';ancestry.write_text(json.dumps(dict(records=extra)))
    limits=asdict(Limits(max_steps=16));config=dict(study='growth',search_version=11,origin='random',seed=1113,
        topology='evolved',pressure='cap256',gene_limit=256,replicate=2,population=32,generations=17,horizon=8,
        fork_sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in forks],
        supplement_sha256=hashlib.sha256(supplement.read_bytes()).hexdigest(),ancestry_sha256=hashlib.sha256(ancestry.read_bytes()).hexdigest(),train_limits=limits,eval_limits=limits)
    data=GrowthData(1113);validation=data.validation(2)[:1]
    def run(c,name,resume=False):
        path=tmp_path/name
        return search(c,lambda g:data.batch(2,g),validation,StringIO(),StringIO(),[],path,
            fork=forks,supplement=supplement,ancestry=ancestry,resume=path if resume else None,progress=False)
    full=run(config,'full.json');run({**config,'generations':16},'part.json')
    assert run(config,'part.json',True)==full
    other=run({**config,'pressure':'cap128','gene_limit':128,'generations':1},'control.json')
    assert other['initial_digests']==full['initial_digests']
    for label in full['frozen']:
        assert other['frozen'][label]['rank']==full['frozen'][label]['rank']
        assert other['frozen'][label]['individual']['genome']==full['frozen'][label]['individual']['genome']
    saved=json.loads((tmp_path/'full.json').read_text())
    assert len(saved['protected'])==20 and set(saved['phase_leaders'])=={'15'}
    assert {i['id'] for i in saved['protected']}<={i['id'] for i in saved['population']}
    with pytest.raises(ValueError):run({**config,'gene_limit':128},'mismatch.json')


def test_capacity_extension_gate_and_snapshot():
    base=dict(junction=1.,junction_both=0.,choice_families={'perfect':0.,'random':0.});champions={}
    for t in ('local','evolved'):
        for p in ('cap128','cap256'):
            for rep in range(3):
                a={'choice':dict(base),'task':{'optimal':0}}
                champions[f'growth/{t}/{p}/{rep}']=dict(config=dict(topology=t,pressure=p,replicate=rep),archives=copy.deepcopy(a),frozen=copy.deepcopy(a))
    assert not extension_decision(champions)['extend']
    for rep in (0,1):champions[f'growth/local/cap256/{rep}']['archives']['choice'].update(junction_both=.5,choice_families={'perfect':.5,'random':.5})
    assert extension_decision(champions)['goal_topologies']==['local']
    champions['growth/local/cap256/1']['archives']['choice']['choice_families']['random']=0
    assert not extension_decision(champions)['extend']
    for rep in (0,1):champions[f'growth/local/cap256/{rep}']['archives']['task']['optimal']=1
    assert extension_decision(champions)['route_topologies']==['local']
    snapshot=source_snapshot(Path(__file__).resolve().parents[1])
    assert 'docs/GROWTH_STUDY_V11.md' in snapshot and 'tests/test_growth.py' in snapshot
