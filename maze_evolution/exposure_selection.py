"""V12M common ranking and explicitly simulated reproduction; no generation loop."""
from collections import defaultdict
import random
from .foundation_pair_confirm import normal_row
from .exposure_genome import Individual
from .exposure_runtime import Organism,ARMS
from .foundation_calibration import LIMITS
from .regulatory_search import Evaluation
from .foundation_fitness import lexicase
from .routing_transfer import canonical


def record(r,o):
    row=canonical(normal_row(r,o));row.update(exposure_checks=r.exposure_checks,suppressed_reads=r.suppressed_reads)
    return row


def physical(item,arm,topology):
    top='local' if arm=='local' else topology
    mask=(item.genome.exposure if arm=='active' else 0 if arm=='zero' else 7) if top!='local' else 7
    key=f'{top}/{item.genome.program.digest}/{mask}'
    return key,dict(genome=dict(version=4,genes=[g.row() for g in item.genome.genes],exposure=mask),topology=top)


def organism(model):
    from .exposure_genome import Genome
    return Organism(Genome.from_dict(model['genome']),'active',model['topology'],LIMITS,True)


def evaluate(rows,meta,shaping=True):
    pairs=defaultdict(list)
    for row in rows:
        m=meta[row['case']]
        if m['family'] in ('paired','fork','two_junction','cycle'):pairs[m['base'],m['family'],m['pose']].append(row)
    pair_success={};weak={}
    for rs in pairs.values():
        assert len(rs)==2
        for r in rs:pair_success[r['case']]=all(x['optimal'] for x in rs);weak[r['case']]=min(x['partial'] for x in rs)
    partial=sum(r['partial']+weak.get(r['case'],0.) for r in rows) if shaping else 0.
    fitness=(sum(pair_success.values())//2,sum(r['optimal'] for r in rows),sum(r['valid'] for r in rows),
        sum(r['no_path'] for r in rows)-sum(r['reachable'] and r['status']=='no_path' for r in rows),round(partial,8))
    values=[(int(pair_success.get(r['case'],False)),int(r['optimal'] or r['no_path']),int(r['valid'] or r['no_path']),
             r['partial']+weak.get(r['case'],0.) if shaping else 0.) for r in rows]
    work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows)
    return Evaluation(fitness,values,(),rows,work)


def choose(pool,rows,meta,seed,shaping=True):
    items=[Individual.load(i) for i in pool['items']]
    ranked=sorted(((evaluate(rows[i.identity],meta,shaping),i) for i in items),key=lambda x:(tuple(-v for v in x[0].fitness),x[1].genome.digest,x[1].identity))
    rng=random.Random(seed);before=rng.getstate();parents=[lexicase(rng,ranked).identity for _ in range(64)]
    elite=[i.identity for _,i in ranked[:max(1,len(items)//4)]];nominees=[i.identity for _,i in ranked[:2]]
    return canonical(dict(best=ranked[0][1].identity,rank=list(ranked[0][0].fitness),elite=elite,nominees=nominees,parents=parents,
        rng_before=before,rng_after=rng.getstate(),fitness={i.identity:list(ev.fitness) for ev,i in ranked},
        shaping=shaping,reproduction_simulation_only=True))


def stats(rows,meta):
    ev=evaluate(rows,meta);pairs=defaultdict(list);groups=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family'] in ('paired','fork','two_junction','cycle'):pairs[m['base'],m['family'],m['pose']].append(r)
    good={k for k,rs in pairs.items() if all(r['optimal'] for r in rs)}
    for k in pairs:groups[k[:2]].append(k in good)
    return dict(rank=list(ev.fitness),pairs=len(good),pair_opportunities=len(pairs),pair_keys=[list(k) for k in sorted(good)],
        full_groups=sum(all(v) for v in groups.values()),any_templates=len({meta[rs[0]['case']]['template'] for k,rs in pairs.items() if k in good}),
        optimal=sum(r['optimal'] for r in rows),valid=sum(r['valid'] for r in rows),no_path=sum(r['no_path'] for r in rows),
        false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),
        corridors=sum(r['optimal'] for r in rows if meta[r['case']]['family'].startswith('corridor')),
        work=ev.work,exposure_checks=sum(r['exposure_checks'] for r in rows),suppressed_reads=sum(r['suppressed_reads'] for r in rows),
        by_family={f:sum(k[1]==f for k in good) for f in ('paired','fork','two_junction','cycle')})
