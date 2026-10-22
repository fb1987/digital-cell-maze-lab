"""M23 generic disabled/enabled expression birth and selected point adaptation.
No maze, fitness, oracle or case identities are accessible to these operators.
"""
from .connected_genome import Genome,embed
from .spare_genome import Genome as Body
from .modular_genome import random_node,random_genome as base_random
from .regulatory import Gene,ALWAYS
from .connected_evolution_genome import ordinary,graph
ARMS=('ordinary','enabled','disabled')

def random_genome(rng):return embed(base_random(rng))

def wrappers(g):
    """Prospective syntactic triplets, including nested or no-longer-live ones.
    Mutation can destroy this syntax; no hidden metadata or repair of old code.
    """
    found=[]
    for m,block in enumerate(g.body.blocks):
        for i in range(1,len(block)-2):
            activation,payload,terminal=block[i:i+3]
            if (terminal.op==12 and terminal.a==12+i and terminal.b==13+i
                and terminal.c==11+i and terminal.gate==ALWAYS and payload.gate==12+i):found.append((m,i))
    return found

def extension(g,rng,disabled,block=None,reuse=None):
    blocks=[list(b) for b in g.body.blocks];active=[m for m,b in enumerate(blocks) if b]
    m=rng.choice(active) if block is None else block;assert m in active
    n=len(blocks[m]);reuse=rng.random()<.5 if reuse is None else reuse
    # Draw payload identically before applying the sole birth-condition difference.
    payload=Gene(0,13+n,12+rng.randrange(n),0,0,0,12+n) if reuse else random_node(rng,n+1)
    row=payload.row();row[6]=12+n;payload=Gene(*row)
    event=dict(kind='disabled_extension' if disabled else 'enabled_extension',block=m,
        activation_index=n,payload_reuse=reuse,payload=payload.row(),before=g.digest,
        admission_instruction_limit=128)
    # Common extension admission ensures added dispatches cannot exhaust the
    # unchanged 32768/site limit before 256 ticks, even on an all-open grid.
    # Other generic edits still have the original 256-instruction genotype cap.
    if n+3>31 or g.instructions+3>128:return g,dict(event,kind='bounded_noop',after=g.digest)
    blocks[m].extend((Gene(1,12+n,0 if disabled else 1,0,0,0,64),payload,
                      Gene(12,14+n,12+n,13+n,11+n,0,64)))
    child=Genome(Body(tuple(tuple(b) for b in blocks),g.body.ports),g.initialization)
    return child,dict(event,after=child.digest)

def tune(g,rng):
    choices=wrappers(g)
    if not choices:return ordinary(g,rng),False
    m,i=rng.choice(choices);activation=rng.random()<.5;j=i if activation else i+1
    blocks=[list(b) for b in g.body.blocks];node=random_node(rng,j)
    if not activation:
        row=node.row();row[6]=12+i;node=Gene(*row)
    blocks[m][j]=node
    child=Genome(Body(tuple(tuple(b) for b in blocks),g.body.ports),g.initialization)
    return (child,dict(kind='activation_expression_edit' if activation else 'payload_expression_edit',
        block=m,index=j,before=g.digest,after=child.digest)),True

def vary(g,rng,arm):
    assert arm in ARMS
    bucket=rng.randrange(4);count=len(wrappers(g));fallback=False
    if arm=='ordinary' or bucket>=2:child,event=ordinary(g,rng)
    elif bucket==0:child,event=extension(g,rng,arm=='disabled')
    else:
        (child,event),used=tune(g,rng);fallback=not used
    return child,dict(event,operator=arm,opportunity=bucket,recognized_wrappers=count,
                      tuning_fallback=fallback)
