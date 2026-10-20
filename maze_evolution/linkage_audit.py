"""V12X full reproduction/RNG replay, all raster grading and deduplicated native replay."""
from functools import lru_cache
from collections import Counter
from .linkage_study import *
from .linkage_analysis import compute
from .foundation_study_verify_core import Checker
from .linkage_operator import LENGTHS

@lru_cache(maxsize=1024)
def independent_groups(program):
    # Independently walk backwards from each operand use; stop only at an
    # unconditional definition. This does not use the operator's forward map.
    from .composition_operator import register_reads
    result=[]
    for store,row in enumerate(program):
        if row[0]!=13:continue
        pending=[store];seen=set()
        while pending:
            instruction=pending.pop()
            if instruction in seen:continue
            seen.add(instruction)
            for reg in register_reads(program[instruction]):
                for j in range(instruction-1,-1,-1):
                    prior=program[j]
                    if prior[0]!=13 and prior[1]==reg:
                        pending.append(j)
                        if prior[6]==64:break
        result.append(tuple(sorted(seen)))
    return tuple(result)

def independent_births(state,event):
    if event.get('frozen'):return Counter()
    registry={r['id']:Individual.load(r) for r in state['population']};count=Counter()
    for birth in event['births']:
        item=Individual.load(birth['item']);parent_id=birth['parents'][0] if birth['parents'] else None
        if parent_id is None:
            assert birth['mutation'] is None and birth['gene_ids']==[item.identity+f'/gene{k}' for k in range(len(item.genome.genes))];count['random_births']+=1;continue
        parent=registry[parent_id];program=parent.genome.program;ids=list(state['gene_ids'][parent_id]);cross=birth['crossover'];donor_changes={}
        if cross and cross['accepted']:
            donor=registry[birth['parents'][1]];di=state['gene_ids'][donor.identity];a=rows(program);b=rows(donor.genome.program);x,y=cross['recipient_interval'];u,v=cross['donor_interval']
            assert y-x==v-u==cross['length'] and y-x in LENGTHS
            assert ids[x-1]==di[u-1] and ids[y]==di[v]
            groups=[{ids[j] for j in group} for group in independent_groups(a)]+[{di[j] for j in group} for group in independent_groups(b)]
            segment=set(ids[x:y])|set(di[u:v]);closed=all(not group&segment or group<=segment for group in groups)
            assert cross['dependency_closed']==closed
            if state['arm']=='linked':assert closed
            assert cross['changed_instructions']==sum(old!=new for old,new in zip(a[x:y],b[u:v]))
            donor_changes={identity:new for old,new,identity in zip(a[x:y],b[u:v],di[u:v]) if old!=new}
            from .regulatory import Gene
            from .growth import Genome as Program
            program=Program(tuple(Gene(*r) for r in a[:x]+b[u:v]+a[y:]));ids=ids[:x]+di[u:v]+ids[y:]
            assert program.digest==cross['child_digest'];count['independent_splices']+=1
        else:assert len(birth['parents'])==1
        program=replay_mutation(program,birth['mutation'],256);assert program==item.genome.program;count['mutations']+=1
        for k,e in enumerate(birth['mutation']):
            i=e['index'];kind=e['kind']
            if kind=='insert':ids[i:i]=[item.identity+f'/edit{k}/new0']
            elif kind=='delete':ids=ids[:i]+ids[i+1:]
            elif kind=='duplicate':ids=ids[:i]+[item.identity+f'/edit{k}/copy{q}' for q in range(e['count'])]+ids[i:]
            elif kind=='swap':ids[i],ids[e['other']]=ids[e['other']],ids[i]
            else:assert kind in ('replace','operand')
        assert ids==birth['gene_ids'] and len(ids)==len(set(ids))==len(program.genes)
        final=dict(zip(ids,rows(program)));retained=sum(final.get(k)==v for k,v in donor_changes.items()) if program.digest!=parent.genome.program.digest else 0
        assert retained==birth['retained_donor_changes'];count['independent_gene_maps']+=1
    return count

class Replay:
    def __init__(self):self.calls=0;self.exact=0;self.work=0;self.seconds=0.;self.graded=0;self.cache={}
    def evaluation(self,e,i,cases,ids,checker,stage,key,g):
        assert (e['stage'],e['key'],e['generation'],e['id'])==(stage,key,g,i.identity)
        assert [r['case'] for r in e['rows']]==ids
        org=organism(physical(i,'neutral','local')[1]);work=0
        for row in e['rows']:
            cid=row['case'];o=cases[cid];m=o.maze;cachekey=(i.genome.digest,cid)
            if cachekey not in self.cache:
                self.cache[cachekey]=record(org.react(m.cells,m.w,m.h,m.start,m.goal),o);self.exact+=1
            assert self.cache[cachekey]==row,(key,g,i.identity,cid)
            checker.row(row);self.graded+=1;self.calls+=1;work+=row['reads']+row['dispatches']+row['exposure_checks']
        assert work==e['work'];self.work+=work;self.seconds+=e['seconds'];return e['rows']

def exhausted(it):assert next(it,None) is None

def assert_corpus(d,path):
    cases,contexts,meta=load(path)
    assert canonical(manifest(d.cache.values()))==read_compressed(path/'mazes.json.gz')
    assert canonical(d.contexts)==contexts and canonical(d.metadata)==meta;geometry(cases,meta)
    return cases,meta

def audit():
    t=time.perf_counter();reg=check_freeze();counts=Counter(prior_hashes=prior_check());assert counts['prior_hashes']==5706
    pools=make_pools();assert pools==read_compressed(OUT/'pools.json.gz');d=fixture(exclusions());fc,fm=assert_corpus(d,FIXTURES)
    sd=Data(12345678,d.layouts)
    for g in range(3):training_batch(sd,g);assert_corpus(sd,OUT/'software_fixtures'/f'g{g:04d}');clear(sd)
    assert len(sd.layouts)==json.loads((OUT/'software_preparation.json').read_text())['whole_layouts']
    replay=Replay();checker=Checker(fc);it=iter(lines(FIXTURES/'responses.jsonl.gz'));births=iter(lines(FIXTURES/'reproduction.jsonl.gz'));ids=profile_ids(fm);rates={}
    for key,pool in pools.items():
        before=replay.seconds;pop=[Individual.load(r) for r in pool['items']];rr={i.identity:replay.evaluation(next(it),i,fc,ids,checker,'profile',key,-1) for i in pop};rates[key]=(replay.seconds-before)/(96*len(ids));rank=ranked(pop,rr,fm)
        for arm in ARMS:
            state=init_state(key+'/'+arm,pool);new,e=reproduce(state,rank);assert next(births)==dict(calibration_only=True,event=e,next_state_digest=digest(new));independent_births(state,e)
    known=Individual.load(read_compressed(ROOT/'results/compatibility_map/panel.json.gz')['items']['intact']);rr=replay.evaluation(next(it),known,fc,list(fc),checker,'profile','intact',-1)
    assert all(r['optimal'] or r['no_path'] for r in rr);exhausted(it);exhausted(births)
    profile=json.loads((FIXTURES/'profile.json').read_text());assert replay.calls==profile['budget']['calls'] and replay.work==profile['budget']['work']
    for k,v in rates.items():assert abs(v-profile['pool_rates'][k])<1e-12
    projections={str(g):projection(profile,g) for g in (96,64,32)};assert projections==profile['projections']
    assert profile['generations']==next((g for g in (96,64,32) if projections[str(g)]<600),0)
    start_calls,start_work,start_seconds=replay.calls,replay.work,replay.seconds
    states={key+'/'+a:init_state(key+'/'+a,pool) for key,pool in pools.items() for a in ARMS};assert states==read_compressed(OUT/'initial_states.json.gz')
    d=Data(seed_for(SEED,'train',0,0),sd.layouts);ex=json.loads((OUT/'execution.json').read_text());assert ex['complete'];births=iter(lines(OUT/'reproduction.jsonl.gz'));baseline_count=0
    assert 0<ex['generations']<=profile['generations']
    for g in range(ex['generations']):
        ids=training_batch(d,g);path=OUT/'train'/f'g{g:04d}';tc,tm=assert_corpus(d,path);assert json.loads((path/'query.json').read_text())['ids']==ids
        gen=json.loads((path/'generation.json').read_text());assert gen['prior_layouts']==d.previous_count and gen['whole_layouts']==len(d.layouts)
        for name,h in gen['hashes'].items():assert sha(ROOT/name)==h
        assert subprocess.check_output(['git','show',gen['revision']+':results/linkage_pilot/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
        checker=Checker(tc);it=iter(lines(path/'responses.jsonl.gz'));replay.cache={}
        for key,state in states.items():
            pop=[Individual.load(r) for r in state['population']];rr={i.identity:replay.evaluation(next(it),i,tc,ids,checker,'train',key,g) for i in pop};rank=ranked(pop,rr,tm)
            new,event=reproduce(state,rank);assert event==next(births),(key,g);counts.update(independent_births(state,event));states[key]=new
        exhausted(it);bs=iter(lines(path/'baselines.jsonl.gz'))
        for name in ('compiled_bfs','compiled_astar','wave_bit'):
            for cid in ids:
                o=tc[cid];m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert next(bs)==dict(model=name,row=r);assert r['optimal'] or r['no_path'];checker.row(r);baseline_count+=1
        exhausted(bs);clear(d)
        if (g+1)%16==0:assert states==read_compressed(OUT/f'checkpoints/g{g+1}.json.gz')
        if (g+1)%4==0:print(json.dumps(dict(generation=g+1,logical_responses=replay.calls,exact_native_replays=replay.exact,wall=round(time.perf_counter()-t,2))),flush=True)
    exhausted(births);assert states==read_compressed(OUT/'next_states.json.gz')==read_compressed(OUT/'latest_states.json.gz')
    assert replay.calls-start_calls==ex['budget']['calls']==ex['generations']*36*96*6
    assert replay.work-start_work==ex['budget']['work'] and abs(replay.seconds-start_seconds-ex['budget']['seconds'])<1e-5
    assert ex['wall_seconds']<720 and ex['budget']['seconds']<720 and ex['budget']['work']<2000000000000 and ex['peak_rss_bytes']<4*2**30
    assert baseline_count==ex['baseline_calls'] and len(d.layouts)==ex['whole_layouts']
    analysis=compute(lines(OUT/'reproduction.jsonl.gz'),ex['generations']);assert analysis==json.loads((OUT/'analysis.json').read_text())
    write_json(OUT/'audit.json',dict(passed=True,counts=counts,logical_candidate_responses=replay.calls,exact_distinct_native_replays=replay.exact,independently_graded_candidate_rasters=replay.graded,baseline_replays=baseline_count,source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),whole_layouts=len(d.layouts),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,limitations='Every candidate record compared with a new native replay, exact genotypes deduplicated within each generation. Every logical raster independently graded. Full selection, mutation, crossover, gene identity and RNG replay. Accepted crossover dependencies independently scanned backwards. Training data only; no efficacy holdout.'))
    print((OUT/'audit.json').read_text(),flush=True)
