"""M27 fixed independent transfer assay. No evolution or candidate modifications."""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import gzip
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import sqlite3
import time
import traceback
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import canonical,sha
from .deep_campaign_store import packed,unpacked,hashed,writer_lock
from .referenced_campaign_store import Journal,load_layouts,write_reference
from . import deep_campaign as shared
from .connected_evaluation import organism,evaluate_task
from .copy_specialization import tasks,fixture_sources
from .connected_evolution import controls,pushed
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .transfer_retention_data import fresh,targeted,observed,observed_hashes,STRATA,component_cycles
from .transfer_retention_metrics import build_summary

OUT=ROOT/'results/transfer_retention_m27'
RUN=ROOT/'runs/transfer_retention_m27'
M25=ROOT/'results/skill_integration'
M26=ROOT/'results/evolvability_audit_m26'
CONFIG=dict(phase='M27',fresh_seed=2026102301,fixture_seed=202610230180,workers=10,
    session_wall_seconds=1200,audit_wall_seconds=1800,call_cap=1000000,work_cap=10**14,
    memory_bytes=8*2**30,storage_bytes=4*2**30,disk_free_floor_bytes=16*2**30,
    layout_base_manifest='results/transfer_retention_m27/exclusions.json')


def clock():return time.monotonic(),time.time()

def elapsed(t):return max(0.,time.monotonic()-t[0],time.time()-t[1])


def storage():return sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file())


def guard(directory,config,started):
    if elapsed(started)>=config['session_wall_seconds']:return 'wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
    if storage()>=config['storage_bytes']:return 'storage'


def ensure(config,started):
    assert guard(RUN,config,started) is None,'M27 resource guard'


def generation_guard(config,started):
    sampled=[0.]
    def check():
        assert elapsed(started)<config['session_wall_seconds'],'M27 generation wall guard'
        if time.monotonic()-sampled[0]>.5:
            ensure(config,started);sampled[0]=time.monotonic()
    return check


def prior_check():
    result={}
    for directory in (M25,M26):
        seal=json.loads((directory/'completion.json').read_text())
        for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
        for p,r in seal.get('local_records',{}).items():
            assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
        result[str(directory.relative_to(ROOT))]=dict(files=len(seal['files']),local_records=len(seal.get('local_records',{})),sha256=sha(directory/'completion.json'))
    return result


def check():
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest()
    assert all(now[k]==reg[k] for k in ('python','dependencies'))
    prior_check();return json.loads((OUT/'config.json').read_text())


def make_pool():
    study=json.loads((M26/'interpretation.json').read_text())
    with gzip.open(M26/'novel_complete_witnesses.json.gz','rt') as f:witnesses=json.load(f)
    inherited=readz(M25/'inherited_registry.json.gz')
    initial=readz(M25/'founders.json.gz')
    entries={i:e for i,e in inherited.items()};parents={i:e['item']['parent'] for i,e in inherited.items()}
    con=sqlite3.connect(f'file:{ROOT}/runs/skill_integration_m25/campaign.sqlite?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
    for blob, in con.execute("select decision from stages where kind='train' order by n"):
        for d in unpacked(blob):
            for b in d['births']:parents[b['item']['id']]=b['item']['parent']
    need=set(study['candidates'])
    for d in study['candidates'].values():need.update(d['offspring_ids']);need.update(x for x in (d['model']['parent'],d['model']['root']) if x)
    for w in witnesses:
        if w['initial_live_ancestor'] not in study['candidates']:need.add(w['initial_live_ancestor'])
    closure=set(need)
    for i in list(need):
        current=i;seen=set()
        while current:
            assert current not in seen;seen.add(current);closure.add(current);current=parents[current]
    for blob, in con.execute("select decision from stages where kind='train' order by n"):
        for d in unpacked(blob):
            for b in d['births']:
                i=b['item']['id']
                if i in closure:entries[i]=dict(phase='M25',item=b['item'],events=b['events'],parent_policy=b['parent_policy'],population=d['name'])
    con.close();assert closure<=set(entries)
    registry={};historical=set();protected={i['id'] for s in initial for i in s['protected']}
    def add(identity,model,role):
        if identity not in registry:registry[identity]=dict(id=identity,model=model,roles=[])
        assert registry[identity]['model']==model,identity
        if role not in registry[identity]['roles']:registry[identity]['roles'].append(role)
    def source(identity,role):
        add(identity,dict(representation='connected',genome=entries[identity]['item']['genome']),role)
    for i in protected:source(i,'protected');historical.add(i)
    conditions=[];relations=[]
    for i,d in sorted(study['candidates'].items()):
        source(i,'rare_variant');item=entries[i]['item'];cohort='random_immigrant' if not item['parent'] else 'noop_mutant' if d['noop'] else 'changed_mutant'
        ws=[w for w in witnesses if w['id']==i];case_ids=sorted({c for w in ws for c in w['case_ids']})
        entry=ws[0]['initial_live_ancestor'] if item['parent'] else None
        for identity,role in [(item['parent'],'actual_parent'),(item['root'],'exact_root'),(entry,'phase_entry')]:
            if identity:source(identity,role)
        if entry:historical.add(entry)
        chain=[];current=i
        while current:
            chain.append(current);current=parents[current]
        phase=sum(entries[x].get('phase')=='M25' and bool(entries[x].get('events')) for x in chain)
        conditions.append(dict(id=i,cohort=cohort,parent=item['parent'],root=item['root'],entry=entry,
                               phase_mutation_births=phase,inherited_records=len(chain)-sum(entries[x].get('phase')=='M25' for x in chain),
                               witness_cases=case_ids,original_max_novel_edges=d['max_novel_edges'],chain=chain))
        for child in d['offspring_ids']:
            assert entries[child]['item']['parent']==i;source(child,'after_hit_offspring')
            event,=entries[child]['events']
            relations.append(dict(parent=i,child=child,parent_witness_cases=case_ids,genotype_noop=event['before']==event['after']))
    old=readz(M25/'choices.json.gz')
    for i,item in old['items'].items():
        add(i,dict(representation=old['representations'][i],genome=item['genome']),'M25_frozen_choice');historical.add(i)
    for a in old['comparison_archive']:
        add(a['id'],{k:a[k] for k in ('representation','genome')},'historical_archive');historical.add(a['id'])
    for c in old['controls']:add(c['id'],{k:c[k] for k in ('representation','genome')},'control')
    assert Counter(c['cohort'] for c in conditions)==dict(changed_mutant=28,noop_mutant=1,random_immigrant=1)
    assert len(relations)==39 and len({c['child'] for c in relations})==39
    pool=canonical(dict(items=sorted(registry.values(),key=lambda x:x['id']),conditions=conditions,
        offspring_relations=relations,historical_references=sorted(historical),control_ids=sorted(c['id'] for c in old['controls']),
        selection_rule='ALL30 M26 rare complete-win identities + all actual parents + all39 after-hit offspring + root/entry/protected + all23 M25 choices + all100 archive +3 intact controls; no transformations or nomination.',
        evolution=False,scientific_inference_used_to_construct_pool=False))
    return pool,{i:entries[i] for i in sorted(closure)}


def replay_panel():
    with gzip.open(M26/'novel_complete_witnesses.json.gz','rt') as f:ws=json.load(f)
    mazes={};meta={};expected={}
    for w in ws:
        for m in w['saved_mazes']:
            cid=m['case_id'];assert cid not in mazes or mazes[cid]==m;mazes[cid]=m
        for c,m in w['metadata'].items():assert c not in meta or meta[c]==m;meta[c]=m
        for i,rs in w['saved_rows'].items():
            for row in rs:
                key=(i,row['case']);assert key not in expected or expected[key]==row;expected[key]=row
    assert len(mazes)==len(meta)==22
    data=dict(kind='assessment',generation=0,mazes=[mazes[c] for c in sorted(mazes)],metadata=meta,
              queries={'all':sorted(mazes)},new_layouts=[],reused_development=True,seed=None)
    return canonical(data),expected


def prepare():
    assert not OUT.exists();prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    pool,ancestry=make_pool();replay,_=replay_panel()
    writej(OUT/'config.json',CONFIG);writez(OUT/'pool.json.gz',pool);writez(OUT/'ancestry.json.gz',ancestry)
    writez(OUT/'replay_panel.json.gz',replay)
    physical=sum(map(len,tasks(pool['items'],[])))
    assert physical*2150<CONFIG['call_cap']
    writej(OUT/'preparation.json',dict(prior=prior,aliases=len(pool['items']),physical_models=physical,
        primary_changed_mutants=28,rare_variants=30,actual_parents=22,after_hit_offspring=39,
        inherited_archive_aliases=100,ancestry_closure=len(ancestry),planned_scientific_calls=physical*2150,
        source_M25_journal_sha256=sha(ROOT/'runs/skill_integration_m25/campaign.sqlite'),scientific_calls=0,new_scientific_cases=0))


def fixture_pool(witness_cases):
    source=fixture_sources();g=source['anchors'];items=[]
    for k in ('parent','child'):items.append(dict(id='fake/'+k,model=dict(representation='connected',genome=g[k]['genome']),roles=['fixture']))
    items.append(dict(id='m14/reference/anchor/0',model=dict(representation='connected',genome=g['parent']['genome']),roles=['fixture_reference']))
    cs=controls()
    for c in cs:items.append(dict(id=c['id'],model={k:c[k] for k in ('representation','genome')},roles=['control']))
    return dict(items=items,historical_references=['fake/parent','m14/reference/anchor/0'],control_ids=[c['id'] for c in cs],
       conditions=[dict(id='fake/child',parent='fake/parent',root='fake/parent',entry='fake/parent',cohort='changed_mutant',phase_mutation_births=1,witness_cases=witness_cases)],offspring_relations=[])


def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'preflight.json').exists()
    start=clock();config=dict(CONFIG,session_wall_seconds=600);previous=load_layouts(M25/'whole_layout_exclusions.json')
    data=observed(lambda s,p:targeted(s,p,1),CONFIG['fixture_seed'],previous,RUN/'fixture_generation_layouts.jsonl',generation_guard(config,start))
    assert len(data['queries']['all'])==28
    old=readz(ROOT/'results/restoration_assay/discarded_corpus_fixture.json.gz')
    groups=defaultdict(list)
    for c in old['queries']['all']:groups[old['metadata'][c]['family']].append(c)
    extra=[c for family,cs in sorted(groups.items()) for c in sorted(cs)[:2]]
    for m in data['metadata'].values():m['panel_group']='targeted'
    for c in extra:data['metadata'][c]=dict(old['metadata'][c],panel_group='standard')
    data['mazes']+=[m for m in old['mazes'] if m['case_id'] in extra]
    data['queries']['all']+=extra
    for m in data['metadata'].values():
        length=len(m['path'])-1;m['length_bin']='none' if length<0 else 'short' if length<8 else 'medium' if length<16 else 'long'
    writez(OUT/'discarded_fixture.json.gz',data)
    pp=fixture_pool(data['queries']['all'][:2]);ids=data['queries']['all'];mz=[m for m in data['mazes'] if m['case_id'] in ids]
    validate_panel(data,previous,fixture=True)
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    directory=RUN/'fixture'
    write_reference(OUT/'exclusions.json',M25/'whole_layout_exclusions.json',previous|set(data['new_layouts']))
    fixture_config=dict(config,layout_base_manifest=str(OUT/'exclusions.json'))
    stage_rows={};native=calls=0;candidate=cpu=0.
    with writer_lock(directory):
        j=Journal(directory);j.initialize(fixture_config,dict(fixture=True),load_layouts(OUT/'exclusions.json'))
        warm=evaluate_task(tasks(pp['items'],ids[:1])[0],mz,'m27-fixture-warm')
        with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            for index in range(2):
                fixture_data=dict(data,new_layouts=[],generation=index);n=j.prepare(fixture_data,tasks(pp['items'],ids))
                reason=shared.run_stage(j,n,fixture_data,ex,fixture_config,start,[False])
                assert reason is None,reason;j.commit(n,j.state(),dict(no_selection=True))
        chain=j.verify_chain();cases=cases_from_manifest(mz);checker=Checker(cases)
        for index in range(2):
            stage_rows[index]={}
            for spec,blob,h in j.db.execute('select spec,result,result_hash from tasks where stage=? order by n',(index,)):
                assert hashed(blob)==h;receipt=unpacked(blob);calls+=receipt['calls'];candidate+=receipt['candidate_seconds'];cpu+=receipt['cpu_seconds']
                for e,r in zip(unpacked(spec),receipt['entries']):
                    for identity in e['aliases']:stage_rows[index][identity]=r['rows']
                    org=organism(e['model'])
                    for row in r['rows']:
                        checker.row(row);o=cases[row['case']];m=o.maze
                        assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;native+=1
                    if any(i.startswith('control/') for i in e['aliases']):assert all(row['optimal'] or row['no_path'] for row in r['rows'])
        usage=j.get('usage');j.close()
    result=build_summary(pp,dict(replay=data,fresh=data),dict(replay=stage_rows[0],fresh=stage_rows[1]),usage,chain,expected_primary=1)
    assert result==build_summary(pp,dict(replay=data,fresh=data),dict(replay=stage_rows[0],fresh=stage_rows[1]),usage,chain,expected_primary=1)
    writez(OUT/'fixture_summary.json.gz',result)
    regenerated=observed(lambda s,p:targeted(s,p,1),CONFIG['fixture_seed'],previous,RUN/'fixture_audit_generation_layouts.jsonl',generation_guard(config,start))
    assert set(regenerated['new_layouts'])==set(data['new_layouts'])
    assert regenerated['queries']['all']==ids[:28]
    assert [m for m in data['mazes'] if m['case_id'] not in extra]==regenerated['mazes']
    ensure(config,start)
    writej(OUT/'preflight.json',dict(status='PASS',new_scientific_cases=0,scientific_candidate_calls=0,
        fixture_inputs=len(ids),discarded_new_layouts=len(data['new_layouts']),fixture_calls=calls,warmup_calls=warm['calls'],
        fixture_candidate_seconds=candidate,fixture_worker_cpu_seconds=cpu,native_replays=native,wall_seconds=elapsed(start),
        rss_peak_bytes=shared._peak_rss,all_intact_controls_correct=True,generator_reproduced=True,summary_reproduced=True,
        all_fixture_rasters_independently_graded=True,journal_chain=chain,usage=usage))


def register():
    assert not (OUT/'registration.json').exists() and json.loads((OUT/'preflight.json').read_text())['status']=='PASS'
    reg=shared.source_manifest();paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/TRANSFER_RETENTION_M27.md',ROOT/'tests/test_transfer_retention_m27.py',ROOT/'tools/run_m27_workflow.py',M25/'completion.json',M26/'completion.json']
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    reg.update(phase='M27',scientific_calls=0,independent_cases_generated=False,pool_fixed_before_fresh=True)
    writej(OUT/'registration.json',reg)


def validate_panel(data,previous,fixture=False):
    ids=data['queries']['all'];assert len(ids)==len(set(ids))
    assert not set(data['new_layouts'])&set(previous)
    lookup={m['case_id']:m for m in data['mazes']};cases=cases_from_manifest([lookup[c] for c in ids])
    groups=defaultdict(list);target=Counter()
    for c in ids:
        m=data['metadata'][c];o=cases[c]
        assert lookup[c]['oracle_length']==len(o.path)
        if m['family'] in ('ordinary_perfect','ordinary_random'):
            groups[m['base']].append(c)
            if m['panel_group']=='targeted':
                lo,hi=map(int,m['target_stratum'].split('/')[-1].split('-'));assert lo<=len(o.path)-1<=hi
                if m['family']=='ordinary_random':assert component_cycles(o.maze)>=1
    for b,cs in groups.items():
        assert len(cs)==2 and {data['metadata'][c]['pose'] for c in cs}=={0,4}
        assert len({len(cases[c].path) for c in cs})==1
        if data['metadata'][cs[0]]['panel_group']=='targeted':target[data['metadata'][cs[0]]['target_stratum']]+=1
    if not fixture:
        assert len(ids)==2128 and len(groups)==480
        assert target==Counter({f'{f}/{n}/{lo}-{hi}':16 for f,n,lo,hi in STRATA})
    return dict(inputs=len(ids),ordinary_bases=len(groups),target_strata=dict(target))


def run():
    config=check();pushed(OUT/'registration.json');start=clock();assert not (RUN/'evaluation/campaign.sqlite').exists()
    pool=readz(OUT/'pool.json.gz');previous=load_layouts(OUT/'exclusions.json')
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    directory=RUN/'evaluation';phase_usage={};reason=None
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(pool_sha256=sha(OUT/'pool.json.gz'),no_evolution=True),previous)
        try:
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
                for index,name in enumerate(('replay','fresh')):
                    ensure(config,start)
                    if name=='replay':data=readz(OUT/'replay_panel.json.gz')
                    else:
                        data=fresh(config['fresh_seed'],previous,RUN/'science_generation_layouts.jsonl',generation_guard(config,start))
                        validation=validate_panel(data,previous);writej(OUT/'panel_validation.json',validation)
                        assert set(data['new_layouts'])==observed_hashes(RUN/'science_generation_layouts.jsonl')
                        assert not (OUT/'fresh_panel.json.gz').exists();writez(OUT/'fresh_panel.json.gz',data)
                    specs=tasks(pool['items'],data['queries']['all']);n=j.prepare(data,specs);before=j.get('usage');phase_start=elapsed(start)
                    reason=shared.run_stage(j,n,data,ex,config,start,[False])
                    if reason:raise RuntimeError('M27 science stopped: '+reason)
                    ensure(config,start);j.commit(n,j.state(),dict(no_selection=True,panel=name))
                    phase_usage[name]=dict(usage={k:j.get('usage')[k]-before[k] for k in before},wall_seconds=elapsed(start)-phase_start,
                                            aliases=len(pool['items']),physical_models=sum(map(len,specs)),logical_queries=len(pool['items'])*len(data['queries']['all']))
                    print(json.dumps(dict(phase=name,usage=j.get('usage'),wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss)),flush=True)
            assert j.get('latest')==1 and not j.pending();ensure(config,start)
            writej(OUT/'session.json',dict(status='complete',reason=None,usage=j.get('usage'),panels=phase_usage,
                wall_seconds=elapsed(start),monotonic_seconds=time.monotonic()-start[0],calendar_seconds=time.time()-start[1],
                rss_peak_bytes=shared._peak_rss,chain=j.verify_chain()))
        finally:j.close()


def load():
    con=sqlite3.connect(f'file:{RUN}/evaluation/campaign.sqlite?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
    j=Journal.__new__(Journal);j.db=con;j.directory=RUN/'evaluation';chain=j.verify_chain()
    assert not j.pending() and j.get('latest')==1
    rows={};models={};panels={}
    for n,name in enumerate(('replay','fresh')):
        inp=con.execute('select input from stages where n=? and complete=1',(n,)).fetchone();assert inp
        panels[name]=unpacked(inp[0]);rows[name]={};models[name]=[]
        for spec,blob,h in con.execute('select spec,result,result_hash from tasks where stage=? order by n',(n,)):
            assert hashed(blob)==h;ss=unpacked(spec);rr=unpacked(blob)['entries'];assert len(ss)==len(rr)
            for e,r in zip(ss,rr):
                assert e['aliases']==r['aliases'] and e['queries']==[x['case'] for x in r['rows']]
                for i in e['aliases']:assert i not in rows[name];rows[name][i]=r['rows']
                models[name].append((e,r))
    usage=j.get('usage');con.close();return panels,rows,models,usage,chain


def analyze():
    check();assert not (OUT/'summary.json').exists();panels,rows,models,usage,chain=load()
    summary=build_summary(readz(OUT/'pool.json.gz'),panels,rows,usage,chain)
    writej(OUT/'summary.json',summary)
    writez(OUT/'responses.json.gz',dict(panels={name:[dict(aliases=e['aliases'],rows=r['rows'],candidate_seconds=r['candidate_seconds'],work=r['work'],calls=r['calls']) for e,r in mm] for name,mm in models.items()}))
    print(json.dumps(summary['primary'],indent=2),flush=True)


def audit():
    config=check();assert not (OUT/'audit.json').exists();start=clock();ac=dict(config,session_wall_seconds=config['audit_wall_seconds'])
    panels,rows,models,usage,chain=load();pool=readz(OUT/'pool.json.gz');rebuilt,ancestry=make_pool()
    assert rebuilt==pool and ancestry==readz(OUT/'ancestry.json.gz')
    expected,original=replay_panel();assert expected==panels['replay']
    old_comparisons=0
    for (identity,cid),row in original.items():
        assert row==next(r for r in rows['replay'][identity] if r['case']==cid);old_comparisons+=1
    assert sum(len(c['witness_cases']) for c in pool['conditions'])==60
    previous=load_layouts(OUT/'exclusions.json')
    expected=fresh(config['fresh_seed'],previous,RUN/'audit_generation_layouts.jsonl',generation_guard(ac,start))
    assert canonical(expected)==panels['fresh'];validate_panel(expected,previous)
    assert observed_hashes(RUN/'audit_generation_layouts.jsonl')==set(expected['new_layouts'])
    calls=work=0;candidate=cpu=0.;tasks_verified=0;grades=0
    reserves=RUN/'audit_reservations.jsonl';receipts=RUN/'audit_receipts.jsonl';assert not reserves.exists() and not receipts.exists()
    with reserves.open('x') as reserved,receipts.open('x') as received:
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            for name in ('replay','fresh'):
                data=panels[name];ids=data['queries']['all'];mz=[m for m in data['mazes'] if m['case_id'] in set(ids)]
                cases=cases_from_manifest(mz);checker=Checker(cases);expected_tasks=tasks(pool['items'],ids)
                assert [e for task in expected_tasks for e in task]==[e for e,r in models[name]]
                lookup={hashed(packed(e)):r for e,r in models[name]};sizes={m['case_id']:m['w']*m['h'] for m in mz}
                pending={};todo=list(enumerate(expected_tasks));reserved_calls=0;reserved_work=0
                while todo or pending:
                    ensure(ac,start)
                    while todo and len(pending)<config['workers']:
                        k,spec=todo.pop(0);cc,ww=shared.reservation(spec,sizes)
                        assert calls+reserved_calls+cc<=config['call_cap'] and work+reserved_work+ww<=config['work_cap']
                        reserved.write(json.dumps(dict(panel=name,task=k,calls=cc,work=ww,spec_sha256=hashed(packed(spec))))+'\n');reserved.flush();os.fsync(reserved.fileno())
                        future=ex.submit(evaluate_task,spec,mz,'M27-audit/'+name);pending[future]=(k,spec,cc,ww);reserved_calls+=cc;reserved_work+=ww
                    done,_=wait(pending,timeout=1,return_when=FIRST_COMPLETED)
                    for future in done:
                        k,spec,cc,ww=pending.pop(future);rr=future.result();assert rr['calls']==cc and rr['work']<=ww
                        assert len(spec)==len(rr['entries'])
                        for e,actual in zip(spec,rr['entries']):
                            old=lookup[hashed(packed(e))]
                            assert actual['aliases']==old['aliases'] and actual['rows']==old['rows']
                            assert actual['calls']==old['calls'] and actual['work']==old['work']
                            for row in old['rows']:checker.row(row);grades+=1
                        calls+=rr['calls'];work+=rr['work'];candidate+=rr['candidate_seconds'];cpu+=rr['cpu_seconds']
                        reserved_calls-=cc;reserved_work-=ww;tasks_verified+=1
                        received.write(json.dumps(dict(panel=name,task=k,calls=cc,work=rr['work'],candidate_seconds=rr['candidate_seconds'],cpu_seconds=rr['cpu_seconds'],all_rows_exact=True))+'\n');received.flush();os.fsync(received.fileno())
                assert reserved_calls==reserved_work==0
    assert calls==grades==usage['calls'] and work==usage['work']
    for name in ('replay','fresh'):
        for identity in pool['control_ids']:assert all(r['optimal'] or r['no_path'] for r in rows[name][identity])
    from .baselines import baseline
    from .foundation_pair_confirm import normal_row
    baselines={};baseline_calls=0
    for name in ('replay','fresh'):
        ids=set(panels[name]['queries']['all']);cases=cases_from_manifest([m for m in panels[name]['mazes'] if m['case_id'] in ids]);checker=Checker(cases);baselines[name]={}
        for method in ('compiled_bfs','compiled_astar','wave_bit'):
            rs=[]
            for o in cases.values():
                m=o.maze;r=canonical(normal_row(baseline(method,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r)
                assert r['optimal'] or r['no_path'];rs.append(r);baseline_calls+=1
            baselines[name][method]=rs
    writez(OUT/'baselines.json.gz',baselines)
    assert build_summary(pool,panels,rows,usage,chain)==json.loads((OUT/'summary.json').read_text())
    ensure(ac,start);prior=prior_check()
    writej(OUT/'audit.json',dict(status='PASS',all_native_replays=calls,independent_grades=grades,counted_work=work,
        candidate_seconds=candidate,worker_cpu_seconds=cpu,original_saved_response_matches=old_comparisons,
        all_tasks_verified=tasks_verified,all_pool_ancestry_reconstructed=True,deterministic_corpus_reproduced=True,
        conventional_calls=baseline_calls,all_controls_correct=True,summary_recomputed=True,source_prior_hashes=prior,
        chain=chain,wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,
        limitation='Shared frozen VM/evaluator; independent raster grader, ALL-native replay, not a second VM or latency benchmark.'))
    print('M27 ALL-native audit PASS',calls,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','preflight','register','run','analyze','audit']);a=p.parse_args()
    try:globals()[a.action]()
    except BaseException:
        directory=OUT if OUT.exists() else ROOT/'results/transfer_retention_m27_preparation_failures'
        directory.mkdir(parents=True,exist_ok=True);path=directory/f'{a.action}_failure_{time.time_ns()}.json'
        with path.open('x') as f:json.dump(dict(action=a.action,traceback=traceback.format_exc()),f,indent=2)
        raise
