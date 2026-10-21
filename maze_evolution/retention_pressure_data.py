"""M10 external difficulty stratification. Candidates see only cells/endpoints."""
from .family_evolution_data import AccessData
from .selectivity_data import SPECS
from .reboot_data import ordinary, confirmation as old_confirmation
from .datasets import manifest


def long_ordinary(d,split,specs,poses=(0,4)):
    ids=[];attempts={}
    for family,n,lo,hi,count in specs:
        name=f'{split}/{family}/{n}/distance{lo}-{hi}'
        for index in range(count):
            for attempt in range(2000):
                queries=ordinary(d,f'{name}/item{index}/try{attempt}',[(family,n,1)],poses)
                length=len(d.cache[queries[0]].path)-1
                if lo<=length and (hi is None or length<=hi):
                    ids+=queries;attempts[f'{name}/{index}']=attempt+1;break
            else:raise RuntimeError('M10 declared length-stratum construction exhausted')
    return ids,attempts


def packet(d,ids,previous,kind,generation,attempts):
    for m in d.metadata.values():
        length=len(m['path'])-1
        m['length_bin']='none' if length<0 else 'short' if length<8 else 'medium' if length<16 else 'long'
    return dict(kind=kind,generation=generation,mazes=manifest(d.cache.values()),metadata=d.metadata,
        contexts=d.contexts,queries={'all' if kind=='assessment' else 'long':ids},
        new_layouts=sorted(d.layouts-set(previous)),rejections=d.rejections,length_sampling_attempts=attempts)


def training(seed,g,previous):
    d=AccessData(seed,previous);length,shape,stress=SPECS[g%6]
    d.context('m10train',g,length,shape,(0,1,2,4,8),stress)
    pose=g%8;graph=('fork','two_junction','cycle')[(g//6)%3] if stress else 'fork'
    prefixes=(g%2,(2,4,8)[g%3],(2,4,8)[(g+1)%3])
    ids=[c for c,m in d.metadata.items() if m['pose']==pose and m['graph']==graph and m['prefix'] in prefixes]
    assert len(ids)==18
    grammar=list(ids)
    # Control reproduces M9's four ordinary strata. The rotating arm changes
    # only ordinary exposure, preserving its 12 bases/two poses per round.
    control_specs=[('perfect',11,1,7,3),('random',9,1,7,3),('perfect',11,16,None,3),('random',9,8,15,3)]
    phase=g%4;pn=11 if phase%2==0 else 15;rn=9 if phase<2 else 15
    rotating_specs=[('perfect',pn,1,7,3),('random',rn,1,7,3),
        ('perfect',pn,16 if phase%2==0 else 8,None if phase%2==0 else 15,3),
        ('random',rn,8 if phase<2 else 16,15 if phase<2 else None,3)]
    poses=(pose,(pose+4)%8)
    control,attempts=long_ordinary(d,f'train{g}/control',control_specs,poses)
    if phase==0:
        # Identical strata share exact cases: avoid gratuitous random differences.
        rotating=list(control);other={}
    else:
        rotating,other=long_ordinary(d,f'train{g}/rotating',rotating_specs,poses)
    attempts.update(other)
    disconnected=ordinary(d,f'train{g}/disconnected',[('disconnected',9,3)],poses)
    queries={arm:grammar+ordinary_ids+disconnected for arm,ordinary_ids in [('control',control),('rotating',rotating)]}
    assert all(len(q)==48 for q in queries.values())
    result=packet(d,queries['control'],previous,'train',g,attempts)
    result['queries']=queries;result['ordinary_schedule']=dict(phase=phase,control=control_specs,rotating=rotating_specs)
    return result


def validation(seed,previous):
    d=AccessData(seed,previous)
    for i,(length,shape,stress) in enumerate(SPECS):d.context('m10validation',i,length,shape,(0,1,2,4,8),stress)
    ids=[c for c,m in d.metadata.items() if (m['family']=='paired' and m['pose'] in (0,4)) or
        (m['family']=='corridor' and m['pose']==0) or (m['family']=='disconnected' and m['prefix']==0 and m['pose']==0)]
    extra,attempts=long_ordinary(d,'validation',[('perfect',11,1,7,6),('random',9,1,7,6),('perfect',11,16,None,6),('random',9,8,15,6)])
    ids+=extra;ids+=ordinary(d,'validation/disconnected',[('disconnected',9,12)])
    assert len(ids)==392
    return packet(d,ids,previous,'assessment',0,attempts)


def confirmation(seed,previous):
    base=old_confirmation(seed,previous);seen=set(previous)|set(base['new_layouts']);d=AccessData(seed,seen)
    ids,attempts=long_ordinary(d,'m10final_long',[
        ('perfect',11,8,15,16),('perfect',11,16,None,16),('random',9,8,15,32),
        ('perfect',15,8,15,16),('perfect',15,16,None,16),('random',15,8,15,16),('random',15,16,None,16)])
    for m in d.metadata.values():m['long_extension']=True
    base['mazes']+=manifest(d.cache.values());base['metadata'].update(d.metadata);base['queries']={'all':base['queries']+ids}
    base['new_layouts']=sorted(set(base['new_layouts'])|(d.layouts-seen));base['length_sampling_attempts']=attempts
    for m in base['metadata'].values():
        length=len(m['path'])-1;m['length_bin']='none' if length<0 else 'short' if length<8 else 'medium' if length<16 else 'long'
    assert len(base['queries']['all'])==1680
    return base
