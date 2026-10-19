import numpy as np

from maze_evolution.foundation_data import load_pairs
from maze_evolution.route_confirmation_data import FIXTURES
from maze_evolution.route_confirmation_analysis import strict_choice, scope_statistics


def test_strict_choice_accepts_each_oracle_exit_and_rejects_branched_or_disconnected_masks():
    _,groups=load_pairs(FIXTURES)
    for group in groups:
        if group.level<0:continue
        pair=group.pairs[0]
        masks=[]
        for side,o in enumerate(pair.cases):
            mask=np.zeros(len(o.maze.cells),np.uint8);mask[o.path]=1
            assert strict_choice(mask,o,side)
            disconnected=mask.copy();disconnected[o.maze.start]=0
            assert not strict_choice(disconnected,o,side)
            masks.append(mask)
        union=masks[0]|masks[1]
        assert not strict_choice(union,pair.first,0)
        assert not strict_choice(union,pair.second,1)


def test_group_aggregation_does_not_count_two_poses_as_two_independent_bases():
    cases,groups=load_pairs(FIXTURES);g=groups[0];rows={}
    for pose,pair in enumerate(g.pairs):
        for o in pair.cases:
            rows[o.maze.case_id]=dict(case=o.maze.case_id,reachable=True,valid=pose<2,optimal=pose<2,
                no_path=False,status='emitted',failure='' if pose<2 else 'branch_or_cycle',
                dispatches=10,reads=5,array_bytes=10)
    result=scope_statistics(rows,[g],cases)
    assert result['optimal']==4 and result['complete_pairs']==2
    assert result['successful_bases']==1 and result['all_pose_bases']==0
