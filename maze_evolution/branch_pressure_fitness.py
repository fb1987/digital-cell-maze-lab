"""V12N goal-dependent interior-arm score; evaluator-only, ordinary emitted masks."""
from collections import defaultdict
import random
import numpy as np
from .exposure_genome import Individual
from .exposure_selection import evaluate as old_evaluate
from .regulatory_search import Evaluation
from .routing_transfer import canonical


def selected(row,n=81):
    return set(np.flatnonzero(np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:n]).tolist())


def pair_score(rows,meta):
    a,b=sorted(rows,key=lambda r:meta[r['case']]['side']);pa,pb=[set(meta[r['case']]['path']) for r in (a,b)]
    goals={meta[r['case']]['path'][-1] for r in (a,b)}
    aa=(pa-pb)-goals;bb=(pb-pa)-goals
    result=dict(eligible=bool(aa and bb),score=0.,contrast=0.,strict_both=False,positive=False)
    if not aa or not bb or a['status']!='emitted' or b['status']!='emitted':return result
    x,y=selected(a),selected(b)
    da=len(x&aa)/len(aa)-len(y&aa)/len(aa)
    db=len(y&bb)/len(bb)-len(x&bb)/len(bb)
    contrast=max(0.,(da+db)/2)
    f1a=2*len(x&pa)/(len(x)+len(pa));f1b=2*len(y&pb)/(len(y)+len(pb))
    score=contrast*min(f1a,f1b)
    return dict(eligible=True,score=score,contrast=contrast,strict_both=da>0 and db>0,positive=score>0)


def measurements(rows,meta):
    groups=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family']=='paired':groups[m['base'],m['pose']].append(r)
    details={}
    for key,rs in groups.items():
        assert len(rs)==2
        details[key]=dict(pair_score(rs,meta),complete=all(r['optimal'] for r in rs),kind=meta[rs[0]['case']]['kind'])
    eligible=[v for v in details.values() if v['eligible']]
    return dict(pairs=sum(v['complete'] for v in details.values()),nonadj_pairs=sum(v['complete'] and v['kind']!='adjacent' for v in details.values()),
        adjacent_pairs=sum(v['complete'] and v['kind']=='adjacent' for v in details.values()),
        mean_score=sum(v['score'] for v in eligible)/max(1,len(eligible)),eligible_pairs=len(eligible),
        positive_pairs=sum(v['positive'] for v in eligible),strict_pairs=sum(v['strict_both'] for v in eligible),
        positive_templates=len({k[0] for k,v in details.items() if v['positive']}),
        three_edge_positive=sum(v['positive'] and v['kind'] in ('three_edge','three_fork') for v in eligible),
        corridors=sum(r['optimal'] for r in rows if meta[r['case']]['family'].startswith('corridor')),
        optimal=sum(r['optimal'] for r in rows),valid=sum(r['valid'] for r in rows),no_path=sum(r['no_path'] for r in rows),
        false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),
        details=[dict(base=k[0],pose=k[1],**v) for k,v in sorted(details.items())])


def evaluate(rows,meta,pressure):
    old=old_evaluate(rows,meta);ms=measurements(rows,meta);score=round(sum(x['score'] for x in ms['details']),8) if pressure=='choice' else 0.
    lookup={(x['base'],x['pose']):x['score'] for x in ms['details']}
    fitness=(old.fitness[0],score,*old.fitness[1:])
    values=[]
    for r,v in zip(rows,old.case_values):
        m=meta[r['case']];s=lookup.get((m['base'],m['pose']),0.) if m['family']=='paired' and pressure=='choice' else 0.
        values.append((v[0],s,*v[1:]))
    return Evaluation(fitness,values,(),rows,old.work)


def lexicase(rng,ranked):
    survivors=list(ranked);cases=list(range(len(survivors[0][0].case_values)));rng.shuffle(cases)
    for case in cases:
        for field in range(5):
            best=max(e.case_values[case][field] for e,_ in survivors);eps=.02 if field in (1,4) else 0.
            survivors=[(e,i) for e,i in survivors if e.case_values[case][field]>=best-eps]
            if len(survivors)==1:return survivors[0][1]
    return rng.choice(survivors)[1]


def choose(pool,rows,meta,seed,pressure):
    assert pressure in ('current','choice')
    ranked=sorted(((evaluate(rows[i['id']],meta,pressure),Individual.load(i)) for i in pool['items']),key=lambda x:(tuple(-v for v in x[0].fitness),x[1].genome.digest,x[1].identity))
    rng=random.Random(seed);before=rng.getstate();parents=[lexicase(rng,ranked).identity for _ in range(64)]
    elite=[i.identity for _,i in ranked[:max(1,len(ranked)//4)]]
    # The exact same protected anchors occupy elite slots under both pressures.
    for a in pool.get('anchors',[]):
        if a not in elite:
            j=next(j for j in range(len(elite)-1,-1,-1) if elite[j] not in pool['anchors']);elite[j]=a
    return canonical(dict(pressure=pressure,elite=elite,nominees=[i.identity for _,i in ranked[:2]],parents=parents,
        best=ranked[0][1].identity,rank=ranked[0][0].fitness,rng_before=before,rng_after=rng.getstate(),
        fitness={i.identity:list(e.fitness) for e,i in ranked},reproduction_simulation_only=True))
