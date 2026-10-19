"""V12O normal-output supply measurements and common frozen nominee rules."""
import hashlib,json
from collections import defaultdict
from .branch_pressure_fitness import measurements,selected
from .routing_transfer import canonical


def summarize(rows,meta):
    m=measurements(rows,meta);pairs=defaultdict(list)
    for r in rows:
        if meta[r['case']]['family']=='paired':pairs[meta[r['case']]['base'],meta[r['case']]['pose']].append(r)
    detail={(d['base'],d['pose']):d for d in m['details']}
    for key,rs in pairs.items():
        a,b=sorted(rs,key=lambda r:meta[r['case']]['side']);pa,pb=[set(meta[r['case']]['path']) for r in (a,b)];goals={meta[r['case']]['path'][-1] for r in (a,b)}
        aa=(pa-pb)-goals;bb=(pb-pa)-goals;x,y=selected(a),selected(b);normal=a['status']==b['status']=='emitted'
        da=(len(x&aa)-len(y&aa))/len(aa) if aa else 0.;db=(len(y&bb)-len(x&bb))/len(bb) if bb else 0.
        detail[key].update(signed=(da+db)/2 if aa and bb and normal else 0.,normal_both=normal,
            switch_away=bool((x^y)-goals) and normal,interior_switch=bool((x^y)&(aa|bb)) and normal,
            response_signature=hashlib.sha256(bytes.fromhex(a['mask'])+bytes.fromhex(b['mask'])+a['status'].encode()+b['status'].encode()).hexdigest())
    m['mean_signed']=sum(d['signed'] for d in m['details'] if d['eligible'])/max(1,m['eligible_pairs'])
    m['mask_signature']=hashlib.sha256(b''.join(bytes.fromhex(r['mask']) for r in rows)).hexdigest()
    m['response_signature']=hashlib.sha256(json.dumps([(r['mask'],r['status']) for r in rows],separators=(',',':')).encode()).hexdigest()
    m['counter_signature']=hashlib.sha256(json.dumps([(r['steps'],r['active'],r['reads'],r['dispatches'],r['range_reads'],r['exposure_checks']) for r in rows],separators=(',',':')).encode()).hexdigest()
    m['paired_signature']=hashlib.sha256(''.join(d['response_signature'] for d in m['details']).encode()).hexdigest()
    return canonical(m)


def compare(child,root):
    a={(d['base'],d['pose']):d for d in child['details']};b={(d['base'],d['pose']):d for d in root['details']};assert a.keys()==b.keys()
    gains=[k for k,d in a.items() if d['eligible'] and d['positive'] and d['score']-b[k]['score']>=.1-1e-12]
    lost=[k for k,d in b.items() if d['positive'] and not a[k]['positive']]
    new_complete=[k for k,d in a.items() if d['complete'] and not b[k]['complete'] and d['kind']!='adjacent']
    useful=child['mean_score']>=.01 and child['positive_pairs']>=2 and len(gains)>=2
    return dict(useful=useful,mask_changed=child['mask_signature']!=root['mask_signature'],counter_changed=child['counter_signature']!=root['counter_signature'],response_changed=child['response_signature']!=root['response_signature'],
        new_positive_pairs=len(gains),new_positive_templates=len({k[0] for k in gains}),lost_positive_pairs=len(lost),new_nonadj_pairs=len(new_complete),
        pair_gain=child['pairs']-root['pairs'],corridor_gain=child['corridors']-root['corridors'])


def rank(m,c):
    return (m['nonadj_pairs'],int(c['useful']),round(m['mean_score'],10),m['strict_pairs'],m['pairs'],m['corridors'],m['no_path']-m['false_no_path'])


def nominate(ids,entries,metrics,aliases):
    scored=[]
    for identity in ids:
        e=entries[identity];m=metrics[aliases[identity]];root=metrics[aliases[e['reference']]];c=compare(m,root)
        scored.append((rank(m,c),e['program_digest'],identity,c))
    scored.sort(key=lambda x:(tuple(-v for v in x[0]),x[1],x[2]))
    return dict(nominees=[v[2] for v in scored[:2]],best=scored[0][2],rank=list(scored[0][0]),
        order=[v[2] for v in scored],comparisons={v[2]:v[3] for v in scored})


def supply(ids,entries,metrics,aliases):
    comparisons={i:compare(metrics[aliases[i]],metrics[aliases[entries[i]['reference']]]) for i in ids}
    useful=[i for i,c in comparisons.items() if c['useful']]
    return dict(candidates=len(ids),genotype_unique=len({entries[i]['program_digest'] for i in ids}),useful_genotypes=len({entries[i]['program_digest'] for i in useful}),useful_count=len(useful),useful_references=len({entries[i]['reference'] for i in useful}),
        useful_behaviors=len({metrics[aliases[i]]['paired_signature'] for i in useful}),
        any_positive=sum(metrics[aliases[i]]['mean_score']>0 for i in ids),any_strict=sum(metrics[aliases[i]]['strict_pairs']>0 for i in ids),
        any_nonadj=sum(metrics[aliases[i]]['nonadj_pairs']>0 for i in ids),
        changed_masks=sum(c['mask_changed'] for c in comparisons.values()),changed_counters=sum(c['counter_changed'] for c in comparisons.values()),
        changed_responses=sum(c['response_changed'] for c in comparisons.values()),useful_ids=useful)
