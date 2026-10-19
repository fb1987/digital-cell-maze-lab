"""V12K staged calibration, registration, independent assay and matched evolution."""
import argparse,gzip,json,random,time,subprocess,platform,resource
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict
from contextlib import ExitStack
from io import StringIO
from importlib.metadata import version
from .foundation_calibration import ROOT,LIMITS,write_json
from .foundation_study import compressed_json,read_compressed
from .foundation_pair_confirm import normal_row
from .growth import Individual,random_genome
from .datasets import seed_for,manifest
from .routing_transfer import sha,canonical,lines,logrow,organism,inference
from .robustness_data import *
from .robustness_search import Search,evaluate,annotate,ARCHIVES
from .baselines import baseline


class Budget:
    def __init__(self,seconds,calls,deadline=None):
        self.cap_seconds=seconds;self.cap_calls=calls;self.deadline=deadline
        self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
    def call(self,fn):
        reserve=max(.25,2*self.maximum)
        if self.calls>=self.cap_calls or self.seconds>=self.cap_seconds-reserve or (self.deadline and time.perf_counter()>=self.deadline-reserve):
            raise TimeoutError('Closed V12K budget; keep partial outputs and last matched checkpoint')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t
        self.seconds+=dt;self.calls+=1;self.work+=r.dispatches+r.spatial_reads;self.maximum=max(self.maximum,dt)
        assert self.seconds<self.cap_seconds
        return r
    def save(self):return {k:v for k,v in vars(self).items() if k!='deadline'}


def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();(OUT/'segments').mkdir()
    gs=read_compressed(ROOT/'results/fork_pressure/checkpoint.latest.json.gz')['states']
    pool=read_compressed(ROOT/'results/validation_breadth/pool.json.gz')
    selections=read_compressed(ROOT/'results/validation_breadth/selections.json.gz')
    prepared=[];provenance={}
    for origin in ('carry','fresh'):
        for topology in ('local','evolved'):
            for rep in range(3):
                family=f'{origin}/{topology}/{rep}';protected=[]
                if origin=='carry':
                    parent=next(s for s in gs if s['key']==f'fork/carry/{topology}/branch/evolution/{rep}')
                    items=parent['protected']+[v['item'] for v in parent['archives'].values()]
                    for sel in selections[parent['key']].values():
                        item=deepcopy(pool['models'][sel['model']]['item']);item.update({k:sel['aliases'][0][k] for k in ('id','parent','birth')});items.append(item)
                    seen=set()
                    for i in items:
                        dna=Individual.load(i).genome.digest
                        if dna not in seen:protected.append(i);seen.add(dna)
                    pop=deepcopy(parent['population']);missing=[i for i in protected if i['id'] not in {p['id'] for p in pop}]
                    positions=[k for k,i in enumerate(pop) if i['id'] not in {a['id'] for a in protected}]
                    for k,item in zip(reversed(positions),missing):pop[k]=item
                    rng_state=parent['rng_state']
                    provenance[family]=dict(donor_key=parent['key'],donor_generation=parent['generation'],
                        unmodified_population=parent['population'],added_anchors=missing,protected=protected)
                else:
                    rng=random.Random(seed_for(SEED,'founders',rep,0))
                    pop=[Individual(f'robustness_founder/{topology}/{rep}/i{k}',random_genome(rng,True),None,0).save() for k in range(96)]
                    rng_state=rng.getstate()
                assert len(protected)<=18 and len(pop)==96 and {i['id'] for i in protected}<={i['id'] for i in pop}
                arms=[('pair','evolution'),('context','evolution')]+([('pair','resample')] if origin=='fresh' else [])
                for policy,method in arms:
                    key=f'robustness/{origin}/{topology}/{policy}/{method}/{rep}'
                    cfg=dict(origin=origin,topology=topology,policy=policy,method=method,replicate=rep,population=96,elite=24,immigrants=9,limits=asdict(LIMITS),seed=SEED)
                    prepared.append(dict(config=cfg,key=key,population=pop,protected=protected,rng_state=rng_state,serial=0,generation=0,responses=0,work=0,archives={},frozen={},history=[]))
    compressed_json(OUT/'initial_states.json.gz',prepared);compressed_json(OUT/'parent_provenance.json.gz',provenance)
    panel=read_compressed(ROOT/'results/junction_distance/panel.json.gz');compressed_json(OUT/'panel.json.gz',panel)
    source=['results/fork_pressure/checkpoint.latest.json.gz','results/validation_breadth/pool.json.gz',
        'results/validation_breadth/selections.json.gz','results/junction_distance/panel.json.gz']
    write_json(OUT/'initial_freeze.json',dict(inputs={p:sha(ROOT/p) for p in source},
        frozen={str(p.relative_to(ROOT)):sha(p) for p in OUT.glob('*.gz')},J_informed=True,known_control_in_populations=False))
    data=RobustnessData(FIXTURE_SEED,exclusions());assert data.previous_count==150776
    fixtures(data);data.save(FIXTURES)
    print(json.dumps(dict(conditions=len(prepared),panel=len(panel),fixtures=len(data.cache),layouts=len(data.layouts)-data.previous_count)),flush=True)


def warm(cases,panel):
    m=next(iter(cases.values())).maze;t=time.perf_counter();org=organism(panel['intact'])
    inference(org,m)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(seconds=time.perf_counter()-t,candidate_calls=1,baseline_calls=3,case=m.case_id,readonly_uint8=True)


def metrics(rows,meta):
    rows=deepcopy(rows);annotate(rows,meta)
    groups=defaultdict(list)
    for r in rows:
        if r['branch']:groups[(r['base'],r['family'])].append(r)
    return dict(pairs=sum(r['pair_optimal'] for r in rows)//2,
        contexts=sum(all(r['pair_optimal'] for r in rs) for rs in groups.values()),
        corridor=sum(r['optimal'] for r in rows if r['family'].startswith('corridor')),
        far_pairs=sum(r['pair_optimal'] and r['prefix']>=4 for r in rows)//2,
        optimal=sum(r['optimal'] for r in rows),valid=sum(r['valid'] for r in rows),
        no_path=sum(r['no_path'] for r in rows),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),
        by_group={f'{b}|{f}':sum(r['pair_optimal'] for r in rs)//2 for (b,f),rs in groups.items()})


def calibrate():
    from .robustness_audit import geometry
    assert not (FIXTURES/'calibration.json').exists()
    t=time.perf_counter();cases,contexts,meta=load(FIXTURES);geo=geometry(cases,contexts,meta)
    panel=read_compressed(OUT/'panel.json.gz');warmup=warm(cases,panel);budget=Budget(180,40000)
    results={};profiles={}
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt') as log:
        for name,e in panel.items():
            org=organism(e);rows=[];start=budget.seconds
            for cid,o in cases.items():
                r=budget.call(lambda:inference(org,o.maze));row=normal_row(r,o);rows.append(row);logrow(log,dict(model=name,mode='normal',row=row))
            results[name]=metrics(rows,meta);profiles[name]=dict(seconds=budget.seconds-start,calls=len(rows))
            if name=='intact':assert all(r['optimal'] or r['no_path'] for r in rows)
    # Profile fixed positions from all twelve foundation classes; never choose by performance.
    states=read_compressed(OUT/'initial_states.json.gz');classes={}
    ids=inputs(contexts[0],('fork',),(0,2,4,6),(0,))+inputs(contexts[4],('fork',),(1,3,5,7),(1,))
    with gzip.open(FIXTURES/'profiles.jsonl.gz','wt') as log:
        for s in states:
            c=s['config'];key=f"{c['origin']}/{c['topology']}/{c['replicate']}"
            if key in classes:continue
            before=budget.seconds;calls=budget.calls;t0=time.perf_counter()
            for k in range(0,96,12):
                item=Individual.load(s['population'][k]);ev=evaluate(item,ids,cases,meta,c['topology'],'pair',budget)
                logrow(log,dict(condition=s['key'],id=item.identity,position=k,cases=ev.rows))
            classes[key]=dict(seconds=budget.seconds-before,calls=budget.calls-calls,wall_seconds=time.perf_counter()-t0)
    # Initial screen 96*208 per physical class; subsequent rounds weight every condition.
    initial=sum(v['seconds']/v['calls']*96*208 for v in classes.values())
    per_round=sum(classes[f"{s['config']['origin']}/{s['config']['topology']}/{s['config']['replicate']}"]['seconds']/160*(96*20+4*208/8) for s in states)
    near={}
    for shape in ('straight','turning'):
        bases={c['id'] for c in contexts if c['goal_shape']==shape and c['prefix']==1}
        counts={n:sum(v for k,v in m['by_group'].items() if k.split('|')[0] in bases and k.endswith('|fork')) for n,m in results.items() if n!='intact'}
        near[shape]=dict(counts=counts,passed=max(counts.values())>=4)
    diagnostic_projection=sum(v['seconds']/v['calls']*1920*2 for v in profiles.values())
    passed=all(v['passed'] for v in near.values()) and initial+16*per_round<620 and diagnostic_projection<180
    packet=dict(passed=passed,geometry=geo,warmup=warmup,near=near,panel=results,profiles=profiles,classes=classes,
        projected_initial_candidate_seconds=initial,projected_round_candidate_seconds=per_round,
        projected_diagnostic_candidate_seconds=diagnostic_projection,budget=budget.save(),wall_seconds=time.perf_counter()-t,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(FIXTURES/'calibration.json',packet)
    print(json.dumps({k:packet[k] for k in ('passed','near','projected_initial_candidate_seconds','projected_round_candidate_seconds','projected_diagnostic_candidate_seconds','budget')},indent=2),flush=True)


def freeze():
    assert not (OUT/'preregistration.json').exists()
    assert json.loads((FIXTURES/'calibration.json').read_text())['passed']
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/ROBUSTNESS_PRESSURE_V12K.md',ROOT/'tests/test_robustness_pressure.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},
        inputs={str(p.relative_to(ROOT)):sha(p) for d in (OUT,FIXTURES) for p in d.iterdir() if p.is_file()},
        platform=platform.platform(),python=platform.python_version(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},
        search_wall_cap=720,max_generations=64,max_calls=4000000,diagnostic_seconds=180,final_seconds=360,
        main_generated=False))


def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for path,h in p[group].items():assert sha(ROOT/path)==h,path
    if committed:
        head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        assert head==subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
        for f in ('preregistration.json','panel.json.gz','initial_states.json.gz'):
            assert subprocess.check_output(['git','show',f'HEAD:results/robustness_pressure/{f}'])==(OUT/f).read_bytes()
    return p


def assay(scope):
    check_freeze(True);target=OUT/scope;assert not target.exists()
    previous=exclusions()+read_compressed(FIXTURES/'mazes.json.gz')+read_compressed(FIXTURES/'geometry_test_mazes.json.gz')
    if scope=='final':
        for f in ('diagnostic/mazes.json.gz','search/mazes.json.gz'):previous+=read_compressed(OUT/f)
        assert subprocess.check_output(['git','show','HEAD:results/robustness_pressure/frozen_selections.json.gz'])==(OUT/'frozen_selections.json.gz').read_bytes()
    data=RobustnessData(seed_for(SEED,scope,0,0),previous);confirmation(data,scope);data.save(target)
    models=read_compressed(OUT/'panel.json.gz');aliases={n:n for n in models}
    if scope=='final':
        physical={f"{e['topology']}/{Individual.load(e['item']).genome.digest}":n for n,e in models.items()}
        sels=read_compressed(OUT/'frozen_selections.json.gz')
        for key,s in sels.items():
            for stage in ('archives','frozen'):
                for name in ('context','pair'):
                    e=dict(item=s[stage][name]['item'],topology=s['config']['topology']);dna=f"{e['topology']}/{Individual.load(e['item']).genome.digest}"
                    alias=f'{key}/{stage}/{name}'
                    if dna not in physical:physical[dna]=alias;models[alias]=e
                    aliases[alias]=physical[dna]
    compressed_json(target/'models.json.gz',models);write_json(target/'aliases.json',aliases)
    write_json(target/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        prior_layouts=data.previous_count,new_layouts=len(data.layouts)-data.previous_count,rejections=data.rejections,
        hashes={str(p.relative_to(ROOT)):sha(p) for p in target.iterdir() if p.is_file()}))
    cases,meta=data.cache,data.metadata;f_cases,_,_=load(FIXTURES);warmup=warm(f_cases,models)
    modes=('normal','nonlocal_off') if scope=='diagnostic' else ('normal',)
    planned=len(models)*len(cases)*len(modes);budget=Budget(180 if scope=='diagnostic' else 360,planned);t=time.perf_counter()
    try:
        with gzip.open(target/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for name,e in models.items():
                for mode in modes:
                    org=organism(e,mode)
                    for o in cases.values():
                        r=budget.call(lambda:inference(org,o.maze,mode));logrow(log,dict(model=name,mode=mode,row=normal_row(r,o)))
                print(json.dumps(dict(scope=scope,model=name,calls=budget.calls,seconds=round(budget.seconds,2))),flush=True)
        with gzip.open(target/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for o in cases.values():
                    m=o.maze;row=normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o)
                    assert row['optimal'] or row['no_path'];logrow(log,dict(model=name,row=row))
    finally:
        write_json(target/'execution.json',dict(complete=budget.calls==planned,planned_calls=planned,budget=budget.save(),warmup=warmup,
            wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run():
    check_freeze(True);assert not (OUT/'checkpoint.latest.json.gz').exists() and not (OUT/'search').exists()
    assert json.loads((OUT/'diagnostic/execution.json').read_text())['complete']
    initial=read_compressed(OUT/'initial_states.json.gz');f_cases,_,_=load(FIXTURES);warmup=warm(f_cases,read_compressed(OUT/'panel.json.gz'))
    previous=exclusions()+read_compressed(FIXTURES/'mazes.json.gz')+read_compressed(FIXTURES/'geometry_test_mazes.json.gz')+read_compressed(OUT/'diagnostic/mazes.json.gz')
    prep_started=time.perf_counter();data=RobustnessData(SEED,previous);validations={r:validation(data,r) for r in range(3)}
    # Generation occurs before timer only for the common validation screen, explicitly recorded.
    data.save(OUT/'search');write_json(OUT/'search/validation_ids.json',validations)
    preparation_seconds=time.perf_counter()-prep_started
    start=time.perf_counter();budget=Budget(720,4000000,start+716)
    searches=[Search(s,StringIO(),StringIO(),data.cache,data.metadata,budget) for s in initial]
    rounds=0;segments=[];times=[];reason='reserve';last=[]
    def elapsed():return time.perf_counter()-start
    def snapshot():
        compressed_json(OUT/'checkpoint.latest.json.gz',dict(rounds=rounds,elapsed_seconds=elapsed(),segments=segments,states=[s.state() for s in searches]))
        data.save(OUT/'search')
    try:
        with gzip.open(OUT/'initial_evaluations.jsonl.gz','wt',compresslevel=1) as log:
            shared={}
            for s in searches:
                c=s.config;key=(c['origin'],c['topology'],c['replicate']);s.log=log
                if key not in shared:s.initialize(validations[key[2]]);shared[key]=s
                else:s.archives=deepcopy(shared[key].archives);s.frozen=deepcopy(shared[key].frozen)
        initialized=elapsed();snapshot();last=[s.state() for s in searches]
        print(json.dumps(dict(initialization_seconds=initialized,prior_layouts=data.previous_count)),flush=True)
        while rounds<64:
            reserve=max(times,default=35.)*1.3+8
            if elapsed()+reserve>=716:break
            if budget.calls+82560>4000000:reason='call_reserve';break
            t=time.perf_counter();names=[f'segments/{rounds:04d}.{kind}.jsonl.gz' for kind in ('lineage','evaluations')]
            batches={r:batch(data,r,rounds) for r in range(3)}
            write_json(OUT/'search'/f'batch_{rounds:04d}.json',batches)
            with ExitStack() as stack:
                registry,log=[stack.enter_context(gzip.open(OUT/n,'wt',compresslevel=1)) for n in names]
                for s in searches[rounds%30:]+searches[:rounds%30]:
                    s.registry,s.log=registry,log;s.step(batches[s.config['replicate']],validations[s.config['replicate']])
            segments.append(dict(generation=rounds,files=names));rounds+=1;last=[s.state() for s in searches]
            if rounds%4==0:snapshot()
            times.append(time.perf_counter()-t)
            print(json.dumps(dict(round=rounds,seconds=round(elapsed(),2),best_contexts=max(s.archives['context']['rank'][0] for s in searches),best_pairs=max(s.archives['pair']['rank'][1] for s in searches))),flush=True)
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:reason='memory_cap';break
            if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:reason='storage_cap';break
    except TimeoutError:
        reason='hard_cap_partial_round_preserved'
        compressed_json(OUT/'partial_states.json.gz',[s.state() for s in searches]);assert last,'Initial screen incomplete'
        searches=[Search(s,StringIO(),StringIO(),data.cache,data.metadata) for s in last]
    snapshot()
    compressed_json(OUT/'frozen_selections.json.gz',{s.key:dict(config=s.config,archives=s.archives,frozen=s.frozen) for s in searches})
    write_json(OUT/'search_summary.json',dict(rounds=rounds,reason=reason,initialization_seconds=initialized,
        elapsed_seconds=elapsed(),round_seconds=times,budget=budget.save(),warmup=warmup,preparation_seconds=preparation_seconds,
        logical_calls_per_condition=96*208+rounds*96*20+((rounds+7)//8)*4*208,
        physical_calls_completed=sum(s.responses for s in searches),work_completed=sum(s.work for s in searches),
        prior_layouts=data.previous_count,resulting_layouts=len(data.layouts),rejections=data.rejections,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        frozen_sha256=sha(OUT/'frozen_selections.json.gz')))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','calibrate','freeze','diagnostic','run','final','audit','analyze'))
    a=p.parse_args().action
    if a in ('diagnostic','final'):assay(a)
    elif a=='audit':
        from .robustness_audit import audit
        audit()
    elif a=='analyze':
        from .robustness_analysis import analyze
        analyze()
    else:globals()[a]()

if __name__=='__main__':main()
