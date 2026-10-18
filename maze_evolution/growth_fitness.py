"""V11 changes capacity only; hard-pair V9 Choice fitness is unchanged."""
from .choice_fitness import evaluate as choice_evaluate,lexicase
from .junction_fitness import decision
from .growth import Genome


def evaluate(individual,pairs,topology,limits,pressure='choice',horizon=16,gene_limit=256):
    if pressure not in ('choice','cap128','cap256'):raise ValueError('Unknown V11 arm')
    if pressure!='choice':gene_limit=int(pressure[3:])
    if gene_limit not in (128,256) or not isinstance(individual.genome,Genome) or len(individual.genome.genes)>gene_limit:
        raise ValueError('V11 capacity bound violated')
    for pair in pairs:pair.first._junction_label=decision(pair)
    return choice_evaluate(individual,pairs,topology,limits,'choice',horizon)
