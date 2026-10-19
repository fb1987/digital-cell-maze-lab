"""V12R complete deterministic replay and independent raster/proxy verification."""
from collections import defaultdict
from .mutation_accessibility_study import *
from .shared_prefix_audit import geometry,Replay,exhausted
from .foundation_study_verify_core import Checker

def independent_scores(rows,meta,m):
    pairs=defaultdict(list)
    for r in rows:
        mm=meta[r['case']]
        if mm['family']=='paired':pairs[mm['base'],mm['pose']].append(r)
    saved={(d['base'],d['pose']):d for d in m['details']}
    for key,rs in pairs.items():
        rs=sorted(rs,key=lambda r:meta[r['case']]['side']);raw=[bytes.fromhex(r['mask']) for r in rs];paths=[meta[r['case']]['path'] for r in rs];goals={p[-1] for p in paths}
        at=lambda i,p:int(bool(raw[i][p//8] & (1<<(p%8))))
        private=[[p for p in paths[i] if p not in paths[1-i] and p not in goals] for i in (0,1)]
        normal=all(r['status']=='emitted' for r in rs)
        contrast=sum(sum(at(i,p)-at(1-i,p) for p in private[i])/len(private[i]) for i in (0,1))/2 if normal and all(private) else 0.
        f1=min(2*sum(at(i,p) for p in paths[i])/(sum(at(i,p) for p in range(361))+len(paths[i])) for i in (0,1));score=max(0.,contrast)*f1 if normal else 0.
        assert abs(score-saved[key]['score'])<1e-12
        assert saved[key]['spill']==sum(at(i,p) for i in (0,1) for p in range(361) if p not in paths[i])
        assert saved[key]['missing']==sum(1-at(i,p) for i in (0,1) for p in paths[i])

def audit():
    t=time.perf_counter();reg=check_freeze();prior=prior_check();assert prior==2644;pool=read_compressed(OUT/'pool.json.gz');assert make_pool()==pool
    previous=exclusions();datasets={};geometry_counts={}
    stages=[(FIXTURES,FIXTURE_SEED,'fixture'),(OUT/'software_fixtures',FIXTURE_SEED+1,'confirmation'),(OUT/'discovery',SEED,'discovery'),(OUT/'validation',seed_for(SEED,'validation',0,0),'validation'),(OUT/'confirmation',seed_for(SEED,'confirmation',0,0),'confirmation')]
    for path,seed,scope in stages:
        d=create(seed,scope,previous);cases,contexts,meta=load(path)
        assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz');assert canonical(d.contexts)==contexts and canonical(d.metadata)==meta
        name='software' if path.name=='software_fixtures' else scope;datasets[name]=(cases,meta);geometry_counts[name]=geometry(cases,meta)
        previous+=read_compressed(path/'mazes.json.gz');whole=len(d.layouts)
    del previous,d
    profile=json.loads((FIXTURES/'profile.json').read_text());n=profile['walks_per_root_block'];choices=read_compressed(OUT/'discovery_choices.json.gz');sel=read_compressed(OUT/'selections.json.gz');panel=read_compressed(OUT/'final_panel.json.gz')
    valid={raw['id'] for raw in pool['roots'].values()}|{pool['control']}
    for g in choices.values():
        for a in ARMS:valid.update(g[a]['nominees'])
    final_ids={raw['id'] for raw in pool['roots'].values()}|{pool['control']}
    for g in sel.values():final_ids.update(g[a]['best'] for a in ARMS)
    assert panel==dict(mapping=identities_for_models(pool,final_ids),ids=sorted(final_ids),selections=sel)
    replay=Replay();stage_counts={};metrics={};seconds={}
    for stage,path,ids in [('fixture',FIXTURES,eligible(pool,16)),('discovery',OUT/'discovery',eligible(pool,n)),('validation',OUT/'validation',valid),('confirmation',OUT/'confirmation',final_ids)]:
        cases,meta=datasets[stage];checker=Checker(cases);query=[c for c,m in meta.items() if m['pose']==0 and not m['stress']] if stage=='fixture' else list(cases);mapping=identities_for_models(pool,ids);assert mapping==read_compressed(path/'mapping.json.gz');it=iter(lines(path/'responses.jsonl.gz'));saved=read_compressed(path/'metrics.json.gz');rates=read_compressed(path/'rates.json.gz');mm={};before=replay.calls;work=replay.work;seconds[stage]=0.
        for pid,identity in mapping.items():
            e=next(it);rr=replay.evaluation(e,Individual.load(pool['entries'][identity]['item']),cases,query,checker,stage,pid,-1);m=summary(rr,meta);assert m==saved[pid];independent_scores(rr,meta,m);mm[pid]=m;seconds[stage]+=e['seconds'];assert rates[pid]==e['seconds']/len(query)
        exhausted(it);assert mm==saved;metrics[stage]=mm;stage_counts[stage]=dict(calls=replay.calls-before,work=replay.work-work,models=len(mapping));print(json.dumps(dict(audit_stage=stage,replays=replay.calls)),flush=True)
    for key,g in pool['groups'].items():
        for arm in ARMS:
            assert choose(g[arm][:n],pool,metrics['discovery'])==choices[key][arm]
            assert choose(choices[key][arm]['nominees'],pool,metrics['validation'])==sel[key][arm]
    rates=read_compressed(FIXTURES/'rates.json.gz');group_rates={f'{k}/{a}':sum(rates[pool['aliases'][i]] for i in ids)/len(ids) for k,g in pool['groups'].items() for a,ids in g.items()};assert group_rates==profile['group_rates'];rate=2*max(group_rates.values());plans={k:(6+60*k)*768+126*768+66*5184 for k in (16,8,4)}
    assert n==next(k for k,calls in plans.items() if rate*calls<600);assert profile['planning_rate']==rate and profile['planned_calls_upper']==plans[n]
    run=json.loads((OUT/'selection_execution.json').read_text());final=json.loads((OUT/'confirmation/execution.json').read_text())
    assert final['complete'] and run['complete'] and final['initial_budget']==run['budget']
    assert profile['budget']['calls']==stage_counts['fixture']['calls'] and profile['budget']['work']==stage_counts['fixture']['work'];assert abs(profile['budget']['seconds']-seconds['fixture'])<1e-8
    assert run['budget']['calls']==sum(stage_counts[s]['calls'] for s in ('discovery','validation'))
    assert final['budget']['calls']==sum(stage_counts[s]['calls'] for s in ('discovery','validation','confirmation'));assert final['budget']['work']==sum(stage_counts[s]['work'] for s in ('discovery','validation','confirmation'));assert abs(final['budget']['seconds']-sum(seconds[s] for s in ('discovery','validation','confirmation')))<1e-8;assert final['budget']['seconds']<720
    cases,meta=datasets['confirmation'];checker=Checker(cases);it=iter(lines(OUT/'confirmation/baselines.jsonl.gz'));bc=0
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        for o in cases.values():
            e=next(it);m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert e==dict(model=name,row=r);checker.row(r);assert r['optimal'] or r['no_path'];bc+=1
    exhausted(it);assert bc==final['baseline_calls'];control=metrics['confirmation'][pool['aliases'][pool['control']]];assert control['optimal']==3456 and control['no_path']==1728
    assert analysis_packet()==read_compressed(OUT/'analysis.json.gz')
    # Frozen artifacts must be committed before their dependent data generation.
    for stage,files in [('discovery',[FIXTURES/'profile.json']),('confirmation',[OUT/'final_panel.json.gz',OUT/'selections.json.gz'])]:
        g=json.loads((OUT/stage/'generation.json').read_text())
        for f in files:assert subprocess.check_output(['git','show',f'{g["revision"]}:{f.relative_to(ROOT)}'])==f.read_bytes()
    write_json(OUT/'audit.json',dict(passed=True,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,prior_hashes=prior,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),candidate_replays=replay.calls,independent_rasters=replay.rasters+bc,baseline_replays=bc,walks=240,mutation_events=len(pool['events']),random_draws=240,whole_layouts=whole,stages=stage_counts,geometry=geometry_counts));print((OUT/'audit.json').read_text(),flush=True)
