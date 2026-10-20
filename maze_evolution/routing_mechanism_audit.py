"""V12T independent graph checks, raster grades and complete exact replay."""
import json,time,resource
from collections import defaultdict,Counter,deque
import numpy as np
from cellular_maze_lab import neighbors
from .routing_mechanism_data import *
from .foundation_study_verify_core import Checker
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines
from .exposure_selection import record,organism
from .foundation_pair_confirm import normal_row
from .baselines import baseline

def component(m,start):
    dist={start:0};q=deque([start])
    while q:
        p=q.popleft()
        for v in neighbors(p,m.w,m.h):
            if m.cells[v] and v not in dist:dist[v]=dist[p]+1;q.append(v)
    return dist

def geometry(cases,contexts,meta):
    pairs=defaultdict(list);poses=defaultdict(set);downstream=defaultdict(set);counts=Counter()
    for cid,o in cases.items():
        m=o.maze;d=meta[cid];comp=component(m,m.start)
        assert m.cells[m.start] and m.cells[m.goal]
        assert bool(o.path)==(m.goal in comp)
        if o.path:assert len(o.path)-1==comp[m.goal]
        counts['inputs']+=1
        if d['family'].startswith('ordinary_'):continue
        poses[d['base'],d['side']].add(d['pose'])
        if d['family']=='disconnected':
            assert not o.path and len(component(m,m.goal))>=3
            assert any(m.cells[q] for q in neighbors(m.goal,m.w,m.h));counts['nonisolated_no_path']+=1;continue
        path=d['path'];assert path==o.path and len(path)==d['prefix']+d['arm_lengths'][d['side']]+1
        assert len(set(path))==len(path) and path[0]==m.start and path[-1]==m.goal
        assert all(b in neighbors(a,m.w,m.h) for a,b in zip(path,path[1:]))
        if d['family']=='paired':
            pairs[d['base'],d['pose']].append((m,d))
            edges=sum(sum(v in comp for v in neighbors(p,m.w,m.h)) for p in comp)//2
            assert edges-len(comp)+1==int(d['graph']=='cycle')
            stem=set(path[:d['prefix']]);downstream[d['template'],d['graph'],d['second'],d['pose']].add(tuple(p for p,v in enumerate(m.cells) if v and p not in stem))
            if d['graph']=='cycle':
                alt=d['alternative'];aset=set(alt)
                assert len(alt)==len(path)+2*(d['second']+d['depth']) and len(aset)==len(alt)
                assert alt[0]==m.start and alt[-1]==m.goal and all(m.cells[p] for p in alt)
                assert all(b in neighbors(a,m.w,m.h) for a,b in zip(alt,alt[1:]))
                assert all(sum(q in aset for q in neighbors(p,m.w,m.h))==(1 if p in (m.start,m.goal) else 2) for p in alt)
                counts['true_cycle_inputs']+=1
    for rs in pairs.values():
        assert len(rs)==2
        (a,da),(b,db)=rs
        assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
        common=[]
        for x,y in zip(da['path'],db['path']):
            if x!=y:break
            common.append(x)
        assert len(common)==da['prefix']+1 and common[-1]==da['junction']
    assert all(len(v)==1 for v in downstream.values())
    assert all(v==set(range(8)) for v in poses.values())
    assert {d['template'] for d in meta.values() if not d['family'].startswith('ordinary_')}=={c['id'] for c in contexts}
    counts.update(contexts=len(contexts),pairs=len(pairs),whole_layouts=len({layout_hash(o.maze) for o in cases.values()}))
    return dict(counts)

def independent_predictor(o,k):
    m=o.maze;ds=component(m,m.goal);ball={p for p,d in ds.items() if d<=ds[m.start]}
    for _ in range(k):ball={p for p in ball if p in (m.start,m.goal) or sum(q in ball for q in neighbors(p,m.w,m.h))>1}
    mask=np.array([p in ball for p in range(len(m.cells))],np.uint8)
    return np.packbits(mask,bitorder='little').tobytes().hex()

def audit():
    from .routing_mechanism_study import check_freeze,prior_check,make_panel,schedules,respond,unpack_history
    from .routing_mechanism_analysis import summarize,packet,predictions
    from .mutation_transition_runtime import Organism as Legacy
    from .exposure_genome import Genome
    from .foundation_calibration import LIMITS
    t=time.perf_counter();reg=check_freeze();counts=Counter(prior_hashes=prior_check());panel=make_panel()
    assert panel==read_compressed(OUT/'panel.json.gz');counts['ancestry_events']=len(panel['events'])
    previous=exclusions();allcases={};datasets={}
    for split,path,seed in [('fixture',FIXTURES,FIXTURE_SEED),('confirmation',OUT/'confirmation',SEED)]:
        d=create(seed,split,previous);cases,contexts,meta=load(path)
        assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz')
        assert canonical(d.contexts)==contexts and canonical(d.metadata)==meta
        geometry(cases,contexts,meta);previous=d.layouts;allcases.update(cases);datasets[split]=(cases,meta)
    counts['whole_layouts']=len(previous);checker=Checker(allcases);metrics={};trace_expected=[];predictor_counts={}
    for split,path in [('fixture',FIXTURES),('confirmation',OUT/'confirmation')]:
        cases,meta=datasets[split];plans=iter((scope,pid,mode,cid) for scope,pid,mode,ids in schedules(panel,meta,split=='fixture') for cid in ids)
        pending=None;rows=defaultdict(list);calls=0;work=0;legacy={};orgs={};traces=0
        for e in lines(path/'responses.jsonl.gz'):
            scope,pid,mode,row=e['scope'],e['model'],e['mode'],e['row'];cid=row['case'];o=cases[cid];m=o.maze;model=panel['models'][pid]
            if scope=='parity':assert pending==(pid,row);pending=None
            else:
                assert pending is None and (scope,pid,mode,cid)==next(plans)
                if split=='fixture' and scope=='normal':pending=(pid,row)
            if scope=='normal':
                if pid not in orgs:orgs[pid]=organism(model)
                result=orgs[pid].react(m.cells,m.w,m.h,m.start,m.goal)
            else:
                diag=respond(model,m,mode,trace=scope=='trace',forced=scope=='trace');result=diag.reaction
                if scope=='trace':
                    h=unpack_history(e['history']);assert np.array_equal(diag.history,h)
                    assert diag.instrumentation_bytes==e['instrumentation_bytes'];counts['trace_frames']+=len(h);traces+=1
                elif split=='fixture' and mode in ('normal','pulse_off','flag_off','both_off','endpoint_off'):
                    key=(pid,mode)
                    if key not in legacy:legacy[key]=Legacy(Genome.from_dict(model['genome']),'active','local',LIMITS,mode not in ('pulse_off','both_off'),mode not in ('flag_off','both_off'),mode!='endpoint_off')
                    assert record(legacy[key].react(m.cells,m.w,m.h,m.start,m.goal),o)==row
                    counts['independent_adapter_parity']+=1
            assert record(result,o)==row,(split,scope,pid,mode,cid)
            checker.row(row);counts['candidate_replays']+=1;calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks']
            if split=='confirmation' and scope in ('normal','intervention'):rows[pid+'|'+mode].append(row)
            if calls%20000==0:print(json.dumps(dict(scope=split,replays=calls,wall=round(time.perf_counter()-t,2))),flush=True)
        assert pending is None and next(plans,None) is None
        ex=json.loads((path/'execution.json').read_text());assert ex['complete'] and calls==ex['budget']['calls'] and work==ex['budget']['work']
        for key,rs in rows.items():metrics[key]=summarize(rs,meta)
        seen=set()
        for e in lines(path/'baselines.jsonl.gz'):
            name,row=e['model'],e['row'];cid=row['case'];o=cases[cid];m=o.maze
            assert (name,cid) not in seen;seen.add((name,cid))
            assert canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o))==row
            checker.row(row);counts['baseline_replays']+=1
        assert seen=={(name,cid) for name in ('compiled_bfs','compiled_astar','wave_bit') for cid in cases if split!='fixture' or meta[cid]['pose']==0}
    # The pre-registration timing refinement reruns native fixture inference;
    # its outputs and additional cost are preserved, not omitted from the audit.
    costs=json.loads((FIXTURES/'native_cost.json').read_text());calls=work=0;seen=set();cases,meta=datasets['fixture'];orgs={}
    for e in lines(FIXTURES/'native_cost.jsonl.gz'):
        pid,row=e['model'],e['row'];cid=row['case'];o=cases[cid];m=o.maze
        assert (pid,cid) not in seen;seen.add((pid,cid))
        if pid not in orgs:orgs[pid]=organism(panel['models'][pid])
        assert record(orgs[pid].react(m.cells,m.w,m.h,m.start,m.goal),o)==row
        checker.row(row);calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks']
    assert seen=={(pid,cid) for pid in panel['models'] for cid in cases if meta[cid]['pose']==0}
    assert calls==costs['budget']['calls']-costs['initial_budget']['calls'] and work==costs['budget']['work']-costs['initial_budget']['work']
    counts['candidate_replays']+=calls;counts['native_cost_replays']=calls
    profile=json.loads((FIXTURES/'profile.json').read_text());initial=json.loads((FIXTURES/'execution.json').read_text())
    from .routing_mechanism_study import TRACE_TARGETS
    target={panel['aliases'][n] for n in TRACE_TARGETS};extra=0
    for key,p in initial['profiles'].items():
        scope,pid,mode=key.split('|')
        if scope=='trace' or scope=='intervention' and pid in target:extra+=p['seconds']*8
    projections={str(n):2*(sum(v['seconds']*(8*n if k.endswith('|structured') else 8) for k,v in costs['rates'].items())+extra) for n in (2,1)}
    assert projections==profile['projections']
    assert profile['contexts_per_shape']==next(n for n in (2,1) if projections[str(n)]<600)
    assert costs['budget']['seconds']<180 and profile['passed']
    assert metrics==read_compressed(OUT/'metrics.json.gz') and packet(panel,metrics)==read_compressed(OUT/'analysis.json.gz')
    # Independent graph implementation verifies all seven explanatory masks;
    # recompute all saved fit counts separately from the analysis implementation.
    cases,meta=datasets['confirmation'];pred={}
    for cid,o in cases.items():
        if o.path:
            pred[cid]=[independent_predictor(o,k) for k in range(7)];assert pred[cid]==predictions(o);counts['predictor_masks']+=7
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        if e['scope']!='normal':continue
        r=e['row'];cid=r['case'];pid=e['model']
        if cid not in pred:continue
        m=meta[cid]
        for label in ('all_reachable',m['family'],f"shape/{m.get('shape','ordinary')}"):
            v=predictor_counts.setdefault(pid,{}).setdefault(label,dict(inputs=0,matches=[0]*7,emitted_matches=[0]*7));v['inputs']+=1
            for k,p in enumerate(pred[cid]):v['matches'][k]+=r['mask']==p;v['emitted_matches'][k]+=r['mask']==p and r['status']=='emitted'
    assert predictor_counts==json.loads((OUT/'predictor_fit.json').read_text())['models']
    # Recompute the complete deterministic analysis including forced-frame grades;
    # byte-equivalent canonical artifacts must remain unchanged.
    from .routing_mechanism_analysis import analyze
    names=('metrics.json.gz','analysis.json.gz','trace_details.json.gz','trace_summary.json','predictor_fit.json')
    before={name:(read_compressed(OUT/name) if name.endswith('.gz') else json.loads((OUT/name).read_text())) for name in names}
    analyze()
    after={name:(read_compressed(OUT/name) if name.endswith('.gz') else json.loads((OUT/name).read_text())) for name in names}
    assert before==after
    counts['independently_graded_rasters']=checker.rasters
    write_json(OUT/'audit.json',dict(passed=True,counts=counts,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limitations='All normal/intervention/forced responses exactly replayed and independently graded. All trace states replayed; frame summaries deterministically recomputed. No independent second interpreter for feedback/halting interventions beyond synthetic tests.'))
    print((OUT/'audit.json').read_text(),flush=True)
