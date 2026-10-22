"""Saved-row analysis checks, with no maze generation or organism inference."""
from collections import Counter
from tools.analyze_m19_history import features, compare_caps, union_caps, allocate_aliases


def row(case, optimal=False, no_path=False, reachable=True, mask='00', status='emitted'):
    return dict(case=case, optimal=optimal, no_path=no_path, reachable=reachable,
                mask=mask, status=status, steps=1, reads=2, dispatches=3, exposure_checks=0)


def test_only_queried_ordinary_bases_count():
    meta = {'a':dict(family='ordinary_perfect',base='queried',path=list(range(18))),
            'b':dict(family='ordinary_perfect',base='queried',path=list(range(18))),
            'unqueried':dict(family='ordinary_perfect',base='unused',path=list(range(30)))}
    cap=features([row('a',True),row('b',True)],meta)
    assert cap['long16']=={'queried'} and cap['ordinary_bases']=={'queried'}
    assert cap['work']==10


def test_complete_pairs_are_not_individual_success_union():
    meta={i:dict(family='paired',base='pair',pose=0,graph='cycle',prefix=2) for i in ['a','b']}
    left=features([row('a',True),row('b')],meta)
    right=features([row('a'),row('b',True)],meta)
    child=features([row('a',True),row('b',True)],meta)
    refs=union_caps([left,right])
    assert refs['success']=={'a','b'} and not refs['pairs']
    cmp=compare_caps(child,left,refs,left,left)
    assert cmp['novel_upstream']==1 and cmp['novel_reachable_success']==0


def test_missing_parent_and_empty_disconnection_are_explicit():
    m={'a':dict(family='corridor')};cap=features([row('a',True)],m)
    v=compare_caps(cap,None,union_caps([cap]),None,cap)
    assert v['parent_all_correct_retained'] is None
    assert not v['parent_available'] and not v['a0_disconnection_90pct']
    assert not v['portfolio_gain_parent_kept'] and not v['upstream_retention_gate']


def test_correct_disconnection_loss_fails_parent_retention():
    meta={'a':dict(family='corridor'),'d':dict(family='ordinary_disconnected',base='disconnected')}
    parent=features([row('a'),row('d',no_path=True,reachable=False,status='no_path')],meta)
    child=features([row('a',True),row('d',reachable=False)],meta)
    v=compare_caps(child,parent,union_caps([parent]),parent,parent)
    assert v['parent_new_correct']==1 and v['parent_lost_correct']==1
    assert not v['parent_all_correct_retained'] and not v['portfolio_gain_parent_kept']


def test_cost_change_does_not_imply_terminal_change():
    m={'a':dict(family='corridor')};r=row('a',True)
    parent=features([r],m);child=features([dict(r,reads=8,steps=2)],m)
    v=compare_caps(child,parent,union_caps([parent]),parent,parent)
    assert v['same_terminal_as_parent'] and not v['same_steps_as_parent']
    assert v['work_delta_from_parent']==6


def test_padding_is_nominally_charged_and_never_a_biological_identity():
    states=[{'name':'generic'},{'name':'connected'}];rows=[{},{}];logical=Counter()
    f={'queried':('a','b','c')}
    allocate_aliases([(0,'organism'),(0,'budget_padding/0/1'),(1,'same_genotype_alias')],f,states,rows,logical,'assessment')
    assert logical=={'generic/assessment':6,'connected/assessment':3}
    assert set(rows[0])=={'organism'} and set(rows[1])=={'same_genotype_alias'}
