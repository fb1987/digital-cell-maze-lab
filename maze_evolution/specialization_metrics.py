"""M20 fixed additive-retention endpoint; oracle information is evaluation only."""
from collections import defaultdict,Counter
from .breeding_allocation_metrics import capabilities_plus,upstream_pairs,comparison
from .routing_transfer import canonical

FIELDS=('pairs','corridors','ordinary_bases','correct_no_path')


def feature(item, caps, union, meta):
    c=caps[item['id']];anchor=caps['anchor/'+item['anchor']]
    base=caps[item['copy_base']];a0=caps['m14/reference/anchor/0']
    retained=bool(anchor['success']) and anchor['success']<=c['success']
    a0_fraction=len(c['correct_no_path']&a0['correct_no_path'])/len(a0['correct_no_path']) if a0['correct_no_path'] else None
    new={k:c[k]-anchor[k]-base[k] for k in FIELDS}
    additive=bool(retained and not c['false'] and a0_fraction is not None and a0_fraction>=.9 and any(new.values()))
    parent=caps['anchor/parent'];child=caps['anchor/child']
    required=parent['success']|child['success']
    combined=bool(not c['false'] and required<=c['success'] and a0_fraction is not None and a0_fraction>=.9)
    base_combined=bool(not base['false'] and required<=base['success'] and a0['correct_no_path'] and
        len(base['correct_no_path']&a0['correct_no_path'])/len(a0['correct_no_path'])>=.9)
    portfolio={k:c[k]-union[k]-anchor[k]-base[k] for k in FIELDS}
    fresh_up=upstream_pairs(c,meta)-upstream_pairs(union,meta)-upstream_pairs(anchor,meta)-upstream_pairs(base,meta)
    fractions={k:len(c[k]&anchor[k])/len(anchor[k]) if anchor[k] else None for k in FIELDS}
    ratios=[v for v in fractions.values() if v is not None]
    om={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    longer={b for b in portfolio['ordinary_bases'] if len(om[b]['path'])-1>=8}
    score=[int(additive),int(retained and not c['false']),-len(c['false']),min(ratios,default=0),
           a0_fraction or 0,len(fresh_up),sum(map(len,new.values())),sum(ratios),len(c['success'])]
    exploratory=[len(fresh_up),len(portfolio['ordinary_bases']),sum(map(len,new.values())),-len(c['false']),*score]
    return dict(metrics=c['summary'],all_anchor_correct_retained=retained,anchor_correct_denominator=len(anchor['success']),
        lost_anchor_correct=len(anchor['success']-c['success']),new_correct_over_anchor_and_copy=len(c['success']-anchor['success']-base['success']),
        anchor_skill_retention=fractions,a0_correct_disconnection_denominator=len(a0['correct_no_path']),a0_fraction=a0_fraction,
        additive_pass=additive,combined_parent_child_capability=combined,combined_parent_child_pass=bool(combined and not base_combined),
        new_skill_units={k:len(v) for k,v in new.items()},
        new_upstream_beyond_protected=len(fresh_up),new_ordinary_beyond_protected=len(portfolio['ordinary_bases']),
        new_long8_beyond_protected=len(longer),new_long16_beyond_protected=sum(len(om[b]['path'])-1>=16 for b in longer),
        score=score,exploratory_score=exploratory)


def analyze_items(items, rows, data, protected):
    caps={i:capabilities_plus(rs,data['metadata']) for i,rs in rows.items()}
    union={k:set().union(*(caps[i][k] for i in protected)) for k in (*FIELDS,'success')}
    return {i['id']:feature(i,caps,union,data['metadata']) for i in items if i['kind']=='mutation'},caps


def nominate(items, rows, data, protected):
    feats,_=analyze_items(items,rows,data,protected);nominations=[]
    for arm in ('generic','local'):
        for anchor in ('parent','child'):
            for depth in (3,5):
                ids=[i['id'] for i in items if i.get('arm')==arm and i.get('anchor')==anchor and i.get('depth')==depth]
                assert ids
                for role,field in [('additive','score'),('exploratory','exploratory_score')]:
                    identity=min(ids,key=lambda i:(tuple(-v for v in feats[i][field]),i))
                    nominations.append(dict(label=f'{arm}/{anchor}/d{depth}/{role}',identity=identity,arm=arm,anchor=anchor,depth=depth,role=role))
    return canonical(dict(nominations=nominations,features=feats,
        counts={arm:dict(proposals=sum(i.get('arm')==arm for i in items),additive_passes=sum(feats[i['id']]['additive_pass'] for i in items if i.get('arm')==arm)) for arm in ('generic','local')}))


def summarize(items, nominations, rows, data, protected):
    feats,caps=analyze_items(items,rows,data,protected);queried=set(data['queries']['all']);strata=defaultdict(set)
    for cid,m in data['metadata'].items():
        if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random'):
            strata[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(m['base'])
    reports=[]
    for n in nominations:
        i=next(i for i in items if i['id']==n['identity']);f=feats[i['id']]
        reports.append(dict(**n,result=f,versus_anchor=comparison(caps[i['id']],caps['anchor/'+i['anchor']],data['metadata']),
            versus_copy=comparison(caps[i['id']],caps[i['copy_base']],data['metadata']),
            ordinary_length_strata={k:dict(bases=len(bs),correct_both_poses=len(bs&caps[i['id']]['ordinary_bases'])) for k,bs in strata.items()}))
    return canonical(dict(inputs=len(queried),nominations=reports,all_models={i:c['summary'] for i,c in caps.items()},
        primary_additive_passes={arm:[n['label'] for n in reports if n['arm']==arm and n['role']=='additive' and n['result']['additive_pass']] for arm in ('generic','local')},
        combined_passes=[n['label'] for n in reports if n['result']['combined_parent_child_pass']],
        limitation='Fixed neighborhoods of two related random-origin anchors, prospectively initialized copies, 3/5 unselected edit opportunities. Mutation-scope package comparison, equal nominal queries not CPU. No significance, independent-origin, general-solving or speed claim.'))
