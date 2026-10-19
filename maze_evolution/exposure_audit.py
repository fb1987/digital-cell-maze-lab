"""V12M independent geometry/raster checks, exact replay and selection provenance."""
import json,random,time,resource
from collections import defaultdict
from dataclasses import replace
from .foundation_calibration import ROOT,write_json,LIMITS
from .foundation_study import read_compressed
from .foundation_study_verify_core import Checker
from .foundation_data import transform_maze,layout_hash
from .route_confirmation_audit import graph_distances,adjacent
from .routing_transfer_audit import synthetic
from .robustness_audit import geometry as carry_geometry
from .routing_transfer import sha,canonical,lines
from .growth import Individual as OldIndividual,random_genome
from .growth_runtime import Organism as OldOrganism
from .exposure_genome import Genome,Individual,mutate,replay
from .exposure_runtime import Organism,ARMS
from .exposure_selection import physical,organism,record,choose,evaluate
from .exposure_data import *
from .evaluator import assess
from .baselines import baseline


def geometry(cases,contexts,meta,origin):
    if origin=='carry':
        result=carry_geometry(cases,contexts,meta);groups=defaultdict(list)
        for c in contexts:groups[c['template']].append(c)
        for cs in groups.values():
            a,b=sorted(cs,key=lambda c:c['position']);dx,dy=b['translation'];n=a['n']
            for family in a['poses'][0]['cases']:
                for ca,cb in zip(a['poses'][0]['cases'][family],b['poses'][0]['cases'][family]):
                    ma,mb=cases[ca].maze,cases[cb].maze
                    assert {p+dx+dy*n for p,v in enumerate(ma.cells) if v}=={p for p,v in enumerate(mb.cells) if v}
                    assert (ma.start+dx+dy*n,ma.goal+dx+dy*n)==(mb.start,mb.goal)
        return dict(result,independent_templates=len(groups))
    count=0
    for c in contexts:
        for pose in c['poses']:
            for family,ids in pose['cases'].items():
                for k,cid in enumerate(ids):
                    o=cases[cid];m=o.maze;label=meta[cid];base=cases[c['poses'][0]['cases'][family][k]].maze
                    t=transform_maze(base,pose['pose']);assert (t.cells,t.start,t.goal)==(m.cells,m.start,m.goal)
                    ds=graph_distances(m.cells,m.w,m.start);dg=graph_distances(m.cells,m.w,m.goal)
                    assert ds==o._from_start and dg==o.to_goal
                    assert (ds[m.goal]<0)==(family=='disconnected');assert m.cells[m.start] and m.cells[m.goal]
                    reached={p for p,d in enumerate(ds) if d>=0};edges=sum(sum(q in reached for q in adjacent(p,m.w,len(m.cells))) for p in reached)//2
                    assert edges-len(reached)+1==0
                    for p in label['clutter']:assert m.cells[p] and not any(m.cells[q] for q in adjacent(p,m.w,len(m.cells)))
                    if o.path:
                        assert o.path==label['path'];assert ds[m.goal]==(1 if c['kind']=='adjacent' else 2)
                        grade=assess(synthetic(o,label['path']),o);assert grade.valid_path and grade.optimal
                    count+=1
                if family=='paired':
                    a,b=[cases[i].maze for i in ids];assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
                    pa,pb=[cases[i].path for i in ids];assert pa!=pb
    assert count==len(cases);return dict(cases=count,independent_templates=len(contexts),whole_layouts=len({layout_hash(o.maze) for o in cases.values()}))


def independent_rank(rows,meta,shaping=True):
    pairs=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family'] in ('paired','fork','two_junction','cycle'):pairs[m['base'],m['family'],m['pose']].append(r)
    assert all(len(rs)==2 for rs in pairs.values())
    return [sum(all(r['optimal'] for r in rs) for rs in pairs.values()),sum(r['optimal'] for r in rows),sum(r['valid'] for r in rows),
        sum(r['no_path'] for r in rows)-sum(r['reachable'] and r['status']=='no_path' for r in rows),
        round(sum(r['partial'] for r in rows)+2*sum(min(r['partial'] for r in rs) for rs in pairs.values()),8) if shaping else 0.]


def audit():
    from .exposure_study import check_freeze,create_data,all_manifests,ids_for,CARRY_NAMES,model_origins,final_panel,normal_old,revised_profile
    started=time.perf_counter();reg=check_freeze();counts=defaultdict(int)
    for name in ('fork_pressure','routing_transfer','validation_breadth','junction_distance','robustness_pressure','lineage_confirmation'):
        for p,h in json.loads((ROOT/'results'/name/'completion.json').read_text())['source_and_artifact_sha256'].items():
            assert sha(ROOT/p)==h,p;counts['prior_completion_hashes']+=1
    pf=json.loads((OUT/'pool_freeze.json').read_text());assert sha(ROOT/pf['source'])==pf['source_sha256']
    for p,h in pf['saved'].items():assert sha(ROOT/p)==h
    pools=read_compressed(OUT/'pools.json.gz');prov=read_compressed(OUT/'provenance.json.gz');events=read_compressed(OUT/'events.json.gz')
    models=read_compressed(OUT/'models.json.gz');aliases=read_compressed(OUT/'aliases.json.gz');oldpanel=read_compressed(ROOT/pf['source'])
    eventmap={e['item']['id']:e for e in events}
    for index,name in enumerate(CARRY_NAMES):
        key='carry/'+name;p=pools[key];old=OldIndividual.load(oldpanel[name]['item']);assert prov[key]['source']==oldpanel[name]
        for mask in range(8):
            item=Individual.load(p['items'][mask]);assert item.genome==Genome(old.genome,mask) and item.parent==old.identity and item.birth==0
        base=Individual.load(p['items'][7]);rng=random.Random(seed_for(SEED,'neighborhood',index,0));assert canonical(rng.getstate())==prov[key]['rng_before']
        for raw in p['items'][8:]:
            item=Individual.load(raw);genome,event=mutate(base.genome,rng);stored=eventmap[item.identity]
            assert canonical(event)==stored['event'] and genome==replay(base.genome,stored['event'])==item.genome
            assert raw==stored['item'] and item.parent==base.identity and item.birth==1;counts['sampled_mutations']+=1
        assert canonical(rng.getstate())==prov[key]['rng_after']
    for rep in range(3):
        key=f'fresh/{rep}';rng=random.Random(seed_for(SEED,'fresh_programs',rep,0));bits=random.Random(seed_for(SEED,'fresh_bits',rep,0))
        assert canonical(rng.getstate())==prov[key]['program_rng_before'] and canonical(bits.getstate())==prov[key]['bit_rng_before']
        for raw in pools[key]['items']:
            i=Individual.load(raw);assert i.genome==Genome(random_genome(rng,True),bits.randrange(8)) and i.parent is None and i.birth==0;counts['random_founders']+=1
        assert canonical(rng.getstate())==prov[key]['program_rng_after'] and canonical(bits.getstate())==prov[key]['bit_rng_after']
    for key,p in pools.items():
        for arm in ARMS:
            for raw in p['items']:
                pid,m=physical(Individual.load(raw),arm,p['topology']);assert aliases[key][arm][raw['id']]==pid and models[pid]==m
    previous=exclusions();data={};allcases={}
    for scope,path,seed,final in [('fixture',FIXTURES,FIXTURE_SEED,False),('calibration',OUT/'calibration',SEED,False),
          ('validation',OUT/'validation',seed_for(SEED,'validation',0,0),False),('confirmation',OUT/'confirmation',seed_for(SEED,'confirmation',0,0),True)]:
        d=create_data(seed,scope,previous,final);assert d['carry'].previous_count==len(d['carry'].layouts)-len({layout_hash(o.maze) for o in d['carry'].cache.values()})
        data[scope]=d
        for origin,x in d.items():
            c,ct,m=load(path/origin);geometry(c,ct,m,origin)
            assert canonical(manifest(x.cache.values()))==read_compressed(path/origin/'mazes.json.gz')
            assert canonical(x.contexts)==ct and canonical(x.metadata)==m;allcases.update(c);counts['regenerated_graph_cases']+=len(c)
        previous+=all_manifests(path)
        if scope!='fixture':
            gen=json.loads((path/'generation.json').read_text())
            for p,h in gen['hashes'].items():assert sha(ROOT/p)==h
    counts['whole_layouts_through_M']=len(data['confirmation']['fresh'].layouts)
    checker=Checker(allcases);orgs={};replayed={};basework={}
    for scope,path,file in [('fixture',FIXTURES,'profiles.jsonl.gz'),('calibration',OUT/'calibration','responses.jsonl.gz'),('validation',OUT/'validation','responses.jsonl.gz'),('confirmation',OUT/'confirmation','responses.jsonl.gz')]:
        current=models if scope=='fixture' else read_compressed(path/'models.json.gz')
        if scope=='fixture':wanted=model_origins(pools,aliases);ids={o:ids_for(x,o,profile=True) for o,x in data[scope].items()}
        else:
            query=read_compressed(path/'query.json.gz');wanted=query['models'];ids=query['ids']
            for o,x in data[scope].items():assert ids[o]==ids_for(x,o,scope=='confirmation',selection=scope=='calibration')
        expected={(o,k,cid) for o,keys in wanted.items() for k in keys for cid in ids[o]};seen=set();rr=defaultdict(dict);work=0;scope_start=time.perf_counter()
        for rec in lines(path/file):
            okey,key=rec['origin'],rec['model'];cid=rec['row']['case'];identity=(okey,key,cid);assert identity in expected and identity not in seen;seen.add(identity)
            cachekey=key
            if cachekey not in orgs:orgs[cachekey]=organism(current[key])
            o=allcases[cid];m=o.maze;r=record(orgs[cachekey].react(m.cells,m.w,m.h,m.start,m.goal),o)
            assert canonical(r)==rec['row'],identity;checker.row(r);counts['candidate_replays']+=1
            rr[okey].setdefault(key,[]).append(r);work+=r['reads']+r['dispatches']+r['exposure_checks']
        assert seen==expected;replayed[scope]=rr;basework[scope]=work;counts[scope+'_calls']=len(seen)
        print(json.dumps(dict(scope=scope,replays=counts['candidate_replays'],seconds=round(time.perf_counter()-scope_start,2))),flush=True)
    parity_seen=set()
    for rec in lines(FIXTURES/'parity.jsonl.gz'):
        item=Individual.load(rec['item']);top=rec['topology'];mask=rec['mask'];o=allcases[rec['row']['case']];m=o.maze
        identity=(rec['pool'],mask,m.case_id);assert identity not in parity_seen;parity_seen.add(identity)
        new=Organism(Genome(item.genome.program,mask),'active',top,LIMITS);old=OldOrganism(item.genome.program,top,LIMITS,ablate_nonlocal=mask==0,goal_pulse=True)
        a=record(new.react(m.cells,m.w,m.h,m.start,m.goal),o);z=normal_old(old.react(m.cells,m.w,m.h,m.start,m.goal),o)
        assert canonical(a)==rec['row'] and z==rec['old'];assert a['array_bytes']==z['array_bytes']+17
        assert {k:v for k,v in a.items() if k not in ('exposure_checks','suppressed_reads','array_bytes')}=={k:v for k,v in z.items() if k!='array_bytes'}
        checker.row(a);checker.row(z);counts['candidate_replays']+=2;counts['adapter_parity']+=1
    calibration=json.loads((FIXTURES/'calibration.json').read_text());assert counts['adapter_parity']==calibration['parity_comparisons']
    assert revised_profile(calibration)==json.loads((FIXTURES/'calibration_revised.json').read_text())
    expected_parity=set()
    for key,p in pools.items():
        for mask in (0,7):
            for cid in ids_for(data['fixture'][p['origin']],p['origin'],profile=True):expected_parity.add((key,mask,cid))
    for mask in (0,7):
        for cid in ids_for(data['fixture']['carry'],'carry',profile=True):expected_parity.add(('intact',mask,cid))
    assert parity_seen==expected_parity
    assert counts['fixture_calls']+2*counts['adapter_parity']==calibration['budget']['calls']
    choices=read_compressed(OUT/'calibration_choices.json.gz');selections=read_compressed(OUT/'selections.json.gz');expected_valid=defaultdict(set)
    for index,(key,p) in enumerate(pools.items()):
        origin=p['origin']
        for arm in ARMS:
            rows={i['id']:replayed['calibration'][origin][aliases[key][arm][i['id']]] for i in p['items']}
            for shaping in (True,False):
                actual=choose(p,rows,data['calibration'][origin].metadata,seed_for(SEED,'reproduction',index,0),shaping)
                assert actual==choices[key][arm][str(shaping)]
                for itemid,rs in rows.items():assert independent_rank(rs,data['calibration'][origin].metadata,shaping)==actual['fitness'][itemid]
                counts['reproductive_draws']+=64;counts['selection_records']+=1
            nominated=choices[key][arm]['True']['nominees'];small=dict(p,items=[i for i in p['items'] if i['id'] in nominated])
            expected_valid[origin].update(aliases[key][arm][i] for i in nominated)
            vr={i['id']:replayed['validation'][origin][aliases[key][arm][i['id']]] for i in small['items']}
            result=choose(small,vr,data['validation'][origin].metadata,seed_for(SEED,'validation_selection',index,0))
            expected=dict(item=next(i for i in p['items'] if i['id']==result['best']),rank=result['rank'],nominees=nominated)
            assert expected==selections[key][arm];counts['validated_choices']+=1
    vquery=read_compressed(OUT/'validation/query.json.gz');assert {k:sorted(v) for k,v in expected_valid.items()}==vquery['models']
    fm,fa,fb,control=final_panel(pools,selections)
    assert fm==read_compressed(OUT/'confirmation/models.json.gz') and fa==read_compressed(OUT/'confirmation/aliases.json.gz')
    assert fb==read_compressed(OUT/'confirmation/query.json.gz')['models']
    for origin,rows in replayed['confirmation'].items():assert all(r['optimal'] or r['no_path'] for r in rows[control])
    expected={(o,n,cid) for o,ids in read_compressed(OUT/'confirmation/query.json.gz')['ids'].items() for n in ('compiled_bfs','compiled_astar','wave_bit') for cid in ids};seen=set()
    for rec in lines(OUT/'confirmation/baselines.jsonl.gz'):
        cid=rec['row']['case'];key=rec['origin'],rec['model'],cid;assert key in expected and key not in seen;seen.add(key)
        o=allcases[cid];m=o.maze;r=normal_old(baseline(rec['model'],m.cells,m.w,m.h,m.start,m.goal),o);assert r==rec['row'] and (r['optimal'] or r['no_path'])
        checker.row(r);counts['baseline_replays']+=1
    assert seen==expected
    run=json.loads((OUT/'selection_execution.json').read_text());final=json.loads((OUT/'confirmation/execution.json').read_text())
    assert run['complete'] and final['complete'] and run['budget']['seconds']<480 and final['budget']['seconds']<300
    assert run['budget']['calls']==counts['calibration_calls']+counts['validation_calls'] and run['budget']['work']==basework['calibration']+basework['validation']
    assert final['budget']['calls']==counts['confirmation_calls']==final['planned_calls'] and final['budget']['work']==basework['confirmation']
    counts['independently_graded_rasters']=checker.rasters
    result=dict(passed=True,counts=dict(counts),source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(OUT/'verification.json',result);print(json.dumps(result,indent=2),flush=True)
