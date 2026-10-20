"""V12W: fixed historical/synthetic mechanistic probes; no evolution or selection."""
import argparse,gzip,json,platform,resource,subprocess,time
from importlib.metadata import version
from .compatibility_map_data import *
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .exposure_genome import Individual,Genome
from .growth import Genome as Program
from .regulatory import Gene
from .exposure_selection import physical,organism,record
from .causal_dissection_study import PRIOR as V_PRIOR
from .routing_mechanism_study import Budget
from .routing_mechanism_audit import geometry
from .growth import replay_mutation
from .baselines import baseline
from .foundation_pair_confirm import normal_row

PRIOR=(*V_PRIOR,'causal_dissection')
CAP=720
EDIT_IDS=(9,10,11,12)
LOCI={9:132,10:106,11:234,12:207}
STORE=[13,2,58,0,0,0,18]
NO_STORE=[0,34,34,0,0,0,64]
BEFORE={9:[11,56,36,0,0,0,24],10:[15,62,5,0,0,2,64],11:[13,2,26,0,0,0,59],12:[0,18,25,0,0,0,12]}
AFTER={9:[17,45,6,0,0,0,64],11:[9,35,28,4,0,0,64],12:[10,51,63,54,0,0,39]}

def label(mask,store):
    return ('store/' if store else 'no_store/')+''.join(str(int(bool(mask&(1<<i)))) for i in range(4))

def construct(base,mask,store):
    # Keys remain the original d07 gene identities throughout every deletion.
    genes={i:g for i,g in enumerate(base.genome.genes)}
    assert genes[222].row()==STORE
    for edit,locus in LOCI.items():assert genes[locus].row()==BEFORE[edit]
    genes[222]=Gene(*(STORE if store else NO_STORE))
    for bit,edit in enumerate(EDIT_IDS):
        if not mask&(1<<bit):continue
        if edit==10:del genes[LOCI[edit]]
        else:genes[LOCI[edit]]=Gene(*AFTER[edit])
    return Individual('diagnostic/v12w/'+label(mask,store),Genome(Program(tuple(genes.values())),base.genome.exposure),base.identity,-1)

def prior_check():
    n=0
    for stage in PRIOR:
        for p,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;n+=1
    return n

def make_panel():
    from .causal_dissection_study import make_panel as v_panel
    v=read_compressed(ROOT/'results/causal_dissection/panel.json.gz');assert v==v_panel()
    names=('d07','d08','d12','fresh2','fresh2_root','carry1','broad_root','random68','intact')
    items={n:v['items'][n] for n in names};kinds={n:v['kinds'][n] for n in names};conditions={}
    base=Individual.load(items['d07'])
    for mask in range(16):
        for store in (False,True):
            name=label(mask,store);items[name]=construct(base,mask,store).save();kinds[name]='synthetic_mechanistic_probe'
            conditions[name]=dict(mask=mask,store=store,edits=[e for bit,e in enumerate(EDIT_IDS) if mask&(1<<bit)],
                original_loci=[LOCI[e] for bit,e in enumerate(EDIT_IDS) if mask&(1<<bit)],output_original_locus=222)
    models={};aliases={}
    for name,raw in items.items():
        pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[name]=pid
    assert len(models)==40 and len(items)==41
    for mask,store,old in ((0,True,'d07'),(0,False,'d07_no_store'),(15,True,'d12_restore_store'),(15,False,'d12_no_store')):
        assert Individual.load(items[label(mask,store)]).genome==Individual.load(v['items'][old]).genome
    return canonical(dict(items=items,models=models,aliases=aliases,kinds=kinds,conditions=conditions,
        edit_order=EDIT_IDS,loci=LOCI,V_informed=True,source_sha256=sha(ROOT/'results/causal_dissection/panel.json.gz'),
        historical_events={k:v['historical_events'][k] for k in ('d09','d10','d11','d12')}))

def warm(cases,panel):
    m=next(iter(cases.values())).maze;t=time.perf_counter()
    organism(panel['models'][panel['aliases']['d07']]).react(m.cells,m.w,m.h,m.start,m.goal)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(candidate_calls=1,baseline_calls=3,seconds=time.perf_counter()-t,case=m.case_id,readonly_bytes=True)

def prepare():
    assert not OUT.exists() and not FIXTURES.exists();OUT.mkdir();t=time.perf_counter()
    panel=make_panel();compressed_json(OUT/'panel.json.gz',panel)
    d=create(FIXTURE_SEED,'fixture',exclusions(),True);d.save(FIXTURES)
    write_json(OUT/'preparation.json',dict(candidate_calls=0,prior_hashes=prior_check(),geometry=geometry(d.cache,d.contexts,d.metadata),prior_layouts=d.previous_count,wall_seconds=time.perf_counter()-t))
    print(dict(models=len(panel['models']),identities=len(panel['items']),inputs=len(d.cache)),flush=True)

def schedules(panel,meta,fixture=False):
    for pid in panel['models']:
        for kind in ('structured','ordinary'):
            ids=[c for c,m in meta.items() if query_case(m,fixture) and m['family'].startswith('ordinary_')==(kind=='ordinary')]
            yield 'normal',pid,'normal',kind,ids

def evaluate(path,cases,meta,panel,fixture=False):
    b=Budget(180 if fixture else CAP);w=warm(cases,panel);complete=False;plans=list(schedules(panel,meta,fixture));expected=sum(len(x[-1]) for x in plans);t=time.perf_counter();profiles={};baseline_calls=0
    native={}
    try:
        with gzip.open(path/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for scope,pid,mode,kind,ids in plans:
                model=panel['models'][pid];org=organism(model);before=b.seconds;count=b.calls
                for cid in ids:
                    o=cases[cid];m=o.maze
                    r=b.call(lambda:org.react(m.cells,m.w,m.h,m.start,m.goal))
                    row=record(r,o)
                    logrow(log,dict(scope=scope,model=pid,mode=mode,row=row))
                profiles[f'{scope}|{pid}|{mode}|{kind}']=dict(calls=b.calls-count,seconds=b.seconds-before)
                print(json.dumps(dict(scope=scope,model=pid,mode=mode,kind=kind,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
                if sum(p.stat().st_size for p in path.rglob('*') if p.is_file())>2*2**30:raise OSError('2GiB artifacts')
        with gzip.open(path/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for cid,o in cases.items():
                    if not query_case(meta[cid],fixture):continue
                    m=o.maze;row=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));assert row['optimal'] or row['no_path'];logrow(log,dict(model=name,row=row));baseline_calls+=1
        assert b.calls==expected;complete=True
    finally:
        packet=dict(complete=complete,planned_calls=expected,budget=b.save(),warmup=w,profiles=profiles,baseline_calls=baseline_calls,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(path/'execution.json',packet)
    return packet

def projection(packet,repeats):
    return 2*sum(v['seconds']*(len(POSES)*repeats if k.endswith('|structured') else 8) for k,v in packet['profiles'].items())

def profile():
    assert not (FIXTURES/'execution.json').exists()
    p=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(FIXTURES);packet=evaluate(FIXTURES,cases,meta,p,True)
    projections={str(n):projection(packet,n) for n in (3,2)}
    chosen=next((n for n in (3,2) if projections[str(n)]<650),None)
    write_json(FIXTURES/'profile.json',dict(passed=packet['complete'] and chosen is not None,projected_seconds=projections.get(str(chosen)),projections=projections,safety_factor=2,contexts_per_shape=chosen,scores_used_for_schedule=False,rule='First of 12 then 8 independent contexts fitting650seconds with2x safety; four fixed structured poses and all eight ordinary poses.'))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def freeze():
    assert not (OUT/'preregistration.json').exists() and json.loads((FIXTURES/'profile.json').read_text())['passed']
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/COMPATIBILITY_MAP_V12W.md',ROOT/'tests/test_compatibility_map.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
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
        for name in ('panel.json.gz','preregistration.json'):assert subprocess.check_output(['git','show',f'HEAD:results/compatibility_map/{name}'])==(OUT/name).read_bytes()
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
        from .compatibility_map_analysis import analyze
        analyze()
    elif action=='audit':
        from .compatibility_map_audit import audit
        audit()
    else:globals()[action]()

if __name__=='__main__':main()
