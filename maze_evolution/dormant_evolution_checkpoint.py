"""M23 explicit matched forks from preserved sources; old histories stay closed."""
import json,random
from copy import deepcopy
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .routing_transfer import sha,canonical
from .datasets import seed_for
from .dormant_evolution_genome import Genome,embed,ARMS
from .modular_genome import Genome as Base
from .deep_campaign_store import unpacked
from .exploration_continuation_checkpoint import lineage

OUT=ROOT/'results/dormant_evolution';PRIOR=ROOT/'results/guarded_extension'
CHILD='m14/modular/1/explore/g320/b48'


def verify_prior():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    for p,e in seal['local_records'].items():assert sha(ROOT/p)==e['sha256'],p
    return dict(prior_completion_hashes=len(seal['files']),prior_local_hashes=len(seal['local_records']))


def anchor_registry(sources):
    from .connected_evolution_checkpoint import anchor_registry as original_registry
    old=readz(ROOT/'results/connected_copy_assay/sources.json.gz')
    registry=original_registry(old)
    identity='historical/M10/threshold'
    item=dict(id=identity,genome=sources['anchors']['threshold']['genome'],root=identity,
              parent=None,birth=0,mutation_depth=0,origin='preserved_random_origin_M10',source_anchor=identity)
    registry[identity]=dict(item=item,events=[],phase='preserved_M10_entry',
        provenance=sources['anchors']['threshold']['provenance'],depth_scope='new preserved entry; zero is not all-time ancestry')
    assert len(registry)==14
    return registry


def founders(seed,namespace='m23',sources=None):
    sources=readz(OUT/'sources.json.gz') if sources is None else sources
    anchors=[e['item'] for e in anchor_registry(sources).values()]
    focal=[next(i for i in anchors if i['id']==identity) for identity in ('m14/reference/gated_specialist',CHILD,'historical/M10/threshold')]
    states=[]
    for rep in range(3):
        for arm in ARMS:
            items=deepcopy(anchors)
            for k in range(82):
                a=focal[k%3];items.append(dict(a,id=f'{namespace}/initial/{rep}/{arm}/{k}',parent=a['id'],birth=0))
            name=f'connected/{rep}/{arm}'
            states.append(dict(name=name,namespace=namespace,representation='connected',replicate=rep,
                method='single',allocation='explore',arm=arm,curriculum=f'{rep}/{arm}',generation=0,assessment_generation=-1,
                population=items,protected=deepcopy(anchors),archive=[],frozen=[],
                rng=random.Random(seed_for(seed,'evolution/paired/'+str(rep),0,0)).getstate()))
    return canonical(states)


def inherited_registry(states,sources):
    registry=anchor_registry(sources)
    for s in states:
        for i in s['population']:
            if i['id'] in registry:assert registry[i['id']]['item']==i
            else:registry[i['id']]=dict(item=i,events=[],phase='M23_initial_clone')
    for i in registry:lineage(i,registry,registry)
    return canonical(registry)


def freeze(j):
    from . import dormant_evolution as runner
    out=runner.OUT;states=j.state();inherited=readz(out/'inherited_registry.json.gz');registry=dict(inherited)
    for blob, in j.db.execute('select decision from stages where complete=1 order by n'):
        for event in unpacked(blob):
            for b in event['births']:
                identity=b['item']['id'];assert identity not in registry;registry[identity]=dict(b,phase='M23')
    items={};roles={};comparisons=[];needed=set()
    for s in states:
        for role,group in [('nominee',s['nominees']),('frozen',s['frozen']),('protected',s['protected'])]:
            for rank,i in enumerate(group):
                assert registry[i['id']]['item']==i
                items[i['id']]=i;roles.setdefault(i['id'],[]).append([s['name'],role,rank])
                if role=='nominee':
                    h=lineage(i['id'],registry,inherited)
                    comparisons.append(dict(condition=s['name'],arm=s['arm'],replicate=s['replicate'],rank=rank,
                        child=i['id'],root=i['root'],parent=i['parent'],mutations=h['phase_mutations'],
                        cumulative_mutations=h['cumulative_mutations'],inherited_mutations=h['inherited_mutations'],phase_entry=h['phase_entry']))
                    needed.update(h['chain'])
                    for identity in (i['root'],i['parent'],h['phase_entry']):
                        if identity:items[identity]=registry[identity]['item']
    for identity in items:needed.update(lineage(identity,registry,inherited)['chain'])
    archive=[dict(id='archive/'+i,representation='connected',genome=v['genome']) for i,v in runner.readz(out/'sources.json.gz')['protected'].items()]
    runner.writez(out/'choices.json.gz',dict(comparison_archive=archive,items=items,representations={i:'connected' for i in items},roles=roles,
        comparisons=comparisons,controls=runner.controls(),chain=j.verify_chain(),start_generation=0,phase='M23',
        inherited_depth_scope='M10-entry study roots plus exact preserved M15 birth and M23 births; not all-time digital evolution depth'))
    runner.writez(out/'ancestry.json.gz',{i:registry[i] for i in sorted(needed)})
    runner.writez(out/'final_states.json.gz',states);runner.write_layouts('search_exclusions',j.layouts())
