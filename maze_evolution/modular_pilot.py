"""M1 registered bounded representation/curriculum pilot; separate resumable journal."""
import argparse,json,time,random,shutil,signal,subprocess,multiprocessing,sqlite3
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from pathlib import Path
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_campaign_store import Journal,packed,unpacked,hashed,writer_lock
from . import deep_campaign as shared
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record,organism as flat_organism
from .exposure_genome import Genome as ExposureGenome
from .modular_runtime import Organism as ModularOrganism
from .modular_controls import intact_control
from .regulatory import seeded_genome
from .growth import Genome as FlatGenome
from .modular_pilot_search import founders,candidates,genome,transition
from . import modular_pilot_data as data_builder
from .routing_transfer import sha,canonical
from .deep_confirmation import writej

OUT=ROOT/'results/modular_pilot';RUN=ROOT/'runs/modular_pilot_m1'
CONFIG=dict(phase='M1',seed=2026102010,validation_seed=2026102011,confirmation_seed=2026102012,
    fixture_seed=202610201010,workers=10,population=96,rounds=128,assessment_every=32,
    session_wall_seconds=5400,memory_bytes=12*2**30,storage_bytes=8*2**30,disk_free_floor_bytes=16*2**30,
    call_cap=15000000,work_cap=10**15)
_cache={}


def model(i,rep):return dict(representation=rep,genome=i['genome'])
def organism(m):
    if m['representation']=='modular':return ModularOrganism(genome('modular',m['genome']))
    g=genome('flat',m['genome']);return flat_organism(dict(genome=ExposureGenome(g,7).to_dict(),topology='local'))


def controls():
    return [dict(id='control/intact_flat',representation='flat',genome=FlatGenome(seeded_genome().genes).to_dict()),
            dict(id='control/intact_modular',representation='modular',genome=intact_control().to_dict())]


def evaluate_task(spec,maze_rows,data_hash):
    global _cache
    start=time.process_time()
    if _cache.get('hash')!=data_hash:
        cases=cases_from_manifest(maze_rows);_cache=dict(hash=data_hash,cases=cases,checker=Checker(cases))
    entries=[];seconds=work=calls=0
    for e in spec:
        org=organism(e['model']);rows=[]
        for cid in e['queries']:
            o=_cache['cases'][cid];m=o.maze;t=time.perf_counter();response=org.react(m.cells,m.w,m.h,m.start,m.goal)
            seconds+=time.perf_counter()-t;r=record(response,o);_cache['checker'].row(r);rows.append(r)
            work+=r['reads']+r['dispatches']+r['exposure_checks'];calls+=1
        entries.append(dict(aliases=e['aliases'],rows=rows))
    return dict(entries=entries,calls=calls,work=work,candidate_seconds=seconds,cpu_seconds=time.process_time()-start,independently_graded=calls)


def task_specs(states,data):
    models={}
    for k,s in enumerate(states):
        queries=data['queries']['all' if data['kind']=='assessment' else s['curriculum']]
        for i in candidates(s,data['kind']=='assessment'):
            m=model(i,s['representation']);key=hashed(packed([m,queries]))
            models.setdefault(key,dict(model=m,queries=queries,aliases=[]))['aliases'].append([k,i['id']])
    items=[models[k] for k in sorted(models)]
    return [items[i:i+8] for i in range(0,len(items),8)]


def resource_reason(directory,config,started):
    if time.monotonic()-started>=config['session_wall_seconds']:return 'session_wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(directory).free<config['disk_free_floor_bytes']:return 'disk_free'
    size=sum(p.stat().st_size for base in (Path(directory),OUT) for p in base.rglob('*') if p.is_file())
    if size>=config['storage_bytes']:return 'storage'


def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(r[k]==now[k] for k in ('python','dependencies'))
    return json.loads((OUT/'config.json').read_text())


def pushed(path):
    assert not subprocess.check_output(['git','status','--porcelain','--',str(path)],cwd=ROOT,text=True)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)==subprocess.check_output(['git','rev-parse','@{u}'],cwd=ROOT)


def prepare():
    assert not (OUT/'registration.json').exists();OUT.mkdir(exist_ok=True)
    # Verify the just-completed independent confirmation before using its exclusions.
    completion=json.loads((ROOT/'results/deep_confirmation/completion.json').read_text())
    for p,h in completion['files'].items():assert sha(ROOT/p)==(h['sha256'] if isinstance(h,dict) else h),p
    prior=set(readz(ROOT/'results/deep_confirmation/exclusions.json.gz')['hashes'])
    prior.update(readz(ROOT/'results/deep_confirmation/confirmation.json.gz')['new_layouts'])
    fixture=data_builder.validation(CONFIG['fixture_seed'],prior)
    prior.update(fixture['new_layouts']);train=[]
    for g in (0,1,20,24,25,29,30,39):
        b=data_builder.training(CONFIG['fixture_seed'],g,prior);prior.update(b['new_layouts']);train.append(b)
    writez(OUT/'fixture.json.gz',fixture);writez(OUT/'fixture_train.json.gz',train)
    writez(OUT/'exclusions.json.gz',dict(count=len(prior),hashes=sorted(prior)))
    writej(OUT/'config.json',CONFIG);writez(OUT/'founders.json.gz',founders(CONFIG['seed']))
    software=founders(CONFIG['fixture_seed']);writez(OUT/'fixture_founders.json.gz',software)
    # Calibration uses discarded random populations, never scientific founders.
    ids=fixture['queries']['all'];mazes=[r for r in fixture['mazes'] if r['case_id'] in ids]
    tasks=task_specs(software,fixture)
    # Two distinct engineering controls; both must solve every declared validation fixture.
    control_result=evaluate_task([dict(model=dict(representation=c['representation'],genome=c['genome']),queries=ids,aliases=[c['id']]) for c in controls()],mazes,'control')
    assert all(r['optimal'] or r['no_path'] for e in control_result['entries'] for r in e['rows'])
    t=time.monotonic()
    with ProcessPoolExecutor(CONFIG['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as pool:
        receipts=list(pool.map(evaluate_task,tasks,[mazes]*len(tasks),['fixture']*len(tasks)))
    profile=dict(calls=sum(r['calls'] for r in receipts),candidate_seconds=sum(r['candidate_seconds'] for r in receipts),worker_cpu_seconds=sum(r['cpu_seconds'] for r in receipts),wall_seconds=time.monotonic()-t,fixture_queries=len(ids),models=sum(len(t) for t in tasks),control_calls=control_result['calls'],control_candidate_seconds=control_result['candidate_seconds'],scientific_calls=0)
    writez(OUT/'fixture_receipts.json.gz',receipts);writez(OUT/'control_fixture.json.gz',control_result)
    writej(OUT/'profile.json',profile);print(json.dumps(profile,indent=2))


def register():
    assert not (OUT/'registration.json').exists();r=shared.source_manifest()
    paths=[*OUT.glob('*.json'),*OUT.glob('*.json.gz'),ROOT/'docs/MODULAR_PILOT.md',ROOT/'tests/test_modular_prototype.py',ROOT/'tests/test_modular_pilot.py']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    r.update(phase='M1',scientific_calls=0,scientific_cases_generated=0)
    writej(OUT/'registration.json',r)


def freeze(j):
    states=j.state();items={};roles={};rep={};comparisons=[];needed=set()
    for s in states:
        for role,group in [('nominee',s['nominees']),('frozen',s['frozen'])]:
            for rank,i in enumerate(group):
                items[i['id']]=i;roles.setdefault(i['id'],[]).append([s['name'],role,rank]);rep[i['id']]=s['representation']
                if role=='nominee':
                    comparisons.append(dict(condition=s['name'],rank=rank,child=i['id'],root=i['root'],parent=i['parent'],mutations=i['mutation_depth']))
                    needed|={i['id'],i['root']};needed.update([i['parent']] if i['parent'] else [])
    panel_ids=needed|set(items);ancestry={}
    for blob, in j.db.execute('select decision from stages where complete=1 order by n desc'):
        for decision in unpacked(blob):
            for b in decision['births']:
                i=b['item']
                if i['id'] in needed:
                    ancestry[i['id']]=b;rep[i['id']]=decision['name'].split('/')[0]
                    if i['id'] in panel_ids:items[i['id']]=i
                    if i['parent']:needed.add(i['parent'])
    initial=unpacked(j.db.execute('select value from states where stage=-1').fetchone()[0])
    for s in initial:
        for i in s['population']:
            if i['id'] in needed:
                ancestry[i['id']]=dict(item=i,event=None);rep[i['id']]=s['representation']
                if i['id'] in panel_ids:items[i['id']]=i
    assert panel_ids<=items.keys() and needed<=ancestry.keys()|items.keys()
    writez(OUT/'choices.json.gz',dict(items=items,representations={i:rep[i] for i in items},roles=roles,comparisons=comparisons,controls=controls(),chain=j.verify_chain()))
    writez(OUT/'ancestry.json.gz',ancestry);writez(OUT/'final_states.json.gz',states)
    writez(OUT/'search_exclusions.json.gz',dict(hashes=sorted(j.layouts()),count=len(j.layouts())))


def run():
    config=check();pushed(OUT/'registration.json');RUN.mkdir(parents=True,exist_ok=True)
    shared.evaluate_task=evaluate_task;shared.resource_reason=resource_reason
    started=time.monotonic();stopping=[False]
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stopping.__setitem__(0,True))
    with writer_lock(RUN):
        j=Journal(RUN);j.initialize(config,readz(OUT/'founders.json.gz'),set(readz(OUT/'exclusions.json.gz')['hashes']));j.verify_chain();previous=j.layouts();reason=None
        with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as pool:
            while not reason:
                states=j.state();g=states[0]['generation'];assert all(s['generation']==g for s in states)
                pending=j.pending()
                if pending:n,data=pending
                else:
                    if g%config['assessment_every']==0 and states[0]['assessment_generation']!=g:
                        if not (OUT/'validation.json.gz').exists():writez(OUT/'validation.json.gz',data_builder.validation(config['validation_seed'],previous))
                        data=deepcopy(readz(OUT/'validation.json.gz'));data['generation']=g
                        if g:data['new_layouts']=[]
                    elif g>=config['rounds']:break
                    else:data=data_builder.training(config['seed'],g,previous)
                    n=j.prepare(data,task_specs(states,data));previous.update(data['new_layouts'])
                assert [s for _,s,_ in j.tasks(n)]==task_specs(states,data)
                reason=shared.run_stage(j,n,data,pool,config,started,stopping)
                if reason:break
                state,decisions=transition(states,data,j.results(n));chain=j.commit(n,state,decisions)
                print(json.dumps(dict(stage=n,kind=data['kind'],round=g,usage=j.get('usage'),rss_peak_bytes=shared._peak_rss,wall=time.monotonic()-started)),flush=True)
        done=not reason and j.state()[0]['generation']==config['rounds']
        if done:freeze(j)
        writej(OUT/'session.json',dict(status='complete' if done else 'checkpoint',reason=reason,usage=j.get('usage'),rss_peak_bytes=shared._peak_rss,wall_seconds=time.monotonic()-started,chain=j.verify_chain()))
        j.close();print('COMPLETE' if done else 'CHECKPOINT '+str(reason),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','run']);a=p.parse_args();globals()[a.action]()
