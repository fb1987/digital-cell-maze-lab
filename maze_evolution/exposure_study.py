"""V12M staged software, frozen neighborhoods, selection and independent confirmation."""
import argparse,json,gzip,time,random,platform,resource,subprocess
from dataclasses import replace,asdict
from collections import defaultdict
from importlib.metadata import version
from .foundation_calibration import ROOT,LIMITS,write_json
from .foundation_study import read_compressed,compressed_json
from .growth import Individual as OldIndividual,random_genome
from .growth_runtime import Organism as OldOrganism
from .exposure_genome import Genome,Individual,mutate,replay
from .exposure_runtime import Organism,ARMS
from .exposure_selection import physical,organism,record,choose,stats
from .routing_transfer import sha,canonical,lines,logrow
from .datasets import seed_for
from .baselines import baseline
from .exposure_data import *

CARRY_NAMES=('branch_narrow','branch_broad','long_prefix','long_replacement','local_long','local_cycle',
             'fresh_evolved','fresh_local','fresh_local_narrow','resampled','branch_narrow_parent','branch_broad_parent',
             'shared_ancestor','k2_target','k2_parent','k2_entry')
CAL_CAP=480
FINAL_CAP=300


class Budget:
    def __init__(self,seconds,calls):self.cap_seconds=seconds;self.cap_calls=calls;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
    def call(self,fn):
        if self.calls>=self.cap_calls or self.seconds>=self.cap_seconds-max(.25,2*self.maximum):raise TimeoutError('Closed V12M cap; preserve partial results, no extension')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('V12M 4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t
        self.seconds+=dt;self.calls+=1;self.maximum=max(self.maximum,dt)
        self.work+=r.dispatches+r.spatial_reads+getattr(r,'exposure_checks',0)
        assert self.seconds<self.cap_seconds
        return r
    def save(self):return vars(self).copy()


def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir()
    old=read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz');pools={};provenance={};events=[]
    for name in CARRY_NAMES:
        item=OldIndividual.load(old[name]['item']);key='carry/'+name;items=[]
        for mask in range(8):items.append(Individual(f'exposure/{key}/mask{mask}',Genome(item.genome,mask),item.identity,0).save())
        base=Individual.load(items[7]);rng=random.Random(seed_for(SEED,'neighborhood',CARRY_NAMES.index(name),0));before=rng.getstate()
        for k in range(8):
            genome,event=mutate(base.genome,rng);child=Individual(f'exposure/{key}/mutation{k}',genome,base.identity,1)
            assert replay(base.genome,event)==genome;items.append(child.save());events.append(dict(pool=key,item=child.save(),event=event))
        pools[key]=dict(origin='carry',topology=old[name]['topology'],items=items,base_id=base.identity)
        provenance[key]=dict(source=old[name],rng_before=before,rng_after=rng.getstate(),enumerated_masks_are_interventions=True)
    for rep in range(3):
        key=f'fresh/{rep}';rng=random.Random(seed_for(SEED,'fresh_programs',rep,0));bits=random.Random(seed_for(SEED,'fresh_bits',rep,0));before=(rng.getstate(),bits.getstate());items=[]
        for k in range(96):items.append(Individual(f'exposure/{key}/founder{k}',Genome(random_genome(rng,True),bits.randrange(8)),None,0).save())
        pools[key]=dict(origin='fresh',topology='evolved',items=items,base_id=items[0]['id'])
        provenance[key]=dict(program_rng_before=before[0],bit_rng_before=before[1],program_rng_after=rng.getstate(),bit_rng_after=bits.getstate())
    models={};aliases={}
    for key,p in pools.items():
        aliases[key]={}
        for arm in ARMS:
            aliases[key][arm]={}
            for raw in p['items']:
                item=Individual.load(raw);pid,m=physical(item,arm,p['topology']);models[pid]=m;aliases[key][arm][item.identity]=pid
    for name,value in [('pools',pools),('provenance',provenance),('events',events),('models',models),('aliases',aliases)]:compressed_json(OUT/f'{name}.json.gz',value)
    write_json(OUT/'pool_freeze.json',dict(L_informed=True,source='results/lineage_confirmation/panel.json.gz',source_sha256=sha(ROOT/'results/lineage_confirmation/panel.json.gz'),
        saved={str(p.relative_to(ROOT)):sha(p) for p in OUT.glob('*.gz')},seed=SEED,known_control_in_pools=False,
        pool_count=len(pools),logical_genotypes=sum(len(p['items']) for p in pools.values()),physical_models=len(models),candidate_calls=0))
    # Entire pool is fixed before any new fixture geometry or candidate response.
    data=create_data(FIXTURE_SEED,'fixture',exclusions(),False);save_data(data,FIXTURES)
    print(json.dumps(dict(pools=len(pools),models=len(models),carry_models=len({x for k,p in pools.items() if p['origin']=='carry' for arm in ARMS for x in aliases[k][arm].values()}),fresh_models=len({x for k,p in pools.items() if p['origin']=='fresh' for arm in ARMS for x in aliases[k][arm].values()}))),flush=True)


def create_data(seed,split,previous,final=False):
    carry=LineageData(seed,previous);carry_corpus(carry,split+'/carry',final)
    fresh=ElementaryData(seed,previous+manifest(carry.cache.values()));fresh_corpus(fresh,split+'/fresh',final)
    return dict(carry=carry,fresh=fresh)


def ids_for(data,origin,final=False,profile=False,selection=False):
    if origin=='carry':
        ids=carry_ids(data,False,profile)
        if selection:ids=[cid for cid in ids if data.metadata[cid]['pose'] in (0,4)]
        if final:ids=[cid for cid,m in data.metadata.items() if m['position']==m['index']%2 and m['pose'] in (0,2,4,6)]
        return ids
    return fresh_ids(data,final,profile)


def save_data(data,path):
    for origin,d in data.items():d.save(path/origin)


def load_data(path):
    return {origin:load(path/origin) for origin in ('carry','fresh')}


def all_manifests(path):return sum((read_compressed(path/origin/'mazes.json.gz') for origin in ('carry','fresh')),[])


def warm(data):
    panel=read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz');i=OldIndividual.load(panel['intact']['item']);m=next(iter(data['carry'].cache.values())).maze;t=time.perf_counter()
    Organism(Genome(i.genome,7),'active','local',LIMITS).react(m.cells,m.w,m.h,m.start,m.goal)
    OldOrganism(i.genome,'local',LIMITS,goal_pulse=True).react(m.cells,m.w,m.h,m.start,m.goal)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(seconds=time.perf_counter()-t,candidate_calls=2,baseline_calls=3,case=m.case_id,read_only=True)


def model_origins(pools,aliases):
    out=defaultdict(set)
    for key,p in pools.items():
        for arm in ARMS:out[p['origin']].update(aliases[key][arm].values())
    return {k:sorted(v) for k,v in out.items()}


def calibrate():
    from .exposure_audit import geometry
    assert not (FIXTURES/'calibration.json').exists();t=time.perf_counter()
    loaded=load_data(FIXTURES);data={}
    for origin,(cases,contexts,meta) in loaded.items():
        d=type('Loaded',(),{})();d.cache=cases;d.contexts=contexts;d.metadata=meta;data[origin]=d
    g={o:geometry(*loaded[o],o) for o in loaded};warmup=warm(data)
    models=read_compressed(OUT/'models.json.gz');pools=read_compressed(OUT/'pools.json.gz');aliases=read_compressed(OUT/'aliases.json.gz')
    origins=model_origins(pools,aliases);b=Budget(240,130000);profiles={};parity=0
    with gzip.open(FIXTURES/'profiles.jsonl.gz','wt',compresslevel=1) as log:
        for origin,keys in origins.items():
            ids=ids_for(data[origin],origin,profile=True)
            for key in keys:
                org=organism(models[key]);start=b.seconds
                for cid in ids:
                    o=data[origin].cache[cid];m=o.maze;r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal))
                    logrow(log,dict(origin=origin,model=key,row=record(r,o)))
                profiles[origin+'|'+key]=dict(seconds=b.seconds-start,calls=len(ids))
            print(json.dumps(dict(profile_origin=origin,calls=b.calls,seconds=b.seconds)),flush=True)
    # Check both endpoints of the new mask against old production semantics on all
    # actual board/geometry strata; fresh samples are fixed founder positions.
    parity_items=[(k,Individual.load(p['items'][7 if p['origin']=='carry' else 0]),p['topology'],p['origin']) for k,p in pools.items()]
    control=OldIndividual.load(read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')['intact']['item'])
    parity_items.append(('intact',Individual('positive_control/intact',Genome(control.genome,7),None,0),'local','carry'))
    with gzip.open(FIXTURES/'parity.jsonl.gz','wt',compresslevel=1) as log:
        for key,item,top,origin in parity_items:
            ids=ids_for(data[origin],origin,profile=True)
            for mask in (0,7):
                new=Organism(Genome(item.genome.program,mask),'active',top,LIMITS)
                old=OldOrganism(item.genome.program,top,LIMITS,ablate_nonlocal=mask==0,goal_pulse=True)
                for cid in ids:
                    o=data[origin].cache[cid];m=o.maze;a=b.call(lambda:new.react(m.cells,m.w,m.h,m.start,m.goal));z=b.call(lambda:old.react(m.cells,m.w,m.h,m.start,m.goal))
                    nr,oldrow=record(a,o),normal_old(z,o);assert {k:v for k,v in nr.items() if k not in ('exposure_checks','suppressed_reads','array_bytes')}=={k:v for k,v in oldrow.items() if k!='array_bytes'}
                    assert nr['array_bytes']==oldrow['array_bytes']+17;parity+=1
                    logrow(log,dict(pool=key,item=item.save(),topology=top,mask=mask,origin=origin,row=nr,old=oldrow))
    # Performance-only projections; all scientific pools/queries remain fixed.
    main_projection=4*sum(v['seconds'] for v in profiles.values())
    validation_upper=0.;final_upper=0.
    for key,p in pools.items():
        origin=p['origin'];rates=[profiles[origin+'|'+pid]['seconds']/profiles[origin+'|'+pid]['calls'] for arm in ARMS for pid in aliases[key][arm].values()]
        rate=max(rates);validation_upper+=8*(360 if origin=='carry' else 144)*rate
        final_upper+=10*(480 if origin=='carry' else 1152)*rate
    packet=dict(passed=main_projection+validation_upper<432 and final_upper<270,geometry=g,warmup=warmup,budget=b.save(),parity_comparisons=parity,
        profiles=profiles,projected_calibration_seconds=main_projection,validation_upper_seconds=validation_upper,final_upper_seconds=final_upper,
        wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(FIXTURES/'calibration.json',packet);print(json.dumps({k:v for k,v in packet.items() if k not in ('profiles','geometry')},indent=2),flush=True)


def normal_old(r,o):
    from .foundation_pair_confirm import normal_row
    return canonical(normal_row(r,o))


def revised_profile(packet):
    carry=2*sum(v['seconds'] for k,v in packet['profiles'].items() if k.startswith('carry|'))
    fresh=4*sum(v['seconds'] for k,v in packet['profiles'].items() if k.startswith('fresh|'))
    return dict(passed=carry+fresh+packet['validation_upper_seconds']<432 and packet['final_upper_seconds']<270,
        original_profile_sha256=sha(FIXTURES/'calibration.json'),original_gate_passed=False,
        reason='Performance-only pre-registration reduction: carried calibration poses 0/4; unchanged validation/final/fresh/pools/readiness gates.',
        new_candidate_calls=0,projected_calibration_seconds=carry+fresh,validation_upper_seconds=packet['validation_upper_seconds'],
        final_upper_seconds=packet['final_upper_seconds'],projected_calibration_validation_seconds=carry+fresh+packet['validation_upper_seconds'],
        carry_calibration_poses=[0,4],other_selection_poses=[0,2,4,6])


def freeze():
    assert not (OUT/'preregistration.json').exists();assert json.loads((FIXTURES/'calibration_revised.json').read_text())['passed']
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/EXPOSURE_CALIBRATION_V12M.md',ROOT/'tests/test_exposure_calibration.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,calibration_validation_cap=CAL_CAP,confirmation_cap=FINAL_CAP,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},inputs={str(p.relative_to(ROOT)):sha(p) for d in (OUT,FIXTURES) for p in d.rglob('*') if p.is_file() and p.suffix!='.log'},
        main_generated=False,platform=platform.platform(),python=platform.python_version(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},limits=asdict(LIMITS)))


def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for path,h in p[group].items():assert sha(ROOT/path)==h,path
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'],text=True)==subprocess.check_output(['git','rev-parse','origin/main'],text=True)
        for f in ('preregistration.json','pools.json.gz','models.json.gz','aliases.json.gz'):
            assert subprocess.check_output(['git','show',f'HEAD:results/exposure_calibration/{f}'])==(OUT/f).read_bytes()
    return p


def run_assay(path,data,models,wanted_models,ids,budget):
    out={o:{} for o in wanted_models}
    with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for origin,keys in wanted_models.items():
            for key in sorted(keys):
                org=organism(models[key]);rows=[]
                for cid in ids[origin]:
                    o=data[origin].cache[cid];m=o.maze;r=budget.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));row=record(r,o);rows.append(row)
                    logrow(log,dict(origin=origin,model=key,row=row))
                out[origin][key]=rows
                if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:raise OSError('V12M output cap')
            print(json.dumps(dict(scope=path.name,origin=origin,calls=budget.calls,seconds=round(budget.seconds,2))),flush=True)
    return out


def generation(path,data,ids,models,wanted_models):
    save_data(data,path);compressed_json(path/'models.json.gz',models);compressed_json(path/'query.json.gz',dict(ids=ids,models={o:sorted(v) for o,v in wanted_models.items()}))
    write_json(path/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        prior_layouts=data['carry'].previous_count,new_layouts=len(data['fresh'].layouts)-data['carry'].previous_count,
        hashes={str(p.relative_to(ROOT)):sha(p) for p in path.rglob('*') if p.is_file()}))


def run():
    check_freeze(True);assert not (OUT/'calibration').exists();t=time.perf_counter();b=Budget(CAL_CAP,600000)
    pools=read_compressed(OUT/'pools.json.gz');aliases=read_compressed(OUT/'aliases.json.gz');models=read_compressed(OUT/'models.json.gz')
    previous=exclusions()+all_manifests(FIXTURES);data=create_data(SEED,'calibration',previous)
    wanted_models=model_origins(pools,aliases);ids={o:ids_for(d,o,selection=True) for o,d in data.items()};path=OUT/'calibration';generation(path,data,ids,models,wanted_models);warmup=warm(data)
    complete=False
    try:
        rows=run_assay(path,data,models,wanted_models,ids,b);choices={};validation_models=defaultdict(set)
        for index,(key,p) in enumerate(pools.items()):
            choices[key]={};origin=p['origin']
            for arm in ARMS:
                rr={i['id']:rows[origin][aliases[key][arm][i['id']]] for i in p['items']}
                choices[key][arm]={str(shaping):choose(p,rr,data[origin].metadata,seed_for(SEED,'reproduction',index,0),shaping) for shaping in (True,False)}
                for itemid in choices[key][arm]['True']['nominees']:validation_models[origin].add(aliases[key][arm][itemid])
        compressed_json(OUT/'calibration_choices.json.gz',choices)
        previous+=all_manifests(path);valid=create_data(seed_for(SEED,'validation',0,0),'validation',previous);vids={o:ids_for(d,o) for o,d in valid.items()}
        vp=OUT/'validation';generation(vp,valid,vids,models,validation_models);vr=run_assay(vp,valid,models,validation_models,vids,b);selections={}
        for index,(key,p) in enumerate(pools.items()):
            selections[key]={};origin=p['origin']
            for arm in ARMS:
                nominated=choices[key][arm]['True']['nominees'];small=dict(p,items=[i for i in p['items'] if i['id'] in nominated])
                rr={i['id']:vr[origin][aliases[key][arm][i['id']]] for i in small['items']}
                selected=choose(small,rr,valid[origin].metadata,seed_for(SEED,'validation_selection',index,0))
                selections[key][arm]=dict(item=next(i for i in p['items'] if i['id']==selected['best']),rank=selected['rank'],nominees=nominated)
        compressed_json(OUT/'selections.json.gz',selections);complete=True
    finally:
        write_json(OUT/'selection_execution.json',dict(complete=complete,budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def final_panel(pools,selections):
    models={};aliases={};by=defaultdict(set)
    for key,p in pools.items():
        aliases[key]={};base=Individual.load(next(i for i in p['items'] if i['id']==p['base_id']))
        specs=[('selected_'+arm,Individual.load(selections[key][arm]['item']),arm) for arm in ARMS]
        selected=Individual.load(selections[key]['active']['item'])
        specs += [('active_as_'+arm,selected,arm) for arm in ARMS]
        specs += [('base_'+arm,base,arm) for arm in ('neutral','zero','local')]
        for label,item,arm in specs:
            pid,m=physical(item,arm,p['topology']);models[pid]=m;by[p['origin']].add(pid)
            aliases[key][label]=dict(model=pid,item=item.save(),arm=arm)
    control=OldIndividual.load(read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')['intact']['item'])
    item=Individual(control.identity,Genome(control.genome,7),None,0);pid,m=physical(item,'local','local');models[pid]=m
    for origin in ('carry','fresh'):by[origin].add(pid)
    return models,aliases,{o:sorted(v) for o,v in by.items()},pid


def confirm():
    check_freeze(True);assert not (OUT/'confirmation').exists();assert json.loads((OUT/'selection_execution.json').read_text())['complete']
    assert subprocess.check_output(['git','show','HEAD:results/exposure_calibration/selections.json.gz'])==(OUT/'selections.json.gz').read_bytes()
    pools=read_compressed(OUT/'pools.json.gz');sel=read_compressed(OUT/'selections.json.gz');models,aliases,by,control=final_panel(pools,sel)
    previous=exclusions()+all_manifests(FIXTURES)+all_manifests(OUT/'calibration')+all_manifests(OUT/'validation')
    data=create_data(seed_for(SEED,'confirmation',0,0),'confirmation',previous,True);ids={o:ids_for(d,o,True) for o,d in data.items()}
    path=OUT/'confirmation';generation(path,data,ids,models,by);compressed_json(path/'aliases.json.gz',aliases);write_json(path/'control.json',dict(model=control))
    planned=sum(len(by[o])*len(ids[o]) for o in by);b=Budget(FINAL_CAP,planned);t=time.perf_counter();warmup=warm(data);complete=False;bc=0
    try:
        run_assay(path,data,models,by,ids,b)
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for origin in ('carry','fresh'):
                for name in ('compiled_bfs','compiled_astar','wave_bit'):
                    for cid in ids[origin]:
                        o=data[origin].cache[cid];m=o.maze;r=normal_old(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o)
                        assert r['optimal'] or r['no_path'];logrow(log,dict(origin=origin,model=name,row=r));bc+=1
        complete=True
    finally:
        write_json(path/'execution.json',dict(complete=complete,planned_calls=planned,budget=b.save(),baseline_calls=bc,warmup=warmup,
            wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','calibrate','freeze','run','confirm','audit','analyze'));a=p.parse_args().action
    if a=='audit':
        from .exposure_audit import audit
        audit()
    elif a=='analyze':
        from .exposure_analysis import analyze
        analyze()
    else:globals()[a]()

if __name__=='__main__':main()
