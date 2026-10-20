"""V12V: fixed historical/synthetic mechanistic probes; no evolution or selection."""
import argparse,gzip,json,platform,resource,subprocess,time
from importlib.metadata import version
from .causal_dissection_data import *
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .exposure_genome import Individual,Genome
from .growth import Genome as Program
from .regulatory import Gene
from .exposure_selection import physical,organism,record
from .lineage_mapping_study import PRIOR as U_PRIOR
from .routing_mechanism_study import Budget
from .causal_dissection_runtime import respond
from .routing_mechanism_audit import geometry
from .growth import replay_mutation
from .baselines import baseline
from .foundation_pair_confirm import normal_row

PRIOR=(*U_PRIOR,'lineage_mapping')
MODES=('channel4_zero','channel4_restore')
EARLY=('d00','d01','d02','dest_only')
CAP=720

def prior_check():
    n=0
    for stage in PRIOR:
        for p,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;n+=1
    return n

def make_panel():
    from .lineage_mapping_study import make_panel as historical_panel
    u=read_compressed(ROOT/'results/lineage_mapping/panel.json.gz')
    assert historical_panel()==u
    historical=('d00','d01','d02','d07','d08','d12','fresh2','fresh2_root','carry1','broad_root','random68','intact')
    items={n:u['items'][n] for n in historical};kinds={n:'historical_random_origin' for n in historical};kinds['intact']='known_control';events={}
    for name,base,index,before,after in (
        ('dest_only','d00',103,[15,44,3,0,0,3,64],[15,32,3,0,0,3,64]),
        ('d07_no_store','d07',222,[13,2,58,0,0,0,18],[0,34,34,0,0,0,64]),
        ('d12_restore_store','d12',221,[8,34,40,39,0,0,64],[13,2,58,0,0,0,18]),
        ('d12_no_store','d12',221,[8,34,40,39,0,0,64],[0,34,34,0,0,0,64])):
        parent=Individual.load(items[base]);genes=list(parent.genome.program.genes);assert genes[index].row()==before
        genes[index]=Gene(*after);probe=Individual('diagnostic/v12v/'+name,Genome(Program(tuple(genes)),parent.genome.exposure),parent.identity,-1)
        items[name]=probe.save();kinds[name]='synthetic_mechanistic_probe'
        events[name]=dict(parent_alias=base,parent_id=parent.identity,index=index,before=before,after=after,not_evolution=True)
    models={};aliases={}
    for name,raw in items.items():
        pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[name]=pid
    assert len(models)==len(items)==16
    return canonical(dict(items=items,models=models,aliases=aliases,kinds=kinds,synthetic_events=events,
        U_informed=True,source_sha256=sha(ROOT/'results/lineage_mapping/panel.json.gz'),historical_events=u['events']))

def warm(cases,panel):
    m=next(iter(cases.values())).maze;model=panel['models'][panel['aliases']['d01']];t=time.perf_counter()
    organism(model).react(m.cells,m.w,m.h,m.start,m.goal)
    for mode in ('normal',*MODES):respond(model,m,mode)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(candidate_calls=4,baseline_calls=3,seconds=time.perf_counter()-t,case=m.case_id,readonly_bytes=True)

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();t=time.perf_counter()
    panel=make_panel();compressed_json(OUT/'panel.json.gz',panel)
    d=create(FIXTURE_SEED,'fixture',exclusions(),True);d.save(FIXTURES)
    write_json(OUT/'preparation.json',dict(candidate_calls=0,prior_hashes=prior_check(),geometry=geometry(d.cache,d.contexts,d.metadata),prior_layouts=d.previous_count,wall_seconds=time.perf_counter()-t))
    print(dict(models=len(panel['models']),identities=len(panel['items']),inputs=len(d.cache)),flush=True)

def schedules(panel,meta,fixture=False):
    for pid in panel['models']:
        for kind in ('structured','ordinary'):
            ids=[c for c,m in meta.items() if normal_case(m) and m['family'].startswith('ordinary_')==(kind=='ordinary') and (not fixture or m['pose']==0)]
            yield 'normal',pid,'normal',kind,ids
    # All native responses finish before any diagnostic response.
    targets={panel['aliases'][n] for n in EARLY}
    for mode in MODES:
        for pid in panel['models']:
            if pid not in targets:continue
            ids=[c for c,m in meta.items() if mechanism_case(m) and (not fixture or m['pose']==0)]
            yield 'intervention',pid,mode,'mechanism',ids
    if fixture:
        for pid in panel['models']:
            yield 'parity',pid,'normal','parity',[c for c,m in meta.items() if normal_case(m) and m['pose']==0]

def evaluate(path,cases,meta,panel,fixture=False):
    b=Budget(180 if fixture else CAP);w=warm(cases,panel);complete=False;plans=list(schedules(panel,meta,fixture));expected=sum(len(x[-1]) for x in plans);t=time.perf_counter();profiles={};baseline_calls=0
    native={}
    try:
        with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for scope,pid,mode,kind,ids in plans:
                model=panel['models'][pid];org=organism(model);before=b.seconds;count=b.calls
                for cid in ids:
                    o=cases[cid];m=o.maze
                    if scope=='normal':r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal))
                    else:r=b.call(lambda:respond(model,m,mode).reaction)
                    row=record(r,o)
                    if fixture and scope=='normal':native[pid,cid]=row
                    if scope=='parity':assert row==native[pid,cid]
                    logrow(log,dict(scope=scope,model=pid,mode=mode,row=row))
                profiles[f'{scope}|{pid}|{mode}|{kind}']=dict(calls=b.calls-count,seconds=b.seconds-before)
                print(json.dumps(dict(scope=scope,model=pid,mode=mode,kind=kind,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
                if sum(p.stat().st_size for p in path.rglob('*') if p.is_file())>2*2**30:raise OSError('2GiB artifacts')
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for cid,o in cases.items():
                    if not normal_case(meta[cid]) or fixture and meta[cid]['pose']!=0:continue
                    m=o.maze;row=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert row['optimal'] or row['no_path'];logrow(log,dict(model=name,row=row));baseline_calls+=1
        assert b.calls==expected;complete=True
    finally:
        packet=dict(complete=complete,planned_calls=expected,budget=b.save(),warmup=w,profiles=profiles,baseline_calls=baseline_calls,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(path/'execution.json',packet)
    return packet

def projection(packet,repeats):
    return 2*sum(v['seconds']*(8*repeats if k.endswith('|structured') else 8) for k,v in packet['profiles'].items() if not k.startswith('parity|'))

def profile():
    assert not (FIXTURES/'execution.json').exists()
    p=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(FIXTURES);packet=evaluate(FIXTURES,cases,meta,p,True)
    projections={str(n):projection(packet,n) for n in (3,2)}
    chosen=next((n for n in (3,2) if projections[str(n)]<650),None)
    write_json(FIXTURES/'profile.json',dict(passed=packet['complete'] and chosen is not None,projected_seconds=projections.get(str(chosen)),projections=projections,safety_factor=2,contexts_per_shape=chosen,scores_used_for_schedule=False,rule='First of 12 then 8 contexts fitting650seconds with2x safety; diagnostic subset fixed4contexts plus ordinary.'))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def freeze():
    assert not (OUT/'preregistration.json').exists() and json.loads((FIXTURES/'profile.json').read_text())['passed']
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/CAUSAL_DISSECTION_V12V.md',ROOT/'tests/test_causal_dissection.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    inputs=[p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file() and p.suffix!='.log']
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,final_generated=False,cap_candidate_seconds=CAP,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        python=platform.python_version(),platform=platform.platform(),cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')}))

def check_freeze(committed=False):
    reg=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for p,h in reg[group].items():assert sha(ROOT/p)==h,p
    if committed:
        assert subprocess.check_output(['git','rev-parse','HEAD'])==subprocess.check_output(['git','rev-parse','origin/main'])
        for name in ('panel.json.gz','preregistration.json'):assert subprocess.check_output(['git','show',f'HEAD:results/causal_dissection/{name}'])==(OUT/name).read_bytes()
    return reg

def run():
    check_freeze(True);path=OUT/'confirmation';assert not path.exists()
    old=exclusions();fc,_,_=load(FIXTURES);old.update(layout_hash(o.maze) for o in fc.values())
    d=create(SEED,'confirmation',old);d.save(path)
    write_json(path/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),geometry=geometry(d.cache,d.contexts,d.metadata),prior_layouts=d.previous_count,whole_layouts=len(d.layouts),rejections=d.rejections,hashes={str(p.relative_to(ROOT)):sha(p) for p in path.iterdir() if p.is_file()}))
    evaluate(path,d.cache,d.metadata,read_compressed(OUT/'panel.json.gz'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','profile','freeze','run','analyze','audit']);action=parser.parse_args().action
    if action=='analyze':
        from .causal_dissection_analysis import analyze
        analyze()
    elif action=='audit':
        from .causal_dissection_audit import audit
        audit()
    else:globals()[action]()

if __name__=='__main__':main()
