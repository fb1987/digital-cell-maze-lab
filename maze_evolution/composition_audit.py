"""V12S full ancestry/selection replay, independent grading and registered inference sample."""
from .composition_study import *
from .shared_prefix_audit import geometry as structured_geometry,exhausted
from .foundation_study_verify_core import Checker

def geometry(cases,meta):
    ids=[c for c,m in meta.items() if not m['family'].startswith('ordinary_')]
    result=structured_geometry({c:cases[c] for c in ids},{c:meta[c] for c in ids})
    ordinary=[c for c in cases if c not in set(ids)]
    for c in ordinary:
        o=cases[c];m=meta[c];assert bool(o.path)==(m['family']!='ordinary_disconnected')
        assert o.path==m['path'] and o.maze.w==o.maze.h==9
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
            if selected or row['valid'] or row['no_path']:
                checker.row(row);self.graded+=1
            self.calls+=1;self.training_rows+=int(stage=='train');work+=row['reads']+row['dispatches']+row['exposure_checks']
        assert work==e['work'];self.work+=work;self.seconds+=e['seconds'];return e['rows']

def assert_corpus(d,path):
    cases,contexts,meta=load(path)
    assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz')
    assert canonical(d.contexts)==contexts and canonical(d.metadata)==meta
    return cases,meta,geometry(cases,meta)

def audit():
    t=time.perf_counter();reg=check_freeze();prior=prior_check();assert prior==2913
    pools=read_compressed(OUT/'pools.json.gz');assert pools==make_pools();previous=exclusions();d=create(FIXTURE_SEED,'fixture',previous)
    fc,fm,fg=assert_corpus(d,FIXTURES);previous+=manifest(d.cache.values());del d
    # Rejected pre-registration construction has no additional layouts beyond
    # the corrected fixture. Its partial grammar was saved before any calls.
    rejected=read_compressed(OUT/'preparation_rejected/mazes.json.gz')
    assert {r['cells_hex'] for r in rejected}<={r['cells_hex'] for r in read_compressed(FIXTURES/'mazes.json.gz')}
    d=schedule_fixture(previous);assert_corpus(d,OUT/'schedule_fixtures');previous+=manifest(d.cache.values());del d
    profile=json.loads((FIXTURES/'profile.json').read_text());execution=json.loads((OUT/'search_execution.json').read_text());assert profile['passed'] and execution['complete']
    replay=Replay();checker=Checker(fc);it=iter(lines(FIXTURES/'responses.jsonl.gz'));ids=[c for c,m in fm.items() if m['family'] in ('paired','corridor','disconnected') and m['index']<2 and m['pose']==0 and m['prefix'] in (0,1)];rates={}
    for key,p in pools.items():
        before=replay.seconds
        for raw in p['items']:replay.evaluation(next(it),Individual.load(raw),fc,ids,checker,'profile',key,-1)
        rates[key]=(replay.seconds-before)/(96*len(ids))
        assert abs(rates[key]-profile['pool_rates'][key])<1e-12
    known=Individual.load(read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']['intact'])
    rr=replay.evaluation(next(it),known,fc,list(fc),checker,'profile','intact',-1);assert all(r['optimal'] or r['no_path'] for r in rr);exhausted(it)
    assert replay.calls==profile['budget']['calls'] and replay.work==profile['budget']['work'];profile_calls=replay.calls;profile_work=replay.work;profile_seconds=replay.seconds
    assert abs(profile['planning_rate']-2*max(rates.values()))<1e-12
    d=create(seed_for(SEED,'validation',0,0),'validation',previous);vc,vm,vg=assert_corpus(d,OUT/'validation');previous+=manifest(d.cache.values());del d
    checker=Checker(vc);it=iter(lines(OUT/'initial.jsonl.gz'));states={};frozen={}
    for key,pool in pools.items():
        aa={}
        for raw in pool['items']:
            i=Individual.load(raw);rr=replay.evaluation(next(it),i,vc,list(vc),checker,'initial',key,0);update_archives(aa,i,summary(rr,vm),0)
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
                    vr=replay.evaluation(next(it),i,vc,list(vc),checker,'validation',key,g);update_archives(aa,i,summary(vr,vm),g)
            new,event=reproduce(state,rank,aa);assert event==next(evs),(key,g);states[key]=new
            counts=by.setdefault(key,dict(births=0,mutations=0,attempts=0,splices=0,complementary_splices=0))
            for birth in event['births']:
                counts['births']+=1;counts['mutations']+=int(birth['mutation'] is not None);counts['attempts']+=int(birth['mating'] is not None);counts['splices']+=int(birth['crossover'] is not None)
                if birth['crossover'] is not None:
                    assert len(birth['parents'])==2 and birth['item']['parent']==birth['parents'][0]
                    counts['complementary_splices']+=int(any(x>0 for x in birth['mating']['gains']))
        exhausted(it);previous+=manifest(train.cache.values());clear_batch(train)
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
    exhausted(it);assert metrics==read_compressed(OUT/'confirmation/metrics.json.gz');final=json.loads((OUT/'confirmation/execution.json').read_text());assert final['complete'] and final['initial_budget']==execution['budget']
    assert replay.calls-profile_calls==final['budget']['calls'] and replay.work-profile_work==final['budget']['work'];assert abs(replay.seconds-profile_seconds-final['budget']['seconds'])<1e-5
    assert final['budget']['seconds']<5400 and final['budget']['calls']<40000000 and final['budget']['work']<40000000000000
    it=iter(lines(OUT/'confirmation/baselines.jsonl.gz'));bc=0
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        for o in cc.values():
            e=next(it);m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert e==dict(model=name,row=r);checker.row(r);assert r['optimal'] or r['no_path'];bc+=1
    exhausted(it);assert bc==final['baseline_calls'];assert analysis_packet()==read_compressed(OUT/'analysis.json.gz')
    for path,files in [(OUT/'validation',[FIXTURES/'profile.json']),(OUT/'confirmation',[OUT/'choices.json.gz',OUT/'next_states.json.gz'])]:
        rev=json.loads((path/'generation.json').read_text())['revision']
        for f in files:assert subprocess.check_output(['git','show',f'{rev}:{f.relative_to(ROOT)}'])==f.read_bytes()
    write_json(OUT/'audit.json',dict(passed=True,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        prior_hashes=prior,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),logged_candidate_calls=replay.calls,
        exact_candidate_replays=replay.exact,independently_graded_candidate_rasters=replay.graded,baseline_replays=bc,
        training_sampling='all claimed valid/no-path independently graded; deterministic1/256 exact replay plus grading of all other training outputs; all nontraining outputs exact replay and grading',
        generations=execution['generations'],populations=len(states),reproduction=by,whole_layouts=len(d.layouts),geometry=dict(fixture=fg,validation=vg,confirmation=cg)))
    print((OUT/'audit.json').read_text(),flush=True)
