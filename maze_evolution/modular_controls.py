"""Explicit engineering controls/converters. NEVER used to initialize random populations."""
from .regulatory import Gene,ALWAYS,seeded_genome
from .growth import Genome as FlatProgram
from .modular_genome import Genome,REFS


def to_flat(genome):
    """Translate M1 to equivalent old instructions for independent-kernel tests.

Extra clears make dispatch counts unequal; use only generous-budget semantic tests.
"""
    result=[]
    for channel,(block,ports) in enumerate(zip(genome.blocks,genome.ports)):
        for g in block:
            row=g.row()
            for k in REFS[g.op]+(6,):
                if row[k]<8:row[k]=ports[row[k]]
            if g.op in (4,5,6,7,14,15,17):row[2]=ports[row[2]]
            if g.gate!=ALWAYS:result.append(Gene(1,g.dst,0))
            result.append(Gene(*row))
        result.append(Gene(13,channel,block[-1].dst))
    return FlatProgram(tuple(result))


def intact_control():
    """Compile the separately labelled existing handwritten solver into M1 blocks."""
    registers=[('input',i) for i in range(12)]+[('node',1,0,0,0)]*52
    outputs=registers[:8]
    for g in seeded_genome().genes:
        assert g.gate==ALWAYS
        if g.op==13:outputs[g.dst]=registers[g.a];continue
        row=g.row();args=[row[2],row[3],row[4]]
        for k in REFS[g.op]:args[k-2]=registers[row[k]]
        registers[g.dst]=('node',g.op,*args)
    blocks=[]
    for root in outputs:
        nodes=[];memo={}
        def build(expr):
            if expr[0]=='input':return expr[1]
            if expr in memo:return memo[expr]
            _,op,*args=expr
            for k in REFS[op]:args[k-2]=build(args[k-2])
            node=Gene(op,12+len(nodes),*args);nodes.append(node);memo[expr]=node.dst
            return node.dst
        value=build(root)
        if not nodes or value!=nodes[-1].dst:nodes.append(Gene(0,12+len(nodes),value))
        blocks.append(tuple(nodes))
    return Genome(tuple(blocks),tuple(tuple(range(8)) for _ in range(8)))
