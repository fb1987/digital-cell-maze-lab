"""V12P independent graphs/raster grading, native parity and exact replay."""
import json,time,resource
from collections import defaultdict
from cellular_maze_lab import neighbors
from .mutation_transition_data import *
from .foundation_study_verify_core import Checker
from .foundation_calibration import write_json,LIMITS
from .routing_transfer import sha,canonical,lines
from .evaluator import distances
from .exposure_selection import record,organism as native_organism
from .exposure_genome import Genome
from .foundation_pair_confirm import normal_row
from .baselines import baseline


def geometry(cases,contexts,meta):
    pairs=defaultdict(list);full=defaultdict(list);posegroups=defaultdict(set);cycles=0
    for cid,o in cases.items():
        m=o.maze;d=meta[cid];path=d['path'];posegroups[d['config'],d['family'],d['side']].add(d['pose'])
        assert m.start==path[0] and m.cells[m.start] and m.cells[m.goal]
        assert sum(m.cells[q] for q in neighbors(m.start,m.w,m.h))==d['source_degree']
        if d['family']=='disconnected':assert not o.path and not any(m.cells[q] for q in neighbors(m.goal,m.w,m.h));continue
        assert path==o.path and len(path)-1==d['prefix']+d['arm'] and m.goal==path[-1]
        assert len(set(path))==len(path)
        assert all(b in neighbors(a,m.w,m.h) for a,b in zip(path,path[1:]))
        if d['family']=='paired':
            pairs[d['config'],d['pose']].append((m,d));ds=distances(m,m.start);component={p for p,v in enumerate(ds) if v>=0};edges=sum(sum(q in component for q in neighbors(p,m.w,m.h)) for p in component)//2
            rank=edges-len(component)+1;assert rank==int(d['graph']=='cycle')
            if d['control']=='full':
                full[d['template'],d['bend'],d['graph'],d['pose'],d['side']].append(m.cells)
                assert d['source_degree']==(3 if d['prefix']==0 else 2)
            elif d['control']=='no_stem':assert d['source_degree']==2 and d['prefix']==0
            else:assert d['source_degree']==3 and d['prefix'] in (2,4)
            if d['graph']=='cycle':
                a=d['alternative'];assert a[0]==m.start and a[-1]==m.goal and len(a)-len(path)==12 and len(set(a))==len(a)
                assert all(m.cells[p] for p in a) and all(b in neighbors(x,m.w,m.h) for x,b in zip(a,a[1:]));aset=set(a)
                assert all(sum(q in aset for q in neighbors(p,m.w,m.h))==(1 if p in (m.start,m.goal) else 2) for p in a);cycles+=1
    for key,rs in pairs.items():
        assert len(rs)==2;rs.sort(key=lambda x:x[1]['side']);(a,da),(b,db)=rs;assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
        common=[]
        for x,y in zip(da['path'],db['path']):
            if x!=y:break
            common.append(x)
        assert len(common)==da['prefix']+1 and common[-1]==da['junction']
    assert all(len(set(cells))==1 for cells in full.values())
    assert all(poses==set(range(8)) for poses in posegroups.values())
    assert set(d['template'] for d in meta.values())=={c['id'] for c in contexts}
    return dict(cases=len(cases),templates=len(contexts),pairs=len(pairs),cycles=cycles,whole_layouts=len({layout_hash(o.maze) for o in cases.values()}))


def independent_counts(rows,meta,saved):
    pairs=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family']=='paired':pairs[m['config']+f'/pose{m["pose"]}'].append(r)
    good={k:len(rs)==2 and all(r['optimal'] for r in rs) for k,rs in pairs.items()}
    assert sum(good.values())==saved['pairs'] and len(good)==saved['pair_opportunities']
    assert good=={k:v['complete'] for k,v in saved['details'].items()}
    for f in ('optimal','valid','no_path'):assert sum(r[f] for r in rows)==saved[f]
    assert sum(r['reachable'] and r['status']=='no_path' for r in rows)==saved['false_no_path']
    assert sum(r['optimal'] for r in rows if meta[r['case']]['family']=='corridor')==saved['corridors']


def audit():
    from .mutation_transition_study import check_freeze,make_panel,organism,schedule,MODES,PRIOR,CAP,CALL_CAP,WORK_CAP
    from .mutation_transition_analysis import summarize,packet
    from .growth_runtime import Organism as Legacy
    from .route_confirmation_runtime import respond
    t=time.perf_counter();reg=check_freeze();counts=defaultdict(int)
    for name in PRIOR:
        for p,h in json.loads((ROOT/'results'/name/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;counts['prior_completion_hashes']+=1
    panel=make_panel();assert panel==read_compressed(OUT/'panel.json.gz');counts['lineage_mutations']=len(panel['events'])
    previous=exclusions();datasets={};allcases={}
    for scope,path,seed,repeats in [('fixture',FIXTURES,FIXTURE_SEED,1),('confirmation',OUT/'confirmation',SEED,2)]:
        actual=create(seed,scope,previous,repeats);cases,contexts,meta=load(path);counts['graph_cases']+=geometry(cases,contexts,meta)['cases']
        assert canonical(manifest(actual.cache.values()))==read_compressed(path/'mazes.json.gz')
        assert canonical(actual.contexts)==contexts and canonical(actual.metadata)==meta
        previous+=read_compressed(path/'mazes.json.gz');datasets[scope]=(cases,contexts,meta);allcases.update(cases)
    counts['whole_layouts_through_P']=len(actual.layouts);del actual,previous
    checker=Checker(allcases);metrics={};budgets={};orgs={};native={};legacy={}
    for scope,path in [('fixture',FIXTURES),('confirmation',OUT/'confirmation')]:
        cases,contexts,meta=datasets[scope];plans=iter(schedule(panel,meta,scope=='fixture'));current=next(plans);ki=0;rows=[];work=0;calls=0;pending_native=None
        for rec in lines(path/'responses.jsonl.gz'):
            key,mode,row=rec['model'],rec['mode'],rec['row'];o=cases[row['case']];m=o.maze
            if mode=='native_parity':
                assert pending_native==(key,row);pending_native=None
                if key not in native:native[key]=native_organism(panel['models'][key])
                r=record(native[key].react(m.cells,m.w,m.h,m.start,m.goal),o);counts['native_parity']+=1
            else:
                assert pending_native is None
                pk,pm,ids=current;assert (key,mode,row['case'])==(pk,pm,ids[ki])
                if (key,mode) not in orgs:orgs[key,mode]=organism(panel['models'][key],mode)
                r=record(orgs[key,mode].react(m.cells,m.w,m.h,m.start,m.goal),o);rows.append(r);ki+=1
                if scope=='fixture' and mode=='normal' and meta[row['case']]['family']=='paired':pending_native=(key,row)
                if scope=='fixture' and key in panel['mechanisms'] and meta[row['case']]['family']=='paired':
                    pulse,flag,endpoint,ablate=MODES[mode]
                    if (key,mode) not in legacy:legacy[key,mode]=Legacy(Genome.from_dict(panel['models'][key]['genome']).program,panel['models'][key]['topology'],LIMITS,ablate_nonlocal=ablate,goal_pulse=pulse)
                    rr=canonical(normal_row(respond(legacy[key,mode],m.cells,m.w,m.h,m.start,m.goal,goal_flag=flag,halt_mode='normal' if endpoint else 'source_only').reaction,o))
                    for f in rr:
                        if f!='array_bytes':assert rr[f]==row[f],(mode,f,row['case'])
                    counts['independent_adapter_parity']+=1
                if ki==len(ids):
                    if scope=='confirmation':
                        s=summarize(rows,meta);independent_counts(rows,meta,s);metrics[key+'|'+mode]=s;counts['model_mode_summaries']+=1
                    rows=[];ki=0;current=next(plans,None)
            assert canonical(r)==row,(scope,key,mode,row['case']);checker.row(row);counts['candidate_replays']+=1;calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks']
            if calls%50000==0:print(json.dumps(dict(scope=scope,calls=calls,seconds=round(time.perf_counter()-t,2))),flush=True)
        assert current is None and not rows and pending_native is None;budgets[scope]=dict(calls=calls,work=work)
    saved=read_compressed(OUT/'metrics.json.gz');assert metrics==saved
    result=packet(metrics,panel);assert result==read_compressed(OUT/'analysis.json.gz')
    # Independent consecutive success-set and intervention retention checks.
    for top in ('local','evolved'):
        sets=[{k for k,d in metrics[panel['aliases'][f'{top}/route/d{depth}']+'|normal']['details'].items() if d['complete']} for depth in range(17)]
        for depth,tr in enumerate(result['transitions'][top],1):assert set(tr['gained_keys'])==sets[depth]-sets[depth-1] and set(tr['lost_keys'])==sets[depth-1]-sets[depth]
    for key,probes in result['mechanisms'].items():
        normal=metrics[key+'|normal']['details']
        for mode,v in probes.items():
            ds=metrics[key+'|'+mode]['details'];good={k for k,d in ds.items() if d['complete']};original={k for k in ds if normal[k]['complete']}
            assert (v['retained'],v['lost'],v['new'])==(len(good&original),len(original-good),len(good-original))
    seen=set();cases,_,meta=datasets['confirmation']
    for rec in lines(OUT/'confirmation/baselines.jsonl.gz'):
        key,row=rec['model'],rec['row'];assert (key,row['case']) not in seen;seen.add((key,row['case']));o=cases[row['case']];m=o.maze
        r=canonical(normal_row(baseline(key,m.cells,m.w,m.h,m.start,m.goal),o));assert r==row and (r['optimal'] or r['no_path']);checker.row(row)
    assert len(seen)==3*len(cases);counts['baseline_replays']=len(seen)
    profile=json.loads((FIXTURES/'profile.json').read_text());run=json.loads((OUT/'confirmation/execution.json').read_text());generation=json.loads((OUT/'confirmation/generation.json').read_text())
    for p,h in generation['hashes'].items():assert sha(ROOT/p)==h,p
    assert run['complete'] and run['planned_calls']==profile['projected_calls']==budgets['confirmation']['calls']
    assert profile['passed'] and abs(profile['projected_seconds']-16*sum(v['seconds'] for v in profile['profiles'].values()))<1e-8
    for scope,recording in [('fixture',profile),('confirmation',run)]:
        assert recording['budget']['calls']==budgets[scope]['calls'] and recording['budget']['work']==budgets[scope]['work']
        assert recording['budget']['seconds']<recording['budget']['cap_seconds'] and recording['peak_rss_bytes']<4*2**30
    assert run['budget']['seconds']<CAP and run['budget']['calls']<=CALL_CAP and run['budget']['work']<=WORK_CAP
    for top in ('local','evolved'):
        s=metrics[panel['aliases'][top+'/intact']+'|normal'];assert s['optimal']==2*len(cases)//3 and s['no_path']==len(cases)//3
    counts['independent_rasters']=checker.rasters
    v=dict(passed=True,counts=dict(counts),source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(OUT/'verification.json',v);print(json.dumps(v,indent=2),flush=True)
