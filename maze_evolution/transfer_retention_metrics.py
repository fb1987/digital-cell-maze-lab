"""M27 frozen transfer/retention endpoints. Oracle data is evaluation-only."""
from collections import Counter,defaultdict
from .breeding_allocation_metrics import capabilities_plus
from .routing_transfer import canonical

FIELDS=('pairs','corridors','ordinary_bases','correct_no_path')


def compare(a,b):
    return {k:dict(before=len(b[k]),retained=len(a[k]&b[k]),gained=len(a[k]-b[k]),lost=len(b[k]-a[k]),
                   fraction=len(a[k]&b[k])/len(b[k]) if b[k] else None) for k in FIELDS}


def gate(child,comparators,a0,positive_mutations):
    retains=all(10*len(child[k]&other[k])>=9*len(other[k]) for other in comparators for k in FIELDS)
    a0_nonempty=bool(a0['correct_no_path'])
    disconnected=a0_nonempty and 10*len(child['correct_no_path']&a0['correct_no_path'])>=9*len(a0['correct_no_path'])
    return dict(positive_mutation_ancestry=bool(positive_mutations),domain_retention90=retains,
                a0_nonempty=a0_nonempty,a0_disconnection90=disconnected,zero_false_no_path=not child['false'],
                passes=bool(positive_mutations and retains and disconnected and not child['false']))


def endpoint(c,comparators,portfolio,a0,meta,positive_mutations):
    ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    target={b for b,m in ordinary.items() if len(m['path'])-1>=8}
    old=set().union(*(p['ordinary_bases'] for p in [portfolio]+comparators))
    new=(c['ordinary_bases']&target)-old
    old_success=set().union(*(p['success'] for p in [portfolio]+comparators))
    strong={b for b in new if any(cid not in old_success for cid,m in meta.items() if m.get('base')==b)}
    checks=gate(c,comparators,a0,positive_mutations)
    families={ordinary[b]['family'] for b in new};long16={b for b in new if len(ordinary[b]['path'])-1>=16}
    broad=checks['passes'] and len(new)>=4 and bool(long16) and {'ordinary_perfect','ordinary_random'}<=families
    return dict(raw_novel_complete8=len(new),novel_complete8_keys=sorted(new),
                raw_novel_complete8_beyond_collective=len(strong),novel_beyond_collective_keys=sorted(strong),
                raw_novel_complete16=len(long16),new_by_family=dict(Counter(ordinary[b]['family'] for b in new)),
                gate=checks,primary_score=len(new) if checks['passes'] else 0,broad_transfer=bool(broad))


def build_summary(pool,panels,rows,usage,chain,expected_primary=28):
    data=panels['fresh'];meta={c:data['metadata'][c] for c in data['queries']['all']}
    caps={i:capabilities_plus(rs,meta) for i,rs in rows['fresh'].items()}
    fields=(*FIELDS,'success','false')
    portfolio={k:set().union(*(caps[i][k] for i in pool['historical_references'])) for k in fields}
    assert not set(pool['historical_references'])&set(pool['control_ids'])
    a0=caps['m14/reference/anchor/0'];conditions=[]
    replaymeta={c:panels['replay']['metadata'][c] for c in panels['replay']['queries']['all']}
    replaycaps={i:capabilities_plus(rs,replaymeta) for i,rs in rows['replay'].items()}
    ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    details={}
    for item in pool['items']:
        i=item['id'];c=caps[i];strata=defaultdict(lambda:dict(bases=0,correct_both_poses=0))
        for b,m in ordinary.items():
            length=len(m['path'])-1;label=f"{m['panel_group']}/{m['family']}/{m['size']}/"+('0-7' if length<8 else '8-11' if length<12 else '12-15' if length<16 else '16-23' if length<24 else '24plus')
            strata[label]['bases']+=1;strata[label]['correct_both_poses']+=b in c['ordinary_bases']
        details[i]=dict(roles=item['roles'],metrics=c['summary'],correct_inputs=len(c['success']),
                       false_no_path=len(c['false']),ordinary_length_strata=dict(strata),
                       status_counts=dict(Counter(r['status'] for r in rows['fresh'][i])),
                       counted_work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows['fresh'][i]),
                       max_array_bytes=max(r['array_bytes'] for r in rows['fresh'][i]),
                       max_correct_ordinary_edges=max((len(ordinary[b]['path'])-1 for b in c['ordinary_bases']),default=None))
    for source in pool['conditions']:
        i=source['id'];c=caps[i]
        comparator_ids=list(dict.fromkeys(x for x in (source['parent'],source['root'],source['entry']) if x and x!=i))
        e=endpoint(c,[caps[p] for p in comparator_ids],portfolio,a0,meta,source['phase_mutation_births'])
        replay_bases={replaymeta[c]['base'] for c in source['witness_cases']}
        conditions.append(dict(**source,**e,comparisons={p:compare(c,caps[p]) for p in comparator_ids},
             original_witness_complete_bases=len(replay_bases),
             original_witness_replayed_both=sum(b in replaycaps[i]['ordinary_bases'] for b in replay_bases),
             original_witness_parent_replayed_both=(sum(b in replaycaps[source['parent']]['ordinary_bases'] for b in replay_bases) if source['parent'] else None),
             fresh_correct_ordinary8=len({b for b in c['ordinary_bases'] if len(ordinary[b]['path'])-1>=8}),
             fresh_correct_ordinary16=len({b for b in c['ordinary_bases'] if len(ordinary[b]['path'])-1>=16}),
             no_path_correct=len(c['correct_no_path']),false_no_path=len(c['false'])))
    children=[]
    for relation in pool['offspring_relations']:
        parent,child=relation['parent'],relation['child'];a,b=caps[child],caps[parent]
        witness={replaymeta[c]['base'] for c in relation['parent_witness_cases']}
        parentlong={x for x in b['ordinary_bases'] if len(ordinary[x]['path'])-1>=8}
        children.append(dict(**relation,comparison=compare(a,b),parent_complete8=len(parentlong),
            retained_parent_complete8=len(parentlong&a['ordinary_bases']),
            original_parent_witness_bases=len(witness),
            original_parent_witness_child_success=sum(x in replaycaps[child]['ordinary_bases'] for x in witness),
            zero_false_no_path=not a['false']))
    primary=[c for c in conditions if c['cohort']=='changed_mutant']
    assert len(primary)==expected_primary
    return canonical(dict(status='evaluated',independent_confirmation=True,queries=len(data['queries']['all']),
        replay_queries=len(panels['replay']['queries']['all']),historical_references=pool['historical_references'],
        control_ids=pool['control_ids'],conditions=conditions,offspring=children,all_models=details,
        primary=dict(definition=f'All{expected_primary} pre-frozen changed mutant identities, gated novel complete ordinary8+ bases; no role switching.',
          identities=expected_primary,positive_scores=sum(c['primary_score']>0 for c in primary),max_score=max(c['primary_score'] for c in primary),
          gate_passes=sum(c['gate']['passes'] for c in primary),raw_positive=sum(c['raw_novel_complete8']>0 for c in primary),
          broad_transfer_passes=sum(c['broad_transfer'] for c in primary)),usage=usage,chain=chain,
        limitations='Selected related lineages and finite correlated pose pairs; raw transfer differs from integrated acquisition. No significance, general-solver or speed claim. Shared VM, independent raster grading.'))
