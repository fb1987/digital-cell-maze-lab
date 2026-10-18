"""V11 validation adapter; inference/probe kernels are the unchanged V6 kernels."""
from .growth import Genome
from .beacon_runtime import Organism as LegacyOrganism,warm_runtime
from .beacon_probe import observe
from .runtime import Limits


class Organism(LegacyOrganism):
    def __init__(self,genome,topology='local',limits=Limits(),ablate_nonlocal=False,goal_pulse=False,gene_limit=256):
        if not isinstance(genome,Genome) or gene_limit not in (128,256) or len(genome.genes)>gene_limit:
            raise ValueError('V11 gene capacity exceeded')
        super().__init__(genome,topology,limits,ablate_nonlocal,goal_pulse)
