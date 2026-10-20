"""V12X generic scratch/output linkage and bounded homologous segment exchange.

Homology uses inherited gene identities, never equal-looking instructions alone.
No maze, oracle, fitness, instruction rewriting or executable code enters here.
"""
from functools import lru_cache
from .composition_operator import register_reads,rows
from .growth import Genome as Program
from .regulatory import Gene

LENGTHS=(2,4,8,16)

def mutate_ids(ids,events,child):
    ids=list(ids)
    for k,e in enumerate(events):
        j=e['index'];kind=e['kind']
        if kind=='insert':ids.insert(j,f'{child}/edit{k}/new0')
        elif kind=='delete':del ids[j]
        elif kind=='swap':ids[j],ids[e['other']]=ids[e['other']],ids[j]
        elif kind=='duplicate':ids[j:j]=[f'{child}/edit{k}/copy{x}' for x in range(e['count'])]
        else:assert kind in ('replace','operand')
        assert len(ids)==e['after_length'] and len(set(ids))==len(ids)
    return ids

@lru_cache(maxsize=2048)
def dependencies(program):
    """Possible reaching definitions; conditional writes do not kill predecessors.

Backward transitive closure from STORE value/gate reads retains dependencies
of the defining instructions as well. Initial registers have no gene provider.
"""
    definitions={r:set() for r in range(64)};parents={};stores=[]
    for i,row in enumerate(program):
        ps=set().union(*(definitions[r] for r in register_reads(row)))
        parents[i]=ps
        if row[0]==13:stores.append(i)
        elif row[6]==64:definitions[row[1]]={i}
        else:definitions[row[1]].add(i)
    groups=[]
    for store in stores:
        todo=[store];seen=set()
        while todo:
            i=todo.pop()
            if i in seen:continue
            seen.add(i);todo.extend(parents[i])
        groups.append(tuple(sorted(seen)))
    return tuple(groups)

@lru_cache(maxsize=512)
def candidates(a,b,aid,bid):
    """Common bounded pool, same-length intervals between inherited anchors.

All shared loci must have consistent order; inversions are ineligible. Exact
scratch-write/store interfaces are intentionally NOT required in either arm.
"""
    assert len(a)==len(aid) and len(b)==len(bid) and len(set(aid))==len(aid) and len(set(bid))==len(bid)
    bp={x:i for i,x in enumerate(bid)};common=[(i,bp[x]) for i,x in enumerate(aid) if x in bp]
    if len(common)<2 or [j for _,j in common]!=sorted(j for _,j in common):return ()
    mapping=dict(common);out=[]
    groups=[{aid[i] for i in g} for g in dependencies(a)]+[{bid[i] for i in g} for g in dependencies(b)]
    # Union parent groups on aligned identities. Testing every group also enforces
    # their transitive closure: a shared group member cannot be cut in either parent.
    for left,dl in common:
        x,u=left+1,dl+1
        for length in LENGTHS:
            y=x+length;v=u+length
            if y not in mapping or mapping[y]!=v:continue
            changed=sum(ar!=br for ar,br in zip(a[x:y],b[u:v]))
            if not changed:continue
            child_ids=aid[:x]+bid[u:v]+aid[y:]
            if len(set(child_ids))!=len(child_ids):continue
            segment=set(aid[x:y])|set(bid[u:v])
            linked=all(not (g&segment) or g<=segment for g in groups)
            out.append((x,y,u,v,changed,linked))
    return tuple(out)

def transfer(parent,donor,aid,bid,rng,policy):
    a,b=rows(parent),rows(donor);opts=candidates(a,b,tuple(aid),tuple(bid))
    assert opts and policy in ('linked','unlinked','sham')
    lengths=sorted({y-x for x,y,u,v,changed,ok in opts});length=rng.choice(lengths)
    common=[v for v in opts if v[1]-v[0]==length];allowed=[v for v in common if v[5]]
    # Common random ordering is consumed in ALL arms, including rejection/fallback.
    order=list(range(len(common)));rng.shuffle(order);ticket=rng.random()
    pool=allowed if policy=='linked' else common if policy=='unlinked' else [common[i] for i in order[:len(allowed)]]
    event=dict(policy=policy,length=length,common=len(common),linked=len(allowed),
        candidate_lengths={str(k):sum(v[1]-v[0]==k for v in opts) for k in lengths},
        accepted=False,reason='no_closed_segment_at_proposed_length',changed_instructions=0)
    if not pool:return parent,list(aid),event
    x,y,u,v,changed,closed=pool[min(int(ticket*len(pool)),len(pool)-1)]
    result=Program(tuple(Gene(*r) for r in a[:x]+b[u:v]+a[y:]));ids=list(aid[:x])+list(bid[u:v])+list(aid[y:])
    assert 1<=len(result.genes)<=256 and result.digest!=parent.digest
    event.update(accepted=True,reason='accepted',recipient_interval=[x,y],donor_interval=[u,v],
        recipient_rows=[list(r) for r in a[x:y]],donor_rows=[list(r) for r in b[u:v]],
        donor_ids=list(bid[u:v]),changed_instructions=changed,dependency_closed=closed,child_digest=result.digest)
    return result,ids,event

def retained_changes(parent,parent_ids,donor,donor_ids,event,child,child_ids):
    if not event or not event['accepted']:return 0
    if child.digest==parent.digest:return 0
    new=dict(zip(child_ids,rows(child)));x,y=event['recipient_interval'];u,v=event['donor_interval'];count=0
    for old,row,identity in zip(rows(parent)[x:y],rows(donor)[u:v],donor_ids[u:v]):
        count+=old!=row and new.get(identity)==row
    return count
