"""V13A independent graph/raster checks, exact inference and ancestry replay."""
import json,time,resource,subprocess
from collections import Counter,defaultdict
import numpy as np
from cellular_maze_lab import neighbors
from .branch_overgrowth_data import *
from .routing_mechanism_audit import component
from .family_evolution_audit import geometry as old_geometry
from .foundation_study_verify_core import Checker
from .routing_transfer import canonical,lines,sha
from .foundation_calibration import write_json,LIMITS
from .exposure_selection import organism,record
from .foundation_pair_confirm import normal_row
from .baselines import baseline

def geometry(cases,contexts,meta):
    result=old_geometry(cases,meta);poses=defaultdict(set);groups=defaultdict(set);starts=defaultdict(set)
    for cid,o in cases.items():
        m=o.maze;v=meta[cid];dist=component(m,m.start)
        assert bool(o.path)==(m.goal in dist)
        if o.path:assert len(o.path)-1==dist[m.goal]
        if v['family'].startswith('ordinary_'):continue
        poses[v['base'],v['family'],v['side']].add(v['pose'])
        if v['family']!='paired':continue
        comp=set(dist);edges=sum(sum(q in comp for q in neighbors(p,m.w,m.h)) for p in comp)//2
        assert edges-len(comp)+1==int(v['graph']=='cycle')
        groups[v['template'],v['graph'],v['pose'],v['side']].add((m.cells,m.goal));starts[v['template'],v['graph'],v['pose'],v['side']].add(m.start)
        assert o.path[v['prefix']]==v['junction']
        if v['graph']=='cycle':
            alt=v['alternative'];points=set(alt)
            assert all(sum(q in points for q in neighbors(p,m.w,m.h))==(1 if p in (m.start,m.goal) else 2) for p in alt)
    assert all(v==set(range(8)) for v in poses.values())
    assert all(len(v)==1 for v in groups.values()) and all(len(v)==5 for v in starts.values())
    assert len(contexts)==result['contexts'];result['total_inputs']=len(cases)
    return result

def audit():
    from .branch_overgrowth_study import check_freeze,prior_check,make_panel,schedules,respond,unpack_history,HORIZON,projection
    from .branch_overgrowth_analysis import compute
    from .mutation_transition_runtime import Organism as Legacy
    from .exposure_genome import Genome
    t=time.perf_counter();reg=check_freeze();counts=Counter(prior_hashes=prior_check());assert counts['prior_hashes']==7880
    panel=make_panel();assert panel==read_compressed(OUT/'panel.json.gz');counts['ancestry_events']=len(panel['events']);old=exclusions();profile=json.loads((FIXTURES/'profile.json').read_text());geometries={}
    for split,path,seed,repeats in [('fixture',FIXTURES,FIXTURE_SEED,1),('confirmation',OUT/'confirmation',SEED,profile['repeats'])]:
        d=create(seed,split,old,repeats);cases,contexts,meta=load(path)
        assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz')
        assert canonical(d.metadata)==meta and canonical(d.contexts)==contexts
        geometries[split]=geometry(cases,contexts,meta);old=d.layouts
        checker=Checker(cases);schedule=iter(schedules(panel,meta,split=='fixture'));orgs={};legacy={};work=calls=0;pending=None
        for e in lines(path/'responses.jsonl.gz'):
            scope,pid,mode,r=e['scope'],e['model'],e['mode'],e['row'];cid=r['case'];o=cases[cid];m=o.maze;model=panel['models'][pid]
            assert (scope,pid,mode,cid)==next(schedule)
            if scope=='normal':
                if pid not in orgs:orgs[pid]=organism(model)
                result=orgs[pid].react(m.cells,m.w,m.h,m.start,m.goal)
                if split=='fixture':assert pending is None;pending=r
            else:
                diag=respond(model,m,mode,trace=scope=='trace',forced=scope=='trace',horizon=HORIZON);result=diag.reaction
                if scope=='trace':
                    h=unpack_history(e['history']);assert np.array_equal(h,diag.history);assert diag.instrumentation_bytes==e['instrumentation_bytes'];counts['trace_frames']+=len(h)
                elif split=='fixture' and mode in ('normal','pulse_off','flag_off','both_off','endpoint_off'):
                    key=(pid,mode)
                    if key not in legacy:legacy[key]=Legacy(Genome.from_dict(model['genome']),'active','local',LIMITS,mode not in ('pulse_off','both_off'),mode not in ('flag_off','both_off'),mode!='endpoint_off')
                    assert record(legacy[key].react(m.cells,m.w,m.h,m.start,m.goal),o)==r;counts['legacy_adapter_parity']+=1
                if scope=='parity':assert r==pending;pending=None
            assert record(result,o)==r,(split,scope,pid,mode,cid)
            checker.row(r);calls+=1;work+=r['reads']+r['dispatches']+r['exposure_checks']
            if calls%20000==0:print(json.dumps(dict(split=split,replays=calls,wall=round(time.perf_counter()-t,2))),flush=True)
        assert next(schedule,None) is None and pending is None
        ex=json.loads((path/'execution.json').read_text());assert ex['complete'] and calls==ex['planned_calls']==ex['budget']['calls'] and work==ex['budget']['work']
        assert ex['budget']['seconds']<(180 if split=='fixture' else 720) and ex['peak_rss_bytes']<4*2**30
        assert sum(v['calls'] for v in ex['rates'].values())==calls and abs(sum(v['seconds'] for v in ex['rates'].values())-ex['budget']['seconds'])<1e-5
        bc=0;seen=set()
        for e in lines(path/'baselines.jsonl.gz'):
            name,r=e['model'],e['row'];o=cases[r['case']];m=o.maze;key=(name,r['case']);assert key not in seen;seen.add(key)
            assert canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o))==r;checker.row(r);bc+=1
        expected={(name,cid) for name in ('compiled_bfs','compiled_astar','wave_bit') for cid in cases if split!='fixture' or meta[cid]['pose']==0}
        assert seen==expected and bc==ex['baseline_calls'];counts['candidate_replays']+=calls;counts['baseline_replays']+=bc;counts['independently_graded_rasters']+=checker.rasters
    fixture=json.loads((FIXTURES/'execution.json').read_text());projections={str(n):projection(fixture['rates'],n) for n in (2,1)}
    assert projections==profile['projections'] and profile['repeats']==next(n for n in (2,1) if projections[str(n)]<600)
    assert compute()==read_compressed(OUT/'analysis.json.gz')
    rev=json.loads((OUT/'confirmation/generation.json').read_text())['revision']
    for name in ('panel.json.gz','preregistration.json'):assert subprocess.check_output(['git','show',f'{rev}:results/branch_overgrowth/{name}'])==(OUT/name).read_bytes()
    for name,h in json.loads((OUT/'confirmation/generation.json').read_text())['hashes'].items():assert sha(ROOT/name)==h,name
    write_json(OUT/'audit.json',dict(passed=True,counts=counts,whole_layouts=len(old),geometry=geometries,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,limitations='Every response and full trajectory exactly replayed; response rasters independently graded. All frame summaries recomputed using separate grader. Halt-off uses tested adapter, not a second full interpreter. No inference tuning or generalization beyond the registered grammar.'))
    print((OUT/'audit.json').read_text(),flush=True)
