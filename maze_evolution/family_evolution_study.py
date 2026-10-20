"""V12Z: fixed75minute mutation versus family-reserve comparison."""
import argparse,gzip,json,random,time,resource,subprocess,platform
from copy import deepcopy
from importlib.metadata import version
from .family_evolution_data import *
from .family_evolution_search import *
from .shared_prefix_study import warm,assay,save_generation
from .linkage_restart_study import PRIOR as X_PRIOR
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .exposure_selection import physical,organism,record
from .baselines import baseline
from .foundation_pair_confirm import normal_row

PRIOR=(*X_PRIOR,'linkage_restart','mating_opportunity')
SEARCH_WALL=4500
MAX_GENERATIONS=4096
VALIDATE_EVERY=32

class Budget:
    def __init__(self,seconds=4500,saved=None):
        self.cap_seconds=seconds;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
        if saved:self.__dict__.update(saved)
    def call(self,fn):
        if self.seconds>=self.cap_seconds-max(.5,2*self.maximum) or self.calls>=40000000 or self.work>=40000000000000:raise TimeoutError('Closed Z cap')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('Z4GiB cap')
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
    old=read_compressed(ROOT/'results/research_reset/panel.json.gz');w=read_compressed(ROOT/'results/compatibility_map/panel.json.gz')
    protected=[p['item'] for p in old.values()]
    for name in ('d07','d12','fresh2','carry1'):
        raw=w['items'][name]
        if raw['id'] not in {i['id'] for i in protected}:protected.append(raw)
    assert len(protected)==20
    special={w['items']['d07']['id']:[f'known_U_d07/{i}' for i in range(256)],w['items']['d12']['id']:[f'known_U_d07/{i}' for i in range(256) if i!=106]}
    pools={}
    for origin in ('carry','fresh'):
        for rep in range(3):
            key=f'{origin}/{rep}';rng=random.Random(seed_for(SEED,'founders/'+origin,rep,0));before=rng.getstate()
            items=deepcopy(protected) if origin=='carry' else []
            for k in range(96-len(items)):items.append(Individual(f'family_z/{key}/founder{k}',Genome(random_genome(rng,True),7),None,0).save())
            ids={r['id']:special.get(r['id'],[r['id']+f'/gene{k}' for k in range(len(Individual.load(r).genome.genes))]) for r in items}
            pools[key]=dict(items=items,protected=deepcopy(protected) if origin=='carry' else [],gene_ids=ids,families={r['id']:('known_U_d07' if r['id'] in special else r['id']) for r in items},founder_rng_before=before,founder_rng_after=rng.getstate(),search_rng=random.Random(seed_for(SEED,'search/'+origin,rep,0)).getstate())
    return canonical(pools)

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();t=time.perf_counter();OUT.mkdir()
    pools=make_pools();compressed_json(OUT/'pools.json.gz',pools)
    previous=exclusions();d=create(FIXTURE_SEED,'fixture',previous);d.save(FIXTURES)
    previous.update(d.layouts);s=schedule_fixture(previous);s.save(OUT/'schedule_fixtures')
    write_json(OUT/'preparation.json',dict(candidate_calls=0,pools=6,protected_carry=20,prior_hashes=prior_check(),previous_layouts=d.previous_count,new_layouts=len(s.layouts)-d.previous_count,fixture_inputs=len(d.cache),schedule_inputs=len(s.cache),wall_seconds=time.perf_counter()-t))

def through_fixtures():
    previous=exclusions()
    for p in (FIXTURES,OUT/'schedule_fixtures',OUT/'software_fixtures'):add_layouts(previous,p)
    return previous


def freeze():
    assert not (OUT/'preregistration.json').exists()
    sources=[ROOT/'cellular_maze_lab.py',ROOT/'docs/FAMILY_EVOLUTION_V12Z.md',ROOT/'tests/test_family_evolution.py',ROOT/'tests/test_family_reservoir.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
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
        assert subprocess.check_output(['git','show','HEAD:results/family_evolution/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return p

def profile_ids(meta):
    return [c for c,m in meta.items() if m['family'] in ('paired','corridor','disconnected') and m['index']<2 and m['pose']==0 and m['prefix'] in (0,1)]

def profile():
    assert not (FIXTURES/'profile.json').exists();t=time.perf_counter();cases,_,meta=load(FIXTURES);w=warm(cases);b=Budget(180);pools=read_compressed(OUT/'pools.json.gz')
    ids=profile_ids(meta);assert len(ids)==24;rates={};opseconds=0.
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt',compresslevel=1) as log,gzip.open(FIXTURES/'reproduction.jsonl.gz','wt',compresslevel=1) as births:
        for key,pool in pools.items():
            before=b.seconds;pop=[Individual.load(raw) for raw in pool['items']]
            rr={i.identity:assay(i,cases,ids,b,log,'profile',key,-1) for i in pop};rates[key]=(b.seconds-before)/(96*len(ids));rank=ranked(pop,rr,meta)
            for arm in ARMS:
                state=init_state(key+'/'+arm,pool);start=time.perf_counter();new,event=reproduce(state,rank,{})
                opseconds+=time.perf_counter()-start;assert reproduce(state,rank,{})==(new,event)
                logrow(births,dict(event=event,next_state_digest=digest(new)))
        known=Individual.load(read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']['intact'])
        rr=assay(known,cases,list(cases),b,log,'profile','intact',-1)
        assert all(r['optimal'] or r['no_path'] for r in rr)
    rate=2*max(rates.values());nv=len(cases);estimated_initial=576*nv*rate
    estimated_round=(24*96*12+24*2*nv/32)*rate+2*opseconds
    write_json(FIXTURES/'profile.json',dict(passed=estimated_initial+96*estimated_round<4200,planning_rate=rate,pool_rates=rates,reproduction_seconds=opseconds,validation_inputs=nv,estimated_initial_seconds=estimated_initial,estimated_round_seconds=estimated_round,estimated_96_round_seconds=estimated_initial+96*estimated_round,budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,scores_used_for_schedule=False,calibration_births_discarded=True))
    print((FIXTURES/'profile.json').read_text(),flush=True)


def choices_packet(states,frozen):
    items={};models={};aliases={}
    for key,s in states.items():
        for name,a in s['archives'].items():items[key+'/'+name]=a['item']
    for key,aa in frozen.items():
        for name,a in aa.items():items[key+'/frozen/'+name]=a['item']
    for k,raw in enumerate(read_compressed(OUT/'pools.json.gz')['carry/0']['protected']):items['anchor/'+str(k)]=raw
    items['anchor/intact']=read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']['intact']
    for a,raw in items.items():pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[a]=pid
    return dict(items=items,models=models,aliases=aliases,frozen_before_final=True)

def run():
    check_freeze(True);p=json.loads((FIXTURES/'profile.json').read_text());assert p['passed'] and json.loads((OUT/'preflight.json').read_text())['passed'] and not (OUT/'validation').exists()
    assert subprocess.check_output(['git','show','HEAD:results/family_evolution_fixtures/profile.json'])==(FIXTURES/'profile.json').read_bytes()
    previous=through_fixtures();v=create(seed_for(SEED,'validation',0,0),'validation',previous);save_generation(v,OUT/'validation');assert len(v.cache)==3872
    d=AccessData(seed_for(SEED,'train',0,0),previous|v.layouts);del previous
    pools=read_compressed(OUT/'pools.json.gz');states={};frozen={};b=Budget();w=warm(v.cache);complete=False;matched=0;max_round=0.;stop='generation_ceiling'
    (OUT/'checkpoints').mkdir();(OUT/'train').mkdir();t=time.perf_counter()
    try:
        with gzip.open(OUT/'initial.jsonl.gz','wt',compresslevel=1) as log:
            for key,pool in pools.items():
                aa={}
                for raw in pool['items']:
                    i=Individual.load(raw);rr=assay(i,v.cache,list(v.cache),b,log,'initial',key,0);update_archives(aa,i,summary(rr,v.metadata),0,dict(family=pool['families'][i.identity],gene_ids=pool['gene_ids'][i.identity]))
                frozen[key]=deepcopy(aa)
                for arm in ARMS:states[key+'/'+arm]=init_state(key+'/'+arm,pool,aa)
                print(json.dumps(dict(initial=key,calls=b.calls,seconds=b.seconds,wall=time.perf_counter()-t)),flush=True)
        initial=b.save();compressed_json(OUT/'frozen.json.gz',frozen);compressed_json(OUT/'initial_states.json.gz',states)
        with gzip.open(OUT/'reproduction.jsonl.gz','wt',compresslevel=1) as births:
            for g in range(MAX_GENERATIONS):
                if time.perf_counter()-t+max(30,1.5*max_round,2*p['estimated_round_seconds']*4)>=SEARCH_WALL:stop='wall_reserve';break
                if b.seconds+max(30,1.5*max_round,2*p['estimated_round_seconds']*4)>=4500:stop='candidate_reserve';break
                start=time.perf_counter();ids=training_batch(d,g);path=OUT/'train'/f'g{g:04d}';save_generation(d,path)
                with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
                    for key,state in states.items():
                        pop=[Individual.load(r) for r in state['population']];rr={i.identity:assay(i,d.cache,ids,b,log,'train',key,g) for i in pop};rank=ranked(pop,rr,d.metadata);aa=deepcopy(state['archives'])
                        if (g+1)%VALIDATE_EVERY==0:
                            for i in nominees(rank):
                                vr=assay(i,v.cache,list(v.cache),b,log,'validation',key,g);update_archives(aa,i,summary(vr,v.metadata),g,lineage(state,i))
                        new,event=reproduce(state,rank,aa);logrow(births,event);states[key]=new
                matched=g+1;max_round=max(max_round,time.perf_counter()-start);clear_batch(d)
                if matched%32==0:compressed_json(OUT/f'checkpoints/g{matched}.json.gz',states)
                compressed_json(OUT/'latest_states.json.gz',states)
                print(json.dumps(dict(generation=matched,calls=b.calls,seconds=round(b.seconds,2),wall=round(time.perf_counter()-t,2),positive={k:s['archives']['primary']['metrics']['positive'] for k,s in states.items()})),flush=True)
                if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>3*2**30:raise OSError('Z3GiB artifact cap')
        compressed_json(OUT/'next_states.json.gz',states);compressed_json(OUT/'choices.json.gz',choices_packet(states,frozen));complete=True
    finally:
        compressed_json(OUT/'latest_states.json.gz',states)
        write_json(OUT/'search_execution.json',dict(complete=complete,generations=matched,stop=stop,initial_budget=locals().get('initial'),budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,largest_round_wall=max_round,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,whole_layouts=len(d.layouts)))

def confirm():
    check_freeze(True);assert not (OUT/'confirmation').exists();ex=json.loads((OUT/'search_execution.json').read_text());assert ex['complete']
    assert subprocess.check_output(['git','show','HEAD:results/family_evolution/choices.json.gz'])==(OUT/'choices.json.gz').read_bytes()
    t=time.perf_counter();previous=through_fixtures();add_layouts(previous,OUT/'validation')
    for path in sorted((OUT/'train').glob('g*/mazes.json.gz')):add_layouts(previous,path.parent)
    d=create(seed_for(SEED,'confirmation',0,0),'confirmation',previous);path=OUT/'confirmation';save_generation(d,path);del previous
    choices=read_compressed(OUT/'choices.json.gz');b=Budget(600);initial=b.save();w=warm(d.cache);metrics={};complete=False;bc=0
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
    states=read_compressed(OUT/'next_states.json.gz');frozen=read_compressed(OUT/'frozen.json.gz');c=read_compressed(OUT/'choices.json.gz');m=read_compressed(OUT/'confirmation/metrics.json.gz');out={}
    _,_,vm=load(OUT/'validation');_,_,fm=load(OUT/'confirmation')
    passes={a:{o:[] for o in ('carry','fresh')} for a in ('current_mutation','family_mutation')}
    for origin in ('carry','fresh'):
        for rep in range(3):
            key=f'{origin}/{rep}';v={a:states[key+'/'+a]['archives']['primary']['metrics'] for a in ARMS};v['frozen']=frozen[key]['primary']['metrics']
            f={a:m[c['aliases'][key+'/'+a+'/primary']] for a in ARMS};f['frozen']=m[c['aliases'][key+'/frozen/primary']]
            gates={}
            for arm in passes:
                controls=['resample','frozen']+(['current_mutation'] if arm=='family_mutation' else [])
                vg=gate(v[arm],[v[a] for a in controls],v['frozen'],vm);fg=gate(f[arm],[f[a] for a in controls],f['frozen'],fm)
                coverage=states[key+'/'+arm]['generation']>=96;passed=vg['passed'] and fg['passed'] and coverage
                if passed:passes[arm][origin].append(rep)
                gates[arm]=dict(validation=vg,final=fg,adequate_schedule=coverage,passed=passed)
            out[key]=dict(validation=v,final=f,gates=gates)
    return dict(results=out,passing=passes,replicated={a:{o:len(p)>=2 for o,p in oo.items()} for a,oo in passes.items()})


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','freeze','profile','preflight','run','confirm','analyze','audit'));a=p.parse_args().action
    if a=='analyze':compressed_json(OUT/'analysis.json.gz',analysis_packet())
    elif a=='preflight':
        from .family_evolution_audit import preflight
        preflight()
    elif a=='audit':
        from .family_evolution_audit import audit
        audit()
    else:globals()[a]()
if __name__=='__main__':main()
