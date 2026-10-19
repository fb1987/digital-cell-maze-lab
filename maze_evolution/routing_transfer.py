"""V12H fixed-genome confirmation. No search, reselection or candidate editing."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from importlib.metadata import version
import gzip
import hashlib
import json
import platform
import resource
import statistics
import subprocess
import time

import numpy as np
from .baselines import baseline
from .datasets import manifest
from .evaluator import assess
from .foundation_calibration import ROOT, LIMITS, controls, write_json
from .foundation_data import layout_hash
from .foundation_fitness import correct_exit
from .foundation_pair_confirm import normal_row
from .foundation_study import read_compressed, compressed_json
from .growth import Individual
from .growth_runtime import Organism
from .route_confirmation import pack_history, unpack_history
from .route_confirmation_runtime import respond
from .routing_transfer_data import OUT, FIXTURES, SEED, CONSTRUCTION_SEED, FAMILIES, TransferData, exclusions, load

CAP_SECONDS = 600
HORIZON = 64
MODES = dict(normal=(True,True,'normal',False), pulse_off=(False,True,'normal',False),
    flag_off=(True,False,'normal',False), pulse_flag_off=(False,False,'normal',False),
    endpoint_off=(True,True,'source_only',False), all_goal_off=(False,False,'source_only',False),
    nonlocal_off=(True,True,'normal',True))
TRACE_MODES = ('normal','pulse_off','flag_off','pulse_flag_off')
MECHANISM_ALIASES = dict(
    carried='fork/carry/evolved/branch/evolution/0/archives',
    fresh_local='fork/fresh/local/branch/evolution/1/archives',
    fresh_evolved='fork/fresh/evolved/branch/evolution/1/archives',
    resampled='fork/fresh/evolved/current/resample/0/archives')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.loads(json.dumps(value))


def lines(path):
    with gzip.open(path,'rt') as f:
        for line in f:
            yield json.loads(line)


def logrow(log,row):
    log.write(json.dumps(row,separators=(',',':'))+'\n')


def organism(entry,mode='normal'):
    pulse,flag,halt,ablate = MODES[mode]
    return Organism(Individual.load(entry['item']).genome,entry['topology'],LIMITS,
                    goal_pulse=pulse,ablate_nonlocal=ablate)


def inference(org,m,mode='normal',trace=False):
    pulse,flag,halt,ablate = MODES[mode]
    args = (m.cells,m.w,m.h,m.start,m.goal)
    if trace:
        return respond(org,*args,goal_flag=flag,halt_mode='forced',trace=True,horizon=HORIZON)
    if flag and halt=='normal':
        return org.react(*args)
    return respond(org,*args,goal_flag=flag,halt_mode=halt).reaction


def record(reaction,o,meta):
    row = normal_row(reaction,o)
    if meta['family'] in FAMILIES:
        row['correct_exit'] = bool(correct_exit(reaction.mask,o,meta['side']))
    return row


def summarize(rows,metadata):
    groups = defaultdict(list)
    for r in rows:
        m = metadata[r['case']]
        groups[m['family'],m['band']].append(r)
    strata = {}
    for (family,band),part in groups.items():
        by_pair = defaultdict(list);by_base = defaultdict(list)
        for r in part:
            m = metadata[r['case']]
            by_pair[m['base'],m['symmetry']].append(r);by_base[m['base']].append(r)
        pairs = {k:len(v)==2 and all(r['optimal'] for r in v) for k,v in by_pair.items()} if family in FAMILIES else {}
        base_counts = {base:sum(pairs.get((base,s),False) for s in range(8)) for base in by_base} if pairs else {}
        strata[f'{family}/band{band}'] = dict(inputs=len(part),valid=sum(r['valid'] for r in part),
            optimal=sum(r['optimal'] for r in part),no_path=sum(r['no_path'] for r in part),
            false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in part),
            complete_pairs=sum(pairs.values()),any_contexts=sum(v>0 for v in base_counts.values()),
            all_pose_contexts=sum(v==8 for v in base_counts.values()),base_pair_counts=base_counts,
            strict_pairs=sum(len(v)==2 and all(r.get('correct_exit',False) for r in v) for v in by_pair.values()) if pairs else 0,
            failures=dict(Counter(r['failure'] for r in part if not r['optimal'] and not r['no_path'])))
    passed = all(strata.get(f'{f}/band1',{}).get('any_contexts',0)>=6
                 and strata.get(f'{f}/band1',{}).get('all_pose_contexts',0)>=2
                 for f in ('two_junction','alternate_cycle'))
    passed &= strata.get('fork/band1',{}).get('any_contexts',0)>=12
    return dict(inputs=len(rows),strata=strata,screen_pass=bool(passed),
        work=sum(max(0,r['reads'])+max(0,r['dispatches']) for r in rows),
        nonlocal_reads=sum(sum(r['range_reads'][1:]) for r in rows if len(r['range_reads'])==4 and r['range_reads'][0]>=0),
        max_array_bytes=max((r['array_bytes'] for r in rows),default=0))


class Budget:
    def __init__(self):
        self.seconds=0.;self.calls=0;self.work=0;self.max_call_seconds=0.;self.scopes={}

    def reserve(self):
        if self.seconds >= CAP_SECONDS-max(5.,2*self.max_call_seconds):
            raise TimeoutError('Fixed candidate-call cap reached; preserve partial packet')

    def charge(self,scope,seconds,result,count=1):
        r = result.reaction if hasattr(result,'reaction') else result
        work = count*(max(0,r.spatial_reads)+max(0,r.instructions))
        self.seconds+=seconds;self.calls+=count;self.work+=work
        self.max_call_seconds=max(self.max_call_seconds,seconds/count)
        row=self.scopes.setdefault(scope,dict(seconds=0.,calls=0,work=0))
        row['seconds']+=seconds;row['calls']+=count;row['work']+=work
        assert self.seconds<CAP_SECONDS

    def call(self,scope,function):
        self.reserve();started=time.perf_counter();r=function()
        self.charge(scope,time.perf_counter()-started,r)
        return r


def warm():
    cases,_,_=load(FIXTURES);m=next(iter(cases.values())).maze
    org=Organism(controls()['intact'].genome,'local',LIMITS,goal_pulse=True)
    started=time.perf_counter()
    org.react(m.cells,m.w,m.h,m.start,m.goal)
    respond(org,m.cells,m.w,m.h,m.start,m.goal)
    respond(org,m.cells,m.w,m.h,m.start,m.goal,halt_mode='forced',trace=True,horizon=HORIZON)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(seconds=time.perf_counter()-started,candidate_calls=3,baseline_calls=3,
                fixture=m.case_id,production_readonly_grid=True)


def calibrate():
    path=FIXTURES/'calibration.json'
    if path.exists():raise FileExistsError('Calibration packet exists')
    from .routing_transfer_audit import audit_geometry
    started=time.perf_counter();warmup=warm();cases,contexts,metadata=load(FIXTURES)
    geometry=audit_geometry(cases,contexts,metadata);summaries={};calls=work=0
    with gzip.open(FIXTURES/'controls.jsonl.gz','wt') as log:
        for name,item in controls().items():
            entry=dict(item=item.save(),topology='evolved');org=organism(entry);rows=[]
            for cid,o in cases.items():
                r=inference(org,o.maze);rows.append(record(r,o,metadata[cid]));calls+=1;work+=r.instructions+r.spatial_reads
            logrow(log,dict(model=name,rows=rows));summaries[name]=summarize(rows,metadata)
        rows=[]
        for cid,o in cases.items():
            m=o.maze;rows.append(record(baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal),o,metadata[cid]))
        logrow(log,dict(model='compiled_bfs',rows=rows));summaries['compiled_bfs']=summarize(rows,metadata)
    for name in ('intact','compiled_bfs'):
        assert sum(v['optimal']+v['no_path'] for v in summaries[name]['strata'].values())==len(cases)
    for name in controls():
        if name!='intact':
            assert sum(v['optimal'] for v in summaries[name]['strata'].values())<256
    write_json(path,dict(passed=True,seed=CONSTRUCTION_SEED,geometry=geometry,summaries=summaries,
        candidate_calls=calls,candidate_work=work,baseline_calls=len(cases),warmup=warmup,
        wall_seconds=time.perf_counter()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(calibration_passed=True,calls=calls,geometry=geometry)),flush=True)


def freeze():
    if OUT.exists():raise FileExistsError('Freeze already exists')
    assert json.loads((FIXTURES/'calibration.json').read_text())['passed']
    source=ROOT/'results/fork_pressure/frozen_selections.json.gz';saved=read_compressed(source)
    models={};aliases={};configs={}
    for key,s in saved.items():
        for phase in ('archives','frozen'):
            item=Individual.load(s[phase]['pair']['item']);topology=s['config']['topology']
            mkey=f'{topology}/{item.genome.digest}'
            models.setdefault(mkey,dict(item=item.save(),topology=topology))
            aliases[f'{key}/{phase}']=mkey;configs[f'{key}/{phase}']=s['config']
    assert len(models)==33 and len(aliases)==60
    mechanism={name:aliases[alias] for name,alias in MECHANISM_ALIASES.items()}
    for name in ('intact','west_return_gate'):
        models[name]=dict(item=controls()[name].save(),topology='evolved');mechanism[name]=name
    OUT.mkdir()
    compressed_json(OUT/'models.json.gz',dict(models=models,aliases=aliases,configs=configs,mechanism=mechanism))
    prior=exclusions();data=TransferData(SEED,prior);assert data.previous_count==136536
    fixtures,_,_=load(FIXTURES);extra={layout_hash(o.maze) for o in fixtures.values()}
    assert len(extra)==192 and not data.layouts&extra
    compressed_json(OUT/'excluded_layouts.json.gz',sorted(data.layouts|extra))
    source_paths=[*sorted((ROOT/'maze_evolution').glob('*.py')),ROOT/'cellular_maze_lab.py',
        ROOT/'tests/test_routing_transfer.py',ROOT/'docs/ROUTING_TRANSFER_V12H.md']
    inputs=[source,ROOT/'results/fork_pressure/completion.json',ROOT/'results/fork_pressure/verification.json',
            *sorted(FIXTURES.glob('*'))]
    # Freeze every prior maze manifest as well as the exact computed exclusion set.
    inputs += [p for p in (ROOT/'results').rglob('*') if p.is_file()
        and (p.name.endswith('mazes.json.gz') or p.name=='mazes.json' or p.name=='fixtures.json.gz')]
    record=dict(study='V12H',seed=SEED,construction_seed=CONSTRUCTION_SEED,
        parent_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        limits=asdict(LIMITS),cap_seconds=CAP_SECONDS,horizon=HORIZON,
        physical_models=35,selection_aliases=60,contexts=48,inputs_per_model=3200,
        prior_layouts=136536,excluded_with_fixtures=136728,
        models_sha256=sha(OUT/'models.json.gz'),exclusions_sha256=sha(OUT/'excluded_layouts.json.gz'),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in source_paths},
        input_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        environment=dict(python=platform.python_version(),platform=platform.platform(),machine=platform.machine(),
            cpu=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
            numpy=version('numpy'),numba=version('numba'),llvmlite=version('llvmlite')),
        no_final_generation_or_candidate_evaluation_yet=True)
    write_json(OUT/'freeze.json',record)
    print(json.dumps(dict(frozen_models=35,aliases=60,mechanism=mechanism)),flush=True)


def check_freeze():
    frozen=json.loads((OUT/'freeze.json').read_text())
    for p,h in {**frozen['source_sha256'],**frozen['input_sha256']}.items():
        assert sha(ROOT/p)==h,p
    assert sha(OUT/'models.json.gz')==frozen['models_sha256']
    assert sha(OUT/'excluded_layouts.json.gz')==frozen['exclusions_sha256']
    return frozen


def timing(org,o,budget):
    m=o.maze;measurements={};baseline_calls=0
    for name,call in (('candidate',lambda:org.react(m.cells,m.w,m.h,m.start,m.goal)),
                      ('bfs',lambda:baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal))):
        budget.reserve();t=time.perf_counter()
        for _ in range(3):r=call()
        if name=='candidate':budget.charge('timing',time.perf_counter()-t,r,3)
        else:baseline_calls+=3
        values=[]
        for _ in range(5):
            budget.reserve();t=time.perf_counter_ns()
            for _ in range(10):r=call()
            elapsed=time.perf_counter_ns()-t;values.append(elapsed/10)
            if name=='candidate':budget.charge('timing',elapsed/1e9,r,10)
            else:baseline_calls+=10
            assert assess(r,o).optimal
        measurements[name]=dict(ns=values,median_ns=statistics.median(values),min_ns=min(values),max_ns=max(values))
    return dict(measurements=measurements,ratio=measurements['candidate']['median_ns']/measurements['bfs']['median_ns'],baseline_calls=baseline_calls)


def run():
    frozen=check_freeze();out=OUT/'confirmation'
    if out.exists():raise FileExistsError('Confirmation already started; do not overwrite')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()==revision
    for p in ['results/routing_transfer/freeze.json','results/routing_transfer/models.json.gz',*frozen['source_sha256']]:
        subprocess.run(['git','diff','--exit-code','HEAD','--',p],check=True,capture_output=True)
        subprocess.run(['git','ls-files','--error-unmatch',p],check=True,capture_output=True)
    started=time.perf_counter();out.mkdir();budget=Budget();phase_times={};completed=False
    write_json(out/'started.json',dict(revision=revision,freeze_sha256=sha(OUT/'freeze.json'),
        utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()))
    packet=read_compressed(OUT/'models.json.gz');models=packet['models'];warmup=warm()
    # Native-adapter parity uses the first pose of each fixture stratum, before
    # any final-case generation. No model is filtered by fixture performance.
    fixtures,fcontexts,fmeta=load(FIXTURES)
    parity_ids=[cid for c in fcontexts if c['index']==0 for family in FAMILIES
                for cid in c['poses'][0]['cases'][family]]
    assert len(parity_ids)==12
    try:
        t=time.perf_counter()
        with gzip.open(out/'parity.jsonl.gz','wt') as log:
            for key,entry in models.items():
                org=organism(entry)
                for cid in parity_ids:
                    o=fixtures[cid];m=o.maze
                    native=budget.call('parity_native',lambda:org.react(m.cells,m.w,m.h,m.start,m.goal))
                    adapter=budget.call('parity_adapter',lambda:respond(org,m.cells,m.w,m.h,m.start,m.goal))
                    assert canonical(normal_row(native,o))==canonical(normal_row(adapter.reaction,o))
                    logrow(log,dict(model=key,row=record(native,o,fmeta[cid])))
        phase_times['parity']=time.perf_counter()-t
        t=time.perf_counter();data=TransferData(SEED,exclusions()+manifest(fixtures.values()))
        assert sorted(data.layouts)==read_compressed(OUT/'excluded_layouts.json.gz')
        before=set(data.layouts);data.matrix('final',24,4);data.save(out)
        cases,contexts,metadata=data.cache,data.contexts,data.metadata
        assert len(cases)==3200
        write_json(out/'layout_ledger.json',dict(prior_whole_layouts=136536,excluded_with_fixtures=len(before),
            new_whole_layouts=len(data.layouts-before),future_exclusion_count=len(data.layouts),
            new_hashes=sorted(data.layouts-before),overlap_rejections=data.rejections))
        phase_times['construction']=time.perf_counter()-t
        summaries={};timing_cases=[];t=time.perf_counter()
        with gzip.open(out/'normal.jsonl.gz','wt',compresslevel=1) as log:
            for key,entry in models.items():
                org=organism(entry);rows=[];timed=Counter()
                for cid,o in cases.items():
                    r=budget.call('normal',lambda:inference(org,o.maze));row=record(r,o,metadata[cid]);rows.append(row)
                    meta=metadata[cid];stratum=(meta['family'],meta['band'])
                    if '/' in key and row['optimal'] and meta['family'] in FAMILIES and timed[stratum]<4:
                        timing_cases.append((key,cid));timed[stratum]+=1
                logrow(log,dict(model=key,rows=rows));summaries[key]=summarize(rows,metadata)
                print(json.dumps(dict(phase='normal',model=key,pairs=sum(s['complete_pairs'] for s in summaries[key]['strata'].values()),inference_seconds=round(budget.seconds,2))),flush=True)
        phase_times['normal']=time.perf_counter()-t
        t=time.perf_counter();baseline_summaries={}
        with gzip.open(out/'baselines.jsonl.gz','wt') as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                rows=[]
                for cid,o in cases.items():
                    m=o.maze;r=baseline(name,m.cells,m.w,m.h,m.start,m.goal);rows.append(record(r,o,metadata[cid]))
                logrow(log,dict(model=name,rows=rows));baseline_summaries[name]=summarize(rows,metadata)
                assert all(r['optimal'] or r['no_path'] for r in rows)
        assert sum(s['optimal']+s['no_path'] for s in summaries['intact']['strata'].values())==3200
        phase_times['baselines']=time.perf_counter()-t
        branch_ids=[cid for cid,m in metadata.items() if m['family'] in FAMILIES]
        assert len(branch_ids)==2304
        t=time.perf_counter();interventions={}
        with gzip.open(out/'interventions.jsonl.gz','wt',compresslevel=1) as log:
            for name,key in packet['mechanism'].items():
                for mode in MODES:
                    if mode=='normal':continue
                    org=organism(models[key],mode);rows=[]
                    for cid in branch_ids:
                        o=cases[cid];r=budget.call('intervention',lambda:inference(org,o.maze,mode))
                        rows.append(record(r,o,metadata[cid]))
                    logrow(log,dict(target=name,model=key,mode=mode,rows=rows))
                    interventions[name+'/'+mode]=summarize(rows,metadata)
                print(json.dumps(dict(phase='interventions',target=name,inference_seconds=round(budget.seconds,2))),flush=True)
        phase_times['interventions']=time.perf_counter()-t
        probe_ids=[cid for cid in branch_ids if metadata[cid]['index']==0];assert len(probe_ids)==96
        t=time.perf_counter();raw_trace_bytes=0;frames=0
        with gzip.open(out/'trajectories.jsonl.gz','wt',compresslevel=1) as log:
            for name in MECHANISM_ALIASES:
                key=packet['mechanism'][name]
                for mode in TRACE_MODES:
                    org=organism(models[key],mode)
                    for cid in probe_ids:
                        o=cases[cid];r=budget.call('forced_probe',lambda:inference(org,o.maze,mode,True))
                        raw_trace_bytes+=r.history.nbytes;frames+=len(r.history)
                        logrow(log,dict(target=name,model=key,mode=mode,normally_emitted=False,
                            row=record(r.reaction,o,metadata[cid]),history=pack_history(r.history)))
                print(json.dumps(dict(phase='probes',target=name,inference_seconds=round(budget.seconds,2))),flush=True)
        phase_times['probes']=time.perf_counter()-t
        t=time.perf_counter();timings=[]
        for key,cid in timing_cases:
            timings.append(dict(model=key,case=cid,**timing(organism(models[key]),cases[cid],budget)))
        write_json(out/'timing.json',timings);phase_times['timing']=time.perf_counter()-t
        write_json(out/'summary.json',dict(models=summaries,baselines=baseline_summaries,interventions=interventions,
            aliases=packet['aliases'],mechanism=packet['mechanism'],trace_frames=frames,raw_trace_bytes=raw_trace_bytes,
            timing_cases=len(timings),timing_baseline_calls=sum(t['baseline_calls'] for t in timings)))
        completed=True
    finally:
        write_json(out/'execution.json',dict(completed=completed,freeze_revision=revision,
            wall_seconds=time.perf_counter()-started,phase_wall_seconds=phase_times,warmup=warmup,
            candidate=vars(budget),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(completed=True,candidate_calls=budget.calls,inference_seconds=budget.seconds,
        wall_seconds=time.perf_counter()-started)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('calibrate','freeze','run'))
    action=parser.parse_args().action
    {'calibrate':calibrate,'freeze':freeze,'run':run}[action]()
