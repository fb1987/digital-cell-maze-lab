"""Independent V12J topology/matching checks, raster grading and full replays."""
from collections import Counter, defaultdict
import json
import resource
import time
import numpy as np

from .baselines import baseline
from .beacon_probe import _probe_kernel
from .beacon_runtime import TOPOLOGIES
from .evaluator import assess
from .foundation_calibration import ROOT, LIMITS, write_json
from .foundation_data import FoundationData, layout_hash
from .foundation_pair_confirm import normal_row
from .foundation_study import read_compressed
from .foundation_study_verify_core import Checker, grade
from .route_confirmation import unpack_history
from .route_confirmation_audit import graph_distances, adjacent
from .route_confirmation_runtime import respond
from .routing_transfer import canonical, sha, lines, organism, inference, MODES
from .routing_transfer_audit import synthetic
from .runtime import STATUSES
from .junction_distance_data import OUT, FIXTURES, N, PREFIXES, BRANCHES, FAMILIES, exclusions, load


def geometry(cases,contexts,metadata):
    counts=Counter();seen=set();layouts=set();downstream={};short_shapes={}
    for context in contexts:
        assert len(context['variants'])==80
        for v in context['variants']:
            for family,ids in v['cases'].items():
                assert len(ids)==(1 if family.startswith('corridor') else 2)
                if len(ids)==2:
                    a,b=[cases[c].maze for c in ids]
                    assert (a.cells,a.start)==(b.cells,b.start) and a.goal!=b.goal
                for cid in ids:
                    assert cid not in seen;seen.add(cid)
                    o=cases[cid];m=o.maze;md=metadata[cid];path=md['path'];p=md['prefix'];j=md['junction']
                    assert (md['shape'],p,md['pose'],md['family'],md['index'])==(v['shape'],v['prefix'],v['pose'],family,context['index'])
                    assert len(path)-1==p+md['tails'][md['side']] and path[p]==j and path[0]==m.start and path[-1]==m.goal
                    ds=graph_distances(m.cells,N,m.start);dg=graph_distances(m.cells,N,m.goal)
                    assert ds==o._from_start and dg==o.to_goal
                    opened={k for k,b in enumerate(m.cells) if b};noise=set(md['clutter'])
                    layouts.add(layout_hash(m))
                    assert len(noise)==10 and all(not any(m.cells[q] for q in adjacent(k,N,N*N)) for k in noise)
                    # The entire downstream graph and clutter are unchanged by source truncation or bending.
                    key=(context['id'],md['pose'],family,md['side'])
                    remaining=opened-set(path[:p])
                    if key in downstream:assert remaining==downstream[key]
                    else:downstream[key]=remaining
                    if p<=2:
                        key=(context['id'],p,md['pose'],family,md['side'])
                        if key in short_shapes:assert (m.cells,m.start,m.goal)==short_shapes[key]
                        else:short_shapes[key]=(m.cells,m.start,m.goal)
                    original_id=cid.rsplit('/d4-',1)[0]+'/d4-0';original=cases[original_id].maze
                    grid=np.frombuffer(original.cells,np.uint8).reshape(N,N);labels=np.arange(N*N).reshape(N,N)
                    if md['pose']>=4:grid=np.fliplr(grid);labels=np.fliplr(labels)
                    grid=np.rot90(grid,-(md['pose']%4));labels=np.rot90(labels,-(md['pose']%4))
                    assert grid.tobytes()==m.cells
                    assert int(np.flatnonzero(labels.ravel()==original.start)[0])==m.start
                    assert int(np.flatnonzero(labels.ravel()==original.goal)[0])==m.goal
                    if family=='disconnected':
                        assert ds[m.goal]<0 and not o.path;counts['no_path_cases']+=1;continue
                    assert ds[m.goal]==len(path)-1 and o.path==path
                    assert assess(synthetic(o,path),o).optimal
                    component={k for k,d in enumerate(ds) if d>=0}
                    degrees={k:sum(q in component for q in adjacent(k,N,N*N)) for k in component}
                    assert degrees[m.start]==degrees[m.goal]==1
                    assert max(degrees.values())<=3
                    expected=3 if family.startswith('cycle') else 2 if family.startswith('two') else 1 if family=='fork' else 0
                    assert sum(d==3 for d in degrees.values())==expected
                    assert sum(degrees.values())//2-len(component)+1==int(family.startswith('cycle'))
                    if family in BRANCHES:assert degrees[j]==3 and ds[j]==p
                    if family.startswith(('two','cycle')):
                        d=int(family[-1]);second=md['second_junctions'][str(d)]
                        assert degrees.get(second)==3 and ds[second]==p+d
                    ways=[0]*(N*N);ways[m.start]=1
                    for k in sorted(component,key=ds.__getitem__):
                        for q in adjacent(k,N,N*N):
                            if ds[q]==ds[k]+1:ways[q]+=ways[k]
                    assert ways[m.goal]==1
                    if md['alternative']:
                        r=assess(synthetic(o,md['alternative']),o)
                        assert r.valid_path and not r.optimal
                        assert len(md['alternative'])-len(path)==2*md['depth']+2*int(family[-1])
                        counts['legal_longer_rasters']+=1
                    counts['reachable_cases']+=1
    assert seen==set(cases)==set(metadata)
    assert len(cases)==1120*len(contexts)
    return dict(counts,contexts=len(contexts),cases=len(cases),whole_layouts=len(layouts))


def compare_traces(a,b,oa,ob,meta,checker):
    count=min(len(a),len(b));j=meta['junction'];source=oa.maze.start
    first=lambda x:next((i+1 for i,v in enumerate(x) if v),None)
    away=np.ones(N*N,bool);away[[oa.maze.goal,ob.maze.goal]]=False
    valid=[];optimal=[]
    for history,o in ((a,oa),(b,ob)):
        vs=[];os=[]
        for state in history:
            g=grade(*checker.prepared[o.maze.case_id],(state[2]>0).astype(np.uint8),0)
            vs.append(bool(g[0]));os.append(bool(g[1]))
        valid.append([i+1 for i,v in enumerate(vs) if v]);optimal.append([i+1 for i,v in enumerate(os) if v])
    return dict(ticks=[len(a),len(b)],identical_full_trajectory=bool(np.array_equal(a,b)),
        first_source_difference=first(np.any(a[:count,:,source]!=b[:count,:,source],axis=1)),
        first_junction_difference=first(np.any(a[:count,:,j]!=b[:count,:,j],axis=1)),
        first_output_away_difference=first(np.any((a[:count,2][:,away]>0)!=(b[:count,2][:,away]>0),axis=1)),
        valid_ticks=valid,optimal_ticks=optimal,paired_shortest_ticks=sorted(set(optimal[0])&set(optimal[1])))


def audit():
    from .junction_distance import check_freeze, warm, selected, TARGETS, panel
    started=time.perf_counter();packet=check_freeze();counts=Counter();replay_seconds=0.;work=0
    if (OUT/'verification.json').exists():raise FileExistsError('Audit closed')
    models=read_compressed(OUT/'panel.json.gz');rebuilt,_=panel();assert canonical(rebuilt)==models
    frozen=json.loads((OUT/'panel_freeze.json').read_text())
    for p,h in frozen['inputs'].items():assert sha(ROOT/p)==h;counts['panel_source_hashes']+=1
    for study in ('fork_pressure','routing_transfer','validation_breadth'):
        old_packet=json.loads((ROOT/'results'/study/'completion.json').read_text())
        for p,h in old_packet['source_and_artifact_sha256'].items():
            assert sha(ROOT/p)==h,p
            counts['prior_completion_entries']+=1
    cases,contexts,meta=load(OUT/'confirmation');fixtures,fc,fm=load(FIXTURES)
    g=geometry(cases,contexts,meta);fg=geometry(fixtures,fc,fm)
    old=FoundationData(0,exclusions()).layouts;assert len(old)==144120
    fixture_hashes={layout_hash(o.maze) for o in fixtures.values()};new={layout_hash(o.maze) for o in cases.values()}
    assert not(old&fixture_hashes or old&new or fixture_hashes&new)
    manifest=json.loads((OUT/'generation_manifest.json').read_text())
    for p,h in manifest['files'].items():assert sha(ROOT/p)==h;counts['main_input_hashes']+=1
    assert manifest['new_layouts']==len(new) and manifest['prior_layouts']==len(old|fixture_hashes)
    check=Checker(cases);fixture_check=Checker(fixtures);warmup=warm(fixtures,models)
    # Each replay is independently graded; exact coverage is checked, not inferred from a call count.
    normal={};trace_comparisons=[];pending={};native_checks=set();scopes=Counter();charged_work=0
    for scope,path,cs,md,checker in [('calibration',FIXTURES/'responses.jsonl.gz',fixtures,fm,fixture_check),
            ('normal',OUT/'normal.jsonl.gz',cases,meta,check),('interventions',OUT/'interventions.jsonl.gz',cases,meta,check),
            ('traces',OUT/'traces.jsonl.gz',cases,meta,check)]:
        seen=set();orgs={}
        for entry in lines(path):
            name,mode,row=entry['model'],entry['mode'],entry['row'];cid=row['case'];o=cs[cid];m=o.maze
            traced='history' in entry;key=(name,mode,cid,traced);assert key not in seen;seen.add(key)
            if (name,mode) not in orgs:orgs[name,mode]=organism(models[name],mode)
            org=orgs[name,mode]
            t=time.perf_counter();r=inference(org,m,mode,traced);replay_seconds+=time.perf_counter()-t
            reaction=r.reaction if traced else r
            assert canonical(normal_row(reaction,o))==row
            checker.row(row);counts['graded_replays']+=1;work+=reaction.instructions+reaction.spatial_reads
            if scope!='calibration':charged_work+=reaction.instructions+reaction.spatial_reads;scopes[scope]+=1
            if scope=='normal':normal[name,cid]=row
            if traced:
                history=unpack_history(entry['history']);assert np.array_equal(history,r.history)
                assert history.shape==(row['steps'],8,N*N) and 1<=row['steps']<=64
                counts['trace_frames']+=len(history);counts['full_horizon_traces']+=len(history)==64
                if scope=='traces':
                    if mode=='normal' and normal[name,cid]['steps']<=len(history):
                        tick=normal[name,cid]['steps']-1
                        assert np.packbits(history[tick,2]>0,bitorder='little').tobytes().hex()==normal[name,cid]['mask']
                        counts['native_emission_trace_matches']+=1
                    label=md[cid];pairkey=(name,mode,label['base'],label['shape'],label['prefix'],label['family'],label['pose'])
                    if label['side']==0:pending[pairkey]=(history,o)
                    else:
                        a,oa=pending.pop(pairkey);c=compare_traces(a,history,oa,o,label,checker)
                        if mode=='pulse_flag_off':assert c['identical_full_trajectory']
                        trace_comparisons.append(dict(model=name,mode=mode,case=cid,**c))
                    if MODES[mode][1]:
                        state,steps,reads,dispatch,active,status,memory,ranges=_probe_kernel(np.frombuffer(m.cells,np.uint8),N,m.start,m.goal,
                            org.program,TOPOLOGIES[org.topology],False,64,N*N*LIMITS.reads_per_site,N*N*LIMITS.instructions_per_site,True,True,org.goal_pulse)
                        assert np.array_equal(state,history[-1])
                        assert (steps,reads,dispatch,active,STATUSES[status],memory,tuple(ranges))==(row['steps'],row['reads'],row['dispatches'],row['active'],row['status'],row['array_bytes'],tuple(row['range_reads']))
                        counts['independent_observer_checks']+=1;work+=reads+dispatch
            if scope=='normal' and (name,md[cid]['family']) not in native_checks:
                native_checks.add((name,md[cid]['family']));adapter=respond(org,m.cells,m.w,m.h,m.start,m.goal).reaction
                assert canonical(normal_row(adapter,o))==row;counts['native_adapter_checks']+=1;work+=adapter.instructions+adapter.spatial_reads
        if scope=='normal':assert seen=={(n,'normal',c,False) for n in models for c in cs}
        if scope in ('interventions','traces'):
            modes=tuple(x for x in MODES if x!='normal') if scope=='interventions' else ('normal','pulse_off','flag_off','pulse_flag_off')
            assert seen=={(n,mode,c,scope=='traces') for n in TARGETS for mode in modes for c in cs if selected(md[c],scope=='traces')}
        print(json.dumps(dict(audit_scope=scope,replays=counts['graded_replays'],candidate_seconds=round(replay_seconds,2))),flush=True)
    assert not pending
    execution=json.loads((OUT/'execution.json').read_text());assert execution['complete']
    assert sum(scopes.values())==execution['budget']['calls']==277152
    assert charged_work==execution['budget']['work']
    for s,c in scopes.items():assert execution['budget']['scopes'][s]['calls']==c
    seen=set()
    for entry in lines(OUT/'baselines.jsonl.gz'):
        name,row=entry['model'],entry['row'];m=cases[row['case']].maze;key=(name,row['case']);assert key not in seen;seen.add(key)
        r=baseline(name,m.cells,m.w,m.h,m.start,m.goal)
        assert canonical(normal_row(r,cases[row['case']]))==row;check.row(row);assert row['optimal'] or row['no_path'];counts['baseline_replays']+=1
    assert seen=={(n,c) for n in ('compiled_bfs','compiled_astar','wave_bit') for c in cases}
    from .foundation_study import compressed_json
    compressed_json(OUT/'trace_comparisons.json.gz',trace_comparisons)
    write_json(OUT/'verification.json',dict(passed=True,counts=dict(counts),geometry=g,fixture_geometry=fg,
        old_layouts=len(old),fixture_layouts=len(fixture_hashes),new_layouts=len(new),future_exclusions=len(old|fixture_hashes|new),
        source_hashes=len(packet['sources']),input_hashes=len(packet['inputs']),warmup=warmup,
        candidate_replay_seconds=replay_seconds,audit_work=work,wall_seconds=time.perf_counter()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(audit_passed=True,counts=dict(counts))),flush=True)
