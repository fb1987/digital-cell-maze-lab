"""M30 fixed causal information-flow diagnostics; no candidate or VM modification."""
import argparse,hashlib,json,multiprocessing,os,shutil,sqlite3,time,traceback,zlib
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from dataclasses import replace
from pathlib import Path
import numpy as np
from .state_interference import encode_history,semantic
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_confirmation import writej
from .routing_transfer import canonical,sha
from .deep_campaign_store import packed,unpacked,hashed,writer_lock
from . import deep_campaign as shared
from .connected_evolution import controls,pushed
from .connected_evaluation import organism
from .connected_trace import respond as passive
from .connected_genome import Genome
from .state_isolation_runtime import writer
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record
from .evaluator import Maze,Oracle
from .datasets import manifest
from .foundation_data import transform_maze,transform_point,layout_hash
from .transfer_retention import clock,elapsed

OUT=ROOT/'results/information_flow_m30'
RUN=ROOT/'runs/information_flow_m30'
PRIOR=ROOT/'results/state_interference_m29'
PREP=ROOT/'results/information_flow_m30_preparation'
PHASES=('native','contrast')
CONFIG=dict(phase='M30',workers=10,session_wall_seconds=1200,audit_wall_seconds=1200,
    execution_cap=100000,work_cap=10**12,memory_bytes=8*2**30,storage_bytes=2*2**30,
    disk_free_floor_bytes=16*2**30,sizes=[13,17,21],poses=list(range(8)),
    development_only=True,evolution=False,new_breeding_genomes=0)
EQUATIONS={
    'notation':'All RHS use PRE-tick values. bool is 0/1; sat=min(65535,x); nbr returns0 at wall/boundary; min+ ignores0 and returns0 if none. Open sites only. S/G are immutable source/goal flags. Directions W/E/N/S are absolute grid axes, not goal-relative.',
    'C0':'sat(C0 + max(0,C5-S))',
    'C1':'min+(four cardinal neighbors of C7)',
    'C2':'if C1==0 then0 else if S then C1 else sat(C2 + (bool(C0) XOR bool(C6) if C4 else0))',
    'C3':'if C1==0 then0 else if S then C1 else sat(C3 + max(0,C5-S))',
    'C4':'bool(C3 or G)',
    'C5':'min+(four cardinal neighbors of C0)',
    'C6_recipient':'if C0 and any cardinal neighbor C1>0 then nbr_E(C3) else nbr_N(C3)',
    'C6_donor':'nbr_W(C3)',
    'C6_regulated':'if C5 and nbr_W(C7)==0 and not G then C6_donor else C6_recipient',
    'C7':'sat(C1+C7)',
    'C8_recipient_regulated':'holds initial0 (inactive writer)',
    'C9_recipient_regulated':'G',
    'C8_donor':'sat(C0+1)',
    'C9_donor':'holds initial0 (inactive writer)',
    'limitation':'Algebraic output recurrence removes dead SSA nodes but does NOT remove their charged dispatch/read cost, stopping logic or budgets. No reduced solver is entered into evaluation/breeding.'}

def prior_check():
    seal=json.loads((PRIOR/'completion.json').read_text())
    for p,h in seal['files'].items():assert sha(ROOT/p)==h,p
    for p,r in seal['local_records'].items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
    return dict(files=len(seal['files']),local_records=len(seal['local_records']),sha256=sha(PRIOR/'completion.json'))

def storage():return sum(p.stat().st_size for b in (OUT,RUN,PREP) for p in b.rglob('*') if p.is_file())

def ensure(config,started):
    assert elapsed(started)<config['session_wall_seconds'],'M30 wall guard'
    assert shared.process_resources()<config['memory_bytes'],'M30 RSS guard'
    assert storage()<config['storage_bytes'],'M30 storage guard'
    assert shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes'],'M30 disk floor'

def check():
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(reg[k]==now[k] for k in ('python','dependencies'));prior_check()
    return json.loads((OUT/'config.json').read_text())

def make_sources():
    old=readz(PRIOR/'sources.json.gz');f=old['focal'];models={f[k]:old['models'][f[k]] for k in ('recipient','donor','regulated')}
    c=next(c for c in controls() if c['id']=='control/intact_connected');models[c['id']]={k:c[k] for k in ('representation','genome')}
    return canonical(dict(models=models,focal={k:f[k] for k in ('recipient','donor','regulated')},control=c['id'],equations=EQUATIONS,
        selection='Fixed M29 focal recipient/donor/regulated plus intact M18 external positive control; no model selection or new genotype.'))

def geometry(n,gate_y,variant):
    """Two long arms with remote gates. Never calls inference or stores an answer."""
    cells=bytearray(n*n);mid=n//2;top=3;bottom=n-4;left=2;right=n-3
    def put(x,y):cells[y*n+x]=1
    for x in range(left,right+1):put(x,top);put(x,bottom)
    for y in range(top,bottom+1):put(left,y);put(right,y)
    for y in range(1,top+1):put(mid,y)
    for y in range(bottom,n-1):put(mid,y)
    gates=[gate_y*n+left,gate_y*n+right]
    if variant in ('A','clutter0','clutter1','neither'):cells[gates[1]]=0
    if variant in ('B','neither'):cells[gates[0]]=0
    if variant=='clutter0':put(1,1)
    if variant=='clutter1':put(n-2,n-2)
    assert variant in ('A','B','both','neither','clutter0','clutter1')
    m=Maze(bytes(cells),n,n,(n-2)*n+mid,n+mid,'M30_controlled',2026102330,'development',f'M30/n{n}/gate{gate_y}/{variant}')
    junction=bottom*n+mid;observers=[junction,junction-1,junction+1,junction+n]
    return m,dict(junction=junction,observers=observers,gates=gates,source=m.start,goal=m.goal,variant=variant)

def make_panel():
    old=readz(PRIOR/'cases.json.gz');mazes=list(old['mazes']);meta={i:dict(m,used_M29=True) for i,m in old['metadata'].items()}
    con=sqlite3.connect(f'file:{ROOT}/runs/state_interference_m29/evaluation/campaign.sqlite?mode=ro',uri=True)
    expected=defaultdict(dict)
    for blob, in con.execute("select result from jobs where phase='native' and status='done'"):
        r=unpacked(blob);expected[r['case']][r['model']]=r['row']
    con.close()
    groups=[];generated=set();newids=[]
    for n in CONFIG['sizes']:
        for gy in (5,n-6):
            bypose=defaultdict(dict)
            for variant in ('A','B','both','neither','clutter0','clutter1'):
                base,info=geometry(n,gy,variant)
                for pose in CONFIG['poses']:
                    m=transform_maze(base,pose);o=Oracle.build(m);cid=m.case_id
                    assert bool(o.path)==(variant!='neither')
                    mazes+=manifest([o]);newids.append(cid);generated.add(layout_hash(m));b=dict(info)
                    for key in ('junction','source','goal'):b[key]=transform_point(info[key],n,pose)
                    for key in ('observers','gates'):b[key]=[transform_point(p,n,pose) for p in info[key]]
                    b.update(pose=pose,size=n,gate_y=gy,used_M29=False,path=o.path,cycle=variant=='both',family='controlled_'+variant)
                    meta[cid]=b;bypose[pose][variant]=cid
            for pose,ids in sorted(bypose.items()):
                for kind,a,b in (('route_swap','A','B'),('connectivity','both','neither'),('irrelevant','clutter0','clutter1')):
                    aa,bb=(next(x for x in mazes if x['case_id']==ids[v]) for v in (a,b));ca,cb=(bytes.fromhex(x['cells_hex']) for x in (aa,bb))
                    changed=[p for p in range(n*n) if ca[p]!=cb[p]];obs=meta[ids[a]]['observers']
                    distance=min(abs(p%n-q%n)+abs(p//n-q//n) for p in changed for q in obs)
                    assert distance>=3 and aa['start']==bb['start'] and aa['goal']==bb['goal']
                    assert all(ca[p]==cb[p]==1 for p in obs)
                    if kind!='connectivity':assert sum(ca)==sum(cb)
                    groups.append(dict(id=f'n{n}/gate{gy}/pose{pose}/{kind}',kind=kind,a=ids[a],b=ids[b],observers=obs,
                        changed_sites=changed,minimum_manhattan_to_observers=distance,equal_open_count=sum(ca)==sum(cb)))
    assert len(newids)==288 and len(groups)==144
    return canonical(dict(mazes=mazes,metadata=meta,queries=dict(old=old['queries']['all'],new=newids,all=old['queries']['all']+newids),
        contrasts=groups,expected_source_rows=dict(expected),generated_layouts=sorted(generated),new_inputs_are_used_development_not_confirmation=True,
        no_rejection_or_search=True,construction='All six fixed templates x six variants x eight poses. No favorable-case filtering; all proposed layouts and full orbits are recorded.'))

def neighbors_array(cells,n):
    count=len(cells);p=np.arange(count);out=np.stack((np.where(p%n,p-1,-1),np.where(p%n<n-1,p+1,-1),np.where(p>=n,p-n,-1),np.where(p+n<count,p+n,-1)))
    out=np.where((out>=0)&(cells[np.maximum(out,0)]>0),out,-1)
    return out

def recurrence(role,maze,state):
    """Independent vector algebra of executed output DAGs; not a candidate VM."""
    cells=np.frombuffer(maze.cells,np.uint8);q=neighbors_array(cells,maze.w);x=state.astype(np.int64);out=np.zeros_like(state)
    def nb(c,d):return np.where(q[d]>=0,x[c,np.maximum(q[d],0)],0)
    def mn(c):
        v=np.stack([nb(c,d) for d in range(4)]);v=np.where(v>0,v,65536);r=v.min(axis=0);return np.where(r==65536,0,r)
    s=np.zeros(len(cells),np.int64);g=s.copy();s[maze.start]=1;g[maze.goal]=1
    out[0]=np.minimum(65535,x[0]+np.maximum(0,x[5]-s))
    out[1]=mn(7)
    out[2]=np.where(x[1]>0,np.where(s,x[1],np.minimum(65535,x[2]+np.where(x[4]>0,(x[0]>0)!=(x[6]>0),0))),0)
    out[3]=np.where(x[1]>0,np.where(s,x[1],np.minimum(65535,x[3]+np.maximum(0,x[5]-s))),0)
    out[4]=(x[3]>0)|(g>0);out[5]=mn(0)
    recipient=np.where((x[0]>0)&(mn(1)>0),nb(3,1),nb(3,2))
    out[6]=nb(3,0) if role=='donor' else np.where((x[5]>0)&(nb(7,0)==0)&(g==0),nb(3,0),recipient) if role=='regulated' else recipient
    out[7]=np.minimum(65535,x[1]+x[7]);out[8]=np.minimum(65535,x[0]+1) if role=='donor' else x[8]
    out[9]=x[9] if role=='donor' else g
    out[:,cells==0]=0
    return out

def make_jobs(sources,data):
    jobs=[]
    def add(phase,**spec):jobs.append(dict(n=len(jobs),phase=phase,**spec))
    for role,i in sources['focal'].items():
        for cid in data['queries']['all']:add('native',id=f'native/{i}/{cid}',model=i,role=role,case=cid)
    for cid in data['queries']['new']:add('native',id=f'native/{sources["control"]}/{cid}',model=sources['control'],role='control',case=cid)
    for i in sources['models']:
        for c in data['contrasts']:add('contrast',id=f'contrast/{i}/{c["id"]}',model=i,role=next((k for k,v in sources['focal'].items() if v==i),'control'),contrast=c['id'],case=c['a'])
    return canonical(jobs)

def prepare():
    assert not OUT.exists();prior=prior_check();OUT.mkdir();RUN.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(RUN).free>=CONFIG['disk_free_floor_bytes']+CONFIG['storage_bytes']
    s=make_sources();d=make_panel();j=make_jobs(s,d)
    writej(OUT/'config.json',CONFIG);writez(OUT/'sources.json.gz',s);writez(OUT/'cases.json.gz',d);writez(OUT/'jobs.json.gz',j)
    writej(OUT/'equations.json',EQUATIONS)
    writej(OUT/'preparation.json',dict(prior=prior,models=len(s['models']),old_inputs=len(d['queries']['old']),new_inputs=len(d['queries']['new']),
        contrasts=len(d['contrasts']),jobs=dict(Counter(x['phase'] for x in j)),generated_layouts=len(d['generated_layouts']),scientific_executions=0))

_worker={}
def init_worker(source_path,case_path,journal_path):
    shared.worker_init();s=readz(source_path);d=readz(case_path);cases=cases_from_manifest(d['mazes'])
    global _worker
    _worker=dict(sources=s,data=d,cases=cases,checker=Checker(cases),journal=str(journal_path),cache={})

def reference(i,cid):
    key=(i,cid)
    if key not in _worker['cache']:
        con=sqlite3.connect(f'file:{_worker["journal"]}?mode=ro',uri=True)
        r,h=con.execute('select result,history from jobs where id=? and status=?',(f'native/{i}/{cid}','done')).fetchone();con.close();r=unpacked(r)
        h=np.frombuffer(zlib.decompress(h),dtype='<u2').reshape(r['history_shape']);assert hashlib.sha256(h.tobytes()).hexdigest()==r['history_sha256']
        _worker['cache'][key]=(r,h)
    return _worker['cache'][key]

def evaluate(spec):
    t=time.perf_counter();cpu=time.process_time();s=_worker['sources'];d=_worker['data'];model=s['models'][spec['model']];role=spec['role'];blob=None
    result=dict(id=spec['id'],phase=spec['phase'],model=spec['model'],role=role,case=spec['case']);work=executions=0
    if spec['phase']=='native':
        o=_worker['cases'][spec['case']];m=o.maze;org=organism(model)
        nt=time.perf_counter();r=org.react(m.cells,m.w,m.h,m.start,m.goal);native_seconds=time.perf_counter()-nt
        tr,h,allocation=passive(model,m);row=record(r,o);assert record(tr,o)==row;_worker['checker'].row(row)
        if role=='control':assert row['optimal'] or row['no_path'],'External intact positive control failed'
        verified=0
        if role!='control':
            for k in range(len(h)-1):assert np.array_equal(recurrence(role,m,h[k]),h[k+1]),(role,spec['case'],k)
            verified=(len(h)-1)*sum(m.cells)*10
        old=d.get('expected_source_rows',{}).get(spec['case'],{}).get(spec['model'])
        if old is not None:assert old==row
        blob,info=encode_history(h);executions=2;work=2*(row['reads']+row['dispatches'])
        result.update(row=row,**info,trace_allocation_bytes=allocation,native_seconds=native_seconds,recurrence_site_channel_checks=verified,prior_row_match=old is not None)
    else:
        c=next(x for x in d['contrasts'] if x['id']==spec['contrast']);ra,a=reference(spec['model'],c['a']);rb,b=reference(spec['model'],c['b']);common=min(len(a),len(b));obs=c['observers']
        m=_worker['cases'][c['a']].maze;mb=_worker['cases'][c['b']].maze
        sharedsites=(np.frombuffer(m.cells,np.uint8)>0)&(np.frombuffer(mb.cells,np.uint8)>0)
        first=[];rescues=[]
        for channel in range(10):
            changed=np.any(a[:common,channel,obs]!=b[:common,channel,obs],axis=1);where=np.flatnonzero(changed)
            first.append(int(where[0]) if len(where) else None)
        for channel in (2,6):
            when=first[channel]
            if when is None or when==0 or role=='control':continue
            tick=when-1;base=a[tick].copy();target=b[tick+1,channel,obs];original=a[tick+1,channel,obs];single=[];changed=[]
            # The changed wall pixels lie outside all observed radius-one footprints.
            # Swap only common open sites, never inject a route or alter candidate inference.
            for ch in range(10):
                patched=base.copy();patched[ch,sharedsites]=b[tick,ch,sharedsites]
                value,reads,dispatch=writer(model,m,patched,channel);executions+=1;work+=reads+dispatch
                expected=recurrence(role,m,patched)[channel];assert np.array_equal(value,expected)
                if not np.array_equal(value[obs],original):changed.append(ch)
                if np.array_equal(value[obs],target):single.append(ch)
            patched=base.copy();patched[:,sharedsites]=b[tick,:,sharedsites]
            value,reads,dispatch=writer(model,m,patched,channel);executions+=1;work+=reads+dispatch
            assert np.array_equal(value[obs],target),'Full local input restoration must reproduce partner observer output'
            rescues.append(dict(channel=channel,input_tick=tick,output_tick=when,single_channel_exact_partner_restorations=single,
                channels_changing_observer=changed,full_common_state_restores=True))
        rra,rrb=ra['row'],rb['row'];ja=d['metadata'][c['a']]['junction'];left,right=obs[1:3]
        # Fixed observer order is transformed with the maze, preserving arm identity.
        result.update(contrast=c['id'],kind=c['kind'],common_ticks=common-1,first_observer_difference_by_channel=first,
            intervention=rescues,observed_sites=obs,minimum_change_distance=c['minimum_manhattan_to_observers'],
            global_state_difference=bool(np.any(a[:common]!=b[:common])),
            a=dict(status=rra['status'],steps=rra['steps'],optimal=rra['optimal'],no_path=rra['no_path'],observer_C2_terminal=a[-1,2,obs].astype(int).tolist()),
            b=dict(status=rrb['status'],steps=rrb['steps'],optimal=rrb['optimal'],no_path=rrb['no_path'],observer_C2_terminal=b[-1,2,obs].astype(int).tolist()),
            complete_both=bool(rra['optimal'] and rrb['optimal']),
            positive_arms_a=[bool(a[-1,2,left]),bool(a[-1,2,right])],positive_arms_b=[bool(b[-1,2,left]),bool(b[-1,2,right])],
            same_terminal_output=bool(rra['mask']==rrb['mask']) if 'mask' in rra else bool(np.array_equal(a[-1,2]>0,b[-1,2]>0)),
            stopped_at_different_ticks=rra['steps']!=rrb['steps'])
        # One-step interventions count separately; reading saved histories is not inference.
    result.update(executions=executions,counted_work=work,seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu)
    return canonical(result),blob

def reservation(spec,data):
    m=next(x for x in data['mazes'] if x['case_id']==spec['case']);n=m['w']*m['h']
    return (2,2*n*(4096+32768)) if spec['phase']=='native' else (22,22*n*156)

def run_jobs(config,jobs,directory,started,audit_old=None):
    directory.mkdir(parents=True,exist_ok=True);db=RUN/'evaluation/campaign.sqlite' if audit_old else directory/'campaign.sqlite'
    con=None;chain='0'*64;totals=dict(executions=0,counted_work=0,seconds=0.,cpu_seconds=0.);phase_records={}
    if audit_old is None:
        assert not db.exists();con=sqlite3.connect(db);con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=FULL')
        con.executescript('CREATE TABLE settings(key TEXT PRIMARY KEY,value BLOB); CREATE TABLE jobs(n INTEGER PRIMARY KEY,id TEXT UNIQUE,phase TEXT,spec BLOB,spec_hash TEXT,status TEXT,result BLOB,result_hash TEXT,history BLOB,history_hash TEXT);')
        with con:
            con.execute('insert into settings values(?,?)',('config',packed(config)))
            for j in jobs:con.execute('insert into jobs(n,id,phase,spec,spec_hash,status) values(?,?,?,?,?,?)',(j['n'],j['id'],j['phase'],packed(j),hashed(packed(j)),'new'))
    data=readz(OUT/'cases.json.gz');count=0
    try:
        with (directory/'reservations.jsonl').open('x') as reserved,(directory/'receipts.jsonl').open('x') as received:
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=init_worker,
                initargs=(OUT/'sources.json.gz',OUT/'cases.json.gz',db)) as ex:
                for phase in PHASES:
                    begin=elapsed(started);todo=[j for j in jobs if j['phase']==phase];pending={};re=rw=0;hashes=[]
                    while todo or pending:
                        ensure(config,started)
                        while todo and len(pending)<config['workers']:
                            j=todo.pop(0);ee,ww=reservation(j,data)
                            assert totals['executions']+re+ee<=config['execution_cap'] and totals['counted_work']+rw+ww<=config['work_cap'],'M30 reservation guard'
                            if con:
                                with con:con.execute("update jobs set status='started' where n=?",(j['n'],))
                            reserved.write(json.dumps(dict(n=j['n'],executions=ee,work=ww,spec_sha256=hashed(packed(j))))+'\n');reserved.flush();os.fsync(reserved.fileno())
                            pending[ex.submit(evaluate,j)]=(j,ee,ww);re+=ee;rw+=ww
                        done,_=wait(pending,timeout=.5,return_when=FIRST_COMPLETED)
                        for f in done:
                            j,ee,ww=pending.pop(f);r,h=f.result();assert r['executions']<=ee and r['counted_work']<=ww
                            if audit_old:
                                old,oldh=audit_old[j['id']];assert semantic(r)==semantic(old) and h==oldh,j['id']
                            received.write(json.dumps(dict(n=j['n'],result=r,history_sha256=hashed(h) if h else None),sort_keys=True)+'\n');received.flush();os.fsync(received.fileno())
                            if con:
                                with con:con.execute("update jobs set status='done',result=?,result_hash=?,history=?,history_hash=? where n=?",(packed(r),hashed(packed(r)),h,hashed(h) if h else None,j['n']))
                            for k in totals:totals[k]+=r[k]
                            hashes.append((j['n'],hashed(packed(r if not audit_old else audit_old[j['id']][0]))));re-=ee;rw-=ww;count+=1
                    assert re==rw==0
                    chain=hashed(packed(dict(previous=chain,phase=phase,results=sorted(hashes))));phase_records[phase]=dict(jobs=len(hashes),wall_seconds=elapsed(started)-begin,chain=chain)
                    if con:
                        with con:con.execute('insert or replace into settings values(?,?)',('progress',packed(dict(totals=totals,phases=phase_records,chain=chain))))
                    print(json.dumps(dict(phase=phase,totals=totals,wall_seconds=elapsed(started))),flush=True)
        ensure(config,started)
        return dict(status='PASS',jobs=count,totals=totals,phases=phase_records,chain=chain,wall_seconds=elapsed(started),rss_peak_bytes=shared._peak_rss,uncertain_attempts=0)
    finally:
        if con:con.execute('PRAGMA wal_checkpoint(TRUNCATE)');con.close()

def read_records():
    con=sqlite3.connect(f'file:{RUN}/evaluation/campaign.sqlite?mode=ro',uri=True);records=[];chain='0'*64
    for n,s,sh,status,r,rh,h,hh in con.execute('select n,spec,spec_hash,status,result,result_hash,history,history_hash from jobs order by n'):
        assert status=='done' and hashed(s)==sh and hashed(r)==rh and (not h or hashed(h)==hh)
        records.append((unpacked(s),unpacked(r),h))
    progress=unpacked(con.execute("select value from settings where key='progress'").fetchone()[0]);con.close()
    for phase in PHASES:
        chain=hashed(packed(dict(previous=chain,phase=phase,results=[(s['n'],hashed(packed(r))) for s,r,h in records if s['phase']==phase])))
        assert chain==progress['phases'][phase]['chain']
    assert chain==json.loads((OUT/'session.json').read_text())['chain'];return records

def summarize(sources,data,records):
    native=[r for s,r,h in records if s['phase']=='native'];contrasts=[r for s,r,h in records if s['phase']=='contrast'];answer={}
    for role in (*sources['focal'],'control'):
        rr=[r for r in native if r['role']==role];cc=[r for r in contrasts if r['role']==role];per={}
        for kind in ('route_swap','connectivity','irrelevant'):
            cs=[c for c in cc if c['kind']==kind];per[kind]=dict(contrasts=len(cs),complete_both=sum(c['complete_both'] for c in cs),
                any_observer_signal=sum(any(t is not None for t in c['first_observer_difference_by_channel']) for c in cs),
                C2_observer_signal=sum(c['first_observer_difference_by_channel'][2] is not None for c in cs),
                C6_observer_signal=sum(c['first_observer_difference_by_channel'][6] is not None for c in cs),
                same_terminal_output=sum(c['same_terminal_output'] for c in cs),different_stop_ticks=sum(c['stopped_at_different_ticks'] for c in cs),
                first_signal_histogram={str(ch):dict(Counter(str(c['first_observer_difference_by_channel'][ch]) for c in cs)) for ch in range(10)},
                single_channel_restoration_presentations={str(ch):dict(Counter(str(x) for c in cs for z in c['intervention'] if z['channel']==ch for x in z['single_channel_exact_partner_restorations'])) for ch in (2,6)})
        news=[r for r in rr if r['case'] in data['queries']['new']]
        answer[role]=dict(native_calls=len(rr),old_row_matches=sum(r['prior_row_match'] for r in rr),recurrence_checks=sum(r['recurrence_site_channel_checks'] for r in rr),
            new_by_variant={v:dict(inputs=len([r for r in news if data['metadata'][r['case']]['variant']==v]),
                optimal=sum(r['row']['optimal'] for r in news if data['metadata'][r['case']]['variant']==v),
                correct_no_path=sum(r['row']['no_path'] for r in news if data['metadata'][r['case']]['variant']==v),
                statuses=dict(Counter(r['row']['status'] for r in news if data['metadata'][r['case']]['variant']==v))) for v in ('A','B','both','neither','clutter0','clutter1')},contrasts=per)
    return canonical(dict(development_only=True,new_evolution=0,new_layout_inputs=len(data['queries']['new']),old_inputs=len(data['queries']['old']),
        all_native_trace_fields_exact=True,all_complete_tick_equations_exact=True,by_role=answer,
        intervention_count=sum(len(c['intervention']) for c in contrasts),
        limitations='Four fixed models on controlled development fixtures. Same VM/passive plus independent ten-channel vector recurrence; no independent full VM, holdout confirmation, selection, improved solver or speed claim. One-step state swaps are causal diagnostics, not full-trajectory/path rescue. Common windows stop at earliest native halt; cyclic/disconnected have unequal open counts; main swap and irrelevant controls equal counts.'))

def register():
    assert not (OUT/'registration.json').exists();assert json.loads((PREP/'tests.json').read_text())['status']=='PASS'
    reg=shared.source_manifest();paths=[p for b in (OUT,PREP) for p in b.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/INFORMATION_FLOW_M30.md',ROOT/'tests/test_information_flow_m30.py',ROOT/'tools/run_m30_workflow.py',PRIOR/'completion.json']
    reg['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths});reg.update(phase='M30',development_only=True,evolution=False)
    writej(OUT/'registration.json',reg)

def run():
    config=check();pushed(OUT/'registration.json');start=clock();s=readz(OUT/'sources.json.gz');d=readz(OUT/'cases.json.gz');j=readz(OUT/'jobs.json.gz')
    assert s==make_sources() and d==make_panel() and j==make_jobs(s,d)
    with writer_lock(RUN/'evaluation'):session=run_jobs(config,j,RUN/'evaluation',start)
    writej(OUT/'session.json',session)

def analyze():
    check();assert not (OUT/'summary.json').exists();records=read_records();s=readz(OUT/'sources.json.gz');d=readz(OUT/'cases.json.gz')
    writej(OUT/'summary.json',summarize(s,d,records));writez(OUT/'mechanism_records.json.gz',[dict(spec=s,result=r) for s,r,h in records])

def audit():
    config=dict(check(),session_wall_seconds=CONFIG['audit_wall_seconds']);assert not (OUT/'audit.json').exists();start=clock()
    s=readz(OUT/'sources.json.gz');d=readz(OUT/'cases.json.gz');j=readz(OUT/'jobs.json.gz');records=read_records()
    assert s==make_sources() and d==make_panel() and j==make_jobs(s,d) and [x[0] for x in records]==j
    assert summarize(s,d,records)==json.loads((OUT/'summary.json').read_text())
    with writer_lock(RUN/'audit'):result=run_jobs(config,j,RUN/'audit',start,{spec['id']:(r,h) for spec,r,h in records})
    original=json.loads((OUT/'session.json').read_text());assert result['chain']==original['chain']
    for k in ('executions','counted_work'):assert result['totals'][k]==original['totals'][k]
    writej(OUT/'audit.json',dict(result,all_jobs_replayed=len(records),all_history_bytes_native_fields_work_exact=True,
        sources_corpus_jobs_summary_reconstructed=True,prior=prior_check()))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','run','analyze','audit']);a=p.parse_args()
    try:globals()[a.action]()
    except BaseException:
        directory=OUT if OUT.exists() else PREP;directory.mkdir(parents=True,exist_ok=True)
        writej(directory/f'{a.action}_failure_{time.time_ns()}.json',dict(action=a.action,traceback=traceback.format_exc()));raise

if __name__=='__main__':main()
