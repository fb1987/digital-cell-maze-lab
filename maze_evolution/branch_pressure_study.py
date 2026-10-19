"""V12N bounded frozen-pool branch-pressure preflight and independent transfer."""
import argparse,gzip,json,random,time,resource,subprocess
from collections import defaultdict
from .foundation_calibration import ROOT,LIMITS,write_json
from .foundation_study import read_compressed,compressed_json
from .growth import mutate,replay_mutation,Individual as OldIndividual
from .exposure_genome import Individual,Genome
from .exposure_selection import physical,organism,record
from .branch_pressure_data import *
from .branch_pressure_fitness import choose,measurements
from .routing_transfer import sha,canonical,logrow,lines
from .baselines import baseline
from .foundation_pair_confirm import normal_row

TOPS=('local','evolved')
PRESSURES=('current','choice')


class Budget:
    def __init__(self,seconds,calls):
        self.cap_seconds=seconds;self.cap_calls=calls;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
    def call(self,fn):
        if self.calls>=self.cap_calls or self.seconds>=self.cap_seconds-max(.25,2*self.maximum):
            raise TimeoutError('Closed V12N cap; preserve partial results, no extension')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('V12N 4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t
        self.seconds+=dt;self.calls+=1;self.maximum=max(self.maximum,dt)
        self.work+=r.dispatches+r.spatial_reads+r.exposure_checks
        assert self.seconds<self.cap_seconds
        return r
    def save(self):return vars(self).copy()


def make_pools():
    old=read_compressed(ROOT/'results/exposure_calibration/pools.json.gz');sel=read_compressed(ROOT/'results/exposure_calibration/selections.json.gz')
    pools={};events=[];rngs={};models={};aliases={}
    for rep in range(3):
        source=old[f'fresh/{rep}']['items'];items=list(source);rng=random.Random(seed_for(SEED,'program_edits',rep,0));before=rng.getstate()
        for raw in source:
            parent=Individual.load(raw)
            for k in range(2):
                program,event=mutate(parent.genome.program,rng,1,256,True)
                child=Individual(f'branch_pressure/r{rep}/f{source.index(raw)}/edit{k}',Genome(program,parent.genome.exposure),parent.identity,1)
                assert replay_mutation(parent.genome.program,event,256)==program
                items.append(child.save());events.append(dict(rep=rep,item=child.save(),event=event))
        anchors=sorted({sel[f'fresh/{rep}'][a]['item']['id'] for a in ('neutral','local')})
        pools[str(rep)]=dict(items=items,anchors=anchors,base_id=source[0]['id'],founders=[i['id'] for i in source])
        rngs[str(rep)]=dict(before=before,after=rng.getstate())
        for top in TOPS:
            key=f'{rep}/{top}';aliases[key]={}
            for raw in items:
                item=Individual.load(raw);pid,m=physical(item,'neutral',top);models[pid]=m;aliases[key][item.identity]=pid
    return canonical(pools),canonical(events),canonical(rngs),models,aliases


def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir()
    for name,value in zip(('pools','events','rng','models','aliases'),make_pools()):compressed_json(OUT/f'{name}.json.gz',value)
    d=create(FIXTURE_SEED,'fixture',exclusions());assert d.previous_count==175592;d.save(FIXTURES)
    print(json.dumps(dict(pools=3,logical_genotypes=864,physical_models=len(read_compressed(OUT/'models.json.gz')),fixture_layouts=len(d.layouts)-d.previous_count)),flush=True)


def freeze():
    assert not (OUT/'preregistration.json').exists()
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/BRANCH_PRESSURE_CALIBRATION_V12N.md',ROOT/'tests/test_branch_pressure_calibration.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for d in (OUT,FIXTURES) for p in d.rglob('*') if p.is_file() and p.suffix!='.log']
    inputs += [ROOT/'results/exposure_calibration/pools.json.gz',ROOT/'results/exposure_calibration/selections.json.gz']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,sources={str(p.relative_to(ROOT)):sha(p) for p in paths},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},main_generated=False,candidate_calls=0))


def check_freeze(committed=False):
    reg=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for p,h in reg[group].items():assert sha(ROOT/p)==h,p
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/branch_pressure_calibration/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return reg


def loaded(path):
    cases,contexts,meta=load(path);d=type('Loaded',(),{})();d.cache=cases;d.contexts=contexts;d.metadata=meta;return d


def warm(data):
    raw=read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')['intact']['item'];old=OldIndividual.load(raw)
    item=Individual(old.identity,Genome(old.genome,7),None,0);pid,m=physical(item,'neutral','local');o=next(iter(data.cache.values()));maze=o.maze
    t=time.perf_counter();r=organism(m).react(maze.cells,maze.w,maze.h,maze.start,maze.goal)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,maze.cells,maze.w,maze.h,maze.start,maze.goal)
    return dict(seconds=time.perf_counter()-t,candidate_calls=1,baseline_calls=3,case=maze.case_id),pid,m


def profile():
    check_freeze(True);assert not (FIXTURES/'profile.json').exists();d=loaded(FIXTURES);warmup,_,_=warm(d);models=read_compressed(OUT/'models.json.gz');aliases=read_compressed(OUT/'aliases.json.gz');pools=read_compressed(OUT/'pools.json.gz')
    ids=[cid for cid,m in d.metadata.items() if m['pose']==0];b=Budget(60,1440);rates=[];t=time.perf_counter()
    with gzip.open(FIXTURES/'profiles.jsonl.gz','wt',compresslevel=1) as log:
        for rep in range(3):
            for top in TOPS:
                for k in (0,24,48,72):
                    pid=aliases[f'{rep}/{top}'][pools[str(rep)]['founders'][k]];org=organism(models[pid]);start=b.seconds
                    for cid in ids:
                        o=d.cache[cid];m=o.maze;r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));logrow(log,dict(model=pid,row=record(r,o)))
                    rates.append((b.seconds-start)/len(ids))
    projected=b.seconds/1440*(len(models)*240);valid=48*240*max(rates);final=40*1440*max(rates)
    packet=dict(passed=projected+valid<432 and final<180,projected_pool_seconds=projected,validation_upper_seconds=valid,final_upper_seconds=final,budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(FIXTURES/'profile.json',packet);print(json.dumps(packet,indent=2),flush=True)


def save_stage(path,data,models,ids):
    data.save(path);compressed_json(path/'models.json.gz',models);compressed_json(path/'query.json.gz',ids)
    write_json(path/'generation.json',dict(cases=len(data.cache),queried=len(ids),models=len(models),planned_calls=len(ids)*len(models),whole_layouts=len(data.layouts),rejections=data.rejections,
        hashes={str(p.relative_to(ROOT)):sha(p) for p in path.glob('*.gz')}))


def assay(path,data,models,ids,budget):
    out={}
    with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for index,(key,model) in enumerate(sorted(models.items())):
            org=organism(model);rows=[]
            for cid in ids:
                o=data.cache[cid];m=o.maze;r=budget.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));row=record(r,o);rows.append(row);logrow(log,dict(model=key,row=row))
            out[key]=rows
            if index%200==199:print(json.dumps(dict(stage=path.name,models=index+1,calls=budget.calls,seconds=round(budget.seconds,2))),flush=True)
            if index%64==0:
                total=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
                if total>2*2**30:raise RuntimeError('Closed output cap')
    return out


def details_map(m):return {(r['base'],r['pose']):r for r in m['details']}


def calibration_gate(pool,rows,meta,current,choice):
    ms={k:measurements(rs,meta) for k,rs in rows.items()}
    cp=sum(ms[i]['mean_score'] for i in current['parents'])/64;np=sum(ms[i]['mean_score'] for i in choice['parents'])/64
    promising=[i for i in choice['nominees'] if ms[i]['mean_score']>=.02 and ms[i]['positive_pairs']>=4 and ms[i]['positive_templates']>=2 and ms[i]['three_edge_positive'] and ms[i]['strict_pairs']]
    improvements=[]
    for raw in pool['items']:
        if raw['parent'] not in ms:continue
        parent=details_map(ms[raw['parent']]);child=details_map(ms[raw['id']])
        better=[list(k) for k,v in child.items() if v['eligible'] and v['strict_both'] and v['score']-parent[k]['score']>=.1-1e-12]
        if better:improvements.append(dict(child=raw['id'],parent=raw['parent'],pairs=better))
    fields=dict(parent_changes=sum(a!=b for a,b in zip(current['parents'],choice['parents'])),elite_changed=set(current['elite'])!=set(choice['elite']),nominees_changed=set(current['nominees'])!=set(choice['nominees']),
        current_parent_score=cp,choice_parent_score=np,promising_nominees=promising,improving_children=improvements,
        anchors_retained=all(a in current['elite'] and a in choice['elite'] for a in pool['anchors']))
    fields['passed']=fields['parent_changes']>=16 and fields['elite_changed'] and fields['nominees_changed'] and np>=cp+.01-1e-12 and bool(promising) and bool(improvements) and fields['anchors_retained']
    return fields,ms


def run():
    check_freeze(True);assert json.loads((FIXTURES/'profile.json').read_text())['passed'];assert not (OUT/'calibration').exists()
    models=read_compressed(OUT/'models.json.gz');aliases=read_compressed(OUT/'aliases.json.gz');pools=read_compressed(OUT/'pools.json.gz')
    previous=exclusions()+read_compressed(FIXTURES/'mazes.json.gz');d=create(SEED,'calibration',previous);path=OUT/'calibration';save_stage(path,d,models,query(d));warmup,_,_=warm(d)
    b=Budget(480,500000);t=time.perf_counter();complete=False
    try:
        rr=assay(path,d,models,query(d),b);choices={};gates={};metrics={};vmodels={}
        for rep,pool in pools.items():
            for top in TOPS:
                key=f'{rep}/{top}';rows={i['id']:rr[aliases[key][i['id']]] for i in pool['items']}
                choices[key]={p:choose(pool,rows,d.metadata,seed_for(SEED,'parents',int(rep),0),p) for p in PRESSURES}
                gates[key],metrics[key]=calibration_gate(pool,rows,d.metadata,choices[key]['current'],choices[key]['choice'])
                for p in PRESSURES:
                    for i in choices[key][p]['nominees']:vmodels[aliases[key][i]]=models[aliases[key][i]]
        compressed_json(OUT/'calibration_choices.json.gz',choices);compressed_json(OUT/'calibration_metrics.json.gz',metrics);write_json(OUT/'calibration_gates.json',gates)
        del rr,rows,metrics
        previous+=read_compressed(path/'mazes.json.gz');v=create(seed_for(SEED,'validation',0,0),'validation',previous);vp=OUT/'validation';save_stage(vp,v,vmodels,query(v));vr=assay(vp,v,vmodels,query(v),b);selections={}
        for rep,pool in pools.items():
            for top in TOPS:
                key=f'{rep}/{top}';selections[key]={}
                for p in PRESSURES:
                    ids=choices[key][p]['nominees'];small=dict(items=[i for i in pool['items'] if i['id'] in ids],anchors=[])
                    rows={i['id']:vr[aliases[key][i['id']]] for i in small['items']};ch=choose(small,rows,v.metadata,seed_for(SEED,'validation',int(rep),0),p)
                    selections[key][p]=dict(item=next(i for i in pool['items'] if i['id']==ch['best']),rank=ch['rank'],nominees=ids,metrics=measurements(rows[ch['best']],v.metadata))
        compressed_json(OUT/'selections.json.gz',selections);complete=True
    finally:write_json(OUT/'selection_execution.json',dict(complete=complete,budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps({k:{f:v for f,v in g.items() if f not in ('improving_children',)} for k,g in gates.items()},indent=2),flush=True)


def final_panel():
    pools=read_compressed(OUT/'pools.json.gz');sel=read_compressed(OUT/'selections.json.gz');models={};aliases={}
    for rep,pool in pools.items():
        for top in TOPS:
            key=f'{rep}/{top}';aliases[key]={}
            specs=[('selected_'+p,sel[key][p]['item']) for p in PRESSURES]
            specs += [('anchor_'+str(j),next(i for i in pool['items'] if i['id']==a)) for j,a in enumerate(pool['anchors'])]
            specs += [('founder0',next(i for i in pool['items'] if i['id']==pool['base_id']))]
            for label,raw in specs:
                pid,m=physical(Individual.load(raw),'neutral',top);models[pid]=m;aliases[key][label]=dict(model=pid,item=raw)
    old=OldIndividual.load(read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')['intact']['item']);item=Individual(old.identity,Genome(old.genome,7),None,0)
    pid,m=physical(item,'neutral','local');models[pid]=m
    return models,aliases,pid


def confirm():
    check_freeze(True);assert not (OUT/'confirmation').exists();assert json.loads((OUT/'selection_execution.json').read_text())['complete']
    assert subprocess.check_output(['git','show','HEAD:results/branch_pressure_calibration/selections.json.gz'])==(OUT/'selections.json.gz').read_bytes()
    previous=exclusions()
    for p in (FIXTURES,OUT/'calibration',OUT/'validation'):previous+=read_compressed(p/'mazes.json.gz')
    d=create(seed_for(SEED,'confirmation',0,0),'confirmation',previous,3);models,aliases,control=final_panel();path=OUT/'confirmation';ids=query(d,True);save_stage(path,d,models,ids)
    compressed_json(path/'aliases.json.gz',aliases);write_json(path/'control.json',dict(model=control));b=Budget(200,60000);t=time.perf_counter();warmup,_,_=warm(d);complete=False;bc=0
    try:
        rr=assay(path,d,models,ids,b);assert all(r['optimal'] or r['no_path'] for r in rr[control])
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for cid in ids:
                    o=d.cache[cid];m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert r['optimal'] or r['no_path'];logrow(log,dict(model=name,row=r));bc+=1
        complete=True
    finally:write_json(path/'execution.json',dict(complete=complete,budget=b.save(),warmup=warmup,baseline_calls=bc,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def analyze():
    d=loaded(OUT/'confirmation');rr=defaultdict(list)
    for r in lines(OUT/'confirmation/responses.jsonl.gz'):rr[r['model']].append(r['row'])
    aliases=read_compressed(OUT/'confirmation/aliases.json.gz');cal=json.loads((OUT/'calibration_gates.json').read_text());out={};passed={top:[] for top in TOPS}
    for key,aa in aliases.items():
        ms={label:measurements(rr[a['model']],d.metadata) for label,a in aa.items()};a,c=ms['selected_choice'],ms['selected_current']
        final=a['mean_score']>=.02 and a['mean_score']>=c['mean_score']+.01-1e-12 and a['positive_pairs']>=4 and a['positive_templates']>=2 and a['three_edge_positive']>0 and a['strict_pairs']>0 and a['pairs']>=c['pairs']
        combined=bool(cal[key]['passed'] and final);out[key]=dict(metrics=ms,calibration_passed=cal[key]['passed'],final_passed=bool(final),combined_passed=combined)
        if combined:passed[key.split('/')[1]].append(int(key.split('/')[0]))
    result=dict(results=out,passing_groups=passed,pilot_eligible=any(len(v)>=2 for v in passed.values()),no_evolution=True)
    write_json(OUT/'analysis.json',result);print(json.dumps(dict(passing_groups=passed,pilot_eligible=result['pilot_eligible'],summary={k:{label:{f:m[f] for f in ('pairs','nonadj_pairs','mean_score','positive_pairs','strict_pairs','corridors')} for label,m in v['metrics'].items()} for k,v in out.items()}),indent=2),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','freeze','profile','run','confirm','analyze','audit'));a=p.parse_args().action
    if a=='audit':
        from .branch_pressure_audit import audit
        audit()
    else:globals()[a]()
if __name__=='__main__':main()
