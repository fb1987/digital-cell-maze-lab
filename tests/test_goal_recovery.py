from maze_evolution.goal_recovery import wilson_case,FinalData
from maze_evolution.goal_data import layout_hash
from cellular_maze_lab import neighbors


def test_wilson_perfect_is_tree_and_reproducible():
    layouts=set()
    for i in range(50):
        a=wilson_case(1054,'unit',0,i);b=wilson_case(1054,'unit',0,i)
        assert a.maze==b.maze and a.path
        m=a.maze;vertices=sum(m.cells)
        edges=sum(m.cells[q] for p,v in enumerate(m.cells) if v for q in neighbors(p,9,9))//2
        assert vertices==31 and edges==vertices-1
        layouts.add(layout_hash(m))
    assert len(layouts)>45


def test_repaired_final_avoids_prior_layouts_and_keeps_divergent_targets():
    d=FinalData(1055)
    first=d.tests(0,1)
    for rep in (1,2):
        cases=d.tests(rep,1);pairs=d.paired_tests(rep)
        assert len(cases)==32 and len(pairs)==8
        for pair in pairs:
            a,b=pair.cases
            if not pair.mixed:
                assert a.to_goal[b.maze.goal]>=max(len(a.path)-1,len(b.path)-1)>=8
    assert len({layout_hash(o.maze) for o in d.cache.values() if o.maze.split=='test_goal'})==96
