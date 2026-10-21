from maze_evolution.reboot_data import wilson,ordinary
from maze_evolution.family_evolution_data import AccessData
from maze_evolution.foundation_data import layout_hash,transform_maze
from maze_evolution.deep_confirmation_analysis import compare,capabilities
from cellular_maze_lab import neighbors


def test_wilson_connected_tree_and_reproducible():
    for n in (11,15):
        o=wilson(202610201009,'software/wilson',0,n);m=o.maze
        assert o==wilson(202610201009,'software/wilson',0,n)
        opened=[p for p,v in enumerate(m.cells) if v]
        edges=sum(sum(m.cells[q] for q in neighbors(p,n,n)) for p in opened)//2
        assert edges==len(opened)-1 and all(o.to_goal[p]>=0 for p in opened)
        assert m.start!=m.goal and o.path


def test_ordinary_excludes_all_poses_and_rejects_prior_layout():
    d=AccessData(202610201009);ids=ordinary(d,'software/ordinary',[('perfect',11,2)])
    assert len(ids)==4 and len(d.cache)==16
    assert {layout_hash(o.maze) for o in d.cache.values()}==d.layouts
    again=AccessData(202610201009,d.layouts)
    ordinary(again,'software/ordinary',[('perfect',11,2)])
    assert not {layout_hash(o.maze) for o in again.cache.values()}&d.layouts
    assert again.rejections>=2


def test_gate_does_not_hide_losses_or_false_no_path():
    keys={(f'b{i}',0) for i in range(12)}
    meta={f'c{i}':dict(base=f'b{i}',pose=0,template=f't{i%3}',family='paired') for i in range(12)}
    root=dict(pairs=set(list(sorted(keys))[:2]),corridors={'a','b'},ordinary_bases=set(),false=set())
    child=dict(pairs=keys,corridors={'a'},ordinary_bases=set(),false=set())
    r=compare(child,root,meta);assert not r['acquisition_gate'] and r['retention']['corridors']==.5
    child['corridors']={'a','b'};assert compare(child,root,meta)['acquisition_gate']
    child['false']={'bad'};assert not compare(child,root,meta)['acquisition_gate']
