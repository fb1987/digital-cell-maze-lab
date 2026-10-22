"""M20 prospective copy-and-reader-local variation in the unchanged M18 VM."""
import random
from .connected_evolution_genome import Genome, eligible, copy, ordinary
from .routing_transfer import canonical

ARMS = ('generic', 'local')


class ScopedRNG:
    """Replace ONLY the ordinary operator's first (writer-selection) draw."""
    def __init__(self, rng, scope):
        self.rng=rng;self.scope=tuple(scope);self.used=False

    def randrange(self, *args):
        if not self.used:
            assert args==(10,), 'Frozen M19 ordinary operator changed its first draw'
            self.used=True
            return self.rng.choice(self.scope)
        return self.rng.randrange(*args)

    def __getattr__(self, name):
        return getattr(self.rng, name)


def vary(g, rng, arm, scope):
    assert arm in ARMS and len(set(scope))==2
    if arm=='generic':return ordinary(g,rng)
    adapter=ScopedRNG(rng,scope);child,event=ordinary(g,adapter)
    assert adapter.used and event['block'] in scope
    for k in set(range(10))-set(scope):
        assert child.body.blocks[k]==g.body.blocks[k]
        assert child.body.ports[k]==g.body.ports[k]
        assert child.initialization[k]==g.initialization[k]
    return child,event


def make_pool(sources, seed, draws):
    assert draws>0 and draws%2==0
    rng=random.Random(seed);initial=rng.getstate();items=[];bases={}
    for anchor in ('parent','child'):
        original=Genome.from_dict(sources['anchors'][anchor]['genome'])
        choices=eligible(original);assert choices
        for reader,donor,target in choices:
            g,event=copy(original,reader,donor,target,True)
            assert event['kind']=='initialized_connected_copy'
            identity=f'copy/{anchor}/r{reader}d{donor}t{target}'
            item=dict(id=identity,kind='copy_base',anchor=anchor,reader=reader,donor=donor,target=target,
                model=dict(representation='connected',genome=g.to_dict()),events=[event])
            items.append(item);bases[identity]=item
        for draw in range(draws):
            reader,donor,target=rng.choice(choices);seed_edit=rng.getrandbits(64);depth=3+2*(draw%2)
            base_id=f'copy/{anchor}/r{reader}d{donor}t{target}'
            for arm in ARMS:
                g=Genome.from_dict(bases[base_id]['model']['genome']);later=random.Random(seed_edit);steps=[]
                for _ in range(depth):
                    g,event=vary(g,later,arm,(reader,target))
                    steps.append(dict(event=event,genome=g.to_dict(),rng_after=later.getstate()))
                items.append(dict(id=f'{arm}/{anchor}/d{depth}/{draw:04d}',kind='mutation',anchor=anchor,
                    arm=arm,depth=depth,paired_draw=draw,copy_base=base_id,reader=reader,donor=donor,target=target,
                    scope=[reader,target],edit_seed=seed_edit,steps=steps,
                    model=dict(representation='connected',genome=g.to_dict())))
    return canonical(dict(items=items,seed=seed,draws_per_anchor=draws,rng_initial=initial,rng_final=rng.getstate(),
        inference_used=False,selection_between_edits=False,copy_edge_rule='uniform CURRENT eligible edge, before arm split'))
