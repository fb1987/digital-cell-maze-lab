"""V13A fixed panel; no candidate editing, selection, training or reproduction."""
import argparse,gzip,json,time,resource,platform,subprocess
from importlib.metadata import version
from .branch_overgrowth_data import *
from .routing_mechanism_runtime import respond
from .routing_mechanism_study import pack_history,unpack_history,Budget
from .family_evolution_study import PRIOR as Z_PRIOR
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .exposure_genome import Individual
from .exposure_selection import physical,organism,record
from .growth import replay_mutation
from .baselines import baseline
from .foundation_pair_confirm import normal_row

PRIOR=(*Z_PRIOR,'family_evolution')
MODES=('normal','pulse_off','flag_off','both_off','endpoint_off','halt_off')
TRACE_MODES=('normal','pulse_off','flag_off','both_off')
TARGETS=tuple(f'{a}{r}' for a in ('mutation','family','resample') for r in range(3))+('historical_long','historical_short','random68','intact')
HORIZON=96

def prior_check():
    n=0
    for stage in PRIOR:
        for name,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():
            assert sha(ROOT/name)==h,name;n+=1
    return n

def make_panel():
    source=ROOT/'results/family_evolution';choices=read_compressed(source/'choices.json.gz');items={}
    for a,key in [('mutation','current_mutation'),('family','family_mutation'),('resample','resample')]:
        for r in range(3):items[f'{a}{r}']=choices['items'][f'fresh/{r}/{key}/primary']
    w=read_compressed(ROOT/'results/compatibility_map/panel.json.gz')
    for a,k in [('historical_long','carry1'),('historical_short','fresh2'),('random68','random68'),('intact','intact')]:items[a]=w['items'][k]
    edges={}
    for e in lines(source/'reproduction.jsonl.gz'):
        if e['key'].startswith('fresh/'):
            for b in e['births']:edges[b['item']['id']]=b['parents']
    chains={};needed=set()
    for name in (f'{a}{r}' for a in ('mutation','family','resample') for r in range(3)):
        identity=items[name]['id'];chain=[identity]
        while edges.get(identity):
            assert len(edges[identity])==1
            identity=edges[identity][0];assert identity not in chain;chain.append(identity)
        chains[name]=dict(nodes=chain,root=identity,mutation_births=len(chain)-1);needed.update(chain)
    registry={i['id']:i for p in read_compressed(source/'pools.json.gz').values() for i in p['items'] if i['id'] in needed};events={}
    for e in lines(source/'reproduction.jsonl.gz'):
        for b in e['births']:
            if b['item']['id'] in needed:registry[b['item']['id']]=b['item'];events[b['item']['id']]=b
    assert set(registry)==needed
    for identity,b in events.items():
        if not b['parents']:assert b['mutation'] is None;continue
        parent=Individual.load(registry[b['parents'][0]])
        assert replay_mutation(parent.genome.program,b['mutation'],256)==Individual.load(b['item']).genome.program
    for name,c in chains.items():
        assert registry[c['nodes'][0]]==items[name]
        if name.startswith(('mutation','family')):
            items[name+'_root']=registry[c['root']];items[name+'_parent']=registry[c['nodes'][1]]
        else:assert c['mutation_births']==0
    models={};aliases={}
    for name,raw in items.items():
        pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[name]=pid
    return canonical(dict(items=items,models=models,aliases=aliases,chains=chains,registry=registry,events=events,Z_informed=True))

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();t=time.perf_counter()
    p=make_panel();compressed_json(OUT/'panel.json.gz',p)
    d=create(FIXTURE_SEED,'fixture',exclusions());d.save(FIXTURES)
    from .branch_overgrowth_audit import geometry
    g=geometry(d.cache,d.contexts,d.metadata)
    write_json(OUT/'preparation.json',dict(candidate_calls=0,prior_hashes=prior_check(),geometry=g,prior_layouts=d.previous_count,wall_seconds=time.perf_counter()-t))
    print(dict(models=len(p['models']),aliases=len(p['aliases']),ancestry_events=len(p['events']),geometry=g),flush=True)

def schedules(panel,meta,fixture=False):
    for pid in panel['models']:
        for cid,m in meta.items():
            if fixture and m['pose']!=0:continue
            yield 'normal',pid,'normal',cid
            if fixture:yield 'parity',pid,'normal',cid
    targets=list(dict.fromkeys(panel['aliases'][name] for name in TARGETS))
    for mode in MODES[1:]:
        for pid in targets:
            for cid,m in meta.items():
                if mechanism_case(m) and (not fixture or m['pose']==0):yield 'intervention',pid,mode,cid
    for mode in TRACE_MODES:
        for pid in targets:
            for cid,m in meta.items():
                if trace_case(m,fixture):yield 'trace',pid,mode,cid

def warm(cases,panel):
    m=next(iter(cases.values())).maze;model=panel['models'][panel['aliases']['intact']];t=time.perf_counter()
    organism(model).react(m.cells,m.w,m.h,m.start,m.goal)
    respond(model,m);respond(model,m,trace=True,forced=True,horizon=HORIZON)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(candidate_calls=3,baseline_calls=3,seconds=time.perf_counter()-t,case=m.case_id,readonly_bytes=True)

def evaluate(path,cases,meta,panel,fixture=False):
    b=Budget(180 if fixture else 720);w=warm(cases,panel);t=time.perf_counter();complete=False;rates={};orgs={};baseline_calls=0;last=None
    planned=sum(1 for _ in schedules(panel,meta,fixture));pending=None
    try:
        with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for scope,pid,mode,cid in schedules(panel,meta,fixture):
                o=cases[cid];m=o.maze;model=panel['models'][pid];before=b.seconds
                if scope=='normal':
                    if pid not in orgs:orgs[pid]=organism(model)
                    r=b.call(lambda:orgs[pid].react(m.cells,m.w,m.h,m.start,m.goal))
                else:
                    result=b.call(lambda:respond(model,m,mode,trace=scope=='trace',forced=scope=='trace',horizon=HORIZON));r=result.reaction
                key=scope+'|'+('ordinary' if meta[cid]['family'].startswith('ordinary_') else 'structured')
                rate=rates.setdefault(key,dict(calls=0,seconds=0.));rate['calls']+=1;rate['seconds']+=b.seconds-before
                row=record(r,o);event=dict(scope=scope,model=pid,mode=mode,row=row)
                if scope=='trace':event.update(history=pack_history(result.history),instrumentation_bytes=result.instrumentation_bytes)
                if fixture:
                    if scope=='normal':pending=row
                    elif scope=='parity':assert row==pending;pending=None
                logrow(log,event)
                block=('native' if scope in ('normal','parity') else scope,mode)
                if block!=last:print(json.dumps(dict(scope=scope,mode=mode,calls=b.calls,seconds=round(b.seconds,2))),flush=True);last=block
                if b.calls%4096==0:
                    if sum(p.stat().st_size for p in path.rglob('*') if p.is_file())>2*2**30:raise OSError('2GiB artifact cap')
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for cid,o in cases.items():
                    if fixture and meta[cid]['pose']!=0:continue
                    m=o.maze;row=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert row['optimal'] or row['no_path'];logrow(log,dict(model=name,row=row));baseline_calls+=1
        assert planned==b.calls and pending is None;complete=True
    finally:
        packet=dict(complete=complete,planned_calls=planned,budget=b.save(),warmup=w,rates=rates,baseline_calls=baseline_calls,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(path/'execution.json',packet)
    print(json.dumps(packet),flush=True);return packet

def projection(rates,repeats):
    return 2*sum(v['seconds']*(2 if k.startswith('trace|') else 8 if k=='normal|ordinary' else 8*repeats) for k,v in rates.items() if not k.startswith('parity|'))

def profile():
    assert not (FIXTURES/'execution.json').exists()
    p=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(FIXTURES);e=evaluate(FIXTURES,cases,meta,p,True)
    projections={str(n):projection(e['rates'],n) for n in (2,1)};chosen=next((n for n in (2,1) if projections[str(n)]<600),None)
    write_json(FIXTURES/'profile.json',dict(passed=chosen is not None,repeats=chosen,projections=projections,safety_factor=2,scores_used_for_schedule=False,rule='First of 2 then 1 repetitions fitting600s with2x measured inference cost; no final generated.'))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def freeze():
    assert not (OUT/'preregistration.json').exists() and json.loads((FIXTURES/'profile.json').read_text())['passed']
    sources=[ROOT/'cellular_maze_lab.py',ROOT/'docs/BRANCH_OVERGROWTH_V13A.md',ROOT/'tests/test_branch_overgrowth.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file()]
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,scientific_calls=0,cap_candidate_seconds=720,horizon=HORIZON,
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        python=platform.python_version(),platform=platform.platform(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')}))

def check_freeze(committed=False):
    reg=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for p,h in reg[group].items():assert sha(ROOT/p)==h,p
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        for name in ('panel.json.gz','preregistration.json'):
            assert subprocess.check_output(['git','show',f'HEAD:results/branch_overgrowth/{name}'])==(OUT/name).read_bytes()
    return reg

def run():
    check_freeze(True);path=OUT/'confirmation';assert not path.exists()
    old=exclusions();add_layouts(old,FIXTURES);rep=json.loads((FIXTURES/'profile.json').read_text())['repeats']
    d=create(SEED,'confirmation',old,rep);d.save(path)
    from .branch_overgrowth_audit import geometry
    g=geometry(d.cache,d.contexts,d.metadata)
    write_json(path/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),geometry=g,prior_layouts=d.previous_count,whole_layouts=len(d.layouts),hashes={str(p.relative_to(ROOT)):sha(p) for p in path.iterdir() if p.is_file()}))
    evaluate(path,d.cache,d.metadata,read_compressed(OUT/'panel.json.gz'))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','profile','freeze','run','analyze','audit'));action=p.parse_args().action
    if action=='analyze':
        from .branch_overgrowth_analysis import analyze
        analyze()
    elif action=='audit':
        from .branch_overgrowth_audit import audit
        audit()
    else:globals()[action]()

if __name__=='__main__':main()
