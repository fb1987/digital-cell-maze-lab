"""M22 strict novel addition with source retention; fixed roles and archive."""
from collections import defaultdict
from .breeding_allocation_metrics import capabilities_plus,upstream_pairs,comparison
from .guarded_extension_genome import ARMS,ANCHORS
from .routing_transfer import canonical
FIELDS=('pairs','corridors','ordinary_bases','correct_no_path')


def features(items,rows,data,archive):
    caps={i:capabilities_plus(r,data['metadata']) for i,r in rows.items()}
    union={k:set().union(*(caps[i][k] for i in archive)) for k in (*FIELDS,'success')}
    meta=data['metadata'];om={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    a0=caps['m14/reference/anchor/0'];result={}
    for item in items:
        if item['kind']!='mutation':continue
        c=caps[item['id']];root=caps['anchor/'+item['anchor']]
        retained=bool(root['success']) and root['success']<=c['success']
        frac=len(c['correct_no_path']&a0['correct_no_path'])/len(a0['correct_no_path']) if a0['correct_no_path'] else None
        new={k:c[k]-root[k] for k in FIELDS};novel={k:new[k]-union[k] for k in FIELDS}
        clean=bool(retained and not c['false']);gate=bool(clean and frac is not None and frac>=.9)
        strict=bool(gate and any(novel.values()));recovery=bool(gate and any(new.values()))
        keep={k:len(c[k]&root[k])/len(root[k]) if root[k] else None for k in FIELDS}
        ratios=[r for r in keep.values() if r is not None]
        up=upstream_pairs(c,meta)-upstream_pairs(root,meta)-upstream_pairs(union,meta)
        long={b for b in novel['ordinary_bases'] if len(om[b]['path'])-1>=8}
        score=[int(strict),int(clean),-len(c['false']),min(ratios,default=0),frac or 0,
               len(up),sum(map(len,novel.values())),sum(map(len,new.values())),sum(ratios),len(c['success'])]
        exploratory=[len(up),len(novel['ordinary_bases']),sum(map(len,novel.values())),-len(c['false']),*score]
        result[item['id']]=dict(strict_novel_additive_pass=strict,additive_including_archive_recovery=recovery,
            clean_source_retention=clean,lost_source_correct=len(root['success']-c['success']),
            source_correct_denominator=len(root['success']),source_retention=keep,a0_denominator=len(a0['correct_no_path']),a0_fraction=frac,
            new_units_over_source={k:len(v) for k,v in new.items()},novel_units_beyond_archive={k:len(v) for k,v in novel.items()},
            new_individual_inputs_beyond_archive=sorted(c['success']-root['success']-union['success']),
            novel_upstream=len(up),novel_long8=len(long),novel_long16=sum(len(om[b]['path'])-1>=16 for b in long),
            metrics=c['summary'],score=score,exploratory_score=exploratory)
    return result,caps


def nominate(items,rows,data,archive):
    ff,caps=features(items,rows,data,archive);ns=[]
    for arm in ARMS:
        for anchor in ANCHORS:
            for depth in (3,5):
                ids=[i['id'] for i in items if (i.get('arm'),i.get('anchor'),i.get('depth'))==(arm,anchor,depth)]
                assert ids
                for role,field in [('primary','score'),('exploratory','exploratory_score')]:
                    ident=min(ids,key=lambda i:(tuple(-x for x in ff[i][field]),i))
                    ns.append(dict(label=f'{arm}/{anchor}/d{depth}/{role}',identity=ident,arm=arm,anchor=anchor,depth=depth,role=role))
    random_ids=[i['id'] for i in items if i['kind']=='random_control']
    if random_ids:
        identity=min(random_ids,key=lambda i:(len(caps[i]['false']),-len(caps[i]['pairs']),-len(caps[i]['ordinary_bases']),-len(caps[i]['success']),i))
        ns.append(dict(label='random_control/best',identity=identity,role='random_control'))
    return canonical(dict(nominations=ns,features=ff,counts={a:dict(proposals=sum(i.get('arm')==a for i in items),
        strict_passes=sum(ff[i['id']]['strict_novel_additive_pass'] for i in items if i.get('arm')==a),
        clean_retention=sum(ff[i['id']]['clean_source_retention'] for i in items if i.get('arm')==a)) for a in ARMS}))


def summarize(items,nominations,rows,data,archive):
    ff,caps=features(items,rows,data,archive);strata=defaultdict(set);queried=set(data['queries']['all'])
    for cid,m in data['metadata'].items():
        if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random'):
            strata[f"{m['family']}/{m['size']}/{m['length_bin']}"].add(m['base'])
    reports=[]
    for n in nominations:
        if n['role']=='random_control':
            reports.append(dict(**n,metrics=caps[n['identity']]['summary']));continue
        reports.append(dict(**n,result=ff[n['identity']],versus_source=comparison(caps[n['identity']],caps['anchor/'+n['anchor']],data['metadata']),
            ordinary_length_strata={k:dict(bases=len(v),correct_both_poses=len(v&caps[n['identity']]['ordinary_bases'])) for k,v in strata.items()}))
    primary={a:[r['label'] for r in reports if r.get('arm')==a and r['role']=='primary' and r['result']['strict_novel_additive_pass']] for a in ARMS}
    paired=[]
    for anchor in ANCHORS:
        totals={a:sum(sum(r['result']['novel_units_beyond_archive'].values()) for r in reports if r.get('anchor')==anchor and r.get('arm')==a and r['role']=='primary' and r['result']['strict_novel_additive_pass']) for a in ARMS}
        paired.append(dict(anchor=anchor,scores=totals,guarded_minus_overwrite=totals['guarded']-totals['overwrite']))
    diffs=[p['guarded_minus_overwrite'] for p in paired]
    return canonical(dict(inputs=len(queried),nominations=reports,primary_passes=primary,
        policy_comparison=dict(endpoint='Fixed primary-role novel complete skill units, zero unless strict retention/disconnection pass',
            backgrounds=paired,sum_difference=sum(diffs),positive_backgrounds=sum(x>0 for x in diffs),
            descriptive_guard_support=sum(x>0 for x in diffs)>=2 and sum(diffs)>0,
            limitation='Three related backgrounds; depths correlated; descriptive, not significance or independent-origin evidence'),
        all_model_metrics={i:c['summary'] for i,c in caps.items()},archive_identities=archive,
        limitation='Fixed 3/5-opportunity unselected neighborhoods, not sustained evolution. Conditional versus matched unconditional append isolates wrapper package, ordinary arm differs in material/scope. Equal nominal queries not CPU. No general-solver or speed claim.'))
