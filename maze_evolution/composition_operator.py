"""Bounded homologous splicing; static compatibility is not functional proof.

No inference, fitness, oracle, generated code or channel rewriting occurs here.
Both parents retain their original instruction/register/channel conventions.
"""
from difflib import SequenceMatcher
from functools import lru_cache
from .growth import Genome as Program
from .regulatory import Gene

def register_reads(row):
    op,dst,a,b,c,rad,gate=row
    operands={0:(a,),2:(a,b),3:(a,b),8:(a,b),9:(a,b),10:(a,b),
              11:(a,),12:(a,b,c),13:(a,),16:(a,b)}.get(op,())
    return set(operands)|({gate} if gate!=64 else set())

def interface(rows):
    """Conservative: gated writes never establish a definite scratch definition."""
    defined=set(range(12));needed=set();writes=set();stores=set();spatial=set()
    for row in rows:
        needed|=register_reads(row)-defined
        op,dst,a,_,_,_,gate=row
        if op==13:stores.add(dst)
        else:
            writes.add(dst)
            if gate==64:defined.add(dst)
        if op in (4,5,6,7,14,15,17):spatial.add(a)
    return dict(live_in=sorted(needed),writes=sorted(writes),stores=sorted(stores),spatial=sorted(spatial))

@lru_cache(maxsize=4096)
def sites(a,b):
    """Swap only differing gaps bracketed by two exact matching instruction runs.

At least 2 equal rows on both sides, both gaps1..16, same scratch write set,
same persistent-store set, no extra live-in scratch demands. Cap is256 genes.
Exact row anchors are structural similarity, not asserted historical homology.
"""
    blocks=SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks();out=[]
    for left,right in zip(blocks,blocks[1:]):
        if left.size<2 or right.size<2:continue
        x,y=left.a+left.size,right.a;u,v=left.b+left.size,right.b
        if not (1<=y-x<=16 and 1<=v-u<=16 and 1<=len(a)-(y-x)+(v-u)<=256):continue
        aa,bb=interface(a[x:y]),interface(b[u:v])
        if aa['writes']!=bb['writes'] or aa['stores']!=bb['stores']:continue
        if not set(bb['live_in'])<=set(aa['live_in']):continue
        out.append((x,y,u,v))
    return tuple(out)

def rows(program):return tuple(tuple(g.row()) for g in program.genes)

def splice(recipient,donor,rng):
    a,b=rows(recipient),rows(donor);options=sites(a,b)
    if not options:return None,None
    x,y,u,v=rng.choice(options);child=Program(tuple(Gene(*r) for r in a[:x]+b[u:v]+a[y:]))
    event=dict(kind='splice',recipient_digest=recipient.digest,donor_digest=donor.digest,
        recipient_interval=[x,y],donor_interval=[u,v],recipient_rows=[list(r) for r in a[x:y]],
        donor_rows=[list(r) for r in b[u:v]],compatible_sites=len(options),child_digest=child.digest)
    return child,event

def replay_splice(recipient,donor,event):
    a,b=rows(recipient),rows(donor);x,y=event['recipient_interval'];u,v=event['donor_interval']
    assert recipient.digest==event['recipient_digest'] and donor.digest==event['donor_digest']
    assert (x,y,u,v) in sites(a,b) and len(sites(a,b))==event['compatible_sites']
    assert [list(r) for r in a[x:y]]==event['recipient_rows']
    assert [list(r) for r in b[u:v]]==event['donor_rows']
    child=Program(tuple(Gene(*r) for r in a[:x]+b[u:v]+a[y:]));assert child.digest==event['child_digest']
    return child
