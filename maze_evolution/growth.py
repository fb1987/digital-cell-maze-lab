"""V11 bounded heritable capacity. Identical V2 genes and instruction semantics."""
from dataclasses import dataclass
from .regulatory import Genome as LegacyGenome,Gene,SPECS,ALWAYS,REMOTE,REMOTE_MIN,random_gene
from .regulatory import random_genome as legacy_random_genome
from .regulatory_search import Individual as LegacyIndividual


@dataclass(frozen=True)
class Genome(LegacyGenome):
    def __post_init__(self):
        if not isinstance(self.genes,tuple) or not 1<=len(self.genes)<=256:
            raise ValueError('Expected1..256 immutable V3 genes')
        if any(not isinstance(g,Gene) for g in self.genes):raise ValueError('Expected validated V2 instruction types')

    def to_dict(self):return dict(version=3,genes=[g.row() for g in self.genes])

    @classmethod
    def from_dict(cls,value):
        if set(value)!={'version','genes'} or type(value['version']) is not int or value['version'] not in (2,3):raise ValueError('Expected V2/V3 schema')
        if value['version']==2:return cls(LegacyGenome.from_dict(value).genes)
        return cls(tuple(Gene(*row) for row in value['genes']))


class Individual(LegacyIndividual):
    @classmethod
    def load(cls,value):return cls(value['id'],Genome.from_dict(value['genome']),value['parent'],value['birth'])


def random_genome(rng,rich=True):
    # Same64..128 rich immigrants and RNG consumption in BOTH capacity arms.
    return Genome(legacy_random_genome(rng,rich).genes)


def mutate(genome,rng,edits=1,ceiling=128,return_events=False):
    if ceiling not in (128,256) or type(edits) is not int or not 1<=edits<=6 or len(genome.genes)>ceiling:
        raise ValueError('Invalid bounded V11 mutation')
    genes=list(genome.genes);events=[]
    for _ in range(edits):
        index=rng.randrange(len(genes));mode=rng.randrange(7);before=len(genes)
        event=dict(requested_mode=mode,index=index,before_length=before)
        if mode==0 and len(genes)<ceiling:
            gene=random_gene(rng);genes.insert(index,gene);event.update(kind='insert',row=gene.row())
        elif mode==1 and len(genes)>1:
            genes.pop(index);event.update(kind='delete')
        elif mode==2:
            gene=random_gene(rng);genes[index]=gene;event.update(kind='replace',row=gene.row())
        elif mode==3:
            other=rng.randrange(len(genes));genes[index],genes[other]=genes[other],genes[index];event.update(kind='swap',other=other)
        elif mode==4 and len(genes)<ceiling:
            block=genes[index:index+rng.randint(1,8)][:ceiling-len(genes)];genes[index:index]=block
            event.update(kind='duplicate',count=len(block))
        else:
            row=genes[index].row();options=list(range(1,1+len(SPECS[row[0]])))+[6]
            if row[0] in (REMOTE,REMOTE_MIN):options.append(5)
            field=rng.choice(options)
            if field==6:row[field]=ALWAYS if rng.random()<.5 else rng.randrange(64)
            elif field==5:row[field]=rng.randrange(4)
            else:
                low,high=SPECS[row[0]][field-1];row[field]=rng.randint(low,high)
            genes[index]=Gene(*row);event.update(kind='operand',field=field,row=row)
        event['after_length']=len(genes);events.append(event)
    result=Genome(tuple(genes))
    return (result,events) if return_events else result


def replay_mutation(genome,events,ceiling):
    """Replay concrete edits without RNG; source data never executes as code."""
    if ceiling not in (128,256) or not 1<=len(events)<=6:raise ValueError('Unbounded edit trace')
    genes=list(genome.genes)
    for event in events:
        assert len(genes)==event['before_length'];i=event['index'];assert 0<=i<len(genes)
        kind=event['kind']
        if kind=='insert':genes.insert(i,Gene(*event['row']))
        elif kind=='delete':genes.pop(i)
        elif kind in ('replace','operand'):genes[i]=Gene(*event['row'])
        elif kind=='swap':
            j=event['other'];assert 0<=j<len(genes);genes[i],genes[j]=genes[j],genes[i]
        elif kind=='duplicate':
            n=event['count'];assert 1<=n<=8 and i+n<=len(genes);genes[i:i]=genes[i:i+n]
        else:raise ValueError('Unknown edit trace')
        assert len(genes)==event['after_length'] and 1<=len(genes)<=ceiling
    return Genome(tuple(genes))
