"""V12L fixed lineage confirmation and predeclared mechanism interventions."""
import argparse,gzip,json,time,resource,subprocess,platform
from collections import defaultdict
from importlib.metadata import version
from copy import deepcopy
from .foundation_calibration import ROOT,write_json,LIMITS
from .foundation_study import read_compressed,compressed_json
from .growth import Individual,replay_mutation
from .routing_transfer import sha,canonical,lines,logrow,organism,inference
from .route_confirmation_runtime import respond
from .foundation_pair_confirm import normal_row
from .baselines import baseline
from .robustness_study import Budget
from .lineage_confirmation_data import *

MODES=('normal','pulse_off','flag_off','endpoint_off','nonlocal_off')
CAP=720


def prepare():
    assert not OUT.exists();OUT.mkdir()
    source=['results/robustness_pressure/panel.json.gz','results/robustness_pressure/frozen_selections.json.gz','results/robustness_pressure/selected_ancestry.json']
    panel=read_compressed(ROOT/source[0]);selections=read_compressed(ROOT/source[1]);ancestry=json.loads((ROOT/source[2]).read_text())
    chains={};needed=set()
    for rep in (1,2):
        key=f'robustness/carry/evolved/pair/evolution/{rep}';a=ancestry[f'{key}/archives/context'];chains[str(rep)]=a
        needed.update(s['id'] for s in a['steps'])
    registry={}
    for path in sorted((ROOT/'results/robustness_pressure/segments').glob('*.lineage.jsonl.gz')):
        selected=[r for r in lines(path) if r['id'] in needed]
        if selected:source.append(str(path.relative_to(ROOT)));registry.update({r['id']:r for r in selected})
    for rep in (1,2):
        a=chains[str(rep)];key=f'robustness/carry/evolved/pair/evolution/{rep}';target=selections[key]['archives']['context']['item']
        parent=registry[target['parent']]
        for suffix,item in [('target',target),('parent',{k:parent[k] for k in ('id','genome','parent','birth')}),('entry',a['entry']),('frozen',selections[key]['frozen']['context']['item'])]:
            panel[f'k{rep}_{suffix}']=dict(item=item,topology='evolved',selection='K-informed fixed lineage confirmation')
        context=selections[key.replace('/pair/','/context/')]['archives']['context']['item']
        assert Individual.load(context).genome==Individual.load(target).genome
        panel[f'k{rep}_target']['context_alias']=context
        current=Individual.load(a['entry'])
        for step in reversed(a['steps']):
            child=registry[step['id']];assert child['parent']==current.identity
            assert replay_mutation(current.genome,child['events'],256)==Individual.load(child).genome
            current=Individual.load(child)
        assert current.save()==target
    models={};aliases={};seen={}
    for name,e in panel.items():
        dna=e['topology']+'/'+Individual.load(e['item']).genome.digest
        if dna not in seen:seen[dna]=name;models[name]=e
        aliases[name]=seen[dna]
    compressed_json(OUT/'panel.json.gz',models);write_json(OUT/'aliases.json',aliases)
    compressed_json(OUT/'lineages.json.gz',dict(chains=chains,registry=registry))
    write_json(OUT/'panel_freeze.json',dict(K_informed=True,source_sha256={p:sha(ROOT/p) for p in source},
        panel_sha256=sha(OUT/'panel.json.gz'),lineages_sha256=sha(OUT/'lineages.json.gz'),aliases_sha256=sha(OUT/'aliases.json'),
        genotypes=len(models),aliases=len(aliases),no_candidate_calls=True))
    print(json.dumps(dict(models=len(models),aliases=len(aliases),lineage_mutations=len(registry))),flush=True)


def warm(cases,models):
    t=time.perf_counter();m=next(iter(cases.values())).maze;entry=models['intact'];calls=0
    for mode in MODES:
        inference(organism(entry,mode),m,mode);calls+=1
    for name in ('compiled_bfs','compiled_astar','wave_bit'):baseline(name,m.cells,m.w,m.h,m.start,m.goal)
    return dict(seconds=time.perf_counter()-t,candidate_calls=calls,baseline_calls=3,case=m.case_id,readonly_bytes=True)


def wanted(meta,mode,fixture=False):
    return (not fixture or meta['pose']==0) and (mode=='normal' or mechanism_case(meta))


def calibrate():
    from .lineage_confirmation_audit import geometry
    assert not (FIXTURES/'calibration.json').exists()
    t=time.perf_counter();cases,contexts,meta=load(FIXTURES);g=geometry(cases,contexts,meta)
    models=read_compressed(OUT/'panel.json.gz');warmup=warm(cases,models);b=Budget(240,40000);profiles={};parity=0
    with gzip.open(FIXTURES/'responses.jsonl.gz','wt',compresslevel=1) as log:
        for name,e in models.items():
            for mode in MODES:
                org=organism(e,mode);start=b.seconds;calls=b.calls
                for cid,o in cases.items():
                    if not wanted(meta[cid],mode,True):continue
                    r=b.call(lambda:inference(org,o.maze,mode));logrow(log,dict(model=name,mode=mode,row=normal_row(r,o)))
                    if name=='intact' and mode=='normal':assert normal_row(r,o)['optimal'] or normal_row(r,o)['no_path']
                profiles[f'{name}/{mode}']=dict(seconds=b.seconds-start,calls=b.calls-calls)
            # Adapter parity on every geometry stratum and both positions at pose zero.
            org=organism(e)
            for c in contexts:
                o=cases[c['poses'][0]['cases']['fork'][0]];m=o.maze
                native=b.call(lambda:inference(org,m));adapter=b.call(lambda:respond(org,m.cells,m.w,m.h,m.start,m.goal).reaction)
                assert canonical(normal_row(native,o))==canonical(normal_row(adapter,o));parity+=1
                logrow(log,dict(model=name,mode='parity',row=normal_row(native,o)))
            print(json.dumps(dict(model=name,calibration_seconds=round(b.seconds,2))),flush=True)
    projection=8*sum(v['seconds'] for v in profiles.values())
    packet=dict(passed=projection<540,projected_candidate_seconds=projection,geometry=g,profiles=profiles,adapter_parity=parity,
        budget=b.save(),warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(FIXTURES/'calibration.json',packet);print(json.dumps({k:packet[k] for k in ('passed','projected_candidate_seconds','budget')},indent=2),flush=True)


def freeze():
    assert not (OUT/'preregistration.json').exists();cal=json.loads((FIXTURES/'calibration.json').read_text());assert cal['passed']
    paths=[ROOT/'cellular_maze_lab.py',ROOT/'docs/LINEAGE_CONFIRMATION_V12L.md',ROOT/'tests/test_lineage_confirmation.py',*sorted((ROOT/'maze_evolution').glob('*.py'))]
    write_json(OUT/'preregistration.json',dict(seed=SEED,fixture_seed=FIXTURE_SEED,cap_candidate_seconds=CAP,main_generated=False,
        sources={str(p.relative_to(ROOT)):sha(p) for p in paths},inputs={str(p.relative_to(ROOT)):sha(p) for d in (OUT,FIXTURES) for p in d.iterdir() if p.is_file() and p.suffix!='.log'},
        platform=platform.platform(),python=platform.python_version(),dependencies={n:version(n) for n in ('numpy','numba','llvmlite','pytest')}))


def check_freeze(committed=False):
    p=json.loads((OUT/'preregistration.json').read_text())
    for group in ('sources','inputs'):
        for path,h in p[group].items():assert sha(ROOT/path)==h,path
    if committed:
        head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        assert head==subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
        for f in ('preregistration.json','panel.json.gz','aliases.json','lineages.json.gz'):
            assert subprocess.check_output(['git','show',f'HEAD:results/lineage_confirmation/{f}'])==(OUT/f).read_bytes()
    return p


def run():
    check_freeze(True);target=OUT/'confirmation';assert not target.exists()
    data=LineageData(SEED,exclusions()+read_compressed(FIXTURES/'mazes.json.gz'));assert data.previous_count==167384
    corpus(data,'confirmation');data.save(target)
    from .lineage_confirmation_audit import geometry
    geometry(data.cache,data.contexts,data.metadata)
    write_json(target/'generation.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),prior_layouts=data.previous_count,
        new_layouts=len(data.layouts)-data.previous_count,rejections=data.rejections,hashes={str(p.relative_to(ROOT)):sha(p) for p in target.iterdir() if p.is_file()}))
    models=read_compressed(OUT/'panel.json.gz');fc,_,_=load(FIXTURES);warmup=warm(fc,models)
    planned=len(models)*sum(wanted(m,mode) for m in data.metadata.values() for mode in MODES)
    b=Budget(CAP,planned);t=time.perf_counter();basecalls=0
    try:
        with gzip.open(target/'responses.jsonl.gz','wt',compresslevel=1) as log:
            for mode in MODES: # Normal output for every fixed model precedes interventions.
                for name,e in models.items():
                    org=organism(e,mode)
                    for cid,o in data.cache.items():
                        if not wanted(data.metadata[cid],mode):continue
                        if b.calls%256==0 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>4*2**30:raise MemoryError('V12L memory cap')
                        r=b.call(lambda:inference(org,o.maze,mode));logrow(log,dict(model=name,mode=mode,row=normal_row(r,o)))
                    if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>2*2**30:raise OSError('V12L storage cap')
                    print(json.dumps(dict(mode=mode,model=name,calls=b.calls,seconds=round(b.seconds,2))),flush=True)
        with gzip.open(target/'baselines.jsonl.gz','wt',compresslevel=1) as log:
            for name in ('compiled_bfs','compiled_astar','wave_bit'):
                for o in data.cache.values():
                    m=o.maze;row=normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o)
                    assert row['optimal'] or row['no_path'];logrow(log,dict(model=name,row=row));basecalls+=1
    finally:
        write_json(target/'execution.json',dict(complete=b.calls==planned and basecalls==3*len(data.cache),planned_calls=planned,budget=b.save(),baseline_calls=basecalls,
            warmup=warmup,wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','calibrate','freeze','run','audit','analyze'));a=p.parse_args().action
    if a=='audit':
        from .lineage_confirmation_audit import audit
        audit()
    elif a=='analyze':
        from .lineage_confirmation_analysis import analyze
        analyze()
    else:globals()[a]()

if __name__=='__main__':main()
