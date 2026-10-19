"""V12G prepare, fixed 12-minute matched pilot, and frozen selection record."""
import argparse,gzip,json,random,time,subprocess,platform,resource,hashlib
from dataclasses import asdict
from pathlib import Path
from contextlib import ExitStack
from io import StringIO
from importlib.metadata import version
from .foundation_calibration import ROOT,LIMITS,write_json
from .foundation_study import compressed_json,read_compressed
from .fork_data import OUT,FIXTURES,SEED,ForkData,exclusions,validation,batch
from .fork_search import Search
from .growth import Individual,random_genome
from .datasets import manifest,seed_for


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def lines(p):
    with gzip.open(p,'rt') as f:
        for line in f:yield json.loads(line)


def parents():
    states=read_compressed(ROOT/'results/foundation_pair/checkpoint.latest.json.gz')['states']
    c=read_compressed(ROOT/'results/foundation_study/frozen_selections.json.gz')
    d=read_compressed(ROOT/'results/foundation_continuation/frozen_selections.json.gz')
    return states,c,d


def prepare():
    assert not OUT.exists();OUT.mkdir();(OUT/'segments').mkdir()
    e,c,d=parents();prepared=[];ancestry={};anchors={}
    for origin in ('carry','fresh'):
        for topology in ('local','evolved'):
            for rep in range(3):
                family=f'{origin}/{topology}/{rep}'
                parent=next(s for s in e if s['config']['study']=='foundation_pair_current' and s['config']['method']=='evolution' and s['config']['topology']==topology and s['config']['replicate']==rep)
                protected=[]
                if origin=='carry':
                    inherited=[c[f'foundation_study/{topology}/fresh/evolution/{rep}'],d[f'foundation_study/{topology}/fresh/evolution/{rep}']]+[s for s in e if s['config']['method']=='evolution' and s['config']['topology']==topology and s['config']['replicate']==rep]
                    seen=set()
                    for s in inherited:
                        items=[s['champion']]+[v['item'] for v in s['skills'].values()]+[v['item'] for v in s.get('common_archives',{}).values()]
                        for item in items:
                            dna=Individual.load(item).genome.digest
                            if dna not in seen:protected.append(item);seen.add(dna)
                    pop=list(parent['population'])
                    missing=[i for i in protected if i['id'] not in {p['id'] for p in pop}]
                    positions=[k for k,i in enumerate(pop) if i['id'] not in {a['id'] for a in protected}]
                    for k,item in zip(reversed(positions),missing):pop[k]=item
                    assert {i['id'] for i in protected}<={i['id'] for i in pop}
                    rng_state=parent['rng_state']
                    ancestry[family]=dict(parent_config=parent['config'],parent_generation=parent['next_generation'],unmodified_population=parent['population'],added_anchors=[i['id'] for i in missing])
                else:
                    rng=random.Random(seed_for(SEED,'founders',rep,0))
                    pop=[Individual(f'fork_founder/{topology}/{rep}/i{k}',random_genome(rng,True),None,0).save() for k in range(96)]
                    rng_state=rng.getstate()
                assert len(protected)<=16 and len(pop)==96
                anchors[family]=[i['id'] for i in protected]
                arms=[('current','evolution'),('branch','evolution')]+([('current','resample')] if origin=='fresh' else [])
                for policy,method in arms:
                    key=f'fork/{origin}/{topology}/{policy}/{method}/{rep}'
                    cfg=dict(origin=origin,topology=topology,policy=policy,method=method,replicate=rep,population=96,elite=24,immigrants=9,limits=asdict(LIMITS),seed=SEED)
                    prepared.append(dict(config=cfg,key=key,population=pop,protected=protected,rng_state=rng_state,serial=0,generation=0,responses=0,work=0,archives={},frozen={},history=[]))
    compressed_json(OUT/'initial_states.json.gz',prepared);compressed_json(OUT/'parent_provenance.json.gz',ancestry)
    write_json(OUT/'anchors.json',anchors)
    print(json.dumps(dict(conditions=len(prepared),anchors={k:len(v) for k,v in anchors.items()}),indent=2))


def source_hashes():
    paths=[*sorted((ROOT/'maze_evolution').glob('*.py')),ROOT/'cellular_maze_lab.py',ROOT/'docs/FORK_PRESSURE_V12G.md',ROOT/'tests/test_fork_pressure.py']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}


def run():
    assert not (OUT/'search_summary.json').exists()
    assert not (OUT/'checkpoint.latest.json.gz').exists(),'Resume requires explicit recovery, never restart the budget'
    assert json.loads((FIXTURES/'calibration_summary.json').read_text())['passed']
    initial=read_compressed(OUT/'initial_states.json.gz')
    input_paths=[OUT/'initial_states.json.gz',OUT/'parent_provenance.json.gz',ROOT/'results/foundation_pair/checkpoint.latest.json.gz',ROOT/'results/foundation_pair/verification.json']+list(FIXTURES.glob('*'))
    metadata=dict(source_sha256=source_hashes(),input_sha256={str(p.relative_to(ROOT)):sha(p) for p in input_paths if p.is_file()},revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        python=platform.python_version(),platform=platform.platform(),packages={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},seconds_budget=720,max_generations=256,seed=SEED)
    # Warm the exact readonly uint8 production signature on a saved software fixture.
    from .fork_data import load
    from .foundation_calibration import controls
    from .fork_fitness import evaluate
    fixture_cases,fixture_groups=load(FIXTURES)
    evaluate(controls()['intact'],fixture_groups[0].pairs[:1],'local',LIMITS,'current')
    started=time.perf_counter()
    previous=exclusions()+manifest(fixture_cases.values());data=ForkData(SEED,previous)
    validations={r:validation(data,r) for r in range(3)}
    searches=[Search(s,StringIO(),StringIO()) for s in initial];segments=[];rounds=0
    def elapsed():return time.perf_counter()-started
    def snapshot():
        compressed_json(OUT/'checkpoint.latest.json.gz',dict(metadata=metadata,rounds=rounds,elapsed_seconds=elapsed(),segments=segments,states=[s.state() for s in searches]))
        data.save(OUT)
    # Identical initial populations in paired policies are evaluated once physically.
    # Aliased initial validation uses the same rows/archives, with zero extra compute.
    with gzip.open(OUT/'initial_evaluations.jsonl.gz','wt',compresslevel=1) as log:
        shared={}
        for s in searches:
            key=(s.config['origin'],s.config['topology'],s.config['replicate']);s.log=log
            if key not in shared:s.initialize(validations[key[2]]);shared[key]=s
            else:
                from copy import deepcopy
                s.archives=deepcopy(shared[key].archives);s.frozen=deepcopy(shared[key].frozen)
    initialized=elapsed();snapshot();round_times=[]
    print(json.dumps(dict(initialization_seconds=initialized,prior_layouts=data.previous_count)),flush=True)
    reason='wall_reserve'
    while rounds<256:
        # Reserve the longest observed round plus checkpoint overhead; never launch
        # a round that is predicted to exceed the fixed total search budget.
        reserve=max(round_times,default=30.)*1.25+3
        if elapsed()+reserve>=720:break
        t=time.perf_counter();names=[f'segments/{rounds:04d}.{kind}.jsonl.gz' for kind in ('lineage','evaluations')]
        with ExitStack() as stack:
            registry,log=[stack.enter_context(gzip.open(OUT/n,'wt',compresslevel=1)) for n in names]
            batches={r:batch(data,r,rounds) for r in range(3)}
            for s in searches[rounds%len(searches):]+searches[:rounds%len(searches)]:
                s.registry,s.log=registry,log;s.step(batches[s.config['replicate']],validations[s.config['replicate']])
        segments.append(dict(generation=rounds,files=names));rounds+=1
        if rounds%4==0:snapshot()
        round_times.append(time.perf_counter()-t)
        print(json.dumps(dict(round=rounds,seconds=round(elapsed(),2),max_validation_pairs=max(s.archives['pair']['rank'][0] for s in searches),max_validation_choices=max(s.archives['choice']['rank'][0] for s in searches))),flush=True)
        if elapsed()>=720:reason='wall_limit_finished_matched_round';break
        if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:reason='storage_limit';break
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:reason='memory_limit';break
    if rounds==256:reason='generation_limit'
    snapshot()
    compressed_json(OUT/'frozen_selections.json.gz',{s.key:dict(config=s.config,archives=s.archives,frozen=s.frozen) for s in searches})
    summary=dict(**metadata,rounds=rounds,reason=reason,initialization_seconds=initialized,elapsed_seconds=elapsed(),max_round_seconds=max(round_times,default=0),responses=sum(s.responses for s in searches),work=sum(s.work for s in searches),max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        prior_layouts=data.previous_count,resulting_layouts=len(data.layouts),frozen_sha256=sha(OUT/'frozen_selections.json.gz'),segments=segments,round_seconds=round_times)
    write_json(OUT/'search_summary.json',summary);print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args()
    prepare() if a.action=='prepare' else run()
