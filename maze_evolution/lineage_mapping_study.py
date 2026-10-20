"""V12U: exact historical lineage, no mutation, selection or native-runtime edits."""
import argparse,gzip,json,platform,resource,subprocess,time
from importlib.metadata import version
from .lineage_mapping_data import *
from .foundation_calibration import write_json
from .routing_transfer import canonical,sha,lines,logrow
from .exposure_genome import Individual
from .exposure_selection import physical,organism,record
from .routing_mechanism_study import PRIOR as T_PRIOR,Budget,warm
from .routing_mechanism_runtime import respond
from .routing_mechanism_audit import geometry
from .growth import replay_mutation
from .baselines import baseline
from .foundation_pair_confirm import normal_row

PRIOR=(*T_PRIOR,'routing_mechanism')
MODES=('pulse_off','flag_off','output_feedback_off','halt_off')
CHAIN=tuple(f'd{i:02}' for i in range(13))
TARGETS=(*CHAIN,'fresh2','carry1','intact')
CAP=720

def prior_check():
    n=0
    for stage in PRIOR:
        for p,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;n+=1
    return n

def make_panel():
    t=read_compressed(ROOT/'results/routing_mechanism/panel.json.gz');ids=[];cur=t['items']['carry0']['id']
    while True:
        ids.append(cur)
        if cur==t['items']['narrow_root']['id']:break
        e=t['events'][cur];assert len(e['parents'])==1 and e['crossover'] is None
        cur=e['parents'][0]
    ids.reverse();assert len(ids)==13 and set(ids)==set(t['chains']['carry0']['nodes'])
    items={name:t['registry'][i] for name,i in zip(CHAIN,ids)};events={}
    for name,previous in zip(CHAIN[1:],CHAIN):
        e=t['events'][items[name]['id']];p=Individual.load(items[previous]);q=Individual.load(items[name])
        assert replay_mutation(p.genome.program,e['mutation'],256)==q.genome.program
        assert p.genome.exposure==q.genome.exposure==7
        events[name]=e
    for name in ('fresh2','fresh2_root','carry1','broad_root','random68','intact'):items[name]=t['items'][name]
    models={};aliases={}
    for name,raw in items.items():
        pid,m=physical(Individual.load(raw),'neutral','local');models[pid]=m;aliases[name]=pid
    return canonical(dict(items=items,models=models,aliases=aliases,chain=list(CHAIN),events=events,T_informed=True,source_sha256=sha(ROOT/'results/routing_mechanism/panel.json.gz')))

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
    targets={panel['aliases'][n] for n in TARGETS}
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

def projection(packet):
    return 2*sum(v['seconds']*(16 if k.endswith('|structured') else 8) for k,v in packet['profiles'].items() if not k.startswith('parity|'))

def profile():
    assert not (FIXTURES/'execution.json').exists()
    p=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(FIXTURES);packet=evaluate(FIXTURES,cases,meta,p,True);projected=projection(packet)
    write_json(FIXTURES/'profile.json',dict(passed=packet['complete'] and projected<650,projected_seconds=projected,safety_factor=2,contexts=8,scores_used_for_schedule=False))
    print((FIXTURES/'profile.json').read_text(),flush=True)

def freeze():
    assert not (OUT/'preregistration.json').exists() and json.loads((FIXTURES/'profile.json').read_text())['passed']
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/LINEAGE_MAPPING_V12U.md',ROOT/'tests/test_lineage_mapping.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
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
        for name in ('panel.json.gz','preregistration.json'):assert subprocess.check_output(['git','show',f'HEAD:results/lineage_mapping/{name}'])==(OUT/name).read_bytes()
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
        from .lineage_mapping_analysis import analyze
        analyze()
    elif action=='audit':
        from .lineage_mapping_audit import audit
        audit()
    else:globals()[action]()

if __name__=='__main__':main()
