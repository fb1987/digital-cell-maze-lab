"""M15 immutable fork and complete ancestry, preserving M14 identities and RNG."""
import json,sqlite3
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .routing_transfer import sha,canonical
from .deep_campaign_store import unpacked,packed,hashed,writer_lock

PRIOR=ROOT/'results/exploration_allocation'
PRIOR_RUN=ROOT/'runs/exploration_allocation_m14'
START=64


def verify_prior():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    for p,entry in seal['local_records'].items():assert sha(ROOT/p)==entry['sha256'],p
    return dict(prior_completion_hashes=len(seal['files']),prior_local_hashes=len(seal['local_records']))


def founders(seed=None):
    # Seed deliberately does NOT create or reset any evolutionary RNG.
    states=readz(PRIOR/'final_states.json.gz')
    assert len(states)==6 and all(s['generation']==s['assessment_generation']==START for s in states)
    return states


def source_registry():
    """Read ALL M14 founders and births, not just its published selected chains."""
    with writer_lock(PRIOR_RUN):
        c=sqlite3.connect(f'file:{PRIOR_RUN}/campaign.sqlite?mode=ro',uri=True)
        c.execute('BEGIN')
        settings={k:unpacked(v) for k,v in c.execute('select key,value from settings')}
        assert settings['finished'] and not c.execute('select n from stages where complete=0').fetchall()
        final=unpacked(c.execute('select value from states where stage=?',(settings['latest'],)).fetchone()[0])
        assert final==founders()
        initial=unpacked(c.execute('select value from states where stage=-1').fetchone()[0])
        registry={}
        for s in initial:
            for i in s['population']:
                entry=dict(item=i,events=[],phase='M14',initial=True)
                if i['id'] in registry:assert registry[i['id']]==entry
                registry[i['id']]=entry
        count=0
        for blob, in c.execute('select decision from stages where complete=1 order by n'):
            for decision in unpacked(blob):
                for b in decision['births']:
                    identity=b['item']['id'];assert identity not in registry
                    registry[identity]=dict(b,phase='M14');count+=1
        assert count==64*6*52
        for entry in registry.values():
            i=entry['item'];assert i['root'] in registry
            if i['parent']:assert i['parent'] in registry
        for s in final:
            for group in ('population','archive','protected','frozen','nominees'):
                for i in s[group]:assert registry[i['id']]['item']==i
        c.close()
    return registry


def export_checkpoint(out):
    evidence=verify_prior();states=founders();registry=source_registry()
    writez(out/'founders.json.gz',states);writez(out/'inherited_registry.json.gz',registry)
    return dict(**evidence,source_journal_sha256=sha(PRIOR_RUN/'campaign.sqlite'),
        source_final_states_sha256=sha(PRIOR/'final_states.json.gz'),
        logical_checkpoint_sha256=hashed(packed(states)),inherited_registry_count=len(registry),
        start_generation=START,evolutionary_rng_reset=False,unchanged_checkpoint=True)


def lineage(identity,registry,inherited):
    chain=[];cur=identity;seen=set()
    while cur:
        assert cur not in seen;seen.add(cur)
        b=registry[cur];chain.append(cur);cur=b['item']['parent']
    mutations=sum(bool(registry[i].get('events')) for i in chain)
    new_mutations=sum(bool(registry[i].get('events')) for i in chain if i not in inherited)
    entry=next((i for i in chain if i in inherited),chain[-1])
    assert mutations==registry[identity]['item']['mutation_depth']
    return dict(chain=chain,phase_entry=entry,cumulative_mutations=mutations,phase_mutations=new_mutations,
        inherited_mutations=mutations-new_mutations)


def freeze(j):
    from . import exploration_continuation as runner
    out=runner.OUT;states=j.state();initial=readz(out/'founders.json.gz')
    inherited=readz(out/'inherited_registry.json.gz');registry=dict(inherited)
    for blob, in j.db.execute('select decision from stages where complete=1 order by n'):
        for decision in unpacked(blob):
            for b in decision['births']:
                identity=b['item']['id'];assert identity not in registry
                registry[identity]=dict(b,phase='M15')
    items={};roles={};comparisons=[];needed=set()
    for s,old in zip(states,initial):
        assert s['name']==old['name']
        for role,group in [('nominee',s['nominees']),('frozen',s['frozen']),('protected',s['protected']),('phase_start',old['nominees'])]:
            for rank,i in enumerate(group):
                assert registry[i['id']]['item']==i
                items[i['id']]=i;roles.setdefault(i['id'],[]).append([s['name'],role,rank])
                if role=='nominee':
                    history=lineage(i['id'],registry,inherited)
                    comparisons.append(dict(condition=s['name'],rank=rank,child=i['id'],root=i['root'],parent=i['parent'],
                        mutations=history['phase_mutations'],cumulative_mutations=history['cumulative_mutations'],
                        inherited_mutations=history['inherited_mutations'],phase_entry=history['phase_entry']))
                    needed.update(history['chain'])
                    for identity in (i['root'],i['parent'],history['phase_entry']):
                        if identity:items[identity]=registry[identity]['item']
    for identity in list(items):needed.update(lineage(identity,registry,inherited)['chain'])
    ancestry={i:registry[i] for i in sorted(needed)}
    runner.writez(out/'choices.json.gz',dict(items=items,representations={i:'modular' for i in items},roles=roles,
        comparisons=comparisons,controls=runner.controls(),chain=j.verify_chain(),
        start_generation=START,phase='M15',identities_and_cumulative_depth_preserved=True))
    runner.writez(out/'ancestry.json.gz',ancestry);runner.writez(out/'final_states.json.gz',states)
    runner.write_layouts('search_exclusions',j.layouts())
