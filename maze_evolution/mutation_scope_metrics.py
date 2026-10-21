"""M13 fixed integration endpoint, separately reported deeper-route acquisition."""
from collections import defaultdict
from .breeding_allocation_metrics import capabilities_plus,upstream_pairs,retention,criterion,comparison
from .routing_transfer import canonical

PARENT='m13/reference/quota_parent'
SPECIALIST='m13/reference/quota_child'
FIELDS=('pairs','corridors','ordinary_bases','correct_no_path')

def integration(child,parent,specialist,meta,mutations):
    target=specialist['pairs']-parent['pairs']
    pm={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    contexts={pm[p]['template'] for p in target}
    keep=retention(child,parent)
    covered=target&child['pairs']
    nonvacuous=all(parent[k] for k in FIELDS) and len(target)>=8 and len(contexts)>=2
    parent_gate=bool(mutations and nonvacuous and not child['false'] and all(parent[k]<=child[k] for k in FIELDS))
    return dict(parent_retention=keep,parent_complete_retention_gate=parent_gate,
        reference_denominators_nonvacuous=bool(nonvacuous),specialist_new_pairs=len(target),
        specialist_new_pair_contexts=len(contexts),specialist_pairs_retained=len(covered),
        specialist_pair_fraction=len(covered)/len(target) if target else None,
        specialist_pair_keys=sorted(target),lost_specialist_pair_keys=sorted(target-child['pairs']),
        integration_pass=bool(parent_gate and target<=child['pairs']))

def policy_comparison(conditions):
    by={(c['condition'],c['rank']):c for c in conditions};pairs=[]
    for rep in range(3):
        arms={a:by[(f'modular/{rep}/{a}',0)] for a in ('focused','broad')}
        scores={a:c['integration']['specialist_pairs_retained'] if c['integration']['integration_pass'] else 0 for a,c in arms.items()}
        pairs.append(dict(replicate=rep,**scores,difference=scores['broad']-scores['focused'],
            focused_child=arms['focused']['child'],broad_child=arms['broad']['child']))
    ds=[p['difference'] for p in pairs]
    return dict(primary='Fixed integrated-role specialist-pair count, zero unless full integration gate passes',pairs=pairs,
        positive_pairs=sum(d>0 for d in ds),total_difference=sum(ds),broad_support=sum(d>0 for d in ds)>=2 and sum(ds)>0,
        limitation='Three paired histories, descriptive pilot rule; no significance or general-solver claim. No final-data role switching.')

def build_summary(choices,data,rows,usage,chain):
    meta=data['metadata'];caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    protected={i for i,roles in choices['roles'].items() if any(r[1]=='protected' for r in roles)}
    union={k:set().union(*(caps[i][k] for i in protected)) for k in (*FIELDS,'false','success')}
    a0=caps['m13/reference/anchor/0'];conditions=[];strata={}
    for identity,rs in rows.items():
        groups=defaultdict(set)
        for r in rs:
            m=meta[r['case']]
            if m['family'] in ('ordinary_perfect','ordinary_random'):
                groups[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(m['base'])
        strata[identity]={k:dict(bases=len(bs),correct_both_poses=len(bs&caps[identity]['ordinary_bases'])) for k,bs in groups.items()}
    for c in choices['comparisons']:
        a=caps[c['child']];b=caps[c['root']]
        frozen=[i for i,roles in choices['roles'].items() if [c['condition'],'frozen',c['rank']] in roles];assert len(frozen)==1
        conditions.append(dict(**c,role=('integrated','upstream_exploratory','ordinary')[c['rank']],metrics=a['summary'],
            versus_root=comparison(a,b,meta),versus_parent=comparison(a,caps[c['parent']],meta) if c['parent'] else None,
            fixed_parent_comparison=comparison(a,caps[PARENT],meta),specialist_comparison=comparison(a,caps[SPECIALIST],meta),
            integration=integration(a,caps[PARENT],caps[SPECIALIST],meta,c['mutations']),
            frozen_reference=frozen[0],versus_frozen=comparison(a,caps[frozen[0]],meta),
            **criterion(a,b,union,a0,meta,c['mutations'])))
    return canonical(dict(policy_comparison=policy_comparison(conditions),status='evaluated',independent_confirmation=True,
        chain=chain,usage=usage,queries=len(data['queries']['all']),conditions=conditions,protected_identities=sorted(protected),
        all_models={i:c['summary'] for i,c in caps.items()},ordinary_length_strata=strata,
        limitation='Three paired related histories share twelve exact M10 founder references. C6-focused versus generic all-block mutation; common rotating fresh training, selection and frozen M11 retention banks inform both arms. Banks are reference-conditioned, not unbiased benchmarks. Equal nominal queries, not equal CPU; M11 construction is prior additional cost. Familiar grammars; no general-solving or speed claim.'))
