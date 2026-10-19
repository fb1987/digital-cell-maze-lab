"""Independent raster grading plus complete Q inference/RNG/birth replay."""
import gzip,json,time,resource
from collections import defaultdict
from .shared_prefix_study import *
from .foundation_study_verify_core import Checker
from .foundation_data import layout_hash
from cellular_maze_lab import neighbors


def geometry(cases,meta):
    paired=defaultdict(list);layout_groups=defaultdict(set)
    for cid,o in cases.items():
        m=o.maze;v=meta[cid];assert bool(o.path)==(v['family']!='disconnected')
        if o.path:
            assert o.path==v['path'] and len(o.path)==len(set(o.path))
            assert all(b in neighbors(a,m.w,m.h) for a,b in zip(o.path,o.path[1:]))
        if v['family']=='paired':
            paired[v['base'],v['pose']].append(cid)
            layout_groups[v['template'],v['graph'],v['pose'],v['side']].add((m.cells,m.goal))
            alt=v['alternative']
            if v['graph']=='cycle':
                assert len(alt)>len(o.path) and alt[0]==m.start and alt[-1]==m.goal and len(alt)==len(set(alt))
                assert all(b in neighbors(a,m.w,m.h) and m.cells[a] and m.cells[b] for a,b in zip(alt,alt[1:]))
    assert all(len(v)==1 for v in layout_groups.values())
    for ids in paired.values():
        a,b=[cases[c].maze for c in ids];assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
    return dict(inputs=len(cases),pairs=len(paired),whole_layouts=len({layout_hash(o.maze) for o in cases.values()}),contexts=len({m['template'] for m in meta.values()}))

class Replay:
    def __init__(self):self.calls=0;self.rasters=0;self.work=0
    def evaluation(self,e,item,cases,ids,checker,stage,key,generation):
        assert (e['stage'],e['key'],e['generation'],e['id'])==(stage,key,generation,item.identity)
        assert [r['case'] for r in e['rows']]==ids
        org=organism(physical(item,'neutral','local')[1]);work=0
        for row in e['rows']:
            o=cases[row['case']];m=o.maze;r=org.react(m.cells,m.w,m.h,m.start,m.goal)
            assert record(r,o)==row,(key,item.identity,row['case']);checker.row(row);self.calls+=1;self.rasters+=1;work+=r.spatial_reads+r.dispatches+r.exposure_checks
        assert work==e['work'];self.work+=work
        return e['rows']

def exhausted(it):
    try:next(it)
    except StopIteration:return
    raise AssertionError('Unexpected trailing records')

def audit():
    t=time.perf_counter();reg=check_freeze();prior=prior_check();assert prior==2384
    pools=read_compressed(OUT/'pools.json.gz');assert make_pools()==pools
    ex=exclusions();assert software_fixture_manifest()==software_fixtures()
    previous=ex;geometries={};datasets={};profile=json.loads((FIXTURES/'profile.json').read_text());execution=json.loads((OUT/'search_execution.json').read_text())
    for path,seed,split,ng in [(FIXTURES,FIXTURE_SEED,'fixture',0),(OUT/'validation',seed_for(SEED,'validation',0,0),'validation',0),(OUT/'train',seed_for(SEED,'train',0,0),'train',profile['generations']),(OUT/'confirmation',seed_for(SEED,'confirmation',0,0),'confirmation',0)]:
        fresh=create(seed,split,previous,ng);cases,contexts,meta=load(path)
        assert canonical(manifest(fresh.cache.values()))==read_compressed(path/'mazes.json.gz')
        assert fresh.metadata==meta and fresh.contexts==contexts
        geometries[split]=geometry(cases,meta);datasets[split]=(cases,meta);previous+=read_compressed(path/'mazes.json.gz')
        if split=='fixture':previous+=software_fixtures()
        del fresh
    replay=Replay();fc,fm=datasets['fixture'];checker=Checker(fc);it=iter(lines(FIXTURES/'responses.jsonl.gz'));ids=[c for c,m in fm.items() if m['pose']==0]
    for key,pool in pools.items():
        for raw in pool['items']:replay.evaluation(next(it),Individual.load(raw),fc,ids,checker,'profile',key,-1)
    exhausted(it);assert replay.calls==profile['budget']['calls'] and replay.work==profile['budget']['work'];profile_calls=replay.calls;profile_work=replay.work
    vc,vm=datasets['validation'];checker=Checker(vc);it=iter(lines(OUT/'initial.jsonl.gz'));states={};frozen={}
    for key,pool in pools.items():
        aa={}
        for raw in pool['items']:
            i=Individual.load(raw);rows=replay.evaluation(next(it),i,vc,list(vc),checker,'initial',key,0);update_archives(aa,i,summary(rows,vm),0)
        frozen[key]=deepcopy(aa)
        for arm in ARMS:states[key+'/'+arm]=init_state(key+'/'+arm,pool,aa)
    exhausted(it);assert frozen==read_compressed(OUT/'frozen.json.gz') and states==read_compressed(OUT/'initial_states.json.gz')
    tc,tm=datasets['train'];tchecker=Checker(tc);it=iter(lines(OUT/'search_responses.jsonl.gz'));evs=iter(lines(OUT/'reproduction.jsonl.gz'));mutations=birth_count=0
    for g in range(execution['generations']):
        for key,state in states.items():
            pop=[Individual.load(i) for i in state['population']];ids=training_ids(tm,g,state['arm']);rows={i.identity:replay.evaluation(next(it),i,tc,ids,tchecker,'train',key,g) for i in pop};rank=ranked(pop,rows,tm);aa=deepcopy(state['archives'])
            if (g+1)%8==0:
                for i in nominees(rank):
                    rs=replay.evaluation(next(it),i,vc,list(vc),checker,'validation',key,g);update_archives(aa,i,summary(rs,vm),g)
            new,event=reproduce(state,rank,aa);saved=next(evs);assert event==saved,(key,g);states[key]=new
            mutations+=sum(v['events'] is not None for v in event['births']);birth_count+=len(event['births'])
        if (g+1)%8==0:assert states==read_compressed(OUT/f'checkpoints/g{g+1}.json.gz')
        if (g+1)%8==0:print(json.dumps(dict(audit_generation=g+1,replays=replay.calls)),flush=True)
    exhausted(it);exhausted(evs);assert states==read_compressed(OUT/'next_states.json.gz')==read_compressed(OUT/'latest_states.json.gz')
    assert replay.calls-profile_calls==execution['budget']['calls'];assert replay.work-profile_work==execution['budget']['work']
    choices=read_compressed(OUT/'choices.json.gz')
    # Rebuild choice aliases without writing any experiment artifact.
    expected={}
    for key,s in states.items():
        for name,a in s['archives'].items():expected[key+'/'+name]=a['item']
    for key,aa in frozen.items():
        for name,a in aa.items():expected[key+'/frozen/'+name]=a['item']
    panel=read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']
    for label in ('route/d9','route/d16','reach1/d16','reach2/d16','resample','intact'):expected['anchor/'+label]=panel[label]
    assert expected==choices['items'];models={};aliases={}
    for alias,raw in expected.items():pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[alias]=pid
    assert models==choices['models'] and aliases==choices['aliases']
    cc,cm=datasets['confirmation'];checker=Checker(cc);it=iter(lines(OUT/'confirmation/responses.jsonl.gz'));metrics={}
    for pid in models:
        i=next(Individual.load(expected[a]) for a,p in aliases.items() if p==pid)
        rows=replay.evaluation(next(it),i,cc,list(cc),checker,'confirmation',pid,-1);metrics[pid]=summary(rows,cm)
    exhausted(it);assert metrics==read_compressed(OUT/'confirmation/metrics.json.gz');final=json.loads((OUT/'confirmation/execution.json').read_text())
    assert replay.calls-profile_calls==final['budget']['calls'];assert replay.work-profile_work==final['budget']['work'];assert final['budget']['seconds']<=720
    intact=metrics[aliases['anchor/intact']];assert intact['optimal']==2688 and intact['no_path']==1344
    bc=0;it=iter(lines(OUT/'confirmation/baselines.jsonl.gz'))
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        for o in cc.values():
            row=next(it);m=o.maze;expected_row=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert row==dict(model=name,row=expected_row);checker.row(expected_row);assert expected_row['optimal'] or expected_row['no_path'];bc+=1
    exhausted(it);assert bc==final['baseline_calls'];assert analysis_packet()==read_compressed(OUT/'analysis.json.gz')
    write_json(OUT/'audit.json',dict(passed=True,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,prior_hash_entries=prior,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),candidate_replays=replay.calls,independent_rasters=replay.rasters+bc,baseline_replays=bc,mutations=mutations,births=birth_count,generations=execution['generations'],geometry=geometries,populations=len(states),choice_aliases=len(aliases),whole_layouts=__import__('maze_evolution.foundation_data',fromlist=['FoundationData']).FoundationData(0,previous).previous_count))
    print((OUT/'audit.json').read_text(),flush=True)
