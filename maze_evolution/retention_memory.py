"""M12 bounded continuation of preserved random-origin wave lineages."""
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
from .modular_pilot_search import candidates,genome
from .retention_memory_search import founders,transition
from . import retention_memory_data as data_builder
from .routing_transfer import sha,canonical
from .deep_confirmation import writej

OUT=ROOT/'results/retention_memory';RUN=ROOT/'runs/retention_memory_m12'
CONFIG=dict(phase='M12',populations=6,seed=2026102160,validation_seed=2026102140,confirmation_seed=2026102161,
    fixture_seed=202610210160,workers=10,population=96,max_rounds=128,assessment_every=32,
    training_soft_wall_seconds=1200,session_wall_seconds=1800,memory_bytes=8*2**30,
    storage_bytes=6*2**30,disk_free_floor_bytes=16*2**30,call_cap=10000000,work_cap=10**13)
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
        queries=data['queries'][s['curriculum']]
        pool=candidates(s,data['kind']=='assessment')
        if data['kind']=='assessment':
            assert len(pool)<=115
            # Fill unused assessment slots with the fixed A0 reference. These
            # aliases are charged but never eligible for selection or nomination.
            pool=pool+[dict(next(i for i in s['protected'] if i['id']=='m12/reference/anchor/0'),id=f'budget_padding/{k}/{n}') for n in range(115-len(pool))]
        for i in pool:
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
    prior=json.loads((ROOT/'results/retention_bank/completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    return json.loads((OUT/'config.json').read_text())


def pushed(path):
    assert not subprocess.check_output(['git','status','--porcelain','--',str(path)],cwd=ROOT,text=True)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)==subprocess.check_output(['git','rev-parse','@{u}'],cwd=ROOT)


def prepare():
    assert not OUT.exists();OUT.mkdir()
    from .retention_memory_search import source_panel
    old=json.loads((ROOT/'results/retention_bank/completion.json').read_text())
    for p,h in old['files'].items():assert sha(ROOT/p)==h,p
    # Read the finished M11 journal, never mutate or run inference on it.
    path=ROOT/'runs/retention_bank_m11/campaign.sqlite'
    assert sha(path)==old['local_records'][str(path.relative_to(ROOT))]['sha256']
    db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
    panels=[unpacked(b) for b, in db.execute("select input from stages where kind='panel' and complete=1 order by n")];db.close()
    assert len(panels)==3
    writez(OUT/'source_panels.json.gz',dict(panels=panels,source_journal_sha256=sha(path),
        source_freeze_sha256=sha(ROOT/'results/retention_bank/calibration_freeze.json.gz'),
        reuse='M11 development panels only; no M11 confirmation cases'))
    writez(OUT/'source_panel.json.gz',source_panel())
    writez(OUT/'founders.json.gz',founders(CONFIG['seed']));writej(OUT/'config.json',CONFIG)
    writej(OUT/'preparation.json',dict(prior_completion_hashes=len(old['files']),
        initial_layout_manifest='results/retention_bank/whole_layout_exclusions.json',scientific_cases_generated=0))


def preflight():
    assert not (OUT/'registration.json').exists() and not (OUT/'rehearsal.json.gz').exists()
    previous=load_layouts(ROOT/'results/retention_bank/whole_layout_exclusions.json')
    states=founders(CONFIG['fixture_seed'],'m12-fixture');writez(OUT/'fixture_founders.json.gz',states)
    fixture=data_builder.validation(CONFIG['validation_seed'],previous);writez(OUT/'fixture.json.gz',fixture)
    ids=list(dict.fromkeys(c for q in fixture['queries'].values() for c in q));maze_map={m['case_id']:m for m in fixture['mazes']}
    control=evaluate_task([dict(model=dict(representation=c['representation'],genome=c['genome']),queries=ids,aliases=[c['id']]) for c in controls()],list(maze_map.values()),'m12controls')
    assert all(r['optimal'] or r['no_path'] for e in control['entries'] for r in e['rows'])
    writez(OUT/'control_fixture.json.gz',control);rehearsal=[];times=[]
    with ProcessPoolExecutor(CONFIG['workers'],mp_context=multiprocessing.get_context('spawn'),initializer=shared.worker_init) as ex:
        for step in range(5):
            start=time.monotonic();data=fixture if not step else data_builder.training(CONFIG['fixture_seed'],step-1,previous)
            previous.update(data['new_layouts']);specs=task_specs(states,data)
            mz=data['mazes'];receipts=list(ex.map(evaluate_task,specs,[mz]*len(specs),[hashed(packed(mz))]*len(specs)))
            next_states,decision=transition(states,data,receipts)
            assert transition(unpacked(packed(states)),unpacked(packed(data)),unpacked(packed(receipts)))==(next_states,decision)
            rehearsal.append(dict(data=data,receipts=receipts,decisions=decision,state_hash=hashed(packed(next_states))))
            states=next_states;times.append(time.monotonic()-start)
    writez(OUT/'rehearsal.json.gz',rehearsal)
    # Fresh final-shaped discarded fixture, not a scientific test of candidates.
    data=data_builder.confirmation(CONFIG['fixture_seed']+1,previous);previous.update(data['new_layouts'])
    ids=data['queries']['all'];mz=[m for m in data['mazes'] if m['case_id'] in set(ids)]
    finalcontrol=evaluate_task([dict(model=dict(representation=c['representation'],genome=c['genome']),queries=ids,aliases=[c['id']]) for c in controls()],mz,'m12finalcontrols')
    assert all(r['optimal'] or r['no_path'] for e in finalcontrol['entries'] for r in e['rows'])
    writez(OUT/'final_fixture.json.gz',data);writez(OUT/'final_control_fixture.json.gz',finalcontrol)
    for f in (OUT/'discarded_namespace_failure_001/exclusions_parts').glob('*.gz'):
        previous.update(readz(f)['hashes'])
    write_layouts('exclusions',previous)
    profile=dict(calls=sum(r['calls'] for step in rehearsal for r in step['receipts']),
        candidate_seconds=sum(r['candidate_seconds'] for step in rehearsal for r in step['receipts']),
        wall_by_stage=times,control_calls=control['calls']+finalcontrol['calls'],
        all_controls_correct=True,rehearsal_births=4*6*52,all_transition_rng_replayed=True,scientific_calls=0)
    writej(OUT/'profile.json',profile);print(json.dumps(profile,indent=2))



def register():
    assert not (OUT/'registration.json').exists();r=shared.source_manifest()
    paths=[*(p for p in OUT.rglob('*') if p.is_file()),ROOT/'docs/RETENTION_MEMORY.md',ROOT/'tests/test_retention_memory.py',ROOT/'results/retention_bank/completion.json',ROOT/'tools/run_m12_workflow.py',ROOT/'tools/inspect_retention_memory.py']
    r['files'].update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    r.update(phase='M12',scientific_calls=0,scientific_cases_generated=0)
    writej(OUT/'registration.json',r)


def freeze(j):
    states=j.state();items={};roles={};rep={};comparisons=[];needed=set()
    for s in states:
        for role,group in [('nominee',s['nominees']),('frozen',s['frozen']),('protected',s['protected'])]:
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
    write_layouts('search_exclusions',j.layouts())


def write_layouts(name,hashes):
    directory=OUT/(name+'_parts');assert not directory.exists();directory.mkdir();ordered=sorted(hashes);parts=[]
    for n,start in enumerate(range(0,len(ordered),1000000)):
        path=directory/f'part{n:03}.json.gz';values=ordered[start:start+1000000];writez(path,dict(hashes=values))
        parts.append(dict(path=str(path.relative_to(ROOT)),count=len(values),sha256=sha(path)))
    writej(OUT/(name+'.json'),dict(format='chunked-layout-hashes-v1',count=len(ordered),parts=parts))


from .retention_bank import load_layouts


def run():
    config=check();pushed(OUT/'registration.json');RUN.mkdir(parents=True,exist_ok=True)
    shared.evaluate_task=evaluate_task;shared.resource_reason=resource_reason
    started=time.monotonic();stopping=[False]
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stopping.__setitem__(0,True))
    with writer_lock(RUN):
        j=Journal(RUN);j.initialize(config,readz(OUT/'founders.json.gz'),load_layouts(OUT/'exclusions.json'));j.verify_chain()
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
                        elapsed=before+time.monotonic()-started
                        # Full logical next round plus a final assessment is reserved.
                        if stop is None:
                            why=('wall_target' if elapsed>=config['training_soft_wall_seconds'] else
                                 'round_ceiling' if g>=config['max_rounds'] else
                                 'call_reserve' if j.get('usage')['calls']+config['populations']*96*96+config['populations']*115*392>=config['call_cap'] else None)
                            if why:
                                stop=dict(generation=g,reason=why,elapsed_seconds=elapsed,usage=j.get('usage'))
                                j.put('nomination_stop',stop);j.db.commit()
                        assessment=(g%config['assessment_every']==0 or stop is not None) and states[0]['assessment_generation']!=g
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
                    print(json.dumps(dict(stage=n,kind=data['kind'],round=g,usage=j.get('usage'),rss_peak_bytes=shared._peak_rss,elapsed=before+time.monotonic()-started)),flush=True)
            done=not reason and j.get('nomination_stop') is not None and not j.pending()
            if done:
                assert j.state()[0]['assessment_generation']==j.state()[0]['generation']
                freeze(j);j.put('finished',True)
            writej(OUT/'session.json',dict(status='complete' if done else 'checkpoint',reason=reason,
                stop=j.get('nomination_stop'),generation=j.state()[0]['generation'],usage=j.get('usage'),
                rss_peak_bytes=shared._peak_rss,wall_seconds=before+time.monotonic()-started,chain=j.verify_chain()))
        finally:
            j.put('elapsed_search_seconds',before+time.monotonic()-started);j.put('active_session_epoch',None);j.db.commit();j.close()
        print('COMPLETE' if done else 'CHECKPOINT '+str(reason),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','preflight','register','run']);a=p.parse_args();globals()[a.action]()
