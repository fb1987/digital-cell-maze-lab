"""V12Z ancestry/selection replay, independent raster grading and fixed inference sample."""
from .family_evolution_study import *
from .shared_prefix_audit import geometry as structured_geometry,exhausted
from .foundation_study_verify_core import Checker

def geometry(cases,meta):
    ids=[c for c,m in meta.items() if not m['family'].startswith('ordinary_')]
    result=structured_geometry({c:cases[c] for c in ids},{c:meta[c] for c in ids})
    structured=set(ids);ordinary=[c for c in cases if c not in structured]
    for c in ordinary:
        o=cases[c];m=meta[c];assert bool(o.path)==(m['family']!='ordinary_disconnected')
        assert o.path==m['path'] and o.maze.w==o.maze.h==9
    from cellular_maze_lab import neighbors
    for o in cases.values():
        if not o.path:
            m=o.maze
            assert any(m.cells[q] for q in neighbors(m.start,m.w,m.h))
            assert any(m.cells[q] for q in neighbors(m.goal,m.w,m.h))
    result['ordinary_inputs']=len(ordinary)
    return result

def sample(key,g,identity,cid):return int(digest([key,g,identity,cid])[:8],16)%256==0

class Replay:
    def __init__(self):self.calls=0;self.work=0;self.seconds=0.;self.exact=0;self.graded=0;self.training_rows=0
    def evaluation(self,e,i,cases,ids,checker,stage,key,g):
        assert (e['stage'],e['key'],e['generation'],e['id'])==(stage,key,g,i.identity)
        assert [r['case'] for r in e['rows']]==ids
        org=organism(physical(i,'neutral','local')[1]);work=0
        for row in e['rows']:
            o=cases[row['case']];m=o.maze;selected=stage!='train' or sample(key,g,i.identity,row['case'])
            if selected:
                r=org.react(m.cells,m.w,m.h,m.start,m.goal);assert record(r,o)==row,(key,i.identity,row['case']);self.exact+=1
            checker.row(row);self.graded+=1
            self.calls+=1;self.training_rows+=int(stage=='train');work+=row['reads']+row['dispatches']+row['exposure_checks']
        assert work==e['work'];self.work+=work;self.seconds+=e['seconds'];return e['rows']

def assert_corpus(d,path):
    cases,contexts,meta=load(path)
    assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz')
    assert canonical(d.contexts)==contexts and canonical(d.metadata)==meta
    return cases,meta,geometry(cases,meta)

def audit():
    t=time.perf_counter();reg=check_freeze();prior=prior_check();assert prior==6923
    pools=read_compressed(OUT/'pools.json.gz');assert pools==make_pools();previous=exclusions();d=create(FIXTURE_SEED,'fixture',previous)
    fc,fm,fg=assert_corpus(d,FIXTURES);previous.update(d.layouts);del d
    d=schedule_fixture(previous);assert_corpus(d,OUT/'schedule_fixtures');previous.update(d.layouts);del d
    sf=software_fixture(exclusions());assert_corpus(sf,OUT/'software_fixtures');previous.update(sf.layouts)
    profile=json.loads((FIXTURES/'profile.json').read_text());execution=json.loads((OUT/'search_execution.json').read_text());assert profile['passed'] and execution['complete']
    replay=Replay();checker=Checker(fc);it=iter(lines(FIXTURES/'responses.jsonl.gz'));ids=profile_ids(fm);rates={};birthlog=iter(lines(FIXTURES/'reproduction.jsonl.gz'))
    for key,p in pools.items():
        before=replay.seconds
        pop=[Individual.load(raw) for raw in p['items']]
        rr={i.identity:replay.evaluation(next(it),i,fc,ids,checker,'profile',key,-1) for i in pop};rank=ranked(pop,rr,fm)
        for arm in ARMS:
            new,event=reproduce(init_state(key+'/'+arm,p),rank,{})
            assert next(birthlog)==dict(event=event,next_state_digest=digest(new))
        rates[key]=(replay.seconds-before)/(96*len(ids))
        assert abs(rates[key]-profile['pool_rates'][key])<1e-12
    exhausted(birthlog)
    preflight_audit=verify_preflight(pools)
    known=Individual.load(read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']['intact'])
    rr=replay.evaluation(next(it),known,fc,list(fc),checker,'profile','intact',-1);assert all(r['optimal'] or r['no_path'] for r in rr);exhausted(it)
    assert replay.calls==profile['budget']['calls'] and replay.work==profile['budget']['work'];profile_calls=replay.calls;profile_work=replay.work;profile_seconds=replay.seconds
    assert abs(profile['planning_rate']-2*max(rates.values()))<1e-12
    d=create(seed_for(SEED,'validation',0,0),'validation',previous);vc,vm,vg=assert_corpus(d,OUT/'validation');previous.update(d.layouts);del d
    checker=Checker(vc);it=iter(lines(OUT/'initial.jsonl.gz'));states={};frozen={}
    for key,pool in pools.items():
        aa={}
        for raw in pool['items']:
            i=Individual.load(raw);rr=replay.evaluation(next(it),i,vc,list(vc),checker,'initial',key,0);update_archives(aa,i,summary(rr,vm),0,dict(family=pool['families'][i.identity],gene_ids=pool['gene_ids'][i.identity]))
        frozen[key]=deepcopy(aa)
        for arm in ARMS:states[key+'/'+arm]=init_state(key+'/'+arm,pool,aa)
    exhausted(it);assert frozen==read_compressed(OUT/'frozen.json.gz');assert states==read_compressed(OUT/'initial_states.json.gz')
    train=AccessData(seed_for(SEED,'train',0,0),previous);evs=iter(lines(OUT/'reproduction.jsonl.gz'));birth_count=mutations=splices=attempts=0;by={}
    for g in range(execution['generations']):
        ids=training_batch(train,g);path=OUT/'train'/f'g{g:04d}';tc,tm,tg=assert_corpus(train,path);tchecker=Checker(tc);it=iter(lines(path/'responses.jsonl.gz'))
        for key,state in states.items():
            pop=[Individual.load(i) for i in state['population']];rr={i.identity:replay.evaluation(next(it),i,tc,ids,tchecker,'train',key,g) for i in pop};rank=ranked(pop,rr,tm);aa=deepcopy(state['archives'])
            if (g+1)%VALIDATE_EVERY==0:
                for i in nominees(rank):
                    vr=replay.evaluation(next(it),i,vc,list(vc),checker,'validation',key,g);update_archives(aa,i,summary(vr,vm),g,lineage(state,i))
            new,event=reproduce(state,rank,aa);assert event==next(evs),(key,g);states[key]=new
            counts=by.setdefault(key,dict(births=0,mutations=0,attempts=0,splices=0,complementary_splices=0))
            for birth in event['births']:
                counts['births']+=1;counts['mutations']+=int(birth['mutation'] is not None);counts['attempts']+=0;counts['splices']+=0
        exhausted(it);previous.update(train.layouts);clear_batch(train)
        if (g+1)%32==0:assert states==read_compressed(OUT/f'checkpoints/g{g+1}.json.gz')
        if (g+1)%16==0:print(json.dumps(dict(audit_generation=g+1,logged_calls=replay.calls,exact_replays=replay.exact)),flush=True)
    exhausted(evs);assert states==read_compressed(OUT/'next_states.json.gz')==read_compressed(OUT/'latest_states.json.gz')
    assert replay.calls-profile_calls==execution['budget']['calls'] and replay.work-profile_work==execution['budget']['work']
    assert abs(replay.seconds-profile_seconds-execution['budget']['seconds'])<1e-5
    choices=choices_packet(states,frozen);assert choices==read_compressed(OUT/'choices.json.gz')
    d=create(seed_for(SEED,'confirmation',0,0),'confirmation',previous);cc,cm,cg=assert_corpus(d,OUT/'confirmation');checker=Checker(cc);it=iter(lines(OUT/'confirmation/responses.jsonl.gz'));metrics={}
    for pid in choices['models']:
        i=next(Individual.load(choices['items'][a]) for a,p in choices['aliases'].items() if p==pid)
        rr=replay.evaluation(next(it),i,cc,list(cc),checker,'confirmation',pid,-1);metrics[pid]=summary(rr,cm)
    exhausted(it);assert metrics==read_compressed(OUT/'confirmation/metrics.json.gz');final=json.loads((OUT/'confirmation/execution.json').read_text());assert final['complete'] and final['initial_budget']['calls']==0
    assert replay.calls-profile_calls-execution['budget']['calls']==final['budget']['calls'] and replay.work-profile_work-execution['budget']['work']==final['budget']['work'];assert abs(replay.seconds-profile_seconds-execution['budget']['seconds']-final['budget']['seconds'])<1e-5
    assert final['budget']['seconds']<600 and execution['budget']['seconds']<4500 and execution['wall_seconds']<4500 and final['budget']['calls']<40000000 and final['budget']['work']<40000000000000
    it=iter(lines(OUT/'confirmation/baselines.jsonl.gz'));bc=0
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        for o in cc.values():
            e=next(it);m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert e==dict(model=name,row=r);checker.row(r);assert r['optimal'] or r['no_path'];bc+=1
    exhausted(it);assert bc==final['baseline_calls'];assert analysis_packet()==read_compressed(OUT/'analysis.json.gz')
    for path,files in [(OUT/'validation',[FIXTURES/'profile.json']),(OUT/'confirmation',[OUT/'choices.json.gz',OUT/'next_states.json.gz'])]:
        rev=json.loads((path/'generation.json').read_text())['revision']
        for f in files:assert subprocess.check_output(['git','show',f'{rev}:{f.relative_to(ROOT)}'])==f.read_bytes()
    write_json(OUT/'audit.json',dict(passed=True,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        preflight_replay=preflight_audit,prior_hashes=prior,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),logged_candidate_calls=replay.calls,
        exact_candidate_replays=replay.exact,independently_graded_candidate_rasters=replay.graded,baseline_replays=bc,
        training_sampling='all rasters independently graded; deterministic1/256 exact inference replay of training; all nontraining outputs exact replay' ,
        generations=execution['generations'],populations=len(states),reproduction=by,whole_layouts=len(d.layouts),geometry=dict(fixture=fg,validation=vg,confirmation=cg)))
    print((OUT/'audit.json').read_text(),flush=True)


def preflight():
    """Discarded three-round trajectory, common fixtures, exact native/RNG replay."""
    assert not (OUT/'preflight.json').exists()
    t=time.perf_counter();sf=software_fixture(exclusions());sf.save(OUT/'software_fixtures');geometry(sf.cache,sf.metadata)
    cases,_,meta=load(OUT/'schedule_fixtures');geometry(cases,meta)
    fc,_,fm=load(FIXTURES);geometry(fc,fm)
    pools=read_compressed(OUT/'pools.json.gz');states={key+'/'+a:init_state(key+'/'+a,p) for key,p in pools.items() for a in ARMS}
    b=Budget(180-json.loads((FIXTURES/'profile.json').read_text())['budget']['seconds']);w=warm(cases);checker=Checker(cases);calls=mutations=0
    with gzip.open(OUT/'preflight_responses.jsonl.gz','wt',compresslevel=1) as log,gzip.open(OUT/'preflight_births.jsonl.gz','wt',compresslevel=1) as births:
        for g in range(3):
            ids=[c for c,m in meta.items() if m['audit_generation']==g];assert len(ids)==12
            for key,s in states.items():
                pop=[Individual.load(r) for r in s['population']];rr={i.identity:assay(i,cases,ids,b,log,'preflight',key,g) for i in pop};rank=ranked(pop,rr,meta)
                for i in pop:
                    org=organism(physical(i,'neutral','local')[1])
                    for row in rr[i.identity]:
                        o=cases[row['case']];m=o.maze;r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal))
                        assert record(r,o)==row;checker.row(row);calls+=1
                new,event=reproduce(s,rank,{})
                assert reproduce(s,rank,{})==(new,event)
                for birth in event['births']:
                    if birth['mutation'] is not None:
                        parent=next(i for i in pop if i.identity==birth['parents'][0])
                        assert replay_mutation(parent.genome.program,birth['mutation'],256)==Individual.load(birth['item']).genome.program;mutations+=1
                logrow(births,event);states[key]=new
    compressed_json(OUT/'preflight_states.json.gz',states)
    write_json(OUT/'preflight.json',dict(passed=True,generations=3,conditions=24,exact_candidate_replays=calls,independent_raster_grades=calls,mutation_replays=mutations,budget=b.save(),warmup=w,wall_seconds=time.perf_counter()-t,discarded=True,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print((OUT/'preflight.json').read_text(),flush=True)


def verify_preflight(pools):
    cases,_,meta=load(OUT/'schedule_fixtures');checker=Checker(cases);r=Replay()
    states={k+'/'+a:init_state(k+'/'+a,p) for k,p in pools.items() for a in ARMS}
    it=iter(lines(OUT/'preflight_responses.jsonl.gz'));births=iter(lines(OUT/'preflight_births.jsonl.gz'))
    for g in range(3):
        ids=[c for c,m in meta.items() if m['audit_generation']==g]
        for key,s in states.items():
            pop=[Individual.load(x) for x in s['population']]
            rr={i.identity:r.evaluation(next(it),i,cases,ids,checker,'preflight',key,g) for i in pop}
            new,event=reproduce(s,ranked(pop,rr,meta),{});assert next(births)==event;states[key]=new
    exhausted(it);exhausted(births);assert states==read_compressed(OUT/'preflight_states.json.gz')
    p=json.loads((OUT/'preflight.json').read_text());assert p['passed'] and p['budget']['calls']==2*r.calls and p['budget']['work']==2*r.work
    assert p['budget']['seconds']+json.loads((FIXTURES/'profile.json').read_text())['budget']['seconds']<180
    return dict(exact_candidate_replays=r.exact,independent_grades=r.graded,states=24)
