import random
from copy import deepcopy
import numpy as np
from maze_evolution.connected_genome import Genome,embed,clone,edges,zero_copy
from maze_evolution.connected_runtime import Organism
from maze_evolution.connected_trace import respond
from maze_evolution.modular_genome import Genome as Base,random_genome
from maze_evolution.modular_runtime import Organism as Original
from maze_evolution.modular_controls import intact_control
from maze_evolution.restoration_trace import respond as old_respond
from maze_evolution.datasets import make_case,Maze
from maze_evolution.exposure_selection import record
from maze_evolution.runtime import Limits
from maze_evolution.regulatory import Gene
from maze_evolution.connected_copy_assay import make_pool


def test_embedding_native_and_trace_fields_and_memory():
    rng=random.Random(181)
    for g in [intact_control(),*[random_genome(rng) for _ in range(3)]]:
        for family in ('perfect','random','disconnected'):
            o=make_case(818,'m18-test',0,0,9,family);m=o.maze
            a=Original(g).react(m.cells,m.w,m.h,m.start,m.goal);e=embed(g)
            b=Organism(e).react(m.cells,m.w,m.h,m.start,m.goal);c,h,_=respond(dict(genome=e.to_dict()),m)
            x=record(a,o);y=record(b,o);assert y==record(c,o)
            assert {k:v for k,v in x.items() if k!='array_bytes'}=={k:v for k,v in y.items() if k!='array_bytes'}
            assert b.array_bytes-a.array_bytes==8*len(m.cells)+162
            assert np.array_equal(h[-1,2]>0,b.mask>0)


def test_all_initialized_connected_edges_preserve_common_legacy_states():
    rng=random.Random(182)
    for g in [intact_control(),random_genome(rng),random_genome(rng)]:
        o=make_case(818,'m18-test',0,0,9,'random');m=o.maze
        _,old,_=old_respond(dict(genome=g.to_dict()),m)
        for reader,donor in edges(g):
            for target in (8,9):
                e,event=clone(embed(g),reader,donor,target,True,True)
                assert e.initialization[target]==e.initialization[donor]
                r,h,_=respond(dict(genome=e.to_dict()),m);native=Organism(e).react(m.cells,m.w,m.h,m.start,m.goal)
                assert record(r,o)==record(native,o)
                n=min(len(h),len(old));assert np.array_equal(h[:n,:8],old[:n])
                assert np.array_equal(h[:,target],h[:,donor]);assert r.steps<=len(old)-1


def test_connected_seeded_copy_can_affect_existing_reader_without_editing_donor():
    blocks=tuple((Gene(0,12,k,0,0,0,64),) for k in range(8));blocks=list(blocks);blocks[2]=(Gene(0,12,0,0,0,0,64),)
    base=Base(tuple(blocks),(tuple(range(8)),)*8);a,_=clone(embed(base),2,0,8,True,True)
    assert a.body.blocks[:8]==base.blocks and a.body.ports[2][0]==8 and a.initialization[8]==1
    m=Maze(bytes([1,1,1]),3,1,0,2);_,h,_=respond(dict(genome=a.to_dict()),m)
    z=zero_copy(a,8);_,zh,_=respond(dict(genome=z.to_dict()),m)
    assert np.array_equal(h[:,0],zh[:len(h),0]) if len(h)<=len(zh) else np.array_equal(h[:len(zh),0],zh[:,0])
    assert np.any(h[2,:8]!=zh[2,:8])


def test_extra_work_can_break_bounded_neutrality_and_is_not_hidden():
    blocks=tuple((Gene(0,12,k,0,0,0,64),) for k in range(8));blocks=list(blocks);blocks[2]=(Gene(0,12,0,0,0,0,64),)
    base=Base(tuple(blocks),(tuple(range(8)),)*8);g,_=clone(embed(base),2,0,8,True,True)
    cells=bytes([1,1,1]);lim=Limits(1,4096,16)
    a=Original(base,lim).react(cells,3,1,0,2);b=Organism(g,lim).react(cells,3,1,0,2)
    assert a.steps==1 and b.steps==0 and a.status=='step_budget' and b.status=='instruction_budget'
    assert not np.array_equal(a.mask,b.mask)


def test_deterministic_factorial_pool_and_intervention_provenance():
    rng=random.Random(183);sources=dict(anchors={k:dict(genome=random_genome(rng).to_dict()) for k in ('parent','child')})
    saved=deepcopy(sources);a=make_pool(sources);assert a==make_pool(sources) and sources==saved
    for i in a['items']:
        g=Base.from_dict(sources['anchors'][i['anchor']]['genome']);e,event=clone(embed(g),i['reader'],i['donor'],i['target'],i['seeded'],i['connected'])
        if i['kind']=='intervention':e=zero_copy(e,i['target'])
        assert e.to_dict()==i['model']['genome'] and Genome.from_dict(e.to_dict())==e
    for anchor,v in sources['anchors'].items():
        n=len(edges(Base.from_dict(v['genome'])))
        assert sum(i['anchor']==anchor for i in a['items'])==n*2*4*2
