"""M28 generic sexual variation within the unchanged M18 local VM.

No case, fitness, path, oracle or evaluator is available to these operators.
Homologous output writers are coherent crossover units. Regulated fusion copies
both private expression DAGs into one writer and adds a generic local selector.
"""
from .connected_genome import Genome
from .spare_genome import Genome as Body
from .modular_genome import REFS, random_node
from .regulatory import Gene, ALWAYS
from .connected_evolution_genome import ordinary

ARMS=('mutation','splice','regulated')
NEIGHBOR_OPS=(4,5,6,7,14,15,17)


def splice(a,b,lo,hi):
    """Homologous contiguous writer segment, ports and initialization together."""
    assert 0<=lo<hi<=8
    blocks=list(a.body.blocks);ports=list(a.body.ports);init=list(a.initialization)
    for k in range(lo,hi):
        blocks[k]=b.body.blocks[k];ports[k]=b.body.ports[k];init[k]=b.initialization[k]
    if sum(len(x)+bool(x) for x in blocks)>256:return a,dict(kind='bounded_noop',reason='instructions')
    return Genome(Body(tuple(blocks),tuple(ports)),tuple(init)),dict(kind='homologous_splice',lo=lo,hi=hi)


def remap_block(block,old_ports,new_ports,offset):
    """Preserve donor physical state inputs; private registers are alpha-renamed.

    The VM exposes eight local channel inputs plus four immutable stimulus
    registers. A donor local channel absent from the recipient's first eight
    ports makes this fusion inadmissible, rather than aliasing a stimulus.
    Neighbor operand schemas also expose only the first eight port positions.
    """
    def ref(r):
        if r>=12:return r+offset
        if r>=8:return r
        q=new_ports.index(old_ports[r])
        if q>=8:raise ValueError('unavailable_local_port')
        return q
    result=[]
    for gene in block:
        row=gene.row();row[1]+=offset
        for j in REFS[gene.op]:row[j]=ref(row[j])
        if gene.gate!=ALWAYS:row[6]=ref(gene.gate)
        if gene.op in NEIGHBOR_OPS:
            row[2]=new_ports.index(old_ports[gene.a])
            if row[2]>=8:raise ValueError('unavailable_neighbor_port')
        result.append(Gene(*row))
    return tuple(result)


def fuse(a,b,k,condition):
    old=a.body.blocks[k];donor=b.body.blocks[k];n=len(old)+len(donor)
    if not old or not donor:return a,dict(kind='bounded_noop',reason='empty_writer',block=k)
    if n+2>31 or a.instructions+len(donor)+2>256:
        return a,dict(kind='bounded_noop',reason='capacity',block=k)
    try:imported=remap_block(donor,b.body.ports[k],a.body.ports[k],len(old))
    except ValueError as e:return a,dict(kind='bounded_noop',reason=str(e),block=k)
    assert condition.dst==12+n
    terminal=Gene(12,13+n,12+n,11+n,11+len(old),0,ALWAYS)
    blocks=list(a.body.blocks);blocks[k]=old+imported+(condition,terminal)
    child=Genome(Body(tuple(blocks),a.body.ports),a.initialization)
    return child,dict(kind='regulated_fusion',block=k,condition=condition.row(),
        recipient_nodes=len(old),donor_nodes=len(donor),added_nodes=len(donor)+2)


def vary(a,b,rng,arm):
    assert arm in ARMS
    if arm=='mutation':child,event=ordinary(a,rng)
    elif arm=='splice':
        lo,hi=sorted(rng.sample(range(9),2));child,event=splice(a,b,lo,hi)
    else:
        k=rng.randrange(8);n=len(a.body.blocks[k])+len(b.body.blocks[k])
        # Even rejected opportunities consume the prospective random condition.
        condition=random_node(rng,n);child,event=fuse(a,b,k,condition)
    event.update(arm=arm,before=a.digest,donor=b.digest,after=child.digest,
                 genotype_noop=child.digest==a.digest)
    return child,event
