"""M29 registered development-only state interference and insulation assay."""
import argparse,hashlib,json,multiprocessing,os,shutil,sqlite3,time,traceback,zlib
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from pathlib import Path
import numpy as np
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import canonical,sha
from .deep_campaign_store import packed,unpacked,hashed,writer_lock
from . import deep_campaign as shared
from .connected_evolution import pushed
from .connected_evaluation import organism
from .connected_trace import respond as passive
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .connected_genome import Genome
from .state_dependency import dependencies,cone,sharing,cross_edges,divergence,digest
from .state_isolation_runtime import respond_pair,writer
from .transfer_retention import clock,elapsed

OUT=ROOT/'results/state_interference_m29'
RUN=ROOT/'runs/state_interference_m29'
PRIOR=ROOT/'results/integration_accessibility_m28'
CONFIG=dict(phase='M29',workers=10,session_wall_seconds=1200,audit_wall_seconds=1200,
    execution_cap=100000,work_cap=10**12,memory_bytes=8*2**30,storage_bytes=2*2**30,disk_free_floor_bytes=16*2**30,
    new_cases=0,evolution=False,diagnostic_banks=20,steps_per_bank=256,reads_per_site_per_bank=4096,dispatches_per_site_per_bank=32768)


def prior_check():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    for p,r in seal['local_records'].items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
    return dict(files=len(seal['files']),local_records=len(seal['local_records']),sha256=sha(PRIOR/'completion.json'))


def storage():return sum(p.stat().st_size for b in (OUT,RUN,ROOT/'results/state_interference_m29_preparation') for p in b.rglob('*') if p.is_file())


def ensure(config,started):
    assert elapsed(started)<config['session_wall_seconds'],'M29 wall guard'
    assert shared.process_resources()<config['memory_bytes'],'M29 memory guard'
    assert storage()<config['storage_bytes'],'M29 storage guard'
    assert shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes'],'M29 disk floor'


def check():
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(reg[k]==now[k] for k in ('python','dependencies'));prior_check()
    return json.loads((OUT/'config.json').read_text())


def make_sources():
    old=readz(PRIOR/'pool.json.gz');lookup={x['id']:x for x in old['items']};choices=readz(PRIOR/'choices.json.gz')
    focal=next(c for c in choices['choices'] if c['arm']=='regulated' and c['role']=='INTEGRATED')
    a,b=(focal['development'][k] for k in ('recipient','donor'));r=focal['id']
    pair_ids={i for p in old['pairs'] for i in p['parents']};models={i:lookup[i]['model'] for i in sorted(pair_ids|{a,b,r})}
    assert len(models)==16
    static={str(n):dict(**p,sharing=sharing(*(models[i] for i in p['parents'])),
        execution_dependencies={i:dependencies(models[i])[0] for i in p['parents']},
        output_cone={i:cone(dependencies(models[i],True)[0]) for i in p['parents']}) for n,p in enumerate(old['pairs'])}
    edges=cross_edges(models[a],models[b]);assert all(v['sharing']['within_instruction_cap'] for v in static.values())
    return canonical(dict(models=models,pairs=old['pairs'],focal=dict(recipient=a,donor=b,regulated=r,writer=6),
        target_bases=old['target_bases'],structural=static,coupling_edges=edges,source_ancestry_sha256=old['source_ancestry_sha256'],
        no_new_genomes=True,no_solver_output_selection=True))


def make_panel(sources):
    from .integration_accessibility import load as load28
    from .transfer_retention import load as load27
    data,rows,_,_,_=load28('final');a,b,r=(sources['focal'][k] for k in ('recipient','donor','regulated'))
    donor={x['case']:x for x in rows[b]};reg={x['case']:x for x in rows[r]}
    targets=set();labels=defaultdict(set)
    def choose(cid,label):targets.add(cid);labels[cid].add(label)
    for cid,m in data['metadata'].items():
        if m['family']=='corridor' and donor[cid]['optimal'] and not reg[cid]['optimal']:choose(cid,'all_donor_corridor_losses')
    assert sum('all_donor_corridor_losses' in x for x in labels.values())==28
    gains=json.loads((PRIOR/'structured_gain_analysis.json').read_text())['panels']['final']['details'][r]['new_individual_inputs']
    for x in gains:
        choose(x['case'],'all_new_single_fork_responses')
        for p in x['partners']:choose(p['case'],'all_failed_fork_counterparts')
    groups=defaultdict(list)
    for cid,m in data['metadata'].items():
        if m['family'] in ('disconnected','ordinary_disconnected'):groups[(m['family'],str(m.get('size','')))].append(cid)
    for cs in groups.values():choose(min(cs),'metadata_disconnection')
    for family in ('ordinary_perfect','ordinary_random'):
        base=min(m['base'] for m in data['metadata'].values() if m['family']==family and len(m['path'])-1>=16)
        for cid,m in data['metadata'].items():
            if m['family']==family and m['base']==base:choose(cid,'metadata_long_ordinary')
    manifest=[];meta={};expected={};target_cases=[]
    def add_phase(prefix,d,rs,ids,source_labels):
        lookup={m['case_id']:m for m in d['mazes']}
        for cid in sorted(ids):
            new=prefix+'/'+cid;m=dict(lookup[cid],case_id=new);manifest.append(m)
            meta[new]=dict(d['metadata'][cid],source_phase=prefix,original_case=cid,labels=sorted(source_labels[cid]))
            expected[new]={i:dict(next(x for x in rs[i] if x['case']==cid),case=new) for i in sources['models'] if i in rs}
        return [prefix+'/'+c for c in sorted(ids)]
    add_phase('M28_used',data,rows,targets,labels)
    del data,rows,reg,donor
    panels,rows,_,_,_=load27();data=panels['fresh'];ids=[c for c in data['queries']['all'] if data['metadata'][c]['base'] in sources['target_bases']]
    assert len(ids)==8
    target_cases=add_phase('M27_used',data,rows['fresh'],ids,defaultdict(lambda:{'all_four_complementary_bases'}))
    witness=panels['replay'];old=readz(ROOT/'results/transfer_retention_m27/pool.json.gz')
    win=next(c for c in old['conditions'] if c['original_max_novel_edges']==16)
    add_phase('M27_witness_used',witness,rows['replay'],win['witness_cases'],defaultdict(lambda:{'old_16edge_witness'}))
    assert len({m['case_id'] for m in manifest})==len(manifest)
    return canonical(dict(kind='development_diagnostics',mazes=manifest,metadata=meta,expected_source_rows=expected,
        queries={'all':sorted(meta),'targets':target_cases},new_layouts=[],all_previously_used=True,
        selection_rule='All four old complementary bases; ALL28 focal donor-corridor losses; ALL12 new fork inputs+ALL12 alternatives; first metadata case per disconnection family/size; first16+ordinary base per family both poses; old16edge witness both poses. Namespaces prevent same case ID across phases from aliasing different layouts.'))


def make_jobs(sources,data):
    jobs=[];targets=set(data['queries']['targets']);focalset=set(sources['focal'][k] for k in ('recipient','donor','regulated'))
    def add(phase,spec):jobs.append(dict(n=len(jobs),phase=phase,**spec))
    for i in sources['models']:
        for cid in data['queries']['all']:
            if cid in targets or i in focalset:add('native',dict(id='native/'+i+'/'+cid,model=i,case=cid))
    for p,pair in enumerate(sources['pairs']):
        for cid in sorted(targets):add('isolation',dict(id=f'isolation/{p}/'+cid,pair=p,parents=pair['parents'],case=cid,edge=None))
    focalparents=[sources['focal'][k] for k in ('recipient','donor')]
    for cid in data['queries']['all']:
        if cid not in targets:add('isolation',dict(id='isolation/focal/'+cid,pair='focal',parents=focalparents,case=cid,edge=None))
    for e,edge in enumerate(sources['coupling_edges']):
        for cid in sorted(targets):add('coupling',dict(id=f'coupling/{e}/'+cid,edge=edge,parents=focalparents,case=cid))
    for cid in data['queries']['all']:add('context',dict(id='context/'+cid,case=cid))
    return canonical(jobs)


def prepare():
    assert not OUT.exists();prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    sources=make_sources();data=make_panel(sources);jobs=make_jobs(sources,data)
    writej(OUT/'config.json',CONFIG);writez(OUT/'sources.json.gz',sources);writez(OUT/'cases.json.gz',data);writez(OUT/'jobs.json.gz',jobs)
    writej(OUT/'preparation.json',dict(prior=prior,source_models=len(sources['models']),pairs=len(sources['pairs']),
        cases=len(data['queries']['all']),target_cases=len(data['queries']['targets']),coupling_edges=len(sources['coupling_edges']),
        jobs_by_phase=dict(Counter(j['phase'] for j in jobs)),new_genomes=0,new_cases=0,new_scientific_executions=0,
        structural_widths=dict(Counter(x['sharing']['conservative_copy_width'] for x in sources['structural'].values()))))


def encode_history(h):
    raw=h.astype('<u2',copy=False).tobytes();return zlib.compress(raw,6),dict(history_shape=list(h.shape),history_sha256=hashlib.sha256(raw).hexdigest())


_worker={}
def init_worker(source_path,case_path,journal_path):
    shared.worker_init();sources=readz(source_path);data=readz(case_path);cases=cases_from_manifest(data['mazes'])
    global _worker
    _worker=dict(sources=sources,data=data,cases=cases,checker=Checker(cases),journal=str(journal_path),cache={})


def reference(i,cid):
    key=(i,cid)
    if key not in _worker['cache']:
        con=sqlite3.connect(f"file:{_worker['journal']}?mode=ro",uri=True);con.execute('PRAGMA query_only=ON')
        result,hblob=con.execute('select result,history from jobs where id=? and status=?',('native/'+i+'/'+cid,'done')).fetchone();con.close()
        r=unpacked(result);raw=zlib.decompress(hblob);assert hashlib.sha256(raw).hexdigest()==r['history_sha256']
        h=np.frombuffer(raw,dtype='<u2').reshape(r['history_shape']);_worker['cache'][key]=(r,h)
    return _worker['cache'][key]


def paired_comparison(reaction,h,bank,ref,history,o):
    row=record(reaction,o);_worker['checker'].row(row);steps=row['steps'];prefix=h[:steps+1,bank*10:bank*10+10]
    states=prefix.shape==history.shape and np.array_equal(prefix,history)
    frozen=bool(np.all(h[steps:,bank*10:bank*10+10]==h[steps,bank*10:bank*10+10]))
    return row,dict(all_native_fields_equal=row==ref['row'],full_native_history_equal=bool(states),
        state_frozen_after_own_stop=frozen,preserved=bool(states and frozen and row==ref['row']))


def evaluate(spec):
    start=time.perf_counter();cpu=time.process_time();sources=_worker['sources'];o=_worker['cases'][spec['case']];m=o.maze
    base=dict(id=spec['id'],phase=spec['phase'],case=spec['case']);blob=None;executions=work=0
    if spec['phase']=='native':
        model=sources['models'][spec['model']];org=organism(model)
        t=time.perf_counter();r=org.react(m.cells,m.w,m.h,m.start,m.goal);native_seconds=time.perf_counter()-t
        t=time.perf_counter();tr,h,allocation=passive(model,m);trace_seconds=time.perf_counter()-t
        row=record(r,o);assert record(tr,o)==row;_worker['checker'].row(row)
        old=_worker['data']['expected_source_rows'][spec['case']].get(spec['model'])
        if old is not None:assert old==row
        blob,info=encode_history(h);work=2*(row['reads']+row['dispatches']);executions=2
        base.update(row=row,model=spec['model'],**info,trace_allocation_bytes=allocation,prior_saved_row_match=old is not None,
                    native_seconds=native_seconds,trace_seconds=trace_seconds)
    elif spec['phase'] in ('isolation','coupling'):
        a,b=[sources['models'][i] for i in spec['parents']]
        rr,h,cost=respond_pair(a,b,m,spec['edge']);rows=[];comparisons=[]
        for bank,i in enumerate(spec['parents']):
            ref,native=reference(i,spec['case']);row,comparison=paired_comparison(rr[bank],h,bank,ref,native,o)
            rows.append(row);comparisons.append(comparison)
        if spec['phase']=='isolation':assert all(c['preserved'] for c in comparisons)
        else:assert comparisons[1-spec['edge'][0]]['preserved'],'Uncoupled donor bank must stay exact'
        base.update(rows=rows,comparisons=comparisons,history_sha256=digest(h),history_shape=list(h.shape),cost=cost)
        executions=1;work=cost['counted_work']
    else:
        assert spec['phase']=='context';f=sources['focal'];regref,rh=reference(f['regulated'],spec['case']);analyses=[]
        for role in ('recipient','donor'):
            identity=f[role];model=sources['models'][identity];ref,nh=reference(identity,spec['case']);common=min(len(nh),len(rh));first=None
            dependencies_used=dependencies(model)[0][f['writer']];verified=0
            for t in range(common-1):
                wanted,reads,dispatches=writer(model,m,nh[t],f['writer']);work+=reads+dispatches;executions+=1
                assert np.array_equal(wanted,nh[t+1,f['writer']]);verified+=1
                if first is not None:continue
                borrowed,reads,dispatches=writer(model,m,rh[t],f['writer']);work+=reads+dispatches;executions+=1
                if np.array_equal(wanted,borrowed):continue
                single=[]
                for channel in range(10):
                    patched=rh[t].copy();patched[channel]=nh[t,channel]
                    restored,reads,dispatches=writer(model,m,patched,f['writer']);work+=reads+dispatches;executions+=1
                    if np.array_equal(wanted,restored):single.append(channel)
                patched=rh[t].copy();patched[dependencies_used]=nh[t,dependencies_used]
                restored,reads,dispatches=writer(model,m,patched,f['writer']);work+=reads+dispatches;executions+=1
                assert np.array_equal(wanted,restored),'Structural input restoration positive control'
                full,reads,dispatches=writer(model,m,nh[t].copy(),f['writer']);work+=reads+dispatches;executions+=1
                assert np.array_equal(wanted,full)
                positions=np.flatnonzero(wanted!=borrowed);p=int(positions[0])
                first=dict(input_tick=t,output_tick=t+1,first_site=p,xy=[p%m.w,p//m.w],native_value=int(wanted[p]),
                    borrowed_value=int(borrowed[p]),different_sites=int(len(positions)),single_channel_exact_rescues=single,
                    all_execution_dependency_channels=dependencies_used,dependency_group_restores_exactly=True,
                    interpretation='Causal one-step writer-context intervention, not closed-loop path rescue.')
            analyses.append(dict(parent=identity,role=role,recorded_state_divergence=divergence(nh,rh),
                native_next_writer_checks=verified,first_context_sensitive_writer=first))
        base['analyses']=analyses
    base.update(executions=executions,counted_work=work,seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu)
    return canonical(base),blob


def reservation(spec,data):
    m=next(m for m in data['mazes'] if m['case_id']==spec['case']);n=m['w']*m['h']
    if spec['phase']=='context':return 1048,1048*n*156
    return 2 if spec['phase']=='native' else 1,2*n*(4096+32768)


def semantic(result):return {k:v for k,v in result.items() if not k.endswith('_seconds') and k!='seconds'}


def run_jobs(config,sources_path,cases_path,jobs,directory,started,fixture=False):
    directory.mkdir(parents=True,exist_ok=True);dbpath=directory/'campaign.sqlite';assert not dbpath.exists()
    data=readz(cases_path);con=sqlite3.connect(dbpath);con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=FULL')
    con.executescript('CREATE TABLE settings(key TEXT PRIMARY KEY,value BLOB); CREATE TABLE jobs(n INTEGER PRIMARY KEY,id TEXT UNIQUE,phase TEXT,spec BLOB,spec_hash TEXT,status TEXT,result BLOB,result_hash TEXT,history BLOB,history_hash TEXT);')
    with con:
        con.execute('insert into settings values(?,?)',('config',packed(config)))
        for j in jobs:con.execute('insert into jobs(n,id,phase,spec,spec_hash,status) values(?,?,?,?,?,?)',(j['n'],j['id'],j['phase'],packed(j),hashed(packed(j)),'new'))
    totals=dict(executions=0,counted_work=0,seconds=0.,cpu_seconds=0.);chain='0'*64;phase_records={}
    receipts=directory/'receipts.jsonl';reservations=directory/'reservations.jsonl'
    try:
        with receipts.open('x') as received,reservations.open('x') as reserved:
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=init_worker,
                initargs=(sources_path,cases_path,dbpath)) as ex:
                for phase in ('native','isolation','coupling','context'):
                    phase_start=elapsed(started);todo=[j for j in jobs if j['phase']==phase];pending={};re=rw=0
                    while todo or pending:
                        ensure(config,started)
                        while todo and len(pending)<config['workers']:
                            spec=todo.pop(0);ee,ww=reservation(spec,data)
                            assert totals['executions']+re+ee<=config['execution_cap'] and totals['counted_work']+rw+ww<=config['work_cap'],'M29 work reservation guard'
                            with con:con.execute("update jobs set status='started' where n=? and status='new'",(spec['n'],))
                            reserved.write(json.dumps(dict(n=spec['n'],executions=ee,work=ww,spec_sha256=hashed(packed(spec))))+'\n');reserved.flush();os.fsync(reserved.fileno())
                            f=ex.submit(evaluate,spec);pending[f]=(spec,ee,ww);re+=ee;rw+=ww
                        done,_=wait(pending,timeout=.5,return_when=FIRST_COMPLETED)
                        for f in done:
                            spec,ee,ww=pending.pop(f);result,blob=f.result();assert result['executions']<=ee and result['counted_work']<=ww
                            receipt=dict(n=spec['n'],result=result,history_compressed_sha256=hashed(blob) if blob else None)
                            received.write(json.dumps(receipt,sort_keys=True)+'\n');received.flush();os.fsync(received.fileno())
                            with con:con.execute("update jobs set status='done',result=?,result_hash=?,history=?,history_hash=? where n=? and status='started'",(packed(result),hashed(packed(result)),blob,hashed(blob) if blob else None,spec['n']))
                            for k in totals:totals[k]+=result[k]
                            re-=ee;rw-=ww
                    assert re==rw==0
                    stage=[(n,h) for n,h in con.execute('select n,result_hash from jobs where phase=? order by n',(phase,))]
                    chain=hashed(packed(dict(previous=chain,phase=phase,results=stage)));phase_records[phase]=dict(jobs=len(stage),wall_seconds=elapsed(started)-phase_start,chain=chain)
                    with con:con.execute('insert or replace into settings values(?,?)',('progress',packed(dict(totals=totals,phases=phase_records,chain=chain))))
                    print(json.dumps(dict(phase=phase,totals=totals,wall_seconds=elapsed(started),rss_peak_bytes=shared._peak_rss)),flush=True)
        assert con.execute("select count(*) from jobs where status!='done'").fetchone()[0]==0;ensure(config,started)
        return dict(status='PASS',totals=totals,phases=phase_records,chain=chain,wall_seconds=elapsed(started),rss_peak_bytes=shared._peak_rss,uncertain_attempts=0,fixture=fixture)
    finally:con.execute('PRAGMA wal_checkpoint(TRUNCATE)');con.close()


def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'preflight.json').exists()
    from tests.test_state_isolation_m29 import constant
    old=readz(ROOT/'results/transfer_retention_m27/discarded_fixture.json.gz');ids=old['queries']['all'][:2]
    data=dict(mazes=[m for m in old['mazes'] if m['case_id'] in ids],metadata={i:old['metadata'][i] for i in ids},
        queries={'all':ids,'targets':ids},expected_source_rows={i:{} for i in ids},new_layouts=[])
    sources=dict(models={'a':constant(1,True),'b':constant(0),'r':constant(1,True)},pairs=[dict(parents=['a','b'])],
        focal=dict(recipient='a',donor='b',regulated='r',writer=6),coupling_edges=[[0,2,2]])
    jobs=make_jobs(sources,data);writez(OUT/'fixture_sources.json.gz',sources);writez(OUT/'fixture_cases.json.gz',data);writez(OUT/'fixture_jobs.json.gz',jobs)
    start=clock();config=dict(CONFIG,workers=2,session_wall_seconds=300)
    with writer_lock(RUN/'fixture'):
        result=run_jobs(config,OUT/'fixture_sources.json.gz',OUT/'fixture_cases.json.gz',jobs,RUN/'fixture',start,True)
    writej(OUT/'preflight.json',result)
    source=RUN/'fixture/campaign.sqlite';writej(OUT/'preparation_local_records.json',{str(source.relative_to(ROOT)):dict(bytes=source.stat().st_size,sha256=sha(source))})


def register():
    assert not (OUT/'registration.json').exists() and json.loads((OUT/'preflight.json').read_text())['status']=='PASS'
    reg=shared.source_manifest();paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [p for p in (ROOT/'results/state_interference_m29_preparation').rglob('*') if p.is_file()]
    paths += [ROOT/'docs/STATE_INTERFERENCE_M29.md',ROOT/'tests/test_state_isolation_m29.py',ROOT/'tools/run_m29_workflow.py',PRIOR/'completion.json']
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});reg.update(phase='M29',development_only=True,new_cases=0,evolution=False)
    writej(OUT/'registration.json',reg)


def run():
    config=check();pushed(OUT/'registration.json');start=clock();sources=readz(OUT/'sources.json.gz');data=readz(OUT/'cases.json.gz');jobs=readz(OUT/'jobs.json.gz')
    assert sources==make_sources() and jobs==make_jobs(sources,data)
    with writer_lock(RUN/'evaluation'):
        result=run_jobs(config,OUT/'sources.json.gz',OUT/'cases.json.gz',jobs,RUN/'evaluation',start)
    writej(OUT/'session.json',result)


def read_records():
    con=sqlite3.connect(f'file:{RUN}/evaluation/campaign.sqlite?mode=ro',uri=True);con.execute('PRAGMA query_only=ON');con.execute('BEGIN');records=[]
    for n,spec,sh,status,result,rh,hblob,hh in con.execute('select n,spec,spec_hash,status,result,result_hash,history,history_hash from jobs order by n'):
        assert status=='done' and hashed(spec)==sh and hashed(result)==rh
        if hblob:assert hashed(hblob)==hh
        records.append((unpacked(spec),unpacked(result),hblob))
    con.close();return records


def summarize(sources,records):
    native=[r for s,r,h in records if s['phase']=='native'];isolated=[r for s,r,h in records if s['phase']=='isolation'];coupled=[(s,r) for s,r,h in records if s['phase']=='coupling'];context=[r for s,r,h in records if s['phase']=='context']
    grouped=defaultdict(list)
    for spec,r in coupled:grouped[str(spec['edge'])].append(r)
    channels=Counter();context_summary={}
    for role in ('recipient','donor'):
        aa=[a for r in context for a in r['analyses'] if a['role']==role];sensitive=[a for a in aa if a['first_context_sensitive_writer']]
        for a in sensitive:channels.update(a['first_context_sensitive_writer']['single_channel_exact_rescues'])
        context_summary[role]=dict(cases=len(aa),state_divergence_cases=sum(a['recorded_state_divergence']['first_tick'] is not None for a in aa),
            context_sensitive_writer_cases=len(sensitive),one_channel_rescuable_cases=sum(bool(a['first_context_sensitive_writer']['single_channel_exact_rescues']) for a in sensitive),
            native_writer_next_tick_checks=sum(a['native_next_writer_checks'] for a in aa),
            dependency_group_exact_rescue_cases=sum(a['first_context_sensitive_writer']['dependency_group_restores_exactly'] for a in sensitive))
    return canonical(dict(development_only=True,new_cases=0,new_evolution=0,native=dict(executions=len(native),saved_row_matches=sum(r['prior_saved_row_match'] for r in native),
        all_native_trace_exact=True),isolation=dict(pair_executions=len(isolated),bank_comparisons=2*len(isolated),
        all_native_fields_and_state_histories_equal=all(c['preserved'] for r in isolated for c in r['comparisons']),
        max_pair_array_bytes=max(r['cost']['array_bytes_excluding_history'] for r in isolated),max_trace_allocation_bytes=max(r['cost']['trace_allocation_bytes'] for r in isolated),
        counted_work=sum(r['counted_work'] for r in isolated)),
        coupling=dict(edges=len(grouped),pair_executions=len(coupled),receiver_history_changed=sum(not r['comparisons'][s['edge'][0]]['full_native_history_equal'] for s,r in coupled),
            receiver_terminal_fields_changed=sum(not r['comparisons'][s['edge'][0]]['all_native_fields_equal'] for s,r in coupled),
            all_uncoupled_donor_banks_exact=all(r['comparisons'][1-s['edge'][0]]['preserved'] for s,r in coupled),
            edges_preserving_both_on_all_cases=[e for e,rr in grouped.items() if all(c['preserved'] for r in rr for c in r['comparisons'])]),
        contexts=context_summary,single_rescue_channel_presentations=dict(channels),
        structural_widths=dict(Counter(x['sharing']['conservative_copy_width'] for x in sources['structural'].values())),
        limitations='Diagnostic20-channel banks, independent clocks/caps and TWO internal rasters; not a combined evolved solver or independent confirmation. One-step restored parent states are diagnostic interventions, never breeding/inference inputs. Static width is sufficient, not a lower bound.'))


def analyze():
    check();assert not (OUT/'summary.json').exists();sources=readz(OUT/'sources.json.gz');records=read_records()
    writej(OUT/'summary.json',summarize(sources,records));writez(OUT/'mechanism_records.json.gz',[dict(spec=s,result=r) for s,r,h in records])


def audit():
    config=dict(check(),session_wall_seconds=CONFIG['audit_wall_seconds']);assert not (OUT/'audit.json').exists();start=clock()
    sources=readz(OUT/'sources.json.gz');data=readz(OUT/'cases.json.gz');jobs=readz(OUT/'jobs.json.gz');records=read_records()
    assert make_sources()==sources and make_panel(sources)==data and make_jobs(sources,data)==jobs
    assert [s for s,r,h in records]==jobs and summarize(sources,records)==json.loads((OUT/'summary.json').read_text())
    lookup={s['id']:(r,h) for s,r,h in records};totals=dict(executions=0,counted_work=0,seconds=0.,cpu_seconds=0.);count=0
    with (RUN/'audit_reservations.jsonl').open('x') as reserved,(RUN/'audit_receipts.jsonl').open('x') as received:
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=init_worker,
            initargs=(OUT/'sources.json.gz',OUT/'cases.json.gz',RUN/'evaluation/campaign.sqlite')) as ex:
            pending={};todo=list(jobs);re=rw=0
            while todo or pending:
                ensure(config,start)
                while todo and len(pending)<config['workers']:
                    s=todo.pop(0);ee,ww=reservation(s,data);assert totals['executions']+re+ee<=config['execution_cap'] and totals['counted_work']+rw+ww<=config['work_cap']
                    reserved.write(json.dumps(dict(n=s['n'],executions=ee,work=ww))+'\n');reserved.flush();os.fsync(reserved.fileno())
                    f=ex.submit(evaluate,s);pending[f]=(s,ee,ww);re+=ee;rw+=ww
                done,_=wait(pending,timeout=.5,return_when=FIRST_COMPLETED)
                for f in done:
                    s,ee,ww=pending.pop(f);actual,h=f.result();old,oldh=lookup[s['id']]
                    assert semantic(actual)==semantic(old) and h==oldh,s['id'];assert actual['executions']<=ee and actual['counted_work']<=ww
                    for k in totals:totals[k]+=actual[k]
                    received.write(json.dumps(dict(n=s['n'],semantic_exact=True,history_exact=h==oldh,executions=actual['executions'],work=actual['counted_work']))+'\n');received.flush();os.fsync(received.fileno());re-=ee;rw-=ww;count+=1
            assert re==rw==0
    session=json.loads((OUT/'session.json').read_text());assert totals['executions']==session['totals']['executions'] and totals['counted_work']==session['totals']['counted_work']
    ensure(config,start);writej(OUT/'audit.json',dict(status='PASS',all_jobs_replayed=count,totals=totals,wall_seconds=elapsed(start),rss_peak_bytes=shared._peak_rss,
        source_priors=prior_check(),all_source_corpus_jobs_summary_reconstructed=True,all_history_bytes_and_native_rows_exact=True,
        limitation='Same diagnostic interpreter replay plus comparison to frozen original M18 VM and independent raster grader. No new performance confirmation.'))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','preflight','register','run','analyze','audit']);a=p.parse_args()
    try:globals()[a.action]()
    except BaseException:
        directory=OUT if OUT.exists() else ROOT/'results/state_interference_m29_preparation';directory.mkdir(parents=True,exist_ok=True)
        with (directory/f'{a.action}_failure_{time.time_ns()}.json').open('x') as f:json.dump(dict(action=a.action,traceback=traceback.format_exc()),f,indent=2)
        raise


if __name__=='__main__':main()
