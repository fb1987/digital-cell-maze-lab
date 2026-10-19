from copy import deepcopy
import pytest
from maze_evolution.robustness_data import RobustnessData,fixtures,confirmation,inputs,batch,validation
from maze_evolution.robustness_audit import geometry,independent_fitness
from maze_evolution.robustness_search import result,archive_rank
from maze_evolution.robustness_study import Budget


def test_fixture_geometry():
    d=RobustnessData(1254);fixtures(d)
    assert geometry(d.cache,d.contexts,d.metadata)==dict(cases=640,contexts=8,whole_layouts=384)


def test_transfer_geometry():
    d=RobustnessData(7654);confirmation(d,'test')
    assert geometry(d.cache,d.contexts,d.metadata)==dict(cases=1920,contexts=24,whole_layouts=1152)
    assert {len(o.path)-1 for o in d.cache.values() if o.path}>={4,5,9}


def test_training_budgets_and_strata():
    d=RobustnessData(7654);assert len(validation(d,0))==208
    for g in range(12):
        ids=batch(d,0,g);assert len(ids)==20
        meta=[d.metadata[i] for i in ids]
        assert len({m['base'] for m in meta})==2
        assert {m['goal_shape'] for m in meta}=={'straight','turning'}
        assert sum(m['family'].startswith('corridor') for m in meta)==4


def fabricated(pairs_per_context):
    rows=[];meta={}
    for context,successes in enumerate(pairs_per_context):
        for pose in range(4):
            for side in range(2):
                cid=f'{context}/{pose}/{side}';ok=pose<successes
                meta[cid]=dict(base=str(context),family='fork',pose=pose,prefix=1)
                rows.append(dict(case=cid,optimal=ok,valid=ok,no_path=False,reachable=True,status='emitted',partial=.2,reads=5,
                    dispatches=5,steps=2,range_reads=[5,0,0]))
    return rows,meta


def test_rank_is_genuine_tradeoff():
    a,m=fabricated([4,0]);b,_=fabricated([3,3])
    assert result(deepcopy(a),m,'pair').fitness<result(deepcopy(b),m,'pair').fitness
    assert result(deepcopy(a),m,'context').fitness>result(deepcopy(b),m,'context').fitness


def test_independent_fitness_and_common_archives():
    rows,m=fabricated([4,2]);a=result(deepcopy(rows),m,'pair');b=result(deepcopy(rows),m,'context')
    assert a.rows==b.rows and a.descriptor==b.descriptor and a.work==b.work
    for ev,p in ((a,'pair'),(b,'context')):assert list(ev.fitness)==independent_fitness(ev.rows,m,p)
    for name in ('context','pair','corridor','distance'):assert archive_rank(a.rows,name)==archive_rank(b.rows,name)


def test_corridors_not_goal_switch_pairs():
    rows,m=fabricated([4,0]);m={cid:dict(v,family='corridor_0') for cid,v in m.items()}
    ev=result(rows,m,'context');assert ev.fitness[:2]==(0,0)


def test_exclusion_all_poses():
    a=RobustnessData(1);fixtures(a)
    from maze_evolution.datasets import manifest
    b=RobustnessData(1,manifest(a.cache.values()));fixtures(b)
    assert len(a.layouts & (b.layouts-a.layouts))==0
    assert len(b.layouts)==768 and b.rejections>0


def test_closed_budget():
    b=Budget(10,0)
    with pytest.raises(TimeoutError):b.call(lambda:None)
