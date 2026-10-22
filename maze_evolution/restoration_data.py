"""M16 fresh screening combines stress/long strata with unconditioned ordinary mazes."""
from .breeding_allocation_data import validation, confirmation as original_confirmation
from .reboot_data import ordinary
from .family_evolution_data import AccessData
from .datasets import manifest


def _screen(seed, previous):
    base=validation(seed,previous);seen=set(previous)|set(base['new_layouts']);d=AccessData(seed,seen)
    ids=ordinary(d,'m16screen',[(f,n,32) for f,n in [('perfect',11),('perfect',15),('random',9),('random',15),('disconnected',15)]])
    for m in d.metadata.values():
        length=len(m['path'])-1;m['length_bin']='none' if length<0 else 'short' if length<8 else 'medium' if length<16 else 'long'
    base['queries']['all']+=ids;base['mazes']+=manifest(d.cache.values());base['metadata'].update(d.metadata)
    base['new_layouts']=sorted(set(base['new_layouts'])|(d.layouts-seen));base['rejections']+=d.rejections
    assert len(base['queries']['all'])==712
    return base


def observed_build(builder,seed,previous):
    # Observe every generated layout, including early disconnected rejection and
    # novel companions of a rejected overlapping geometry batch. Does not change
    # acceptance, RNG, queries, or inference. Restore borrowed globals on exit.
    from . import reboot_data, family_evolution_data
    from .foundation_data import layout_hash,transform_maze
    seen=set();old_hash=family_evolution_data.layout_hash
    old_make=reboot_data.make_case;old_wilson=reboot_data.wilson
    def observed_hash(maze):
        value=old_hash(maze);seen.add(value);return value
    def wrap(fn):
        def generated(*args,**kwargs):
            oracle=fn(*args,**kwargs)
            seen.update(layout_hash(transform_maze(oracle.maze,p)) for p in range(8))
            return oracle
        return generated
    family_evolution_data.layout_hash=observed_hash
    reboot_data.make_case=wrap(old_make);reboot_data.wilson=wrap(old_wilson)
    try:data=builder(seed,previous)
    finally:
        family_evolution_data.layout_hash=old_hash
        reboot_data.make_case=old_make;reboot_data.wilson=old_wilson
    original=set(data['new_layouts']);complete=(original|seen)-set(previous)
    data['additional_rejected_layouts_captured']=len(complete-original)
    data['new_layouts']=sorted(complete)
    return data


def screen(seed,previous):return observed_build(_screen,seed,previous)
def confirmation(seed,previous):return observed_build(original_confirmation,seed,previous)
