"""M19 explicit matched forks from preserved sources; old histories stay closed."""
import json,random
from copy import deepcopy
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .routing_transfer import sha,canonical
from .datasets import seed_for
from .connected_evolution_genome import Genome,embed,ARMS
from .modular_genome import Genome as Base
from .deep_campaign_store import unpacked
from .exploration_continuation_checkpoint import lineage

OUT=ROOT/'results/connected_evolution';PRIOR=ROOT/'results/connected_copy_assay'
CHILD='m14/modular/1/explore/g320/b48'


def verify_prior():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    for p,e in seal['local_records'].items():assert sha(ROOT/p)==e['sha256'],p
    return dict(prior_completion_hashes=len(seal['files']),prior_local_hashes=len(seal['local_records']))


def anchor_registry(sources):
    originals=dict(sources['protected']);originals[CHILD]=sources['anchors']['child'];reg={}
    for identity,old in originals.items():
        item=deepcopy(old);item['genome']=embed(Base.from_dict(old['genome'])).to_dict()
        reg[identity]=dict(item=item,events=deepcopy(sources['last_birth']['events']) if identity==CHILD else [],
            phase='M15' if identity==CHILD else 'preserved_M10_entry',
            neutral_M18_embedding=True,source_record=old,source='results/connected_copy_assay/sources.json.gz')
    assert len(reg)==13
    return reg


def founders(seed,namespace='m19',sources=None):
    sources=readz(OUT/'sources.json.gz') if sources is None else sources
    anchors=[e['item'] for e in anchor_registry(sources).values()]
    focal=[next(i for i in anchors if i['id']==identity) for identity in ('m14/reference/gated_specialist',CHILD)]
    states=[]
    for rep in range(3):
        for arm in ARMS:
            items=deepcopy(anchors)
            for k in range(83):
                a=focal[k%2];items.append(dict(a,id=f'{namespace}/initial/{rep}/{arm}/{k}',parent=a['id'],birth=0))
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
            else:registry[i['id']]=dict(item=i,events=[],phase='M19_initial_clone')
    for i in registry:lineage(i,registry,registry)
    return canonical(registry)


def freeze(j):
    from . import connected_evolution as runner
    out=runner.OUT;states=j.state();inherited=readz(out/'inherited_registry.json.gz');registry=dict(inherited)
    for blob, in j.db.execute('select decision from stages where complete=1 order by n'):
        for event in unpacked(blob):
            for b in event['births']:
                identity=b['item']['id'];assert identity not in registry;registry[identity]=dict(b,phase='M19')
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
    runner.writez(out/'choices.json.gz',dict(items=items,representations={i:'connected' for i in items},roles=roles,
        comparisons=comparisons,controls=runner.controls(),chain=j.verify_chain(),start_generation=0,phase='M19',
        inherited_depth_scope='M10-entry study roots plus exact preserved M15 birth and M19 births; not all-time digital evolution depth'))
    runner.writez(out/'ancestry.json.gz',{i:registry[i] for i in sorted(needed)})
    runner.writez(out/'final_states.json.gz',states);runner.write_layouts('search_exclusions',j.layouts())
