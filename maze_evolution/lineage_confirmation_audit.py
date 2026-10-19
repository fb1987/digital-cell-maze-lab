"""V12L independent graph/raster grading, provenance and complete exact replay."""
import json,time,resource
from collections import defaultdict
from .foundation_calibration import ROOT,write_json
from .foundation_study import read_compressed
from .foundation_study_verify_core import Checker
from .foundation_data import layout_hash
from .datasets import manifest
from .growth import Individual,replay_mutation
from .routing_transfer import sha,canonical,lines,organism,inference
from .route_confirmation_runtime import respond
from .foundation_pair_confirm import normal_row
from .baselines import baseline
from .robustness_audit import geometry as prior_geometry
from .lineage_confirmation_data import *


def geometry(cases,contexts,meta):
    result=prior_geometry(cases,contexts,meta);groups=defaultdict(list)
    for c in contexts:groups[c['template']].append(c)
    assert len(groups)==36
    for cs in groups.values():
        a,b=sorted(cs,key=lambda c:c['position']);dx,dy=b['translation'];n=a['n'];assert (dx,dy) in ((2,-2),(-2,2))
        for family in FAMILIES:
            for ca,cb in zip(a['poses'][0]['cases'][family],b['poses'][0]['cases'][family]):
                ma,mb=cases[ca].maze,cases[cb].maze
                assert {i+dx+dy*n for i,v in enumerate(ma.cells) if v}=={i for i,v in enumerate(mb.cells) if v}
                assert (ma.start+dx+dy*n,ma.goal+dx+dy*n)==(mb.start,mb.goal)
                assert [p+dx+dy*n for p in meta[ca]['path']]==meta[cb]['path']
    result.update(independent_templates=len(groups),matched_translation_pairs=len(groups));return result


def audit():
    from .lineage_confirmation import check_freeze,MODES,wanted
    started=time.perf_counter();packet=check_freeze();counts=defaultdict(int)
    for name in ('fork_pressure','routing_transfer','validation_breadth','junction_distance','robustness_pressure'):
        old=json.loads((ROOT/'results'/name/'completion.json').read_text())
        for p,h in old['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;counts['prior_completion_hashes']+=1
    pf=json.loads((OUT/'panel_freeze.json').read_text())
    for p,h in pf['source_sha256'].items():assert sha(ROOT/p)==h;counts['panel_source_hashes']+=1
    for f in ('panel','lineages'):assert sha(OUT/f'{f}.json.gz')==pf[f'{f}_sha256']
    assert sha(OUT/'aliases.json')==pf['aliases_sha256']
    lineage=read_compressed(OUT/'lineages.json.gz');models=read_compressed(OUT/'panel.json.gz');aliases=json.loads((OUT/'aliases.json').read_text())
    observed={}
    for path in pf['source_sha256']:
        if path.endswith('.lineage.jsonl.gz'):
            for r in lines(ROOT/path):
                if r['id'] in lineage['registry']:observed[r['id']]=r
    assert observed==lineage['registry']
    oldpanel=read_compressed(ROOT/'results/robustness_pressure/panel.json.gz')
    for name,e in oldpanel.items():assert models[aliases[name]]==e
    selections=read_compressed(ROOT/'results/robustness_pressure/frozen_selections.json.gz')
    for rep,a in lineage['chains'].items():
        current=Individual.load(a['entry']);assert current.save()==models[aliases[f'k{rep}_entry']]['item']
        for s in reversed(a['steps']):
            r=lineage['registry'][s['id']];assert current.identity==r['parent'];child=Individual.load(r)
            assert replay_mutation(current.genome,r['events'],256)==child.genome;current=child;counts['ancestry_mutations']+=1
        target=models[aliases[f'k{rep}_target']];assert current.save()==target['item']
        assert target['item']['parent']==models[aliases[f'k{rep}_parent']]['item']['id']
        assert Individual.load(target['context_alias']).genome==current.genome
        key=f'robustness/carry/evolved/pair/evolution/{rep}'
        assert selections[key]['archives']['context']['item']==target['item']
        assert selections[key]['frozen']['context']['item']==models[aliases[f'k{rep}_frozen']]['item']
    previous=exclusions();allcases={};meta_by_scope={};cases_by_scope={}
    for scope,path,seed in [('fixture',FIXTURES,FIXTURE_SEED),('confirmation',OUT/'confirmation',SEED)]:
        cases,contexts,meta=load(path);geometry(cases,contexts,meta);counts['graph_cases']+=len(cases)
        data=LineageData(seed,previous);assert data.previous_count==(163928 if scope=='fixture' else 167384)
        corpus(data,scope)
        assert canonical(manifest(data.cache.values()))==read_compressed(path/'mazes.json.gz')
        assert canonical(data.contexts)==contexts and canonical(data.metadata)==meta
        previous+=read_compressed(path/'mazes.json.gz');allcases.update(cases);meta_by_scope[scope]=meta;cases_by_scope[scope]=cases
        counts['regenerated_cases']+=len(cases)
    counts['whole_layouts_through_L']=len(data.layouts)
    generation=json.loads((OUT/'confirmation/generation.json').read_text())
    for p,h in generation['hashes'].items():assert sha(ROOT/p)==h,p
    checker=Checker(allcases);orgs={};work=0
    for scope,path in [('fixture',FIXTURES),('confirmation',OUT/'confirmation')]:
        expected={(name,mode,cid) for name in models for mode in MODES for cid,m in meta_by_scope[scope].items() if wanted(m,mode,scope=='fixture')}
        seen=set();parity_seen=set();sec=time.perf_counter()
        for rec in lines(path/'responses.jsonl.gz'):
            name,mode=rec['model'],rec['mode'];cid=rec['row']['case'];key=(name,mode);o=allcases[cid];m=o.maze
            if mode=='parity':
                assert scope=='fixture' and meta_by_scope[scope][cid]['pose']==0 and meta_by_scope[scope][cid]['family']=='fork' and meta_by_scope[scope][cid]['side']==0
                assert (name,cid) not in parity_seen;parity_seen.add((name,cid));org=organism(models[name])
                a=normal_row(inference(org,m),o);b=normal_row(respond(org,m.cells,m.w,m.h,m.start,m.goal).reaction,o)
                assert canonical(a)==canonical(b)==rec['row'];counts['candidate_replays']+=2;counts['adapter_parity']+=1
            else:
                identity=(name,mode,cid);assert identity in expected and identity not in seen;seen.add(identity)
                if key not in orgs:orgs[key]=organism(models[name],mode)
                row=normal_row(inference(orgs[key],m,mode),o);assert canonical(row)==rec['row'],identity
                counts['candidate_replays']+=1
                if scope=='confirmation':work+=row['reads']+row['dispatches']
            checker.row(rec['row'])
        assert seen==expected
        if scope=='fixture':assert len(parity_seen)==len(models)*72
        counts[f'{scope}_responses']=len(seen)
        print(json.dumps(dict(scope=scope,replays=counts['candidate_replays'],seconds=round(time.perf_counter()-sec,2))),flush=True)
    expected={(name,cid) for name in ('compiled_bfs','compiled_astar','wave_bit') for cid in cases_by_scope['confirmation']};seen=set()
    for rec in lines(OUT/'confirmation/baselines.jsonl.gz'):
        cid=rec['row']['case'];key=(rec['model'],cid);assert key in expected and key not in seen;seen.add(key)
        o=allcases[cid];m=o.maze;checker.row(rec['row']);r=normal_row(baseline(rec['model'],m.cells,m.w,m.h,m.start,m.goal),o)
        assert canonical(r)==rec['row'] and (r['optimal'] or r['no_path']);counts['baseline_replays']+=1
    assert seen==expected
    execution=json.loads((OUT/'confirmation/execution.json').read_text());assert execution['complete']
    assert execution['budget']['calls']==counts['confirmation_responses']==execution['planned_calls']
    assert execution['budget']['work']==work and execution['budget']['seconds']<720
    counts['independently_graded_rasters']=checker.rasters
    result=dict(passed=True,counts=dict(counts),source_hashes=len(packet['sources']),input_hashes=len(packet['inputs']),
        wall_seconds=time.perf_counter()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(OUT/'verification.json',result);print(json.dumps(result,indent=2),flush=True)
