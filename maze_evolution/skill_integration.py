"""M25 selected disabled-at-birth expression evolution in the unchanged M18 runtime."""
import argparse,json,time,random,shutil,signal,subprocess,multiprocessing,sqlite3
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from pathlib import Path
from .foundation_calibration import ROOT
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_campaign_store import packed,unpacked,hashed,writer_lock
from .referenced_campaign_store import Journal,load_layouts,write_reference
from . import deep_campaign as shared
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import record,organism as flat_organism
from .exposure_genome import Genome as ExposureGenome
from .modular_runtime import Organism as ModularOrganism
from .modular_controls import intact_control
from .regulatory import seeded_genome
from .growth import Genome as FlatGenome
from .modular_pilot_search import candidates,genome
from .skill_integration_checkpoint import founders,verify_prior,export_checkpoint,freeze,START
from .skill_integration_search import transition
from . import skill_integration_data as data_builder
from .routing_transfer import sha,canonical
from .deep_confirmation import writej

OUT=ROOT/'results/skill_integration';RUN=ROOT/'runs/skill_integration_m25'
CONFIG=dict(phase='M25',populations=6,seed=2026102224,validation_seed=2026102140,confirmation_seed=2026102225,
    fixture_seed=202610222480,workers=10,population=96,start_generation=START,max_rounds=START+1024,assessment_every=16,
    training_soft_wall_seconds=4200,session_wall_seconds=5400,audit_wall_seconds=3600,memory_bytes=8*2**30,
    storage_bytes=12*2**30,disk_free_floor_bytes=16*2**30,layout_base_manifest="results/skill_integration/registered_exclusions.json",call_cap=100000000,work_cap=10**15)
_cache={}


def model(i,rep):return dict(representation=rep,genome=i['genome'])
from .connected_evaluation import organism,evaluate_task
from .connected_genome import embed


def controls():
    from .exploration_continuation import controls as old_controls
    return old_controls()+[dict(id='control/intact_connected',representation='connected',genome=embed(intact_control()).to_dict())]


def task_specs(states,data):
    models={}
    for k,s in enumerate(states):
        queries=data['queries'][s['curriculum']]
        pool=candidates(s,data['kind']=='assessment')
        if data['kind']=='assessment':
            assert len(pool)<=115
            # Fill unused assessment slots with the fixed A0 reference. These
            # aliases are charged but never eligible for selection or nomination.
            pool=pool+[dict(next(i for i in s['protected'] if i['id']=='m14/reference/anchor/0'),id=f'budget_padding/{k}/{n}') for n in range(115-len(pool))]
        for i in pool:
            m=model(i,s['representation']);key=hashed(packed([m,queries]))
            models.setdefault(key,dict(model=m,queries=queries,aliases=[]))['aliases'].append([k,i['id']])
    items=[models[k] for k in sorted(models)]
    return [items[i:i+8] for i in range(0,len(items),8)]


def clock():return (time.monotonic(),time.time())


def elapsed(started):return max(0.,time.monotonic()-started[0],time.time()-started[1])


def resource_reason(directory,config,started):
    if elapsed(started)>=config['session_wall_seconds']:return 'session_wall'
    if shared.process_resources()>=config['memory_bytes']:return 'memory'
    if shutil.disk_usage(directory).free<config['disk_free_floor_bytes']:return 'disk_free'
    size=sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())
    if size>=config['storage_bytes']:return 'storage'


def check():
    r=json.loads((OUT/'registration.json').read_text())
    for p,h in r['files'].items():assert sha(ROOT/p)==h,p
    now=shared.source_manifest();assert all(r[k]==now[k] for k in ('python','dependencies'))
    verify_prior()
    return json.loads((OUT/'config.json').read_text())


def pushed(path):
    assert not subprocess.check_output(['git','status','--porcelain','--',str(path)],cwd=ROOT,text=True)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)==subprocess.check_output(['git','rev-parse','@{u}'],cwd=ROOT)


def prepare():
    assert not OUT.exists();verify_prior();OUT.mkdir()
    evidence=export_checkpoint(OUT)
    writez(OUT/'retention_panel.json.gz',data_builder.retention_panel())
    writej(OUT/'config.json',CONFIG)
    writej(OUT/'preparation.json',dict(**evidence,matched_genomes_and_rng_per_replicate=True,
        histories='Matched M25 forks of three entire M23 enabled final populations, original nine states remain closed',
        protected_references=14,scientific_cases_generated=0))


def register():
    assert not (OUT/'registration.json').exists()
    storage=json.loads((OUT/'storage_plan.json').read_text())
    assert storage['admission_reserve_satisfied'] and storage['projection_fits_cap']
    assert json.loads((OUT/'profile.json').read_text())['status']=='PASS'
    assert json.loads((OUT/'pipeline_rehearsal.json').read_text())['status']=='PASS'
    assert json.loads((OUT/'runner_smoke.json').read_text())['status']=='PASS'
    r=shared.source_manifest()
    paths=[*(p for p in OUT.rglob('*') if p.is_file()),ROOT/'docs/SKILL_INTEGRATION.md',
           ROOT/'tests/test_skill_integration.py',ROOT/'tools/run_m25_workflow.py',
           ROOT/'tools/inspect_skill_integration.py',ROOT/'tools/preflight_m25.py',ROOT/'tools/rehearse_m25_pipeline.py',ROOT/'tools/smoke_m25_runner.py',ROOT/'results/dormant_evolution/completion.json',ROOT/'results/branch_causality/completion.json']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    r.update(phase='M25',scientific_calls=0,scientific_cases_generated=0)
    writej(OUT/'registration.json',r)




def write_layouts(name,hashes):
    base=(ROOT/'results/branch_causality/whole_layout_exclusions.json' if name=='exclusions' else OUT/'exclusions.json')
    write_reference(OUT/(name+'.json'),base,hashes)


def run():
    config=check();pushed(OUT/'registration.json');RUN.mkdir(parents=True,exist_ok=True)
    assert not (RUN/'campaign.sqlite').exists(),'Never automatically resume an old or failed workflow'
    if not (RUN/'campaign.sqlite').exists():
        assert shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']+config['storage_bytes'],'Insufficient admission reserve'
    shared.evaluate_task=evaluate_task;shared.resource_reason=resource_reason
    started=clock();stopping=[False]
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stopping.__setitem__(0,True))
    with writer_lock(RUN):
        j=Journal(RUN);j.initialize(config,readz(OUT/'founders.json.gz'),load_layouts(ROOT/config['layout_base_manifest']));j.verify_chain()
        if j.get('finished'):j.close();print('Already complete');return
        # A killed session conservatively charges downtime until resumption.
        before=j.get('elapsed_search_seconds') or 0.
        if j.get('active_session_epoch') is not None:before+=max(0.,time.time()-j.get('active_session_epoch'))
        j.put('elapsed_search_seconds',before);j.put('active_session_epoch',time.time());j.db.commit()
        remaining=config['session_wall_seconds']-before
        run_config=dict(config,session_wall_seconds=max(0.,remaining))
        previous=j.layouts();reason=None
        try:
            with ProcessPoolExecutor(config['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as pool:
                while not reason:
                    states=j.state();g=states[0]['generation'];assert all(s['generation']==g for s in states)
                    stop=j.get('nomination_stop');pending=j.pending()
                    if pending:n,data=pending
                    else:
                        used_seconds=before+elapsed(started)
                        # Full logical next round plus a final assessment is reserved.
                        if stop is None:
                            why=('wall_target' if used_seconds>=config['training_soft_wall_seconds'] else
                                 'round_ceiling' if g>=config['max_rounds'] else
                                 'call_reserve' if j.get('usage')['calls']+config['populations']*96*120+config['populations']*115*392>=config['call_cap'] else None)
                            if why:
                                stop=dict(generation=g,reason=why,elapsed_seconds=used_seconds,usage=j.get('usage'))
                                j.put('nomination_stop',stop);j.db.commit()
                        assessment=((g-config['start_generation'])%config['assessment_every']==0 or stop is not None) and states[0]['assessment_generation']!=g
                        if assessment:
                            if not (OUT/'validation.json.gz').exists():writez(OUT/'validation.json.gz',data_builder.validation(config['validation_seed'],previous))
                            data=deepcopy(readz(OUT/'validation.json.gz'));data['generation']=g
                            if g:data['new_layouts']=[]
                        elif stop is not None:break
                        else:data=data_builder.training(config['seed'],g,previous)
                        n=j.prepare(data,task_specs(states,data));previous.update(data['new_layouts'])
                    assert [s for _,s,_ in j.tasks(n)]==task_specs(states,data)
                    reason=shared.run_stage(j,n,data,pool,run_config,started,stopping)
                    if reason:break
                    state,decisions=transition(states,data,j.results(n));chain=j.commit(n,state,decisions)
                    print(json.dumps(dict(stage=n,kind=data['kind'],round=g,usage=j.get('usage'),rss_peak_bytes=shared._peak_rss,used_seconds=before+elapsed(started))),flush=True)
            done=not reason and j.get('nomination_stop') is not None and not j.pending()
            if done:
                assert j.state()[0]['assessment_generation']==j.state()[0]['generation']
                freeze(j,guard=lambda:resource_reason(RUN,run_config,started));j.put('finished',True)
            writej(OUT/'session.json',dict(status='complete' if done else 'checkpoint',reason=reason,
                stop=j.get('nomination_stop'),generation=j.state()[0]['generation'],new_rounds=j.state()[0]['generation']-config['start_generation'],usage=j.get('usage'),
                rss_peak_bytes=shared._peak_rss,wall_seconds=before+elapsed(started),monotonic_seconds=time.monotonic()-started[0],calendar_seconds=time.time()-started[1],chain=j.verify_chain()))
        finally:
            j.put('elapsed_search_seconds',before+elapsed(started));j.put('active_session_epoch',None);j.db.commit();j.close()
        print('COMPLETE' if done else 'CHECKPOINT '+str(reason),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','run']);a=p.parse_args();globals()[a.action]()
