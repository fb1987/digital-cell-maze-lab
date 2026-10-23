"""M25 checkpoint, bounded selection and equal-budget invariants. No new mazes."""
from copy import deepcopy
from collections import Counter
import random
from maze_evolution.skill_integration_checkpoint import founders,START,PRIOR,comparison_archive
from maze_evolution.skill_integration_data import retention_panel,validation
from maze_evolution.skill_integration_search import balance_rank,quality_profile
from maze_evolution import skill_integration as m
from maze_evolution.skill_integration_metrics import policy_comparison


def test_exact_whole_checkpoint_pairs_and_rng():
    ss=founders();old={s['name']:s for s in m.readz(PRIOR/'final_states.json.gz')}
    assert len(ss)==6
    for a,b in zip(ss[::2],ss[1::2]):
        source=old[a['predecessor_name']]
        for key in ('population','archive','protected','frozen','nominees','rng','generation','arm','method','allocation'):
            assert a[key]==b[key]==source[key]
        assert a['policy']=='current' and b['policy']=='integrate' and a['generation']==START
    assert founders(123)==founders(98765)


def test_only_historical_M24_comparators_not_founders():
    ss=founders();assert all(s['arm']=='enabled' for s in ss)
    source_items={i['id']:i for s in m.readz(PRIOR/'final_states.json.gz') for i in s['population']+s['archive']}
    assert all(i==source_items[i['id']] for s in ss for i in s['population'])
    assert len(comparison_archive())==100
    assert any(any(study=='M24' for study,i in a['source_aliases']) for a in comparison_archive())


def test_fixed_retention_panel_complete_units_and_scope():
    data=validation(None,None);panel=retention_panel();meta=data['metadata']
    for rep,ids in panel.items():
        assert len(ids)==len(set(ids))==24 and set(ids)<=set(data['queries'][rep+'/enabled'])
        counts=Counter(meta[c]['family'] for c in ids)
        assert counts=={'paired':8,'corridor':12,'disconnected':2,'ordinary_disconnected':2}
        units=Counter((meta[c]['base'],meta[c]['pose']) for c in ids if meta[c]['family']=='paired')
        assert len(units)==4 and set(units.values())=={2}
        assert len({meta[c]['graph'] for c in ids if meta[c]['family']=='paired'})==3
    assert panel==retention_panel()


def test_balanced_skill_beats_one_domain_specialist_without_hard_ban():
    fields=('pairs','corridors','ordinary_bases','correct_no_path')
    protected=[dict(id='ref')]
    ref={k:{0,1} for k in fields};ref['pairs']={('p0',0),('p1',0)};ref['false']=set()
    balanced={k:{next(iter(ref[k]))} for k in fields};balanced['false']=set()
    narrow={k:set(v) if k!='ordinary_bases' else set() for k,v in ref.items()}
    caps={'ref':ref,'balanced':balanced,'narrow':narrow}
    meta={f'p{n}':dict(family='paired',base=f'p{n}',pose=0,graph='fork',prefix=0) for n in (0,1)}
    row=dict(case='p0',reachable=True,status='emitted',optimal=False,valid=False,no_path=False,partial=.5)
    rows={i:[row] for i in caps}
    assert balance_rank(dict(id='balanced'),rows,meta,caps,protected)>balance_rank(dict(id='narrow'),rows,meta,caps,protected)
    assert quality_profile([dict(row,failure='missing_endpoint',mask='00')]) is not None
    assert quality_profile([dict(row,status='no_path',failure='missing_endpoint',mask='00')]) is None


def test_nominal_training_and_assessment_budgets():
    ss=founders();d=dict(kind='train',queries={s['curriculum']:list(range(120)) for s in ss})
    for data,expected in ((d,96*120),(dict(kind='assessment',queries={s['curriculum']:list(range(392)) for s in ss}),115*392)):
        counts=Counter()
        for task in m.task_specs(ss,data):
            for e in task:
                for k,i in e['aliases']:counts[k]+=len(e['queries'])
        assert counts==Counter({k:expected for k in range(6)})


def test_sleep_counts_against_clock(monkeypatch):
    monkeypatch.setattr(m.time,'monotonic',lambda:101.);monkeypatch.setattr(m.time,'time',lambda:150.)
    assert m.elapsed((100.,100.))==50.


def test_primary_never_switches_roles_and_zeros_failed_gate():
    cs=[]
    for rep in range(3):
        for policy in ('current','integrate'):
            for rank in range(3):
                cs.append(dict(replicate=rep,policy=policy,rank=rank,child=f'{rep}/{policy}/{rank}',retention_and_disconnection_gate=True,
                    beyond_root_and_protected_union=dict(new_long_bases=1 if policy=='integrate' else 0)))
    p=policy_comparison(cs);assert p['descriptive_support'] and p['positive_pairs']==3
    for c in cs:
        if c['policy']=='integrate' and c['rank']==0:c['retention_and_disconnection_gate']=False
        elif c['policy']=='integrate':c['beyond_root_and_protected_union']['new_long_bases']=999
    p=policy_comparison(cs);assert not p['descriptive_support'] and p['total_difference']==0
