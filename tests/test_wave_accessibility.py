from copy import deepcopy
from maze_evolution.wave_accessibility import pool, tasks, route_precision, select, anchors, selection_score
from maze_evolution.deep_campaign_store import packed,unpacked


def test_pool_replay_and_common_origin():
    aa=anchors();p=pool(202610210101,8,aa)
    assert p==pool(202610210101,8,aa)==unpacked(packed(p))
    assert len(p['items'])==40
    for i in p['items']:
        if i['kind']=='random':assert i['anchor'] is None and i['depth']==0
        else:
            assert len(i['events'])==i['depth']
            if i['depth']==2:assert i['events'][0]['after']==i['events'][1]['before']
            assert (i['intermediate'] is not None)==(i['depth']==2)
    ts=tasks(aa+[dict(aa[0],id='duplicate')],['one'])
    assert sum(map(len,ts))==2
    assert sorted(a for t in ts for e in t for a in e['aliases'])==sorted([a['id'] for a in aa]+['duplicate'])


def test_precision_requires_entire_route_and_emission():
    meta={'c':dict(family='paired',graph='fork',path=[0,1,2])}
    def score(mask,status='emitted'):
        return route_precision([dict(case='c',mask=mask.to_bytes(1,'little').hex(),status=status)],meta)
    assert score(7)['precision']==1
    assert score(15)['precision']==.75
    assert score(7)['precision']>score(15)['precision']>score(3)['precision']==score(0)['precision']==0
    assert score(7,'budget') ['precision']==0
    assert score(15)['full']==1 and score(15)['excess']==1
    meta['c']['graph']='cycle'
    assert score(7)['total']==0


def test_retention_filter_cannot_be_bought_with_high_new_score():
    aa=[dict(id='anchor',kind='accumulating')]
    def f(pairs,eligible=True):
        return dict(rank=[pairs,0,0],metrics=dict(paired=pairs,ordinary_bases_both_poses=0),
            route=dict(full=1,precision=1),versus={'anchor':dict(eligible=eligible)})
    items=[dict(id='lost',anchor='anchor',depth=1,kind='mutant'),
           dict(id='gain',anchor='anchor',depth=2,kind='mutant'),
           dict(id='rnd',anchor=None,depth=0,kind='random')]
    fs={'anchor':f(2),'lost':f(100,False),'gain':f(3),'rnd':f(0,False)}
    cs=select(items,fs,aa);by={c['label']:c['item']['id'] for c in cs}
    assert by['a0/d1/original']=='lost'
    assert by['a0/d1/selective']=='anchor'
    assert by['a0/d2/selective']=='gain'
    assert by['random/retained_a0']=='anchor'


def test_discarded_receipt_selection_replay():
    from maze_evolution.wave_accessibility import OUT, feature, capabilities
    from maze_evolution.foundation_study import read_compressed as readz
    p=readz(OUT/'fixture_pool.json.gz');d=readz(OUT/'fixture.json.gz')
    rr=readz(OUT/'fixture_receipts.json.gz')
    rows={a:e['rows'] for r in rr for e in r['entries'] for a in e['aliases']}
    aa=p['anchors'];parents={a['id']:capabilities(rows[a['id']],d['metadata']) for a in aa}
    fs={i:feature(r,d['metadata'],parents) for i,r in rows.items()}
    assert select(p['pool']['items'],fs,aa)==readz(OUT/'fixture_selection.json.gz')
    assert all(fs[a['id']]['versus'][a['id']]['eligible'] for a in aa)
