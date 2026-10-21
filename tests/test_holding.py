import random
import numpy as np
import pytest
from maze_evolution.modular_genome import Genome as Base,random_genome
from maze_evolution.holding_genome import Genome
from maze_evolution.holding_runtime import Organism
from maze_evolution.modular_runtime import Organism as Old
from maze_evolution.regulatory import Gene
from maze_evolution.runtime import Limits

def test_validation_and_roundtrip():
    base=random_genome(random.Random(511));g=Genome(base)
    assert Genome.from_dict(g.to_dict())==g
    for gates,holds in [((99,)*8,(0,)*8),((64,)*7,(0,)*8),((64,)*8,(2,)*8)]:
        with pytest.raises(ValueError):Genome(base,gates,holds)

def test_embedding_matches_old_behavior_and_work_at_budget_boundaries():
    rng=random.Random(512);cells=bytes([0,0,0,0,1,1,0,1,1])
    for _ in range(12):
        g=random_genome(rng)
        for limits in (Limits(256,4096,32768),Limits(1,1,1),Limits(4,2,64)):
            a=Old(g,limits).react(cells,3,3,4,8);b=Organism(Genome(g),limits).react(cells,3,3,4,8)
            for k,v in vars(a).items():
                if k=='mask':assert np.array_equal(v,b.mask)
                elif k=='array_bytes':assert b.array_bytes==v+64
                else:assert getattr(b,k)==v

def test_false_writer_holds_old_state_instead_of_implicit_zero():
    blocks=[(Gene(1,12,0,0,0,0,64),) for _ in range(8)]
    blocks[2]=(Gene(0,12,0,0,0,0,64),)
    base=Base(tuple(blocks),(tuple(range(8)),)*8);gates=(12,)+(64,)*7
    held=Organism(Genome(base,gates,(1,)+(0,)*7)).react(bytes([1,1]),2,1,0,1)
    erased=Organism(Genome(base,gates,(0,)*8)).react(bytes([1,1]),2,1,0,1)
    assert held.mask.tolist()==[1,0] and erased.mask.tolist()==[0,0]
    assert held.status=='quiescent' and erased.status=='no_path'

def test_true_writer_ignores_fallback_and_preserves_work():
    base=random_genome(random.Random(513));cells=bytes([1]*9)
    a=Organism(Genome(base,(8,)*8,(0,)*8)).react(cells,3,3,0,8)
    b=Organism(Genome(base,(8,)*8,(1,)*8)).react(cells,3,3,0,8)
    assert np.array_equal(a.mask,b.mask)
    assert all(getattr(a,k)==getattr(b,k) for k in vars(a) if k!='mask')

def test_paired_pool_is_reproducible_and_changes_only_false_condition_fallback():
    from maze_evolution.holding_assay import pool
    aa=[dict(base=random_genome(random.Random(514+k)).to_dict()) for k in range(2)]
    p=pool(515,16,aa);assert p==pool(515,16,aa)
    items={i['id']:i for i in p['items']}
    for k in range(2):
        for n in range(16):
            h=items[f'a{k}/hold/{n:04}'];z=items[f'a{k}/zero/{n:04}'];s=items[f'a{k}/standard/{n:04}']
            assert h['depth']==z['depth']==s['depth']==1+n%2
            assert h['model']['genome']['base']==z['model']['genome']['base']
            assert h['model']['genome']['write_gates']==z['model']['genome']['write_gates']
            assert sum(h['model']['genome']['write_holds'])==1
            assert sum(z['model']['genome']['write_holds'])==0
            assert all(g==64 for g in s['model']['genome']['write_gates'])
