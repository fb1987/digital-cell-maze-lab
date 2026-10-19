"""V12N independent graph/raster/proxy checks, exact execution and selection replay."""
import json,time,resource,random
from collections import defaultdict
from .foundation_calibration import ROOT,write_json
from .foundation_study import read_compressed
from .foundation_study_verify_core import Checker
from .foundation_data import transform_maze,layout_hash
from .route_confirmation_audit import graph_distances,adjacent
from .routing_transfer import sha,canonical,lines
from .branch_pressure_data import *
from .branch_pressure_fitness import choose,measurements,evaluate,pair_score,selected
from .exposure_selection import organism,record
from .foundation_pair_confirm import normal_row
from .baselines import baseline


def geometry(d):
    count=0
    for c in d.contexts:
        for pose in c['poses']:
            for family,ids in pose['cases'].items():
                for side,cid in enumerate(ids):
                    o=d.cache[cid];m=o.maze;label=d.metadata[cid];base=d.cache[c['poses'][0]['cases'][family][side]].maze
                    tr=transform_maze(base,pose['pose']);assert (tr.cells,tr.start,tr.goal)==(m.cells,m.start,m.goal)
                    ds=graph_distances(m.cells,m.w,m.start);dg=graph_distances(m.cells,m.w,m.goal);assert ds==o._from_start and dg==o.to_goal
                    assert (ds[m.goal]<0)==(family=='disconnected');assert m.cells[m.start] and m.cells[m.goal]
                    reached={p for p,v in enumerate(ds) if v>=0};edges=sum(sum(q in reached for q in adjacent(p,m.w,len(m.cells))) for p in reached)//2
                    assert edges==len(reached)-1
                    for p in label['clutter']:assert m.cells[p] and not any(m.cells[q] for q in adjacent(p,m.w,len(m.cells)))
                    if o.path:
                        assert o.path==label['path'];expected=1 if c['kind']=='adjacent' else 3 if c['kind'].startswith('three') else 2
                        assert ds[m.goal]==expected
                    count+=1
                if family=='paired':
                    a,b=[d.cache[cid].maze for cid in ids];assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
    assert count==len(d.cache);return count


def independent_proxy(rows,meta):
    rs=sorted(rows,key=lambda r:meta[r['case']]['side']);paths=[meta[r['case']]['path'] for r in rs];goals={p[-1] for p in paths}
    private=[[p for p in paths[k] if p not in paths[1-k] and p not in goals] for k in range(2)]
    eligible=all(private)
    if not eligible or any(r['status']!='emitted' for r in rs):return dict(eligible=bool(eligible),score=0.,contrast=0.,strict_both=False,positive=False)
    masks=[]
    for r in rs:
        bits=bytes.fromhex(r['mask']);masks.append([bool(bits[p//8] & (1<<(p%8))) for p in range(81)])
    deltas=[];f1=[]
    for k in range(2):
        deltas.append(sum(int(masks[k][p])-int(masks[1-k][p]) for p in private[k])/len(private[k]))
        f1.append(2*sum(masks[k][p] for p in paths[k])/(sum(masks[k])+len(paths[k])))
    contrast=max(0.,sum(deltas)/2);score=contrast*min(f1)
    return dict(eligible=True,score=score,contrast=contrast,strict_both=all(v>0 for v in deltas),positive=score>0)


def independent_fitness(rows,meta,pressure):
    groups=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family']=='paired':groups[m['base'],m['pose']].append(r)
    score=0.
    for rs in groups.values():
        a,b=independent_proxy(rs,meta),pair_score(rs,meta)
        assert a==b,(a,b)
        score+=a['score']
    return [sum(all(r['optimal'] for r in rs) for rs in groups.values()),round(score,8) if pressure=='choice' else 0.,
        sum(r['optimal'] for r in rows),sum(r['valid'] for r in rows),sum(r['no_path'] for r in rows)-sum(r['reachable'] and r['status']=='no_path' for r in rows),
        round(sum(r['partial'] for r in rows)+2*sum(min(r['partial'] for r in rs) for rs in groups.values()),8)]


def audit():
    from .branch_pressure_study import check_freeze,make_pools,loaded,final_panel,calibration_gate,TOPS,PRESSURES
    t=time.perf_counter();reg=check_freeze();counts=defaultdict(int)
    for name in ('fork_pressure','routing_transfer','validation_breadth','junction_distance','robustness_pressure','lineage_confirmation','exposure_calibration'):
        for p,h in json.loads((ROOT/'results'/name/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;counts['prior_completion_hashes']+=1
    values=make_pools()
    for name,value in zip(('pools','events','rng','models','aliases'),values):assert value==read_compressed(OUT/f'{name}.json.gz')
    pools,events,rngs,models,aliases=values;counts['mutation_replays']=len(events);counts['preserved_founders']=288
    previous=exclusions();datasets={};cases={}
    for scope,path,seed,repeats in [('fixture',FIXTURES,FIXTURE_SEED,1),('calibration',OUT/'calibration',SEED,1),('validation',OUT/'validation',seed_for(SEED,'validation',0,0),1),('confirmation',OUT/'confirmation',seed_for(SEED,'confirmation',0,0),3)]:
        actual=create(seed,scope,previous,repeats);d=loaded(path);counts['graph_cases']+=geometry(d)
        assert canonical(manifest(actual.cache.values()))==read_compressed(path/'mazes.json.gz');assert canonical(actual.contexts)==d.contexts and canonical(actual.metadata)==d.metadata
        if scope!='fixture':
            for p,h in json.loads((path/'generation.json').read_text())['hashes'].items():assert sha(ROOT/p)==h,p
            assert read_compressed(path/'query.json.gz')==query(actual,scope=='confirmation')
        previous+=read_compressed(path/'mazes.json.gz');datasets[scope]=d;cases.update(d.cache)
    counts['whole_layouts_through_N']=len(actual.layouts);checker=Checker(cases);orgs={};replayed={};works={}
    for scope,path,file in [('fixture',FIXTURES,'profiles.jsonl.gz'),('calibration',OUT/'calibration','responses.jsonl.gz'),('validation',OUT/'validation','responses.jsonl.gz'),('confirmation',OUT/'confirmation','responses.jsonl.gz')]:
        current=models if scope=='fixture' else read_compressed(path/'models.json.gz');d=datasets[scope]
        if scope=='fixture':
            want=[aliases[f'{rep}/{top}'][pools[str(rep)]['founders'][k]] for rep in range(3) for top in TOPS for k in (0,24,48,72)]
            assert len(set(want))==24;ids=[cid for cid,m in d.metadata.items() if m['pose']==0]
        else:want=list(current);ids=read_compressed(path/'query.json.gz')
        expected={(k,cid) for k in want for cid in ids};seen=set();rr=defaultdict(list);work=0;start=time.perf_counter()
        for rec in lines(path/file):
            key,cid=rec['model'],rec['row']['case'];assert (key,cid) in expected and (key,cid) not in seen;seen.add((key,cid))
            if key not in orgs:orgs[key]=organism(current[key])
            o=cases[cid];m=o.maze;r=record(orgs[key].react(m.cells,m.w,m.h,m.start,m.goal),o);assert canonical(r)==rec['row'],(scope,key,cid)
            checker.row(r);counts['candidate_replays']+=1;work+=r['reads']+r['dispatches']+r['exposure_checks'];rr[key].append(r)
        assert seen==expected;counts[scope+'_calls']=len(seen);works[scope]=work;replayed[scope]=rr
        print(json.dumps(dict(scope=scope,calls=len(seen),seconds=time.perf_counter()-start)),flush=True)
    choices=read_compressed(OUT/'calibration_choices.json.gz');metrics=read_compressed(OUT/'calibration_metrics.json.gz');gates=json.loads((OUT/'calibration_gates.json').read_text());selections=read_compressed(OUT/'selections.json.gz');wanted=set()
    for rep,pool in pools.items():
        for top in TOPS:
            key=f'{rep}/{top}';rows={i['id']:replayed['calibration'][aliases[key][i['id']]] for i in pool['items']}
            for pressure in PRESSURES:
                actual=choose(pool,rows,datasets['calibration'].metadata,seed_for(SEED,'parents',int(rep),0),pressure);assert actual==choices[key][pressure];counts['parent_draws']+=64
                for itemid,rs in rows.items():
                    assert independent_fitness(rs,datasets['calibration'].metadata,pressure)==actual['fitness'][itemid];counts['independent_ranks']+=1
                ids=actual['nominees'];small=dict(items=[i for i in pool['items'] if i['id'] in ids],anchors=[]);wanted.update(aliases[key][i] for i in ids)
                vr={i['id']:replayed['validation'][aliases[key][i['id']]] for i in small['items']};v=choose(small,vr,datasets['validation'].metadata,seed_for(SEED,'validation',int(rep),0),pressure)
                expected=dict(item=next(i for i in pool['items'] if i['id']==v['best']),rank=v['rank'],nominees=ids,metrics=measurements(vr[v['best']],datasets['validation'].metadata));assert expected==selections[key][pressure];counts['validated_choices']+=1
            g,ms=calibration_gate(pool,rows,datasets['calibration'].metadata,choices[key]['current'],choices[key]['choice']);assert g==gates[key] and ms==metrics[key]
    assert wanted==set(replayed['validation'])
    fm,fa,control=final_panel();assert fm==read_compressed(OUT/'confirmation/models.json.gz') and fa==read_compressed(OUT/'confirmation/aliases.json.gz')
    assert all(r['optimal'] or r['no_path'] for r in replayed['confirmation'][control])
    analysis=json.loads((OUT/'analysis.json').read_text());passing={top:[] for top in TOPS}
    for key,aa in fa.items():
        ms={label:measurements(replayed['confirmation'][v['model']],datasets['confirmation'].metadata) for label,v in aa.items()}
        for label,v in aa.items():
            for pressure in PRESSURES:assert independent_fitness(replayed['confirmation'][v['model']],datasets['confirmation'].metadata,pressure)==list(evaluate(replayed['confirmation'][v['model']],datasets['confirmation'].metadata,pressure).fitness)
        a,c=ms['selected_choice'],ms['selected_current'];ok=a['mean_score']>=.02 and a['mean_score']>=c['mean_score']+.01-1e-12 and a['positive_pairs']>=4 and a['positive_templates']>=2 and a['three_edge_positive']>0 and a['strict_pairs']>0 and a['pairs']>=c['pairs']
        combined=bool(gates[key]['passed'] and ok);assert analysis['results'][key]==dict(metrics=ms,calibration_passed=gates[key]['passed'],final_passed=bool(ok),combined_passed=combined)
        if combined:passing[key.split('/')[1]].append(int(key.split('/')[0]))
    assert passing==analysis['passing_groups'] and analysis['pilot_eligible']==any(len(v)>=2 for v in passing.values())
    seen=set();ids=read_compressed(OUT/'confirmation/query.json.gz')
    for rec in lines(OUT/'confirmation/baselines.jsonl.gz'):
        key,cid=rec['model'],rec['row']['case'];assert (key,cid) not in seen;seen.add((key,cid));o=cases[cid];m=o.maze
        r=canonical(normal_row(baseline(key,m.cells,m.w,m.h,m.start,m.goal),o));assert r==rec['row'] and (r['optimal'] or r['no_path']);checker.row(r)
    assert seen=={(n,cid) for n in ('compiled_bfs','compiled_astar','wave_bit') for cid in ids};counts['baseline_replays']=len(seen)
    profile=json.loads((FIXTURES/'profile.json').read_text());run=json.loads((OUT/'selection_execution.json').read_text());final=json.loads((OUT/'confirmation/execution.json').read_text())
    for packet,scopes,cap in ((profile,['fixture'],60),(run,['calibration','validation'],480),(final,['confirmation'],200)):
        assert packet['budget']['calls']==sum(counts[s+'_calls'] for s in scopes) and packet['budget']['work']==sum(works[s] for s in scopes)
        assert packet['budget']['seconds']<cap and packet['peak_rss_bytes']<4*2**30
    assert profile['passed'] and run['complete'] and final['complete'];counts['independent_rasters']=checker.rasters
    result=dict(passed=True,counts=dict(counts),source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(OUT/'verification.json',result);print(json.dumps(result,indent=2),flush=True)
