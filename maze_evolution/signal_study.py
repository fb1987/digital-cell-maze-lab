"""Paired source-transmission pressure study, branching random-origin V2 populations."""
import argparse
from dataclasses import asdict
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import platform
import random
import resource
import subprocess
import time
from zoneinfo import ZoneInfo
import numpy as np
from .baselines import baseline, warm_baselines
from .datasets import manifest, seed_for
from .evaluator import assess
from .experiment import write_json, write_csv
from .range_study import StudyData, output_row, summarize, benchmark
from .regulatory import Genome
from .regulatory_runtime import Organism, warm_runtime
from .runtime import Limits
from .signal_probe import observe
from .signal_fitness import signal_metrics
from .signal_search import search


def extension_decision(champions):
    details, passes = [], []
    for topology in ('local','evolved'):
        wins = 0
        for replicate in range(3):
            a = champions[f'signal/{topology}/causal/{replicate}']
            b = champions[f'signal/{topology}/current/{replicate}']
            score, control = a['transmission_fitness'][0], b['transmission_fitness'][0]
            initial = a['frozen_transmission_fitness'][0]
            family = a['transmission_families']
            passed = (score >= initial+.10 and score >= control+.05
                      and family.get('perfect',0)>0 and family.get('random',0)>0)
            wins += int(passed)
            details.append(dict(topology=topology,replicate=replicate,initial=initial,
                current=control,causal=score,families=family,signal_pass=passed))
        if wins>=2:
            passes.append(topology)
    # Alternative trigger: at least two extra valid validation routes per topology,
    # relative to both its frozen and current-objective champions. This is still
    # validation evidence, never a final accuracy claim.
    route_passes=[]
    for topology in ('local','evolved'):
        aa=[champions[f'signal/{topology}/causal/{r}'] for r in range(3)]
        bb=[champions[f'signal/{topology}/current/{r}'] for r in range(3)]
        gain=sum(a['fitness'][0]-a['frozen_fitness'][0] for a in aa)
        relative=sum(a['fitness'][0]-b['fitness'][0] for a,b in zip(aa,bb))
        if gain>=2 and relative>=2:
            route_passes.append(topology)
    return dict(extend=bool(passes or route_passes),signal_topologies=passes,
                route_topologies=route_passes,details=details)


def calls_for(champions, replicate, limits):
    calls, organisms = {}, {}
    for key,saved in champions.items():
        c=saved['config']
        if c['replicate']!=replicate:
            continue
        for field,label in (('champion','task'),('transmission','transmission'),
                            ('frozen','frozen_task'),('frozen_transmission','frozen_transmission')):
            arm=f"{c['topology']}/{c['pressure']}/{label}"
            o=Organism(Genome.from_dict(saved[field]['genome']),c['topology'],limits)
            organisms[arm]=o
            calls[arm]=o.react
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        calls[name]=lambda cells,w,h,start,goal,name=name:baseline(name,cells,w,h,start,goal)
    return calls,organisms


def run(out, config):
    out=Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Use a fresh result directory')
    out.mkdir(parents=True,exist_ok=True)
    (out/'checkpoints').mkdir()
    root=Path(__file__).resolve().parents[1]
    write_json(out/'config.json',config)
    source_paths=sorted((root/'maze_evolution').glob('*.py'))+sorted((root/'tests').glob('*.py'))+[root/'docs/SIGNAL_PRESSURE_V3.md']
    sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    previous=json.loads((root/'results/first_evolution/mazes.json').read_text())
    with gzip.open(root/'results/range_and_regulation/mazes.json.gz','rt') as f:
        previous+=json.load(f)
    prior_hashes={r['sha256'] for r in previous}
    data=StudyData(config['seed'],prior_hashes)
    started=time.perf_counter()
    deadline=started+config['max_seconds']
    warm_runtime(); warm_baselines()
    # Compile both source-presence signatures before timed search.
    dummy=Organism(Genome.from_dict(json.loads((root/'results/range_and_regulation/checkpoints/rich_local_random_evolution_0.json').read_text())['population'][0]['genome']))
    for present in (True,False):
        observe(dummy,bytes([1]*9),3,3,0,8,config['horizon'],present)
    champions,forks={}, {}
    history=[]
    stage_times=[]
    gate=None
    for stage,target in enumerate((config['screen_generations'],config['extended_generations'])):
        if stage==1 and not gate['extend']:
            break
        stage_start=time.perf_counter()
        for topology in ('local','evolved'):
            for replicate in range(3):
                validation=data.validation(replicate)
                fork=root/f'results/range_and_regulation/checkpoints/rich_{topology}_random_evolution_{replicate}.json'
                forks[str(fork.relative_to(root))]=hashlib.sha256(fork.read_bytes()).hexdigest()
                for pressure in ('current','causal'):
                    if time.perf_counter()>=deadline:
                        print('Compute ceiling reached; preserving all completed checkpoints.',flush=True)
                        break
                    condition=dict(seed=config['seed'],study='signal',topology=topology,
                        origin='random',pressure=pressure,replicate=replicate,
                        population=96,generations=target,rich=True,horizon=config['horizon'],
                        train_limits=config['train_limits'],eval_limits=config['eval_limits'],
                        search_version=3,fork_sha256=forks[str(fork.relative_to(root))])
                    key=f'signal/{topology}/{pressure}/{replicate}'
                    tag=key.replace('/','_')
                    checkpoint=out/'checkpoints'/(tag+'.json')
                    logdir=out/'logs'/f'stage{stage}'
                    logdir.mkdir(parents=True,exist_ok=True)
                    with gzip.open(logdir/(tag+'.genomes.jsonl.gz'),'wt',compresslevel=3) as registry, \
                            gzip.open(logdir/(tag+'.evaluations.jsonl.gz'),'wt',compresslevel=3) as evals:
                        champions[key]=search(condition,
                            lambda g,rep=replicate:data.batch('rich',rep,g+120),
                            validation,registry,evals,history,checkpoint,
                            fork=fork,resume=checkpoint if stage else None,deadline=deadline)
        stage_times.append(time.perf_counter()-stage_start)
        write_json(out/f'stage{stage}_champions.json',champions)
        write_csv(out/'history.csv',history)
        if stage==0:
            gate=extension_decision(champions)
            gate['elapsed_seconds']=time.perf_counter()-started
            write_json(out/'extension_decision.json',gate)
            print(f'SCREEN COMPLETE: extension={gate["extend"]}; signal={gate["signal_topologies"]}; routes={gate["route_topologies"]}',flush=True)
        if time.perf_counter()>=deadline:
            break
    for topology in ('local','evolved'):
        for rep in range(3):
            assert champions[f'signal/{topology}/current/{rep}']['initial_digests']==champions[f'signal/{topology}/causal/{rep}']['initial_digests']
    write_json(out/'champions.json',champions)
    freeze=hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    training_seconds=time.perf_counter()-started
    print(f'ALL CHAMPIONS FROZEN {freeze[:16]}; generating fresh final tests.',flush=True)
    rows,timings,signals=[],[],[]
    limits=Limits(**config['eval_limits'])
    for replicate in range(3):
        tests=data.tests(replicate,config['samples'])
        calls,organisms=calls_for(champions,replicate,limits)
        for oracle in tests:
            m=oracle.maze
            for arm,call in calls.items():
                r=call(m.cells,m.w,m.h,m.start,m.goal)
                rows.append(output_row(arm,replicate,oracle,r,assess(r,oracle)))
            for arm,o in organisms.items():
                a=observe(o,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],True)
                b=observe(o,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],False)
                signals.append(dict(arm=arm,replicate=replicate,case_id=m.case_id,
                    family=m.family,n=m.w,edges=len(oracle.path)-1,
                    **signal_metrics(a,b,oracle,config['horizon'])))
                del a,b
        timings.extend(benchmark(calls,tests,config['benchmark_repeats'],
            random.Random(seed_for(config['seed'],'signal-timing',replicate,0)),replicate))
        print(f'Unseen evaluation complete for replicate {replicate}.',flush=True)
    for name,values in (('holdout',rows),('signals',signals)):
        with gzip.open(out/(name+'.jsonl.gz'),'wt',compresslevel=9) as f:
            for row in values:
                f.write(json.dumps(row,separators=(',',':'))+'\n')
    with gzip.open(out/'mazes.json.gz','wt',compresslevel=9) as f:
        json.dump(manifest(data.cache.values()),f,separators=(',',':'))
    summary=summarize(rows)
    write_json(out/'summary.json',summary)
    write_csv(out.with_suffix('.csv'),summary)
    write_json(out/'timings.json',timings)
    write_json(out/'forks.json',forks)
    environment=dict(recorded_at=datetime.now(ZoneInfo('America/Toronto')).isoformat(),
        elapsed_seconds=time.perf_counter()-started,training_seconds=training_seconds,stage_seconds=stage_times,
        source_sha256=sources,parent_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        python=platform.python_version(),os=platform.platform(),cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        champions_sha256=freeze,previous_hashes=len(prior_hashes),hash_rejections=data.rejections,
        packages={n:__import__('importlib.metadata',fromlist=['version']).version(n) for n in ('numpy','numba','llvmlite','pillow','pytest')})
    write_json(out/'environment.json',environment)
    print(f'Study complete: {environment["elapsed_seconds"]:.1f}s; report with maze_evolution.signal_report.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='results/source_pressure')
    args=parser.parse_args()
    config=dict(seed=2026101801,screen_generations=32,extended_generations=160,
        max_seconds=5100,horizon=16,samples=8,benchmark_repeats=30,
        train_limits=asdict(Limits(max_steps=256,reads_per_site=4096,instructions_per_site=32768)),
        eval_limits=asdict(Limits(max_steps=1024,reads_per_site=8192,instructions_per_site=131072)))
    run(args.out,config)

if __name__=='__main__':
    main()
