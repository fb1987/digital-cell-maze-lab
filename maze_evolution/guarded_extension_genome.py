"""M22 generic expression extensions. No evaluator, maze or fitness access."""
import random
from .connected_genome import Genome, embed
from .spare_genome import Genome as Body
from .modular_genome import random_node, random_genome
from .regulatory import Gene
from .connected_evolution_genome import ordinary
from .routing_transfer import canonical

ARMS=('ordinary','overwrite','guarded')
ANCHORS=('parent','child','threshold')


def extension(genome,rng,conditional):
    """Append the same payload and one terminal node in both extension arms.

    SELECT keeps old and new values addressable; COPY always exposes new value.
    Every random draw is consumed identically, including unused COPY condition.
    No particular writer, gate, arithmetic expression or endpoint is preferred.
    """
    blocks=[list(b) for b in genome.body.blocks]
    active=[k for k,b in enumerate(blocks) if b]
    m=rng.choice(active);length=len(blocks[m]);old=12+length-1;new=12+length
    reuse=rng.random()<.5
    payload=Gene(0,new,12+rng.randrange(length),0,0,0,64) if reuse else random_node(rng,length)
    condition=rng.randrange(new+1);new_when_true=bool(rng.randrange(2))
    event=dict(kind='guarded_extension' if conditional else 'overwrite_extension',block=m,
        old_register=old,new_register=new,condition=condition,new_when_true=new_when_true,
        payload=payload.row(),payload_reuses_private_expression=reuse,before=genome.digest)
    if length+2>31 or genome.instructions+2>256:
        return genome,dict(event,kind='bounded_noop',after=genome.digest)
    terminal=(Gene(12,new+1,condition,new if new_when_true else old,old if new_when_true else new,0,64)
              if conditional else Gene(0,new+1,new,0,0,0,64))
    blocks[m].extend((payload,terminal))
    result=Genome(Body(tuple(tuple(b) for b in blocks),genome.body.ports),genome.initialization)
    return result,dict(event,terminal=terminal.row(),after=result.digest)


def make_pool(sources,seed,draws,random_count=256):
    assert draws>0 and draws%2==0
    rng=random.Random(seed);initial=rng.getstate();items=[]
    for anchor in ANCHORS:
        original=Genome.from_dict(sources['anchors'][anchor]['genome'])
        for draw in range(draws):
            edit_seed=rng.getrandbits(64);depth=3+2*(draw%2)
            for arm in ARMS:
                g=original;later=random.Random(edit_seed);steps=[]
                for _ in range(depth):
                    g,event=ordinary(g,later) if arm=='ordinary' else extension(g,later,arm=='guarded')
                    steps.append(dict(event=event,genome=g.to_dict(),rng_after=later.getstate()))
                items.append(dict(id=f'{arm}/{anchor}/d{depth}/{draw:04d}',kind='mutation',arm=arm,
                    anchor=anchor,depth=depth,paired_draw=draw,edit_seed=edit_seed,steps=steps,
                    model=dict(representation='connected',genome=g.to_dict())))
    for n in range(random_count):
        g=embed(random_genome(rng))
        items.append(dict(id=f'random/{n:04d}',kind='random_control',model=dict(representation='connected',genome=g.to_dict())))
    return canonical(dict(items=items,seed=seed,draws_per_anchor=draws,random_count=random_count,
        rng_initial=initial,rng_final=rng.getstate(),selection_between_edits=False,inference_used=False))
