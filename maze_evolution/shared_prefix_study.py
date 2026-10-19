"""V12Q bounded evolution; immutable registration and pre-final selection freeze."""
import argparse,gzip,json,random,resource,subprocess,time,platform
from copy import deepcopy
from importlib.metadata import version
from .shared_prefix_data import *
from .shared_prefix_search import *
from .exposure_selection import physical,organism,record
from .foundation_calibration import write_json
from .routing_transfer import sha,canonical,logrow,lines
from .baselines import baseline
from .foundation_pair_confirm import normal_row
from .mutation_transition_study import PRIOR as OLD_PRIOR

PRIOR=(*OLD_PRIOR,'mutation_transition')
MAX_GENERATIONS=128
CALL_CAP=5000000
WORK_CAP=2000000000000

class Budget:
    def __init__(self,seconds=720,saved=None):
        self.cap_seconds=seconds;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
        if saved:self.__dict__.update(saved)
    def call(self,fn):
        if self.seconds>=self.cap_seconds-max(.5,2*self.maximum) or self.calls>=CALL_CAP or self.work>=WORK_CAP:raise TimeoutError('Closed Q budget; no extension')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('Q 4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t;self.seconds+=dt;self.calls+=1;self.maximum=max(self.maximum,dt);self.work+=r.spatial_reads+r.dispatches+r.exposure_checks
        assert self.seconds<self.cap_seconds and self.work<WORK_CAP
        return r
    def save(self):return vars(self).copy()

def make_pools():
    p=read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items'];old=read_compressed(ROOT/'results/exposure_calibration/pools.json.gz')
    labels=['route/d9','route/d16','reach1/d16','reach2/d16',*sorted(k for k in p if k.startswith('anchor')),'resample'];protected=[p[k] for k in labels]
    pools={}
    for origin in ('carry','fresh'):
        for rep in range(3):
            key=f'{origin}/{rep}';rng=random.Random(seed_for(SEED,'founders/'+origin,rep,0));before=rng.getstate()
            if origin=='carry':
                items=deepcopy(protected);seen={i['id'] for i in items}
                candidates=sorted(old[f'fresh/{rep}']['items'],key=lambda r:(sha_text(r['id']),r['id']))
                for i in candidates:
                    if i['id'] not in seen and len(items)<96:items.append(i);seen.add(i['id'])
            else:items=[Individual(f'shared_prefix/{key}/founder{i}',Genome(random_genome(rng,True),7),None,0).save() for i in range(96)]
            assert len(items)==96 and len({i['id'] for i in items})==96
            search=random.Random(seed_for(SEED,'search/'+origin,rep,0))
            pools[key]=dict(items=items,protected=deepcopy(protected) if origin=='carry' else [],founder_rng_before=before,founder_rng_after=rng.getstate(),search_rng=search.getstate())
    return canonical(pools)

def sha_text(s):return __import__('hashlib').sha256(s.encode()).hexdigest()

def prior_check():
    n=0
    for stage in PRIOR:
        p=json.loads((ROOT/'results'/stage/'completion.json').read_text())
        for path,h in p['source_and_artifact_sha256'].items():assert sha(ROOT/path)==h,path;n+=1
    return n

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();t=time.perf_counter();OUT.mkdir();pools=make_pools();compressed_json(OUT/'pools.json.gz',pools)
    d=create(FIXTURE_SEED,'fixture',exclusions());assert d.previous_count==181928;d.save(FIXTURES);(OUT/'software_fixtures').mkdir();compressed_json(OUT/'software_fixtures/mazes.json.gz',software_fixture_manifest())
    write_json(OUT/'preparation.json',dict(candidate_calls=0,pools=6,memberships=576,protected_carry=len(pools['carry/0']['protected']),prior_hashes=prior_check(),previous_layouts=d.previous_count,new_layouts=len(d.layouts)-d.previous_count,fixture_inputs=len(d.cache),wall_seconds=time.perf_counter()-t))

def freeze():
    assert not (OUT/'preregistration.json').exists()
    sources=[ROOT/'cellular_maze_lab.py',ROOT/'docs/SHARED_PREFIX_V12Q.md',ROOT/'tests/test_shared_prefix.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for path in (OUT,FIXTURES) for p in path.rglob('*') if p.is_file() and p.suffix!='.log']
    inputs +=[ROOT/'results/mutation_transition/panel.json.gz',ROOT/'results/mutation_transition/completion.json',ROOT/'results/exposure_calibration/pools.json.gz']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,sources={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},python=platform.python_version(),platform=platform.platform(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},candidate_calls=0))

def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for name,h in p[group].items():assert sha(ROOT/name)==h,name
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/shared_prefix/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return p

def warm(cases):
    item=Individual.load(read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']['intact']);m=next(iter(cases.values())).maze
    t=time.perf_counter();organism(physical(item,'neutral','local')[1]).react(m.cells,m.w,m.h,m.start,m.goal)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(candidate_calls=1,baseline_calls=3,seconds=time.perf_counter()-t,case=m.case_id,readonly_bytes=True)

def assay(item,cases,ids,budget,log,stage,key,generation):
    org=organism(physical(item,'neutral','local')[1]);rows=[];before=budget.save()
    for cid in ids:
        o=cases[cid];m=o.maze;r=budget.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));rows.append(record(r,o))
    logrow(log,dict(stage=stage,key=key,generation=generation,id=item.identity,seconds=budget.seconds-before['seconds'],work=budget.work-before['work'],rows=rows))
    return rows

def profile():
    check_freeze(True);assert not (FIXTURES/'profile.json').exists();t=time.perf_counter();cases,contexts,meta=load(FIXTURES);warmup=warm(cases);b=Budget(120);pools=read_compressed(OUT/'pools.json.gz');ids=[c for c,m in meta.items() if m['pose']==0];rates=[]
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for key,p in pools.items():
            before=b.seconds
            for raw in p['items']:assay(Individual.load(raw),cases,ids,b,log,'profile',key,-1)
            rates.append((b.seconds-before)/(96*len(ids)))
    # Conservative fixed planning rate: twice the worst pool mean; never uses fitness.
    rate=2*max(rates);fixed_calls=576*768+78*4032
    options=[g for g in (128,96,64,32,16,8) if rate*(fixed_calls+g*18*96*12+(g//8)*18*2*768)<600]
    generations=options[0] if options else 0
    write_json(FIXTURES/'profile.json',dict(passed=generations>=8,generations=generations,planning_rate=rate,pool_rates=rates,projected_calls=fixed_calls+generations*18*96*12+(generations//8)*18*2*768,projected_seconds=rate*(fixed_calls+generations*18*96*12+(generations//8)*18*2*768),budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,fitness_used_for_schedule=False))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def init_state(key,pool,archives):
    return dict(key=key,arm=key.split('/')[-1],population=deepcopy(pool['items']),protected=deepcopy(pool['protected']),rng=deepcopy(pool['search_rng']),serial=0,generation=0,archives=deepcopy(archives))

def save_generation(d,path):
    d.save(path);write_json(path/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),prior_layouts=d.previous_count,whole_layouts=len(d.layouts),new_layouts=len(d.layouts)-d.previous_count,rejections=d.rejections,inputs=len(d.cache),contexts=len(d.contexts),hashes={str(p.relative_to(ROOT)):sha(p) for p in path.glob('*.gz')}))

def run():
    check_freeze(True);profile=json.loads((FIXTURES/'profile.json').read_text());assert profile['passed'];assert not (OUT/'train').exists()
    assert subprocess.check_output(['git','show','HEAD:results/shared_prefix_fixtures/profile.json'])==(FIXTURES/'profile.json').read_bytes()
    t=time.perf_counter();previous=exclusions()+software_fixtures()+read_compressed(FIXTURES/'mazes.json.gz');ng=profile['generations']
    v=create(seed_for(SEED,'validation',0,0),'validation',previous);save_generation(v,OUT/'validation');previous+=manifest(v.cache.values())
    d=create(seed_for(SEED,'train',0,0),'train',previous,ng);save_generation(d,OUT/'train')
    (OUT/'checkpoints').mkdir();pools=read_compressed(OUT/'pools.json.gz');b=Budget();warmup=warm(v.cache);states={};frozen={};complete=False;matched=0;largest_round=0.;stop='planned_generations';initial_budget=None
    try:
        with gzip.open(OUT/'initial.jsonl.gz','wt',compresslevel=1) as log:
            for key,pool in pools.items():
                archives={}
                for raw in pool['items']:
                    i=Individual.load(raw);rows=assay(i,v.cache,list(v.cache),b,log,'initial',key,0);update_archives(archives,i,summary(rows,v.metadata),0)
                frozen[key]=deepcopy(archives)
                for arm in ARMS:states[key+'/'+arm]=init_state(key+'/'+arm,pool,archives)
                print(json.dumps(dict(initial=key,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
        initial_budget=b.save();compressed_json(OUT/'frozen.json.gz',frozen);compressed_json(OUT/'initial_states.json.gz',states)
        with gzip.open(OUT/'search_responses.jsonl.gz','wt',compresslevel=1) as log,gzip.open(OUT/'reproduction.jsonl.gz','wt',compresslevel=1) as births:
            for g in range(ng):
                # Matched blocks only. Reserve100 candidate seconds for final, never extend.
                if b.seconds+max(largest_round*1.5,10)+100>=720:stop='reserve_rule';break
                before=b.seconds
                for key,state in states.items():
                    pop=[Individual.load(i) for i in state['population']];ids=training_ids(d.metadata,g,state['arm']);rs={i.identity:assay(i,d.cache,ids,b,log,'train',key,g) for i in pop};rank=ranked(pop,rs,d.metadata);archives=deepcopy(state['archives'])
                    if (g+1)%8==0:
                        for i in nominees(rank):
                            vr=assay(i,v.cache,list(v.cache),b,log,'validation',key,g);update_archives(archives,i,summary(vr,v.metadata),g)
                    new,event=reproduce(state,rank,archives);logrow(births,event);states[key]=new
                matched=g+1;largest_round=max(largest_round,b.seconds-before)
                if matched%8==0:compressed_json(OUT/f'checkpoints/g{matched}.json.gz',states)
                print(json.dumps(dict(generation=matched,calls=b.calls,seconds=round(b.seconds,2),positive={k:s['archives']['primary']['metrics']['positive'] for k,s in states.items()})),flush=True)
                if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:raise OSError('Q2GiB output cap')
        compressed_json(OUT/'next_states.json.gz',states);freeze_choices(states,frozen);complete=True
    finally:
        compressed_json(OUT/'latest_states.json.gz',states)
        write_json(OUT/'search_execution.json',dict(complete=complete,generations=matched,planned_generations=ng,stop=stop,initial_budget=initial_budget,budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))

def freeze_choices(states,frozen):
    models={};aliases={};items={}
    def add(alias,raw):
        i=Individual.load(raw);pid,model=physical(i,'neutral','local');models[pid]=model;aliases[alias]=pid;items[alias]=raw
    for key,s in states.items():
        for name,a in s['archives'].items():add(key+'/'+name,a['item'])
    for key,aa in frozen.items():
        for name,a in aa.items():add(key+'/frozen/'+name,a['item'])
    old=read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']
    for label in ('route/d9','route/d16','reach1/d16','reach2/d16','resample','intact'):add('anchor/'+label,old[label])
    assert len(models)<=78
    compressed_json(OUT/'choices.json.gz',dict(models=models,aliases=aliases,items=items,frozen_before_final=True))

def confirm():
    check_freeze(True);assert not (OUT/'confirmation').exists();execution=json.loads((OUT/'search_execution.json').read_text());assert execution['complete']
    assert subprocess.check_output(['git','show','HEAD:results/shared_prefix/choices.json.gz'])==(OUT/'choices.json.gz').read_bytes()
    t=time.perf_counter();previous=exclusions()+software_fixtures()
    for path in (FIXTURES,OUT/'validation',OUT/'train'):previous+=read_compressed(path/'mazes.json.gz')
    d=create(seed_for(SEED,'confirmation',0,0),'confirmation',previous);path=OUT/'confirmation';save_generation(d,path);choices=read_compressed(OUT/'choices.json.gz');warmup=warm(d.cache);b=Budget(saved=execution['budget']);initial=b.save();metrics={};bc=0;complete=False
    try:
        with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for pid,model in choices['models'].items():
                i=next(Individual.load(choices['items'][a]) for a,p in choices['aliases'].items() if p==pid)
                rows=assay(i,d.cache,list(d.cache),b,log,'confirmation',pid,-1);metrics[pid]=summary(rows,d.metadata)
                print(json.dumps(dict(final=pid,calls=b.calls,seconds=round(b.seconds,2),positive=metrics[pid]['positive'])),flush=True)
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for o in d.cache.values():
                    m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert r['optimal'] or r['no_path'];logrow(log,dict(model=name,row=r));bc+=1
        compressed_json(path/'metrics.json.gz',metrics);complete=True
    finally:write_json(path/'execution.json',dict(complete=complete,initial_budget=initial,budget=b.save(),warmup=warmup,baseline_calls=bc,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))

def analysis_packet():
    states=read_compressed(OUT/'next_states.json.gz');frozen=read_compressed(OUT/'frozen.json.gz');choices=read_compressed(OUT/'choices.json.gz');metrics=read_compressed(OUT/'confirmation/metrics.json.gz');out={};passing={o:[] for o in ('carry','fresh')}
    for origin in ('carry','fresh'):
        for rep in range(3):
            key=f'{origin}/{rep}';v={a:states[key+'/'+a]['archives']['primary']['metrics'] for a in ARMS};v['frozen']=frozen[key]['primary']['metrics'];f={a:metrics[choices['aliases'][key+'/'+a+'/primary']] for a in ARMS};f['frozen']=metrics[choices['aliases'][key+'/frozen/primary']]
            vg=gate(v['mixed'],v['current'],v['resample'],v['frozen']);fg=gate(f['mixed'],f['current'],f['resample'],f['frozen']);passed=vg and fg and states[key+'/mixed']['generation']>=16
            if passed:passing[origin].append(rep)
            out[key]=dict(validation=v,final=f,validation_passed=vg,final_passed=fg,passed=passed,selections={a:states[key+'/'+a]['archives']['primary']['item']['id'] for a in ARMS})
    return dict(results=out,passing=passing,larger_run_ready={o:len(v)>=2 for o,v in passing.items()})

def analyze():
    p=analysis_packet();compressed_json(OUT/'analysis.json.gz',p);print(json.dumps({k:dict(validation={a:m['positive'] for a,m in v['validation'].items()},final={a:m['positive'] for a,m in v['final'].items()},passed=v['passed']) for k,v in p['results'].items()},indent=2),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','freeze','profile','run','confirm','analyze','audit'));action=p.parse_args().action
    if action=='audit':
        from .shared_prefix_audit import audit
        audit()
    else:globals()[action]()
if __name__=='__main__':main()
