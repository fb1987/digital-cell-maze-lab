"""M28 fixed integration-accessibility assay. New related crosses, no evolution."""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import json,multiprocessing,os,random,shutil,sqlite3,subprocess,time,traceback
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import canonical,sha
from .deep_campaign_store import packed,unpacked,hashed,writer_lock
from .referenced_campaign_store import Journal,load_layouts,write_reference
from . import deep_campaign as shared
from .connected_evaluation import organism,evaluate_task
from .copy_specialization import tasks
from .connected_evolution import pushed
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .transfer_retention_data import fresh,observed_hashes
from .transfer_retention import clock,elapsed,validate_panel
from .transfer_retention_metrics import FIELDS,compare,gate,endpoint
from .breeding_allocation_metrics import capabilities_plus
from .integration_genome import Genome,ARMS,vary

OUT=ROOT/'results/integration_accessibility_m28'
RUN=ROOT/'runs/integration_accessibility_m28'
PRIOR=ROOT/'results/transfer_retention_m27'
CONFIG=dict(phase='M28',seed=2026102328,fresh_seed=2026102302,draws_per_direction=8,workers=10,
    session_wall_seconds=1200,final_wall_seconds=900,audit_wall_seconds=1800,
    call_cap=3000000,work_cap=10**14,memory_bytes=8*2**30,storage_bytes=6*2**30,
    disk_free_floor_bytes=16*2**30,layout_base_manifest='results/integration_accessibility_m28/exclusions.json')


def storage():
    return sum(p.stat().st_size for b in (RUN,OUT,ROOT/'results/integration_m28_preparation_failures') for p in b.rglob('*') if p.is_file())


def guard(directory,config,started):
    if elapsed(started)>=config['session_wall_seconds']:return 'wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
    if storage()>=config['storage_bytes']:return 'storage'


def ensure(config,started):assert guard(RUN,config,started) is None,'M28 resource guard'


def generation_guard(config,started):
    sampled=[0.]
    def check():
        assert elapsed(started)<config['session_wall_seconds'],'M28 generation wall guard'
        if time.monotonic()-sampled[0]>.5:ensure(config,started);sampled[0]=time.monotonic()
    return check


def prior_check():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    for p,r in seal['local_records'].items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
    return dict(files=len(seal['files']),local_records=len(seal['local_records']),sha256=sha(PRIOR/'completion.json'))


def check():
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(now[k]==reg[k] for k in ('python','dependencies'))
    prior_check();return json.loads((OUT/'config.json').read_text())


def parent_pairs():
    old=readz(PRIOR/'pool.json.gz');lookup={x['id']:x for x in old['items']}
    note=json.loads((PRIOR/'complementarity_note.json').read_text());models={};aliases=defaultdict(set);pairs={}
    for base in note['bases']:
        for side in ('0','4'):
            for i in base['identities_by_pose'][side]:
                g=Genome.from_dict(lookup[i]['model']['genome']);models[g.digest]=g;aliases[g.digest].add(i)
        for a in base['identities_by_pose']['0']:
            for b in base['identities_by_pose']['4']:
                key=tuple(sorted(Genome.from_dict(lookup[i]['model']['genome']).digest for i in (a,b)))
                pairs.setdefault(key,set()).add(base['base'])
    result=[]
    for key,bases in sorted(pairs.items()):
        result.append(dict(digests=list(key),parents=[min(aliases[k]) for k in key],complementary_development_bases=sorted(bases)))
    assert len(result)==38 and len(models)==15
    return old,result,models,{k:sorted(v) for k,v in aliases.items()},[x['base'] for x in note['bases']]


def make_pool():
    old,pairs,models,aliases,bases=parent_pairs();items=list(old['items']);conditions=[]
    oldconditions={c['id']:c for c in old['conditions']};ancestry=readz(PRIOR/'ancestry.json.gz')
    def lineage(i):
        cur=i
        while cur not in oldconditions:cur=ancestry[cur]['item']['parent'];assert cur
        c=oldconditions[cur];return [x for x in (c['root'],c['entry']) if x]
    for pi,pair in enumerate(pairs):
        for direction in range(2):
            a,b=pair['parents'][direction],pair['parents'][1-direction]
            ga=models[pair['digests'][direction]];gb=models[pair['digests'][1-direction]]
            for draw in range(CONFIG['draws_per_direction']):
                seed=CONFIG['seed']+pi*1000+direction*100+draw
                for arm in ARMS:
                    rng=random.Random(seed);child,event=vary(ga,gb,rng,arm)
                    i=f'm28/{arm}/pair{pi:02d}/direction{direction}/draw{draw}'
                    items.append(dict(id=i,model=dict(representation='connected',genome=child.to_dict()),roles=['M28_proposal',arm]))
                    conditions.append(dict(id=i,arm=arm,pair=pi,direction=direction,draw=draw,seed=seed,
                        recipient=a,donor=b,comparators=list(dict.fromkeys([a,b]+lineage(a)+lineage(b))),event=event,
                        rng_after=hashed(packed(rng.getstate())),positive_variation=not event['genotype_noop']))
    assert Counter(c['arm'] for c in conditions)=={a:608 for a in ARMS}
    return canonical(dict(items=sorted(items,key=lambda x:x['id']),conditions=conditions,pairs=pairs,parent_aliases=aliases,
        target_bases=bases,control_ids=old['control_ids'],historical_references=[i['id'] for i in old['items'] if i['id'] not in old['control_ids']],
        source_ancestry_sha256=sha(PRIOR/'ancestry.json.gz'),pool_rule='ALL38 complementary genotype pairs; both directions; eight draws; lexicographically first source alias per genotype; no response-dependent operator choices.',
        no_evolution=True,opportunity_matched=True,mutation_scope_and_material_differ=True))


def development_panel():
    data=readz(PRIOR/'fresh_panel.json.gz');replay=readz(PRIOR/'replay_panel.json.gz')
    _,_,_,_,target=parent_pairs();groups=defaultdict(lambda:defaultdict(list))
    for c in data['queries']['all']:
        m=data['metadata'][c];groups[m['family']][m['base']].append(c)
    chosen=set()
    for family,bb in sorted(groups.items()):
        strata=defaultdict(list)
        for b,cs in sorted(bb.items()):
            m=data['metadata'][cs[0]];strata[(str(m.get('size','')),m['length_bin'],m['panel_group'])].append(b)
        take=[]
        while len(take)<24 and any(strata.values()):
            for key in sorted(strata):
                if strata[key] and len(take)<24:take.append(strata[key].pop(0))
        chosen.update(c for b in take for c in bb[b])
    chosen.update(c for c in data['queries']['all'] if data['metadata'][c]['base'] in target)
    meta={c:data['metadata'][c] for c in chosen};mazes={m['case_id']:m for m in data['mazes'] if m['case_id'] in chosen}
    for c in replay['queries']['all']:meta[c]=dict(replay['metadata'][c],panel_group='reused_witness');mazes[c]=next(m for m in replay['mazes'] if m['case_id']==c)
    return canonical(dict(kind='assessment',generation=0,mazes=[mazes[c] for c in sorted(mazes)],metadata=meta,
        queries={'all':sorted(meta)},new_layouts=[],reused_development=True,
        rule='All four complementary bases, all22 old witnesses, plus24 bases per family round-robin by size/length-bin/panel-group; include all queried poses.'))


def prepare():
    assert not OUT.exists();prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    pool=make_pool();data=development_panel();writej(OUT/'config.json',CONFIG);writez(OUT/'pool.json.gz',pool);writez(OUT/'development_panel.json.gz',data)
    base=PRIOR/'whole_layout_exclusions.json';previous=load_layouts(base);write_reference(OUT/'exclusions.json',base,previous)
    physical=sum(map(len,tasks(pool['items'],[])));calls=physical*len(data['queries']['all']);assert calls<CONFIG['call_cap']
    writej(OUT/'preparation.json',dict(prior=prior,genotype_pairs=38,parent_genotypes=15,proposals_per_arm=608,
        aliases=len(pool['items']),physical_models=physical,development_inputs=len(data['queries']['all']),
        planned_development_calls=calls,nominees_per_arm=3,planned_final_call_upper_bound=217*2128,
        scientific_candidate_calls=0,fresh_cases_generated=0))


def capabilities(data,rows):
    meta={c:data['metadata'][c] for c in data['queries']['all']}
    return meta,{i:capabilities_plus(rs,meta) for i,rs in rows.items()}


def assess(pool,data,rows):
    meta,caps=capabilities(data,rows);fields=(*FIELDS,'success','false')
    union={k:set().union(*(caps[i][k] for i in pool['historical_references'])) for k in fields}
    details=[];targets=set(pool['target_bases']);a0=caps['m14/reference/anchor/0']
    for condition in pool['conditions']:
        i=condition['id']
        if i not in caps:continue
        c=caps[i];cc=[caps[p] for p in condition['comparators']]
        e=endpoint(c,cc,union,a0,meta,condition['positive_variation'])
        fractions=[len(c[k]&x[k])/len(x[k]) for x in cc for k in FIELDS if x[k]]
        details.append(dict(**condition,endpoint=e,known_complementary_complete=len(c['ordinary_bases']&targets),
            known_complementary_keys=sorted(c['ordinary_bases']&targets),retention_floor=min(fractions,default=1.),
            comparisons={p:compare(c,caps[p]) for p in condition['comparators']},metrics=c['summary'],
            correct_inputs=len(c['success']),correct_no_path=len(c['correct_no_path']),false_no_path=len(c['false']),
            work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows[i]),
            status_counts=dict(Counter(r['status'] for r in rows[i]))))
    return canonical(dict(conditions=details,queries=len(meta),reference_aliases=len(pool['historical_references']),
        controls_all_correct=all(all(r['optimal'] or r['no_path'] for r in rows[i]) for i in pool['control_ids']),
        usage_by_arm={arm:dict(proposals=sum(c['arm']==arm for c in details),
            changed=sum(c['arm']==arm and c['positive_variation'] for c in details),
            complete_known_positive=sum(c['arm']==arm and c['known_complementary_complete']>0 for c in details),
            gate_passes=sum(c['arm']==arm and c['endpoint']['gate']['passes'] for c in details),
            raw_fresh_positive=sum(c['arm']==arm and c['endpoint']['raw_novel_complete8']>0 for c in details)) for arm in ARMS}))


def nominate(pool,data,rows):
    assessed=assess(pool,data,rows);choices=[]
    for arm in ARMS:
        candidates=[x for x in assessed['conditions'] if x['arm']==arm]
        # All criteria use DEVELOPMENT only. A failed gate cannot earn the primary score.
        keys={
          'INTEGRATED':lambda x:(x['endpoint']['gate']['passes'],x['known_complementary_complete'],x['retention_floor'],x['endpoint']['raw_novel_complete8'],x['correct_inputs'],-x['work']),
          'COMPLEMENT':lambda x:(x['known_complementary_complete'],x['endpoint']['raw_novel_complete8'],x['retention_floor'],x['correct_inputs'],-x['work']),
          'RETENTION':lambda x:(x['endpoint']['gate']['passes'],x['retention_floor'],x['known_complementary_complete'],x['correct_inputs'],-x['work'])}
        for role,key in keys.items():
            selected=sorted(candidates,key=lambda x:x['id'])[0]
            for x in sorted(candidates,key=lambda x:x['id']):
                if key(x)>key(selected):selected=x
            choices.append(dict(arm=arm,role=role,id=selected['id'],development=selected))
    ids=set(x['id'] for x in choices)|set(pool['historical_references'])|set(pool['control_ids'])
    result=dict(choices=choices,items=[x for x in pool['items'] if x['id'] in ids],
        selection_panel_sha256=sha(OUT/'development_panel.json.gz'),fresh_cases_generated=False,
        primary='Exactly INTEGRATED role per arm. Final score gated novel complete ordinary8+ beyond ALL205 M27 comparison aliases. No role substitution.',
        control_ids=pool['control_ids'],historical_references=pool['historical_references'])
    return canonical(result),assessed


def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'preflight.json').exists()
    start=clock();data=readz(PRIOR/'discarded_fixture.json.gz');data=dict(data,new_layouts=[])
    ids=data['queries']['all'];pool=readz(OUT/'pool.json.gz');selected=[]
    for arm in ARMS:
        selected += [x for x in pool['items'] if x['id'].startswith('m28/'+arm+'/')][:2]
    selected += [x for x in pool['items'] if x['id'] in pool['control_ids']]
    specs=tasks(selected,ids);shared.evaluate_task=evaluate_task;shared.resource_reason=guard
    directory=RUN/'fixture';config=dict(CONFIG,session_wall_seconds=600)
    mz=[m for m in data['mazes'] if m['case_id'] in set(ids)];cases=cases_from_manifest(mz);checker=Checker(cases)
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(fixture=True),load_layouts(OUT/'exclusions.json'))
        warm=evaluate_task(specs[0][:1],mz,'m28-warm')
        with ProcessPoolExecutor(10,mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            n=j.prepare(data,specs);assert shared.run_stage(j,n,data,ex,config,start,[False]) is None
            j.commit(n,j.state(),dict(fixture=True))
        native=0
        for spec,blob in j.db.execute('select spec,result from tasks order by n'):
            for e,r in zip(unpacked(spec),unpacked(blob)['entries']):
                org=organism(e['model'])
                for row in r['rows']:
                    checker.row(row);o=cases[row['case']];m=o.maze;assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==row;native+=1
                if set(e['aliases'])&set(pool['control_ids']):assert all(r['optimal'] or r['no_path'] for r in r['rows'])
        usage=j.get('usage');chain=j.verify_chain();j.close()
    assert make_pool()==pool and development_panel()==readz(OUT/'development_panel.json.gz')
    # Exercise nomination and metrics on the saved full M27 records without new inference.
    from .transfer_retention import load as oldload
    panels,oldrows,_,_,_=oldload();meta=panels['fresh']['metadata']
    assert all(b in {meta[c]['base'] for c in panels['fresh']['queries']['all']} for b in pool['target_bases'])
    development=readz(OUT/'development_panel.json.gz');selected_ids=set(development['queries']['all']);mock={}
    for i in pool['historical_references']+pool['control_ids']:
        mock[i]=[r for name in ('replay','fresh') for r in oldrows[name][i] if r['case'] in selected_ids]
        assert len(mock[i])==len(selected_ids)
    for c in pool['conditions']:mock[c['id']]=mock[c['recipient']]
    chosen,result=nominate(pool,development,mock);again,repeated=nominate(pool,development,mock)
    assert chosen==again and result==repeated and len(chosen['choices'])==9
    writez(OUT/'discarded_nomination_fixture.json.gz',dict(choices=chosen,summary=result,scope='Artificial parent-response substitution; not candidate evidence.'))
    ensure(config,start)
    writej(OUT/'preflight.json',dict(status='PASS',fixture_inputs=len(ids),fixture_calls=usage['calls'],native_replays=native,
        warmup_calls=warm['calls'],usage=usage,chain=chain,wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,
        exact_pool_and_rng_reconstruction=True,development_selection_reproduced=True,all_controls_correct=True,
        new_layouts=0,scientific_calls=0,limitation='Discarded rehearsal on previously excluded fixture cases; ALL-native shared VM, independent grader.'))
    records={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*') if p.is_file() and p.suffix=='.sqlite'}
    writej(OUT/'preparation_local_records.json',records)


def register():
    assert not (OUT/'registration.json').exists() and json.loads((OUT/'preflight.json').read_text())['status']=='PASS'
    reg=shared.source_manifest();paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/INTEGRATION_ACCESSIBILITY_M28.md',ROOT/'tests/test_integration_m28.py',ROOT/'tools/run_m28_workflow.py',PRIOR/'completion.json']
    paths += [p for p in (ROOT/'results/integration_m28_preparation_failures').rglob('*') if p.is_file()]
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    reg.update(phase='M28',scientific_calls=0,pool_fixed_before_development=True,independent_cases_generated=False)
    writej(OUT/'registration.json',reg)


def stage_config(config,name,audit=False):
    return dict(config,session_wall_seconds=config['audit_wall_seconds'] if audit else config['final_wall_seconds'] if name=='final' else config['session_wall_seconds'])


def run_stage(name):
    config=stage_config(check(),name);pushed(OUT/'registration.json');start=clock()
    pool=readz(OUT/'pool.json.gz');previous=load_layouts(OUT/'exclusions.json');directory=RUN/name
    assert not (directory/'campaign.sqlite').exists()
    if name=='development':data=readz(OUT/'development_panel.json.gz');items=pool['items']
    else:
        pushed(OUT/'choices.json.gz');assert json.loads((OUT/'development_audit.json').read_text())['status']=='PASS'
        items=readz(OUT/'choices.json.gz')['items']
        data=fresh(config['fresh_seed'],previous,RUN/'science_generation_layouts.jsonl',generation_guard(config,start))
        validate_panel(data,previous);assert observed_hashes(RUN/'science_generation_layouts.jsonl')==set(data['new_layouts'])
        writez(OUT/'fresh_panel.json.gz',data)
    shared.evaluate_task=evaluate_task;shared.resource_reason=guard;specs=tasks(items,data['queries']['all'])
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(pool_sha256=sha(OUT/'pool.json.gz'),fixed_assay=True),previous)
        try:
            n=j.prepare(data,specs)
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
                reason=shared.run_stage(j,n,data,ex,config,start,[False])
                if reason:raise RuntimeError('M28 '+name+' stopped: '+reason)
            ensure(config,start);j.commit(n,j.state(),dict(panel=name,no_evolution=True))
            writej(OUT/(name+'_session.json'),dict(status='complete',reason=None,usage=j.get('usage'),wall_seconds=elapsed(start),
                rss_peak_bytes=shared._peak_rss,chain=j.verify_chain(),physical_models=sum(map(len,specs)),aliases=len(items),
                logical_queries=len(items)*len(data['queries']['all']),queries=len(data['queries']['all'])))
        finally:j.close()
    print(name,'complete',flush=True)


def load(name):
    directory=RUN/name;con=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON');con.execute('BEGIN');j=Journal.__new__(Journal);j.db=con;j.directory=directory
    chain=j.verify_chain();assert not j.pending() and j.get('latest')==0
    data=unpacked(con.execute('select input from stages where n=0 and complete=1').fetchone()[0]);rows={};models=[]
    for spec,blob,h in con.execute('select spec,result,result_hash from tasks order by n'):
        assert hashed(blob)==h;ss=unpacked(spec);rr=unpacked(blob)['entries'];assert len(ss)==len(rr)
        for e,r in zip(ss,rr):
            assert e['aliases']==r['aliases'] and e['queries']==[x['case'] for x in r['rows']]
            for i in e['aliases']:assert i not in rows;rows[i]=r['rows']
            models.append((e,r))
    usage=j.get('usage');con.close();return data,rows,models,usage,chain


def select():
    check();assert not (OUT/'choices.json.gz').exists();pool=readz(OUT/'pool.json.gz');data,rows,models,usage,chain=load('development')
    choices,result=nominate(pool,data,rows);writez(OUT/'choices.json.gz',choices);writez(OUT/'development_summary.json.gz',result)
    writez(OUT/'development_responses.json.gz',[dict(aliases=e['aliases'],**{k:r[k] for k in ('rows','calls','work','candidate_seconds')}) for e,r in models])
    print(json.dumps([dict(arm=x['arm'],role=x['role'],id=x['id'],known=x['development']['known_complementary_complete'],gate=x['development']['endpoint']['gate']) for x in choices['choices']],indent=2),flush=True)


def analyze():
    check();assert not (OUT/'summary.json').exists();pool=readz(OUT/'pool.json.gz');data,rows,models,usage,chain=load('final')
    result=assess(pool,data,rows);choices=readz(OUT/'choices.json.gz');lookup={c['id']:c for c in result['conditions']}
    chosen=[dict(arm=c['arm'],role=c['role'],id=c['id'],final=lookup[c['id']]) for c in choices['choices']]
    meta,caps=capabilities(data,rows);ordinary={m['base']:m for m in meta.values() if m['family'] in ('ordinary_perfect','ordinary_random')}
    strata={}
    for i,c in caps.items():
        bins=defaultdict(lambda:dict(total=0,correct=0))
        for b,m in ordinary.items():
            edges=len(m['path'])-1;key=f"{m['family']}/{m.get('size')}/"+('0-7' if edges<8 else '8-15' if edges<16 else '16plus')
            bins[key]['total']+=1;bins[key]['correct']+=b in c['ordinary_bases']
        strata[i]=dict(bins)
    union=set().union(*(caps[i]['ordinary_bases'] for i in pool['historical_references']))
    result.update(choices=chosen,primary={c['arm']:c['final']['endpoint']['primary_score'] for c in chosen if c['role']=='INTEGRATED'},
        interpretation_scope='Related finite fixed neighborhoods, three unequal-material one-opportunity grammars; no significance, sustained evolution, general-solving or speed claim.',
        usage=usage,chain=chain,ordinary_bases=len(ordinary),ordinary8_bases=sum(len(m['path'])-1>=8 for m in ordinary.values()),
        ordinary16_bases=sum(len(m['path'])-1>=16 for m in ordinary.values()),historical_complete8=len({b for b in union if len(ordinary[b]['path'])-1>=8}),
        all_model_metrics={i:c['summary'] for i,c in caps.items()},ordinary_length_strata=strata)
    writej(OUT/'summary.json',canonical(result))
    writez(OUT/'final_responses.json.gz',[dict(aliases=e['aliases'],**{k:r[k] for k in ('rows','calls','work','candidate_seconds')}) for e,r in models])
    print(json.dumps(result['primary']),flush=True)


def audit_stage(name):
    config=stage_config(check(),name,True);start=clock();path=OUT/(name+'_audit.json');assert not path.exists()
    pool=readz(OUT/'pool.json.gz');assert make_pool()==pool
    data,rows,models,usage,chain=load(name);previous=load_layouts(OUT/'exclusions.json')
    if name=='development':
        assert data==development_panel();choices,result=nominate(pool,data,rows)
        assert choices==readz(OUT/'choices.json.gz') and result==readz(OUT/'development_summary.json.gz');items=pool['items']
    else:
        pushed(OUT/'choices.json.gz');expected=fresh(config['fresh_seed'],previous,RUN/'audit_generation_layouts.jsonl',generation_guard(config,start))
        assert canonical(expected)==data;validate_panel(data,previous);assert observed_hashes(RUN/'audit_generation_layouts.jsonl')==set(data['new_layouts'])
        items=readz(OUT/'choices.json.gz')['items'];result=assess(pool,data,rows);saved=json.loads((OUT/'summary.json').read_text())
        assert all(saved[k]==v for k,v in result.items())
    expected_tasks=tasks(items,data['queries']['all']);assert [e for task in expected_tasks for e in task]==[e for e,r in models]
    ids=set(data['queries']['all']);mz=[m for m in data['mazes'] if m['case_id'] in ids];sizes={m['case_id']:m['w']*m['h'] for m in mz}
    cases=cases_from_manifest(mz);checker=Checker(cases);lookup={hashed(packed(e)):r for e,r in models}
    calls=work=grades=0;candidate=cpu=0.;reserves=RUN/(name+'_audit_reservations.jsonl');receipts=RUN/(name+'_audit_receipts.jsonl')
    with reserves.open('x') as reserved,receipts.open('x') as received:
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            pending={};todo=list(enumerate(expected_tasks));rc=rw=0
            while todo or pending:
                ensure(config,start)
                while todo and len(pending)<config['workers']:
                    k,spec=todo.pop(0);cc,ww=shared.reservation(spec,sizes)
                    assert calls+rc+cc<=config['call_cap'] and work+rw+ww<=config['work_cap']
                    reserved.write(json.dumps(dict(task=k,calls=cc,work=ww,spec_sha256=hashed(packed(spec))))+'\n');reserved.flush();os.fsync(reserved.fileno())
                    f=ex.submit(evaluate_task,spec,mz,'M28-audit/'+name);pending[f]=(k,spec,cc,ww);rc+=cc;rw+=ww
                done,_=wait(pending,timeout=1,return_when=FIRST_COMPLETED)
                for f in done:
                    k,spec,cc,ww=pending.pop(f);rr=f.result();assert rr['calls']==cc and rr['work']<=ww
                    for e,actual in zip(spec,rr['entries']):
                        old=lookup[hashed(packed(e))];assert actual['aliases']==old['aliases'] and actual['rows']==old['rows']
                        assert actual['calls']==old['calls'] and actual['work']==old['work']
                        for row in old['rows']:checker.row(row);grades+=1
                    calls+=cc;work+=rr['work'];candidate+=rr['candidate_seconds'];cpu+=rr['cpu_seconds'];rc-=cc;rw-=ww
                    received.write(json.dumps(dict(task=k,calls=cc,work=rr['work'],candidate_seconds=rr['candidate_seconds'],cpu_seconds=rr['cpu_seconds'],all_rows_exact=True))+'\n');received.flush();os.fsync(received.fileno())
            assert rc==rw==0
    assert calls==grades==usage['calls'] and work==usage['work']
    assert all(all(r['optimal'] or r['no_path'] for r in rows[i]) for i in pool['control_ids'])
    from .baselines import baseline
    from .foundation_pair_confirm import normal_row
    baseline_rows={};bc=0
    for method in ('compiled_bfs','compiled_astar','wave_bit'):
        rs=[]
        for o in cases.values():
            m=o.maze;r=canonical(normal_row(baseline(method,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];rs.append(r);bc+=1
        baseline_rows[method]=rs
    writez(OUT/(name+'_baselines.json.gz'),baseline_rows);ensure(config,start)
    writej(path,dict(status='PASS',all_native_replays=calls,independent_grades=grades,counted_work=work,
        candidate_seconds=candidate,worker_cpu_seconds=cpu,wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,
        all_pool_variation_rng_reconstructed=True,all_tasks_verified=True,all_controls_correct=True,conventional_calls=bc,
        nomination_replayed=name=='development',deterministic_corpus_reproduced=True,source_prior_hashes=prior_check(),chain=chain,
        limitation='Shared unchanged production VM; independent raster grader and ALL-native replay, not second VM or end-to-end latency benchmark.'))
    print('M28',name,'audit PASS',calls,flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','preflight','register','development','select','audit_development','final','analyze','audit_final']);a=p.parse_args()
    try:
        if a.action in ('development','final'):run_stage(a.action)
        elif a.action.startswith('audit_'):audit_stage(a.action[6:])
        else:globals()[a.action]()
    except BaseException:
        directory=OUT if OUT.exists() else ROOT/'results/integration_m28_preparation_failures';directory.mkdir(parents=True,exist_ok=True)
        with (directory/f'{a.action}_failure_{time.time_ns()}.json').open('x') as f:json.dump(dict(action=a.action,traceback=traceback.format_exc()),f,indent=2)
        raise


if __name__=='__main__':main()
