"""V12X registered 12-minute operator activation pilot; no efficacy holdout."""
import argparse,gzip,json,platform,random,resource,subprocess,time
from copy import deepcopy
from importlib.metadata import version
from .linkage_data import *
from .linkage_search import *
from .compatibility_map_study import PRIOR as W_PRIOR
from .shared_prefix_study import assay,warm,save_generation
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .composition_audit import geometry
from .baselines import baseline
from .foundation_pair_confirm import normal_row
from .exposure_selection import physical,organism,record

PRIOR=(*W_PRIOR,'compatibility_map')
CAP=720

class Budget:
    def __init__(self,cap=CAP):self.cap=cap;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
    def save(self):return vars(self).copy()
    def call(self,fn):
        if self.seconds+max(.5,2*self.maximum)>=self.cap or self.calls>=3000000 or self.work>=2000000000000:raise TimeoutError('Closed V12X cap')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t;self.seconds+=dt;self.maximum=max(self.maximum,dt);self.calls+=1;self.work+=r.spatial_reads+r.dispatches+r.exposure_checks
        assert self.seconds<self.cap and self.work<2000000000000
        return r

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
            for k in range(96-len(items)):items.append(Individual(f'linkage/{key}/founder{k}',Genome(random_genome(rng,True),7),None,0).save())
            ids={r['id']:special.get(r['id'],[r['id']+f'/gene{k}' for k in range(len(Individual.load(r).genome.genes))]) for r in items}
            pools[key]=dict(items=items,protected=deepcopy(protected) if origin=='carry' else [],gene_ids=ids,founder_rng_before=before,founder_rng_after=rng.getstate(),search_rng=random.Random(seed_for(SEED,'search/'+origin,rep,0)).getstate())
    return canonical(pools)

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();p=make_pools();compressed_json(OUT/'pools.json.gz',p)
    d=fixture(exclusions());d.save(FIXTURES)
    write_json(OUT/'preparation.json',dict(candidate_calls=0,prior_hashes=prior_check(),geometry=geometry(d.cache,d.metadata),prior_layouts=d.previous_count,new_layouts=len(d.layouts)-d.previous_count))
    prepare_software(d.layouts)
    print(dict(pools=len(p),fixtures=len(d.cache)),flush=True)

def prepare_software(previous):
    d=Data(12345678,previous)
    for g in range(3):
        ids=training_batch(d,g);d.save(OUT/'software_fixtures'/f'g{g:04d}');clear(d)
    write_json(OUT/'software_preparation.json',dict(seed=12345678,candidate_calls=0,whole_layouts=len(d.layouts)))

def through_fixtures():
    old=exclusions()
    for folder in (FIXTURES,*sorted((OUT/'software_fixtures').glob('g*'))):
        cases,_,_=load(folder);old.update(layout_hash(o.maze) for o in cases.values())
    return old

def profile_ids(meta):return [c for c,m in meta.items() if m['index']==0 and m['pose']==0 and m['prefix']==1 and m['graph']=='fork']

def projection(profile,g):
    return g*(36*96*6*2*max(profile['pool_rates'].values())+max(2,2*profile['reproduction_seconds']))

def profile():
    assert not (FIXTURES/'profile.json').exists();pools=read_compressed(OUT/'pools.json.gz');cases,_,meta=load(FIXTURES);ids=profile_ids(meta);assert len(ids)==6
    t=time.perf_counter();b=Budget(180);w=warm(cases);rates={};rrs={};opseconds=0.
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt',compresslevel=1) as log,gzip.open(FIXTURES/'reproduction.jsonl.gz','wt',compresslevel=1) as births:
        for key,pool in pools.items():
            before=b.seconds;pop=[Individual.load(r) for r in pool['items']]
            rr={i.identity:assay(i,cases,ids,b,log,'profile',key,-1) for i in pop};rates[key]=(b.seconds-before)/(96*len(ids));rank=ranked(pop,rr,meta)
            for arm in ARMS:
                state=init_state(key+'/'+arm,pool);start=time.perf_counter();new,event=reproduce(state,rank);opseconds+=time.perf_counter()-start
                logrow(births,dict(calibration_only=True,event=event,next_state_digest=digest(new)))
        known=Individual.load(read_compressed(ROOT/'results/compatibility_map/panel.json.gz')['items']['intact'])
        r=assay(known,cases,list(cases),b,log,'profile','intact',-1);assert all(x['optimal'] or x['no_path'] for x in r)
    p=dict(pool_rates=rates,reproduction_seconds=opseconds);estimates={str(g):projection(p,g) for g in (96,64,32)};ng=next((g for g in (96,64,32) if estimates[str(g)]<600),0)
    write_json(FIXTURES/'profile.json',dict(p,passed=ng>=32,generations=ng,projections=estimates,budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scores_used_for_schedule=False,calibration_births_not_seeded=True))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def freeze():
    assert not (OUT/'preregistration.json').exists()
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/LINKAGE_V12X.md',ROOT/'tests/test_linkage.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for folder in (OUT,FIXTURES) for p in folder.rglob('*') if p.is_file() and p.suffix!='.log']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,pilot_generated=False,wall_cap=CAP,candidate_cap=CAP,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        python=platform.python_version(),platform=platform.platform(),cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')}))

def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for name,h in p[group].items():assert sha(ROOT/name)==h,name
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/linkage_pilot/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return p

def run():
    check_freeze(True);p=json.loads((FIXTURES/'profile.json').read_text());assert p['passed'] and not (OUT/'train').exists()
    pools=read_compressed(OUT/'pools.json.gz');states={key+'/'+a:init_state(key+'/'+a,pool) for key,pool in pools.items() for a in ARMS}
    compressed_json(OUT/'initial_states.json.gz',states);fc,_,_=load(FIXTURES);old=through_fixtures()
    d=Data(seed_for(SEED,'train',0,0),old);b=Budget();w=warm(fc);matched=0;largest=0.;complete=False;stop='planned_generations';t=time.perf_counter();bc=0;opseconds=0.
    (OUT/'train').mkdir();(OUT/'checkpoints').mkdir()
    try:
        with gzip.open(OUT/'reproduction.jsonl.gz','wt',compresslevel=1) as births:
            for g in range(p['generations']):
                if time.perf_counter()-t+max(30,1.5*largest)>=CAP or b.seconds+max(30,1.5*largest)>=CAP:stop='matched_round_reserve';break
                start=time.perf_counter();ids=training_batch(d,g);path=OUT/'train'/f'g{g:04d}';save_generation(d,path);write_json(path/'query.json',dict(ids=ids))
                with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
                    for key,state in states.items():
                        pop=[Individual.load(i) for i in state['population']];rr={i.identity:assay(i,d.cache,ids,b,log,'train',key,g) for i in pop};rank=ranked(pop,rr,d.metadata)
                        stamp=time.perf_counter();new,event=reproduce(state,rank);opseconds+=time.perf_counter()-stamp;logrow(births,event);states[key]=new
                with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
                    for name in ('compiled_bfs','compiled_astar','wave_bit'):
                        for cid in ids:
                            o=d.cache[cid];m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert r['optimal'] or r['no_path'];logrow(log,dict(model=name,row=r));bc+=1
                matched=g+1;clear(d);compressed_json(OUT/'latest_states.json.gz',states)
                if matched%16==0:compressed_json(OUT/f'checkpoints/g{matched}.json.gz',states)
                largest=max(largest,time.perf_counter()-start)
                print(json.dumps(dict(generation=matched,calls=b.calls,seconds=round(b.seconds,2),wall=round(time.perf_counter()-t,2),reproduction_seconds=round(opseconds,2))),flush=True)
                if sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())>3*2**30:raise OSError('3GiB cap')
        compressed_json(OUT/'next_states.json.gz',states);complete=True
    finally:
        compressed_json(OUT/'latest_states.json.gz',states)
        write_json(OUT/'execution.json',dict(complete=complete,generations=matched,planned_generations=p['generations'],stop=stop,budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,largest_round=largest,reproduction_seconds=opseconds,baseline_calls=bc,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,whole_layouts=len(d.layouts)))

def main():
    q=argparse.ArgumentParser();q.add_argument('action',choices=['prepare','profile','freeze','run','analyze','audit']);a=q.parse_args().action
    if a=='analyze':
        from .linkage_analysis import analyze
        analyze()
    elif a=='audit':
        from .linkage_audit import audit
        audit()
    else:globals()[a]()
if __name__=='__main__':main()
