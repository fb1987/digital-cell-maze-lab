"""V12P fixed saved lineage; no breeding, reselection or new candidate edits."""
import argparse,gzip,json,platform,resource,subprocess,time
from importlib.metadata import version
from .foundation_calibration import ROOT,LIMITS,write_json
from .foundation_study import read_compressed,compressed_json
from .exposure_genome import Individual,Genome
from .exposure_selection import physical,record,organism as native_organism
from .growth import Individual as OldIndividual,replay_mutation
from .mutation_transition_runtime import Organism
from .mutation_transition_data import *
from .routing_transfer import sha,canonical,logrow,lines
from .foundation_pair_confirm import normal_row
from .baselines import baseline

MODES=dict(normal=(True,True,True,False),pulse_off=(False,True,True,False),flag_off=(True,False,True,False),
           both_off=(False,False,True,False),endpoint_off=(True,True,False,False),nonlocal_off=(True,True,True,True))
CAP=720
CALL_CAP=1500000
WORK_CAP=1200000000000
PRIOR=('fork_pressure','routing_transfer','validation_breadth','junction_distance','robustness_pressure','lineage_confirmation','exposure_calibration','branch_pressure_calibration','mutation_depth')


def make_panel():
    old=read_compressed(ROOT/'results/mutation_depth/pools.json.gz');events=read_compressed(ROOT/'results/mutation_depth/events.json.gz')
    items={};chains={};selected_events=[]
    for label,rep,index,walk,depths in [('route',0,71,0,list(range(1,17))),('reach1',1,53,0,[1,4,16]),('reach2',2,69,1,[1,4,16])]:
        root=f'exposure/fresh/{rep}/founder{index}';items[label+'/d0']=old['entries'][root]['item'];chains[label]=[label+'/d0'];current=Individual.load(items[label+'/d0'])
        for event in events:
            if (event['kind'],event['rep'],event['index'],event['walk'])!=('walk',rep,index,walk):continue
            child=Individual.load(event['item']);assert child.parent==current.identity
            assert replay_mutation(current.genome.program,event['event'],256)==child.genome.program
            selected_events.append(event);current=child
            if event['depth'] in depths:
                alias=f'{label}/d{event["depth"]}';items[alias]=child.save();chains[label].append(alias)
    for rep,ids in old['anchors'].items():
        for k,i in enumerate(ids):items[f'anchor{rep}/{k}']=old['entries'][i]['item']
    sel=read_compressed(ROOT/'results/mutation_depth/selections.json.gz');resample=sel['2/local']['resample']['best'];items['resample']=old['entries'][resample]['item']
    known=OldIndividual.load(read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')['intact']['item'])
    items['intact']=Individual(known.identity,Genome(known.genome,7),None,0).save()
    models={};aliases={};mechanisms=set()
    for top in ('local','evolved'):
        for label,raw in items.items():
            key,model=physical(Individual.load(raw),'neutral',top);models[key]=model;aliases[f'{top}/{label}']=key
            if label in ('route/d0','route/d4','route/d15','route/d16','intact'):mechanisms.add(key)
    return canonical(dict(items=items,chains=chains,events=selected_events,aliases=aliases,mechanisms=sorted(mechanisms),models=models,O_informed=True))


def organism(model,mode='normal'):
    pulse,flag,endpoint,ablate=MODES[mode]
    return Organism(Genome.from_dict(model['genome']),'active',model['topology'],LIMITS,pulse,flag,endpoint,ablate)


class Budget:
    def __init__(self,seconds=CAP,calls=CALL_CAP,work=WORK_CAP):
        self.cap_seconds=seconds;self.cap_calls=calls;self.cap_work=work;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
    def call(self,fn):
        if self.calls>=self.cap_calls or self.seconds>=self.cap_seconds-max(.5,2*self.maximum) or self.work>=self.cap_work:
            raise TimeoutError('Closed V12P cap; no extension')
        if self.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('V12P 4GiB cap')
        start=time.perf_counter();r=fn();dt=time.perf_counter()-start;self.seconds+=dt;self.calls+=1;self.maximum=max(self.maximum,dt)
        self.work+=r.spatial_reads+r.dispatches+r.exposure_checks
        assert self.seconds<self.cap_seconds and self.work<=self.cap_work
        return r
    def save(self):return vars(self).copy()


def prepare():
    assert not OUT.exists() and not FIXTURES.exists();t=time.perf_counter();OUT.mkdir();panel=make_panel();compressed_json(OUT/'panel.json.gz',panel)
    d=create(FIXTURE_SEED,'fixture',exclusions(),1);assert d.previous_count==178232;d.save(FIXTURES)
    from .mutation_transition_audit import geometry
    g=geometry(d.cache,d.contexts,d.metadata)
    write_json(OUT/'preparation.json',dict(wall_seconds=time.perf_counter()-t,models=len(panel['models']),aliases=len(panel['aliases']),mechanism_models=len(panel['mechanisms']),geometry=g,candidate_calls=0))
    print((OUT/'preparation.json').read_text(),flush=True)


def freeze():
    assert not (OUT/'preregistration.json').exists()
    sources=[ROOT/'cellular_maze_lab.py',ROOT/'docs/MUTATION_TRANSITION_V12P.md',ROOT/'tests/test_mutation_transition.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for path in (OUT,FIXTURES) for p in path.rglob('*') if p.is_file() and p.suffix!='.log']
    inputs += [ROOT/'results/mutation_depth'/name for name in ('pools.json.gz','events.json.gz','walks.json.gz','selections.json.gz','completion.json')]
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,sources={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        platform=platform.platform(),python=platform.python_version(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')},main_generated=False))


def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for name,h in p[group].items():assert sha(ROOT/name)==h,name
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        assert subprocess.check_output(['git','show','HEAD:results/mutation_transition/preregistration.json'])==(OUT/'preregistration.json').read_bytes()
    return p


def warm(cases,panel):
    m=next(iter(cases.values())).maze;model=panel['models'][panel['aliases']['local/intact']];t=time.perf_counter()
    for mode in MODES:organism(model,mode).react(m.cells,m.w,m.h,m.start,m.goal)
    native_organism(model).react(m.cells,m.w,m.h,m.start,m.goal)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(candidate_calls=len(MODES)+1,baseline_calls=3,seconds=time.perf_counter()-t,case=m.case_id,readonly_bytes=True)


def schedule(panel,meta,fixture=False):
    for mode in MODES:
        for key in sorted(panel['models'] if mode=='normal' else panel['mechanisms']):
            ids=[cid for cid,m in meta.items() if (not fixture or m['pose']==0) and (mode=='normal' or mechanism_case(m))]
            yield key,mode,ids


def profile():
    check_freeze(True);assert not (FIXTURES/'profile.json').exists();t=time.perf_counter();cases,contexts,meta=load(FIXTURES);panel=read_compressed(OUT/'panel.json.gz');warmup=warm(cases,panel);b=Budget(120,150000);profiles={};parity=0
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for key,mode,ids in schedule(panel,meta,True):
            org=organism(panel['models'][key],mode);native=native_organism(panel['models'][key]);before=b.seconds;work=b.work
            normal_seconds=0.;normal_work=0
            for cid in ids:
                o=cases[cid];m=o.maze;ts=b.seconds;ws=b.work;r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));normal_seconds+=b.seconds-ts;normal_work+=b.work-ws
                row=record(r,o);logrow(log,dict(model=key,mode=mode,row=row))
                if mode=='normal' and meta[cid]['family']=='paired':
                    rr=b.call(lambda:native.react(m.cells,m.w,m.h,m.start,m.goal));assert record(rr,o)==row;logrow(log,dict(model=key,mode='native_parity',row=record(rr,o)));parity+=1
            profiles[f'{key}/{mode}']=dict(seconds=normal_seconds,work=normal_work,calls=len(ids))
            print(json.dumps(dict(mode=mode,model=key,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
    projected=16*sum(v['seconds'] for v in profiles.values());calls=16*sum(v['calls'] for v in profiles.values());work=16*sum(v['work'] for v in profiles.values())
    packet=dict(passed=projected<648 and calls<=CALL_CAP and work<.9*WORK_CAP,projected_seconds=projected,projected_calls=calls,projected_work=work,profiles=profiles,parity_checks=parity,
        budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(FIXTURES/'profile.json',packet);print(json.dumps({k:v for k,v in packet.items() if k!='profiles'},indent=2),flush=True)


def run():
    check_freeze(True);profile=json.loads((FIXTURES/'profile.json').read_text());assert profile['passed'];assert not (OUT/'confirmation').exists()
    assert subprocess.check_output(['git','show','HEAD:results/mutation_transition_fixtures/profile.json'])==(FIXTURES/'profile.json').read_bytes()
    t=time.perf_counter();panel=read_compressed(OUT/'panel.json.gz');d=create(SEED,'confirmation',exclusions()+read_compressed(FIXTURES/'mazes.json.gz'),2);path=OUT/'confirmation';d.save(path)
    from .mutation_transition_audit import geometry
    g=geometry(d.cache,d.contexts,d.metadata);planned=sum(len(ids) for _,_,ids in schedule(panel,d.metadata));assert planned==profile['projected_calls']
    write_json(path/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),geometry=g,planned_calls=planned,prior_layouts=d.previous_count,whole_layouts=len(d.layouts),rejections=d.rejections,hashes={str(p.relative_to(ROOT)):sha(p) for p in path.glob('*.gz')}))
    fc,_,_=load(FIXTURES);warmup=warm(fc,panel);b=Budget();bc=0;complete=False
    try:
        with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for key,mode,ids in schedule(panel,d.metadata):
                org=organism(panel['models'][key],mode)
                for cid in ids:
                    o=d.cache[cid];m=o.maze;r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));row=record(r,o);logrow(log,dict(model=key,mode=mode,row=row))
                    if mode=='normal' and key in (panel['aliases']['local/intact'],panel['aliases']['evolved/intact']):assert row['optimal'] or row['no_path']
                if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:raise OSError('V12P 2GiB output cap')
                print(json.dumps(dict(mode=mode,model=key,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for o in d.cache.values():
                    m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert r['optimal'] or r['no_path'];logrow(log,dict(model=name,row=r));bc+=1
        complete=True
    finally:write_json(path/'execution.json',dict(complete=complete,planned_calls=planned,budget=b.save(),baseline_calls=bc,warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','freeze','profile','run','analyze','audit'));action=p.parse_args().action
    if action=='audit':
        from .mutation_transition_audit import audit
        audit()
    elif action=='analyze':
        from .mutation_transition_analysis import analyze
        analyze()
    else:globals()[action]()
if __name__=='__main__':main()
