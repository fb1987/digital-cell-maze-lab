"""V12F prespecified aggregation; no candidate calls or genotype selection."""
from collections import Counter, defaultdict, deque
import gzip
import json
import time

import numpy as np
from .foundation_calibration import write_json
from .foundation_data import load_pairs
from .foundation_study_verify_core import Checker, grade
from .route_confirmation import OUT, lines, unpack_history, sha
from .route_confirmation_audit import adjacent


def unpack(row,n):
    return np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:n]


def strict_choice(mask,o,side):
    label=o._foundation_label;allowed=set(label['allowed'][side])
    if sum(bool(mask[p]) for p in allowed)!=1 or any(mask[p] for p in set(label['exits'])-allowed):
        return False
    m=o.maze;blocked=set(label['exits'])
    if not mask[m.start] or m.start in blocked:return False
    ds={m.start:0};queue=deque([m.start])
    while queue:
        p=queue.popleft()
        if p==label['vertex']:return ds[p]==label['distance']
        for q in adjacent(p,m.w,len(m.cells)):
            if q not in blocked and mask[q] and q not in ds:
                ds[q]=ds[p]+1;queue.append(q)
    return False


def scope_statistics(rows,groups,cases):
    singles=[r for r in rows.values()]
    by_case={r['case']:r for r in singles}
    base=[]
    for g in groups:
        selected=[p for p in g.pairs if p.first.maze.case_id in by_case]
        if not selected:continue
        successes=[]
        for pose,p in enumerate(selected):
            if all(by_case[o.maze.case_id]['optimal'] for o in p.cases):successes.append(pose)
        base.append(dict(group=g.identity,band=g.level,family=g.key[3],placement=g.key[4],
            misleading=g.key[5],complete_poses=successes))
    reachable=[r for r in singles if r['reachable']]
    return dict(inputs=len(singles),reachable=len(reachable),unreachable=len(singles)-len(reachable),
        valid=sum(r['valid'] for r in singles),optimal=sum(r['optimal'] for r in singles),
        no_path=sum(r['no_path'] for r in singles),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in singles),
        complete_pairs=sum(len(b['complete_poses']) for b in base),
        successful_bases=sum(bool(b['complete_poses']) for b in base),
        all_pose_bases=sum(len(b['complete_poses'])==8 for b in base),
        status=dict(Counter(r['status'] for r in singles)),failure=dict(Counter(r['failure'] for r in singles)),
        work=sum(max(0,r['dispatches']+r['reads']) for r in singles),
        max_array_bytes=max(r['array_bytes'] for r in singles),bases=base)


def analyze():
    started=time.perf_counter();target=OUT/'confirmation'
    proof=json.loads((OUT/'verification.json').read_text());assert proof['all_checks_passed']
    for path,digest in proof['artifact_sha256'].items():
        from .foundation_calibration import ROOT
        assert sha(ROOT/path)==digest
    cases,groups=load_pairs(target)
    rows=list(lines(target/'normal.jsonl.gz'))
    buckets=defaultdict(dict)
    for r in rows:buckets[r['model']+'/'+r['variant']][r['case']]=r
    summaries={k:scope_statistics(v,groups,cases) for k,v in buckets.items()}
    strata={}
    for key,values in buckets.items():
        strata[key]={}
        for family in ('tree','cyclic'):
            for band in range(3):
                gs=[g for g in groups if g.level==band and g.key[3]==family]
                ids={o.maze.case_id for g in gs for p in g.pairs for o in p.cases}
                strata[key][f'{family}/{band}']=scope_statistics({k:r for k,r in values.items() if k in ids},gs,cases)
    screen={}
    for family in ('tree','cyclic'):
        eligible=[b for b in summaries['target/normal']['bases'] if b['family']==family and b['band']>=1 and b['complete_poses']]
        criteria=dict(three_independent_bases=len(eligible)>=3,
            all_eight_poses=any(len(b['complete_poses'])==8 for b in eligible),
            interior=any(b['placement']=='interior' for b in eligible),
            misleading=any(b['misleading'] for b in eligible),
            longest_band=any(b['band']==2 for b in eligible))
        screen[family]=dict(successful_bases=len(eligible),criteria=criteria,passes=all(criteria.values()))
    pair_lookup={p.first.maze.case_id:(g,pose,p) for g in groups for pose,p in enumerate(g.pairs)}
    checker=Checker(cases)
    for r in buckets['target/normal'].values():checker.row(r)
    probe_summary=defaultdict(Counter);diagnostics=[];pending=None
    with gzip.open(OUT/'pair_trajectory_metrics.jsonl.gz','wt') as log:
        for rec in lines(target/'trajectories.jsonl.gz'):
            if pending is None:
                pending=rec;continue
            a_rec,b_rec=pending,rec;pending=None
            assert a_rec['variant']==b_rec['variant']
            g,pose,pair=pair_lookup[a_rec['reaction']['case']]
            assert b_rec['reaction']['case']==pair.second.maze.case_id
            a,b=pair.cases;m=a.maze;label=a._foundation_label;variant=rec['variant']
            h1,h2=unpack_history(a_rec['history']),unpack_history(b_rec['history'])
            nsteps=min(len(h1),len(h2))
            if variant=='both_off':assert np.array_equal(h1,h2)
            before=min(buckets['target/'+variant][o.maze.case_id]['steps'] for o in pair.cases)
            strict=[];geom=[];source=[];junction=[];outdiff=[];pre=[]
            choices=[[],[]];geometries=[[],[]]
            for side,(o,h) in enumerate(((a,h1),(b,h2))):
                for state in h:
                    mask=(state[2]>0).astype(np.uint8)
                    choices[side].append(strict_choice(mask,o,side))
                    geometries[side].append(bool(grade(*checker.prepared[o.maze.case_id],mask,0)[1]))
            for tick in range(nsteps):
                if choices[0][tick] and choices[1][tick]:
                    strict.append(tick+1)
                    if tick+1<before:pre.append(tick+1)
                if geometries[0][tick] and geometries[1][tick]:geom.append(tick+1)
                if np.any(h1[tick,:,m.start]!=h2[tick,:,m.start]):source.append(tick+1)
                if np.any(h1[tick,:,label['vertex']]!=h2[tick,:,label['vertex']]):junction.append(tick+1)
                difference=(h1[tick,2]>0)!=(h2[tick,2]>0)
                difference[[a.maze.goal,b.maze.goal]]=False
                if np.any(difference):outdiff.append(tick+1)
            entry=dict(variant=variant,group=g.identity,band=g.level,family=g.key[3],placement=g.key[4],
                misleading=g.key[5],pose=pose,cases=[o.maze.case_id for o in pair.cases],
                normal_stops=[buckets['target/'+variant][o.maze.case_id]['steps'] for o in pair.cases],
                normal_complete_pair=all(buckets['target/'+variant][o.maze.case_id]['optimal'] for o in pair.cases),
                paired_strict_ticks=strict,paired_strict_pre_stop_ticks=pre,paired_geometry_shortest_ticks=geom,
                source_state_difference_ticks=source,junction_state_difference_ticks=junction,
                output_difference_excluding_goals_ticks=outdiff,
                geometry_shortest_ticks=[[i+1 for i,v in enumerate(vs) if v] for vs in geometries])
            diagnostics.append(entry);log.write(json.dumps(entry,separators=(',',':'))+'\n')
            for scope in (variant,f'{variant}/{g.key[3]}/{g.level}'):
                count=probe_summary[scope];count['pairs']+=1
                for name,values in (('strict_any',strict),('strict_pre_stop',pre),('geometry_both_any',geom),
                    ('source_response',source),('junction_response',junction),('output_response_excluding_goals',outdiff)):
                    count[name]+=bool(values)
                    for tick in (8,16,32,64,96):count[f'{name}_t{tick}']+=tick in values
    assert pending is None and len(diagnostics)==1536
    success_rows=[]
    for cid,r in buckets['target/normal'].items():
        if r['optimal']:
            o=cases[cid]
            success_rows.append(dict(case=cid,edges=len(o.path)-1,family=o.maze.family,steps=r['steps'],
                retained={v:buckets['target/'+v][cid]['optimal'] for v in ('pulse_off','flag_off','both_off','source_only')}))
    timings=json.loads((target/'timings.json').read_text())['rows']
    timing_summary=[]
    for r in timings:
        stats={k:dict(median=float(np.median(v)),min=min(v),max=max(v)) for k,v in r['samples'].items()}
        timing_summary.append(dict(case=r['case'],edges=r['edges'],seconds=stats,
            target_to_bfs=stats['target']['median']/stats['bfs']['median']))
    result=dict(scope='Frozen single-lineage independent confirmation, no evolution.',
        summaries=summaries,strata=strata,screen=screen,screen_pass=all(v['passes'] for v in screen.values()),
        probes={k:dict(v) for k,v in probe_summary.items()},target_successes=success_rows,
        timing=timing_summary,analysis_seconds=time.perf_counter()-started,
        source_sha256=sha(__file__),verification_sha256=sha(OUT/'verification.json'))
    write_json(OUT/'analysis.json',result)
    print(json.dumps(dict(primary={k:{f:v[f] for f in ('valid','optimal','complete_pairs','successful_bases','all_pose_bases','no_path')} for k,v in summaries.items()},screen=screen,probes={k:v for k,v in result['probes'].items() if '/' not in k}),indent=2))


if __name__=='__main__':analyze()
