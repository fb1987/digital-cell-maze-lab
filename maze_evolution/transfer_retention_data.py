"""M27 externally stratified independent cases, with durable layout observations.

No candidate genome, fitness or response is available to these constructors.
"""
import json
import os
from pathlib import Path
from .breeding_allocation_data import confirmation as standard_confirmation
from .reboot_data import ordinary
from .family_evolution_data import AccessData
from .datasets import manifest
from .foundation_data import layout_hash, transform_maze

STRATA = [(f,n,lo,hi) for f in ('perfect','random') for n in (11,15)
          for lo,hi in ((8,11),(12,15),(16,23))] + [(f,15,24,31) for f in ('perfect','random')]


def component_cycles(maze):
    cells=maze.cells;w=maze.w;pending=[maze.start];seen=set();edges=0
    while pending:
        p=pending.pop()
        if p in seen:continue
        seen.add(p)
        opts=[q for q in (p-w if p>=w else -1,p+w if p+w<len(cells) else -1,
                         p-1 if p%w else -1,p+1 if p%w<w-1 else -1) if q>=0 and cells[q]]
        edges+=len(opts);pending.extend(q for q in opts if q not in seen)
    return edges//2-len(seen)+1


def targeted(seed,previous,count=16):
    d=AccessData(seed,previous);ids=[];attempts={}
    for family,n,lo,hi in STRATA:
        label=f'm27_target/{family}/{n}/edges{lo}-{hi}'
        for index in range(count):
            for attempt in range(2000):
                queries=ordinary(d,f'{label}/item{index}/try{attempt}',[(family,n,1)])
                oracle=d.cache[queries[0]];length=len(oracle.path)-1;cycles=component_cycles(oracle.maze)
                if not lo<=length<=hi or (family=='random' and cycles<1):continue
                ids+=queries;attempts[f'{label}/{index}']=attempt+1
                for c in queries:
                    d.metadata[c].update(target_stratum=f'{family}/{n}/{lo}-{hi}',component_cycles=cycles)
                break
            else:raise RuntimeError(f'M27 fixed stratum exhausted: {label}/{index}')
    return dict(kind='assessment',generation=0,mazes=manifest(d.cache.values()),metadata=d.metadata,
                contexts=d.contexts,queries={'all':ids},new_layouts=sorted(d.layouts-set(previous)),
                rejections=d.rejections,length_sampling_attempts=attempts,seed=seed)


def _fresh(seed,previous,count=16):
    base=standard_confirmation(seed,previous)
    assert len(base['queries']['all'])==1680
    for m in base['metadata'].values():m['panel_group']='standard'
    extra=targeted(seed,set(previous)|set(base['new_layouts']),count)
    for m in extra['metadata'].values():m['panel_group']='targeted'
    assert not set(base['metadata'])&set(extra['metadata'])
    base['mazes']+=extra['mazes'];base['metadata'].update(extra['metadata'])
    base['queries']['all']+=extra['queries']['all']
    base['new_layouts']=sorted(set(base['new_layouts'])|set(extra['new_layouts']))
    base['length_sampling_attempts'].update(extra['length_sampling_attempts'])
    base['rejections']+=extra['rejections'];base['seed']=seed
    base['standard_queries']=1680;base['targeted_queries']=28*count
    for m in base['metadata'].values():
        length=len(m['path'])-1;m['length_bin']='none' if length<0 else 'short' if length<8 else 'medium' if length<16 else 'long'
    assert len(base['queries']['all'])==1680+28*count
    return base


def observed(builder,seed,previous,log_path,guard=lambda:None):
    """Same generator acceptance/RNG; flush every novel returned-proposal orbit.
    Structured rejected geometry batches are captured by their existing hash calls.
    A failure leaves the observer log intact, including proposals not in a packet.
    """
    from . import reboot_data, family_evolution_data
    previous=set(previous);seen=set();path=Path(log_path);assert not path.exists()
    old_hash=family_evolution_data.layout_hash
    old_make,old_wilson=reboot_data.make_case,reboot_data.wilson
    with path.open('x') as log:
        def note(hashes):
            guard();new=set(hashes)-previous-seen
            if new:
                log.write(json.dumps(sorted(new))+'\n');log.flush();os.fsync(log.fileno());seen.update(new)
        def observed_hash(maze):
            value=old_hash(maze);note([value]);return value
        def wrap(fn):
            def generate(*args,**kwargs):
                result=fn(*args,**kwargs)
                note(layout_hash(transform_maze(result.maze,p)) for p in range(8))
                return result
            return generate
        family_evolution_data.layout_hash=observed_hash
        reboot_data.make_case=wrap(old_make);reboot_data.wilson=wrap(old_wilson)
        try:data=builder(seed,previous)
        finally:
            family_evolution_data.layout_hash=old_hash
            reboot_data.make_case, reboot_data.wilson=old_make,old_wilson
            log.flush();os.fsync(log.fileno())
    original=set(data['new_layouts']);data['new_layouts']=sorted((original|seen)-previous)
    data['additional_rejected_layouts_captured']=len(set(data['new_layouts'])-original)
    return data


def fresh(seed,previous,log_path,guard=lambda:None):
    return observed(_fresh,seed,previous,log_path,guard)


def observed_hashes(path):
    values=set()
    with Path(path).open() as f:
        for line in f:values.update(json.loads(line))
    return values
