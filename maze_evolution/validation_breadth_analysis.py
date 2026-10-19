"""Preregistered V12I comparison and descriptive context-cluster intervals."""
from collections import defaultdict
import json
import numpy as np

from .foundation_calibration import write_json
from .foundation_study import read_compressed
from .validation_breadth_data import OUT, FAMILIES, load


def metrics(summary):
    strata=summary['strata']
    contexts=set(); cycles=set(); by_stratum=[0]*4
    for key,part in strata.items():
        family,s=key.split('/'); st=int(s[1:])
        if family in FAMILIES:
            by_stratum[st]+=part['pairs']
            contexts.update(b for b,n in part['base_pairs'].items() if n)
        if family=='alternate_cycle':
            cycles.update(b for b,n in part['base_pairs'].items() if n)
    return dict(pairs=summary['rank'][0],branch_shortest=summary['rank'][2],branch_legal=summary['rank'][3],
        corridor_shortest=summary['rank'][4],false_no_path=-summary['rank'][5],
        no_path=sum(s['no_path'] for s in strata.values()),contexts=sorted(contexts),cycle_contexts=sorted(cycles),
        stratum_pairs=by_stratum,
        family_pairs={f:sum(v['pairs'] for k,v in strata.items() if k.startswith(f+'/')) for f in FAMILIES},
        all_eight=sum(s['all_eight_contexts'] for k,s in strata.items() if k.split('/')[0] in FAMILIES))


def gate(narrow,broad):
    return dict(pair_gain=broad['pairs']-narrow['pairs']>=8,
        context_gain=len(broad['contexts'])-len(narrow['contexts'])>=2,
        new_cycle_context=bool(set(broad['cycle_contexts'])-set(narrow['cycle_contexts'])),
        harder_stratum_gain=any(broad['stratum_pairs'][i]>narrow['stratum_pairs'][i] for i in (1,2,3)),
        corridor_retention=broad['corridor_shortest']>=.95*narrow['corridor_shortest'],
        false_no_path_not_worse=broad['false_no_path']<=narrow['false_no_path'])


def analyze(save=True):
    pool=read_compressed(OUT/'pool.json.gz'); chosen=read_compressed(OUT/'selections.json.gz')
    summaries=read_compressed(OUT/'confirmation/summaries.json.gz')
    _,contexts,_=load(OUT/'confirmation')
    cohorts=defaultdict(list); comparisons={}
    for key,selection in chosen.items():
        cfg=pool['conditions'][key]['config']
        cohort='/'.join(str(cfg[k]) for k in ('origin','topology','policy','method'))
        measurements={arm:metrics(summaries[s['model']]) for arm,s in selection.items()}
        criteria=gate(measurements['narrow'],measurements['broad'])
        comparisons[key]=dict(replicate=cfg['replicate'],models={a:s['model'] for a,s in selection.items()},
            **measurements,criteria=criteria,passed=all(criteria.values()))
        cohorts[cohort].append(key)
    report={}; rng=np.random.default_rng(2026101944)
    for cohort,keys in sorted(cohorts.items()):
        keys.sort(key=lambda k:comparisons[k]['replicate'])
        totals={arm:{name:sum(comparisons[k][arm][name] for k in keys)
            for name in ('pairs','branch_shortest','branch_legal','corridor_shortest','no_path','false_no_path')}
            for arm in ('narrow','broad')}
        differences=np.zeros((4,16),dtype=np.int64)
        for c in contexts:
            for key in keys:
                for arm,sign in (('narrow',-1),('broad',1)):
                    summary=summaries[chosen[key][arm]['model']]
                    differences[c['stratum'],c['index']]+=sign*sum(summary['strata'][f'{f}/s{c["stratum"]}']['base_pairs'].get(c['id'],0) for f in FAMILIES)
        boot=np.zeros(2000,dtype=np.int64)
        for st in range(4):
            draws=rng.integers(0,16,size=(2000,16)); boot+=differences[st][draws].sum(axis=1)
        interval=np.quantile(boot,[.025,.975]).tolist()
        report[cohort]=dict(conditions=keys,totals=totals,
            pair_difference=totals['broad']['pairs']-totals['narrow']['pairs'],
            context_bootstrap_95_pair_difference=interval,
            passing_replicates=sum(comparisons[k]['passed'] for k in keys),
            gate_pass=sum(comparisons[k]['passed'] for k in keys)>=2,
            pair_counts_by_replicate={arm:[comparisons[k][arm]['pairs'] for k in keys] for arm in ('narrow','broad')})
    result=dict(cohorts=report,comparisons=comparisons,
        denominators_per_model=dict(branch_pairs=1536,branch_inputs=3072,corridors=1024,no_path=128,independent_contexts=64),
        bootstrap=dict(seed=2026101944,draws=2000,unit='independent context, stratified by prefix/tail; all poses, families and fixed selected models kept together',
            caveat='Descriptive conditional intervals: do not include new lineage/validation-draw uncertainty or multiplicity correction.'),
        unique_narrow=len({s['narrow']['model'] for s in chosen.values()}),
        unique_broad=len({s['broad']['model'] for s in chosen.values()}),
        changed_choices=sum(s['narrow']['model']!=s['broad']['model'] for s in chosen.values()))
    if save:
        write_json(OUT/'analysis.json',result)
        print(json.dumps({c:{k:v[k] for k in ('pair_counts_by_replicate','pair_difference','passing_replicates','gate_pass')} for c,v in report.items()},indent=2))
    return result


if __name__=='__main__': analyze()
