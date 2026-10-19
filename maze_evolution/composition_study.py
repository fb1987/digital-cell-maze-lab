"""V12S: fixed75minute matched search; protected diversity and two-parent ancestry."""
import argparse,gzip,json,random,time,resource,subprocess,platform
from copy import deepcopy
from importlib.metadata import version
from .composition_data import *
from .composition_search import *
from .shared_prefix_study import warm,assay,save_generation,init_state
from .mutation_accessibility_study import PRIOR as R_PRIOR
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .exposure_selection import physical,organism,record
from .baselines import baseline
from .foundation_pair_confirm import normal_row

PRIOR=(*R_PRIOR,'mutation_accessibility')
SEARCH_WALL=4500
MAX_GENERATIONS=4096
VALIDATE_EVERY=32

class Budget:
    def __init__(self,seconds=5400,saved=None):
        self.cap_seconds=seconds;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
        if saved:self.__dict__.update(saved)
    def call(self,fn):
        if self.seconds>=self.cap_seconds-max(.5,2*self.maximum) or self.calls>=40000000 or self.work>=40000000000000:raise TimeoutError('Closed S cap')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('S4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t;self.seconds+=dt;self.calls+=1;self.maximum=max(self.maximum,dt);self.work+=r.spatial_reads+r.dispatches+r.exposure_checks
        assert self.seconds<self.cap_seconds and self.work<40000000000000
        return r
    def save(self):return vars(self).copy()

def prior_check():
    n=0
    for stage in PRIOR:
        for name,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/name)==h,name;n+=1
    return n

def make_pools():
    panel=read_compressed(ROOT/'results/research_reset/panel.json.gz');protected=[v['item'] for v in panel.values()]
    assert len({i['id'] for i in protected})==16
    pools={}
    for origin in ('carry','fresh'):
        for rep in range(3):
            key=f'{origin}/{rep}';rng=random.Random(seed_for(SEED,'founders/'+origin,rep,0));before=rng.getstate()
            items=deepcopy(protected) if origin=='carry' else []
            for k in range(96-len(items)):
                i=Individual(f'composition/{key}/founder{k}',Genome(random_genome(rng,True),7),None,0);items.append(i.save())
            search=random.Random(seed_for(SEED,'search/'+origin,rep,0))
            pools[key]=dict(items=items,protected=deepcopy(protected) if origin=='carry' else [],founder_rng_before=before,founder_rng_after=rng.getstate(),search_rng=search.getstate())
    return canonical(pools)

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();t=time.perf_counter();OUT.mkdir()
    pools=make_pools();compressed_json(OUT/'pools.json.gz',pools)
    d=create(FIXTURE_SEED,'fixture',exclusions());assert d.previous_count==191784;d.save(FIXTURES)
    s=schedule_fixture(exclusions()+manifest(d.cache.values()));s.save(OUT/'schedule_fixtures')
    # Complete normal and stress grammar is covered here before scientific calls.
    write_json(OUT/'preparation.json',dict(candidate_calls=0,pools=6,protected_carry=16,prior_hashes=prior_check(),previous_layouts=d.previous_count,new_layouts=len(s.layouts)-d.previous_count,fixture_inputs=len(d.cache),schedule_inputs=len(s.cache),wall_seconds=time.perf_counter()-t))

def freeze():
    assert not (OUT/'preregistration.json').exists()
    sources=[ROOT/'cellular_maze_lab.py',ROOT/'docs/COMPOSITION_V12S.md',ROOT/'tests/test_composition.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for base in (OUT,FIXTURES,ROOT/'results/research_reset') for p in base.rglob('*') if p.is_file() and p.suffix!='.log']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,scientific_calls=0,
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        python=platform.python_version(),platform=platform.platform(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')}))

def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for name,h in p[group].items():assert sha(ROOT/name)==h,name
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/composition_study/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return p

def profile():
    check_freeze(True);assert not (FIXTURES/'profile.json').exists();t=time.perf_counter();cases,_,meta=load(FIXTURES);w=warm(cases);b=Budget(180);pools=read_compressed(OUT/'pools.json.gz')
    ids=[c for c,m in meta.items() if m['family'] in ('paired','corridor','disconnected') and m['index']<2 and m['pose']==0 and m['prefix'] in (0,1)];assert len(ids)==24
    rates={}
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for key,p in pools.items():
            before=b.seconds
            for raw in p['items']:assay(Individual.load(raw),cases,ids,b,log,'profile',key,-1)
            rates[key]=(b.seconds-before)/(96*len(ids))
        known=Individual.load(read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']['intact'])
        rr=assay(known,cases,list(cases),b,log,'profile','intact',-1)
        assert all(r['optimal'] or r['no_path'] for r in rr)
    # Only feasibility is gated; duration fixed, no score-dependent extension/stop.
    rate=2*max(rates.values());estimated_initial=576*3456*rate;estimated_round=(18*96*12+18*2*3456/32)*rate
    write_json(FIXTURES/'profile.json',dict(passed=estimated_initial+96*estimated_round<4200,
        planning_rate=rate,pool_rates=rates,estimated_initial_seconds=estimated_initial,estimated_round_seconds=estimated_round,
        estimated_96_round_seconds=estimated_initial+96*estimated_round,budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,scores_used_for_schedule=False))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def choices_packet(states,frozen):
    items={};models={};aliases={}
    for key,s in states.items():
        for name,a in s['archives'].items():items[key+'/'+name]=a['item']
    for key,aa in frozen.items():
        for name,a in aa.items():items[key+'/frozen/'+name]=a['item']
    for k,v in read_compressed(ROOT/'results/research_reset/panel.json.gz').items():items['anchor/'+k]=v['item']
    items['anchor/intact']=read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']['intact']
    for a,raw in items.items():pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[a]=pid
    return dict(items=items,models=models,aliases=aliases,frozen_before_final=True)

def run():
    check_freeze(True);p=json.loads((FIXTURES/'profile.json').read_text());assert p['passed'] and not (OUT/'validation').exists()
    assert subprocess.check_output(['git','show','HEAD:results/composition_fixtures/profile.json'])==(FIXTURES/'profile.json').read_bytes()
    previous=exclusions()+read_compressed(FIXTURES/'mazes.json.gz')+read_compressed(OUT/'schedule_fixtures/mazes.json.gz');v=create(seed_for(SEED,'validation',0,0),'validation',previous);save_generation(v,OUT/'validation');assert len(v.cache)==3456
    d=AccessData(seed_for(SEED,'train',0,0),previous+manifest(v.cache.values()));del previous
    pools=read_compressed(OUT/'pools.json.gz');states={};frozen={};b=Budget();w=warm(v.cache);complete=False;matched=0;max_round=0.;stop='generation_ceiling'
    (OUT/'checkpoints').mkdir();(OUT/'train').mkdir();t=time.perf_counter()
    try:
        with gzip.open(OUT/'initial.jsonl.gz','wt',compresslevel=1) as log:
            for key,pool in pools.items():
                aa={}
                for raw in pool['items']:
                    i=Individual.load(raw);rr=assay(i,v.cache,list(v.cache),b,log,'initial',key,0);update_archives(aa,i,summary(rr,v.metadata),0)
                frozen[key]=deepcopy(aa)
                for arm in ARMS:states[key+'/'+arm]=init_state(key+'/'+arm,pool,aa)
                print(json.dumps(dict(initial=key,calls=b.calls,seconds=b.seconds,wall=time.perf_counter()-t)),flush=True)
        initial=b.save();compressed_json(OUT/'frozen.json.gz',frozen);compressed_json(OUT/'initial_states.json.gz',states)
        with gzip.open(OUT/'reproduction.jsonl.gz','wt',compresslevel=1) as births:
            for g in range(MAX_GENERATIONS):
                if time.perf_counter()-t+max(30,1.5*max_round)>=SEARCH_WALL:stop='wall_reserve';break
                if b.seconds+max(30,1.5*max_round)>=4800:stop='candidate_final_reserve';break
                start=time.perf_counter();ids=training_batch(d,g);path=OUT/'train'/f'g{g:04d}';save_generation(d,path)
                with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
                    for key,state in states.items():
                        pop=[Individual.load(r) for r in state['population']];rr={i.identity:assay(i,d.cache,ids,b,log,'train',key,g) for i in pop};rank=ranked(pop,rr,d.metadata);aa=deepcopy(state['archives'])
                        if (g+1)%VALIDATE_EVERY==0:
                            for i in nominees(rank):
                                vr=assay(i,v.cache,list(v.cache),b,log,'validation',key,g);update_archives(aa,i,summary(vr,v.metadata),g)
                        new,event=reproduce(state,rank,aa);logrow(births,event);states[key]=new
                matched=g+1;max_round=max(max_round,time.perf_counter()-start);clear_batch(d)
                if matched%32==0:compressed_json(OUT/f'checkpoints/g{matched}.json.gz',states)
                compressed_json(OUT/'latest_states.json.gz',states)
                print(json.dumps(dict(generation=matched,calls=b.calls,seconds=round(b.seconds,2),wall=round(time.perf_counter()-t,2),positive={k:s['archives']['primary']['metrics']['positive'] for k,s in states.items()})),flush=True)
                if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>3*2**30:raise OSError('S3GiB artifact cap')
        compressed_json(OUT/'next_states.json.gz',states);compressed_json(OUT/'choices.json.gz',choices_packet(states,frozen));complete=True
    finally:
        compressed_json(OUT/'latest_states.json.gz',states)
        write_json(OUT/'search_execution.json',dict(complete=complete,generations=matched,stop=stop,initial_budget=locals().get('initial'),budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,largest_round_wall=max_round,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,whole_layouts=len(d.layouts)))

def confirm():
    check_freeze(True);assert not (OUT/'confirmation').exists();ex=json.loads((OUT/'search_execution.json').read_text());assert ex['complete']
    assert subprocess.check_output(['git','show','HEAD:results/composition_study/choices.json.gz'])==(OUT/'choices.json.gz').read_bytes()
    t=time.perf_counter();previous=exclusions()+read_compressed(FIXTURES/'mazes.json.gz')+read_compressed(OUT/'schedule_fixtures/mazes.json.gz')+read_compressed(OUT/'validation/mazes.json.gz')
    for path in sorted((OUT/'train').glob('g*/mazes.json.gz')):previous+=read_compressed(path)
    d=create(seed_for(SEED,'confirmation',0,0),'confirmation',previous);path=OUT/'confirmation';save_generation(d,path);del previous
    choices=read_compressed(OUT/'choices.json.gz');b=Budget(saved=ex['budget']);initial=b.save();w=warm(d.cache);metrics={};complete=False;bc=0
    try:
        with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for pid in choices['models']:
                i=next(Individual.load(choices['items'][a]) for a,p in choices['aliases'].items() if p==pid)
                rr=assay(i,d.cache,list(d.cache),b,log,'confirmation',pid,-1);metrics[pid]=summary(rr,d.metadata)
                print(json.dumps(dict(model=pid,positive=metrics[pid]['positive'],seconds=b.seconds)),flush=True)
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for o in d.cache.values():
                    m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert r['optimal'] or r['no_path'];logrow(log,dict(model=name,row=r));bc+=1
        compressed_json(path/'metrics.json.gz',metrics);complete=True
    finally:write_json(path/'execution.json',dict(complete=complete,initial_budget=initial,budget=b.save(),warmup=w,baseline_calls=bc,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))

def analysis_packet():
    states=read_compressed(OUT/'next_states.json.gz');frozen=read_compressed(OUT/'frozen.json.gz');c=read_compressed(OUT/'choices.json.gz');m=read_compressed(OUT/'confirmation/metrics.json.gz');out={};passes={o:[] for o in ('carry','fresh')}
    for origin in passes:
        for rep in range(3):
            key=f'{origin}/{rep}';v={a:states[key+'/'+a]['archives']['primary']['metrics'] for a in ARMS};v['frozen']=frozen[key]['primary']['metrics']
            f={a:m[c['aliases'][key+'/'+a+'/primary']] for a in ARMS};f['frozen']=m[c['aliases'][key+'/frozen/primary']]
            vg=gate(v['recombination'],v['mutation'],v['resample'],v['frozen']);fg=gate(f['recombination'],f['mutation'],f['resample'],f['frozen'])
            coverage=states[key+'/recombination']['generation']>=96
            if vg and fg and coverage:passes[origin].append(rep)
            out[key]=dict(validation=v,final=f,validation_gate=vg,final_gate=fg,adequate_schedule=coverage,passed=vg and fg and coverage)
    return dict(results=out,passing=passes,replicated={o:len(p)>=2 for o,p in passes.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','freeze','profile','run','confirm','analyze','audit'));a=p.parse_args().action
    if a=='analyze':compressed_json(OUT/'analysis.json.gz',analysis_packet())
    elif a=='audit':
        from .composition_audit import audit
        audit()
    else:globals()[a]()
if __name__=='__main__':main()
