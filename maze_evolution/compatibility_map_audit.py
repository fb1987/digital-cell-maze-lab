"""V12W exact probe reconstruction, full replay and independent raster/graph audit."""
import json,time,resource,subprocess
from collections import Counter,defaultdict
from .compatibility_map_data import *
from .compatibility_map_study import (check_freeze,prior_check,make_panel,schedules,projection,organism,record,label)
from .compatibility_map_analysis import compute
from .routing_mechanism_audit import geometry
from .foundation_study_verify_core import Checker
from .foundation_pair_confirm import normal_row
from .baselines import baseline
from .routing_transfer import canonical,sha,lines
from .foundation_calibration import write_json

def independent_panel(panel):
    from .exposure_genome import Individual
    u=read_compressed(ROOT/'results/lineage_mapping/panel.json.gz')
    base=Individual.load(u['items']['d07']);original=[g.row() for g in base.genome.genes]
    ids=list(range(len(original)));history=[g.row() for g in Individual.load(u['items']['d08']).genome.genes];changes={}
    for edit in (9,10,11,12):
        event=u['events'][f'd{edit:02}']['mutation'][0];idx=event['index'];locus=ids[idx]
        changes[edit]=(locus,event.get('row'))
        if event['kind']=='delete':del ids[idx];del history[idx]
        else:history[idx]=event['row']
        assert history==[g.row() for g in Individual.load(u['items'][f'd{edit:02}']).genome.genes]
    assert changes=={9:(132,[17,45,6,0,0,0,64]),10:(106,None),11:(234,[9,35,28,4,0,0,64]),12:(207,[10,51,63,54,0,0,39])}
    for name,c in panel['conditions'].items():
        rows=list(original);rows[222]=original[222] if c['store'] else [0,34,34,0,0,0,64]
        # Descending original positions make deletions independent of application order.
        for locus,new in sorted((changes[e] for e in c['edits']),reverse=True):
            if new is None:del rows[locus]
            else:rows[locus]=new
        item=Individual.load(panel['items'][name]);assert rows==[g.row() for g in item.genome.genes]
        assert item.genome.exposure==base.genome.exposure==7 and item.birth==-1 and item.parent==base.identity
        assert len(rows)==256-int(10 in c['edits'])
        assert name==label(c['mask'],c['store'])
    return len(panel['conditions'])

def audit():
    t=time.perf_counter();reg=check_freeze();counts=Counter(prior_hashes=prior_check());panel=make_panel()
    assert panel==read_compressed(OUT/'panel.json.gz');counts['factorial_programs_independently_rebuilt']=independent_panel(panel)
    previous=exclusions();allcases={};datasets={}
    generation=json.loads((OUT/'confirmation/generation.json').read_text())
    for name in ('panel.json.gz','preregistration.json'):
        assert subprocess.check_output(['git','show',f"{generation['revision']}:results/compatibility_map/{name}"])==(OUT/name).read_bytes()
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
            assert scope==mode=='normal'
            if pid not in orgs:orgs[pid]=organism(model)
            result=orgs[pid].react(m.cells,m.w,m.h,m.start,m.goal)
            assert record(result,o)==row,(split,scope,pid,mode,cid)
            checker.row(row);counts['candidate_replays']+=1;calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks']
            kind='structured' if not meta[cid]['family'].startswith('ordinary_') else 'ordinary'
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
        assert seen=={(name,cid) for name in ('compiled_bfs','compiled_astar','wave_bit') for cid in cases if query_case(meta[cid],split=='fixture')}
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
    # Separately recompute each context's factorial store effects from raw pairs,
    # then reconstruct every subset's effect from anchored higher-order coefficients.
    raw=defaultdict(dict)
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):raw[e['model']][e['row']['case']]=e['row']
    grouped=defaultdict(list)
    for cid,m in meta.items():
        if m['family']=='paired' and query_case(m):grouped[(m['template'],m['base'],m['pose'])].append(cid)
    direct=defaultdict(lambda:Counter({str(i):0 for i in range(16)}))
    for (context,base,pose),ids in grouped.items():
        assert len(ids)==2
        if meta[ids[0]]['prefix']==0:continue
        for mask in range(16):
            a,b=panel['aliases'][label(mask,False)],panel['aliases'][label(mask,True)]
            direct[context][str(mask)]+=int(all(raw[b][i]['optimal'] for i in ids))-int(all(raw[a][i]['optimal'] for i in ids))
    assert dict(direct)==analysis['context_store_effects']
    for context,coeff in analysis['context_anchored_higher_order'].items():
        for mask in range(16):assert sum(coeff[s] for s in range(16) if s&mask==s)==direct[context][str(mask)]
    counts['independent_factorial_context_checks']=16*len(direct)
    counts['independently_graded_rasters']=checker.rasters
    write_json(OUT/'audit.json',dict(passed=True,counts=counts,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limitations='Full exact native replay and independent raster/graph grading; historical event indices independently mapped to original loci for all32 probes. Per-context factorial effects separately tallied from raw paired responses. No independent second VM interpreter, no lineage replication, no speed benchmark.'))
    print((OUT/'audit.json').read_text(),flush=True)
