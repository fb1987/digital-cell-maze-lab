import random,json
from copy import deepcopy
from maze_evolution.exploration_allocation import OUT,readz,task_specs,CONFIG
from maze_evolution.exploration_allocation_search import founders,source_panel,transition,retain,vary,PARENT,SPECIALIST
from maze_evolution.exploration_allocation_metrics import criterion,upstream_pairs,build_summary
from maze_evolution.deep_campaign_store import packed,unpacked,hashed


def test_exact_sources_clonal_provenance_and_disjoint_rng():
    sources=source_panel();ss=founders(CONFIG['seed'])
    assert len(sources)==12 and len(ss)==6
    assert ss==readz(OUT/'founders.json.gz')
    assert len({hashed(packed(s['rng'])) for s in ss})==3
    for source in sources:assert source['genome']==source['source_record']['genome']
    for s in ss:
        assert len(s['population'])==96 and len(s['protected'])==12
        registry={i['id']:i for i in s['protected']}
        assert all(i['mutation_depth']==0 for i in s['population'])
        for i in s['population'][12:]:
            assert i['genome']==registry[i['root']]['genome'] and i['parent']==i['root']
        assert all(not i['id'].startswith('control/') for i in s['population'])
    for a,b in zip(ss[::2],ss[1::2]):
        assert a['rng']==b['rng']
        assert [(i['genome'],i['root']) for i in a['population']]==[(i['genome'],i['root']) for i in b['population']]
        assert sum(i['root']=='m14/reference/gated_partial' for i in a['population'][12:])==42
        assert sum(i['root']=='m14/reference/gated_specialist' for i in a['population'][12:])==42


def test_rehearsal_allocation_protection_and_rng_replay():
    states=readz(OUT/'fixture_founders.json.gz');steps=readz(OUT/'rehearsal.json.gz');births=0
    for step in steps:
        data=step['data'];counts=[0]*6
        for task in task_specs(states,data):
            for e in task:
                for k,identity in e['aliases']:counts[k]+=len(e['queries'])
        assert counts==([96*96]*6 if data['kind']=='train' else [115*392]*6)
        states,events=transition(unpacked(packed(states)),data,step['receipts'])
        assert events==step['decisions'] and hashed(packed(states))==step['state_hash']
        for s,e in zip(states,events):
            assert all(i in s['population'] for i in s['protected'])
            if data['kind']=='train':
                assert len(e['births'])==52
                assert sum(len(b['events'])==0 for b in e['births'])==7
                assert sum(len(b['events'])==1 for b in e['births'])==45
                births+=52
    assert births==1248


def gate_fixture():
    meta={}
    pairs=set()
    for k in range(8):
        pairs.add((str(k),0));meta[str(k)]=dict(family='paired',base=str(k),pose=0,
            prefix=2,graph='cycle',template=str(k%2))
    def cap(pairs=(),no=()):return dict(pairs=set(pairs),corridors=set(),ordinary_bases=set(),correct_no_path=set(no),false=set(),success=set())
    child=cap(pairs,range(10));root=cap();union=cap();a0=cap(no=range(10))
    return child,root,union,a0,meta


def test_no_path_gate_nonvacuous_and_explicit_loss():
    c,r,u,a,m=gate_fixture()
    assert criterion(c,r,u,a,m,1)['upstream_acquisition']
    c['correct_no_path']=set()
    assert criterion(c,r,u,a,m,1)['root_retention']['correct_no_path'] is None
    assert not criterion(c,r,u,a,m,1)['upstream_acquisition']
    c['correct_no_path']=set(range(9))
    assert criterion(c,r,u,a,m,1)['upstream_acquisition']
    r['correct_no_path']={99}
    assert not criterion(c,r,u,a,m,1)['upstream_acquisition']
    r['correct_no_path']=set();a['correct_no_path']=set()
    assert not criterion(c,r,u,a,m,1)['upstream_acquisition']


def test_novelty_false_no_path_mutation_and_prefix_boundaries():
    c,r,u,a,m=gate_fixture()
    assert not criterion(c,r,u,a,m,0)['upstream_acquisition']
    c['false']={'bad'};assert not criterion(c,r,u,a,m,1)['upstream_acquisition'];c['false']=set()
    u['pairs']=set(c['pairs']);assert not criterion(c,r,u,a,m,1)['upstream_acquisition']
    u['pairs']=set();r['pairs']=set(c['pairs']);assert not criterion(c,r,u,a,m,1)['upstream_acquisition']
    r['pairs']=set()
    for x in m.values():x['prefix']=1
    assert not upstream_pairs(c,m)
    for x in m.values():x.update(prefix=2,graph='fork')
    assert not upstream_pairs(c,m)


def test_common_global_operator_exact_replay_and_all_blocks():
    from maze_evolution.modular_genome import Genome,mutate
    g=Genome.from_dict(source_panel()[-2]['genome']);seen=set()
    for seed in range(256):
        a=random.Random(seed);b=random.Random(seed)
        x,event=vary(g,a,'global');y,other=mutate(g,b)
        assert x==y and {k:v for k,v in event.items() if k!='operator'}==other
        assert a.getstate()==b.getstate() and x.instructions<=256
        seen.add(event['block'])
    assert seen==set(range(8))


def test_integration_gate_requires_all_parent_and_specialist_skills():
    from maze_evolution.exploration_allocation_metrics import integration
    c,r,u,a,m=gate_fixture();specialist=deepcopy(c)
    r.update(pairs={('old',0)},corridors={'corridor'},ordinary_bases={'ordinary'},correct_no_path={1})
    c.update(pairs=c['pairs']|r['pairs'],corridors={'corridor'},ordinary_bases={'ordinary'})
    assert integration(c,r,specialist,m,1)['integration_pass']
    for field in ('pairs','corridors','ordinary_bases','correct_no_path'):
        bad=deepcopy(c);bad[field]-=r[field]
        assert not integration(bad,r,specialist,m,1)['integration_pass']
    bad=deepcopy(c);bad['pairs'].remove(('0',0));assert not integration(bad,r,specialist,m,1)['integration_pass']
    assert not integration(c,r,specialist,m,0)['integration_pass']
    bad=deepcopy(c);bad['false']={'bad'};assert not integration(bad,r,specialist,m,1)['integration_pass']
    bad=deepcopy(r);bad['correct_no_path']=set();assert not integration(c,bad,specialist,m,1)['integration_pass']
    assert not integration(c,r,r,m,1)['integration_pass']

def test_policy_endpoint_does_not_reselect_or_reward_failed_integration():
    from maze_evolution.exploration_allocation_metrics import policy_comparison
    conditions=[]
    for rep in range(3):
        for arm in ('retention','explore'):
            for role in range(3):
                conditions.append(dict(condition=f'modular/{rep}/{arm}',rank=role,child=f'{rep}/{arm}/{role}',
                    integration=dict(integration_pass=arm=='explore',specialist_pairs_retained=32)))
    assert policy_comparison(conditions)['exploration_support']
    for c in conditions:
        if c['rank']==0 and c['condition'].endswith('/explore'):c['integration']['integration_pass']=False
    assert not policy_comparison(conditions)['exploration_support']
    assert policy_comparison(conditions)['total_difference']==0
    conditions[3]['integration']['integration_pass']=True
    assert policy_comparison(conditions)['positive_pairs']==1
    assert not policy_comparison(conditions)['exploration_support']


def test_matched_persistent_panels_and_common_fresh_challenges():
    from maze_evolution.exploration_allocation_data import panels
    ps=panels();steps=readz(OUT/'rehearsal.json.gz')[1:]
    for rep,p in enumerate(ps):
        a=p['methods']['bank'];b=p['methods']['bank']
        assert len(a)==len(b)==392 and len(set(a)&set(b))==392
    for step in steps:
        d=step['data'];common=d['common_queries'];assert len(common)==48
        for rep in range(3):
            for arm in ('retention','explore'):
                key=f'{rep}/{arm}';q=d['queries'][key];assert len(q)==len(set(q))==96
                fixed=[c for c in ps[rep]['methods']['bank'] if ps[rep]['metadata'][c]['family'] in ('ordinary_perfect','ordinary_random')]
                assert q==common+fixed and d['persistent_queries'][key]==fixed
        for decision in step['decisions']:
            assert all(e['operator']=='global' for b in decision['births'] for e in b['events'])


def test_frozen_bank_exact_m11_provenance_and_parent_successes():
    from maze_evolution import exploration_allocation as m
    from maze_evolution.referenced_campaign_store import load_layouts
    source=m.readz(m.OUT/'source_panels.json.gz')
    old=m.ROOT/'results/retention_bank'
    assert source['source_freeze_sha256']==m.sha(old/'calibration_freeze.json.gz')
    fixture=m.readz(m.OUT/'rehearsal.json.gz')[0]
    caps={}
    from maze_evolution.exploration_allocation_metrics import capabilities_plus
    for result in fixture['receipts']:
        for e in result['entries']:
            for k,i in e['aliases']:
                if i==PARENT:caps[k]=capabilities_plus(e['rows'],fixture['data']['metadata'])
    assert [len(caps[k]['ordinary_bases']) for k in range(6)]==[24]*6
    # Reuse is limited to the exported M11 development panels, already excluded
    # from NEW generation. Fresh fixture draws never duplicate those layouts.
    initial=load_layouts(m.OUT/'exclusions.json')
    oldlayouts=load_layouts(old/'whole_layout_exclusions.json');assert oldlayouts<=initial
    assert all(not oldlayouts&set(s['data']['new_layouts']) for s in m.readz(m.OUT/'rehearsal.json.gz')[1:])


def test_panel_namespace_preserves_exact_stimuli_without_collisions():
    from maze_evolution.exploration_allocation_data import panels,validation
    from maze_evolution.exploration_allocation import readz,OUT
    raw=readz(OUT/'source_panels.json.gz')['panels'];ps=panels();seen=set()
    for rep,(a,b) in enumerate(zip(raw,ps)):
        prefix=f'm14/reused/{rep}/'
        for old,new in zip(a['mazes'],b['mazes']):
            assert dict(new,case_id=old['case_id'])==old
            assert new['case_id']==prefix+old['case_id'] and new['case_id'] not in seen
            seen.add(new['case_id'])
        for c,m in a['metadata'].items():
            assert dict(b['metadata'][prefix+c],base=m['base'],template=m['template'])==m
    d=validation(None,None)
    assert len(d['mazes'])==len(d['metadata'])==1320
    assert len({m['case_id'] for m in d['mazes']})==1320


def test_imperfect_intermediates_remain_eligible():
    from maze_evolution.exploration_allocation_metrics import capabilities_plus,integration
    steps=readz(OUT/'rehearsal.json.gz');states=readz(OUT/'fixture_founders.json.gz');found=False
    for step in steps:
        rows=[{} for _ in states]
        for receipt in step['receipts']:
            for e in receipt['entries']:
                for k,i in e['aliases']:rows[k][i]=e['rows']
        if step['data']['kind']=='train':
            for k,decision in enumerate(step['decisions']):
                caps={i:capabilities_plus(rs,step['data']['metadata']) for i,rs in rows[k].items()}
                for b in decision['births']:
                    parent=b['item']['parent']
                    if parent and not integration(caps[parent],caps[PARENT],caps[SPECIALIST],step['data']['metadata'],1)['integration_pass']:found=True
        states,_=transition(states,step['data'],step['receipts'])
    assert found,'The design must permit imperfect surviving intermediates to breed.'


def test_full_zero_round_freeze_audit_confirmation_pipeline(tmp_path,monkeypatch):
    from contextlib import nullcontext
    from maze_evolution import exploration_allocation as m,exploration_allocation_analysis as a
    fixture=readz(OUT/'rehearsal.json.gz')[0];ss=readz(OUT/'fixture_founders.json.gz')
    finalfixture=readz(OUT/'final_fixture.json.gz')
    out=tmp_path/'results';out.mkdir();run=tmp_path/'run'
    m.writez(out/'founders.json.gz',ss)
    def export_layouts(name,hashes):
        path=out/(name+'.part.json.gz');m.writez(path,dict(hashes=sorted(hashes)))
        m.writej(out/(name+'.json'),dict(count=len(hashes),parts=[dict(path=str(path),count=len(hashes),sha256=m.sha(path))]))
    export_layouts('exclusions',set())
    monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run)
    monkeypatch.setattr(m,'write_layouts',export_layouts)
    monkeypatch.setattr(m,'check',lambda:dict(m.CONFIG,max_rounds=0,storage_bytes=32*2**20,layout_base_manifest=str(out/'exclusions.json')))
    monkeypatch.setattr(m,'pushed',lambda _:None)
    monkeypatch.setattr(m.data_builder,'validation',lambda *args:deepcopy(fixture['data']))
    monkeypatch.setattr(m,'ProcessPoolExecutor',lambda *args,**kwargs:nullcontext(None))
    def saved_search(j,n,data,*args):
        for (k,spec,status),receipt in zip(j.tasks(n),fixture['receipts']):
            assert spec==m.task_specs(ss,data)[k]
            j.reserve(n,k,receipt['calls'],receipt['work']);j.receipt(n,k,receipt,receipt['work'])
        return None
    monkeypatch.setattr(m.shared,'run_stage',saved_search)
    m.run();assert json.loads((out/'session.json').read_text())['status']=='complete'
    frozen=(out/'choices.json.gz').read_bytes();m.run();assert (out/'choices.json.gz').read_bytes()==frozen
    monkeypatch.setattr(a,'OUT',out);monkeypatch.setattr(a,'RUN',run)
    monkeypatch.setattr(a,'check',lambda:dict(m.CONFIG,max_rounds=0,storage_bytes=32*2**20,layout_base_manifest=str(out/'exclusions.json')))
    monkeypatch.setattr(a,'founders',lambda seed:deepcopy(ss));monkeypatch.setattr(a,'pushed',lambda _:None)
    a.audit_search();assert json.loads((out/'search_audit.json').read_text())['status']=='PASS'
    monkeypatch.setattr(a,'confirmation',lambda *args:deepcopy(finalfixture))
    monkeypatch.setattr(a,'ProcessPoolExecutor',lambda *args,**kwargs:nullcontext(None))
    def evaluate_final(j,n,data,*args):
        ids=set(data['queries']['all']);mz=[x for x in data['mazes'] if x['case_id'] in ids]
        for k,spec,status in j.tasks(n):
            receipt=m.evaluate_task(spec,mz,hashed(packed(mz)))
            j.reserve(n,k,receipt['calls'],receipt['work']);j.receipt(n,k,receipt,receipt['work'])
        return None
    monkeypatch.setattr(a.shared,'run_stage',evaluate_final)
    a.final();a.analyze();a.audit_final()
    result=json.loads((out/'summary.json').read_text());audit=json.loads((out/'final_audit.json').read_text())
    assert result['queries']==1680 and len(result['conditions'])==18
    assert all(not c['integration']['integration_pass'] for c in result['conditions'])
    assert audit['status']=='PASS' and audit['native_replays']==result['usage']['calls'] and audit['conventional_calls']==5040


def test_quality_profile_rejects_empty_flood_wall_timeout_and_false_no_path():
    from maze_evolution.exploration_allocation_search import quality_profile
    base=dict(case='q',reachable=True,status='emitted',optimal=False,valid=False,failure='missing_endpoint',partial=.25,mask='01')
    assert quality_profile([base])==(1,)
    assert quality_profile([dict(base,partial=.5)])==(2,)
    assert quality_profile([dict(base,valid=True,partial=0)])==(3,)
    assert quality_profile([dict(base,optimal=True,valid=True)])==(4,)
    assert quality_profile([dict(base,partial=.249)]) is None
    for failure in ('empty_output','wall_crossing','branch_or_cycle','budget_exhausted','disconnected_output'):
        assert quality_profile([dict(base,failure=failure,partial=.9)]) is None
    assert quality_profile([dict(base,status='budget_exhausted',partial=.9)]) is None
    assert quality_profile([base,dict(base,status='no_path')]) is None
    assert quality_profile([dict(base,reachable=False,status='no_path',no_path=True)]) is None
    # Arbitrary raster changes with identical performance do not create cells.
    assert quality_profile([base])==quality_profile([dict(base,mask='ffff')])


def test_exploration_samples_cells_not_clone_count_and_keeps_cap():
    from maze_evolution.exploration_allocation_search import exploration_pool,quality_profile
    g=source_panel()[0]['genome'];base=dict(reachable=True,status='emitted',optimal=False,valid=False,failure='missing_endpoint',partial=0,mask='01',no_path=False)
    meta={str(n):dict(family='paired',graph='fork',prefix=n,base=str(n),pose=0,template='t') for n in range(20)}
    def rr(active):return [dict(base,case=str(n),partial=.5 if n==active else 0) for n in range(20)]
    items=[dict(id=f'i{k:02}',genome=g) for k in range(20)];core=[dict(id='core',genome=g)]
    rows={i['id']:rr(k) for k,i in enumerate(items)};rows['core']=rr(-1)
    a=random.Random(3);b=random.Random(3)
    x,log=exploration_pool(items,rows,meta,core,a)
    duplicates=[dict(items[0],id=f'zclone{k}') for k in range(80)]
    rows.update({i['id']:rr(0) for i in duplicates})
    y,other=exploration_pool(items+duplicates,rows,meta,core,b)
    assert len(x)==len(y)==12 and [i['id'] for i in x]==[i['id'] for i in y] and a.getstate()==b.getstate()
    assert log['quality_eligible_distinct_cells']==other['quality_eligible_distinct_cells']==20
    assert len({quality_profile(rows[i['id']]) for i in x})==12
    # An existing core behavior takes no extra exploration slot.
    core=[items[0]]
    z,log=exploration_pool(items[1:],rows,meta,core,random.Random(3))
    assert all(quality_profile(rows[i['id']])!=quality_profile(rows['i00']) for i in z)


def test_retention_control_matches_prior_selector_exactly():
    from maze_evolution.mutation_scope_search import retain as old_retain
    states=readz(OUT/'fixture_founders.json.gz')
    for step in readz(OUT/'rehearsal.json.gz'):
        data=step['data'];rows=[{} for _ in states]
        for receipt in step['receipts']:
            for e in receipt['entries']:
                for k,i in e['aliases']:rows[k][i]=e['rows']
        if data['kind']=='train':
            # Only reference identity spelling is translated; same genomes, rows,
            # panel metadata and RNG. This tests compatibility, not new inference.
            for k in (0,2,4):
                pop=states[k]['population'];protected=states[k]['protected']
                rename=lambda i:dict(i,id=i['id'].replace('m14/','m13/'))
                a=random.Random(101+k);b=random.Random(101+k)
                actual,neutral,explorers,log=retain(pop,rows[k],data['metadata'],a,protected,exploration=False)
                expected,oldneutral=old_retain([rename(i) for i in pop],{i.replace('m14/','m13/'):v for i,v in rows[k].items()},data['metadata'],b,[rename(i) for i in protected])
                assert [i['id'].replace('m14/','m13/') for i in actual]==[i['id'] for i in expected]
                assert [i.replace('m14/','m13/') for i in neutral]==oldneutral and a.getstate()==b.getstate()
                assert not explorers and log==dict(enabled=False)
        states,_=transition(states,data,step['receipts'])


def test_rehearsal_reserved_survival_and_breeding_are_real_and_replayable():
    seen=0
    for step in readz(OUT/'rehearsal.json.gz')[1:]:
        for decision in step['decisions']:
            explorers=decision['explorer_ids'];births=decision['births']
            assert len(explorers)<=12 and set(explorers)<=set(decision['survivors'])
            allotted=[b for b in births if b['parent_policy']=='exploration_cycle']
            if decision['name'].endswith('/retention'):assert not explorers and not allotted
            elif explorers:
                seen+=1;assert len(allotted)==12
                assert [b['item']['parent'] for b in allotted]==[explorers[k%len(explorers)] for k in range(12)]
                assert set(explorers)<=set(b['item']['parent'] for b in allotted)
                assert all(sum(b['item']['parent']==i for b in allotted)>=1 for i in explorers)
            else:assert not allotted
            assert len([b for b in births if b['parent_policy']=='random_immigrant'])==7
            assert len([b for b in births if b['parent_policy']=='shared_lexicase'])==45-len(allotted)
    assert seen,'The discarded rehearsal must exercise nonempty explorer allocation.'
