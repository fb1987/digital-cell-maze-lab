"""Summarize frozen V12G evidence; never select or modify candidate genomes."""
import gzip,json,statistics,sys
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.fork_confirm import stats
from maze_evolution.fork_study import lines
from maze_evolution.foundation_study import read_compressed
OUT=ROOT/'results/fork_pressure'


def aggregate(summaries):
    names=['fork_inputs','fork_valid','fork_optimal','complete_pairs','strict_pairs','any_complete_bases','all_poses_complete_bases','all_poses_strict_bases','corridor_inputs','corridor_optimal','no_path','unreachable_inputs','false_no_path']
    return {n:sum(s[n] for s in summaries) for n in names}|{'replicates':summaries}


def run():
    summary=json.loads((OUT/'confirmation/summary.json').read_text());saved=read_compressed(OUT/'checkpoint.latest.json.gz')
    cohorts=defaultdict(list);secondary=defaultdict(list);validation=[];aliases=summary['aliases'];models=summary['models']
    states={s['key']:s for s in saved['states']}
    for key,s in states.items():
        c=s['config'];label='/'.join(c[k] for k in ('origin','topology','policy','method'))
        cohorts[label].append(models[aliases[key+'/archives/pair']]);secondary[label].append(models[aliases[key+'/archives/choice']])
        if c['policy']=='current' and c['method']=='evolution':
            cohorts[c['origin']+'/'+c['topology']+'/frozen'].append(models[aliases[key+'/frozen/pair']])
        current=states[f"fork/{c['origin']}/{c['topology']}/current/evolution/{c['replicate']}"]
        a=stats(s['archives']['pair']['rows']);f=stats(s['frozen']['pair']['rows']);control=stats(current['archives']['pair']['rows'])
        extra=states.get(f"fork/fresh/{c['topology']}/current/resample/{c['replicate']}") if c['origin']=='fresh' else None
        resample=stats(extra['archives']['pair']['rows']) if extra else None
        gate=(a['complete_pairs']>=8 and a['any_complete_bases']>=2 and a['all_poses_complete_bases']>=1
            and a['complete_pairs']>=control['complete_pairs']+4 and a['complete_pairs']>=f['complete_pairs']+4
            and a['corridor_optimal']>=.9*f['corridor_optimal'] and (resample is None or a['complete_pairs']>=resample['complete_pairs']+4))
        validation.append(dict(condition=key,config=c,primary=a,frozen=f,control=control,resample=resample,passes=bool(gate)))
    gates={}
    for origin in ('carry','fresh'):
        for topology in ('local','evolved'):
            relevant=[r for r in validation if r['config']['origin']==origin and r['config']['topology']==topology and r['config']['policy']=='branch']
            gates[origin+'/'+topology]=dict(passing_replicates=sum(r['passes'] for r in relevant),passes=sum(r['passes'] for r in relevant)>=2)
    timing=json.loads((OUT/'confirmation/timing.json').read_text());bykind=defaultdict(list)
    for row in timing:bykind['corridor' if '/corridor/' in row['case'] else 'fork'].append(row['ratio'])
    timing_summary={k:dict(cases=len(v),median_ratio=statistics.median(v),min_ratio=min(v),max_ratio=max(v)) for k,v in bykind.items()}
    # Per-base outcomes are counts of distinct common test layouts, not discovery events.
    physical={r['model']:r['rows'] for r in lines(OUT/'confirmation/outputs.jsonl.gz')}
    detail=[];primary_ids={v for k,v in aliases.items() if k.endswith('/archives/pair')}
    for key in primary_ids:
        rows=physical[key]
        detail.append(dict(model=key,optimal_by_family=dict(Counter('cyclic' if '/cyclic/' in r['case'] else 'tree' for r in rows if r['fork'] and r['optimal'])),
            work=sum(r['reads']+r['dispatches'] for r in rows),max_array_bytes=max(r['array_bytes'] for r in rows),nonlocal_reads=sum(sum(r['range_reads'][1:]) for r in rows)))
    result=dict(primary={k:aggregate(v) for k,v in cohorts.items()},secondary={k:aggregate(v) for k,v in secondary.items()},validation=validation,extension_gates=gates,timing=timing_summary,primary_cost=detail)
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{f:v[f] for f in ('fork_optimal','complete_pairs','strict_pairs','corridor_optimal','no_path')} for k,v in result['primary'].items()},indent=2))
    print(json.dumps(dict(gates=gates,timing=timing_summary),indent=2))

if __name__=='__main__':run()
