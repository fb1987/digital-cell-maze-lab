"""M31 scope-only wrapper around the unchanged ordinary M19 mutation grammar.
No maze, answer, fitness or evaluator is accessible to variation.
"""
import random
from .connected_genome import Genome
from .connected_evolution_genome import ordinary
from .deep_campaign_store import packed,hashed
ARMS=('ordinary','output','C6')

class ScopeRNG:
    def __init__(self,rng,target):self.rng=rng;self.target=target;self.first=True
    def randrange(self,*args,**kwargs):
        value=self.rng.randrange(*args,**kwargs)
        if self.first:
            assert args==(10,) and not kwargs,'Unchanged ordinary writer draw required'
            self.first=False;return self.target
        return value
    def __getattr__(self,name):return getattr(self.rng,name)

def vary(g,seed,arm):
    assert arm in ARMS;rng=random.Random(seed)
    scope=None if arm=='ordinary' else 2 if arm=='output' else 6
    child,event=ordinary(g,rng if scope is None else ScopeRNG(rng,scope))
    if scope is not None:
        assert event['block']==scope
        assert all(g.body.blocks[c]==child.body.blocks[c] and g.body.ports[c]==child.body.ports[c] for c in range(10) if c!=scope)
        assert g.initialization==child.initialization
    return child,dict(event,arm=arm,scope=scope,seed=seed,genotype_noop=child.to_dict()==g.to_dict(),rng_after=hashed(packed(rng.getstate())))
