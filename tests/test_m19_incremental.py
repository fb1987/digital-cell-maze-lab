from tools.analyze_m19_incremental import additions


def cap(success):
    return dict(reachable_success=set(success),upstream=set(),ordinary_bases=set(),long8=set(),long16=set())


def test_portfolio_new_but_parent_inherited_is_not_an_addition():
    result=additions(cap(['x']),cap(['x']),cap([]),cap([]))
    assert result['inherited_coverage']=={'x'}
    assert not result['reachable_success'] and not result['new_reachable_over_parent']


def test_subtract_both_parent_and_protected_and_keep_missing_explicit():
    result=additions(cap(['old','protected','new']),cap(['old']),cap(['protected']),None)
    assert result['reachable_success']=={'new'} and result['phase_new'] is None
    assert additions(cap(['new']),None,cap([]),None) is None
