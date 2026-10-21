"""M7 prospective capability criteria, including non-vacuous disconnection retention."""
from collections import defaultdict,Counter
from .deep_confirmation_analysis import capabilities,compare
from .routing_transfer import canonical


def capabilities_plus(rows,meta):
    c=capabilities(rows,meta)
    c['correct_no_path']={r['case'] for r in rows if r['no_path']}
    c['summary']['correct_no_path']=len(c['correct_no_path'])
    c['summary']['disconnected_inputs']=sum(not r['reachable'] for r in rows)
    return c


def upstream_pairs(cap,meta):
    pm={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    return {p for p in cap['pairs'] if pm[p]['graph']!='fork' and pm[p]['prefix']>=2}


def retention(a,b):
    return {k:len(a[k]&b[k])/len(b[k]) if b[k] else None
            for k in ('pairs','corridors','ordinary_bases','correct_no_path')}


def criterion(child,root,protected_union,a0,meta,mutations):
    pm={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    om={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    new=upstream_pairs(child,meta)-upstream_pairs(root,meta)-upstream_pairs(protected_union,meta)
    long=lambda c:{b for b in c['ordinary_bases'] if len(om[b]['path'])-1>=8}
    newlong=long(child)-long(root)-long(protected_union)
    keep=retention(child,root)
    a0_fraction=len(child['correct_no_path']&a0['correct_no_path'])/len(a0['correct_no_path']) if a0['correct_no_path'] else None
    # A zero-skill exact root cannot make correct-disconnection retention vacuous.
    eligible=bool(mutations and all(x is None or x>=.9 for x in keep.values()) and
                  not child['false'] and a0_fraction is not None and a0_fraction>=.9)
    contexts={pm[p]['template'] for p in new}
    families={om[b]['family'] for b in newlong};long16=sum(len(om[b]['path'])-1>=16 for b in newlong)
    up=eligible and len(new)>=8 and len(contexts)>=2
    ordinary=eligible and len(newlong)>=4 and long16>=1 and {'ordinary_perfect','ordinary_random'}<=families
    return dict(root_retention=keep,a0_correct_no_path_retention=a0_fraction,retention_and_disconnection_gate=eligible,
        upstream_acquisition=bool(up),long_ordinary_acquisition=bool(ordinary),combined_transfer=bool(up and ordinary),
        beyond_root_and_protected_union=dict(new_upstream_pairs=len(new),new_contexts=len(contexts),new_upstream_keys=sorted(new),
            new_long_bases=len(newlong),new_long16_bases=long16,new_long_keys=sorted(newlong),
            new_long_by_domain=dict(Counter(om[b]['family']+'/'+str(om[b]['size']) for b in newlong))))


def comparison(a,b,meta):
    c=compare(a,b,meta)
    for key in ('acquisition_gate','gate_checks','broad_transfer_flag'):c.pop(key,None)
    c.update(new_correct_no_path=len(a['correct_no_path']-b['correct_no_path']),
             lost_correct_no_path=len(b['correct_no_path']-a['correct_no_path']))
    return c


def build_summary(choices,data,rows,usage,chain):
    meta=data['metadata'];caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    protected={i for i,roles in choices['roles'].items() if any(r[1]=='protected' for r in roles)}
    union={k:set().union(*(caps[i][k] for i in protected)) for k in
           ('pairs','corridors','ordinary_bases','correct_no_path','false','success')}
    a0=caps['m7/reference/anchor/0'];conditions=[];strata={}
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
            frozen_reference=frozen[0],versus_frozen=comparison(a,caps[frozen[0]],meta),
            **criterion(a,b,union,a0,meta,c['mutations'])))
    policy=policy_comparison(conditions)
    return canonical(dict(policy_comparison=policy,status='evaluated',independent_confirmation=True,chain=chain,usage=usage,
        queries=len(data['queries']['all']),conditions=conditions,protected_identities=sorted(protected),
        all_models={i:c['summary'] for i,c in caps.items()},ordinary_length_strata=strata,
        limitation='Three paired shared/quota histories share seven exact M6-informed random-origin references and clonal founders. Equal logical train allocations and mutation opportunities, not equal CPU. Three pairs give limited policy evidence. Correlated familiar-grammar poses/variants; no general-solver or speed claim.'))


def policy_comparison(conditions):
    """Prespecified primary: integrated-role novel target count, zero unless gated.

    No role switching on confirmation. Quota support needs positive paired
    difference in at least two of three replicates AND positive summed difference.
    This descriptive pilot rule is not a significance test.
    """
    indexed={(c['condition'],c['rank']):c for c in conditions}
    pairs=[]
    for rep in range(3):
        arms={a:indexed[(f'modular/{rep}/{a}',0)] for a in ('shared','quota')}
        scores={a:c['beyond_root_and_protected_union']['new_upstream_pairs']
                if c['retention_and_disconnection_gate'] else 0 for a,c in arms.items()}
        pairs.append(dict(replicate=rep,shared=scores['shared'],quota=scores['quota'],
            difference=scores['quota']-scores['shared'],
            shared_child=arms['shared']['child'],quota_child=arms['quota']['child']))
    differences=[p['difference'] for p in pairs]
    return dict(primary='integrated-role novel nonfork prefix2+ complete pairs, zero when retention/disconnection gate fails',
        pairs=pairs,total_difference=sum(differences),positive_pairs=sum(d>0 for d in differences),
        quota_support=sum(d>0 for d in differences)>=2 and sum(differences)>0,
        limitation='Descriptive three-pair pilot, not a significance test or proof of general solving; roles and endpoint frozen prospectively.')
