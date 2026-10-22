import random
from copy import deepcopy
import numpy as np
from maze_evolution.spare_genome import Genome,embed,duplicate,mutate
from maze_evolution.spare_runtime import Organism
from maze_evolution.modular_genome import Genome as Base,random_genome,mutate as old_mutate
from maze_evolution.modular_runtime import Organism as OldOrganism
from maze_evolution.modular_controls import intact_control
from maze_evolution.datasets import make_case
from maze_evolution.exposure_selection import record
from maze_evolution.runtime import Limits
from maze_evolution.regulatory import Gene
from maze_evolution.spare_state_assay import make_pool,tasks
from maze_evolution.spare_metrics import feature


def test_neutral_embedding_preserves_native_behavior_and_charges_extra_memory():
    rng=random.Random(177)
    for g in [intact_control(),*[random_genome(rng) for _ in range(6)]]:
        e=embed(g);assert Genome.from_dict(e.to_dict())==e and e.instructions==g.instructions
        for family in ('perfect','random','disconnected'):
            o=make_case(817,'m17-test',0,0,9,family);m=o.maze
            for limits in (Limits(256,4096,32768),Limits(3,1,10)):
                a=OldOrganism(g,limits).react(m.cells,m.w,m.h,m.start,m.goal)
                b=Organism(e,limits).react(m.cells,m.w,m.h,m.start,m.goal)
                x=record(a,o);y=record(b,o)
                assert {k:v for k,v in x.items() if k!='array_bytes'}=={k:v for k,v in y.items() if k!='array_bytes'}
                assert b.array_bytes-a.array_bytes==8*len(m.cells)+152


def test_generic_copy_preserves_original_writers_and_rebinds_only_copy():
    base=random_genome(random.Random(1));g=embed(base)
    child,event=duplicate(g,4,8)
    assert child.blocks[:8]==g.blocks[:8] and child.ports[:8]==g.ports[:8]
    assert child.blocks[8]==g.blocks[4] and child.ports[8][4]==8 and child.ports[8][8]==4
    assert child.instructions==g.instructions+len(g.blocks[4])+1
    assert event['before']==g.digest and event['after']==child.digest
    overwrite,_=duplicate(base,4,3);assert overwrite.blocks[3]==base.blocks[4]


def test_spare_is_real_persistent_state_accessible_through_generic_ports():
    # All eight old outputs zero, generic constant writer copied from C4 to C8.
    blocks=tuple((Gene(1,12,int(k==4),0,0,0,64),) for k in range(8))
    g=embed(Base(blocks,(tuple(range(8)),)*8));g,_=duplicate(g,4,8)
    blocks=list(g.blocks);blocks[2]=(Gene(0,12,0,0,0,0,64),)
    ports=list(g.ports);ports[2]=(8,1,2,3,4,5,6,7,0,9)
    g=Genome(tuple(blocks),tuple(ports))
    r=Organism(g,Limits(2,4096,32768)).react(bytes([1,1,1]),3,1,0,2)
    assert r.mask.tolist()==[1,1,1] and r.steps==2
    assert r.dispatches==2*3*18 # nine primitive nodes + nine output writes per site/tick


def test_mutation_pool_paired_budgets_sources_and_full_events_rng_replay():
    rng=random.Random(231);sources={'anchors':{k:{'genome':random_genome(rng).to_dict()} for k in ('parent','child')}}
    original=deepcopy(sources);a=make_pool(sources,42,8,4)
    assert a==make_pool(sources,42,8,4) and sources==original
    for i in a['items']:
        cls=Genome if i['model']['representation']=='spare' else Base
        assert cls.from_dict(i['model']['genome']).instructions<=256
        if i['kind']!='mutation':continue
        base=Base.from_dict(sources['anchors'][i['anchor']]['genome']);g=embed(base) if i['arm']=='spare' else base
        first=random.Random(i['first_seed']);later=random.Random(i['later_seed'])
        if i['arm']=='unchanged':g,e=old_mutate(g,first)
        else:g,e=duplicate(g,i['donor'],i['spare_target'] if i['arm']=='spare' else i['overwrite_target'])
        events=[e]
        for _ in range(i['depth']-1):g,e=(mutate if i['arm']=='spare' else old_mutate)(g,later);events.append(e)
        assert events==i['events'] and g.to_dict()==i['model']['genome']
        from maze_evolution.routing_transfer import canonical
        assert canonical(later.getstate())==i['later_rng_final'] and canonical(first.getstate())==i['first_rng_final']
    for arm in ('unchanged','overwrite','spare'):
        assert sum(i['depth'] for i in a['items'] if i.get('arm')==arm and i['kind']=='mutation')==64


def test_random_mutations_obey_channel_register_and_instruction_bounds():
    rng=random.Random(19);g=embed(random_genome(rng));seen=set()
    for _ in range(2000):
        g,e=mutate(g,rng);seen.add(e['kind']);assert Genome.from_dict(g.to_dict())==g
    assert {'copy_block','activate_node','ports','insert','delete','duplicate_node','operand','replace'}<=seen


def test_exact_joint_gate_and_deduplication():
    def cap(p,d):return dict(pairs=set(p),corridors={1},ordinary_bases={1},correct_no_path=set(d),false=set(),summary={'work':1})
    parent=cap(range(4),['d']);child=cap(range(12),[]);combined=cap(range(12),['d'])
    targets=set(range(4,12));pm={i:{'template':str(i%2)} for i in range(12)}
    assert feature(combined,parent,child,targets,pm)['joint_restoration_pass']
    for field in ('pairs','corridors','ordinary_bases','correct_no_path'):
        bad=deepcopy(combined);bad[field].pop();assert not feature(bad,parent,child,targets,pm)['joint_restoration_pass']
    assert not feature(combined,parent,child,set(),pm)['reference_eligible']
    bad=deepcopy(combined);bad['false']={1};assert not feature(bad,parent,child,targets,pm)['joint_restoration_pass']
    m=dict(representation='modular',genome=random_genome(random.Random(1)).to_dict())
    t=tasks([dict(id='a',model=m),dict(id='b',model=m)],['x'])
    assert len(t)==len(t[0])==1 and t[0][0]['aliases']==['a','b']
