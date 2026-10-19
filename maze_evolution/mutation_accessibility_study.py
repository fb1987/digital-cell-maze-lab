"""V12R performance-blind neighborhoods, frozen choices, bounded untouched final."""
import argparse,gzip,json,random,time,resource,subprocess,platform
from importlib.metadata import version
from .mutation_accessibility_data import *
from .mutation_accessibility_metrics import summary,compare,choose
from .exposure_genome import Individual,Genome
from .exposure_selection import physical,organism,record
from .growth import mutate,replay_mutation,random_genome
from .shared_prefix_study import PRIOR as Q_PRIOR,warm,assay,save_generation
from .routing_transfer import canonical,sha,logrow,lines
from .foundation_calibration import write_json
from .baselines import baseline
from .foundation_pair_confirm import normal_row

ARMS=('depth1','depth4','depth16','resample');DEPTHS=(1,4,16);PRIOR=(*Q_PRIOR,'shared_prefix')

class Budget:
    def __init__(self,seconds=720,saved=None):
        self.cap_seconds=seconds;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
        if saved:self.__dict__.update(saved)
    def call(self,fn):
        if self.seconds>=self.cap_seconds-max(.5,2*self.maximum) or self.calls>=5000000 or self.work>=2000000000000:raise TimeoutError('Closed R cap; no extension')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('R4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t;self.seconds+=dt;self.calls+=1;self.maximum=max(self.maximum,dt);self.work+=r.spatial_reads+r.dispatches+r.exposure_checks
        assert self.seconds<self.cap_seconds and self.work<2000000000000
        return r
    def save(self):return vars(self).copy()

def make_pool():
    p=read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items'];q=read_compressed(ROOT/'results/shared_prefix/choices.json.gz')['items']
    roots={'P9':p['route/d9'],'Qfresh0':q['fresh/0/mixed/primary'],'Qcurrent1':q['fresh/1/current/primary'],'Qfresh2':q['fresh/2/mixed/primary'],'Qrandom95':q['carry/0/resample/primary']}
    entries={};groups={};events=[];rngs={}
    def add(i,root,label,rep,arm,index):
        entries[i.identity]=dict(item=i.save(),root=root,label=label,rep=rep,arm=arm,index=index,digest=i.genome.digest,static_opcodes=[sum(g.row()[0]==op for g in i.genome.genes) for op in range(18)],static_store_channels=sorted({g.row()[1] for g in i.genome.genes if g.row()[0]==13}))
    for label,raw in roots.items():
        root=Individual.load(raw);add(root,root.identity,label,-1,'root',-1)
        for rep in range(3):
            key=f'{label}/{rep}';groups[key]={a:[] for a in ARMS}
            for index in range(16):
                rng=random.Random(seed_for(SEED,'walk/'+label,rep,index));before=rng.getstate();current=root
                for depth in range(1,17):
                    bh=sha_value(rng.getstate());program,event=mutate(current.genome.program,rng,1,256,True);i=Individual(f'accessibility/{key}/walk{index}/d{depth}',Genome(program,7),current.identity,depth)
                    assert replay_mutation(current.genome.program,event,256)==program
                    add(i,root.identity,label,rep,f'depth{depth}',index);events.append(dict(item=i.identity,event=event,rng_before=bh,rng_after=sha_value(rng.getstate())))
                    if depth in DEPTHS:groups[key][f'depth{depth}'].append(i.identity)
                    current=i
                rngs[f'{key}/walk{index}']=dict(before=before,after=rng.getstate())
            rng=random.Random(seed_for(SEED,'resample/'+label,rep,0));before=rng.getstate()
            for index in range(16):
                i=Individual(f'accessibility/{key}/random{index}',Genome(random_genome(rng,True),7),None,0);add(i,root.identity,label,rep,'resample',index);groups[key]['resample'].append(i.identity)
            rngs[key+'/resample']=dict(before=before,after=rng.getstate())
    known=Individual.load(p['intact']);add(known,known.identity,'intact',-1,'control',-1)
    models={};aliases={}
    for identity,e in entries.items():pid,m=physical(Individual.load(e['item']),'neutral','local');aliases[identity]=pid;models[pid]=m
    return canonical(dict(roots=roots,entries=entries,groups=groups,events=events,rngs=rngs,models=models,aliases=aliases,control=known.identity))

def sha_value(x):return __import__('hashlib').sha256(json.dumps(canonical(x),separators=(',',':')).encode()).hexdigest()

def eligible(pool,n):
    ids={raw['id'] for raw in pool['roots'].values()}|{pool['control']}
    for g in pool['groups'].values():
        for a in ARMS:ids.update(g[a][:n])
    return ids

def prior_check():
    n=0
    for stage in PRIOR:
        for name,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/name)==h,name;n+=1
    return n

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();pool=make_pool();compressed_json(OUT/'pool.json.gz',pool)
    previous=exclusions();d=create(FIXTURE_SEED,'fixture',previous);assert d.previous_count==187416;d.save(FIXTURES)
    s=create(FIXTURE_SEED+1,'confirmation',previous+manifest(d.cache.values()));s.save(OUT/'software_fixtures')
    write_json(OUT/'preparation.json',dict(candidate_calls=0,roots=len(pool['roots']),walks=240,mutations=len(pool['events']),random_draws=240,prior_hashes=prior_check(),whole_layouts=len(s.layouts)))

def freeze():
    assert not (OUT/'preregistration.json').exists()
    sources=[ROOT/'cellular_maze_lab.py',ROOT/'docs/MUTATION_ACCESSIBILITY_V12R.md',ROOT/'tests/test_mutation_accessibility.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for root in (OUT,FIXTURES) for p in root.rglob('*') if p.is_file() and p.suffix!='.log']+[ROOT/'results/shared_prefix/choices.json.gz',ROOT/'results/shared_prefix/completion.json',ROOT/'results/mutation_transition/panel.json.gz']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,sources={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},python=platform.python_version(),platform=platform.platform(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},scientific_calls=0))

def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for name,h in p[group].items():assert sha(ROOT/name)==h,name
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/mutation_accessibility/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return p

def identities_for_models(pool,ids):
    out={}
    for i in sorted(ids):out.setdefault(pool['aliases'][i],i)
    return dict(sorted(out.items()))

def evaluate_stage(pool,ids,cases,meta,path,b,stage,query=None):
    query=list(cases) if query is None else query;mapping=identities_for_models(pool,ids);compressed_json(path/'mapping.json.gz',mapping);metrics={};rates={}
    with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for k,(pid,identity) in enumerate(mapping.items()):
            before=b.seconds;rows=assay(Individual.load(pool['entries'][identity]['item']),cases,query,b,log,stage,pid,-1);rates[pid]=(b.seconds-before)/len(query);metrics[pid]=summary(rows,meta)
            if (k+1)%100==0:print(json.dumps(dict(stage=stage,models=k+1,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
            if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:raise OSError('R2GiB artifact cap')
    compressed_json(path/'metrics.json.gz',metrics);compressed_json(path/'rates.json.gz',rates);return metrics,rates

def profile():
    check_freeze(True);assert not (FIXTURES/'profile.json').exists();t=time.perf_counter();pool=read_compressed(OUT/'pool.json.gz');cases,_,meta=load(FIXTURES);w=warm(cases);b=Budget(120);query=[c for c,m in meta.items() if m['pose']==0 and not m['stress']]
    _,rates=evaluate_stage(pool,eligible(pool,16),cases,meta,FIXTURES,b,'fixture',query)
    group_rates={f'{k}/{a}':sum(rates[pool['aliases'][i]] for i in ids)/len(ids) for k,g in pool['groups'].items() for a,ids in g.items()};rate=2*max(group_rates.values());plans={n:(6+60*n)*768+126*768+66*5184 for n in (16,8,4)};options=[n for n,c in plans.items() if rate*c<600];n=options[0] if options else 0
    write_json(FIXTURES/'profile.json',dict(passed=bool(n),walks_per_root_block=n,planning_rate=rate,group_rates=group_rates,planned_calls_upper=plans.get(n,0),projected_seconds=rate*plans.get(n,0),budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,scores_used_for_schedule=False));print((FIXTURES/'profile.json').read_text(),flush=True)

def stage_previous():return exclusions()+read_compressed(FIXTURES/'mazes.json.gz')+read_compressed(OUT/'software_fixtures/mazes.json.gz')

def run():
    check_freeze(True);p=json.loads((FIXTURES/'profile.json').read_text());assert p['passed'];assert not (OUT/'discovery').exists()
    assert subprocess.check_output(['git','show','HEAD:results/mutation_accessibility_fixtures/profile.json'])==(FIXTURES/'profile.json').read_bytes()
    t=time.perf_counter();pool=read_compressed(OUT/'pool.json.gz');n=p['walks_per_root_block'];previous=stage_previous();d=create(SEED,'discovery',previous);save_generation(d,OUT/'discovery');b=Budget();w=warm(d.cache);complete=False
    try:
        metrics,_=evaluate_stage(pool,eligible(pool,n),d.cache,d.metadata,OUT/'discovery',b,'discovery');choices={};valid={raw['id'] for raw in pool['roots'].values()}|{pool['control']}
        for key,g in pool['groups'].items():
            choices[key]={}
            for a in ARMS:choices[key][a]=choose(g[a][:n],pool,metrics);valid.update(choices[key][a]['nominees'])
        compressed_json(OUT/'discovery_choices.json.gz',choices)
        v=create(seed_for(SEED,'validation',0,0),'validation',previous+manifest(d.cache.values()));save_generation(v,OUT/'validation');vm,_=evaluate_stage(pool,valid,v.cache,v.metadata,OUT/'validation',b,'validation');sel={}
        for key,g in choices.items():sel[key]={a:choose(g[a]['nominees'],pool,vm) for a in ARMS}
        compressed_json(OUT/'selections.json.gz',sel);final_ids={raw['id'] for raw in pool['roots'].values()}|{pool['control']}
        for g in sel.values():final_ids.update(g[a]['best'] for a in ARMS)
        compressed_json(OUT/'final_panel.json.gz',dict(mapping=identities_for_models(pool,final_ids),ids=sorted(final_ids),selections=sel));complete=True
    finally:write_json(OUT/'selection_execution.json',dict(complete=complete,budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))

def confirm():
    check_freeze(True);assert not (OUT/'confirmation').exists();execution=json.loads((OUT/'selection_execution.json').read_text());assert execution['complete']
    assert subprocess.check_output(['git','show','HEAD:results/mutation_accessibility/final_panel.json.gz'])==(OUT/'final_panel.json.gz').read_bytes()
    t=time.perf_counter();previous=stage_previous()
    for stage in ('discovery','validation'):previous+=read_compressed(OUT/stage/'mazes.json.gz')
    d=create(seed_for(SEED,'confirmation',0,0),'confirmation',previous);path=OUT/'confirmation';save_generation(d,path);pool=read_compressed(OUT/'pool.json.gz');panel=read_compressed(OUT/'final_panel.json.gz');b=Budget(saved=execution['budget']);initial=b.save();w=warm(d.cache);complete=False;bc=0
    try:
        metrics,_=evaluate_stage(pool,panel['ids'],d.cache,d.metadata,path,b,'confirmation')
        known=metrics[pool['aliases'][pool['control']]];assert known['optimal']==3456 and known['no_path']==1728
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for o in d.cache.values():
                    m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert r['optimal'] or r['no_path'];logrow(log,dict(model=name,row=r));bc+=1
        complete=True
    finally:write_json(path/'execution.json',dict(complete=complete,initial_budget=initial,budget=b.save(),warmup=w,baseline_calls=bc,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))

def analysis_packet():
    pool=read_compressed(OUT/'pool.json.gz');sel=read_compressed(OUT/'selections.json.gz');dm=read_compressed(OUT/'discovery/metrics.json.gz');vm=read_compressed(OUT/'validation/metrics.json.gz');fm=read_compressed(OUT/'confirmation/metrics.json.gz');n=json.loads((FIXTURES/'profile.json').read_text())['walks_per_root_block'];out={};supply={};passed={a:{kind:[] for kind in ('correct','partial')} for a in ('depth4','depth16')}
    for key,g in pool['groups'].items():
        out[key]={};supply[key]={};root=pool['entries'][g['depth1'][0]]['root'];rp=pool['aliases'][root]
        for arm in ARMS:
            identity=sel[key][arm]['best'];pid=pool['aliases'][identity];m=fm[pid];v=vm[pid];out[key][arm]=dict(id=identity,root=root,final=m,validation=v,final_comparison=compare(m,fm[rp]),validation_comparison=compare(v,vm[rp]))
            cs=[compare(dm[pool['aliases'][i]],dm[rp]) for i in g[arm][:n]]
            supply[key][arm]=dict(candidates=n,changed=sum(c['changed'] for c in cs),counter_changed=sum(c['counters_changed'] for c in cs),correct=sum(c['correct'] for c in cs),partial=sum(c['partial'] for c in cs),max_pairs=max(dm[pool['aliases'][i]]['positive'] for i in g[arm][:n]),max_score=max(dm[pool['aliases'][i]]['mean_score'] for i in g[arm][:n]))
        for arm in ('depth4','depth16'):
            target=out[key][arm];gates={}
            for kind in ('correct','partial'):
                passed_stage=[]
                for stage in ('validation','final'):
                    m=target[stage];controls=[out[key][a][stage] for a in ('depth1','resample')]
                    advantage=m['positive']>=max(c['positive'] for c in controls)+8 if kind=='correct' else m['mean_score']>=max(c['mean_score'] for c in controls)+.02-1e-12
                    passed_stage.append(target[stage+'_comparison'][kind] and advantage)
                gates[kind]=all(passed_stage)
                if gates[kind]:passed[arm][kind].append(key)
            target['gates']=gates
    readiness={}
    for arm,pp in passed.items():
        readiness[arm]={kind:sum(sum(k.startswith(label+'/') for k in keys)>=2 for label in pool['roots'])>=2 for kind,keys in pp.items()}
    return dict(results=out,supply=supply,passing_blocks=passed,readiness=readiness,partial_never_authorizes_large_run=True)

def analyze():compressed_json(OUT/'analysis.json.gz',analysis_packet())

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','freeze','profile','run','confirm','analyze','audit'));a=p.parse_args().action
    if a=='audit':
        from .mutation_accessibility_audit import audit
        audit()
    else:globals()[a]()
if __name__=='__main__':main()
