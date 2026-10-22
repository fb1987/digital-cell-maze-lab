"""M19 bounded variation in the unchanged M18 representation, no evaluator access."""
from .connected_genome import Genome,embed
from .spare_genome import Genome as Body,duplicate
from .modular_genome import random_genome as base_random,REFS,random_node
from .regulatory import Gene,ALWAYS,SPECS

ARMS=('generic','disconnected','connected')


def graph(g):
    reads=[]
    for k,block in enumerate(g.body.blocks):
        channels=set();seen=set();todo=[len(block)-1] if block else []
        while todo:
            n=todo.pop()
            if n in seen:continue
            seen.add(n);gene=block[n];row=gene.row()
            refs=[row[j] for j in REFS[gene.op]]+([gene.gate] if gene.gate!=ALWAYS else [])
            for r in refs:
                if r>=12:todo.append(r-12)
                elif r<8:channels.add(g.body.ports[k][r])
            if gene.op in (4,5,6,7,14,15,17):channels.add(g.body.ports[k][gene.a])
        reads.append(channels)
    return reads


def eligible(g):
    """Structural, prospective edges. Unread empty spare targets only.

    All active writers count when checking whether an empty slot is unread;
    readers are in the conservative output/halt cone. No favorable-edge list.
    """
    reads=graph(g);used=set().union(*reads);cone={2,7}
    while True:
        more=cone|{d for r in cone for d in reads[r]}
        if more==cone:break
        cone=more
    targets=[t for t in (8,9) if not g.body.blocks[t] and g.initialization[t]==0 and t not in used]
    return [(r,d,t) for r in sorted(cone) for d in sorted(reads[r]) if g.body.blocks[d]
            for t in targets if g.body.ports[r].index(t)>=8]


def copy(g,reader,donor,target,connected):
    assert (reader,donor,target) in eligible(g)
    body,event=duplicate(g.body,donor,target)
    if event['kind']=='bounded_noop':return g,dict(kind='bounded_noop',reader=reader,donor=donor,target=target,before=g.digest,after=g.digest)
    ports=list(body.ports)
    if connected:
        p=list(ports[reader]);a=p.index(donor);b=p.index(target)
        assert a<8 and b>=8
        p[a],p[b]=p[b],p[a];ports[reader]=tuple(p)
    tags=list(g.initialization);tags[target]=tags[donor]
    child=Genome(Body(body.blocks,tuple(ports)),tuple(tags))
    return child,dict(kind='initialized_connected_copy' if connected else 'initialized_disconnected_copy',
        reader=reader,donor=donor,target=target,before=g.digest,after=child.digest)


def random_genome(rng):return embed(base_random(rng))


def ordinary(genome,rng):
    """Common M17 grammar plus deletion of the last spare node and its seed.

    Original eight writers retain their one-node minimum. Last-node deletion
    makes spare-slot recycling possible under the existing two-spare capacity.
    """
    blocks=[list(b) for b in genome.body.blocks];ports=[list(p) for p in genome.body.ports]
    m=rng.randrange(10);block=blocks[m];i=rng.randrange(len(block)) if block else 0;mode=rng.randrange(7)
    event=dict(mode=mode,block=m,index=i,before=genome.digest)
    if not block:
        if genome.instructions+2<=256:block.append(random_node(rng,0));event['kind']='activate_node'
        else:event['kind']='bounded_noop'
    elif mode==0:block[i]=random_node(rng,i);event['kind']='replace'
    elif mode==1 and len(block)<31 and genome.instructions<256:
        for j in range(i,len(block)):
            row=block[j].row();row[1]+=1
            for k in REFS[row[0]]+(6,):
                if row[k]!=ALWAYS and row[k]>=12+i:row[k]+=1
            block[j]=Gene(*row)
        block.insert(i,random_node(rng,i));event['kind']='insert'
    elif mode==2 and (len(block)>1 or m>=8):
        block.pop(i)
        if not block:event['kind']='deactivate_spare'
        else:
            replacement=rng.randrange(12)
            for j in range(i,len(block)):
                row=block[j].row();row[1]-=1
                for k in REFS[row[0]]+(6,):
                    if row[k]==12+i:row[k]=replacement
                    elif row[k]!=ALWAYS and row[k]>12+i:row[k]-=1
                block[j]=Gene(*row)
            event.update(kind='delete',replacement=replacement)
    elif mode==3 and len(block)<31 and genome.instructions<256:
        row=block[i].row();row[1]=12+len(block);block.append(Gene(*row));event['kind']='duplicate_node'
    elif mode==4:
        a,b=rng.sample(range(10),2);ports[m][a],ports[m][b]=ports[m][b],ports[m][a];event.update(kind='ports',a=a,b=b)
    elif mode==5:
        donor=rng.choice([k for k in range(10) if k!=m and blocks[k]])
        if genome.instructions-len(block)+len(blocks[donor])<=256:
            blocks[m]=blocks[donor].copy();ports[m]=[m if p==donor else donor if p==m else p for p in ports[donor]]
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
    tags=tuple(t if blocks[k] else 0 for k,t in enumerate(genome.initialization))
    child=Genome(Body(tuple(tuple(b) for b in blocks),tuple(tuple(p) for p in ports)),tags)
    event['after']=child.digest;return child,event


def vary(g,rng,arm):
    assert arm in ARMS
    bucket=rng.randrange(4);choices=eligible(g) if bucket==0 and arm!='generic' else []
    if choices:
        reader,donor,target=rng.choice(choices);child,event=copy(g,reader,donor,target,arm=='connected')
    else:child,event=ordinary(g,rng)
    return child,dict(event,operator=arm,copy_bucket=bucket==0,eligible_copy_edges=len(choices),
        ordinary_fallback=bool(bucket==0 and arm!='generic' and not choices))
