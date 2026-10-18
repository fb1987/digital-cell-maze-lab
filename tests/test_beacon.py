from dataclasses import asdict
from io import StringIO
from pathlib import Path
import ast,hashlib,json,random
import numpy as np
import pytest
from maze_evolution.beacon_runtime import Organism
from maze_evolution.beacon_probe import observe
from maze_evolution.beacon_fitness import evaluate
from maze_evolution.beacon_data import BeaconData,prior_manifests
from maze_evolution.beacon_search import search,learned_parents
from maze_evolution.regulatory_runtime import Organism as OldOrganism
from maze_evolution.signal_probe import observe as old_observe
from maze_evolution.factor_fitness import evaluate as old_evaluate
from maze_evolution.regulatory import Gene,Genome,random_genome,seeded_genome
from maze_evolution.regulatory_search import Individual
from maze_evolution.runtime import Limits
from maze_evolution.goal_data import layout_hash


def test_flag_runtime_exact_v2_parity_including_caps_and_topologies():
    rng=random.Random(1060)
    genomes=[seeded_genome()]+[random_genome(rng,True) for _ in range(8)]
    cells=bytes([1,1,1,1,0,1,1,1,1])
    for genome in genomes:
        for topology in ('local','fixed','evolved'):
            for limits in (Limits(max_steps=32),Limits(max_steps=16,reads_per_site=2,instructions_per_site=64)):
                a=OldOrganism(genome,topology,limits).react(cells,3,3,0,8)
                b=Organism(genome,topology,limits).react(cells,3,3,0,8)
                assert a.__dict__.keys()==b.__dict__.keys()
                for k,v in a.__dict__.items():
                    assert np.array_equal(v,b.__dict__[k]),k


def test_goal_pulse_changes_only_initial_channel_and_survives_source_removal():
    genome=Genome((Gene(13,2,1),))
    cells=bytes([1]*5)
    for pulse in (False,True):
        organism=Organism(genome,goal_pulse=pulse)
        a=observe(organism,cells,5,1,0,4,1,True)
        b=observe(organism,cells,5,1,0,4,1,False)
        assert a.state[0,0]==1 and b.state[0,0]==0
        assert a.state[1,4]==b.state[1,4]==int(pulse)
        assert a.state[2,4]==b.state[2,4]==int(pulse)
        assert a.state[2].sum()==int(pulse)
        assert not a.state.flags.writeable
    with pytest.raises(ValueError):Organism(genome,goal_pulse='pulse')


def test_flag_observer_parity_and_both_modes_match_normal_stopping():
    rng=random.Random(1061);cells=bytes([1]*9)
    for genome in [seeded_genome()]+[random_genome(rng,True) for _ in range(5)]:
        for topology in ('local','evolved'):
            for source in (False,True):
                old=old_observe(OldOrganism(genome,topology),cells,3,3,0,8,16,source)
                new=observe(Organism(genome,topology),cells,3,3,0,8,16,source)
                for k,v in old.__dict__.items():assert np.array_equal(v,new.__dict__[k])
            for pulse in (False,True):
                organism=Organism(genome,topology,Limits(max_steps=16),goal_pulse=pulse)
                r=organism.react(cells,3,3,0,8)
                o=observe(organism,cells,3,3,0,8,16,force_horizon=False)
                assert np.array_equal(r.mask,o.state[2]>0)
                assert (r.status,r.steps,r.spatial_reads,r.dispatches,r.active_instructions,r.range_reads)==(o.status,o.steps,o.reads,o.dispatches,o.active,o.range_reads)
    with pytest.raises(ValueError):observe(organism,cells,3,3,0,8,65)


def test_flag_fitness_is_unchanged_product_reward_and_pulse_work_is_charged():
    data=BeaconData(1062);pairs=data.batch(0,0);limits=Limits(max_steps=32)
    item=Individual('unit',random_genome(random.Random(1062),True),None,0)
    old=old_evaluate(item,pairs,'evolved',limits,'product')
    flag=evaluate(item,pairs,'evolved',limits,'flag')
    assert old.__dict__==flag.__dict__
    pulse=evaluate(item,pairs,'evolved',limits,'pulse')
    assert pulse.work==pulse.inference_work+pulse.probe_work
    assert pulse.alpha==flag.alpha==1.
    assert all(r['factor_bonus']==2*r['goal']['score'] for r in pulse.rows)
    with pytest.raises(ValueError):evaluate(item,pairs,'local',limits,'bad')


def test_v6_data_all_splits_exclude_every_prior_layout():
    data=BeaconData(2026101804,prior_manifests(Path(__file__).resolve().parents[1]))
    for rep in range(3):
        data.validation(rep)
        for generation in range(192):data.batch(rep,generation)
        assert len(data.tests(rep,8))==88 and len(data.paired_tests(rep))==8
    assert len({layout_hash(o.maze) for o in data.cache.values() if o.maze.split=='test_goal'})==264


def test_both_archive_sets_protected_with_identical_inputs_and_exact_resume(tmp_path):
    rng=random.Random(1063);forks=[]
    for pressure in ('product','curriculum'):
        parents=[Individual(f'{pressure}/p{i}',Genome((Gene(1,12,i+(pressure=='curriculum')*100),)),None,48).save() for i in range(12)]
        archive={k:{'individual':parents[i]} for i,k in enumerate(('task','goal','transmission'))}
        saved=dict(config=dict(search_version=5,origin='random',pressure=pressure,topology='local',replicate=0),
            population=parents,archives=archive,protected=[parents[3]],rng_state=rng.getstate())
        path=tmp_path/(pressure+'.json');path.write_text(json.dumps(saved));forks.append(path)
    limits=asdict(Limits(max_steps=16));config=dict(study='beacon',search_version=6,origin='random',seed=1063,
        topology='local',pressure='flag',replicate=0,population=12,generations=3,horizon=8,
        fork_sha256=[hashlib.sha256(p.read_bytes()).hexdigest() for p in forks],train_limits=limits,eval_limits=limits)
    data=BeaconData(1063);validation=data.validation(0)[:1]
    def run(c,name,resume=False):
        path=tmp_path/name
        return search(c,lambda g:data.batch(0,g),validation,StringIO(),StringIO(),[],path,
            fork=forks,resume=path if resume else None,progress=False)
    full=run(config,'full.json');run({**config,'generations':1},'part.json')
    assert run(config,'part.json',True)==full
    pulse=run({**config,'pressure':'pulse','generations':1},'pulse.json')
    assert pulse['initial_digests']==full['initial_digests']
    checkpoint=json.loads((tmp_path/'full.json').read_text())
    assert len(checkpoint['protected'])==8 and len(checkpoint['population'])==12
    assert {i['id'] for i in checkpoint['protected']}<={i['id'] for i in checkpoint['population']}
    assert len(full['fork_injection'])==4
    with pytest.raises(ValueError,match='hash'):run({**config,'fork_sha256':['bad']*2},'bad.json')


def test_candidate_execution_has_no_oracle_or_search_dependencies():
    root=Path(__file__).resolve().parents[1]/'maze_evolution'
    allowed={'dataclasses','numpy','numba','regulatory','runtime','beacon_runtime'}
    for name in ('beacon_runtime.py','beacon_probe.py'):
        tree=ast.parse((root/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):assert node.module in allowed
            elif isinstance(node,ast.Import):assert all(a.name in allowed for a in node.names)
