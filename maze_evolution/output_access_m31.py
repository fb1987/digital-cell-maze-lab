"""M31 finite output-interface mutation accessibility; unchanged M18 native VM."""
import argparse,base64,hashlib,json,multiprocessing,os,random,shutil,sqlite3,subprocess,time,traceback,zlib
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import canonical,sha
from .deep_campaign_store import packed,unpacked,hashed,writer_lock
from .referenced_campaign_store import Journal,load_layouts,write_reference
from . import deep_campaign as shared
from .connected_evolution import pushed
from .connected_evaluation import organism,evaluate_task
from .copy_specialization import tasks
from .connected_trace import respond as passive
from .state_interference import encode_history
from .foundation_study_verify_core import Checker
from .deep_campaign_data import cases_from_manifest
from .transfer_retention import clock,elapsed,validate_panel
from .transfer_retention_data import fresh,observed_hashes
from .output_access_genome_m31 import Genome,ARMS,vary
from .output_access_metrics_m31 import assess,assess_one,package,nominate,nominate_assessed,summarize,FIELDS
from .breeding_allocation_metrics import capabilities_plus
from .exposure_selection import record

OUT=ROOT/'results/output_access_m31';RUN=ROOT/'runs/output_access_m31';PREP=ROOT/'results/output_access_m31_preparation'
PRIOR=ROOT/'results/information_flow_m30'
CONFIG=dict(phase='M31',seed=2026102331,fresh_seed=20261023310,draws_per_parent=512,workers=10,
    session_wall_seconds=1800,final_wall_seconds=900,audit_wall_seconds=2400,trace_wall_seconds=1200,
    call_cap=5000000,work_cap=10**14,memory_bytes=8*2**30,storage_bytes=6*2**30,disk_free_floor_bytes=16*2**30,
    layout_base_manifest='results/output_access_m31/exclusions.json',evolution=False)

def storage():return sum(p.stat().st_size for b in (OUT,RUN,PREP) for p in b.rglob('*') if p.is_file())
def prior_check():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    for p,r in seal['local_records'].items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
    return dict(files=len(seal['files']),local_records=len(seal['local_records']),sha256=sha(PRIOR/'completion.json'))
def guard(directory,config,started):
    if elapsed(started)>=config['session_wall_seconds']:return 'wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if storage()>=config['storage_bytes']:return 'storage'
    if shutil.disk_usage(RUN).free<config['disk_free_floor_bytes']:return 'disk_free'
def ensure(config,started):assert guard(RUN,config,started) is None,'M31 resource guard'
def generation_guard(config,started):
    last=[0.]
    def check_guard():
        assert elapsed(started)<config['session_wall_seconds'],'M31 generation wall guard'
        if time.monotonic()-last[0]>.5:ensure(config,started);last[0]=time.monotonic()
    return check_guard
def check():
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(reg[k]==now[k] for k in ('python','dependencies'));prior_check()
    return json.loads((OUT/'config.json').read_text())

def make_sources():
    m30=readz(PRIOR/'sources.json.gz');old=readz(ROOT/'results/integration_accessibility_m28/choices.json.gz')
    ancestry=readz(ROOT/'results/transfer_retention_m27/ancestry.json.gz');conditions={c['id']:c for c in readz(ROOT/'results/transfer_retention_m27/pool.json.gz')['conditions']}
    def origins(identity):
        seen=[]
        while identity not in conditions:
            seen.append(identity);identity=ancestry[identity]['item']['parent'];assert identity
        c=conditions[identity];return [x for x in (c['root'],c['entry']) if x],seen+c['chain']
    parents={}
    for role,identity in m30['focal'].items():
        source_roles=('recipient','donor') if role=='regulated' else (role,)
        comparators=[];closure=set()
        for k in source_roles:
            cs,chain=origins(m30['focal'][k]);comparators+=cs;closure.update(chain)
        parents[role]=dict(id=identity,model=m30['models'][identity],comparators=list(dict.fromkeys([identity]+comparators)),
            inherited_ancestry=sorted(closure),M28_regulated_birth=role=='regulated',random_origin=True)
    items=old['items'];assert all(p['id'] in {i['id'] for i in items} for p in parents.values())
    return canonical(dict(parents=parents,references=items,control_ids=old['control_ids'],
        historical_references=sorted(i['id'] for i in items if i['id'] not in old['control_ids']),
        ancestry_sha256=sha(ROOT/'results/transfer_retention_m27/ancestry.json.gz'),M28_pool_sha256=sha(ROOT/'results/integration_accessibility_m28/pool.json.gz'),
        source_rule='Exact three M30 focal genomes. ALL208 M27 aliases plus ALL3 fixed M28 nominees as reference material; three known intact controls excluded from novelty and breeding.'))

def make_pool(sources=None,draws=None):
    sources=make_sources() if sources is None else sources;draws=CONFIG['draws_per_parent'] if draws is None else draws
    items=list(sources['references']);conditions=[]
    for index,(source,p) in enumerate(sources['parents'].items()):
        g=Genome.from_dict(p['model']['genome'])
        for draw in range(draws):
            seed=CONFIG['seed']+index*100000+draw
            for arm in ARMS:
                child,event=vary(g,seed,arm);identity=f'm31/{source}/{arm}/draw{draw:04d}'
                items.append(dict(id=identity,model=dict(representation='connected',genome=child.to_dict()),roles=['M31_proposal',source,arm]))
                conditions.append(dict(id=identity,source=source,arm=arm,parent=p['id'],comparators=p['comparators'],draw=draw,seed=seed,event=event,
                    M31_variation_opportunities=1,positive_M31_genotype_change=not event['genotype_noop']))
    return canonical(dict(items=sorted(items,key=lambda i:i['id']),conditions=conditions,parents=sources['parents'],
        historical_references=sources['historical_references'],control_ids=sources['control_ids'],no_multigeneration_search=True,draws_per_parent=draws))

def development_panel():
    legacy=readz(ROOT/'results/integration_accessibility_m28/development_panel.json.gz');flow=readz(PRIOR/'cases.json.gz')
    from .integration_accessibility import load as load28
    _,legacy_rows,_,_,_=load28('development');old={}
    con=sqlite3.connect(f'file:{ROOT}/runs/information_flow_m30/evaluation/campaign.sqlite?mode=ro',uri=True)
    for result, in con.execute("select result from jobs where phase='native'"):
        r=unpacked(result);old.setdefault(r['model'],{})[r['case']]=r['row']
    con.close();mazes=[];meta={};expected={};queries=[];refs={i['id'] for i in make_sources()['references']}
    for prefix,d,rows in (('legacy',legacy,{i:{r['case']:r for r in rs} for i,rs in legacy_rows.items() if i in refs}),('flow',flow,old)):
        lookup={m['case_id']:m for m in d['mazes']}
        for cid in d['queries']['all']:
            new=prefix+'/'+cid;queries.append(new);mazes.append(dict(lookup[cid],case_id=new));m=dict(d['metadata'][cid])
            for k in ('base','template'):
                if k in m:m[k]=prefix+'/'+m[k]
            m.update(original_case=cid,source_panel=prefix);meta[new]=m
            expected[new]={i:dict(rs[cid],case=new) for i,rs in rows.items() if cid in rs and i in refs}
    contrasts=[dict(c,id='flow/'+c['id'],a='flow/'+c['a'],b='flow/'+c['b']) for c in flow['contrasts']]
    assert len(queries)==811
    return canonical(dict(kind='assessment',generation=0,mazes=mazes,metadata=meta,queries={'all':queries},contrasts=contrasts,
        expected_source_rows=expected,new_layouts=[],all_development_cases_previously_used=True,selection='ALL454 M28 development inputs +ALL357 M30 inputs, namespaced; all aliases retained and charged.'))

def prepare():
    assert not OUT.exists();prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    sources=make_sources();pool=make_pool(sources);data=development_panel();physical=sum(map(len,tasks(pool['items'],[])))
    writej(OUT/'config.json',CONFIG);writez(OUT/'sources.json.gz',sources);writez(OUT/'pool.json.gz',pool);writez(OUT/'development_panel.json.gz',data)
    previous=load_layouts(PRIOR/'whole_layout_exclusions.json');write_reference(OUT/'exclusions.json',PRIOR/'whole_layout_exclusions.json',previous)
    calls=physical*len(data['queries']['all']);assert calls<CONFIG['call_cap']
    writej(OUT/'preparation.json',dict(prior=prior,parents=len(sources['parents']),reference_aliases=len(sources['references']),
        historical_noncontrol_aliases=len(sources['historical_references']),proposals=len(pool['conditions']),opportunities_per_arm=3*CONFIG['draws_per_parent'],
        aliases=len(pool['items']),physical_models=physical,development_inputs=811,nominal_proposal_queries_per_arm=3*CONFIG['draws_per_parent']*811,
        planned_actual_development_calls=calls,max_nomination_roles=27,planned_final_upper_bound=(len(sources['references'])+27)*2128,
        original_layouts=len(previous),scientific_calls=0,fresh_cases_generated=0))

def stage_config(config,name,audit=False):
    return dict(config,session_wall_seconds=config['audit_wall_seconds'] if audit else config['final_wall_seconds'] if name=='final' else config['trace_wall_seconds'] if name=='trace' else config['session_wall_seconds'])

def trace_items():
    choices=readz(OUT/'choices.json.gz');sources=readz(OUT/'sources.json.gz');wanted={c['id'] for c in choices['choices']}|{p['id'] for p in sources['parents'].values()}|{'control/intact_connected'}
    return [i for i in readz(OUT/'pool.json.gz')['items'] if i['id'] in wanted]
def trace_panel():
    d=readz(OUT/'development_panel.json.gz');ids=[c for c in d['queries']['all'] if c.startswith('flow/M30/')]
    assert len(ids)==288
    return dict(d,queries={'all':ids},mazes=[m for m in d['mazes'] if m['case_id'] in ids],metadata={i:d['metadata'][i] for i in ids},expected_source_rows={},new_layouts=[])

_trace_cache={}
def evaluate_trace(spec,maze_rows,data_hash):
    global _trace_cache
    if _trace_cache.get('hash')!=data_hash:
        cs=cases_from_manifest(maze_rows);_trace_cache=dict(hash=data_hash,cases=cs,checker=Checker(cs))
    start=time.process_time();entries=[];seconds=work=calls=0
    for entry in spec:
        rows=[];traces=[];sec=ww=0
        for cid in entry['queries']:
            o=_trace_cache['cases'][cid];t=time.perf_counter();r,h,allocation=passive(entry['model'],o.maze);dt=time.perf_counter()-t
            row=record(r,o);_trace_cache['checker'].row(row);blob,info=encode_history(h);rows.append(row)
            traces.append(dict(case=cid,**info,history_b64=base64.b64encode(blob).decode(),allocation_bytes=allocation))
            cost=row['reads']+row['dispatches'];sec+=dt;ww+=cost;calls+=1
        entries.append(dict(aliases=entry['aliases'],rows=rows,traces=traces,candidate_seconds=sec,work=ww,calls=len(rows)));seconds+=sec;work+=ww
    return dict(entries=entries,calls=calls,work=work,candidate_seconds=seconds,cpu_seconds=time.process_time()-start,independently_graded=calls)

def panel_stream(name):
    con=sqlite3.connect(f'file:{RUN}/{name}/campaign.sqlite?mode=ro',uri=True);con.execute('PRAGMA query_only=ON');con.execute('BEGIN')
    j=Journal.__new__(Journal);j.db=con;j.directory=RUN/name;chain=j.verify_chain();assert not j.pending() and j.get('latest')==0
    data=unpacked(con.execute('select input from stages where n=0 and complete=1').fetchone()[0]);usage=j.get('usage')
    return con,data,usage,chain
def entries(con):
    for spec,blob,h in con.execute('select spec,result,result_hash from tasks order by n'):
        assert hashed(blob)==h;s=unpacked(spec);r=unpacked(blob)
        for e,x in zip(s,r['entries']):
            assert e['aliases']==x['aliases'] and e['queries']==[row['case'] for row in x['rows']]
            yield e,x
def load(name):
    assert name!='development','Development analysis must stream bounded model batches'
    con,data,usage,chain=panel_stream(name);rows={};models=[]
    for e,r in entries(con):
        for i in e['aliases']:rows[i]=r['rows']
        models.append((e,r))
    con.close();return data,rows,models,usage,chain

def development_assessment():
    pool=readz(OUT/'pool.json.gz');con,data,usage,chain=panel_stream('development');meta={c:data['metadata'][c] for c in data['queries']['all']}
    reference=set(pool['historical_references'])|set(pool['control_ids']);caps={};control_ok=True;matches=0
    for e,r in entries(con):
        ids=reference&set(e['aliases'])
        if not ids:continue
        c=capabilities_plus(r['rows'],meta)
        for i in ids:
            caps[i]=c
            if i in pool['control_ids']:control_ok &= all(x['optimal'] or x['no_path'] for x in r['rows'])
            for row in r['rows']:
                expected=data['expected_source_rows'].get(row['case'],{}).get(i)
                if expected is not None:assert row==expected,(i,row['case']);matches+=1
    assert reference==set(caps) and control_ok
    union={k:set().union(*(caps[i][k] for i in pool['historical_references'])) for k in (*FIELDS,'success','false')};a0=caps['m14/reference/anchor/0'];conditions={c['id']:c for c in pool['conditions']};details=[]
    for e,r in entries(con):
        ids=set(e['aliases'])&set(conditions)
        if not ids:continue
        cap=capabilities_plus(r['rows'],meta)
        for i in sorted(ids):details.append(assess_one(conditions[i],cap,caps,union,a0,meta,data,r['rows']))
    con.close();answer=package(sorted(details,key=lambda c:c['id']),pool,meta,control_ok);answer['old_source_rows_exact']=matches
    return canonical(answer)

def select():
    check();assert not (OUT/'choices.json.gz').exists();pool=readz(OUT/'pool.json.gz');result=development_assessment();choices,_=nominate_assessed(pool,result)
    writez(OUT/'choices.json.gz',choices);writez(OUT/'development_summary.json.gz',result)
    print(json.dumps([dict(source=c['source'],arm=c['arm'],role=c['role'],id=c['id'],controlled=c['development']['controlled_route_pairs'],raw8=c['development']['endpoint']['raw_novel_complete8'],gate=c['development']['endpoint']['gate']['passes']) for c in choices['choices']]),flush=True)

def analyze():
    check();assert not (OUT/'summary.json').exists();data,rows,models,usage,chain=load('final');pool=readz(OUT/'pool.json.gz');choices=readz(OUT/'choices.json.gz')
    writej(OUT/'summary.json',summarize(pool,choices,data,rows,usage,chain));writez(OUT/'final_responses.json.gz',[dict(aliases=e['aliases'],**{k:r[k] for k in ('rows','calls','work','candidate_seconds')}) for e,r in models])

def register():
    assert not (OUT/'registration.json').exists() and json.loads((OUT/'preflight.json').read_text())['status']=='PASS'
    _,fixture_rows,_,_,_=load('fixture');sources=readz(OUT/'sources.json.gz')
    assert all(all(r['optimal'] or r['no_path'] for r in fixture_rows[i]) for i in sources['control_ids'])
    reg=shared.source_manifest();paths=[p for b in (OUT,PREP) for p in b.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/OUTPUT_ACCESS_M31.md',ROOT/'tests/test_output_access_m31.py',ROOT/'tools/run_m31_workflow.py',PRIOR/'completion.json']
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});reg.update(phase='M31',scientific_calls=0,fresh_cases_generated=False,evolution=False,preflight_all_intact_controls_correct=True)
    writej(OUT/'registration.json',reg)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','preflight','register','development','select','trace','audit_development','audit_trace','final','analyze','audit_final','analyze_trace']);a=p.parse_args()
    try:
        if a.action in ('development','trace','final'):run_stage(a.action)
        elif a.action.startswith('audit_'):audit_stage(a.action[6:])
        else:globals()[a.action]()
    except BaseException:
        directory=OUT if OUT.exists() else PREP;directory.mkdir(parents=True,exist_ok=True)
        writej(directory/f'{a.action}_failure_{time.time_ns()}.json',dict(action=a.action,traceback=traceback.format_exc()));raise

# Stage/audit and discarded-preflight implementations follow below.

def execute(items,data,directory,config,previous,started,fn=evaluate_task):
    shared.evaluate_task=fn;shared.resource_reason=guard;specs=tasks(items,data['queries']['all'])
    with writer_lock(directory):
        j=Journal(directory);j.initialize(config,dict(pool_sha256=sha(OUT/'pool.json.gz'),finite_assay=True),previous)
        try:
            n=j.prepare(data,specs)
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
                reason=shared.run_stage(j,n,data,ex,config,started,[False])
                if reason:raise RuntimeError('M31 stage stopped: '+reason)
            ensure(config,started);j.commit(n,j.state(),dict(no_evolution=True,stage=directory.name))
            return dict(status='complete',usage=j.get('usage'),wall_seconds=elapsed(started),rss_peak_bytes=shared._peak_rss,chain=j.verify_chain(),
                physical_models=sum(map(len,specs)),aliases=len(items),logical_queries=len(items)*len(data['queries']['all']),queries=len(data['queries']['all']))
        finally:j.close()

def run_stage(name):
    config=stage_config(check(),name);pushed(OUT/'registration.json');start=clock();pool=readz(OUT/'pool.json.gz');previous=load_layouts(OUT/'exclusions.json');directory=RUN/name
    assert not (directory/'campaign.sqlite').exists()
    if name=='development':data=readz(OUT/'development_panel.json.gz');items=pool['items']
    elif name=='trace':
        pushed(OUT/'choices.json.gz');assert json.loads((OUT/'development_audit.json').read_text())['status']=='PASS'
        data=trace_panel();items=trace_items()
    else:
        pushed(OUT/'choices.json.gz');assert json.loads((OUT/'trace_audit.json').read_text())['status']=='PASS'
        items=readz(OUT/'choices.json.gz')['items'];data=fresh(config['fresh_seed'],previous,RUN/'science_generation_layouts.jsonl',generation_guard(config,start))
        validate_panel(data,previous);assert observed_hashes(RUN/'science_generation_layouts.jsonl')==set(data['new_layouts']);writez(OUT/'fresh_panel.json.gz',data)
    result=execute(items,data,directory,config,previous,start,evaluate_trace if name=='trace' else evaluate_task)
    writej(OUT/(name+'_session.json'),result);print(name,'complete',json.dumps(result),flush=True)

def development_native_subset(wanted,ids):
    con,_,_,_=panel_stream('development');rows={}
    for e,r in entries(con):
        for i in set(e['aliases'])&wanted:rows[i]={x['case']:x for x in r['rows'] if x['case'] in ids}
    con.close();return rows

def audit_stage(name):
    config=stage_config(check(),name,True);start=clock();path=OUT/(name+'_audit.json');assert not path.exists()
    pool=readz(OUT/'pool.json.gz');assert make_pool()==pool;con,data,usage,chain=panel_stream(name);previous=load_layouts(OUT/'exclusions.json')
    if name=='development':
        assert data==development_panel();assessed=development_assessment();choices,_=nominate_assessed(pool,assessed)
        assert choices==readz(OUT/'choices.json.gz') and assessed==readz(OUT/'development_summary.json.gz');items=pool['items'];fn=evaluate_task
    elif name=='trace':
        assert data==trace_panel();items=trace_items();fn=evaluate_trace
    else:
        pushed(OUT/'choices.json.gz');expected=fresh(config['fresh_seed'],previous,RUN/'audit_generation_layouts.jsonl',generation_guard(config,start))
        assert canonical(expected)==data;validate_panel(data,previous);assert observed_hashes(RUN/'audit_generation_layouts.jsonl')==set(data['new_layouts'])
        items=readz(OUT/'choices.json.gz')['items'];dd,rows,_,uu,ch=load('final')
        assert summarize(pool,readz(OUT/'choices.json.gz'),dd,rows,uu,ch)==json.loads((OUT/'summary.json').read_text());del rows
        fn=evaluate_task
    specs=tasks(items,data['queries']['all']);assert [unpacked(b) for b, in con.execute('select spec from tasks order by n')]==specs
    lookup={hashed(packed(unpacked(b))):n for n,b in con.execute('select n,spec from tasks')};ids=set(data['queries']['all']);mz=[m for m in data['mazes'] if m['case_id'] in ids];sizes={m['case_id']:m['w']*m['h'] for m in mz}
    cases=cases_from_manifest(mz);checker=Checker(cases);old_native=development_native_subset({i['id'] for i in items},ids) if name=='trace' else None
    calls=work=grades=source_matches=0;candidate=cpu=0.;reserves=RUN/(name+'_audit_reservations.jsonl');receipts=RUN/(name+'_audit_receipts.jsonl')
    with reserves.open('x') as reserved,receipts.open('x') as received:
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
            todo=list(enumerate(specs));pending={};rc=rw=0
            while todo or pending:
                ensure(config,start)
                while todo and len(pending)<config['workers']:
                    k,spec=todo.pop(0);cc,ww=shared.reservation(spec,sizes)
                    assert calls+rc+cc<=config['call_cap'] and work+rw+ww<=config['work_cap']
                    reserved.write(json.dumps(dict(task=k,calls=cc,work=ww,spec_sha256=hashed(packed(spec))))+'\n');reserved.flush();os.fsync(reserved.fileno())
                    pending[ex.submit(fn,spec,mz,'M31-audit/'+name)]=(k,spec,cc,ww);rc+=cc;rw+=ww
                done,_=wait(pending,timeout=.5,return_when=FIRST_COMPLETED)
                for f in done:
                    k,spec,cc,ww=pending.pop(f);actual=f.result();assert actual['calls']==cc and actual['work']<=ww
                    n=lookup[hashed(packed(spec))];blob,h=con.execute('select result,result_hash from tasks where n=?',(n,)).fetchone();assert hashed(blob)==h;old=unpacked(blob)
                    for e,a,b in zip(spec,actual['entries'],old['entries']):
                        assert a['aliases']==b['aliases'] and a['rows']==b['rows'] and a['work']==b['work'] and a['calls']==b['calls']
                        if name=='trace':assert a['traces']==b['traces'],'ALL compressed history bytes and metadata must match'
                        for row in b['rows']:
                            checker.row(row);grades+=1
                            for i in e['aliases']:
                                expected=old_native[i][row['case']] if name=='trace' else data.get('expected_source_rows',{}).get(row['case'],{}).get(i)
                                if expected is not None:assert row==expected;(source_matches:=source_matches+1)
                            if set(e['aliases'])&set(pool['control_ids']):assert row['optimal'] or row['no_path']
                    assert actual['work']==old['work'];calls+=cc;work+=actual['work'];candidate+=actual['candidate_seconds'];cpu+=actual['cpu_seconds'];rc-=cc;rw-=ww
                    received.write(json.dumps(dict(task=k,calls=cc,work=actual['work'],candidate_seconds=actual['candidate_seconds'],cpu_seconds=actual['cpu_seconds'],all_rows_exact=True,trace_history_exact=name=='trace'))+'\n');received.flush();os.fsync(received.fileno())
            assert rc==rw==0
    con.close();assert calls==grades==usage['calls'] and work==usage['work']
    baselines=0
    if name!='trace':
        from .baselines import baseline
        from .foundation_pair_confirm import normal_row
        for method in ('compiled_bfs','compiled_astar','wave_bit'):
            for o in cases.values():
                m=o.maze;r=canonical(normal_row(baseline(method,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];baselines+=1
    ensure(config,start);writej(path,dict(status='PASS',all_native_replays=calls,independent_grades=grades,counted_work=work,source_saved_row_matches=source_matches,
        candidate_seconds=candidate,worker_cpu_seconds=cpu,wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,chain=chain,
        all_pool_variation_rng_reconstructed=True,all_tasks_verified=True,all_controls_correct=True,conventional_calls=baselines,
        nomination_replayed=name=='development',deterministic_corpus_reproduced=True,source_prior_hashes=prior_check(),
        all_passive_history_bytes_exact=name=='trace',limitation='Same unchanged production VM plus passive copy and independent raster grader, not second independent full VM or latency benchmark.'))
    print(name,'audit PASS',calls,flush=True)

def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'preflight.json').exists();start=clock();sources=readz(OUT/'sources.json.gz');pool=make_pool(sources,2)
    fixture=readz(ROOT/'results/transfer_retention_m27/discarded_fixture.json.gz');ids=fixture['queries']['all'][:4]
    data=dict(fixture,queries={'all':ids},mazes=[m for m in fixture['mazes'] if m['case_id'] in ids],metadata={i:fixture['metadata'][i] for i in ids},new_layouts=[])
    previous=load_layouts(OUT/'exclusions.json');config=dict(CONFIG,workers=2,session_wall_seconds=600)
    native=execute(pool['items'],data,RUN/'fixture',config,previous,start)
    _,rows,_,_,_=load('fixture');choices,result=nominate(pool,data,rows);assert (choices,result)==nominate(pool,data,rows)
    samples=[i for i in pool['items'] if i['id'].startswith('m31/')][:3]+[i for i in pool['items'] if i['id']=='control/intact_connected']
    trace=execute(samples,data,RUN/'fixture_trace',config,previous,start,evaluate_trace)
    _,tr,_,_,_=load('fixture_trace')
    for i,rs in tr.items():assert rs==rows[i]
    writez(OUT/'preflight_choices.json.gz',choices);writej(OUT/'preflight.json',dict(status='PASS',scientific_calls=0,native=native,trace=trace,old_discarded_inputs=ids,
        nomination_replayed=True,all_trace_native_rows_match=True,prior_hashes=prior_check(),wall_seconds=elapsed(start)))
    writej(OUT/'preparation_local_records.json',{str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*.sqlite')})

def analyze_trace():
    check();assert not (OUT/'trace_summary.json').exists();assert json.loads((OUT/'trace_audit.json').read_text())['status']=='PASS'
    import numpy as np
    from .evaluator import distances
    data,rows,models,usage,chain=load('trace');cases=cases_from_manifest(data['mazes']);pool=readz(OUT/'pool.json.gz');conditions={c['id']:c for c in pool['conditions']}
    traces={i:{t['case']:t for t in r['traces']} for e,r in models for i in e['aliases']};details={};physical=len(models)
    def history(t):
        blob=base64.b64decode(t['history_b64']);raw=zlib.decompress(blob);assert hashlib.sha256(raw).hexdigest()==t['history_sha256']
        return np.frombuffer(raw,dtype='<u2').reshape(t['history_shape'])
    for i,tt in traces.items():
        counter=Counter();parent=conditions[i]['parent'] if i in conditions else None;case_details=[]
        for cid,t in tt.items():
            h=history(t);o=cases[cid];mask=h[:,2]>0;counter['presentations']+=1
            if parent:
                ph=history(traces[parent][cid]);end=min(len(h),len(ph));same=bool(np.array_equal(h[:end,[0,1,3,4,5,7]],ph[:end,[0,1,3,4,5,7]]));counter['parent_core_equal_common_windows']+=same
            if o.path:
                ds=distances(o.maze,o.maze.start);d=len(o.path)-1;allowed=np.array([a>=0 and b>=0 and a+b==d for a,b in zip(ds,o.to_goal)])
                bad=mask&~allowed[None,:];erasures=bad[:-1]&~mask[1:];counter['reachable']+=1;counter['ever_wrong_pixel']+=bool(np.any(bad));counter['erases_wrong_pixel']+=bool(np.any(erasures));counter['C2_positive_to_zero_events']+=int(np.count_nonzero(mask[:-1]&~mask[1:]));counter['terminal_wrong_pixels']+=int(np.count_nonzero(bad[-1]))
                counter['empty_terminal_output']+=not bool(np.any(mask[-1]));counter['correct_reachable']+=next(r['optimal'] for r in rows[i] if r['case']==cid)
                case_details.append(dict(case=cid,ever_wrong=bool(np.any(bad)),erases_wrong=bool(np.any(erasures)),terminal_wrong_pixels=int(np.count_nonzero(bad[-1])),empty=not bool(np.any(mask[-1]))))
        details[i]=dict(counts=dict(counter),parent=parent,cases=case_details)
    writej(OUT/'trace_summary.json',dict(frozen_nominees_only=True,development_not_confirmation=True,queries=288,physical_models=physical,aliases=len(traces),usage=usage,chain=chain,
        details=details,limitation='ALL nominated identities plus fixed sources/control, no re-selection. Erasure/empty-output changes alone do not imply a correct path or retained skills. Off-shortest means outside union of all shortest paths. Common windows end at earlier native stop.'))

if __name__=='__main__':main()
