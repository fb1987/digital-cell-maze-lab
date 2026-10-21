"""M1 fixed, paired curriculum schedules. All inference receives only maze bytes/endpoints."""
from .family_evolution_data import AccessData
from .reboot_data import ordinary,confirmation
from .selectivity_data import SPECS
from .datasets import manifest


def training(seed,g,previous):
    d=AccessData(seed,previous);length,shape,stress=SPECS[(g//5)%len(SPECS)]
    prefixes=(0,1,2,4,8);d.context('train',g,length,shape,prefixes,stress)
    pose=g%8;graph=('fork','two_junction','cycle')[(g//5)%3] if stress else 'fork'
    chosen=[prefixes[(g+j)%5] for j in range(3)]
    structured=[[c for c,m in d.metadata.items() if m['pose']==pose and m['graph']==graph and m['prefix']==p] for p in chosen]
    assert all(len(cs)==6 for cs in structured)
    ids=ordinary(d,f'train/{g}',[(f,n,6) for f,n in [('perfect',11),('random',9),('disconnected',9)]],(pose,))
    short=[c for c in ids if d.metadata[c]['index']<2]
    queries=dict(familiar=sum(structured,[])+short,broad=structured[0]+ids)
    assert all(len(q)==24 and sum(bool(d.cache[c].path) for c in q)==16 for q in queries.values())
    return dict(kind='train',generation=g,mazes=manifest(d.cache.values()),metadata=d.metadata,contexts=d.contexts,queries=queries,new_layouts=sorted(d.layouts-set(previous)),rejections=d.rejections)


def validation(seed,previous):
    d=AccessData(seed,previous)
    for i,(length,shape,stress) in enumerate(SPECS[:4]):d.context('validation',i,length,shape,(0,1,2,4,8),stress)
    ids=[c for c,m in d.metadata.items() if (m['family']=='paired' and m['pose'] in (0,4)) or (m['family']=='corridor' and m['pose']==0) or (m['family']=='disconnected' and m['prefix']==0 and m['pose']==0)]
    ids+=ordinary(d,'validation',[(f,n,12) for f,n in [('perfect',11),('random',9),('disconnected',9)]])
    return dict(kind='assessment',generation=0,mazes=manifest(d.cache.values()),metadata=d.metadata,contexts=d.contexts,queries=dict(all=ids),new_layouts=sorted(d.layouts-set(previous)),rejections=d.rejections)
