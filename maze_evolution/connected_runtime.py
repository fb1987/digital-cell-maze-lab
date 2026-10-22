"""M18 inherited generic source/goal initialization; bounded ten-channel VM. No oracle or evaluator imports."""
import numpy as np
from numba import njit
from .runtime import Limits,STATUSES
from .exposure_runtime import ExposureReaction
from .beacon_runtime import _neighbor
from .connected_genome import Genome

@njit(cache=True)
def kernel(cells,w,start,goal,program,offsets,ports,initialization,max_steps,read_cap,dispatch_cap):
    n=len(cells);old=np.zeros((10,n),np.uint16);new=np.zeros((10,n),np.uint16)
    registers=np.zeros(64,np.int32);out=np.zeros(n,np.uint8)
    if not cells[start] or not cells[goal]:return out,0,0,0,0,2
    for channel in range(10):
        if initialization[channel]&1:old[channel,start]=1
        if initialization[channel]&2:old[channel,goal]=1
    reads=dispatches=active=quiet=steps=0;reason=3
    for tick in range(max_steps):
        interrupted=False;changed=False
        for p in range(n):
            if not cells[p]:continue
            for channel in range(10):new[channel,p]=old[channel,p]
            for module in range(10):
                if offsets[module]==offsets[module+1]:continue
                for r in range(64):registers[r]=0
                for r in range(8):registers[r]=old[ports[module,r],p]
                registers[8]=1;registers[9]=int(p==start);registers[10]=int(p==goal);registers[11]=1
                for i in range(offsets[module],offsets[module+1]):
                    if dispatches>=dispatch_cap:reason=5;interrupted=True;break
                    dispatches+=1
                    op,dst,a,b,c,radius,gate=program[i]
                    if gate!=64 and registers[gate]==0:continue
                    cost=4 if op in (4,5,15,17) else 1 if op in (6,7,14) else 0
                    if reads+cost>read_cap:reason=4;interrupted=True;break
                    reads+=cost;active+=1
                    if op==0:registers[dst]=registers[a]
                    elif op==1:registers[dst]=a
                    elif op==2:registers[dst]=min(65535,registers[a]+registers[b])
                    elif op==3:registers[dst]=max(0,registers[a]-registers[b])
                    elif op in (4,5,15,17):
                        best=65536;chosen=0;count=0
                        for direction in range(4):
                            q=_neighbor(p,direction,1,w,n)
                            value=int(old[ports[module,a],q]) if q>=0 and cells[q] else 0
                            count+=int(value>0)
                            if value>0 and value<best:best=value;chosen=direction+1
                        registers[dst]=count if op==17 else chosen if op==5 else best if chosen else 0
                    elif op in (6,7,14):
                        q=_neighbor(p,c if op==7 else b,1,w,n)
                        value=int(old[ports[module,a],q]) if q>=0 and cells[q] else 0
                        registers[dst]=int(value==b) if op==7 else value
                    elif op==8:registers[dst]=int(registers[a]==registers[b])
                    elif op==9:registers[dst]=int(registers[a]!=0 and registers[b]!=0)
                    elif op==10:registers[dst]=int(registers[a]!=0 or registers[b]!=0)
                    elif op==11:registers[dst]=int(registers[a]==0)
                    elif op==12:registers[dst]=registers[b] if registers[a] else registers[c]
                    elif op==16:registers[dst]=int((registers[a]!=0)!=(registers[b]!=0))
                if interrupted:break
                if dispatches>=dispatch_cap:reason=5;interrupted=True;break
                dispatches+=1;active+=1 # explicit output-port write charged as an instruction
                last=12+offsets[module+1]-offsets[module]-1
                new[module,p]=registers[last]
            if interrupted:break
            for channel in range(10):changed|=new[channel,p]!=old[channel,p]
        if interrupted:break
        old,new=new,old;steps+=1
        if old[7,start]>0 and old[2,start]>0 and old[2,goal]>0:reason=0;break
        quiet=0 if changed else quiet+1
        if quiet>=4:
            reason=0 if old[2,start]>0 and old[2,goal]>0 else 2
            if reason!=0:
                for p in range(n):
                    if old[2,p]>0:reason=1;break
            break
    for p in range(n):out[p]=int(old[2,p]>0)
    return out,steps,reads,dispatches,active,reason

class Organism:
    def __init__(self,genome,limits=Limits(256,4096,32768)):
        if not isinstance(genome,Genome):raise ValueError('Expected M18 genome')
        self.genome=genome;self.limits=limits;genome=genome.body
        self.initialization=np.array(self.genome.initialization,np.uint8)
        self.program=np.array([g.row() for b in genome.blocks for g in b],np.int32)
        self.offsets=np.array([0]+list(np.cumsum([len(b) for b in genome.blocks])),np.int32)
        self.ports=np.array(genome.ports,np.int32)
        for a in (self.program,self.offsets,self.ports,self.initialization):a.flags.writeable=False
    def react(self,cells,w,h,start,goal):
        if type(cells) is not bytes or type(w) is not int or type(h) is not int or w<1 or h<1 or len(cells)!=w*h or w*h>self.limits.max_cells or not 0<=start<len(cells) or not 0<=goal<len(cells):raise ValueError('Invalid maze')
        grid=np.frombuffer(cells,np.uint8)
        if np.any(grid>1):raise ValueError('Nonbinary maze')
        out,steps,reads,dispatches,active,reason=kernel(grid,w,start,goal,self.program,self.offsets,self.ports,self.initialization,self.limits.max_steps,len(cells)*self.limits.reads_per_site,len(cells)*self.limits.instructions_per_site)
        memory=42*len(cells)+256+self.program.nbytes+self.offsets.nbytes+self.ports.nbytes+self.initialization.nbytes
        assert memory<=64*len(cells)+65536
        return ExposureReaction(out,STATUSES[reason],steps,reads,dispatches,memory,dispatches,active,(reads,0,0,0),0,0)
