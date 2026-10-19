"""V12H independent graph/raster arithmetic and complete deterministic replays."""
from collections import Counter, defaultdict
import json
import resource
import statistics
import time

import numpy as np
from .baselines import baseline
from .beacon_probe import _probe_kernel
from .beacon_runtime import TOPOLOGIES
from .evaluator import assess
from .foundation_calibration import ROOT, LIMITS, controls, write_json
from .foundation_data import layout_hash
from .foundation_study import read_compressed
from .foundation_study_verify_core import Checker, grade
from .route_confirmation_audit import adjacent, graph_distances
from .runtime import Reaction, STATUSES
from .routing_transfer_data import OUT, FIXTURES, N, BANDS, FAMILIES, load, exclusions, TransferData
from .routing_transfer import (check_freeze, lines, organism, inference, record, canonical,
    summarize, unpack_history, MODES, TRACE_MODES, MECHANISM_ALIASES, HORIZON)
from .route_confirmation_runtime import respond


REACTION_FIELDS = ('status','steps','mask','reads','dispatches','range_reads','active','array_bytes')


def reaction_fields(row):
    return {k:row[k] for k in REACTION_FIELDS}


def synthetic(o,path):
    mask=np.zeros(len(o.maze.cells),np.uint8);mask[path]=1
    return Reaction(mask,'emitted',1,0,0,mask.nbytes)


def audit_geometry(cases,contexts,metadata):
    counts=Counter();seen=set();layouts=set()
    for context in contexts:
        assert len(context['poses'])==8
        first=context['poses'][0]
        for pose in context['poses']:
            s=pose['symmetry'];meta=pose['meta'];noise=set(meta['clutter'])
            assert len(noise)==8 and 2<=meta['gap']<=12
            fork=set(meta['paths'][0])|set(meta['paths'][1])
            expected=dict(fork=fork,two_junction=fork|set(meta['stub']),
                alternate_cycle=fork|set(meta['detour']),corridor_0=set(meta['paths'][0]),
                corridor_1=set(meta['paths'][1]),disconnected=(fork|set(meta['detour']))-{meta['decision']['vertex']})
            for family,ids in pose['cases'].items():
                if family in FAMILIES or family=='disconnected':
                    assert len(ids)==2
                    a,b=[cases[cid].maze for cid in ids]
                    assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
                else:assert len(ids)==1
                layout=layout_hash(cases[ids[0]].maze)
                assert layout not in layouts;layouts.add(layout)
                for cid in ids:
                    assert cid not in seen;seen.add(cid);o=cases[cid];m=o.maze
                    descriptor=metadata[cid];side=descriptor['side']
                    assert descriptor==dict(base=context['id'],index=context['index'],band=context['band'],
                        family='corridor' if family.startswith('corridor_') else family,side=side,symmetry=s)
                    assert (m.w,m.h,m.start,m.goal)==(N,N,meta['start'],meta['goals'][side])
                    assert set(np.flatnonzero(np.frombuffer(m.cells,np.uint8)))==expected[family]|noise
                    # Independent array transformation, rather than the generator's point routine.
                    original=cases[first['cases'][family][0 if family.startswith('corridor_') else side]].maze
                    grid=np.frombuffer(original.cells,np.uint8).reshape(N,N)
                    labels=np.arange(N*N).reshape(N,N)
                    if s>=4:grid=np.fliplr(grid);labels=np.fliplr(labels)
                    grid=np.rot90(grid,-(s%4));labels=np.rot90(labels,-(s%4))
                    assert grid.tobytes()==m.cells
                    assert np.flatnonzero(labels.ravel()==original.start)[0]==m.start
                    assert np.flatnonzero(labels.ravel()==original.goal)[0]==m.goal
                    ds=graph_distances(m.cells,N,m.start);dg=graph_distances(m.cells,N,m.goal)
                    assert ds==o._from_start and dg==o.to_goal
                    for p in noise:
                        assert ds[p]<0 and not any(m.cells[q] for q in adjacent(p,N,N*N))
                    if family=='disconnected':
                        assert ds[m.goal]<0 and not o.path;counts['no_path_cases']+=1
                        continue
                    lo,hi=BANDS[context['band']]
                    assert lo<=ds[m.goal]==len(o.path)-1<=hi
                    assert o.path==meta['paths'][side]
                    path=o.path
                    assert path[0]==m.start and path[-1]==m.goal and len(set(path))==len(path)
                    assert all(q in list(adjacent(p,N,N*N)) for p,q in zip(path,path[1:]))
                    selected=set(path)
                    assert all(sum(q in selected for q in adjacent(p,N,N*N))==(1 if p in (m.start,m.goal) else 2) for p in selected)
                    assert assess(synthetic(o,path),o).optimal;counts['shortest_masks']+=1
                    # Count all shortest paths by an independently computed DAG.
                    ways=[0]*(N*N);ways[m.start]=1
                    for p in sorted((p for p,d in enumerate(ds) if d>=0),key=ds.__getitem__):
                        for q in adjacent(p,N,N*N):
                            if ds[q]==ds[p]+1:ways[q]+=ways[p]
                    assert ways[m.goal]==1
                    component={p for p,d in enumerate(ds) if d>=0}
                    degree={p:sum(q in component for q in adjacent(p,N,N*N)) for p in component}
                    rank=sum(degree.values())//2-len(component)+1
                    if family in FAMILIES:
                        assert rank==int(family=='alternate_cycle')
                        assert sum(d==3 for d in degree.values())==dict(fork=1,two_junction=2,alternate_cycle=3)[family]
                        assert max(degree.values())==3
                        label=meta['decision'];v=label['vertex']
                        assert o._foundation_label==label and label['prefix']==path[:label['distance']+1]
                        assert ds[v]==label['distance'] and path[label['distance']]==v
                        exits={q for q in adjacent(v,N,N*N) if m.cells[q] and q!=label['incoming']}
                        assert exits==set(label['exits'])
                        allowed={q for q in exits if dg[q]+1==dg[v]}
                        assert allowed==set(label['allowed'][side]) and allowed
                        assert not set(label['allowed'][0])&set(label['allowed'][1])
                        counts['decision_labels']+=1
                    else:assert rank==0 and max(degree.values())==2
                    if family=='alternate_cycle':
                        alt=meta['alternatives'][side];ar=assess(synthetic(o,alt),o)
                        assert ar.valid_path and not ar.optimal and len(alt)-len(path)==meta['gap']
                        assert set(alt)-set(path) and set(path)-set(alt)
                        counts['legal_longer_masks']+=1
                    counts['reachable_cases']+=1
    assert seen==set(cases)==set(metadata)
    return dict(counts,contexts=len(contexts),whole_layouts=len(layouts),cases=len(cases))


def trace_pair(a,b,oa,ob,checker):
    n=min(len(a),len(b));m=oa.maze;label=oa._foundation_label
    source=np.any(a[:n,:,m.start]!=b[:n,:,m.start],axis=1)
    junction=np.any(a[:n,:,label['vertex']]!=b[:n,:,label['vertex']],axis=1)
    maska=a[:n,2]>0;maskb=b[:n,2]>0
    away=np.ones(len(m.cells),bool);away[[m.goal,ob.maze.goal]]=False
    output=np.any(maska[:,away]!=maskb[:,away],axis=1)
    first=lambda values:next((i+1 for i,v in enumerate(values) if v),None)
    geometries=[];choices=[]
    for history,o in ((a,oa),(b,ob)):
        valid=[];optimal=[];strict=[]
        side=0 if o is oa else 1;allowed=set(label['allowed'][side]);wrong=set(label['exits'])-allowed
        for state in history:
            mask=(state[2]>0).astype(np.uint8)
            g=grade(*checker.prepared[o.maze.case_id],mask,0)
            valid.append(bool(g[0]));optimal.append(bool(g[1]))
            strict.append(bool(g[6][label['vertex']]) and sum(mask[p]>0 for p in allowed)==1 and all(not mask[p] for p in wrong))
        geometries.append(dict(frames=len(history),valid=sum(valid),optimal=sum(optimal),
            first_valid=first(valid),first_optimal=first(optimal),optimal_ticks=[i+1 for i,v in enumerate(optimal) if v]))
        choices.append(strict)
    return dict(shared_ticks=n,lengths=[len(a),len(b)],first_source_difference=first(source),
        first_junction_difference=first(junction),first_output_away_difference=first(output),
        identical_full_trajectory=bool(np.array_equal(a,b)),geometry=geometries,
        strict_both_ticks=sum(x and y for x,y in zip(*choices)),
        first_strict_both=first([x and y for x,y in zip(*choices)]),
        simultaneous_shortest_ticks=sorted(set(geometries[0]['optimal_ticks'])&set(geometries[1]['optimal_ticks'])))


def audit():
    started=time.perf_counter();frozen=check_freeze();out=OUT/'confirmation'
    if (OUT/'verification.json').exists():raise FileExistsError('Audit already completed')
    packet=read_compressed(OUT/'models.json.gz');models=packet['models'];summary=json.loads((out/'summary.json').read_text())
    cases,contexts,metadata=load(out);fcases,fcontexts,fmeta=load(FIXTURES)
    geometry=dict(final=audit_geometry(cases,contexts,metadata),fixtures=audit_geometry(fcases,fcontexts,fmeta))
    old=TransferData(0,exclusions()).layouts;fixture_layouts={layout_hash(o.maze) for o in fcases.values()}
    new={layout_hash(o.maze) for o in cases.values()}
    assert len(old)==136536 and len(fixture_layouts)==192 and len(new)==1984
    assert not old&fixture_layouts and not (old|fixture_layouts)&new
    assert read_compressed(OUT/'excluded_layouts.json.gz')==sorted(old|fixture_layouts)
    ledger=json.loads((out/'layout_ledger.json').read_text())
    assert ledger['new_hashes']==sorted(new) and ledger['future_exclusion_count']==len(old|fixture_layouts|new)==138712
    # All 60 aliases are the unchanged G primary/frozen selections, with topology.
    source=read_compressed(ROOT/'results/fork_pressure/frozen_selections.json.gz')
    for alias,key in packet['aliases'].items():
        condition,phase=alias.rsplit('/',1);s=source[condition]
        assert models[key]['topology']==s['config']['topology']
        assert models[key]['item']['genome']==s[phase]['pair']['item']['genome']
    checker=Checker(cases);fchecker=Checker(fcases);counts=Counter();audit_work=0;charged_work=0;charged_calls=0
    # Recheck saved calibration controls and BFS, including every mask.
    for entry in lines(FIXTURES/'controls.jsonl.gz'):
        name=entry['model'];org=organism(dict(item=controls()[name].save(),topology='evolved')) if name!='compiled_bfs' else None
        for row in entry['rows']:
            cid=row['case'];o=fcases[cid];m=o.maze;fchecker.row(row,fmeta[cid]['side'])
            r=inference(org,m) if org else baseline(name,m.cells,m.w,m.h,m.start,m.goal)
            assert canonical(record(r,o,fmeta[cid]))==row
            if org:audit_work+=r.spatial_reads+r.instructions;counts['calibration_candidate_replays']+=1
            else:counts['calibration_baseline_replays']+=1
    for entry in lines(out/'parity.jsonl.gz'):
        row=entry['row'];o=fcases[row['case']];m=o.maze;org=organism(models[entry['model']])
        fchecker.row(row,fmeta[row['case']]['side']);native=inference(org,m)
        adapter=respond(org,m.cells,m.w,m.h,m.start,m.goal).reaction
        assert canonical(record(native,o,fmeta[row['case']]))==row
        assert canonical(record(adapter,o,fmeta[row['case']]))==row
        audit_work+=2*(native.instructions+native.spatial_reads);charged_work+=2*(native.instructions+native.spatial_reads)
        charged_calls+=2;counts['native_adapter_checks']+=1
    normal={};expected_timing=[]
    for entry in lines(out/'normal.jsonl.gz'):
        key=entry['model'];org=organism(models[key]);seen=set();timed=Counter()
        for row in entry['rows']:
            cid=row['case'];assert cid not in seen;seen.add(cid)
            o=cases[cid];checker.row(row,metadata[cid]['side']);r=inference(org,o.maze)
            assert canonical(record(r,o,metadata[cid]))==row
            audit_work+=r.instructions+r.spatial_reads;charged_work+=r.instructions+r.spatial_reads;charged_calls+=1
            meta=metadata[cid];stratum=(meta['family'],meta['band'])
            if '/' in key and row['optimal'] and meta['family'] in FAMILIES and timed[stratum]<4:
                expected_timing.append((key,cid));timed[stratum]+=1
            if key in packet['mechanism'].values():normal[key,cid]=row
            counts['normal_candidate_replays']+=1
        assert seen==set(cases)
        assert summarize(entry['rows'],metadata)==summary['models'][key]
        print(json.dumps(dict(audit='normal',model=key,elapsed=round(time.perf_counter()-started,1))),flush=True)
    for entry in lines(out/'baselines.jsonl.gz'):
        seen=set();name=entry['model']
        for row in entry['rows']:
            cid=row['case'];assert cid not in seen;seen.add(cid);o=cases[cid];m=o.maze
            checker.row(row,metadata[cid]['side']);r=baseline(name,m.cells,m.w,m.h,m.start,m.goal)
            assert canonical(record(r,o,metadata[cid]))==row and (row['optimal'] or row['no_path'])
            counts['final_baseline_replays']+=1
        assert seen==set(cases) and summarize(entry['rows'],metadata)==summary['baselines'][name]
    intervention_rows={}
    for entry in lines(out/'interventions.jsonl.gz'):
        key,mode=entry['model'],entry['mode'];org=organism(models[key],mode);seen=set();blind={}
        assert packet['mechanism'][entry['target']]==key
        for row in entry['rows']:
            cid=row['case'];assert cid not in seen;seen.add(cid);o=cases[cid];m=metadata[cid]
            checker.row(row,m['side']);r=inference(org,o.maze,mode)
            assert canonical(record(r,o,m))==row
            audit_work+=r.instructions+r.spatial_reads;charged_work+=r.instructions+r.spatial_reads;charged_calls+=1
            if mode=='all_goal_off':
                pair=(m['base'],m['family'],m['symmetry'])
                if pair in blind:assert reaction_fields(row)==blind[pair];counts['goal_blind_pair_checks']+=1
                else:blind[pair]=reaction_fields(row)
            if m['index']==0 and entry['target'] in MECHANISM_ALIASES:
                intervention_rows[key,mode,cid]=row
            counts['intervention_replays']+=1
        assert seen=={cid for cid,m in metadata.items() if m['family'] in FAMILIES}
        assert summarize(entry['rows'],metadata)==summary['interventions'][entry['target']+'/'+mode]
    pending={};trace_records=[];raw_trace_bytes=0;frames=0;seen_traces=set()
    for entry in lines(out/'trajectories.jsonl.gz'):
        key,mode,row=entry['model'],entry['mode'],entry['row'];cid=row['case'];m=cases[cid].maze;meta=metadata[cid]
        assert (key,mode,cid) not in seen_traces;seen_traces.add((key,mode,cid))
        assert not entry['normally_emitted'] and entry['target'] in MECHANISM_ALIASES
        assert key==packet['mechanism'][entry['target']] and mode in TRACE_MODES and meta['index']==0
        org=organism(models[key],mode);history=unpack_history(entry['history'])
        replay=inference(org,m,mode,True)
        assert np.array_equal(replay.history,history)
        assert canonical(record(replay.reaction,cases[cid],meta))==row
        checker.row(row,meta['side']);counts['trace_replays']+=1
        audit_work+=replay.reaction.instructions+replay.reaction.spatial_reads
        charged_work+=replay.reaction.instructions+replay.reaction.spatial_reads;charged_calls+=1
        assert history.shape==(row['steps'],8,N*N) and 1<=row['steps']<=HORIZON
        raw_trace_bytes+=history.nbytes;frames+=len(history)
        counts['full_horizon_traces']+=len(history)==HORIZON
        normal_row=(normal[key,cid] if mode=='normal' else intervention_rows[key,mode,cid])
        if 1<=normal_row['steps']<=len(history):
            mask=np.packbits(history[normal_row['steps']-1,2]>0,bitorder='little').tobytes().hex()
            assert mask==normal_row['mask'];counts['normal_trace_matches']+=1
        if MODES[mode][1]:
            state,steps,reads,dispatches,active,status,memory,ranges=_probe_kernel(
                np.frombuffer(m.cells,np.uint8),N,m.start,m.goal,org.program,TOPOLOGIES[org.topology],False,
                HORIZON,len(m.cells)*LIMITS.reads_per_site,len(m.cells)*LIMITS.instructions_per_site,
                True,True,org.goal_pulse)
            assert np.array_equal(state,history[-1])
            assert (steps,reads,dispatches,active,STATUSES[status],memory,tuple(ranges))==(
                row['steps'],row['reads'],row['dispatches'],row['active'],row['status'],row['array_bytes'],tuple(row['range_reads']))
            counts['independent_observer_checks']+=1;audit_work+=reads+dispatches
        pairkey=(entry['target'],mode,meta['base'],meta['family'],meta['symmetry'])
        if meta['side']==0:pending[pairkey]=(history,cases[cid])
        else:
            a,oa=pending.pop(pairkey);comparison=trace_pair(a,history,oa,cases[cid],checker)
            if mode=='pulse_flag_off':assert comparison['identical_full_trajectory']
            trace_records.append(dict(target=entry['target'],model=key,mode=mode,base=meta['base'],
                family=meta['family'],band=meta['band'],symmetry=meta['symmetry'],**comparison))
    assert not pending and len(seen_traces)==1536 and len(trace_records)==768
    assert frames==summary['trace_frames'] and raw_trace_bytes==summary['raw_trace_bytes']
    timings=json.loads((out/'timing.json').read_text())
    assert [(r['model'],r['case']) for r in timings]==expected_timing
    for row in timings:
        o=cases[row['case']];m=o.maze;org=organism(models[row['model']]);r=inference(org,m)
        b=baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal)
        assert assess(r,o).optimal and assess(b,o).optimal
        charged_work+=53*(r.instructions+r.spatial_reads);charged_calls+=53
        audit_work+=r.instructions+r.spatial_reads;counts['timing_candidate_replays']+=1;counts['timing_baseline_replays']+=1
        assert row['baseline_calls']==53
        for measure in row['measurements'].values():
            values=measure['ns'];assert len(values)==5 and min(values)>0
            assert measure['median_ns']==statistics.median(values) and measure['min_ns']==min(values) and measure['max_ns']==max(values)
        assert row['ratio']==row['measurements']['candidate']['median_ns']/row['measurements']['bfs']['median_ns']
    execution=json.loads((out/'execution.json').read_text());assert execution['completed'] and execution['candidate']['seconds']<600
    assert execution['candidate']['calls']==charged_calls and execution['candidate']['work']==charged_work
    assert counts['normal_candidate_replays']==112000 and counts['intervention_replays']==82944
    assert counts['native_adapter_checks']==420 and counts['final_baseline_replays']==9600
    assert charged_calls==197320+53*len(timings)
    from .foundation_study import compressed_json
    compressed_json(OUT/'trajectory_diagnostics.json.gz',trace_records)
    result=dict(passed=True,source_hashes=len(frozen['source_sha256']),input_hashes=len(frozen['input_sha256']),
        geometry=geometry,counts=dict(counts),graded_rasters=checker.rasters+fchecker.rasters,
        geometry_frames=frames,raw_trace_bytes=raw_trace_bytes,candidate_charged_calls=charged_calls,
        candidate_charged_work=charged_work,audit_replay_work=audit_work,
        future_exclusion_count=len(old|fixture_layouts|new),wall_seconds=time.perf_counter()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(OUT/'verification.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':audit()
