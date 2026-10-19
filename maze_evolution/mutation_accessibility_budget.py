"""Explicit pre-scientific R budget amendment; no fitness or output fields."""
from .mutation_accessibility_study import ARMS,eligible,identities_for_models

def plans(pool,rates):
    roots={r['id'] for r in pool['roots'].values()}|{pool['control']}
    root_cost=sum(rates[pool['aliases'][i]] for i in roots);out={}
    for n in (16,8,4):
        discovery=2*768*sum(rates[pid] for pid in identities_for_models(pool,eligible(pool,n)))
        worst=sum(max(rates[pool['aliases'][i]] for i in g[a][:n]) for g in pool['groups'].values() for a in ARMS)
        validation=2*768*(2*worst+root_cost);final=2*5184*(worst+root_cost)
        out[str(n)]=dict(discovery=discovery,validation=validation,confirmation=final,total=discovery+validation+final)
    return out

def verify_profile(pool,rates,profile):
    bounds=plans(pool,rates);n=next((n for n in (16,8,4) if bounds[str(n)]['total']<600),0)
    assert profile['bounds']==bounds and profile['walks_per_root_block']==n and profile['passed']==bool(n)
    assert profile['projected_seconds']==bounds[str(n)]['total']
    assert profile['planned_calls_upper']==(6+60*n)*768+126*768+66*5184
