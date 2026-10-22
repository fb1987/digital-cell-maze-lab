import random
from copy import deepcopy
import numpy as np
from maze_evolution.restoration_metrics import feature
from maze_evolution.restoration_assay import make_pool,tasks,trace_ids
from maze_evolution.modular_genome import random_genome,Genome,mutate
from maze_evolution.modular_runtime import Organism
from maze_evolution.restoration_trace import respond
from maze_evolution.datasets import make_case
from maze_evolution.exposure_selection import record


def cap(pairs,ordinary,disc):
    return dict(pairs=set(pairs),corridors={1,2},ordinary_bases=set(ordinary),correct_no_path=set(disc),false=set(),summary={'work':1})


def test_gate_demands_route_and_no_path_and_ordinary_nonvacuously():
    parent=cap(range(4),['a','b'],['d']);child=cap(range(12),['a'],[])
    targets=set(range(4,12));pm={i:{'template':str(i%2)} for i in range(12)}
    combined=cap(range(12),['a','b'],['d'])
    assert feature(combined,parent,child,targets,pm)['joint_restoration_pass']
    for key in ('pairs','corridors','ordinary_bases','correct_no_path'):
        x=deepcopy(combined);x[key].pop();assert not feature(x,parent,child,targets,pm)['joint_restoration_pass']
    x=deepcopy(combined);x['false']={42};assert not feature(x,parent,child,targets,pm)['joint_restoration_pass']
    assert not feature(combined,parent,child,set(),pm)['reference_eligible']
    p=deepcopy(parent);p['correct_no_path']=set();assert not feature(combined,p,child,targets,pm)['reference_eligible']


def test_pool_is_fixed_and_mutation_events_replay():
    rng=random.Random(231);sources={'anchors':{k:{'genome':random_genome(rng).to_dict()} for k in ('parent','child')}}
    original=deepcopy(sources);a=make_pool(sources,42,8,4);assert a==make_pool(sources,42,8,4) and sources==original
    rng=random.Random(42)
    for anchor in ('parent','child'):
        entries=[x for x in a['items'] if x.get('anchor')==anchor and x['kind']=='mutation']
        assert [x['depth'] for x in entries]==[1,2]*4
        for entry in entries:
            g=Genome.from_dict(sources['anchors'][anchor]['genome']);events=[]
            for _ in range(entry['depth']):g,event=mutate(g,rng);events.append(event)
            assert g.to_dict()==entry['model']['genome'] and events==entry['events']
    assert sum(x['kind']=='diagnostic' for x in a['items'])==72
    for x in a['items']:assert Genome.from_dict(x['model']['genome']).instructions<=256


def test_dedup_preserves_every_alias_and_same_queries():
    g=random_genome(random.Random(1)).to_dict();model=dict(representation='modular',genome=g)
    result=tasks([dict(id='a',model=model),dict(id='b',model=model)],['x','y'])
    assert len(result)==1 and len(result[0])==1
    assert result[0][0]['aliases']==['a','b'] and result[0][0]['queries']==['x','y']


def test_trace_is_passive_and_matches_native_on_random_and_control():
    from maze_evolution.modular_controls import intact_control
    rng=random.Random(98)
    for g in [intact_control(),*[random_genome(rng) for _ in range(4)]]:
        for family in ('perfect','random','disconnected'):
            o=make_case(812,'m16-test',0,0,9,family);m=o.maze
            native=Organism(g).react(m.cells,m.w,m.h,m.start,m.goal)
            traced,h,mem=respond(dict(genome=g.to_dict()),m)
            assert record(native,o)==record(traced,o)
            assert np.array_equal(h[-1,2]>0,native.mask>0)
            assert h[0,0,m.start]==1 and h[0,1,m.goal]==1
            assert mem<=257*8*81*2


def test_trace_selection_depends_only_on_fixed_metadata():
    meta={x:dict(family='paired',graph='cycle',prefix=2) for x in ('b','a')}
    assert trace_ids(dict(queries={'all':['b','a']},metadata=meta))=={'cycle/2':'a'}
