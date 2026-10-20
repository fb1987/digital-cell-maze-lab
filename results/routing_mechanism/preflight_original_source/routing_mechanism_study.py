"""V12T fixed-panel mechanism/transfer, no selection or reproduction."""
import argparse,gzip,json,platform,resource,subprocess,time,base64,zlib
from importlib.metadata import version
import numpy as np
from .routing_mechanism_data import *
from .routing_mechanism_runtime import respond,MODES,TRACE_MODES
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .exposure_genome import Individual,Genome
from .exposure_selection import physical,organism,record
from .composition_study import PRIOR as S_PRIOR
from .growth import replay_mutation
from .composition_operator import replay_splice
from .baselines import baseline
from .foundation_pair_confirm import normal_row

PRIOR=(*S_PRIOR,'composition_study')
CAP=720
CALL_CAP=400000
WORK_CAP=2000000000000
DESCENDANTS={'fresh0':'fresh/0/mutation/primary','fresh2':'fresh/2/mutation/primary',
             'carry0':'carry/0/mutation/primary','carry1':'carry/1/mutation/primary','spliced':'carry/0/recombination/primary'}
TRACE_TARGETS=(*DESCENDANTS,'intact')

def prior_check():
    n=0
    for stage in PRIOR:
        for p,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;n+=1
    return n

def make_panel():
    source=ROOT/'results/composition_study';choices=read_compressed(source/'choices.json.gz')
    founders={i['id']:i for p in read_compressed(source/'pools.json.gz').values() for i in p['items']}
    desc={name:choices['items'][a] for name,a in DESCENDANTS.items()}
    prefixes={i['id'].rsplit('/i',1)[0] for i in desc.values()};edges={}
    for e in lines(source/'reproduction.jsonl.gz'):
        if e['key'] in prefixes:
            for b in e['births']:edges[b['item']['id']]=b['parents']
    chains={};needed=set()
    for name,item in desc.items():
        todo=[item['id']];seen=set();roots=set()
        while todo:
            i=todo.pop()
            if i in seen:continue
            seen.add(i);parents=edges.get(i,[])
            if parents:todo.extend(parents)
            else:roots.add(i)
        chains[name]=dict(target=item['id'],nodes=sorted(seen),roots=sorted(roots));needed.update(seen)
    events={}
    for e in lines(source/'reproduction.jsonl.gz'):
        if e['key'] in prefixes:
            for b in e['births']:
                if b['item']['id'] in needed:events[b['item']['id']]=b
    registry={i:raw for i,raw in founders.items() if i in needed}
    registry.update({i:b['item'] for i,b in events.items()})
    assert set(registry)==needed
    for i,b in events.items():
        if not b['parents']:assert b['mutation'] is None and b['crossover'] is None;continue
        program=Individual.load(registry[b['parents'][0]]).genome.program
        if b['crossover'] is not None:program=replay_splice(program,Individual.load(registry[b['parents'][1]]).genome.program,b['crossover'])
        program=replay_mutation(program,b['mutation'],256)
        assert program==Individual.load(b['item']).genome.program,i
    items=dict(desc)
    for name in ('fresh0','fresh2'):
        assert len(chains[name]['roots'])==1;items[name+'_root']=registry[chains[name]['roots'][0]]
    for name,alias in [('narrow_root','branch_narrow'),('broad_root','branch_broad'),('shared_root','shared_ancestor'),('random68','resampled')]:items[name]=choices['items']['anchor/historical/'+alias]
    items['intact']=choices['items']['anchor/intact']
    assert set(chains['spliced']['roots'])=={items[k]['id'] for k in ('narrow_root','broad_root','shared_root')}
    models={};aliases={}
    for name,raw in items.items():
        pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[name]=pid
    return canonical(dict(items=items,models=models,aliases=aliases,chains=chains,registry=registry,events=events,S_informed=True))

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();t=time.perf_counter()
    p=make_panel();compressed_json(OUT/'panel.json.gz',p)
    print(json.dumps(dict(panel=len(p['models']),ancestry=len(p['events']),seconds=time.perf_counter()-t)),flush=True)
    d=create(FIXTURE_SEED,'fixture',exclusions());d.save(FIXTURES)
    from .routing_mechanism_audit import geometry
    g=geometry(d.cache,d.contexts,d.metadata)
    write_json(OUT/'preparation.json',dict(candidate_calls=0,prior_hashes=prior_check(),geometry=g,prior_layouts=d.previous_count,wall_seconds=time.perf_counter()-t))

class Budget:
    def __init__(self,cap=CAP):self.cap=cap;self.seconds=0.;self.calls=0;self.work=0;self.maximum=0.
    def call(self,fn):
        if self.seconds+max(.5,2*self.maximum)>=self.cap or self.calls>=CALL_CAP or self.work>=WORK_CAP:raise TimeoutError('Closed V12T budget')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('4GiB cap')
        t=time.perf_counter();r=fn();dt=time.perf_counter()-t;self.seconds+=dt;self.maximum=max(self.maximum,dt);self.calls+=1
        reaction=r.reaction if hasattr(r,'reaction') else r
        self.work+=reaction.spatial_reads+reaction.dispatches+reaction.exposure_checks
        assert self.seconds<self.cap and self.work<WORK_CAP
        return r
    def save(self):return vars(self).copy()

def pack_history(h):
    return dict(shape=list(h.shape),dtype='<u2',data=base64.b64encode(zlib.compress(h.astype('<u2',copy=False).tobytes(),1)).decode())

def unpack_history(v):return np.frombuffer(zlib.decompress(base64.b64decode(v['data'])),dtype='<u2').reshape(v['shape'])

def schedules(panel,meta,fixture=False):
    # Complete normal inference for the entire panel precedes every intervention.
    for mode in MODES:
        for pid in panel['models']:
            ids=[c for c,m in meta.items() if (not fixture or m['pose']==0) and (mode=='normal' or mechanism_case(m))]
            yield 'normal' if mode=='normal' else 'intervention',pid,mode,ids
    for mode in TRACE_MODES:
        for name in TRACE_TARGETS:
            ids=[c for c,m in meta.items() if trace_case(m) and (not fixture or m['pose']==0)]
            yield 'trace',panel['aliases'][name],mode,ids

def warm(cases,panel):
    m=next(iter(cases.values())).maze;model=panel['models'][panel['aliases']['intact']];t=time.perf_counter()
    organism(model).react(m.cells,m.w,m.h,m.start,m.goal)
    respond(model,m);respond(model,m,trace=True,forced=True)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(candidate_calls=3,baseline_calls=3,seconds=time.perf_counter()-t,case=m.case_id,readonly_bytes=True)

def evaluate(path,cases,meta,panel,fixture=False):
    b=Budget(180 if fixture else CAP);w=warm(cases,panel);complete=False;planned=sum(len(ids) for _,_,_,ids in schedules(panel,meta,fixture));t=time.perf_counter();profiles={};parity=0;baseline_calls=0
    # Fixture normal adapter parity is charged and logged separately.
    expected=planned+(sum(m['pose']==0 for m in meta.values())*len(panel['models']) if fixture else 0)
    try:
        with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for scope,pid,mode,ids in schedules(panel,meta,fixture):
                model=panel['models'][pid];org=organism(model);before=b.seconds;before_calls=b.calls
                for cid in ids:
                    o=cases[cid];m=o.maze
                    if scope=='normal':r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal));row=record(r,o)
                    else:
                        result=b.call(lambda:respond(model,m,mode,trace=scope=='trace',forced=scope=='trace'))
                        row=record(result.reaction,o)
                    e=dict(scope=scope,model=pid,mode=mode,row=row)
                    if scope=='trace':e.update(history=pack_history(result.history),instrumentation_bytes=result.instrumentation_bytes)
                    logrow(log,e)
                    if fixture and scope=='normal':
                        r=b.call(lambda:respond(model,m).reaction);check=record(r,o);assert check==row
                        logrow(log,dict(scope='parity',model=pid,mode='normal',row=check));parity+=1
                profiles[f'{scope}|{pid}|{mode}']=dict(calls=b.calls-before_calls,seconds=b.seconds-before)
                print(json.dumps(dict(scope=scope,model=pid,mode=mode,calls=b.calls,seconds=round(b.seconds,2),wall=round(time.perf_counter()-t,2))),flush=True)
                if sum(p.stat().st_size for p in path.rglob('*') if p.is_file())>2*2**30:raise OSError('2GiB artifact cap')
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for cid,o in cases.items():
                    if fixture and meta[cid]['pose']!=0:continue
                    m=o.maze;row=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert row['optimal'] or row['no_path'];logrow(log,dict(model=name,row=row));baseline_calls+=1
        assert b.calls==expected;complete=True
    finally:
        packet=dict(complete=complete,planned_calls=expected,budget=b.save(),warmup=w,profiles=profiles,adapter_parity=parity,baseline_calls=baseline_calls,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(path/'execution.json',packet)
    return packet

def profile():
    assert not (FIXTURES/'execution.json').exists()
    p=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(FIXTURES);packet=evaluate(FIXTURES,cases,meta,p,True)
    # 2x safety; final has 3x structured normal contexts and 8 poses, same
    # ordinary size and mechanism/trace context count. Normal includes adapter
    # parity in fixture cost, making this deliberately conservative.
    projected=sum(v['seconds']*(24 if k.startswith('normal|') else 8) for k,v in packet['profiles'].items())*2
    write_json(FIXTURES/'profile.json',dict(passed=packet['complete'] and projected<600,projected_seconds=projected,safety_factor=2,scores_used_for_schedule=False))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def freeze():
    assert not (OUT/'preregistration.json').exists() and json.loads((FIXTURES/'profile.json').read_text())['passed']
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/ROUTING_MECHANISM_V12T.md',ROOT/'tests/test_routing_mechanism.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file() and p.suffix!='.log']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,final_generated=False,cap_candidate_seconds=CAP,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        python=platform.python_version(),platform=platform.platform(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')}))

def check_freeze(committed=False):
    reg=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for p,h in reg[group].items():assert sha(ROOT/p)==h,p
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        for name in ('panel.json.gz','preregistration.json'):
            assert subprocess.check_output(['git','show',f'HEAD:results/routing_mechanism/{name}'])==(OUT/name).read_bytes()
    return reg

def run():
    check_freeze(True);path=OUT/'confirmation';assert not path.exists()
    old=exclusions();fc,_,_=load(FIXTURES);old.update(layout_hash(o.maze) for o in fc.values())
    d=create(SEED,'confirmation',old);d.save(path)
    from .routing_mechanism_audit import geometry
    g=geometry(d.cache,d.contexts,d.metadata)
    write_json(path/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),geometry=g,
        prior_layouts=d.previous_count,whole_layouts=len(d.layouts),rejections=d.rejections,hashes={str(p.relative_to(ROOT)):sha(p) for p in path.iterdir() if p.is_file()}))
    evaluate(path,d.cache,d.metadata,read_compressed(OUT/'panel.json.gz'))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','profile','freeze','run','analyze','audit'));action=p.parse_args().action
    if action=='analyze':
        from .routing_mechanism_analysis import analyze
        analyze()
    elif action=='audit':
        from .routing_mechanism_audit import audit
        audit()
    else:globals()[action]()

if __name__=='__main__':main()
