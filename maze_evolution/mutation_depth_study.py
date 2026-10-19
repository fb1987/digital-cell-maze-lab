"""V12O performance-blind mutation walks, equal-size controls, frozen transfer."""
import argparse,gzip,json,random,time,resource,subprocess,hashlib
from collections import defaultdict
from .foundation_calibration import ROOT,LIMITS,write_json
from .foundation_study import read_compressed,compressed_json
from .growth import mutate,replay_mutation,random_genome,Individual as OldIndividual
from .exposure_genome import Individual,Genome
from .exposure_selection import physical,organism,record
from .branch_pressure_study import loaded,warm
from .mutation_depth_data import *
from .mutation_depth_metrics import summarize,compare,nominate,supply,rank
from .routing_transfer import canonical,sha,logrow,lines
from .datasets import seed_for
from .baselines import baseline
from .foundation_pair_confirm import normal_row


def rng_hash(rng):return hashlib.sha256(json.dumps(rng.getstate(),separators=(',',':')).encode()).hexdigest()


def make_pools():
    old=read_compressed(ROOT/'results/exposure_calibration/pools.json.gz');sel=read_compressed(ROOT/'results/exposure_calibration/selections.json.gz')
    entries={};groups={};roots={};anchors={};walks=[];events=[];random_states={}
    def entry(item,reference,arm,rep,index,walk=None,depth=None):
        entries[item.identity]=dict(item=item.save(),reference=reference,arm=arm,rep=rep,index=index,walk=walk,depth=depth,program_digest=item.genome.program.digest)
    for rep in range(3):
        rr=old[f'fresh/{rep}']['items'];roots[str(rep)]=[i['id'] for i in rr];groups[str(rep)]={a:[] for a in ARMS}
        anchors[str(rep)]=sorted({sel[f'fresh/{rep}'][a]['item']['id'] for a in ('neutral','local')})
        for index,raw in enumerate(rr):
            root=Individual.load(raw);entry(root,root.identity,'frozen',rep,index)
            for w in range(2):
                rng=random.Random(seed_for(SEED,'walk',rep,index*2+w));before=rng.getstate();current=root;checkpoints={};states={}
                for depth in range(1,17):
                    before_hash=rng_hash(rng);program,event=mutate(current.genome.program,rng,1,256,True)
                    child=Individual(f'mutation_depth/r{rep}/f{index}/walk{w}/d{depth}',Genome(program,root.genome.exposure),current.identity,depth)
                    assert replay_mutation(current.genome.program,event,256)==program
                    events.append(dict(kind='walk',rep=rep,index=index,walk=w,depth=depth,item=child.save(),event=event,rng_before_sha256=before_hash,rng_after_sha256=rng_hash(rng)))
                    if depth in DEPTHS:
                        arm=f'depth{depth}';entry(child,root.identity,arm,rep,index,w,depth);groups[str(rep)][arm].append(child.identity);checkpoints[str(depth)]=child.identity;states[str(depth)]=rng.getstate()
                    current=child
                walks.append(dict(rep=rep,index=index,walk=w,root=root.identity,before=before,after=rng.getstate(),checkpoints=checkpoints,checkpoint_rng=states))
            for w in range(2):
                rng=random.Random(seed_for(SEED,'single',rep,index*2+w));before=rng.getstate();program,event=mutate(root.genome.program,rng,1,256,True)
                child=Individual(f'mutation_depth/r{rep}/f{index}/single{w}',Genome(program,root.genome.exposure),root.identity,1)
                assert replay_mutation(root.genome.program,event,256)==program
                events.append(dict(kind='single',rep=rep,index=index,walk=w,depth=1,item=child.save(),event=event,rng_before=before,rng_after=rng.getstate()))
                entry(child,root.identity,'single',rep,index,w,1);groups[str(rep)]['single'].append(child.identity)
        rng=random.Random(seed_for(SEED,'resample',rep,0));before=rng.getstate()
        for index in range(96):
            for w in range(2):
                child=Individual(f'mutation_depth/r{rep}/f{index}/random{w}',Genome(random_genome(rng,True),7),None,0)
                entry(child,rr[index]['id'],'resample',rep,index,w,0);groups[str(rep)]['resample'].append(child.identity)
        random_states[str(rep)]=dict(before=before,after=rng.getstate())
    models={};aliases={top:{} for top in TOPS}
    for top in TOPS:
        for identity,e in entries.items():
            pid,m=physical(Individual.load(e['item']),'neutral',top);models[pid]=m;aliases[top][identity]=pid
    pool=dict(entries=entries,groups=groups,roots=roots,anchors=anchors)
    return canonical(pool),canonical(events),canonical(walks),canonical(random_states),models,aliases


class Budget:
    def __init__(self,seconds=720,calls=3400000,saved=None):
        self.cap_seconds=seconds;self.cap_calls=calls;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
        if saved:
            assert saved['cap_seconds']==seconds and saved['cap_calls']==calls
            for k,v in saved.items():setattr(self,k,v)
    def call(self,fn):
        if self.calls>=self.cap_calls or self.seconds>=self.cap_seconds-max(.25,2*self.maximum):raise TimeoutError('Closed V12O cap; preserve partial results, no extension')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('V12O 4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t;self.seconds+=dt;self.calls+=1;self.maximum=max(self.maximum,dt);self.work+=r.spatial_reads+r.dispatches+r.exposure_checks
        assert self.seconds<self.cap_seconds
        return r
    def save(self):return vars(self).copy()


def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();t=time.perf_counter()
    values=make_pools()
    for name,value in zip(('pools','events','walks','random_rng','models','aliases'),values):compressed_json(OUT/f'{name}.json.gz',value)
    mutation_seconds=time.perf_counter()-t;d=create(FIXTURE_SEED,'fixture',exclusions());assert d.previous_count==177032;d.save(FIXTURES)
    write_json(OUT/'preparation.json',dict(wall_seconds=time.perf_counter()-t,mutation_and_serialization_seconds=mutation_seconds,entries=len(values[0]['entries']),events=len(values[1]),walks=len(values[2]),physical_models=len(values[4]),fixture_layouts=len(d.layouts)-d.previous_count,candidate_calls=0))
    print((OUT/'preparation.json').read_text(),flush=True)


def freeze():
    assert not (OUT/'preregistration.json').exists();paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/MUTATION_DEPTH_V12O.md',ROOT/'tests/test_mutation_depth.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for d in (OUT,FIXTURES) for p in d.rglob('*') if p.is_file() and p.suffix!='.log']
    inputs +=[ROOT/'results/exposure_calibration/pools.json.gz',ROOT/'results/exposure_calibration/selections.json.gz']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,sources={str(p.relative_to(ROOT)):sha(p) for p in paths},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},candidate_calls=0))


def check_freeze(committed=False):
    reg=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for p,h in reg[group].items():assert sha(ROOT/p)==h,p
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/mutation_depth/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return reg


def profile():
    check_freeze(True);assert not (FIXTURES/'profile.json').exists();d=loaded(FIXTURES);warmup,_,_=warm(d);models=read_compressed(OUT/'models.json.gz');ids=[cid for cid,m in d.metadata.items() if m['pose']==0];b=Budget(120,400000);rates={};t=time.perf_counter()
    with gzip.open(FIXTURES/'profiles.jsonl.gz','wt',compresslevel=1) as log:
        for index,(key,model) in enumerate(sorted(models.items())):
            org=organism(model);start=b.seconds
            for cid in ids:
                o=d.cache[cid];m=o.maze;r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));logrow(log,dict(model=key,row=record(r,o)))
            rates[key]=(b.seconds-start)/len(ids)
            if index%500==499:print(json.dumps(dict(models=index+1,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
    maximum=max(rates.values());projection=8*b.seconds+120*480*maximum+90*960*maximum
    compressed_json(FIXTURES/'rates.json.gz',rates)
    packet=dict(passed=projection<648,projected_discovery=8*b.seconds,projected_validation=120*480*maximum,projected_final=90*960*maximum,projected_total=projection,budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(FIXTURES/'profile.json',packet);print(json.dumps(packet,indent=2),flush=True)


def save_stage(path,data,models):
    data.save(path);ids=query(data,True);compressed_json(path/'models.json.gz',models);compressed_json(path/'query.json.gz',ids)
    write_json(path/'generation.json',dict(cases=len(data.cache),queried=len(ids),models=len(models),planned_calls=len(ids)*len(models),whole_layouts=len(data.layouts),rejections=data.rejections,hashes={str(p.relative_to(ROOT)):sha(p) for p in path.glob('*.gz')}))
    return ids


def assay(path,data,models,ids,budget):
    metrics={};summary_seconds=0.;start=time.perf_counter();initial=budget.save()
    with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for index,(key,model) in enumerate(sorted(models.items())):
            org=organism(model);rows=[]
            for cid in ids:
                o=data.cache[cid];m=o.maze;r=budget.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));row=record(r,o);rows.append(row);logrow(log,dict(model=key,row=row))
            st=time.perf_counter();metrics[key]=summarize(rows,data.metadata);summary_seconds+=time.perf_counter()-st
            if index%250==249:print(json.dumps(dict(stage=path.name,models=index+1,calls=budget.calls,seconds=round(budget.seconds,2))),flush=True)
            if index%128==0 and sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:raise RuntimeError('Closed V12O output cap')
    compressed_json(path/'metrics.json.gz',metrics)
    write_json(path/'assay.json',dict(initial_budget=initial,final_budget=budget.save(),summary_seconds=summary_seconds,wall_seconds=time.perf_counter()-start))
    return metrics


def discovery_gates(pool,metrics,aliases):
    result={}
    for rep,arms in pool['groups'].items():
        for top in TOPS:
            key=f'{rep}/{top}';sup={a:supply(ids,pool['entries'],metrics,aliases[top]) for a,ids in arms.items()};gates={}
            for depth in ('depth4','depth16'):
                d=sup[depth];gates[depth]=d['useful_count']>=4 and d['useful_references']>=2 and d['useful_behaviors']>=2 and all(d['useful_count']>=sup[c]['useful_count']+2 for c in ('depth1','single','resample'))
            result[key]=dict(supply=sup,passed=gates)
    return result


def run():
    check_freeze(True);assert json.loads((FIXTURES/'profile.json').read_text())['passed'];assert not (OUT/'discovery').exists();t=time.perf_counter();pool=read_compressed(OUT/'pools.json.gz');models=read_compressed(OUT/'models.json.gz');aliases=read_compressed(OUT/'aliases.json.gz')
    previous=exclusions()+read_compressed(FIXTURES/'mazes.json.gz');d=create(SEED,'discovery',previous);path=OUT/'discovery';ids=save_stage(path,d,models);warmup,_,_=warm(d);b=Budget();complete=False
    try:
        ms=assay(path,d,models,ids,b);choices={};vmodels={}
        gates=discovery_gates(pool,ms,aliases);write_json(OUT/'discovery_gates.json',gates)
        for rep,arms in pool['groups'].items():
            for top in TOPS:
                key=f'{rep}/{top}';choices[key]={}
                for a,ids in arms.items():
                    ch=nominate(ids,pool['entries'],ms,aliases[top]);choices[key][a]=ch
                    for identity in ch['nominees']:
                        for i in (identity,pool['entries'][identity]['reference']):vmodels[aliases[top][i]]=models[aliases[top][i]]
        compressed_json(OUT/'discovery_choices.json.gz',choices);del ms
        previous+=read_compressed(path/'mazes.json.gz');v=create(seed_for(SEED,'validation',0,0),'validation',previous);vp=OUT/'validation';vids=save_stage(vp,v,vmodels);vm=assay(vp,v,vmodels,vids,b);selections={}
        for rep in pool['groups']:
            for top in TOPS:
                key=f'{rep}/{top}';selections[key]={}
                for a in ARMS:
                    ch=nominate(choices[key][a]['nominees'],pool['entries'],vm,aliases[top]);selections[key][a]=ch
        compressed_json(OUT/'selections.json.gz',selections);complete=True
    finally:write_json(OUT/'selection_execution.json',dict(complete=complete,budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps({k:g['passed'] for k,g in gates.items()},indent=2),flush=True)


def final_panel():
    pool=read_compressed(OUT/'pools.json.gz');sel=read_compressed(OUT/'selections.json.gz');allmodels=read_compressed(OUT/'models.json.gz');aa=read_compressed(OUT/'aliases.json.gz');models={};panel={}
    for rep in pool['groups']:
        for top in TOPS:
            key=f'{rep}/{top}';panel[key]={}
            for arm in ARMS:
                identity=sel[key][arm]['best'];e=pool['entries'][identity];ids=[identity,e['reference']]
                if arm.startswith('depth'):
                    ids += [f'mutation_depth/r{rep}/f{e["index"]}/walk{e["walk"]}/d{d}' for d in DEPTHS if d<e['depth']]
                panel[key][arm]=dict(selected=identity,reference=e['reference'],checkpoints=ids)
                for i in ids:models[aa[top][i]]=allmodels[aa[top][i]]
            panel[key]['anchors']=pool['anchors'][rep]
            for i in pool['anchors'][rep]:models[aa[top][i]]=allmodels[aa[top][i]]
    old=OldIndividual.load(read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')['intact']['item']);item=Individual(old.identity,Genome(old.genome,7),None,0);pid,m=physical(item,'neutral','local');models[pid]=m
    assert len(models)<=90
    return models,panel,pid


def confirm():
    check_freeze(True);assert not (OUT/'confirmation').exists();run=json.loads((OUT/'selection_execution.json').read_text());assert run['complete']
    assert subprocess.check_output(['git','show','HEAD:results/mutation_depth/selections.json.gz'])==(OUT/'selections.json.gz').read_bytes()
    t=time.perf_counter();previous=exclusions()
    for path in (FIXTURES,OUT/'discovery',OUT/'validation'):previous+=read_compressed(path/'mazes.json.gz')
    d=create(seed_for(SEED,'confirmation',0,0),'confirmation',previous,2);models,panel,control=final_panel();path=OUT/'confirmation';ids=save_stage(path,d,models);compressed_json(path/'panel.json.gz',panel);write_json(path/'control.json',dict(model=control))
    b=Budget(saved=run['budget']);initial=b.save();warmup,_,_=warm(d);bc=0;complete=False
    try:
        ms=assay(path,d,models,ids,b);assert ms[control]['optimal']==640 and ms[control]['no_path']==320
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for cid in ids:
                    o=d.cache[cid];m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert r['optimal'] or r['no_path'];logrow(log,dict(model=name,row=r));bc+=1
        complete=True
    finally:write_json(path/'execution.json',dict(complete=complete,initial_budget=initial,budget=b.save(),warmup=warmup,baseline_calls=bc,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def analysis_packet():
    pool=read_compressed(OUT/'pools.json.gz');aa=read_compressed(OUT/'aliases.json.gz');panel=read_compressed(OUT/'confirmation/panel.json.gz');ms=read_compressed(OUT/'confirmation/metrics.json.gz');dg=json.loads((OUT/'discovery_gates.json').read_text());result={};passing={f'{d}/{t}':[] for d in ('depth4','depth16') for t in TOPS}
    for key,pp in panel.items():
        rep,top=key.split('/');arms={}
        for arm in ARMS:
            row=pp[arm];m=ms[aa[top][row['selected']]];root=ms[aa[top][row['reference']]];c=compare(m,root)
            arms[arm]=dict(selected=row['selected'],reference=row['reference'],metrics=m,reference_metrics=root,comparison=c,checkpoints={i:ms[aa[top][i]] for i in row['checkpoints']})
        gates={}
        for depth in ('depth4','depth16'):
            d=arms[depth];m,c=d['metrics'],d['comparison'];controls=[arms[a]['metrics'] for a in ('depth1','single','resample')]
            contrast=all(m['nonadj_pairs']>v['nonadj_pairs'] for v in controls) or all(m['mean_score']>=v['mean_score']+.005-1e-12 for v in controls)
            ok=m['mean_score']>=.01 and c['new_positive_pairs']>=4 and c['new_positive_templates']>=2 and c['response_changed'] and contrast
            gates[depth]=dict(discovery_passed=dg[key]['passed'][depth],final_passed=bool(ok),combined_passed=bool(ok and dg[key]['passed'][depth]))
            if gates[depth]['combined_passed']:passing[f'{depth}/{top}'].append(int(rep))
        result[key]=dict(arms=arms,gates=gates,anchors={i:ms[aa[top][i]] for i in pp['anchors']})
    return dict(results=result,passing_groups=passing,exploration_ready=any(len(v)>=2 for v in passing.values()),fitness_guided_evolution=False)


def analyze():
    result=analysis_packet();compressed_json(OUT/'analysis.json.gz',result)
    concise={k:{a:{f:v['metrics'][f] for f in ('pairs','nonadj_pairs','mean_score','strict_pairs','corridors')} for a,v in r['arms'].items()} for k,r in result['results'].items()}
    write_json(OUT/'analysis_summary.json',dict(passing_groups=result['passing_groups'],exploration_ready=result['exploration_ready'],final=concise));print((OUT/'analysis_summary.json').read_text(),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','freeze','profile','run','confirm','analyze','audit'));a=p.parse_args().action
    if a=='audit':
        from .mutation_depth_audit import audit
        audit()
    else:globals()[a]()
if __name__=='__main__':main()
