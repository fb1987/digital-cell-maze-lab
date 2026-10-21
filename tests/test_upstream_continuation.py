import random,json
from copy import deepcopy
from maze_evolution.upstream_continuation import OUT,readz,task_specs,CONFIG
from maze_evolution.upstream_continuation_search import founders,source_panel,transition,retain
from maze_evolution.upstream_continuation_metrics import criterion,upstream_pairs,build_summary
from maze_evolution.deep_campaign_store import packed,unpacked,hashed


def test_exact_sources_clonal_provenance_and_disjoint_rng():
    sources=source_panel();ss=founders(CONFIG['seed'])
    assert len(sources)==6 and len(ss)==3
    assert ss==readz(OUT/'founders.json.gz')
    assert len({hashed(packed(s['rng'])) for s in ss})==3
    for s in ss:
        assert len(s['population'])==96 and len(s['protected'])==6
        registry={i['id']:i for i in s['protected']}
        assert all(i['mutation_depth']==0 for i in s['population'])
        for i in s['population'][6:]:
            assert i['genome']==registry[i['root']]['genome'] and i['parent']==i['root']
        assert all(not i['id'].startswith('control/') for i in s['population'])
    for i in sources:
        original=i['source_record']['model']['genome']
        assert original['write_gates']==[64]*8 and original['write_holds']==[0]*8
        assert i['genome']==original['base']


def test_rehearsal_allocation_protection_and_rng_replay():
    states=readz(OUT/'fixture_founders.json.gz');steps=readz(OUT/'rehearsal.json.gz');births=0
    for step in steps:
        data=step['data'];counts=[0]*3
        for task in task_specs(states,data):
            for e in task:
                for k,identity in e['aliases']:counts[k]+=len(e['queries'])
        if data['kind']=='train':assert counts==[96*48]*3
        states,events=transition(unpacked(packed(states)),data,step['receipts'])
        assert events==step['decisions'] and hashed(packed(states))==step['state_hash']
        for s,e in zip(states,events):
            assert all(i in s['population'] for i in s['protected'])
            if data['kind']=='train':
                assert len(e['births'])==52
                assert sum(len(b['events'])==0 for b in e['births'])==7
                assert sum(len(b['events'])==1 for b in e['births'])==45
                births+=52
    assert births==624


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


def test_summary_json_and_disconnected_denominators():
    step=readz(OUT/'rehearsal.json.gz')[0];data=step['data'];rows={}
    for receipt in step['receipts']:
        for e in receipt['entries']:
            for k,i in e['aliases']:rows[i]=e['rows']
    states=readz(OUT/'fixture_founders.json.gz');roles={};comparisons=[]
    for s in states:
        for rank,i in enumerate(s['protected']):roles.setdefault(i['id'],[]).append([s['name'],'protected',rank])
        for rank in range(3):
            i=s['protected'][rank];roles.setdefault(i['id'],[]).append([s['name'],'frozen',rank])
            comparisons.append(dict(condition=s['name'],rank=rank,child=i['id'],root=i['id'],parent=None,mutations=0))
    summary=build_summary(dict(roles=roles,comparisons=comparisons),data,rows,{},'software')
    assert summary==json.loads(json.dumps(summary))
    assert all(not c['upstream_acquisition'] for c in summary['conditions'])
    assert all(sum(v['bases'] for v in s.values())==24 for s in summary['ordinary_length_strata'].values())
    assert summary['all_models']['m6/reference/anchor/0']['disconnected_inputs']>0


def test_runner_zero_round_freeze_and_no_restart(tmp_path,monkeypatch):
    from contextlib import nullcontext
    from maze_evolution import upstream_continuation as m
    fixture=readz(OUT/'rehearsal.json.gz')[0];ss=readz(OUT/'fixture_founders.json.gz')
    out=tmp_path/'results';out.mkdir();run=tmp_path/'run'
    m.writez(out/'founders.json.gz',ss);m.writez(out/'exclusions.json.gz',dict(hashes=[],count=0))
    monkeypatch.setattr(m,'OUT',out);monkeypatch.setattr(m,'RUN',run)
    monkeypatch.setattr(m,'check',lambda:dict(m.CONFIG,max_rounds=0))
    monkeypatch.setattr(m,'pushed',lambda _:None)
    monkeypatch.setattr(m,'ProcessPoolExecutor',lambda *a,**k:nullcontext(None))
    monkeypatch.setattr(m.data_builder,'validation',lambda *a:deepcopy(fixture['data']))
    def saved_stage(j,n,data,*args):
        assert n==0
        for k,r in enumerate(fixture['receipts']):
            j.reserve(n,k,r['calls'],r['work']);j.receipt(n,k,r,r['work'])
        return None
    monkeypatch.setattr(m.shared,'run_stage',saved_stage)
    m.run();result=json.loads((out/'session.json').read_text())
    assert result['status']=='complete' and result['generation']==0
    choices=m.readz(out/'choices.json.gz');assert len(choices['comparisons'])==9
    assert all(c['mutations']==0 for c in choices['comparisons'])
    before=(out/'choices.json.gz').read_bytes();m.run();assert (out/'choices.json.gz').read_bytes()==before
    # End-to-end software-only audit/freeze/final/summary pipeline on already
    # excluded saved fixture responses. No scientific cases are generated here.
    from maze_evolution import upstream_continuation_analysis as a
    monkeypatch.setattr(a,'OUT',out);monkeypatch.setattr(a,'RUN',run)
    monkeypatch.setattr(a,'check',lambda:dict(m.CONFIG,max_rounds=0))
    monkeypatch.setattr(a,'founders',lambda seed:deepcopy(ss))
    monkeypatch.setattr(a,'pushed',lambda _:None)
    a.audit_search();assert json.loads((out/'search_audit.json').read_text())['status']=='PASS'
    final_data=deepcopy(fixture['data']);final_data['new_layouts']=[]
    monkeypatch.setattr(a,'confirmation',lambda *args:deepcopy(final_data))
    monkeypatch.setattr(a,'ProcessPoolExecutor',lambda *args,**kwargs:nullcontext(None))
    saved={}
    specs=m.task_specs(ss,fixture['data'])
    for task,receipt in zip(specs,fixture['receipts']):
        for e,r in zip(task,receipt['entries']):saved[hashed(packed(e['model']))]=r['rows']
    control=readz(OUT/'control_fixture.json.gz')
    for c,e in zip(m.controls(),control['entries']):
        saved[hashed(packed(dict(representation=c['representation'],genome=c['genome'])))]=e['rows']
    def saved_final(j,n,data,*args):
        for k,spec,status in j.tasks(n):
            e=spec[0];rs=saved[hashed(packed(e['model']))]
            work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rs)
            receipt=dict(entries=[dict(aliases=e['aliases'],rows=rs)],calls=len(rs),work=work,candidate_seconds=0,cpu_seconds=0,independently_graded=len(rs))
            j.reserve(n,k,len(rs),work);j.receipt(n,k,receipt,work)
        return None
    monkeypatch.setattr(a.shared,'run_stage',saved_final)
    a.final();a.analyze();a.audit_final()
    audit=json.loads((out/'final_audit.json').read_text())
    assert audit['status']=='PASS' and audit['native_replays']==8*392
    assert audit['conventional_calls']==3*392
