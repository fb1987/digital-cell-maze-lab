"""M20 mutation-scope and additive-criterion checks without new maze layouts."""
import random
from copy import deepcopy
from maze_evolution.copy_specialization import fixture_sources
from maze_evolution.specialization_genome import Genome,eligible,copy,vary,make_pool
from maze_evolution.specialization_metrics import feature,FIELDS


def test_pool_reproducible_and_matched_material():
    sources=fixture_sources();pool=make_pool(sources,2020,4)
    assert pool==make_pool(sources,2020,4)
    mutants=[i for i in pool['items'] if i['kind']=='mutation']
    assert len(mutants)==16
    for anchor in ('parent','child'):
        for draw in range(4):
            a,b=[i for i in mutants if i['anchor']==anchor and i['paired_draw']==draw]
            assert a['copy_base']==b['copy_base'] and a['edit_seed']==b['edit_seed'] and a['depth']==b['depth']
            assert len(a['steps'])==len(b['steps'])==a['depth']


def test_local_walk_never_changes_other_scaffold_writers():
    original=Genome.from_dict(fixture_sources()['anchors']['parent']['genome']);edge=eligible(original)[0]
    base,_=copy(original,*edge,True);reader,donor,target=edge;g=base;rng=random.Random(17)
    for _ in range(1000):
        g,event=vary(g,rng,'local',(reader,target))
        assert event['block'] in (reader,target)
        for k in set(range(10))-{reader,target}:
            assert g.body.blocks[k]==base.body.blocks[k] and g.body.ports[k]==base.body.ports[k]
            assert g.initialization[k]==base.initialization[k]
        assert g.instructions<=256


def test_generic_can_reach_outside_local_scope():
    g=Genome.from_dict(fixture_sources()['anchors']['parent']['genome']);rng=random.Random(1);blocks=set()
    for _ in range(200):
        g,event=vary(g,rng,'generic',(2,8));blocks.add(event['block'])
    assert blocks==set(range(10))


def cap(success=(),nopath=(),pairs=(),ordinary=()):
    return dict(success=set(success),correct_no_path=set(nopath),pairs=set(pairs),ordinary_bases=set(ordinary),corridors=set(),false=set(),summary={})


def model(c,anchor,base,a0=None):
    caps={'mutant':c,'anchor/parent':anchor,'anchor/child':anchor,'base':base,'m14/reference/anchor/0':a0 or anchor}
    item=dict(id='mutant',anchor='parent',copy_base='base')
    union={k:set() for k in (*FIELDS,'success')}
    return feature(item,caps,union,{})


def test_additive_requires_real_gain_retention_and_nonvacuous_disconnection():
    anchor=cap(['old','d'],['d']);base=cap(['old','d'],['d']);c=cap(['old','d','new'],['d'],pairs=[('p',0)])
    meta={}
    # Pair metadata is needed only for an upstream pair; use a corridor gain here.
    c['pairs']=set();c['corridors']={'new'}
    assert model(c,anchor,base)['additive_pass']
    lost=deepcopy(c);lost['success'].remove('old');assert not model(lost,anchor,base)['additive_pass']
    false=deepcopy(c);false['false']={'oops'};assert not model(false,anchor,base)['additive_pass']
    empty=cap(['old']);assert not model(c,empty,empty,cap())['additive_pass']


def test_copy_inherited_gain_is_not_edit_acquisition():
    anchor=cap(['old','d'],['d']);base=cap(['old','d','new'],['d']);base['corridors']={'new'}
    result=model(deepcopy(base),anchor,base)
    assert not result['additive_pass']
    assert result['combined_parent_child_capability'] and not result['combined_parent_child_pass']
