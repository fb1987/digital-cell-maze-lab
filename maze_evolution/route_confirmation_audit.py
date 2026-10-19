"""V12F independent graph/label/raster checks and complete saved-output replays."""
import argparse
from collections import deque
from dataclasses import replace
from heapq import heappop, heappush
import hashlib
import json
import time
import resource

import numpy as np
from .baselines import baseline
from .beacon_probe import _probe_kernel
from .beacon_runtime import TOPOLOGIES
from .foundation_calibration import ROOT, write_json
from .foundation_data import load_pairs, layout_hash, transform_maze, transform_point
from .foundation_pair_confirm import normal_row
from .foundation_study_verify_core import Checker, grade
from .growth import Individual, replay_mutation
from .growth_runtime import Organism
from .route_confirmation import OUT, FIXTURES, LIMITS, VARIANTS, HORIZON, check_freeze, lines, sha, unpack_history
from .route_confirmation_data import exclusions, BANDS
from .route_confirmation_runtime import respond
from .runtime import STATUSES
from .evaluator import Maze


def adjacent(p,w,n):
    if p%w:yield p-1
    if p%w+1<w:yield p+1
    if p>=w:yield p-w
    if p+w<n:yield p+w


def graph_distances(cells,w,source):
    ds=[-1]*len(cells)
    if not cells[source]:return ds
    ds[source]=0;queue=deque([source])
    while queue:
        p=queue.popleft()
        for q in adjacent(p,w,len(cells)):
            if cells[q] and ds[q]<0:
                ds[q]=ds[p]+1;queue.append(q)
    return ds


def shortest_turns(m):
    """Independent lexicographic Dijkstra on (cell, incoming direction)."""
    best={(m.start,4):(0,0)};queue=[(0,0,m.start,4)]
    result={}
    while queue:
        distance,turns,p,direction=heappop(queue)
        if best[p,direction]!=(distance,turns):continue
        result[p]=min(result.get(p,(10**9,10**9)),(distance,turns))
        for q in adjacent(p,m.w,len(m.cells)):
            if not m.cells[q]:continue
            step=q-p
            nd=(-1,1,-m.w,m.w).index(step)
            value=(distance+1,turns+int(direction!=4 and direction!=nd))
            if value<best.get((q,nd),(10**9,10**9)):
                best[q,nd]=value;heappush(queue,(*value,q,nd))
    return result


def audit_groups(groups):
    checked=0
    for g in groups:
        assert len(g.pairs)==8
        base=g.pairs[0]
        independent_turns=shortest_turns(base.first.maze)
        for symmetry,pair in enumerate(g.pairs):
            a,b=pair.cases;m=a.maze
            assert m.cells==b.maze.cells and m.start==b.maze.start and m.goal!=b.maze.goal
            for o,original in zip(pair.cases,base.cases):
                expected=transform_maze(original.maze,symmetry)
                assert (o.maze.cells,o.maze.start,o.maze.goal)==(expected.cells,expected.start,expected.goal)
                ds=graph_distances(o.maze.cells,o.maze.w,o.maze.start)
                dg=graph_distances(o.maze.cells,o.maze.w,o.maze.goal)
                assert ds==o._from_start and dg==o.to_goal
                assert (ds[o.maze.goal]+1 if ds[o.maze.goal]>=0 else 0)==len(o.path)
            if g.level<0:
                assert not a.path and not b.path
                checked+=1;continue
            low,high,required,n=BANDS[g.level]
            label=a._foundation_label
            original=base.first._foundation_label
            conv=lambda p:transform_point(p,n,symmetry)
            assert label==dict(vertex=conv(original['vertex']),prefix=[conv(p) for p in original['prefix']],
                incoming=conv(original['incoming']),exits=[conv(p) for p in original['exits']],
                allowed=[[conv(p) for p in xs] for xs in original['allowed']],distance=original['distance'],
                misleading=original['misleading'],min_turns=original['min_turns'],cycle_rank=original['cycle_rank'])
            prefix=label['prefix'];v=label['vertex'];incoming=label['incoming']
            assert prefix[0]==m.start and prefix[-1]==v and prefix[-2]==incoming
            assert 1<=len(prefix)-1==label['distance']<=6
            assert all(q in list(adjacent(p,m.w,len(m.cells))) and m.cells[q] for p,q in zip(prefix,prefix[1:]))
            assert a._from_start[v]==len(prefix)-1
            exits={q for q in adjacent(v,m.w,len(m.cells)) if m.cells[q] and q!=incoming}
            assert set(label['exits'])==exits
            assert not set(label['allowed'][0])&set(label['allowed'][1])
            component=[p for p,d in enumerate(a._from_start) if d>=0]
            rank=sum(sum(a._from_start[q]>=0 for q in adjacent(p,n,n*n)) for p in component)//2-len(component)+1
            assert rank==label['cycle_rank'] and ((rank==0) if m.family=='tree' else rank>0)
            for side,o in enumerate(pair.cases):
                assert low<=len(o.path)-1<=high
                assert label['distance']+o.to_goal[v]==len(o.path)-1
                assert o.to_goal[v]>=2
                expected={q for q in exits if o.to_goal[q]+1==o.to_goal[v]}
                assert set(label['allowed'][side])==expected and expected
                # Minimum-turn value is invariant under the verified D4 transform.
                length,turns=independent_turns[base.cases[side].maze.goal]
                assert length==len(o.path)-1 and turns==label['min_turns'][side] and turns>=required
                md=lambda p:abs(p%n-o.maze.goal%n)+abs(p//n-o.maze.goal//n)
                assert label['misleading'][side]==all(md(q)>md(v) for q in expected)
                rim=lambda p:min(p%n,p//n,n-1-p%n,n-1-p//n)
                if g.key[4]=='interior':assert min(rim(m.start),rim(o.maze.goal))>=3
                else:assert rim(m.start)==1
            assert any(label['misleading'])==g.key[5]
            checked+=1
    return checked


def audit():
    started=time.perf_counter();frozen=check_freeze();target=OUT/'confirmation'
    if (OUT/'verification.json').exists():raise FileExistsError('Audit already complete')
    cases,groups=load_pairs(target);fixture_cases,fixture_groups=load_pairs(FIXTURES)
    labels=audit_groups(groups)+audit_groups(fixture_groups)
    previous=exclusions()
    excluded={layout_hash(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'])) for r in previous}
    assert len(excluded)==124392
    fixture_layouts={layout_hash(o.maze) for o in fixture_cases.values()}
    assert not excluded&fixture_layouts
    seen=excluded|fixture_layouts
    for g in groups:
        orbit={layout_hash(p.first.maze) for p in g.pairs}
        assert len(orbit)==8 and not orbit&seen
        seen.update(orbit)
    ledger=json.loads((target/'layout_ledger.json').read_text())
    assert ledger['future_exclusion_count']==len(seen)
    assert ledger['excluded_with_fixtures']==len(excluded|fixture_layouts)
    assert ledger['new_hashes']==sorted(seen-excluded-fixture_layouts)
    assert len(groups)==52 and len(cases)==832
    items={k:Individual.load(v) for k,v in json.loads((OUT/'models.json').read_text()).items()}
    lineage=json.loads((OUT/'lineage.json').read_text())
    assert replay_mutation(items['parent'].genome,lineage[items['target'].identity]['events'],256)==items['target'].genome
    models={k:Organism(v.genome,'local',LIMITS,goal_pulse=True) for k,v in items.items()}
    variants={k:Organism(items['target'].genome,'local',LIMITS,goal_pulse=p) for k,(p,_) in VARIANTS.items()}
    checker=Checker(cases);normal={};normal_replays=adapter_parity=0;work=0
    for row in lines(target/'normal.jsonl.gz'):
        key=row['model'],row['variant'],row['case'];assert key not in normal
        normal[key]=row;checker.row(row)
        o=cases[row['case']];m=o.maze
        if row['model']=='bfs':
            r=baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal)
            r.dispatches=-1;r.active_instructions=-1;r.range_reads=(-1,)*4
        elif row['variant']=='normal':
            organism=models[row['model']]
            r=organism.react(m.cells,m.w,m.h,m.start,m.goal)
            adapted=respond(organism,m.cells,m.w,m.h,m.start,m.goal).reaction
            assert normal_row(adapted,o)==normal_row(r,o)
            adapter_parity+=1;work+=adapted.dispatches+adapted.spatial_reads
        elif row['variant']=='source_only':
            r=respond(models['target'],m.cells,m.w,m.h,m.start,m.goal,halt_mode='source_only').reaction
        else:
            organism=variants[row['variant']];flag=VARIANTS[row['variant']][1]
            r=(organism.react(m.cells,m.w,m.h,m.start,m.goal) if flag else
               respond(organism,m.cells,m.w,m.h,m.start,m.goal,goal_flag=False).reaction)
        assert json.loads(json.dumps(dict(model=row['model'],variant=row['variant'],**normal_row(r,o))))==row
        work+=max(0,r.instructions+r.spatial_reads);normal_replays+=1
    assert len(normal)==8320
    trajectories=set();trace_replays=trace_rasters=observer_checks=emission_matches=0
    raw_bytes=0;max_instrumentation=0;geometry_counts={k:dict(valid=0,optimal=0) for k in VARIANTS}
    for record in lines(target/'trajectories.jsonl.gz'):
        row=record['reaction'];variant=record['variant'];key=variant,row['case']
        assert key not in trajectories;trajectories.add(key)
        assert not record['normally_emitted'] and not record['endpoint_halt'] and not record['quiescence_halt']
        o=cases[row['case']];m=o.maze;assert o.path
        history=unpack_history(record['history']);organism=variants[variant]
        flag=VARIANTS[variant][1]
        replay=respond(organism,m.cells,m.w,m.h,m.start,m.goal,goal_flag=flag,halt_mode='forced',trace=True,horizon=HORIZON)
        assert json.loads(json.dumps(normal_row(replay.reaction,o)))==row and np.array_equal(history,replay.history)
        assert 1<=len(history)<=HORIZON and history.shape[1:]==(8,len(m.cells))
        work+=replay.reaction.dispatches+replay.reaction.spatial_reads
        checker.row(row)
        # Independent original observer, including tick96 via its bounded kernel.
        if flag:
            state,steps,reads,dispatches,active,status,memory,ranges=_probe_kernel(
                np.frombuffer(m.cells,np.uint8),m.w,m.start,m.goal,organism.program,0,False,HORIZON,
                len(m.cells)*LIMITS.reads_per_site,len(m.cells)*LIMITS.instructions_per_site,True,True,organism.goal_pulse)
            assert np.array_equal(state,history[-1])
            assert (steps,reads,dispatches,active,STATUSES[status],memory,tuple(ranges))==(row['steps'],row['reads'],row['dispatches'],row['active'],row['status'],row['array_bytes'],tuple(row['range_reads']))
            observer_checks+=1;work+=dispatches+reads
        normal_row_saved=normal['target',variant,m.case_id]
        if normal_row_saved['steps']<=len(history):
            frame=history[normal_row_saved['steps']-1,2]>0
            assert np.packbits(frame,bitorder='little').tobytes().hex()==normal_row_saved['mask']
            emission_matches+=int(normal_row_saved['status']=='emitted')
        for state in history:
            mask=(state[2]>0).astype(np.uint8)
            # Grade as geometry only. Normal emission never follows from this status assumption.
            graded=grade(*checker.prepared[m.case_id],mask,0)
            geometry_counts[variant]['valid']+=int(graded[0]);geometry_counts[variant]['optimal']+=int(graded[1])
            trace_rasters+=1
        raw_bytes+=history.nbytes;max_instrumentation=max(max_instrumentation,history.nbytes)
        trace_replays+=1
    assert trace_replays==3072
    # Independent goal-blind trajectory equality is checked again by the analysis,
    # which retains corresponding per-pair source/junction and raster comparisons.
    execution=json.loads((target/'execution.json').read_text())
    assert execution['completed'] and execution['candidate']['seconds']<600
    counts=execution['candidate']['by_scope']
    assert sum(x['calls'] for x in counts.values())==execution['candidate']['calls']
    assert sum(x['work'] for x in counts.values())==execution['candidate']['work']
    timing=json.loads((target/'timings.json').read_text())['rows']
    assert execution['candidate']['calls']==7488+3072+62*len(timing)
    expected_work=sum(max(0,r['reads']+r['dispatches']) for r in normal.values())
    expected_work+=sum(r['reaction']['reads']+r['reaction']['dispatches'] for r in lines(target/'trajectories.jsonl.gz'))
    expected_work+=sum(31*(normal[k,'normal',t['case']]['reads']+normal[k,'normal',t['case']]['dispatches']) for t in timing for k in ('target','intact'))
    assert expected_work==execution['candidate']['work']
    artifact_hashes={str(p.relative_to(ROOT)):sha(p) for p in target.iterdir() if p.is_file()}
    result=dict(all_checks_passed=True,source_hashes=len(frozen['source_sha256']),input_hashes=len(frozen['input_sha256']),
        paired_labels=labels,normal_rasters=8320,normal_replays=normal_replays,adapter_native_parity=adapter_parity,
        forced_final_rasters=3072,trace_replays=trace_replays,trace_rasters=trace_rasters,
        original_observer_checks=observer_checks,normal_emission_tick_matches=emission_matches,
        trace_geometry_counts=geometry_counts,trace_raw_bytes=raw_bytes,max_trace_instrumentation_bytes=max_instrumentation,
        future_exclusion_count=len(seen),replay_work=work,elapsed_seconds=time.perf_counter()-started,
        max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,artifact_sha256=artifact_hashes,
        freeze_sha256=sha(OUT/'freeze.json'))
    write_json(OUT/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='artifact_sha256'},indent=2))


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    audit()
