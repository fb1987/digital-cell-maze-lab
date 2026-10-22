"""M17 bounded extra-state representation. No solver-specific primitive."""
from dataclasses import dataclass
import json,hashlib
from .regulatory import Gene,ALWAYS,SPECS
from .modular_genome import Genome as BaseGenome,REFS,random_node

@dataclass(frozen=True)
class Genome:
    blocks: tuple
    ports: tuple
    def __post_init__(self):
        if len(self.blocks)!=10 or len(self.ports)!=10:raise ValueError('Ten channel slots required')
        if self.instructions>256:raise ValueError('256 total instructions including active writes')
        for k,(block,ports) in enumerate(zip(self.blocks,self.ports)):
            if not (int(k<8)<=len(block)<=31) or tuple(sorted(ports))!=tuple(range(10)):raise ValueError('Invalid block/ports')
            for i,g in enumerate(block):
                if not isinstance(g,Gene) or g.op not in REFS or g.dst!=12+i or g.radius!=0:raise ValueError('Invalid node')
                if any(g.row()[j]>=12+i for j in REFS[g.op]) or (g.gate!=ALWAYS and g.gate>=12+i):raise ValueError('Forward reference')
    @property
    def instructions(self):return sum(len(b)+bool(b) for b in self.blocks)
    def to_dict(self):return dict(version='M17',blocks=[[g.row() for g in b] for b in self.blocks],ports=[list(p) for p in self.ports])
    @classmethod
    def from_dict(cls,x):
        if set(x)!={'version','blocks','ports'} or x['version']!='M17':raise ValueError('Expected M17 schema')
        return cls(tuple(tuple(Gene(*g) for g in b) for b in x['blocks']),tuple(tuple(p) for p in x['ports']))
    @property
    def digest(self):return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()[:20]

def embed(g):
    return Genome(g.blocks+((),()),tuple(p+(8,9) for p in g.ports)+(tuple(range(10)),)*2)

def duplicate(g,donor,target):
    """Generic copy with donor/target state-role exchange, as in M1 copy_block."""
    assert donor!=target and g.blocks[donor]
    blocks=list(g.blocks);ports=list(g.ports)
    blocks[target]=g.blocks[donor]
    ports[target]=tuple(target if p==donor else donor if p==target else p for p in g.ports[donor])
    cls=type(g)
    count=sum(len(b)+bool(b) for b in blocks)
    if count>256:return g,dict(kind='bounded_noop',donor=donor,target=target,before=g.digest,after=g.digest)
    child=cls(tuple(blocks),tuple(ports))
    return child,dict(kind='generic_copy',donor=donor,target=target,before=g.digest,after=child.digest)

def mutate(genome,rng):
    """One bounded variation opportunity. Concrete child is kept for replay."""
    blocks=[list(b) for b in genome.blocks];ports=[list(p) for p in genome.ports]
    m=rng.randrange(10);block=blocks[m];i=rng.randrange(len(block)) if block else 0;mode=rng.randrange(7)
    event=dict(mode=mode,block=m,index=i,before=genome.digest)
    if not block:
        if genome.instructions+2<=256:
            block.append(random_node(rng,0));event['kind']='activate_node'
        else:event['kind']='bounded_noop'
    elif mode==0: # replace one primitive, retaining safe input addressing
        block[i]=random_node(rng,i);event['kind']='replace'
    elif mode==1 and len(block)<31 and genome.instructions<256:
        # Insert an independent node and preserve existing references by renumbering.
        for j in range(i,len(block)):
            row=block[j].row();row[1]+=1
            for k in REFS[row[0]]+(6,):
                if row[k]!=ALWAYS and row[k]>=12+i:row[k]+=1
            block[j]=Gene(*row)
        block.insert(i,random_node(rng,i));event['kind']='insert'
    elif mode==2 and len(block)>1:
        block.pop(i);replacement=rng.randrange(12)
        for j in range(i,len(block)):
            row=block[j].row();row[1]-=1
            for k in REFS[row[0]]+(6,):
                if row[k]==12+i:row[k]=replacement
                elif row[k]!=ALWAYS and row[k]>12+i:row[k]-=1
            block[j]=Gene(*row)
        event.update(kind='delete',replacement=replacement)
    elif mode==3 and len(block)<31 and genome.instructions<256:
        # Copy a computation to a fresh private node; references remain backward.
        row=block[i].row();row[1]=12+len(block);block.append(Gene(*row));event['kind']='duplicate_node'
    elif mode==4:
        a,b=rng.sample(range(10),2);ports[m][a],ports[m][b]=ports[m][b],ports[m][a]
        event.update(kind='ports',a=a,b=b)
    elif mode==5:
        donor=rng.choice([k for k in range(10) if k!=m and blocks[k]])
        if genome.instructions-len(block)+len(blocks[donor])<=256:
            blocks[m]=blocks[donor].copy();ports[m]=ports[donor].copy()
            # Generic rebinding: exchange source/destination channel roles in copied inputs.
            ports[m]=[m if p==donor else donor if p==m else p for p in ports[m]]
            event.update(kind='copy_block',donor=donor)
        else:event['kind']='bounded_noop'
    else:
        row=block[i].row();fields=list(REFS[row[0]])+[6]
        if row[0] in (1,4,5,6,7,14,15,17):fields += [2]
        if row[0] in (6,14):fields += [3]
        if row[0]==7:fields += [3,4]
        k=rng.choice(fields)
        if k==6:row[k]=ALWAYS if rng.random()<.5 else rng.randrange(12+i)
        elif k in REFS[row[0]]:row[k]=rng.randrange(12+i)
        else:
            lo,hi=SPECS[row[0]][k-1];row[k]=rng.randint(lo,hi)
        block[i]=Gene(*row);event.update(kind='operand',field=k)
    child=Genome(tuple(tuple(b) for b in blocks),tuple(tuple(p) for p in ports))
    event['after']=child.digest
    return child,event
