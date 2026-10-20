import random
import pytest
from maze_evolution.linkage_restart_operator import *
from maze_evolution.linkage_restart_data import *
from maze_evolution.linkage_restart_study import make_pools,profile_ids,projection
from maze_evolution.linkage_restart_analysis import compute
from maze_evolution.exposure_genome import Individual
from maze_evolution.growth import replay_mutation
from maze_evolution.composition_audit import geometry

@pytest.fixture(scope='module')
def pools():return read_compressed(OUT/'pools.json.gz')
@pytest.fixture(scope='module')
def data():return load(FIXTURES)

def toy():
    a=((1,20,0,0,0,0,64),(1,18,0,0,0,0,64),(13,2,10,0,0,0,18),(0,30,0,0,0,0,64),(1,21,3,0,0,0,64),(0,22,1,0,0,0,64),(13,0,9,0,0,0,64),(0,23,2,0,0,0,64),(1,24,0,0,0,0,64))
    b=list(a);b[1]=(10,51,8,10,0,0,64);b[2]=(8,34,40,39,0,0,64)
    return a,tuple(b),tuple(f'g{i}' for i in range(len(a)))

def test_conditional_reaching_definitions_do_not_kill_predecessors():
    a=((1,18,1,0,0,0,64),(0,18,9,0,0,0,10),(13,2,18,0,0,0,64))
    assert dependencies(a)==((0,1,2),)
    b=list(a);b[1]=(0,18,9,0,0,0,64)
    assert dependencies(tuple(b))==((1,2),)

def test_transitive_definition_dependencies_are_included():
    a=((1,12,1,0,0,0,64),(0,18,12,0,0,0,64),(13,2,10,0,0,0,18))
    assert dependencies(a)==((0,1,2),)

def test_union_parent_dependency_survives_store_replacement():
    a,b,ids=toy();opts=candidates(a,b,ids,ids)
    assert any(v[:4]==(1,3,1,3) and v[5] and v[4]==2 for v in opts)
    assert any(v[:4]==(2,4,2,4) and not v[5] for v in opts)
    for x,y,u,v,changed,closed in opts:
        if (1 in range(x,y))!=(2 in range(x,y)):assert not closed

def test_no_invented_homology_and_inversions_rejected():
    a,b,ids=toy()
    assert not candidates(a,b,ids,tuple('unrelated'+s for s in ids))
    inv=list(ids);inv[1],inv[2]=inv[2],inv[1]
    assert not candidates(a,b,ids,tuple(inv))

def test_identity_tracking_for_all_structural_edit_types():
    ids=['a','b','c'];events=[dict(kind='insert',index=1,after_length=4),dict(kind='duplicate',index=2,count=2,after_length=6),dict(kind='swap',index=0,other=5,after_length=6),dict(kind='delete',index=2,after_length=5),dict(kind='operand',index=0,after_length=5)]
    got=mutate_ids(ids,events,'kid')
    assert got==['c','kid/edit0/new0','kid/edit1/copy1','b','a'] and len(set(got))==5

def test_linked_and_sham_match_proposal_length_and_feasibility():
    a,b,ids=toy();p=Program(tuple(Gene(*r) for r in a));d=Program(tuple(Gene(*r) for r in b))
    for seed in range(30):
        outcomes=[transfer(p,d,list(ids),list(ids),random.Random(seed),mode)[2] for mode in ('linked','unlinked','sham')]
        x,u,s=outcomes
        assert x['length']==u['length']==s['length'] and x['linked']==s['linked']
        assert x['accepted']==s['accepted']
        if x['accepted']:assert x['dependency_closed']

def test_retained_transfer_does_not_count_new_identity_with_same_instruction():
    a,b,ids=toy();p=Program(tuple(Gene(*r) for r in a));d=Program(tuple(Gene(*r) for r in b))
    e=dict(accepted=True,recipient_interval=[1,3],donor_interval=[1,3]);child=d
    assert retained_changes(p,ids,d,ids,e,child,ids)==2
    changed=list(b);changed[1]=a[1];c=Program(tuple(Gene(*r) for r in changed))
    assert retained_changes(p,ids,d,ids,e,c,ids)==1
    assert retained_changes(p,ids,d,ids,e,p,ids)==0

def test_fresh_origins_and_protected_historical_panel(pools):
    assert pools==make_pools()
    for key,p in pools.items():
        assert len(p['items'])==96 and len(p['protected'])==(20 if key.startswith('carry') else 0)
        for raw in p['items']:
            i=Individual.load(raw);ids=p['gene_ids'][i.identity]
            assert len(ids)==len(set(ids))==len(i.genome.genes)<=256 and not i.identity.startswith('diagnostic/')
            if key.startswith('fresh'):assert i.parent is None and i.birth==0

def test_known_U_homology_uses_exact_historical_edits(pools):
    w=read_compressed(ROOT/'results/compatibility_map/panel.json.gz');u=read_compressed(ROOT/'results/lineage_mapping/panel.json.gz')
    d07=Individual.load(w['items']['d07']);d12=Individual.load(w['items']['d12']);prog=d07.genome.program
    for edit in range(8,13):prog=replay_mutation(prog,u['events'][f'd{edit:02}']['mutation'],256)
    assert prog==d12.genome.program
    ids=pools['carry/0']['gene_ids'];a,b=ids[d07.identity],ids[d12.identity]
    assert a[:106]+a[107:]==b
    opts=candidates(rows(d07.genome.program),rows(d12.genome.program),tuple(a),tuple(b));assert opts
    cut=0
    for x,y,u,v,changed,closed in opts:
        group=set(a[x:y])|set(b[u:v])
        if ('known_U_d07/207' in group)!=('known_U_d07/222' in group):assert not closed;cut+=1
    assert cut

def test_fixture_geometry_and_all_layout_exclusion(data):
    c,ctx,m=data;g=geometry(c,m);assert g['ordinary_inputs']==512
    assert not exclusions()&{layout_hash(o.maze) for o in c.values()}
    assert len(profile_ids(m))==6

def test_training_schedule_pairs_and_stress_are_complete(data):
    old=exclusions()|{layout_hash(o.maze) for o in data[0].values()};d=Data(12345679,old)
    for g in range(3):
        ids=training_batch(d,g);assert len(ids)==6
        cases,contexts,metadata=load(OUT/'software_fixtures'/f'g{g:04d}')
        assert manifest(d.cache.values())==manifest(cases.values())
        meta=[d.metadata[i] for i in ids]
        assert {m['family'] for m in meta}=={'paired','corridor','disconnected'}
        assert len({m['graph'] for m in meta})==1
        geometry(d.cache,d.metadata);clear(d)

def test_projection_uses_only_costs():
    assert projection(dict(pool_rates={'a':.001},reproduction_seconds=.2),32)==32*(36*96*6*.002+2)

def test_activation_requires_two_surviving_donor_changes_and_spread():
    events=[]
    for o in ('carry','fresh'):
        for rep in range(3):
            for arm in ('linked','unlinked','sham'):
                for g in range(32):
                    births=[]
                    for i in range(32):
                        x=dict(length=2,accepted=True,changed_instructions=2,dependency_closed=arm=='linked',reason='accepted')
                        births.append(dict(mating={},crossover=x,retained_donor_changes=2 if i<4 else 1))
                    events.append(dict(key=f'{o}/{rep}/{arm}',generation=g,births=births))
    a=compute(events,32);assert a['longer_search_authorized_by_gate']
    for e in events:
        for b in e['births']:b['retained_donor_changes']=1
    assert not compute(events,32)['longer_search_authorized_by_gate']

def test_dependencies_match_independent_backward_scan(pools):
    from maze_evolution.linkage_restart_audit import independent_groups
    for pool in pools.values():
        for raw in pool['items'][:24]:
            p=rows(Individual.load(raw).genome.program)
            assert dependencies(p)==independent_groups(p)

def test_calibration_births_have_independently_verified_gene_maps(pools,data):
    from maze_evolution.linkage_restart_audit import independent_births
    from maze_evolution.linkage_restart_search import init_state,reproduce,ranked,digest,ARMS
    from maze_evolution.routing_transfer import lines
    responses=iter(lines(FIXTURES/'responses.jsonl.gz'));events=iter(lines(FIXTURES/'reproduction.jsonl.gz'))
    for key,pool in pools.items():
        pop=[Individual.load(raw) for raw in pool['items']];rr={}
        for i in pop:
            e=next(responses);assert e['id']==i.identity and e['key']==key;rr[i.identity]=e['rows']
        rank=ranked(pop,rr,data[2])
        for arm in ARMS:
            state=init_state(key+'/'+arm,pool);new,event=reproduce(state,rank)
            assert next(events)==dict(calibration_only=True,event=event,next_state_digest=digest(new))
            independent_births(state,event)
    assert next(events,None) is None

def test_original_namespace_collision_is_reproduced_from_preserved_records():
    from maze_evolution.routing_transfer import lines
    old=read_compressed(ROOT/'results/linkage_pilot/pools.json.gz')['carry/0']
    protected={r['id'] for r in old['protected']}
    collisions=[]
    for packet in lines(ROOT/'results/linkage_fixtures/reproduction.jsonl.gz'):
        if packet['event']['key']=='carry/0/resample':
            collisions=[b['item']['id'] for b in packet['event']['births'] if b['item']['id'] in protected]
    assert collisions==['carry/0/resample/i63']

def test_duplicate_and_corrupted_population_maps_are_rejected(pools):
    from copy import deepcopy
    from maze_evolution.linkage_restart_search import init_state,assert_population
    s=init_state('carry/0/mutation',pools['carry/0']);bad=deepcopy(s)
    bad['population'][-1]=deepcopy(bad['population'][0])
    with pytest.raises(AssertionError,match='identity collision'):assert_population(bad)
    bad=deepcopy(s);bad['gene_ids'][bad['population'][0]['id']].pop()
    with pytest.raises(AssertionError,match='mapping mismatch'):assert_population(bad)

def test_restart_budget_is_combined_with_failed_attempt():
    from maze_evolution.linkage_restart_study import CANDIDATE_CAP,CALL_CAP,WORK_CAP
    import json
    ex=json.loads((ROOT/'results/linkage_pilot/execution.json').read_text())
    assert CANDIDATE_CAP+ex['budget']['seconds']==720
    assert CALL_CAP+ex['budget']['calls']==3000000
    assert WORK_CAP+ex['budget']['work']==2000000000000

def test_new_birth_namespace_cannot_match_any_historical_pool_identity(pools):
    from maze_evolution.routing_transfer import lines
    historical={r['id'] for p in pools.values() for r in p['items']}
    for packet in lines(FIXTURES/'reproduction.jsonl.gz'):
        event=packet['event'];ids=list(event.get('elite',[]))
        for b in event.get('births',[]):
            assert b['item']['id'].startswith('linkage_x2/') and b['item']['id'] not in historical
            ids.append(b['item']['id'])
        if not event.get('frozen'):assert len(ids)==len(set(ids))==96
