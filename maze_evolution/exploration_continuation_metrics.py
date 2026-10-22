"""Unchanged M14 endpoints, explicitly attributed to new M15 mutations."""
from .exploration_allocation_metrics import build_summary as original,capabilities_plus,comparison,integration,criterion,FIELDS,PARENT,SPECIALIST,policy_comparison
from .routing_transfer import canonical


def build_summary(choices,data,rows,usage,chain):
    result=original(choices,data,rows,usage,chain)
    meta=data['metadata'];caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    protected=result['protected_identities']
    union={k:set().union(*(caps[i][k] for i in protected)) for k in (*FIELDS,'false','success')}
    for c in result['conditions']:
        entry=caps[c['phase_entry']];a=caps[c['child']]
        phase_start=[i for i,roles in choices['roles'].items() if [c['condition'],'phase_start',c['rank']] in roles]
        assert len(phase_start)==1
        c.update(versus_phase_entry=comparison(a,entry,meta),phase_start_nominee=phase_start[0],
            versus_phase_start=comparison(a,caps[phase_start[0]],meta))
        # Inherited successes cannot become M15 acquisitions merely by mutating.
        inherited_gate=integration(entry,caps[PARENT],caps[SPECIALIST],meta,1)['integration_pass']
        c['integration']['phase_entry_already_integrated']=inherited_gate
        c['integration']['full_endpoint_pass_before_phase_attribution']=c['integration']['integration_pass']
        c['integration']['integration_pass']=bool(c['integration']['integration_pass'] and not inherited_gate)
        adjusted={k:union[k]|entry[k] for k in union}
        c['historical_root_and_protected_criterion']=criterion(a,caps[c['root']],union,caps['m14/reference/anchor/0'],meta,c['mutations'])
        c.update(criterion(a,caps[c['root']],adjusted,caps['m14/reference/anchor/0'],meta,c['mutations']))
        c['phase_attribution']='mutations counts M15 only; novelty excludes inherited phase-entry skills as well as root and protected union'
    result['policy_comparison']=policy_comparison(result['conditions'])
    result['phase']='M15';result['start_generation']=choices['start_generation']
    result['limitation']+=' Exact M14 generation-64 continuation: arms already differ at entry. This extends their matched histories, not a fresh randomization. Original IDs/RNG and cumulative depths preserved; phase mutation counts and entry comparisons distinguish inheritance. No inference that more time caused a gain without a matched no-continuation comparison on these cases.'
    return canonical(result)
