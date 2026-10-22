"""M19 fixed-role novel routing endpoint, retention, and explicit phase attribution."""
from collections import defaultdict
from .breeding_allocation_metrics import capabilities_plus,upstream_pairs,comparison,criterion
from .exploration_allocation_metrics import integration,FIELDS
from .connected_evolution_search import PARENT,SPECIALIST
from .connected_evolution_genome import ARMS,Genome,graph
from .routing_transfer import canonical


def policy_comparison(conditions):
    index={(c['replicate'],c['arm'],c['rank']):c for c in conditions};pairs=[]
    for rep in range(3):
        roles={a:index[(rep,a,0)] for a in ARMS}
        scores={a:(c['beyond_root_and_protected_union']['new_upstream_pairs'] if c['retention_and_disconnection_gate'] else 0) for a,c in roles.items()}
        pairs.append(dict(replicate=rep,**scores,connected_minus_generic=scores['connected']-scores['generic'],
            connected_minus_disconnected=scores['connected']-scores['disconnected'],nominees={a:c['child'] for a,c in roles.items()}))
    def contrast(field):
        ds=[p[field] for p in pairs];return dict(differences=ds,positive_pairs=sum(d>0 for d in ds),sum=sum(ds),descriptive_support=sum(d>0 for d in ds)>=2 and sum(ds)>0)
    a=contrast('connected_minus_generic');b=contrast('connected_minus_disconnected')
    return dict(primary='Fixed integrated-role new nonfork prefix2+ complete pairs beyond exact root, phase entry and ALL13 protected references, zero unless retention/disconnection and M19 mutation gates pass',
        pairs=pairs,connected_vs_generic=a,attachment_vs_disconnected=b,descriptive_support_both=bool(a['descriptive_support'] and b['descriptive_support']),
        limitation='Three matched trios from related random-origin entries; descriptive rule, not significance or independent origins. No substitution of secondary roles.')


def acquisition(a,root,entry,union,a0,meta,mutations):
    from .breeding_allocation_metrics import retention
    adjusted={k:union[k]|entry[k] for k in union}
    v=criterion(a,root,adjusted,a0,meta,mutations);keep=retention(a,entry)
    entry_gate=all(x is None or x>=.9 for x in keep.values())
    v['root_and_A0_gate_before_entry_retention']=v['retention_and_disconnection_gate']
    for k in ('retention_and_disconnection_gate','upstream_acquisition','long_ordinary_acquisition','combined_transfer'):
        v[k]=bool(v[k] and entry_gate)
    return v,keep


def build_summary(choices,data,rows,usage,chain):
    meta=data['metadata'];caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    protected={i for i,roles in choices['roles'].items() if any(r[1]=='protected' for r in roles)}
    union={k:set().union(*(caps[i][k] for i in protected)) for k in (*FIELDS,'false','success')}
    conditions=[];strata={}
    for identity,rs in rows.items():
        groups=defaultdict(set)
        for r in rs:
            m=meta[r['case']]
            if m['family'] in ('ordinary_perfect','ordinary_random'):
                groups[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(m['base'])
        strata[identity]={k:dict(bases=len(bs),correct_both_poses=len(bs&caps[identity]['ordinary_bases'])) for k,bs in groups.items()}
    for c in choices['comparisons']:
        a=caps[c['child']];root=caps[c['root']];entry=caps[c['phase_entry']]
        adjusted={k:union[k]|entry[k] for k in union}
        frozen=[i for i,roles in choices['roles'].items() if [c['condition'],'frozen',c['rank']] in roles];assert len(frozen)==1
        v,keep=acquisition(a,root,entry,union,caps['m14/reference/anchor/0'],meta,c['mutations'])
        integ=integration(a,caps[PARENT],caps[SPECIALIST],meta,c['mutations'])
        integ['phase_entry_already_integrated']=integration(entry,caps[PARENT],caps[SPECIALIST],meta,1)['integration_pass']
        integ['integration_pass']=bool(integ['integration_pass'] and not integ['phase_entry_already_integrated'])
        g=Genome.from_dict(choices['items'][c['child']]['genome']);reads=graph(g)
        conditions.append(dict(**c,role=('integrated','upstream_exploratory','ordinary')[c['rank']],metrics=a['summary'],
            versus_root=comparison(a,root,meta),versus_parent=comparison(a,caps[c['parent']],meta) if c['parent'] else None,
            versus_phase_entry=comparison(a,entry,meta),phase_entry_retention=keep,
            fixed_retention_reference=PARENT,versus_fixed_retention_reference=comparison(a,caps[PARENT],meta),
            target_specialist=SPECIALIST,versus_target_specialist=comparison(a,caps[SPECIALIST],meta),integration=integ,
            frozen_reference=frozen[0],versus_frozen=comparison(a,caps[frozen[0]],meta),
            genome=dict(instructions=g.instructions,active_spares=[k for k in (8,9) if g.body.blocks[k]],
                initialization=list(g.initialization),spares_read_by_active_writers=sorted(set().union(*reads)&{8,9})),**v))
    return canonical(dict(phase='M19',status='evaluated',independent_confirmation=True,chain=chain,usage=usage,
        queries=len(data['queries']['all']),conditions=conditions,policy_comparison=policy_comparison(conditions),
        protected_identities=sorted(protected),all_models={i:c['summary'] for i,c in caps.items()},ordinary_length_strata=strata,
        limitation='New matched forks in a common unchanged M18 VM; generic mutation versus 25% eligible initialized disconnected/connected copying. All use common spare deletion, exploration allocation and frozen M11 retention banks. Nine histories share thirteen preserved random-origin sources; not independent origins. Equal nominal queries/opportunities, not equal CPU. Bank-conditioned development, familiar grammar transfer, no general-solver or speed claim. Mutation counts distinguish inherited M15 source-study depth from M19 births.'))
