"""Bounded M5 writer regulation, with exact M1 bodies and neutral embedding."""
from dataclasses import dataclass
from .modular_genome import Genome as BaseGenome

@dataclass(frozen=True)
class Genome:
    base: BaseGenome
    write_gates: tuple = (64,)*8
    write_holds: tuple = (0,)*8

    def __post_init__(self):
        if not isinstance(self.base,BaseGenome):raise ValueError('Expected M1 body')
        if len(self.write_gates)!=8 or len(self.write_holds)!=8:raise ValueError('Eight bounded writers required')
        for k,(gate,hold) in enumerate(zip(self.write_gates,self.write_holds)):
            if type(gate)!=int or (gate!=64 and not 0<=gate<12+len(self.base.blocks[k])):raise ValueError('Invalid writer condition')
            if type(hold)!=int or hold not in (0,1):raise ValueError('Invalid writer fallback')

    def to_dict(self):
        return dict(version='M5',base=self.base.to_dict(),write_gates=list(self.write_gates),write_holds=list(self.write_holds))

    @classmethod
    def from_dict(cls,x):
        if set(x)!={'version','base','write_gates','write_holds'} or x['version']!='M5':raise ValueError('Expected M5 schema')
        return cls(BaseGenome.from_dict(x['base']),tuple(x['write_gates']),tuple(x['write_holds']))
