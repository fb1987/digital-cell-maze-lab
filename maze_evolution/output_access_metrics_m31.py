"""M31 fixed selection and independent endpoints; analysis only, no candidate VM."""
from collections import Counter,defaultdict
from .breeding_allocation_metrics import capabilities_plus
from .transfer_retention_metrics import FIELDS,gate,endpoint,compare
from .routing_transfer import canonical
from .output_access_genome_m31 import ARMS

def assess_one(condition,c,caps,union,a0,meta,data,rows):
    comparators=condition['comparators'];e=endpoint(c,[caps[p] for p in comparators],union,a0,meta,not condition['event']['genotype_noop'])
    fractions=[len(c[k]&caps[p][k])/len(caps[p][k]) for p in comparators for k in FIELDS if caps[p][k]]
    complete=[g['id'] for g in data.get('contrasts',[]) if g['kind']=='route_swap' and g['a'] in c['success'] and g['b'] in c['success']]
    return dict(**condition,endpoint=e,controlled_route_pairs=len(complete),controlled_pair_keys=complete,
        retention_floor=min(fractions,default=1.),comparisons={p:compare(c,caps[p]) for p in comparators},metrics=c['summary'],
        correct_inputs=len(c['success']),correct_reachable=sum(r['optimal'] for r in rows),correct_no_path=len(c['correct_no_path']),false_no_path=len(c['false']),
        work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows),status_counts=dict(Counter(r['status'] for r in rows)))

def package(details,pool,meta,controls_correct):
    return canonical(dict(conditions=details,queries=len(meta),historical_reference_aliases=len(pool['historical_references']),
        controls_all_correct=controls_correct,
        by_arm={a:dict(opportunities=sum(c['arm']==a for c in details),changed=sum(c['arm']==a and not c['event']['genotype_noop'] for c in details),
            controlled_pair_positive=sum(c['arm']==a and c['controlled_route_pairs']>0 for c in details),
            raw_ordinary8_positive=sum(c['arm']==a and c['endpoint']['raw_novel_complete8']>0 for c in details),
            gate_passes=sum(c['arm']==a and c['endpoint']['gate']['passes'] for c in details)) for a in ARMS}))

def assess(pool,data,rows):
    meta={c:data['metadata'][c] for c in data['queries']['all']};caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()}
    union={k:set().union(*(caps[i][k] for i in pool['historical_references'])) for k in (*FIELDS,'success','false')}
    a0=caps['m14/reference/anchor/0'];details=[]
    for condition in pool['conditions']:
        i=condition['id']
        if i not in caps:continue
        details.append(assess_one(condition,caps[i],caps,union,a0,meta,data,rows[i]))
    return package(details,pool,meta,all(all(r['optimal'] or r['no_path'] for r in rows[i]) for i in pool['control_ids']))

def nominate_assessed(pool,assessment):
    choices=[]
    for source in pool['parents']:
        for arm in ARMS:
            candidates=sorted((c for c in assessment['conditions'] if c['source']==source and c['arm']==arm),key=lambda x:x['id'])
            keys={
                'INTEGRATED':lambda x:(x['endpoint']['gate']['passes'],x['controlled_route_pairs'],x['endpoint']['raw_novel_complete8'],x['retention_floor'],x['correct_reachable'],x['correct_inputs'],-x['work']),
                'OUTPUT_EXPLORATORY':lambda x:(x['controlled_route_pairs'],x['endpoint']['raw_novel_complete8'],x['correct_reachable'],x['retention_floor'],x['correct_inputs'],-x['work']),
                'RETENTION':lambda x:(x['endpoint']['gate']['passes'],x['retention_floor'],x['endpoint']['raw_novel_complete8'],x['controlled_route_pairs'],x['correct_reachable'],x['correct_inputs'],-x['work'])}
            for role,key in keys.items():
                selected=candidates[0]
                for c in candidates:
                    if key(c)>key(selected):selected=c
                choices.append(dict(source=source,arm=arm,role=role,id=selected['id'],development=selected))
    wanted={c['id'] for c in choices}|set(pool['historical_references'])|set(pool['control_ids'])
    return canonical(dict(choices=choices,items=[i for i in pool['items'] if i['id'] in wanted],fresh_cases_generated=False,
        historical_references=pool['historical_references'],control_ids=pool['control_ids'],
        primary='Fixed INTEGRATED role per source/arm; final gated novel complete ordinary8+ beyond all declared historical comparison aliases. No role switching.')),assessment

def nominate(pool,data,rows):return nominate_assessed(pool,assess(pool,data,rows))

def summarize(pool,choices,data,rows,usage,chain):
    result=assess(pool,data,rows);lookup={c['id']:c for c in result['conditions']}
    selected=[dict(source=c['source'],arm=c['arm'],role=c['role'],id=c['id'],final=lookup[c['id']]) for c in choices['choices']]
    comparisons={}
    for other in ('ordinary','C6'):
        pairs=[]
        for source in pool['parents']:
            selected_for={c['arm']:c for c in selected if c['source']==source and c['role']=='INTEGRATED'}
            scores={a:c['final']['endpoint']['primary_score'] for a,c in selected_for.items()}
            pairs.append(dict(source=source,output=scores['output'],control=scores[other],difference=scores['output']-scores[other]))
        differences=[p['difference'] for p in pairs]
        comparisons['output_vs_'+other]=dict(pairs=pairs,positive_pairs=sum(d>0 for d in differences),sum_difference=sum(differences),
            descriptive_support=sum(d>0 for d in differences)>=2 and sum(differences)>0)
    meta={c:data['metadata'][c] for c in data['queries']['all']};ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')};strata={};all_metrics={}
    for i,rs in rows.items():
        cap=capabilities_plus(rs,meta);bins=defaultdict(lambda:dict(bases=0,complete=0))
        for b,m in ordinary.items():
            edges=len(m['path'])-1;key=f'{m["family"]}/{m.get("size")}/'+('0-7' if edges<8 else '8-15' if edges<16 else '16plus')
            bins[key]['bases']+=1;bins[key]['complete']+=b in cap['ordinary_bases']
        strata[i]=dict(bins);all_metrics[i]=cap['summary']
    result.update(choices=selected,policy_comparison=comparisons,combined_descriptive_support=all(c['descriptive_support'] for c in comparisons.values()),
        independent_confirmation=True,ordinary_bases=len(ordinary),ordinary8_bases=sum(len(m['path'])-1>=8 for m in ordinary.values()),
        ordinary16_bases=sum(len(m['path'])-1>=16 for m in ordinary.values()),ordinary_length_strata=strata,all_model_metrics=all_metrics,usage=usage,chain=chain,
        limitation='Finite related one-opportunity neighborhoods, not evolution or independent origins. Matched seeds/opportunities and nominal cases, not equal CPU. Distinct mutation scopes/material. No role substitution, significance, speed or general-solver claim.')
    return canonical(result)
