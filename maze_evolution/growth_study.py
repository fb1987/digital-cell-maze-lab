"""V11 strict paired-choice priority experiment, offline CPU only."""
import argparse
from dataclasses import asdict
from datetime import datetime
import gzip,hashlib,json,platform,random,resource,subprocess,time
from pathlib import Path
from zoneinfo import ZoneInfo
from .baselines import baseline,warm_baselines
from .datasets import manifest,seed_for
from .evaluator import assess
from .experiment import write_json,write_csv
from .growth_data import GrowthData,prior_manifests
from .growth_fitness import evaluate
from .growth_search import search
from .range_study import output_row,summarize,benchmark
from .growth import Genome,Individual
from .growth_runtime import Organism,warm_runtime
from .runtime import Limits


def extension_decision(champions):
    routes=[];choices=[];records=[]
    for topology in ('local','evolved'):
        good=0;route_gain=0
        for rep in range(3):
            a=champions[f'growth/{topology}/cap256/{rep}'];b=champions[f'growth/{topology}/cap128/{rep}']
            r=a['archives']['choice'];f=a['frozen']['choice'];c=b['archives']['choice']
            qualifies=(r['junction_both']>=.5 and r['junction_both']>=f['junction_both']+.25
                and r['junction_both']>=c['junction_both']+.25 and r['junction']>=.4
                and all(r['choice_families'].get(k,0)>0 for k in ('perfect','random')))
            good+=qualifies
            route_gain+=max(0,a['archives']['task']['optimal']-max(a['frozen']['task']['optimal'],b['archives']['task']['optimal']))
            records.append(dict(topology=topology,replicate=rep,qualifies=qualifies,score=r['junction'],both=r['junction_both']))
        if good>=2:choices.append(topology)
        if route_gain>=2:routes.append(topology)
    return dict(extend=bool(routes or choices),goal_topologies=choices,route_topologies=routes,records=records)


def selections(champions,replicate,limits):
    calls={};items={}
    for key,saved in champions.items():
        c=saved['config']
        if c['replicate']!=replicate:continue
        for source,prefix in (('archives',''),('frozen','frozen_')):
            for archive in ('task','choice'):
                arm=f"{c['topology']}/{c['pressure']}/{prefix}{archive}"
                item=Individual.load(saved[source][archive]['individual'])
                items[arm]=(item,c['topology'],c['pressure'])
                calls[arm]=Organism(item.genome,c['topology'],limits,goal_pulse=True,gene_limit=c['gene_limit']).react
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        calls[name]=lambda cells,w,h,start,goal,name=name:baseline(name,cells,w,h,start,goal)
    return calls,items


def source_snapshot(root):
    excluded={'growth_audit.py','growth_report.py','growth_diagnostics.py','growth_equivalence.py'}
    sources=[p for p in (root/'maze_evolution').glob('*.py') if p.name not in excluded]
    sources += [root/'cellular_maze_lab.py',root/'tests/test_growth.py',root/'docs/GROWTH_STUDY_V11.md']
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}


def run(out,config):
    out=Path(out);root=Path(__file__).resolve().parents[1]
    if out.exists() and any(out.iterdir()):raise FileExistsError('Choose a fresh output directory')
    out.mkdir(parents=True,exist_ok=True);(out/'checkpoints').mkdir()
    write_json(out/'config.json',config)
    proof_path=root/'results/capacity_equivalence.json'
    proof=json.loads(proof_path.read_text())
    if not proof['all_checks_passed']:raise ValueError('Old-program equivalence is required')
    for path,h in {**proof['source_sha256'],**proof['input_sha256']}.items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=h:raise ValueError('Equivalence source/input changed')
    write_json(out/'equivalence.json',proof)
    source_hashes=source_snapshot(root)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    previous=prior_manifests(root);data=GrowthData(config['seed'],previous)
    started=time.perf_counter();deadline=started+config['max_seconds']
    warm_runtime();warm_baselines()
    history=[];champions={};forks={};stage_times=[];gate=None
    for stage,target in enumerate((config['screen_generations'],128,config['extended_generations'])):
        if stage and not gate['extend']:break
        phase=time.perf_counter()
        for topology in ('local','evolved'):
            for rep in range(3):
                validation=data.validation(rep)
                fork=[root/f'results/distance_curriculum/checkpoints/distance_{topology}_{a}_{rep}.json' for a in ('fixed','curriculum')]
                supplement=root/'results/distance_curriculum/strict_validation_archive.json'
                ancestry=root/'results/distance_curriculum/training_choice_diagnostic.json'
                supplement_sha=hashlib.sha256(supplement.read_bytes()).hexdigest();ancestry_sha=hashlib.sha256(ancestry.read_bytes()).hexdigest()
                for f in (supplement,ancestry):forks[str(f.relative_to(root))]=hashlib.sha256(f.read_bytes()).hexdigest()
                fork_sha=[hashlib.sha256(f.read_bytes()).hexdigest() for f in fork]
                for f,h in zip(fork,fork_sha):forks[str(f.relative_to(root))]=h
                for pressure in ('cap128','cap256'):
                    if time.perf_counter()>=deadline:break
                    condition=dict(study='growth',search_version=11,origin='random',seed=config['seed'],
                        topology=topology,replicate=rep,pressure=pressure,gene_limit=int(pressure[3:]),population=96,generations=target,
                        horizon=config['horizon'],fork_sha256=fork_sha,supplement_sha256=supplement_sha,ancestry_sha256=ancestry_sha,
                        train_limits=config['train_limits'],eval_limits=config['eval_limits'])
                    key=f'growth/{topology}/{pressure}/{rep}';tag=key.replace('/','_')
                    checkpoint=out/'checkpoints'/(tag+'.json')
                    logs=out/'logs'/f'stage{stage}';logs.mkdir(parents=True,exist_ok=True)
                    with gzip.open(logs/(tag+'.genomes.jsonl.gz'),'wt',compresslevel=3) as registry, \
                            gzip.open(logs/(tag+'.evaluations.jsonl.gz'),'wt',compresslevel=3) as evaluations:
                        champions[key]=search(condition,lambda g,r=rep:data.batch(r,g),validation,
                            registry,evaluations,history,checkpoint,fork=fork,
                            resume=checkpoint if stage else None,deadline=deadline,supplement=supplement,ancestry=ancestry)
        stage_times.append(time.perf_counter()-phase)
        write_json(out/f'stage{stage}_champions.json',champions);write_csv(out/'history.csv',history)
        if stage==0:
            if len(champions)!=12:raise RuntimeError('Screen ceiling reached; partial checkpoints preserved')
            gate=extension_decision(champions);gate['elapsed_seconds']=time.perf_counter()-started
            write_json(out/'extension_decision.json',gate)
            print(f"SCREEN COMPLETE: extend={gate['extend']}; goal={gate['goal_topologies']}; routes={gate['route_topologies']}",flush=True)
        if time.perf_counter()>=deadline:break
    for t in ('local','evolved'):
        for r in range(3):
            assert champions[f'growth/{t}/cap128/{r}']['initial_digests']==champions[f'growth/{t}/cap256/{r}']['initial_digests']
    write_json(out/'champions.json',champions)
    frozen=hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    training_seconds=time.perf_counter()-started
    write_json(out/'training_environment.json',dict(training_seconds=training_seconds,
        source_sha256=source_hashes,parent_revision=revision,champions_sha256=frozen,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(f'ALL GENOMES FROZEN {frozen[:16]}; generating fresh tests.',flush=True)
    limits=Limits(**config['eval_limits']);rows=[];paired_rows=[];timings=[]
    for rep in range(3):
        tests=data.tests(rep,config['samples']);pairs=data.paired_tests(rep)
        with gzip.open(out/'mazes.json.gz','wt',compresslevel=9) as f:json.dump(manifest(data.cache.values()),f,separators=(',',':'))
        write_json(out/'pairs.json',data.pair_manifest())
        calls,items=selections(champions,rep,limits)
        for oracle in tests:
            m=oracle.maze
            for arm,call in calls.items():
                r=call(m.cells,m.w,m.h,m.start,m.goal)
                rows.append(output_row(arm,rep,oracle,r,assess(r,oracle)))
        for arm,(item,topology,mode) in items.items():
            ev=evaluate(item,pairs,topology,limits,mode,config['horizon'])
            paired_rows.append(dict(arm=arm,replicate=rep,id=item.identity,goal=ev.goal_score,signal=ev.long_signal,
                quality=ev.goal_quality,specificity=ev.goal_specificity,both=ev.pair_both,balanced=ev.balanced_goal,balanced_families=ev.balanced_families,
                strict_pairs=ev.strict_pairs,selection_credit=ev.selection_credit,choice_families=ev.choice_families,junction=ev.junction,junction_both=ev.junction_both,junction_families=ev.junction_families,
                work=ev.work,inference_work=ev.inference_work,probe_work=ev.probe_work,cases=ev.rows))
        for name in ('compiled_bfs','compiled_astar','wave_bit'):
            for pair in pairs:
                for oracle in pair.cases:
                    m=oracle.maze;r=calls[name](m.cells,m.w,m.h,m.start,m.goal)
                    paired_rows.append(dict(arm=name,replicate=rep,baseline=output_row(name,rep,oracle,r,assess(r,oracle))))
        timings.extend(benchmark(calls,tests,config['benchmark_repeats'],random.Random(seed_for(config['seed'],'growth-timing',rep,0)),rep))
        print(f'Unseen output, goal-pair and timing evaluation complete for replicate {rep}.',flush=True)
    for name,values in (('holdout',rows),('paired_holdout',paired_rows)):
        with gzip.open(out/(name+'.jsonl.gz'),'wt',compresslevel=9) as f:
            for row in values:f.write(json.dumps(row,separators=(',',':'))+'\n')
    with gzip.open(out/'mazes.json.gz','wt',compresslevel=9) as f:json.dump(manifest(data.cache.values()),f,separators=(',',':'))
    write_json(out/'pairs.json',data.pair_manifest());write_json(out/'timings.json',timings);write_json(out/'forks.json',forks)
    summary=summarize(rows);write_json(out/'summary.json',summary);write_csv(out.with_suffix('.csv'),summary)
    environment=dict(recorded_at=datetime.now(ZoneInfo('America/Toronto')).isoformat(),elapsed_seconds=time.perf_counter()-started,
        training_seconds=training_seconds,stage_seconds=stage_times,source_sha256=source_hashes,parent_revision=revision,
        python=platform.python_version(),os=platform.platform(),cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,champions_sha256=frozen,
        previous_hashes=len({r['sha256'] for r in previous}),
        previous_layouts=len({hashlib.sha256(f"{r['w']},{r['h']}:".encode()+bytes.fromhex(r['cells_hex'])).hexdigest() for r in previous}),
        layout_rejections=data.rejections,packages={n:__import__('importlib.metadata',fromlist=['version']).version(n) for n in ('numpy','numba','llvmlite','pillow','pytest')})
    write_json(out/'environment.json',environment)
    print(f"Study complete: {environment['elapsed_seconds']:.1f}s.",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',default='results/capacity_growth')
    args=parser.parse_args()
    run(args.out,dict(seed=2026101811,screen_generations=48,extended_generations=192,max_seconds=4500,horizon=16,
        samples=8,benchmark_repeats=30,
        train_limits=asdict(Limits(max_steps=256,reads_per_site=4096,instructions_per_site=32768)),
        eval_limits=asdict(Limits(max_steps=1024,reads_per_site=8192,instructions_per_site=131072))))

if __name__=='__main__':main()
