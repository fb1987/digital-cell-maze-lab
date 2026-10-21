"""M1 prototype: eight bounded expression blocks, one writer per state channel.

Generic typed data only. A block has private, single-assignment scratch registers,
explicit input-channel ports and an output port fixed by block position. There is
no distance, path, parent-pointer or solver-specific instruction.
"""
from dataclasses import dataclass
import hashlib
import json
from .regulatory import Gene, SPECS, ALWAYS

OPS=tuple(op for op in SPECS if op!=13)
REFS={0:(2,),1:(),2:(2,3),3:(2,3),4:(),5:(),6:(),7:(),8:(2,3),
      9:(2,3),10:(2,3),11:(2,),12:(2,3,4),14:(),15:(),16:(2,3),17:()}

@dataclass(frozen=True)
class Genome:
    blocks: tuple
    ports: tuple

    def __post_init__(self):
        if len(self.blocks)!=8 or len(self.ports)!=8: raise ValueError('Eight output blocks required')
        if sum(map(len,self.blocks))+8>256: raise ValueError('Instruction cap includes eight output writes')
        for block,ports in zip(self.blocks,self.ports):
            if not 1<=len(block)<=31 or tuple(sorted(ports))!=tuple(range(8)): raise ValueError('Invalid block or input ports')
            for index,g in enumerate(block):
                if not isinstance(g,Gene) or g.op==13 or g.dst!=12+index or g.radius!=0: raise ValueError('Invalid expression node')
                row=g.row()
                if any(row[k]>=12+index for k in REFS[g.op]): raise ValueError('Forward/uninitialized reference')
                if g.gate!=ALWAYS and g.gate>=12+index: raise ValueError('Forward gate reference')

    def to_dict(self):return dict(version='M1',blocks=[[g.row() for g in b] for b in self.blocks],ports=[list(p) for p in self.ports])
    @classmethod
    def from_dict(cls,x):
        if set(x)!={'version','blocks','ports'} or x['version']!='M1':raise ValueError('Expected M1 schema')
        return cls(tuple(tuple(Gene(*g) for g in b) for b in x['blocks']),tuple(tuple(p) for p in x['ports']))
    @property
    def digest(self):return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()[:20]
    @property
    def instructions(self):return sum(map(len,self.blocks))+8


def random_node(rng,index):
    op=rng.choice(OPS);args=[rng.randint(lo,hi) for lo,hi in SPECS[op]]+[0]*4
    row=[op,12+index,*args[1:4],0,ALWAYS if rng.random()<.75 else rng.randrange(12+index)]
    for k in REFS[op]:row[k]=rng.randrange(12+index)
    if op==1:row[2]=rng.randrange(9) if rng.random()<.9 else rng.randrange(256)
    if op==7:row[3]=rng.randrange(9) if rng.random()<.9 else rng.randrange(256)
    return Gene(*row)


def random_genome(rng):
    total=rng.randint(64,128)-8
    lengths=[total//8+(i<total%8) for i in range(8)]
    return Genome(tuple(tuple(random_node(rng,i) for i in range(n)) for n in lengths),tuple(tuple(range(8)) for _ in range(8)))


def mutate(genome,rng):
    """One bounded variation opportunity. Concrete child is kept for replay."""
    blocks=[list(b) for b in genome.blocks];ports=[list(p) for p in genome.ports]
    m=rng.randrange(8);block=blocks[m];i=rng.randrange(len(block));mode=rng.randrange(7)
    event=dict(mode=mode,block=m,index=i,before=genome.digest)
    if mode==0: # replace one primitive, retaining safe input addressing
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
        a,b=rng.sample(range(8),2);ports[m][a],ports[m][b]=ports[m][b],ports[m][a]
        event.update(kind='ports',a=a,b=b)
    elif mode==5:
        donor=rng.choice([k for k in range(8) if k!=m])
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
