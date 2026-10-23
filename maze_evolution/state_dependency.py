"""M29 structural bounds and passive-history comparisons; no oracle routing."""
import hashlib
import numpy as np
from .modular_genome import REFS
from .connected_genome import Genome


def digest(array):return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def dependencies(model,live_only=False):
    g=Genome.from_dict(model['genome']);graphs=[];slots=[]
    for k,block in enumerate(g.body.blocks):
        pending=[len(block)-1] if live_only and block else list(range(len(block)));seen=set();ports=set()
        while pending:
            i=pending.pop()
            if i in seen:continue
            seen.add(i);gene=block[i];row=gene.row()
            for r in [row[j] for j in REFS[gene.op]]+([gene.gate] if gene.gate!=64 else []):
                if r>=12:pending.append(r-12)
                elif r<8:ports.add(r)
            if gene.op in (4,5,6,7,14,15,17):ports.add(gene.a)
        graphs.append(sorted({g.body.ports[k][p] for p in ports}));slots.append(sorted(ports))
    return graphs,slots


def cone(graph):
    result={2,7}
    while True:
        update=result|{c for k in result for c in graph[k]}
        if update==result:return sorted(result)
        result=update


def sharing(a,b):
    ga,gb=(Genome.from_dict(m['genome']) for m in (a,b));da,_=dependencies(a);db,_=dependencies(b)
    shared={k for k in range(10) if ga.initialization[k]==gb.initialization[k] and ga.body.blocks[k]==gb.body.blocks[k] and ga.body.ports[k]==gb.body.ports[k]}
    initial=sorted(shared)
    while True:
        reduced={k for k in shared if set(da[k])|set(db[k])<=shared}
        if reduced==shared:break
        shared=reduced
    return dict(initial_identical_writers=initial,closed_shareable_channels=sorted(shared),conservative_copy_width=20-len(shared),
        total_instructions=ga.instructions+gb.instructions,within_instruction_cap=ga.instructions+gb.instructions<=256,
        sufficient_structural_bound_not_semantic_minimum=True,
        clock_and_budget_accounting_must_remain_separate=True)


def cross_edges(a,b):
    result=[]
    for bank,model in enumerate((a,b)):
        graph,slots=dependencies(model,True)
        for reader in cone(graph):
            for p in slots[reader]:result.append([bank,reader,p])
    return result


def divergence(a,b):
    common=min(len(a),len(b));different=np.any(a[:common]!=b[:common],axis=(1,2));hits=np.flatnonzero(different)
    channels={}
    for k in range(10):
        ticks=np.flatnonzero(np.any(a[:common,k]!=b[:common,k],axis=1))
        channels[str(k)]=int(ticks[0]) if len(ticks) else None
    if not len(hits):return dict(first_tick=None,channels=channels,common_ticks=common)
    t=int(hits[0]);changed=np.argwhere(a[t]!=b[t])
    return dict(first_tick=t,channels=channels,common_ticks=common,first_channel=int(changed[0,0]),first_site=int(changed[0,1]),different_values=int(len(changed)))
