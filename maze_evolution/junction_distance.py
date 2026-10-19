"""V12J fixed-panel assay. Separate fixture, freeze, run and audit commands."""
import argparse
from collections import Counter, defaultdict
import gzip
from importlib.metadata import version
import json
import platform
import resource
import subprocess
import time

import numpy as np
from .baselines import baseline
from .foundation_calibration import ROOT, LIMITS, controls, write_json
from .foundation_data import layout_hash
from .foundation_pair_confirm import normal_row
from .foundation_study import compressed_json, read_compressed
from .growth import Individual
from .route_confirmation import pack_history
from .route_confirmation_runtime import respond
from .routing_transfer import sha, canonical, lines, logrow, organism, inference, MODES, TRACE_MODES
from .junction_distance_data import OUT, FIXTURES, SEED, FIXTURE_SEED, N, PREFIXES, BRANCHES, DistanceData, exclusions, load

CAP_SECONDS, CAP_CALLS, CONTEXTS = 720, 280000, 12
TARGETS = ('branch_narrow','branch_broad','long_prefix','local_long','local_cycle',
           'fresh_evolved','fresh_local','resampled','intact')
POOL_KEYS = dict(branch_narrow='evolved/06708b886ad4ff6ced39', branch_broad='evolved/163db2d988303e279f6c',
    long_prefix='evolved/6251d8a39c24aa6e3034', long_replacement='evolved/a2a9660cc0b834ec66fe',
    local_long='local/dea7d3831d8e42746fda',local_cycle='local/4383e8d8ac50810ac978',
    fresh_evolved='evolved/05094bcd640f49a0139f',fresh_local='local/110ef8628430ec129788',
    fresh_local_narrow='local/07ef765c7ca41e478a47',resampled='evolved/3e2faaad7ce784699c1a')


def panel():
    pool=read_compressed(ROOT/'results/validation_breadth/pool.json.gz')
    selections=read_compressed(ROOT/'results/validation_breadth/selections.json.gz')
    ancestry=json.loads((ROOT/'results/validation_breadth/selected_G_ancestry.json').read_text())
    models={}
    for name,key in POOL_KEYS.items():
        aliases=[a for c in selections.values() for s in c.values() if s['model']==key for a in s['aliases']]
        alias=aliases[0];entry=canonical(pool['models'][key]);entry['item'].update({k:alias[k] for k in ('id','parent','birth')})
        entry.update(pool_model=key,aliases=aliases,selection='I-informed frozen target')
        models[name]=entry
    wanted={models[n]['item']['parent']:n+'_parent' for n in ('branch_narrow','branch_broad')}
    sources=set()
    for path in sorted((ROOT/'results/fork_pressure/segments').glob('*.lineage.jsonl.gz')):
        for row in lines(path):
            if row['id'] in wanted:
                name=wanted[row['id']];models[name]=dict(item={k:row[k] for k in ('id','genome','parent','birth')},
                    topology='evolved',selection='prespecified immediate parent',source=str(path.relative_to(ROOT)))
                sources.add(str(path.relative_to(ROOT)))
    assert all(n+'_parent' in models for n in ('branch_narrow','branch_broad'))
    anchor=ancestry[models['branch_narrow']['item']['id']]['entry_item']
    assert anchor['id']==ancestry[models['branch_broad']['item']['id']]['entry_item']['id']
    models['shared_ancestor']=dict(item=anchor,topology='evolved',selection='shared protected E ancestor')
    models['intact']=dict(item=controls()['intact'].save(),topology='local',selection='separate known control')
    for name,e in models.items():
        item=Individual.load(e['item']);e['digest']=item.genome.digest;e['genes']=len(item.genome.genes)
        assert 1<=e['genes']<=256
        e['lineage_group']=('known' if name=='intact' else 'carried_evolved_E0' if name in
            ('branch_narrow','branch_broad','long_prefix','long_replacement','branch_narrow_parent','branch_broad_parent','shared_ancestor')
            else 'carried_local_E1' if name in ('local_long','local_cycle') else 'fresh_evolved_G1' if name=='fresh_evolved'
            else 'fresh_local_G1' if name in ('fresh_local','fresh_local_narrow') else 'unmutated_resampling')
    assert len(models)==14
    return models,sources


class Budget:
    def __init__(self):
        self.seconds=0.;self.calls=0;self.work=0;self.scopes={};self.maximum=0.
    def call(self,scope,fn):
        if self.calls>=CAP_CALLS or self.seconds>=CAP_SECONDS-max(5.,2*self.maximum):
            raise TimeoutError('V12J closed cap; preserve partial outputs')
        t=time.perf_counter();result=fn();elapsed=time.perf_counter()-t
        r=result.reaction if hasattr(result,'reaction') else result
        self.seconds+=elapsed;self.calls+=1;self.work+=r.instructions+r.spatial_reads;self.maximum=max(self.maximum,elapsed)
        s=self.scopes.setdefault(scope,dict(seconds=0.,calls=0,work=0));s['seconds']+=elapsed;s['calls']+=1;s['work']+=r.instructions+r.spatial_reads
        assert self.seconds<CAP_SECONDS
        return result


def selected(meta,trace=False):
    if trace:
        return meta['index']==0 and meta['prefix'] in (1,4,8) and meta['family'] in ('fork','two_4','cycle_4') and meta['pose'] in (0,1)
    return meta['index']<2 and meta['family'] in BRANCHES


def warm(cases,models):
    m=next(iter(cases.values())).maze;org=organism(models['intact'])
    t=time.perf_counter();inference(org,m);respond(org,m.cells,m.w,m.h,m.start,m.goal)
    inference(org,m,trace=True)
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(seconds=time.perf_counter()-t,candidate_calls=3,baseline_calls=3,case=m.case_id,readonly_input=True)


def frozen_sources():
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/JUNCTION_DISTANCE_V12J.md',
           ROOT/'tests/test_junction_distance.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}


def prepare():
    if OUT.exists() or FIXTURES.exists():raise FileExistsError('V12J already prepared')
    OUT.mkdir();models,sources=panel();compressed_json(OUT/'panel.json.gz',models)
    ancestry=json.loads((ROOT/'results/validation_breadth/selected_G_ancestry.json').read_text())
    write_json(OUT/'ancestry.json',{n:ancestry[e['item']['id']] for n,e in models.items() if e['item']['id'] in ancestry})
    source_paths=sources|{'results/validation_breadth/pool.json.gz','results/validation_breadth/selections.json.gz',
        'results/validation_breadth/selected_G_ancestry.json','results/validation_breadth/completion.json',
        'results/fork_pressure/completion.json','results/routing_transfer/completion.json'}
    write_json(OUT/'panel_freeze.json',dict(sha256=sha(OUT/'panel.json.gz'),inputs={p:sha(ROOT/p) for p in sorted(source_paths)},
        selection_used_inspected_I=True,models=len(models),genome_edits=False))
    data=DistanceData(FIXTURE_SEED,exclusions());assert data.previous_count==144120
    data.context('fixture',0);data.save(FIXTURES)
    print(json.dumps(dict(panel=len(models),fixture_cases=len(data.cache),new_layouts=len(data.layouts)-data.previous_count)),flush=True)


def calibrate():
    from .junction_distance_audit import geometry
    if (FIXTURES/'calibration.json').exists():raise FileExistsError('Calibration closed')
    models=read_compressed(OUT/'panel.json.gz');cases,contexts,meta=load(FIXTURES)
    t=time.perf_counter();g=geometry(cases,contexts,meta);warmup=warm(cases,models);budget=Budget();counts=Counter()
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt') as log:
        for name,e in models.items():
            org=organism(e)
            # All intact cases; fixed production-signature profile for every other model.
            for cid,o in cases.items():
                m=meta[cid]
                if name!='intact' and not (m['pose']==0 and m['shape']=='bent'):continue
                r=budget.call('normal',lambda:inference(org,o.maze));row=normal_row(r,o)
                logrow(log,dict(model=name,mode='normal',row=row));counts[name]+=1
                if name=='intact':assert row['optimal'] or row['no_path']
        for name in TARGETS:
            for mode in MODES:
                if mode=='normal':continue
                org=organism(models[name],mode)
                for cid,o in cases.items():
                    m=meta[cid]
                    if not (m['pose']==0 and m['shape']=='bent' and m['prefix'] in (1,8) and m['family']=='cycle_4'):continue
                    r=budget.call('interventions',lambda:inference(org,o.maze,mode));logrow(log,dict(model=name,mode=mode,row=normal_row(r,o)))
        for name in TARGETS:
            for mode in TRACE_MODES:
                org=organism(models[name],mode)
                for cid,o in cases.items():
                    m=meta[cid]
                    if not (m['pose']==0 and m['shape']=='bent' and m['prefix']==8 and m['family']=='cycle_4'):continue
                    r=budget.call('traces',lambda:inference(org,o.maze,mode,True))
                    logrow(log,dict(model=name,mode=mode,row=normal_row(r.reaction,o),history=pack_history(r.history)))
    # Fixed invocation counts, deliberately no throughput-based model/case selection.
    projected=(budget.scopes['normal']['seconds']/budget.scopes['normal']['calls']*188160
        +budget.scopes['interventions']['seconds']/216*86400+budget.scopes['traces']['seconds']/72*2592)
    write_json(FIXTURES/'calibration.json',dict(passed=True,geometry=g,warmup=warmup,budget=vars(budget),
        rough_projected_candidate_seconds=projected,main_call_count=277152,
        wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(calibration_passed=True,seconds=budget.seconds,projection=projected)),flush=True)


def freeze():
    if (OUT/'preregistration.json').exists():raise FileExistsError('Protocol frozen')
    calibration=json.loads((FIXTURES/'calibration.json').read_text());assert calibration['passed']
    # Conservative gate: main assay must plausibly fit without an extension.
    assert calibration['rough_projected_candidate_seconds']<650
    inputs={str(p.relative_to(ROOT)):sha(p) for directory in (FIXTURES,OUT) for p in directory.iterdir() if p.is_file()}
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,contexts=CONTEXTS,
        cap_seconds=CAP_SECONDS,cap_calls=CAP_CALLS,planned_calls=277152,sources=frozen_sources(),inputs=inputs,
        platform=platform.platform(),python=platform.python_version(),dependencies={x:version(x) for x in ('numpy','numba','llvmlite')},
        main_generated=False))


def check_freeze(committed=False):
    packet=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for p,h in packet[group].items():assert sha(ROOT/p)==h,p
    if committed:
        for p in [OUT/'preregistration.json',OUT/'panel.json.gz']:
            assert subprocess.check_output(['git','show',f'HEAD:{p.relative_to(ROOT)}'],cwd=ROOT)==p.read_bytes(),'Uncommitted freeze'
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        remote=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
        assert head==remote,'Freeze not pushed'
    return packet


def run():
    check_freeze(True)
    if (OUT/'confirmation').exists():raise FileExistsError('Main corpus already generated; no repeat/extension')
    started=time.perf_counter();previous=exclusions()+read_compressed(FIXTURES/'mazes.json.gz')
    data=DistanceData(SEED,previous)
    for index in range(CONTEXTS):data.context('confirmation',index)
    data.save(OUT/'confirmation');cases,meta=data.cache,data.metadata
    models=read_compressed(OUT/'panel.json.gz');fixture_cases,_,_=load(FIXTURES)
    warmup=warm(fixture_cases,models);budget=Budget()
    write_json(OUT/'generation_manifest.json',dict(preregistration_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        prior_layouts=data.previous_count,new_layouts=len(data.layouts)-data.previous_count,cases=len(cases),
        files={str(p.relative_to(ROOT)):sha(p) for p in (OUT/'confirmation').iterdir()},rejections=data.rejections))
    try:
        for scope in ('normal','interventions','traces'):
            with gzip.open(OUT/f'{scope}.jsonl.gz','wt') as log:
                for name,e in models.items():
                    if scope!='normal' and name not in TARGETS:continue
                    modes=('normal',) if scope=='normal' else tuple(m for m in MODES if m!='normal') if scope=='interventions' else TRACE_MODES
                    for mode in modes:
                        org=organism(e,mode)
                        for cid,o in cases.items():
                            if scope!='normal' and not selected(meta[cid],scope=='traces'):continue
                            r=budget.call(scope,lambda:inference(org,o.maze,mode,scope=='traces'))
                            row=dict(model=name,mode=mode,row=normal_row(r.reaction if scope=='traces' else r,o))
                            if scope=='traces':row['history']=pack_history(r.history)
                            logrow(log,row)
                    print(json.dumps(dict(scope=scope,model=name,seconds=round(budget.seconds,2),calls=budget.calls)),flush=True)
        with gzip.open(OUT/'baselines.jsonl.gz','wt') as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for o in cases.values():
                    m=o.maze;r=baseline(name,m.cells,m.w,m.h,m.start,m.goal);row=normal_row(r,o)
                    assert row['optimal'] or row['no_path'];logrow(log,dict(model=name,row=row))
        assert budget.calls==277152
    finally:
        write_json(OUT/'execution.json',dict(budget=vars(budget),warmup=warmup,wall_seconds=time.perf_counter()-started,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,complete=budget.calls==277152))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','calibrate','freeze','run','audit','analyze'))
    a=p.parse_args().action
    if a=='audit':
        from .junction_distance_audit import audit
        audit()
    elif a=='analyze':
        from .junction_distance_analysis import analyze
        analyze()
    else:globals()[a]()


if __name__=='__main__':main()
