from maze_evolution.mutation_accessibility_study import *
from maze_evolution.mutation_accessibility_budget import plans

def test_per_group_maxima_bound_arbitrary_nominees():
    p=read_compressed(OUT/'pool.json.gz');rates=read_compressed(FIXTURES/'rates.json.gz');b=plans(p,rates)
    assert b['16']['total']>600 and b['8']['total']<600
    for n in (4,8,16):
        chosen=[g[a][0] for g in p['groups'].values() for a in ARMS]+[r['id'] for r in p['roots'].values()]+[p['control']]
        assert 2*5184*sum(rates[p['aliases'][i]] for i in chosen)<=b[str(n)]['confirmation']
        assert b[str(n)]['total']==sum(b[str(n)][k] for k in ('discovery','validation','confirmation'))
