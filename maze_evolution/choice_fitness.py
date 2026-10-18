"""V9: a separate strict paired-choice priority, with unchanged V8 shaping/VM."""
from dataclasses import dataclass
from .junction_fitness import JunctionEvaluation,evaluate as junction_evaluate


def priority_fitness(smooth,strict_pairs,pressure):
    if pressure not in ('prefix','choice') or len(smooth)!=5 or not isinstance(strict_pairs,int) or strict_pairs<0:
        raise ValueError('Invalid bounded choice priority')
    return tuple(smooth[:3])+(strict_pairs if pressure=='choice' else 0,)+tuple(smooth[3:])


def lexicase(rng,ranked,epsilon=.02):
    """Route validity, optimality, paired choice, then epsilon-smoothed shaping."""
    survivors=list(ranked);cases=list(range(len(survivors[0][0].case_values)));rng.shuffle(cases)
    for case in cases:
        for field in (0,1,2,3):
            best=max(ev.case_values[case][field] for ev,_ in survivors)
            tolerance=epsilon if field==3 else 0
            survivors=[(ev,item) for ev,item in survivors if ev.case_values[case][field]>=best-tolerance]
            if len(survivors)==1:return survivors[0][1]
    return rng.choice(survivors)[1]


@dataclass
class ChoiceEvaluation(JunctionEvaluation):
    strict_pairs: int
    selection_credit: int
    choice_families: dict
    smooth_fitness: tuple


def prioritize(ev,pairs,pressure):
    smooth=ev.fitness;families={};strict_pairs=0;credits=[]
    for j,pair in enumerate(pairs):
        rows=ev.rows[2*j:2*j+2];eligible=rows[0]['junction']['eligible']
        strict=int(eligible and all(r['junction']['strict'] for r in rows))
        if eligible:families.setdefault(pair.first.maze.family,[]).append(strict)
        strict_pairs+=strict
        credit=strict if pressure=='choice' else 0
        for row in rows:row['strict_pair_credit']=credit;credits.append(credit)
    ev.fitness=priority_fitness(smooth,strict_pairs,pressure)
    ev.case_values=[(a,b,credit,c) for (a,b,c),credit in zip(ev.case_values,credits)]
    return ChoiceEvaluation(**ev.__dict__,strict_pairs=strict_pairs,
        selection_credit=strict_pairs if pressure=='choice' else 0,
        choice_families={k:sum(v)/len(v) for k,v in families.items()},smooth_fitness=tuple(smooth))


def evaluate(individual,pairs,topology,limits,pressure,horizon=16):
    if pressure not in ('prefix','choice'):raise ValueError('Unknown V9 pressure')
    return prioritize(junction_evaluate(individual,pairs,topology,limits,'junction',horizon),pairs,pressure)
