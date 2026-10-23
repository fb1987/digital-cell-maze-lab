"""M29 diagnostic interpreter, NOT an evolved organism or combined solver.

Two inherited programs occupy separate ten-channel banks. Clocks, quiet/stop
latches and original work caps are independent. No output selector or oracle.
The total allowance can be twice the original and all work is charged.
Optional one-port cross-bank edges are diagnostic interventions only.
"""
import numpy as np
from numba import njit
from .connected_genome import Genome
from .connected_runtime import Organism
from .beacon_runtime import _neighbor
from .runtime import STATUSES
from .exposure_runtime import ExposureReaction


@njit(cache=True)
def expression(cells,w,p,start,goal,state,program,lo,hi,ports,registers,reads,dispatches,active,read_cap,dispatch_cap):
    n=len(cells)
    for r in range(64):registers[r]=0
    for r in range(8):registers[r]=state[ports[r],p]
    registers[8]=1;registers[9]=int(p==start);registers[10]=int(p==goal);registers[11]=1
    for i in range(lo,hi):
        if dispatches>=dispatch_cap:return 0,reads,dispatches,active,5
        dispatches+=1
        op,dst,a,b,c,radius,gate=program[i]
        if gate!=64 and registers[gate]==0:continue
        cost=4 if op in (4,5,15,17) else 1 if op in (6,7,14) else 0
        if reads+cost>read_cap:return 0,reads,dispatches,active,4
        reads+=cost;active+=1
        if op==0:registers[dst]=registers[a]
        elif op==1:registers[dst]=a
        elif op==2:registers[dst]=min(65535,registers[a]+registers[b])
        elif op==3:registers[dst]=max(0,registers[a]-registers[b])
        elif op in (4,5,15,17):
            best=65536;chosen=0;count=0
            for direction in range(4):
                q=_neighbor(p,direction,1,w,n)
                value=int(state[ports[a],q]) if q>=0 and cells[q] else 0
                count+=int(value>0)
                if value>0 and value<best:best=value;chosen=direction+1
            registers[dst]=count if op==17 else chosen if op==5 else best if chosen else 0
        elif op in (6,7,14):
            q=_neighbor(p,c if op==7 else b,1,w,n)
            value=int(state[ports[a],q]) if q>=0 and cells[q] else 0
            registers[dst]=int(value==b) if op==7 else value
        elif op==8:registers[dst]=int(registers[a]==registers[b])
        elif op==9:registers[dst]=int(registers[a]!=0 and registers[b]!=0)
        elif op==10:registers[dst]=int(registers[a]!=0 or registers[b]!=0)
        elif op==11:registers[dst]=int(registers[a]==0)
        elif op==12:registers[dst]=registers[b] if registers[a] else registers[c]
        elif op==16:registers[dst]=int((registers[a]!=0)!=(registers[b]!=0))
    if dispatches>=dispatch_cap:return 0,reads,dispatches,active,5
    dispatches+=1;active+=1
    return registers[11+hi-lo],reads,dispatches,active,-1


@njit(cache=True)
def bank_kernel(cells,w,start,goal,program,offsets,ports,initialization,max_steps,read_cap,dispatch_cap):
    n=len(cells);old=np.zeros((20,n),np.uint16);new=np.zeros((20,n),np.uint16)
    registers=np.zeros(64,np.int32);history=np.zeros((max_steps+1,20,n),np.uint16)
    steps=np.zeros(2,np.int64);reads=np.zeros(2,np.int64);dispatches=np.zeros(2,np.int64)
    active=np.zeros(2,np.int64);quiet=np.zeros(2,np.int64);reasons=np.full(2,3,np.int64);done=np.zeros(2,np.uint8)
    completed=np.zeros(2,np.uint8);ticks=0
    if not cells[start] or not cells[goal]:
        reasons[:]=2;return old,steps,reads,dispatches,active,reasons,history,ticks
    for channel in range(20):
        if initialization[channel]&1:old[channel,start]=1
        if initialization[channel]&2:old[channel,goal]=1
    history[0]=old
    for tick in range(max_steps):
        new[:]=old;completed[:]=0
        # Both banks read the SAME pre-tick snapshot, including cross-bank edges.
        for bank in range(2):
            if done[bank]:continue
            interrupted=False;changed=False;base=10*bank
            for p in range(n):
                if not cells[p]:continue
                for module in range(base,base+10):
                    if offsets[module]==offsets[module+1]:continue
                    value,rr,dd,aa,reason=expression(cells,w,p,start,goal,old,program,offsets[module],offsets[module+1],ports[module],registers,
                        reads[bank],dispatches[bank],active[bank],read_cap,dispatch_cap)
                    reads[bank]=rr;dispatches[bank]=dd;active[bank]=aa
                    if reason!=-1:
                        reasons[bank]=reason;done[bank]=1;interrupted=True;break
                    new[module,p]=value
                if interrupted:break
                for channel in range(base,base+10):changed|=new[channel,p]!=old[channel,p]
            if interrupted:continue # incomplete bank tick is discarded, like M18
            completed[bank]=1;steps[bank]+=1;quiet[bank]=0 if changed else quiet[bank]+1
            if new[base+7,start]>0 and new[base+2,start]>0 and new[base+2,goal]>0:
                reasons[bank]=0;done[bank]=1
            elif quiet[bank]>=4:
                reasons[bank]=0 if new[base+2,start]>0 and new[base+2,goal]>0 else 2
                if reasons[bank]!=0:
                    for p in range(n):
                        if new[base+2,p]>0:reasons[bank]=1;break
                done[bank]=1
        for bank in range(2):
            if completed[bank]:old[bank*10:bank*10+10]=new[bank*10:bank*10+10]
        ticks=tick+1;history[ticks]=old
        if done[0] and done[1]:break
    return old,steps,reads,dispatches,active,reasons,history,ticks


def compile_pair(a,b,edge=None):
    ga,gb=(Genome.from_dict(m['genome']) for m in (a,b));assert ga.instructions+gb.instructions<=256
    orgs=[Organism(ga),Organism(gb)]
    program=np.concatenate([o.program for o in orgs]);offsets=np.concatenate([orgs[0].offsets,orgs[1].offsets[1:]+len(orgs[0].program)]).astype(np.int32)
    ports=np.concatenate([orgs[0].ports,orgs[1].ports+10]);init=np.concatenate([o.initialization for o in orgs])
    if edge is not None:
        bank,reader,position=edge;assert bank in (0,1) and 0<=reader<10 and 0<=position<8
        channel=int(ports[bank*10+reader,position])%10
        ports[bank*10+reader,position]=(1-bank)*10+channel
    for x in (program,offsets,ports,init):x.flags.writeable=False
    return program,offsets,ports,init


def respond_pair(a,b,maze,edge=None,limits=None):
    from .runtime import Limits
    limits=limits or Limits(256,4096,32768)
    assert maze.w*maze.h<=1024 and limits.max_steps<=256
    program,offsets,ports,init=compile_pair(a,b,edge)
    grid=np.frombuffer(maze.cells,np.uint8)
    old,steps,reads,dispatches,active,reasons,h,ticks=bank_kernel(grid,maze.w,maze.start,maze.goal,program,offsets,ports,init,
        limits.max_steps,len(grid)*limits.reads_per_site,len(grid)*limits.instructions_per_site)
    reactions=[]
    for bank in range(2):
        # Each internal response retains its legacy metadata for exact comparison;
        # actual pair allocation is reported separately and is NEVER free.
        org=Organism(Genome.from_dict((a,b)[bank]['genome']))
        memory=42*len(grid)+256+org.program.nbytes+org.offsets.nbytes+org.ports.nbytes+org.initialization.nbytes
        reactions.append(ExposureReaction((old[bank*10+2]>0).astype(np.uint8),STATUSES[reasons[bank]],int(steps[bank]),int(reads[bank]),int(dispatches[bank]),memory,
            int(dispatches[bank]),int(active[bank]),(int(reads[bank]),0,0,0),0,0))
    # Explicit modeled array allocation excluding trace, and actual trace allocation.
    allocation=83*len(grid)+256+6*2*8+2*2+program.nbytes+offsets.nbytes+ports.nbytes+init.nbytes
    return reactions,h[:ticks+1].copy(),dict(state_channels=20,program_instructions=ga_instructions(a)+ga_instructions(b),
        array_bytes_excluding_history=allocation,trace_allocation_bytes=h.nbytes,global_ticks=ticks,
        counted_work=int(sum(reads)+sum(dispatches)),internal_responses_not_a_combined_path=True)


def ga_instructions(model):return Genome.from_dict(model['genome']).instructions


@njit(cache=True)
def writer_kernel(cells,w,start,goal,state,program,lo,hi,ports):
    out=np.zeros(len(cells),np.uint16);registers=np.zeros(64,np.int32);rr=dd=aa=0
    for p in range(len(cells)):
        if not cells[p]:continue
        value,rr,dd,aa,reason=expression(cells,w,p,start,goal,state,program,lo,hi,ports,registers,rr,dd,aa,10**15,10**15)
        out[p]=value
    return out,rr,dd


def writer(model,maze,state,channel):
    org=Organism(Genome.from_dict(model['genome']));assert state.shape==(10,len(maze.cells))
    if org.offsets[channel]==org.offsets[channel+1]:return state[channel].copy(),0,0
    return writer_kernel(np.frombuffer(maze.cells,np.uint8),maze.w,maze.start,maze.goal,state,org.program,
                         org.offsets[channel],org.offsets[channel+1],org.ports[channel])
