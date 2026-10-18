"""Recover V4 final evaluation after the corner-DFS size9 layout pool failed.

Training and frozen archives are unchanged. Only final size9 perfect layouts
use loop-erased random-walk spanning trees, specified before evaluating outputs.
"""
import argparse,gzip,hashlib,json,platform,random,resource,subprocess,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from .datasets import manifest,seed_for
from .evaluator import Maze,Oracle,assess,distances
from .experiment import write_json,write_csv
from .goal_data import GoalData,GoalPair,layout_hash,prior_manifests
from .goal_fitness import evaluate
from .goal_study import selections
from .range_study import output_row,summarize,benchmark
from .regulatory_runtime import warm_runtime
from .baselines import warm_baselines
from .runtime import Limits


def wilson_case(root,split,replicate,index):
    seed=seed_for(root,split+'-wilson-v1',replicate,index);rng=random.Random(seed)
    n=9;side=4;tree={rng.randrange(16)};edges=[]
    adjacent=lambda p:[q for q in (p-1,p+1,p-side,p+side) if 0<=q<16 and abs(p%side-q%side)+abs(p//side-q//side)==1]
    while len(tree)<16:
        path=[next(p for p in range(16) if p not in tree)];positions={path[0]:0}
        while path[-1] not in tree:
            q=rng.choice(adjacent(path[-1]))
            if q in positions:
                path=path[:positions[q]+1];positions={p:i for i,p in enumerate(path)}
            else:positions[q]=len(path);path.append(q)
        edges.extend(zip(path,path[1:]));tree.update(path)
    cells=bytearray(81)
    pixel=lambda p:(2*(p//side)+1)*n+2*(p%side)+1
    for p in tree:cells[pixel(p)]=1
    for a,b in edges:cells[(pixel(a)+pixel(b))//2]=1
    opened=[p for p,v in enumerate(cells) if v];start,goal=rng.sample(opened,2)
    case=f'{split}/r{replicate}/{index}/perfect/9x9/wilson'
    return Oracle.build(Maze(bytes(cells),9,9,start,goal,'perfect',seed,split,case))


class FinalData(GoalData):
    def tests(self,replicate,samples=8):
        specs=[(n,f) for n in (9,17,33,65) for f in ('perfect','random') for _ in range(samples)]
        specs += [(n,'disconnected') for n in (9,17,33,65) for _ in range(4)]
        specs += [(n,'rectangular') for n in (9,17) for _ in range(4)]
        cases=[]
        for i,(n,family) in enumerate(specs):
            for salt in range(4000):
                oracle=wilson_case(self.seed,'test_goal',replicate,i*10000+salt) if n==9 and family=='perfect' else self.single.case('test_goal',replicate,i*10000+salt,n,family)
                lh=layout_hash(oracle.maze)
                if lh in self.layouts:self.rejections+=1;continue
                self.layouts[lh]='test_goal';self.cache[oracle.maze.case_id]=oracle;cases.append(oracle);break
            else:raise RuntimeError('Cannot create independent repaired primary case')
        return cases

    def paired_tests(self,replicate):
        result=[]
        specs=[(n,f) for n in (9,17,33) for f in ('perfect','random')]+[(9,'disconnected'),(17,'disconnected')]
        for i,(n,family) in enumerate(specs):
            if (n,family)!=(9,'perfect'):
                result.append(self.pair('test_pairs',replicate,i,n,family,64));continue
            for salt in range(4000):
                base=wilson_case(self.seed,'test_pairs',replicate,i*10000+salt);m=base.maze;lh=layout_hash(m)
                if lh in self.layouts:self.rejections+=1;continue
                d=distances(m,m.start);possible=[p for p,v in enumerate(d) if v>=8]
                rng=random.Random(seed_for(self.seed,'test_pairs-goals-wilson',replicate,salt));rng.shuffle(possible)
                chosen=None
                for a in possible:
                    between=distances(m,a)
                    b=next((b for b in possible if b!=a and between[b]>=max(d[a],d[b])),None)
                    if b is not None:chosen=(a,b);break
                if chosen is None:self.rejections+=1;continue
                cases=[Oracle.build(Maze(m.cells,9,9,m.start,goal,'perfect',m.seed,'test_pairs',m.case_id+'/'+label)) for label,goal in zip(('a','b'),chosen)]
                pair=GoalPair(*cases);self.layouts[lh]='test_pairs'
                for o in cases:self.cache[o.maze.case_id]=o
                self.pairs[('test_pairs',replicate,i,n,family,64)]=pair;result.append(pair);break
            else:raise RuntimeError('Cannot create independent repaired pair')
        return result


def recover(out,training_revision='0ecb1ad',training_sources=None):
    out=Path(out);root=Path(__file__).resolve().parents[1];started=time.perf_counter()
    if (out/'environment.json').exists():raise FileExistsError('Final evaluation already completed')
    champions=json.loads((out/'champions.json').read_text());config=json.loads((out/'config.json').read_text())
    gate=json.loads((out/'extension_decision.json').read_text());frozen=hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    assert not gate['extend'] and all(s['next_generation']==40 for s in champions.values())
    revision=training_revision;tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'maze_evolution'],text=True).splitlines()
    sources=[p for p in tracked if p.endswith('.py')]+['cellular_maze_lab.py','tests/test_goal_pressure.py','docs/GOAL_STUDY_V4.md']
    source_hashes=training_sources or {p:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+p])).hexdigest() for p in sources}
    assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in source_hashes.items())
    repair=dict(reason='Original corner-start DFS size9 perfect generator rejected 4000 seeds before fourth fresh primary layout; no final candidate output had been evaluated.',
        change='Only final size9 perfect mazes use Wilson loop-erased random-walk spanning trees; other final generators unchanged.',
        frozen_champions_sha256=frozen,training_unchanged=True,original_revision=revision,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),specified_at=datetime.now(ZoneInfo('America/Toronto')).isoformat())
    write_json(out/'final_generation_repair.json',repair)
    previous=prior_manifests(root);data=FinalData(config['seed'],previous)
    for rep in range(3):
        data.validation(rep)
        for g in range(40):data.batch(rep,g)
    warm_runtime();warm_baselines();limits=Limits(**config['eval_limits']);rows=[];paired_rows=[];timings=[]
    for rep in range(3):
        tests=data.tests(rep,config['samples']);pairs=data.paired_tests(rep);calls,items=selections(champions,rep,limits)
        for oracle in tests:
            m=oracle.maze
            for arm,call in calls.items():
                r=call(m.cells,m.w,m.h,m.start,m.goal);rows.append(output_row(arm,rep,oracle,r,assess(r,oracle)))
        for arm,(item,topology) in items.items():
            ev=evaluate(item,pairs,topology,limits,'transmission',config['horizon'])
            paired_rows.append(dict(arm=arm,replicate=rep,id=item.identity,goal=ev.goal_score,signal=ev.long_signal,
                quality=ev.goal_quality,specificity=ev.goal_specificity,both=ev.pair_both,
                work=ev.work,inference_work=ev.inference_work,probe_work=ev.probe_work,cases=ev.rows))
        for name in ('compiled_bfs','compiled_astar','wave_bit'):
            for pair in pairs:
                for oracle in pair.cases:
                    m=oracle.maze;r=calls[name](m.cells,m.w,m.h,m.start,m.goal)
                    paired_rows.append(dict(arm=name,replicate=rep,baseline=output_row(name,rep,oracle,r,assess(r,oracle))))
        timings.extend(benchmark(calls,tests,config['benchmark_repeats'],random.Random(seed_for(config['seed'],'goal-timing',rep,0)),rep))
        print(f'Recovered final evaluation complete: replicate {rep}',flush=True)
    assert frozen==hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    for name,values in (('holdout',rows),('paired_holdout',paired_rows)):
        with gzip.open(out/(name+'.jsonl.gz'),'wt',compresslevel=9) as f:
            for r in values:f.write(json.dumps(r,separators=(',',':'))+'\n')
    with gzip.open(out/'mazes.json.gz','wt',compresslevel=9) as f:json.dump(manifest(data.cache.values()),f,separators=(',',':'))
    write_json(out/'pairs.json',data.pair_manifest());write_json(out/'timings.json',timings)
    summary=summarize(rows);write_json(out/'summary.json',summary);write_csv(out.with_suffix('.csv'),summary)
    forks={f"results/source_pressure/checkpoints/signal_{s['config']['topology']}_causal_{s['config']['replicate']}.json":s['config']['fork_sha256'] for s in champions.values()}
    write_json(out/'forks.json',forks);seconds=time.perf_counter()-started
    environment=dict(recorded_at=datetime.now(ZoneInfo('America/Toronto')).isoformat(),training_seconds=gate['elapsed_seconds'],
        elapsed_seconds=gate['elapsed_seconds']+seconds,recovered_final_seconds=seconds,
        timing_scope='Sum of recorded training window and recovered final process; excludes failed sampling attempt and repair development gap.',
        source_sha256=source_hashes,parent_revision=revision,python=platform.python_version(),os=platform.platform(),
        cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        rss_scope='Recovered final process maximum only; original training high-water mark unavailable. Observed training RSS was approximately120MiB.',
        champions_sha256=frozen,previous_hashes=len({r['sha256'] for r in previous}),layout_rejections=data.rejections,
        packages={n:__import__('importlib.metadata',fromlist=['version']).version(n) for n in ('numpy','numba','llvmlite','pillow','pytest')})
    write_json(out/'environment.json',environment);print(f'Final evaluation recovered in {seconds:.1f}s.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/goal_conditioning')
    parser.add_argument('--run',action='store_true',help='Run the registered study and recover this specific sampling failure')
    args=parser.parse_args();revision='0ecb1ad';sources=None
    if args.run:
        from dataclasses import asdict
        from .goal_study import run
        root=Path(__file__).resolve().parents[1]
        paths=[p for p in (root/'maze_evolution').glob('*.py') if p.name not in {'goal_audit.py','goal_report.py','goal_diagnostics.py'}]
        paths += [root/'cellular_maze_lab.py',root/'tests/test_goal_pressure.py',root/'docs/GOAL_STUDY_V4.md']
        sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        try:
            run(args.out,dict(seed=2026101802,screen_generations=40,extended_generations=160,max_seconds=4500,horizon=16,
                samples=8,benchmark_repeats=30,train_limits=asdict(Limits(max_steps=256,reads_per_site=4096,instructions_per_site=32768)),
                eval_limits=asdict(Limits(max_steps=1024,reads_per_site=8192,instructions_per_site=131072))))
        except RuntimeError as error:
            if str(error)!='Cannot generate an independent primary test':raise
        else:raise SystemExit(0)
    recover(args.out,revision,sources)
