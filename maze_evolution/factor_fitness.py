"""V5 reward decomposition only; candidates use the unchanged V2 runtime."""
from dataclasses import dataclass
from .goal_fitness import GoalEvaluation,evaluate as goal_evaluate


def curriculum_alpha(pressure,generation):
    if pressure not in ('product','curriculum'):raise ValueError('Unknown V5 pressure')
    if pressure=='product':return 1.
    if generation<0:raise ValueError('A curriculum generation is required')
    return max(0.,min(1.,(generation-15)/16))


def factor_bonus(goal,alpha,reachable=True):
    if not 0<=alpha<=1:raise ValueError('Unbounded curriculum blend')
    if not reachable or not goal['aligned']:return 0.
    return (1-alpha)*(goal['quality']+goal['specificity'])+alpha*2*goal['score']


@dataclass
class FactorEvaluation(GoalEvaluation):
    alpha: float
    normal_fitness: tuple


def evaluate(individual,pairs,topology,limits,pressure,horizon=16,generation=32):
    ev=goal_evaluate(individual,pairs,topology,limits,'transmission',horizon)
    alpha=curriculum_alpha(pressure,generation)
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
