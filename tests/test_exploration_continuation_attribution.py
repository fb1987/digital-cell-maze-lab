"""An inherited success cannot be relabeled after one neutral phase mutation."""
from copy import deepcopy
from maze_evolution import exploration_continuation_metrics as m
from tests.test_exploration_allocation import gate_fixture


def packet(monkeypatch,entry_is_integrated):
    child,root,union,a0,meta=gate_fixture()
    root.update(pairs={('old',0)},corridors={'corridor'},ordinary_bases={'ordinary'},correct_no_path={1})
    child.update(pairs=child['pairs']|root['pairs'],corridors={'corridor'},ordinary_bases={'ordinary'})
    meta['old']=dict(family='paired',base='old',pose=0,prefix=0,graph='fork',template='old')
    meta['ordinary']=dict(family='ordinary_perfect',base='ordinary',path=[0,1],size=11)
    specialist=deepcopy(child);entry=deepcopy(child if entry_is_integrated else root)
    caps={'child':child,'entry':entry,'root':root,m.PARENT:root,m.SPECIALIST:specialist,'m14/reference/anchor/0':a0}
    comparisons=[];roles={}
    for rep in range(3):
        for arm in ('retention','explore'):
            name=f'modular/{rep}/{arm}'
            roles.setdefault('entry',[]).append([name,'phase_start',0])
            comparisons.append(dict(condition=name,rank=0,child='child',root='root',phase_entry='entry',mutations=1,
                integration=m.integration(child,root,specialist,meta,1)))
    monkeypatch.setattr(m,'capabilities_plus',lambda rows,meta:caps[rows])
    monkeypatch.setattr(m,'comparison',lambda *args:{})
    monkeypatch.setattr(m,'original',lambda *args:dict(conditions=deepcopy(comparisons),protected_identities=[m.PARENT,m.SPECIALIST,'m14/reference/anchor/0'],limitation=''))
    return m.build_summary(dict(roles=roles,start_generation=64),dict(metadata=meta),{i:i for i in caps},{},'test')


def test_neutral_mutation_cannot_claim_inherited_integration(monkeypatch):
    s=packet(monkeypatch,True)
    assert all(c['integration']['full_endpoint_pass_before_phase_attribution'] for c in s['conditions'])
    assert all(c['integration']['phase_entry_already_integrated'] for c in s['conditions'])
    assert not any(c['integration']['integration_pass'] for c in s['conditions'])
    assert all(p['retention']==p['explore']==0 for p in s['policy_comparison']['pairs'])


def test_new_integration_can_pass_same_strict_endpoint(monkeypatch):
    s=packet(monkeypatch,False)
    assert all(c['integration']['integration_pass'] for c in s['conditions'])
    assert not any(c['integration']['phase_entry_already_integrated'] for c in s['conditions'])
