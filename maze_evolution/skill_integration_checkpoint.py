"""M25 immutable matched forks of three complete M23 enabled checkpoints."""
import json,sqlite3
from copy import deepcopy
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .routing_transfer import sha,canonical
from .deep_campaign_store import unpacked,packed,hashed,writer_lock
from .exploration_continuation_checkpoint import lineage

OUT=ROOT/'results/skill_integration';PRIOR=ROOT/'results/dormant_evolution'
PRIOR_RUN=ROOT/'runs/dormant_evolution_m23';MECHANISM=ROOT/'results/branch_causality'
START=243;POLICIES=('current','integrate')


def verify_prior():
    result={}
    for directory in (PRIOR,MECHANISM):
        seal=json.loads((directory/'completion.json').read_text())
        for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
        for p,e in seal['local_records'].items():assert sha(ROOT/p)==e['sha256'],p
        result[str(directory.relative_to(ROOT))]=dict(files=len(seal['files']),local_records=len(seal['local_records']),completion_sha256=sha(directory/'completion.json'))
    return result


def founders(seed=None):
    # This seed does not initialize/reset evolutionary RNGs.
    old=readz(PRIOR/'final_states.json.gz');selected=[s for s in old if s['arm']=='enabled'];assert len(selected)==3
    states=[]
    for s in selected:
        assert s['generation']==s['assessment_generation']==START and s['allocation']=='explore'
        for policy in POLICIES:
            v=deepcopy(s);v.update(name=s['name']+'/'+policy,namespace='m25',policy=policy,
                predecessor_name=s['name'],phase_start=START,assessment_generation=-1)
            # ALL ordered population/archive/protected/frozen/nominees and RNG bytes retained.
            states.append(v)
    return canonical(states)


def source_registry():
    """Extract ancestor closure of selected whole checkpoints, preserving ALL original journal data."""
    inherited=readz(PRIOR/'inherited_registry.json.gz');states=founders();wanted=set()
    for s in states:
        for label in ('population','archive','protected','frozen','nominees'):
            wanted.update(i['id'] for i in s[label])
    with writer_lock(PRIOR_RUN):
        c=sqlite3.connect(f'file:{PRIOR_RUN}/campaign.sqlite?mode=ro',uri=True);c.execute('BEGIN')
        settings={k:unpacked(v) for k,v in c.execute('select key,value from settings')}
        assert settings['finished'] and not c.execute('select n from stages where complete=0').fetchall()
        actual=unpacked(c.execute('select value from states where stage=?',(settings['latest'],)).fetchone()[0])
        assert actual==readz(PRIOR/'final_states.json.gz')
        # First pass stores only ancestry indices, not every old genome in RAM.
        parents={i:e['item'].get('parent') for i,e in inherited.items()};locations={};count=0
        for n,blob in c.execute('select n,decision from stages where complete=1 order by n'):
            for event in unpacked(blob):
                for b in event['births']:
                    i=b['item'];assert i['id'] not in parents;parents[i['id']]=i['parent'];locations[i['id']]=n;count+=1
        assert count==START*9*52
        closure=set();todo=list(wanted)
        while todo:
            i=todo.pop()
            if i in closure:continue
            assert i in parents;closure.add(i)
            if parents[i]:todo.append(parents[i])
        registry={i:inherited[i] for i in closure if i in inherited};needed_stages={locations[i] for i in closure if i in locations}
        for n in sorted(needed_stages):
            blob=c.execute('select decision from stages where n=?',(n,)).fetchone()[0]
            for event in unpacked(blob):
                for b in event['births']:
                    i=b['item']['id']
                    if i in closure:registry[i]=dict(b,phase='M23')
        assert set(registry)==closure
        for s in states:
            for label in ('population','archive','protected','frozen','nominees'):
                for i in s[label]:assert registry[i['id']]['item']==i
        for i in registry:lineage(i,registry,registry)
        c.close()
    return canonical(registry)


def comparison_archive():
    # Comparison only: no M24 intervention model enters any population or archive used by breeding.
    unique={}
    old=readz(PRIOR/'final_responses.json.gz')
    entries=[(e['model'],[i for i in e['aliases'] if not i.startswith('control/')],'M23') for e,rs in old['models']]
    entries += [(i['model'],[i['id']],'M24') for i in readz(MECHANISM/'variants.json.gz')['items'] if i['kind']!='control']
    for model,aliases,study in entries:
        if not aliases:continue
        key=hashed(packed(model));entry=unique.setdefault(key,dict(id='archive/preM25/'+key,**model,source_aliases=[]))
        entry['source_aliases'] += [[study,i] for i in aliases]
    return canonical([unique[k] for k in sorted(unique)])


def export_checkpoint(out):
    states=founders();registry=source_registry()
    writez(out/'founders.json.gz',states);writez(out/'inherited_registry.json.gz',registry)
    writez(out/'comparison_archive.json.gz',comparison_archive())
    return dict(prior=verify_prior(),source_journal_sha256=sha(PRIOR_RUN/'campaign.sqlite'),
        source_final_states_sha256=sha(PRIOR/'final_states.json.gz'),logical_checkpoint_sha256=hashed(packed(states)),
        inherited_registry_count=len(registry),start_generation=START,evolutionary_rng_reset=False,
        unchanged_material_fields=['population','archive','protected','frozen','nominees','rng','generation','arm','method','allocation'],
        administrative_changes=['name','namespace','policy','predecessor_name','phase_start','assessment_generation'],
        all_nine_M23_states_preserved=True,selected_three_enabled_states=True,M24_ablations_breeding_founders=False)


def freeze(j,guard=None):
    from . import skill_integration as runner
    out=runner.OUT;states=j.state();initial=readz(out/'founders.json.gz');inherited=readz(out/'inherited_registry.json.gz');registry=dict(inherited)
    for blob, in j.db.execute('select decision from stages where complete=1 order by n'):
        if guard:assert guard() is None,'Freeze resource guard'
        for event in unpacked(blob):
            for b in event['births']:
                identity=b['item']['id'];assert identity not in registry;registry[identity]=dict(b,phase='M25')
    if guard:assert guard() is None,'Freeze resource guard'
    items={};roles={};comparisons=[];needed=set()
    for s,old in zip(states,initial):
        for role,group in [('nominee',s['nominees']),('frozen',s['frozen']),('protected',s['protected']),('M23_ending_nominee',old['nominees'])]:
            for rank,i in enumerate(group):
                assert registry[i['id']]['item']==i;items[i['id']]=i;roles.setdefault(i['id'],[]).append([s['name'],role,rank])
                if role=='nominee':
                    h=lineage(i['id'],registry,inherited)
                    comparisons.append(dict(condition=s['name'],policy=s['policy'],replicate=s['replicate'],arm='enabled',rank=rank,
                        child=i['id'],root=i['root'],parent=i['parent'],mutations=h['phase_mutations'],cumulative_mutations=h['cumulative_mutations'],
                        inherited_mutations=h['inherited_mutations'],phase_entry=h['phase_entry']))
                    needed.update(h['chain'])
                    for identity in (i['root'],i['parent'],h['phase_entry']):
                        if identity:items[identity]=registry[identity]['item']
    for identity in items:needed.update(lineage(identity,registry,inherited)['chain'])
    runner.writez(out/'choices.json.gz',dict(comparison_archive=readz(out/'comparison_archive.json.gz'),items=items,
        representations={i:'connected' for i in items},roles=roles,comparisons=comparisons,controls=runner.controls(),chain=j.verify_chain(),
        start_generation=START,phase='M25',inherited_depth_scope='Full ancestor closure of three M23 ending enabled populations; new M25 forks, not independent origins'))
    runner.writez(out/'ancestry.json.gz',{i:registry[i] for i in sorted(needed)})
    runner.writez(out/'final_states.json.gz',states);runner.write_layouts('search_exclusions',j.layouts())
