"""V6: identical V5 product reward; only initial goal-state stimulus varies.

Normal inference, source-removal probes and final scoring use the same input mode.
All oracle and graph computations are confined to fitness, outside inference.
"""
from dataclasses import dataclass
import numpy as np
from .beacon_runtime import Organism
from .beacon_probe import observe
from .evaluator import assess
from .regulatory_search import Evaluation
from .goal_fitness import GoalEvaluation,goal_metrics
from .signal_fitness import signal_metrics
from .factor_fitness import factor_bonus


def route_evaluate(individual, cases, topology, limits, goal_pulse):
    organism = Organism(individual.genome, topology, limits, goal_pulse=goal_pulse)
    assessed, reactions, rows = [], [], []
    for oracle in cases:
        m = oracle.maze
        r = organism.react(m.cells, m.w, m.h, m.start, m.goal)
        a = assess(r, oracle)
        assessed.append(a)
        reactions.append(r)
        rows.append(dict(case=m.case_id, status=r.status, steps=r.steps, valid=a.valid_path,
                         optimal=a.optimal, no_path=a.no_path_correct, partial=a.partial,
                         failure=a.failure, reads=r.range_reads, dispatches=r.dispatches,
                         active=r.active_instructions,
                         mask=np.packbits(r.mask, bitorder='little').tobytes().hex()))
    work = sum(r.dispatches + r.spatial_reads for r in reactions)
    complete = all(a.valid_path or a.no_path_correct for a in assessed)
    # Invalid phenotypes carry no cost/length tie-break: don't select immediate
    # program shrinkage instead of allowing neutral complexity to accumulate.
    fitness = (sum(a.valid_path for a in assessed), sum(a.optimal for a in assessed),
               sum(a.no_path_correct for a in assessed)
               - sum(a.reachable and r.status == 'no_path' for a, r in zip(assessed, reactions)),
               round(sum(a.partial for a in assessed), 8), -work if complete else 0)
    case_values = [(int(a.valid_path or a.no_path_correct),
                    int(a.optimal or a.no_path_correct), a.partial) for a in assessed]
    length_bin = min(3, (len(individual.genome.genes)-1)//32)
    density = tuple(min(7, int(float(np.mean(r.mask))*8)) for r in reactions)
    progress = tuple(min(7, int(a.partial*8)) for a in assessed)
    expression = min(3, int(4 * sum(r.active_instructions for r in reactions)
                            / max(1, sum(r.dispatches for r in reactions))))
    lifetime = min(3, max(r.steps for r in reactions)//16)
    descriptor = (density, progress, length_bin, expression, lifetime,
                  int(any(sum(r.range_reads[1:]) for r in reactions)))
    return Evaluation(fitness, case_values, descriptor, rows, work)


def goal_evaluate(individual,pairs,topology,limits,pressure,horizon=16,goal_pulse=False):
    if pressure not in ('transmission','goal'):raise ValueError('Unknown V4 objective')
    cases=[case for pair in pairs for case in pair.cases]
    if not cases:raise ValueError('Empty goal evaluation')
    base=route_evaluate(individual,cases,topology,limits,goal_pulse)
    organism=Organism(individual.genome,topology,limits,goal_pulse=goal_pulse)
    signals=[]; long=[]; families={}; goal_families={}; goals=[]; regular=[]; work=0
    for j,pair in enumerate(pairs):
        masks=[]; removed=[]; aligned=True
        for i,oracle in enumerate(pair.cases):
            m=oracle.maze
            a=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
            b=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,False)
            metrics=signal_metrics(a,b,oracle,horizon)
            masks.append((a.state[2]>0).astype(np.uint8))
            removed.append((b.state[2]>0).astype(np.uint8))
            aligned &= metrics['aligned']
            row=base.rows[2*j+i]; row['signal']=metrics
            row['probe_mask']=np.packbits(masks[-1],bitorder='little').tobytes().hex()
            row['source_removed_mask']=np.packbits(removed[-1],bitorder='little').tobytes().hex()
            signals.append(metrics['score'])
            if oracle.path:
                long.append(metrics['score']);families.setdefault(m.family,[]).append(metrics['score'])
            work+=a.dispatches+a.reads+b.dispatches+b.reads
            del a,b
        metrics=goal_metrics(masks,removed,pair)
        if not aligned:
            for r in metrics:r['score']=0.;r['pair_both']=False
        for i,(oracle,r) in enumerate(zip(pair.cases,metrics)):
            r['aligned']=bool(aligned)
            base.rows[2*j+i]['goal']=r
            goals.append(r)
            if oracle.path:goal_families.setdefault(oracle.maze.family,[]).append(r['score'])
        if not pair.mixed:regular.append(metrics[0]['pair_both'])
    fitness=list(base.fitness)
    fitness[3]=round(fitness[3]+sum(signals)+(2*sum(r['score'] for r in goals) if pressure=='goal' else 0.),8)
    values=[(v,o,p+s+(2*g['score'] if pressure=='goal' else 0.))
            for (v,o,p),s,g in zip(base.case_values,signals,goals)]
    mean=lambda vals:float(np.mean(vals)) if vals else 0.
    return GoalEvaluation(tuple(fitness),values,base.descriptor,base.rows,base.work+work,
        mean(signals),mean(long),{k:mean(v) for k,v in families.items()},base.work,work,
        mean([r['score'] for r in goals]),{k:mean(v) for k,v in goal_families.items()},
        mean([r['quality'] for r in goals]),mean([r['specificity'] for r in goals]),mean(regular))

@dataclass
class FactorEvaluation(GoalEvaluation):
    alpha: float
    normal_fitness: tuple


def evaluate(individual,pairs,topology,limits,pressure,horizon=16,generation=32):
    if pressure not in ('flag','pulse'):raise ValueError('Unknown V6 input mode')
    ev=goal_evaluate(individual,pairs,topology,limits,'transmission',horizon,pressure=='pulse')
    alpha=1.
    normal=(*ev.fitness[:3],round(sum(r['partial'] for r in ev.rows),8),ev.fitness[-1])
    bonuses=[];qualities=[];specificities=[]
    for row,oracle in zip(ev.rows,[o for p in pairs for o in p.cases]):
        bonus=factor_bonus(row['goal'],alpha,bool(oracle.path));bonuses.append(bonus)
        row['factor_bonus']=bonus
        eligible=bool(oracle.path) and row['goal']['aligned']
        qualities.append(row['goal']['quality'] if eligible else 0.)
        specificities.append(row['goal']['specificity'] if eligible else 0.)
    # Reconstruct once from the normal partial sum to avoid rounding an
    # intermediate partial+source value before applying the shaping term.
    fitness=list(normal);fitness[3]=round(normal[3]+sum(r['signal']['score'] for r in ev.rows)+sum(bonuses),8)
    ev.fitness=tuple(fitness)
    ev.case_values=[(a,b,c+bonus) for (a,b,c),bonus in zip(ev.case_values,bonuses)]
    ev.goal_quality=sum(qualities)/len(qualities);ev.goal_specificity=sum(specificities)/len(specificities)
    return FactorEvaluation(**ev.__dict__,alpha=alpha,normal_fitness=normal)
