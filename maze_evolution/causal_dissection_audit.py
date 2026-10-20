"""V12V exact probe reconstruction, full replay and independent raster/graph audit."""
import json,time,resource,subprocess
from collections import Counter,defaultdict
from .causal_dissection_data import *
from .causal_dissection_study import (check_freeze,prior_check,make_panel,schedules,respond,projection,organism,record)
from .causal_dissection_analysis import compute
from .routing_mechanism_audit import geometry
from .foundation_study_verify_core import Checker
from .foundation_pair_confirm import normal_row
from .baselines import baseline
from .routing_transfer import canonical,sha,lines
from .foundation_calibration import write_json

def audit():
    t=time.perf_counter();reg=check_freeze();counts=Counter(prior_hashes=prior_check());panel=make_panel()
    assert panel==read_compressed(OUT/'panel.json.gz');counts['historical_edits']=len(panel['historical_events']);counts['synthetic_edits']=len(panel['synthetic_events'])
    previous=exclusions();allcases={};datasets={}
    generation=json.loads((OUT/'confirmation/generation.json').read_text())
    for name in ('panel.json.gz','preregistration.json'):
        assert subprocess.check_output(['git','show',f"{generation['revision']}:results/causal_dissection/{name}"])==(OUT/name).read_bytes()
    for p,h in generation['hashes'].items():assert sha(ROOT/p)==h
    for split,path,seed in [('fixture',FIXTURES,FIXTURE_SEED),('confirmation',OUT/'confirmation',SEED)]:
        d=create(seed,split,previous,split=='fixture');cases,contexts,meta=load(path)
        assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz')
        assert canonical(d.contexts)==contexts and canonical(d.metadata)==meta
        geometry(cases,contexts,meta);previous=d.layouts;allcases.update(cases);datasets[split]=(cases,meta)
    counts['whole_layouts']=len(previous);checker=Checker(allcases)
    for split,path in [('fixture',FIXTURES),('confirmation',OUT/'confirmation')]:
        cases,meta=datasets[split];plans=iter((scope,pid,mode,cid) for scope,pid,mode,kind,ids in schedules(panel,meta,split=='fixture') for cid in ids)
        calls=work=0;orgs={};native={};byprofile=Counter()
        for e in lines(path/'responses.jsonl.gz'):
            scope,pid,mode,row=e['scope'],e['model'],e['mode'],e['row'];cid=row['case'];o=cases[cid];m=o.maze;model=panel['models'][pid]
            assert (scope,pid,mode,cid)==next(plans)
            if scope=='normal':
                if pid not in orgs:orgs[pid]=organism(model)
                result=orgs[pid].react(m.cells,m.w,m.h,m.start,m.goal)
                if split=='fixture':native[pid,cid]=row
            else:result=respond(model,m,mode).reaction
            if scope=='parity':assert row==native[pid,cid];counts['native_adapter_parity']+=1
            assert record(result,o)==row,(split,scope,pid,mode,cid)
            checker.row(row);counts['candidate_replays']+=1;calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks']
            kind='structured' if not meta[cid]['family'].startswith('ordinary_') else 'ordinary'
            if scope!='normal':kind='parity' if scope=='parity' else 'mechanism'
            byprofile[f'{scope}|{pid}|{mode}|{kind}']+=1
            if calls%20000==0:print(json.dumps(dict(scope=split,replays=calls,wall=round(time.perf_counter()-t,2))),flush=True)
        assert next(plans,None) is None
        ex=json.loads((path/'execution.json').read_text());assert ex['complete'] and calls==ex['planned_calls']==ex['budget']['calls'] and work==ex['budget']['work']
        assert ex['budget']['seconds']<ex['budget']['cap'] and work<2_000_000_000_000 and calls<400000
        assert dict(byprofile)=={k:v['calls'] for k,v in ex['profiles'].items()}
        assert ex['peak_rss_bytes']<4*2**30
        assert sum(p.stat().st_size for p in path.rglob('*') if p.is_file())<2*2**30
        seen=set()
        for e in lines(path/'baselines.jsonl.gz'):
            name,row=e['model'],e['row'];cid=row['case'];o=cases[cid];m=o.maze
            assert (name,cid) not in seen;seen.add((name,cid))
            assert canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o))==row
            assert row['optimal'] or row['no_path'];checker.row(row);counts['baseline_replays']+=1
        assert seen=={(name,cid) for name in ('compiled_bfs','compiled_astar','wave_bit') for cid in cases if normal_case(meta[cid]) and (split!='fixture' or meta[cid]['pose']==0)}
        assert len(seen)==ex['baseline_calls']
    profile=json.loads((FIXTURES/'profile.json').read_text());fixture=json.loads((FIXTURES/'execution.json').read_text())
    projections={str(n):projection(fixture,n) for n in (3,2)}
    assert projections==profile['projections'] and profile['passed']
    chosen=next(n for n in (3,2) if projections[str(n)]<650)
    assert profile['contexts_per_shape']==chosen and profile['projected_seconds']==projections[str(chosen)]
    cases,meta=datasets['confirmation'];metrics,analysis=compute(panel,meta,lines(OUT/'confirmation/responses.jsonl.gz'))
    assert metrics==read_compressed(OUT/'metrics.json.gz') and analysis==read_compressed(OUT/'analysis.json.gz')
    brief={a:dict(kind=panel['kinds'][a],pairs=metrics[p+'|normal']['pairs'],positive=metrics[p+'|normal']['positive'],families=metrics[p+'|normal']['families']) for a,p in panel['aliases'].items()}
    assert brief==json.loads((OUT/'summary.json').read_text())
    from .causal_dissection_analysis import PREDICTIONS
    native={};observed={};aliases=panel['aliases'];reverse={pid:n for n,pid in aliases.items()}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        r=e['row'];key=(e['model'],r['case'])
        if e['scope']=='normal':native[key]=r
        else:
            name=reverse[e['model']];target=PREDICTIONS[name,e['mode']];q=native[aliases[target],r['case']]
            v=observed.setdefault(name+'|'+e['mode'],Counter());v['inputs']+=1
            v['full_record_equal']+=r==q;v['mask_equal']+=r['mask']==q['mask'];v['status_equal']+=r['status']==q['status'];v['steps_equal']+=r['steps']==q['steps'];v['behavior_equal']+=all(r[f]==q[f] for f in ('mask','status','steps'))
    assert {k:dict(v) for k,v in observed.items()}=={k:v['counts'] for k,v in analysis['signal_predictions'].items()}
    counts['signal_equivalence_cases']=sum(v['inputs'] for v in observed.values())
    counts['independently_graded_rasters']=checker.rasters
    write_json(OUT/'audit.json',dict(passed=True,counts=counts,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limitations='Exact candidate and baseline replay, independently graded rasters and graph oracles. New channel4 diagnostic adapter is checked against native fixture inference. Prespecified intervention-to-native equivalence predictions are independently tallied below; no second diagnostic interpreter. Analysis deterministically recomputed.'))
    print((OUT/'audit.json').read_text(),flush=True)
