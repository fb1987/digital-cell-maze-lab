"""V12M immutable inherited range exposure, separate from all V3 lineages."""
from dataclasses import dataclass
import hashlib
from .growth import Genome as Program,mutate as mutate_program,replay_mutation as replay_program


@dataclass(frozen=True)
class Genome:
    program: Program
    exposure: int=7

    def __post_init__(self):
        if not isinstance(self.program,Program) or type(self.exposure) is not int or not 0<=self.exposure<=7:
            raise ValueError('Expected bounded V3 program and three-bit exposure')

    @property
    def genes(self):return self.program.genes
    @property
    def digest(self):
        return hashlib.sha256(b'V4-exposure\0'+bytes([self.exposure])+self.program.array().astype('<i4',copy=False).tobytes()).hexdigest()[:20]
    def to_dict(self):return dict(version=4,genes=[g.row() for g in self.genes],exposure=self.exposure)
    @classmethod
    def from_dict(cls,value):
        if set(value)!={'version','genes','exposure'} or type(value['version']) is not int or value['version']!=4:raise ValueError('Expected V4 exposure schema')
        return cls(Program.from_dict(dict(version=3,genes=value['genes'])),value['exposure'])


@dataclass(frozen=True)
class Individual:
    identity: str
    genome: Genome
    parent: str|None
    birth: int
    def save(self):return dict(id=self.identity,genome=self.genome.to_dict(),parent=self.parent,birth=self.birth)
    @classmethod
    def load(cls,value):return cls(value['id'],Genome.from_dict(value['genome']),value['parent'],value['birth'])


def mutate(genome,rng):
    """Exactly one opportunity: 1/5 bit flip, 4/5 old one-edit instruction mutation."""
    if rng.randrange(5)==0:
        bit=rng.randrange(3);after=genome.exposure^(1<<bit)
        return Genome(genome.program,after),dict(kind='exposure',bit=bit,before=genome.exposure,after=after)
    program,events=mutate_program(genome.program,rng,1,256,True)
    return Genome(program,genome.exposure),dict(kind='program',events=events,exposure=genome.exposure)


def replay(genome,event):
    if event['kind']=='exposure':
        assert event['before']==genome.exposure and type(event['bit']) is int and 0<=event['bit']<3
        assert event['after']==genome.exposure^(1<<event['bit'])
        return Genome(genome.program,event['after'])
    if event['kind']=='program':
        assert event['exposure']==genome.exposure and len(event['events'])==1
        return Genome(replay_program(genome.program,event['events'],256),genome.exposure)
    raise ValueError('Unknown exposure mutation')
