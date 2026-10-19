"""V12K independent geometry/raster checks and exact candidate/lineage replay."""
from collections import defaultdict
from copy import deepcopy
from io import StringIO
import json,time,resource
import numpy as np
from .foundation_calibration import ROOT,write_json
from .foundation_study import read_compressed
from .foundation_study_verify_core import Checker
from .foundation_data import layout_hash,transform_maze
from .route_confirmation_audit import graph_distances,adjacent
from .routing_transfer_audit import synthetic
from .evaluator import assess,Maze
from .growth import Individual,replay_mutation
from .routing_transfer import lines,sha,canonical,organism,inference
from .foundation_pair_confirm import normal_row
from .baselines import baseline
from .robustness_data import *
from .robustness_search import Search,evaluate,result


def geometry(cases,contexts,meta):
    count=0
    for c in contexts:
        assert len(c['poses'])==8
        for p in c['poses']:
            for f,ids in p['cases'].items():
                for k,cid in enumerate(ids):
                    o=cases[cid];m=o.maze;lab=meta[cid];base=cases[c['poses'][0]['cases'][f][k]].maze
                    transformed=transform_maze(base,p['pose'])
                    assert (transformed.cells,transformed.start,transformed.goal)==(m.cells,m.start,m.goal)
                    ds=graph_distances(m.cells,m.w,m.start);dg=graph_distances(m.cells,m.w,m.goal)
                    assert ds==o._from_start and dg==o.to_goal
                    assert len(o.path)==(ds[m.goal]+1 if ds[m.goal]>=0 else 0)
                    assert ds[lab['junction']]==lab['prefix'] if f!='disconnected' else ds[m.goal]<0
                    assert sum(m.cells[q] for q in adjacent(m.start,m.w,len(m.cells)))==(0 if f=='disconnected' and lab['prefix']==1 else 1)
                    assert sum(m.cells[q] for q in adjacent(m.goal,m.w,len(m.cells)))==1
                    reached={i for i,d in enumerate(ds) if d>=0}
                    edges=sum(sum(q in reached for q in adjacent(v,m.w,len(m.cells))) for v in reached)//2
                    assert edges-len(reached)+1==(1 if f=='cycle' else 0)
                    if f!='disconnected':
                        assert o.path==lab['path'];a=assess(synthetic(o,lab['path']),o);assert a.valid_path and a.optimal
                    if f=='cycle':
                        a=assess(synthetic(o,lab['alternative']),o);assert a.valid_path and not a.optimal
                        assert len(lab['alternative'])>len(lab['path'])
                    for v in lab['clutter']:assert m.cells[v] and not any(m.cells[q] for q in adjacent(v,m.w,len(m.cells)))
                    count+=1
                if f in BRANCHES or f=='disconnected':
                    a,b=(cases[x].maze for x in ids);assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
    assert count==len(cases)
    return dict(cases=count,contexts=len(contexts),whole_layouts=len({layout_hash(o.maze) for o in cases.values()}))


def independent_fitness(rows,meta,policy):
    pairs=defaultdict(list);groups=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family'] in BRANCHES:pairs[(m['base'],m['family'],m['pose'])].append(r)
    for key,rs in pairs.items():
        assert len(rs)==2;success=all(r['optimal'] for r in rs);weak=min(r['partial'] for r in rs)
        for r in rs:assert r['pair_optimal']==success and r['paired_partial']==weak
        groups[key[:2]].append(success)
    context_count=sum(all(v) for v in groups.values())
    for r in rows:
        m=meta[r['case']];branch=m['family'] in BRANCHES
        assert r['branch']==branch
        if branch:assert r['context_complete']==all(groups[(m['base'],m['family'])])
        else:assert not r['context_complete'] and not r['pair_optimal']
    return [context_count if policy=='context' else 0,sum(all(r['optimal'] for r in rs) for rs in pairs.values()),
        sum(r['optimal'] for r in rows),sum(r['valid'] for r in rows),
        sum(int(r['no_path'])-int(r['reachable'] and r['status']=='no_path') for r in rows),
        round(sum(r['partial']+r['paired_partial'] for r in rows),8),
        -sum(r['reads']+r['dispatches'] for r in rows) if all(r['optimal'] or r['no_path'] for r in rows) else 0]


def audit():
    from .robustness_study import check_freeze
    started=time.perf_counter();packet=check_freeze();counts=defaultdict(int)
    for name in ('fork_pressure','routing_transfer','validation_breadth','junction_distance'):
        old=json.loads((ROOT/'results'/name/'completion.json').read_text())
        for p,h in old['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;counts['prior_completion_hashes']+=1
    previous={layout_hash(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'])) for r in exclusions()}
    assert len(previous)==150776;allcases={};allmeta={}
    for scope,path in [('fixtures',FIXTURES),('diagnostic',OUT/'diagnostic'),('search',OUT/'search'),('final',OUT/'final')]:
        cases,contexts,meta=load(path);g=geometry(cases,contexts,meta);layouts={layout_hash(o.maze) for o in cases.values()}
        assert not previous&layouts;previous|=layouts
        if scope=='fixtures':
            previous.update(layout_hash(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'])) for r in read_compressed(FIXTURES/'geometry_test_mazes.json.gz'))
        allcases.update(cases);allmeta.update(meta);counts['graph_cases']+=g['cases']
        if scope in ('diagnostic','final'):
            for p,h in json.loads((path/'generation.json').read_text())['hashes'].items():assert sha(ROOT/p)==h,p
    checker=Checker(allcases);states=read_compressed(OUT/'initial_states.json.gz');final=read_compressed(OUT/'checkpoint.latest.json.gz')
    summary=json.loads((OUT/'search_summary.json').read_text());assert sha(OUT/'frozen_selections.json.gz')==summary['frozen_sha256']
    individuals={i['id']:Individual.load(i) for s in states for i in s['population']+s['protected']}
    searches={s['key']:Search(s,StringIO(),StringIO(),allcases,allmeta) for s in states};groups=defaultdict(list)
    for s in searches.values():
        key=(s.config['origin'],s.config['topology'],s.config['replicate']);groups[key].append(s)
        assert all('positive_control' not in i.identity for i in s.population)
    for group in groups.values():
        for s in group:
            assert [i.save() for i in s.population]==[i.save() for i in group[0].population]
            assert s.rng.getstate()==group[0].rng.getstate()
    def check_record(rec,s):
        rows=rec['cases']
        for r in rows:checker.row(r)
        assert rec['fitness']==independent_fitness(rows,allmeta,s.config['policy'])
        ev=evaluate(individuals[rec['id']],[r['case'] for r in rows],allcases,allmeta,s.config['topology'],s.config['policy'])
        assert canonical(ev.rows)==rows and list(ev.fitness)==rec['fitness'] and canonical(ev.descriptor)==rec['descriptor'] and ev.work==rec['work']
        counts['candidate_replays']+=len(rows);counts['fitness_records']+=1
        return ev
    for rec in lines(OUT/'initial_evaluations.jsonl.gz'):
        s=searches[rec['condition']];ev=check_record(rec,s);s.responses+=len(ev.rows);s.work+=ev.work;s.archive(individuals[rec['id']],ev)
    for group in groups.values():
        for s in group:s.archives=deepcopy(group[0].archives);s.frozen=deepcopy(s.archives)
    val=json.loads((OUT/'search/validation_ids.json').read_text())
    for segment in final['segments']:
        g=segment['generation'];registry=list(lines(OUT/segment['files'][0]));newborn={r['id']:r for r in registry};bycondition=defaultdict(list)
        for rec in lines(OUT/segment['files'][1]):
            check_record(rec,searches[rec['condition']]);bycondition[rec['condition']].append(rec)
        for r in registry:
            item=Individual.load(r)
            if item.parent:assert replay_mutation(individuals[item.parent].genome,r['events'],256)==item.genome;counts['mutations']+=1
            individuals[item.identity]=item
        batch_ids=json.loads((OUT/'search'/f'batch_{g:04d}.json').read_text())
        for key,s in searches.items():
            expected=iter(bycondition[key]);written=StringIO();s.registry=written
            def replay(item,ids,split):
                rec=next(expected);assert (rec['id'],rec['split'],rec['generation'])==(item.identity,split,g)
                assert [r['case'] for r in rec['cases']]==ids
                ev=result(rec['cases'],allmeta,s.config['policy']);s.responses+=len(ev.rows);s.work+=ev.work;return ev
            s.evaluate=replay;s.step(batch_ids[str(s.config['replicate'])],val[str(s.config['replicate'])]);assert next(expected,None) is None
            for line in written.getvalue().splitlines():
                r=json.loads(line);assert r==newborn[r['id']];counts['births_replayed']+=1
        print(json.dumps(dict(audited_generation=g,seconds=round(time.perf_counter()-started,1))),flush=True)
    for state in final['states']:assert canonical(searches[state['key']].state())==state,state['key'];counts['final_states']+=1
    assert sum(s.responses for s in searches.values())==summary['physical_calls_completed']
    assert sum(s.work for s in searches.values())==summary['work_completed']
    frozen=read_compressed(OUT/'frozen_selections.json.gz')
    for key,s in searches.items():assert canonical(dict(config=s.config,archives=s.archives,frozen=s.frozen))==frozen[key]
    # Replay fixtures, fixed diagnostic and final, with independent grading and exact counters.
    for scope,path in [('fixtures',FIXTURES),('diagnostic',OUT/'diagnostic'),('final',OUT/'final')]:
        models=read_compressed(OUT/'panel.json.gz' if scope=='fixtures' else path/'models.json.gz');orgs={}
        for rec in lines(path/'responses.jsonl.gz'):
            name,mode=rec['model'],rec['mode'];org=orgs.setdefault((name,mode),organism(models[name],mode))
            o=allcases[rec['row']['case']];checker.row(rec['row']);row=normal_row(inference(org,o.maze,mode),o)
            assert canonical(row)==rec['row'];counts['candidate_replays']+=1
        if scope!='fixtures':
            for rec in lines(path/'baselines.jsonl.gz'):
                o=allcases[rec['row']['case']];m=o.maze;checker.row(rec['row'])
                row=normal_row(baseline(rec['model'],m.cells,m.w,m.h,m.start,m.goal),o)
                assert canonical(row)==rec['row'];counts['baseline_replays']+=1
    for rec in lines(FIXTURES/'profiles.jsonl.gz'):
        s=searches[rec['condition']];item=individuals[rec['id']]
        ev=evaluate(item,[r['case'] for r in rec['cases']],allcases,allmeta,s.config['topology'],'pair')
        assert canonical(ev.rows)==rec['cases']
        for r in rec['cases']:checker.row(r)
        counts['candidate_replays']+=len(rec['cases'])
    counts['rasters']=checker.rasters
    result_packet=dict(passed=True,counts=dict(counts),layout_total=len(previous),seconds=time.perf_counter()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        source_hashes=len(packet['sources']),input_hashes=len(packet['inputs']))
    write_json(OUT/'verification.json',result_packet);print(json.dumps(result_packet,indent=2),flush=True)
