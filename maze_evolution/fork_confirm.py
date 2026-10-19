"""V12G confirmation of frozen selections on fresh minimal forks and matched corridors."""
import gzip,json,time,statistics,resource,subprocess
from collections import Counter,defaultdict
import numpy as np
from .foundation_calibration import ROOT,LIMITS,controls,write_json
from .foundation_study import read_compressed,compressed_json
from .foundation_pair_confirm import normal_row
from .foundation_fitness import correct_exit
from .fork_data import OUT,FIXTURES,SEED,ForkData,exclusions,load,cut_group
from .fork_fitness import annotate
from .fork_study import sha
from .datasets import manifest
from .growth import Individual
from .growth_runtime import Organism
from .regulatory_search import Evaluation
from .evaluator import assess
from .baselines import baseline


def evaluate_model(item,pairs,topology,mode='normal'):
    organism=Organism(item.genome,topology,LIMITS,ablate_nonlocal=mode=='nonlocal_off',goal_pulse=mode!='pulse_off')
    rows=[]
    for pair in pairs:
        part=[]
        for side,o in enumerate(pair.cases):
            m=o.maze;r=organism.react(m.cells,m.w,m.h,m.start,m.goal);row=normal_row(r,o)
            row.update(old_partial=assess(r,o).partial,correct_exit=bool(correct_exit(r.mask,o,side)))
            part.append(row)
        for r in part:r.update(pair_valid=all(x['valid'] for x in part),pair_optimal=all(x['optimal'] for x in part),paired_partial=min(x['partial'] for x in part))
        rows+=part
    return annotate(Evaluation((),[],(),rows,sum(r['dispatches']+r['reads'] for r in rows)),pairs,'current')


def stats(rows):
    fork=[r for r in rows if r['fork']];corridor=[r for r in rows if '/corridor/' in r['case']]
    unreachable=[r for r in rows if not r['reachable']]
    bybase=defaultdict(list)
    for r in fork:bybase[r['case'].split('/d4-')[0].rsplit('/',1)[0]].append(r)
    return dict(inputs=len(rows),fork_inputs=len(fork),fork_valid=sum(r['valid'] for r in fork),fork_optimal=sum(r['optimal'] for r in fork),complete_pairs=sum(r['pair_optimal'] for r in fork)//2,strict_pairs=sum(r['pair_strict'] for r in fork)//2,
        any_complete_bases=sum(any(r['pair_optimal'] for r in x) for x in bybase.values()),all_poses_complete_bases=sum(len(x)==16 and all(r['optimal'] for r in x) for x in bybase.values()),all_poses_strict_bases=sum(len(x)==16 and all(r['pair_strict'] for r in x) for x in bybase.values()),
        corridor_inputs=len(corridor),corridor_optimal=sum(r['optimal'] for r in corridor),no_path=sum(r['no_path'] for r in unreachable),unreachable_inputs=len(unreachable),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),
        by_stage={str(stage):dict(optimal=sum(r['optimal'] for r in fork if f'/stage{stage}/' in r['case']),pairs=sum(r['pair_optimal'] for r in fork if f'/stage{stage}/' in r['case'])//2,strict=sum(r['pair_strict'] for r in fork if f'/stage{stage}/' in r['case'])//2) for stage in range(3)},failures=dict(Counter(r['failure'] for r in rows if not r['optimal'] and not r['no_path'])))


def run():
    out=OUT/'confirmation';assert not out.exists();out.mkdir()
    search=json.loads((OUT/'search_summary.json').read_text());assert sha(OUT/'frozen_selections.json.gz')==search['frozen_sha256']
    for p,h in search['source_sha256'].items():assert sha(ROOT/p)==h,p
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','status','--porcelain','--','maze_evolution','docs/FORK_PRESSURE_V12G.md','tests/test_fork_pressure.py'],text=True)==''
    t=time.perf_counter();prior=exclusions()
    for path in (FIXTURES,OUT):
        c,_=load(path);prior+=manifest(c.values())
    data=ForkData(SEED,prior);pairs=[]
    for stage in range(3):
        for family in ('tree','cyclic'):
            for index in range(4):
                g=data.group('final',0,index,stage,family)
                pairs+=list(g.pairs)+list(data.corridor(g).pairs)
                if stage==0:pairs+=list(cut_group(data,g).pairs)
    data.save(out);assert len(pairs)==448
    frozen=read_compressed(OUT/'frozen_selections.json.gz');models={};aliases={}
    for key,s in frozen.items():
        for phase in ('archives','frozen'):
            for name in ('pair','choice'):
                item=Individual.load(s[phase][name]['item']);mkey=f"{s['config']['topology']}/{item.genome.digest}"
                models.setdefault(mkey,dict(item=item.save(),topology=s['config']['topology']))
                aliases[key+'/'+phase+'/'+name]=mkey
    item=controls()['intact'];models['intact']=dict(item=item.save(),topology='evolved');aliases['intact']='intact'
    compressed_json(out/'models.json.gz',dict(models=models,aliases=aliases))
    summaries={};physical_responses=work=0;allrows={}
    with gzip.open(out/'outputs.jsonl.gz','wt',compresslevel=1) as log:
        for key,entry in models.items():
            ev=evaluate_model(Individual.load(entry['item']),pairs,entry['topology']);allrows[key]=ev.rows
            log.write(json.dumps(dict(model=key,rows=ev.rows),separators=(',',':'))+'\n')
            summaries[key]=stats(ev.rows);physical_responses+=len(ev.rows);work+=ev.work
            print(json.dumps(dict(model=key,complete_pairs=summaries[key]['complete_pairs'],seconds=round(time.perf_counter()-t,1))),flush=True)
    baseline_stats={}
    with gzip.open(out/'baselines.jsonl.gz','wt') as log:
        for name in ('compiled_bfs','compiled_astar','wave_bit'):
            rows=[]
            for pair in pairs:
                for o in pair.cases:
                    m=o.maze;r=baseline(name,m.cells,m.w,m.h,m.start,m.goal);row=normal_row(r,o);rows.append(row)
            assert sum(r['optimal'] for r in rows)==768 and sum(r['no_path'] for r in rows)==128
            log.write(json.dumps(dict(name=name,rows=rows),separators=(',',':'))+'\n')
            baseline_stats[name]=dict(optimal=768,no_path=128,inputs=896)
    ablations=[]
    with gzip.open(out/'ablations.jsonl.gz','wt') as log:
        for key in sorted({v for k,v in aliases.items() if k.endswith('/archives/pair')}):
            successful=[pair for i,pair in enumerate(pairs) if allrows[key][2*i]['fork'] and allrows[key][2*i]['pair_optimal']]
            if not successful:continue
            for mode in ('pulse_off','nonlocal_off'):
                ev=evaluate_model(Individual.load(models[key]['item']),successful,models[key]['topology'],mode)
                log.write(json.dumps(dict(model=key,mode=mode,rows=ev.rows),separators=(',',':'))+'\n')
                ablations.append(dict(model=key,mode=mode,**stats(ev.rows)));physical_responses+=len(ev.rows);work+=ev.work
    # Fair end-to-end input decode, internal update and final mask construction.
    # Genome setup excluded for both; no timing ratio is reported for failed output.
    timings=[]
    for key in sorted({v for k,v in aliases.items() if k.endswith('/archives/pair')}):
        successes=[r for r in allrows[key] if r['optimal']][:32]
        org=Organism(Individual.load(models[key]['item']).genome,models[key]['topology'],LIMITS,goal_pulse=True)
        for r in successes:
            o=data.cache[r['case']];m=o.maze;calls={'candidate':lambda:org.react(m.cells,m.w,m.h,m.start,m.goal),'bfs':lambda:baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal)}
            measurements={}
            for name,call in calls.items():
                for _ in range(3):call()
                values=[]
                for _ in range(5):
                    started=time.perf_counter_ns()
                    for _ in range(10):result=call()
                    values.append((time.perf_counter_ns()-started)/10)
                    assert assess(result,o).optimal
                measurements[name]=dict(ns=values,median_ns=statistics.median(values),min_ns=min(values),max_ns=max(values))
            timings.append(dict(model=key,case=r['case'],measurements=measurements,ratio=measurements['candidate']['median_ns']/measurements['bfs']['median_ns']))
    write_json(out/'timing.json',timings)
    summary=dict(freeze_revision=revision,source_sha256=search['source_sha256'],frozen_sha256=search['frozen_sha256'],previous_layouts=data.previous_count,resulting_layouts=len(data.layouts),bases=24,fork_inputs=384,corridor_inputs=384,no_path_inputs=128,aliases=aliases,models=summaries,baselines=baseline_stats,ablations=ablations,
        candidate_responses=physical_responses,work=work,elapsed_seconds=time.perf_counter()-t,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(out/'summary.json',summary)

if __name__=='__main__':run()
