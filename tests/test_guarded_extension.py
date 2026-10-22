"""M22 material matching, retained branch, bounds, and acceptance gates."""
import random
from copy import deepcopy
from maze_evolution.guarded_extension import fixture_sources
from maze_evolution.guarded_extension_genome import Genome,extension,make_pool
from maze_evolution import guarded_extension_metrics as metrics


def test_identical_material_and_rng_except_selector():
    source=Genome.from_dict(fixture_sources()['anchors']['parent']['genome']);a=b=source
    ra=random.Random(5);rb=random.Random(5)
    for _ in range(5):
        a,ea=extension(a,ra,True);b,eb=extension(b,rb,False)
        assert ra.getstate()==rb.getstate() and a.instructions==b.instructions
        assert a.body.ports==b.body.ports and a.initialization==b.initialization
        for field in ('block','old_register','new_register','condition','new_when_true','payload'):
            assert ea[field]==eb[field]
        assert ea['terminal'][0]==12 and eb['terminal'][0]==0
        assert ea['old_register'] in ea['terminal'][3:5]
        assert ea['new_register'] in ea['terminal'][3:5]


def test_all_ancestor_nodes_ports_and_seeds_are_retained():
    source=Genome.from_dict(fixture_sources()['anchors']['parent']['genome']);g=source;rng=random.Random(91)
    for _ in range(200):
        previous=g;g,event=extension(g,rng,True)
        assert g.instructions<=256 and all(len(b)<=31 for b in g.body.blocks)
        assert g.initialization==source.initialization and g.body.ports==source.body.ports
        assert all(g.body.blocks[k][:len(b)]==b for k,b in enumerate(previous.body.blocks))
        if event['kind']=='bounded_noop':assert g==previous


def test_pool_matches_each_extension_walk_and_is_reproducible():
    s=fixture_sources();p=make_pool(s,44,4,4);assert p==make_pool(s,44,4,4)
    assert len(p['items'])==40
    for anchor in s['anchors']:
        for draw in range(4):
            pair={i['arm']:i for i in p['items'] if i.get('anchor')==anchor and i.get('paired_draw')==draw}
            for a,b in zip(pair['guarded']['steps'],pair['overwrite']['steps']):
                assert a['rng_after']==b['rng_after']
                assert a['event']['payload']==b['event']['payload']
            assert pair['guarded']['edit_seed']==pair['ordinary']['edit_seed']


def cap(success=(),corridors=(),nopath=(),false=()):
    return dict(success=set(success),pairs=set(),corridors=set(corridors),ordinary_bases=set(),correct_no_path=set(nopath),false=set(false),summary={})


def feature(monkeypatch,candidate,root,archive,a0):
    monkeypatch.setattr(metrics,'capabilities_plus',lambda rows,meta:rows)
    item=dict(id='x',kind='mutation',anchor='parent')
    rows={'x':candidate,'anchor/parent':root,'archive':archive,'m14/reference/anchor/0':a0}
    return metrics.features([item],rows,dict(metadata={}),['archive'])[0]['x']


def test_strict_novelty_subtracts_archive_not_just_source(monkeypatch):
    root=cap(['old','d'],nopath=['d']);new=cap(['old','d','new'],corridors=['new'],nopath=['d'])
    assert feature(monkeypatch,new,root,root,root)['strict_novel_additive_pass']
    inherited=feature(monkeypatch,new,root,new,root)
    assert inherited['additive_including_archive_recovery'] and not inherited['strict_novel_additive_pass']


def test_lost_skills_empty_disconnection_and_false_claims_fail(monkeypatch):
    root=cap(['old','d'],nopath=['d']);new=cap(['old','d','new'],corridors=['new'],nopath=['d'])
    bad=deepcopy(new);bad['success'].remove('old');assert not feature(monkeypatch,bad,root,root,root)['strict_novel_additive_pass']
    bad=deepcopy(new);bad['false'].add('oops');assert not feature(monkeypatch,bad,root,root,root)['strict_novel_additive_pass']
    assert not feature(monkeypatch,new,root,root,cap())['strict_novel_additive_pass']
