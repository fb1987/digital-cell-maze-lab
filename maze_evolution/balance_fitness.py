"""V7 paired-goal pressure only; unchanged V6 pulse inference and probes."""
from dataclasses import dataclass
import numpy as np
from .beacon_fitness import evaluate as pulse_evaluate
from .factor_fitness import FactorEvaluation


def pair_bonuses(scores,pressure,regular=True):
    if pressure not in ('mean','balanced') or len(scores)!=2 or any(not 0<=s<=1 for s in scores):
        raise ValueError('Invalid bounded paired-goal reward')
    if pressure=='mean' or not regular:return tuple(2*s for s in scores)
    weaker=min(scores)
    return tuple(s+weaker for s in scores)


@dataclass
class BalanceEvaluation(FactorEvaluation):
    balanced_goal: float
    balanced_families: dict


def evaluate(individual,pairs,topology,limits,pressure,horizon=16):
    if pressure not in ('mean','balanced'):raise ValueError('Unknown V7 pressure')
    ev=pulse_evaluate(individual,pairs,topology,limits,'pulse',horizon)
    minima=[];families={};bonuses=[]
    for j,pair in enumerate(pairs):
        rows=ev.rows[2*j:2*j+2]
        regular=not pair.mixed and all(bool(o.path) for o in pair.cases)
        scores=[r['goal']['score'] for r in rows]
        pair_min=min(scores) if regular else None
        if regular:
            minima.append(pair_min);families.setdefault(pair.first.maze.family,[]).append(pair_min)
        pair_values=pair_bonuses(scores,pressure,regular)
        for row,bonus in zip(rows,pair_values):
            row['factor_bonus']=bonus;row['pair_min_goal']=pair_min;bonuses.append(bonus)
    if pressure=='balanced':
        fitness=list(ev.normal_fitness)
        fitness[3]=round(ev.normal_fitness[3]+sum(r['signal']['score'] for r in ev.rows)+sum(bonuses),8)
        ev.fitness=tuple(fitness)
        ev.case_values=[(a,b,(r['partial']+r['signal']['score'])+bonus)
            for (a,b,_),r,bonus in zip(ev.case_values,ev.rows,bonuses)]
    mean=lambda values:float(np.mean(values)) if values else 0.
    return BalanceEvaluation(**ev.__dict__,balanced_goal=mean(minima),
        balanced_families={k:mean(v) for k,v in families.items()})
