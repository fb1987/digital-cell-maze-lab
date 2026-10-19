"""Descriptive V12H analysis of the frozen panel; never selects new genomes."""
import json
from collections import Counter,defaultdict
from pathlib import Path
import sys
import statistics
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_calibration import write_json
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines,MECHANISM_ALIASES
from maze_evolution.routing_transfer_data import OUT,FAMILIES,load
from maze_evolution.routing_transfer_audit import reaction_fields


def pairs(rows,metadata):
    grouped=defaultdict(list)
    for r in rows:
        m=metadata[r['case']]
        if m['family'] in FAMILIES:
            grouped[m['family'],m['band'],m['base'],m['symmetry']].append(r)
    return {key for key,rs in grouped.items() if len(rs)==2 and all(r['optimal'] for r in rs)}


def totals(s,family=None,band=None):
    selected=[v for k,v in s['strata'].items() if (family is None or k.startswith(family+'/'))
              and (band is None or k.endswith(f'band{band}'))]
    fields=('inputs','valid','optimal','no_path','false_no_path','complete_pairs','any_contexts','all_pose_contexts','strict_pairs')
    return {f:sum(r[f] for r in selected) for f in fields}


def run():
    verification=json.loads((OUT/'verification.json').read_text());assert verification['passed']
    summary=json.loads((OUT/'confirmation/summary.json').read_text())
    packet=read_compressed(OUT/'models.json.gz');_,contexts,metadata=load(OUT/'confirmation')
    cohorts=defaultdict(list);screens={}
    for alias,key in packet['aliases'].items():
        config=packet['configs'][alias];phase=alias.rsplit('/',1)[1]
        origin,topology,policy,method,rep=[config[f] for f in ('origin','topology','policy','method','replicate')]
        if phase=='frozen':
            if policy!='current' or method!='evolution':continue
            arm='frozen'
        else:arm=policy if method=='evolution' else 'resample'
        cohort=f'{origin}/{topology}/{arm}'
        cohorts[cohort].append(dict(replicate=rep,model=key,alias=alias,
            screen_pass=summary['models'][key]['screen_pass'],
            by_family={f:totals(summary['models'][key],f) for f in (*FAMILIES,'corridor','disconnected')},
            by_band={str(b):{f:totals(summary['models'][key],f,b) for f in FAMILIES} for b in range(2)}))
    aggregate={}
    for key,rs in cohorts.items():
        rs.sort(key=lambda x:x['replicate']);assert len(rs)==3
        combined={}
        for family in (*FAMILIES,'corridor','disconnected'):
            combined[family]={metric:sum(r['by_family'][family][metric] for r in rs) for metric in rs[0]['by_family'][family]}
            combined[family]['replicate_pairs']=[r['by_family'][family]['complete_pairs'] for r in rs]
        aggregate[key]=dict(replicates=rs,by_family=combined,screen_passes=sum(r['screen_pass'] for r in rs))
    gate={key:value['screen_passes'] for key,value in aggregate.items() if key.endswith('/branch')}
    # Normal rows are needed only for the predetermined six mechanism targets.
    normal={r['model']:r['rows'] for r in lines(OUT/'confirmation/normal.jsonl.gz') if r['model'] in packet['mechanism'].values()}
    interventions={}
    for entry in lines(OUT/'confirmation/interventions.jsonl.gz'):
        key,mode=entry['model'],entry['mode'];base=normal[key];changed=entry['rows']
        bp=pairs(base,metadata);cp=pairs(changed,metadata)
        old={r['case']:r for r in base};values={}
        for family in FAMILIES:
            for band in range(2):
                b={v for v in bp if v[:2]==(family,band)};c={v for v in cp if v[:2]==(family,band)}
                subset=[r for r in changed if (metadata[r['case']]['family'],metadata[r['case']]['band'])==(family,band)]
                values[f'{family}/band{band}']=dict(normal_pairs=len(b),intervention_pairs=len(c),
                    retained_pairs=len(b&c),lost_pairs=len(b-c),gained_pairs=len(c-b),
                    same_mask=sum(r['mask']==old[r['case']]['mask'] for r in subset),
                    same_reaction=sum(reaction_fields(r)==reaction_fields(old[r['case']]) for r in subset),
                    inputs=len(subset))
        interventions[entry['target']+'/'+mode]=values
    traces=read_compressed(OUT/'trajectory_diagnostics.json.gz');trace_summaries={}
    for target in MECHANISM_ALIASES:
        for mode in ('normal','pulse_off','flag_off','pulse_flag_off'):
            part=[r for r in traces if r['target']==target and r['mode']==mode]
            trace_summaries[target+'/'+mode]=dict(pairs=len(part),
                source_changed=sum(r['first_source_difference'] is not None for r in part),
                junction_changed=sum(r['first_junction_difference'] is not None for r in part),
                output_away_changed=sum(r['first_output_away_difference'] is not None for r in part),
                strict_both_any_tick=sum(r['first_strict_both'] is not None for r in part),
                simultaneous_shortest_pairs=sum(bool(r['simultaneous_shortest_ticks']) for r in part),
                both_have_shortest_at_some_tick=sum(all(g['optimal']>0 for g in r['geometry']) for r in part),
                full_equal=sum(r['identical_full_trajectory'] for r in part),
                frames=sum(sum(r['lengths']) for r in part),
                valid_frames=sum(sum(g['valid'] for g in r['geometry']) for r in part),
                shortest_frames=sum(sum(g['optimal'] for g in r['geometry']) for r in part),
                full_horizon_traces=sum(sum(n==64 for n in r['lengths']) for r in part))
    carried=summary['models'][packet['mechanism']['carried']];rng=np.random.default_rng(1228);intervals={}
    for band in range(2):
        bases=[c['id'] for c in contexts if c['band']==band];draws=rng.integers(0,len(bases),(10000,len(bases)))
        arrays={f:np.array([carried['strata'][f'{f}/band{band}']['base_pair_counts'][b]/8 for b in bases]) for f in FAMILIES}
        for f,values in arrays.items():
            boot=values[draws].mean(axis=1)
            intervals[f'{f}/band{band}']=dict(rate=float(values.mean()),descriptive_ci95=np.quantile(boot,[.025,.975]).tolist(),contexts=len(bases))
        for f in ('two_junction','alternate_cycle'):
            diff=arrays[f]-arrays['fork'];boot=diff[draws].mean(axis=1)
            intervals[f'{f}-fork/band{band}']=dict(paired_rate_difference=float(diff.mean()),descriptive_ci95=np.quantile(boot,[.025,.975]).tolist(),contexts=len(bases))
    timing=json.loads((OUT/'confirmation/timing.json').read_text());timing_summary={}
    for family in FAMILIES:
        ratios=[r['ratio'] for r in timing if metadata[r['case']]['family']==family]
        if ratios:timing_summary[family]=dict(cases=len(ratios),median_ratio=statistics.median(ratios),min_ratio=min(ratios),max_ratio=max(ratios))
    # Matched context-level transitions, without fitting or choosing a new model.
    matched={}
    for name,key in packet['mechanism'].items():
        p=pairs(normal[key],metadata);g={f:{x[1:] for x in p if x[0]==f} for f in FAMILIES}
        matched[name]={f:dict(fork_pairs=len(g['fork']),harder_pairs=len(g[f]),
            retained=len(g['fork']&g[f]),lost=len(g['fork']-g[f]),gained=len(g[f]-g['fork']))
            for f in ('two_junction','alternate_cycle')}
    result=dict(cohorts=aggregate,gate=dict(passes=gate,met=any(v>=2 for v in gate.values())),
        mechanisms=interventions,traces=trace_summaries,carried_intervals=intervals,
        timing=timing_summary,matched=matched)
    write_json(OUT/'analysis.json',result)
    print(json.dumps(dict(cohorts={k:{f:(r['complete_pairs'],r['optimal'],r['no_path']) for f,r in v['by_family'].items()} for k,v in aggregate.items()},gate=result['gate'],matched=matched,timing=timing_summary),indent=2))


if __name__=='__main__':run()
