import random
import pytest
from maze_evolution.regulatory import Gene
from maze_evolution.modular_genome import Genome,random_genome,mutate
from maze_evolution.modular_runtime import Organism
from maze_evolution.modular_controls import to_flat,intact_control
from maze_evolution.exposure_genome import Genome as FlatGenome
from maze_evolution.exposure_runtime import Organism as FlatOrganism
from maze_evolution.runtime import Limits
from maze_evolution.deep_campaign_data import cases_from_manifest
from maze_evolution.foundation_study import read_compressed
from maze_evolution.foundation_calibration import ROOT
from maze_evolution.exposure_selection import record
from maze_evolution.foundation_study_verify_core import Checker


def fixture():
    x=read_compressed(ROOT/'results/deep_confirmation/fixture.json.gz')
    return cases_from_manifest([r for r in x['mazes'] if r['case_id'] in x['queries']])


def test_no_forward_refs_or_implicit_cross_block_scratch():
    b=tuple((Gene(0,12,k),) for k in range(8));ports=tuple(tuple(range(8)) for _ in range(8))
    Genome(b,ports)
    bad=list(b);bad[0]=(Gene(0,12,12),)
    with pytest.raises(ValueError):Genome(tuple(bad),ports)
    bad=list(b);bad[0]=(Gene(13,0,0),)
    with pytest.raises(ValueError):Genome(tuple(bad),ports)


def test_mutation_bounds_serialization_and_rng_replay():
    rng=random.Random(202610201010);g=random_genome(rng);kinds=set()
    for _ in range(2000):
        state=rng.getstate();child,event=mutate(g,rng);other=random.Random();other.setstate(state)
        assert mutate(g,other)==(child,event) and other.getstate()==rng.getstate()
        assert Genome.from_dict(child.to_dict())==child and child.instructions<=256
        kinds.add(event['kind']);g=child
    assert {'replace','insert','delete','ports','copy_block','duplicate_node','operand'}<=kinds


def test_random_m1_matches_separate_old_kernel_after_translation():
    rng=random.Random(202610201011);cases=list(fixture().values())[::9]
    limits=Limits(24,65536,131072)
    for _ in range(12):
        g=random_genome(rng)
        # Exercise nonidentity channel ports as well as gated private nodes.
        for _ in range(8):g,_=mutate(g,rng)
        a=Organism(g,limits);b=FlatOrganism(FlatGenome(to_flat(g),7),'local','local',limits,True)
        for o in cases:
            m=o.maze;args=(m.cells,m.w,m.h,m.start,m.goal);x=a.react(*args);y=b.react(*args)
            assert (x.status,x.steps,x.mask.tolist())==(y.status,y.steps,y.mask.tolist())
            assert x.spatial_reads==y.spatial_reads


def test_separate_known_solver_control_can_solve_all_fixture_queries():
    cases=fixture();checker=Checker(cases);g=intact_control();org=Organism(g)
    assert g.instructions<=256
    for o in cases.values():
        m=o.maze;r=record(org.react(m.cells,m.w,m.h,m.start,m.goal),o);checker.row(r)
        assert r['optimal'] or r['no_path']
