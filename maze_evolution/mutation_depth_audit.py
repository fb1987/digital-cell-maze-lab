"""V12O streaming exact replay and independent normal-output/selection checks."""
import json,time,resource
from collections import defaultdict
from .foundation_calibration import ROOT,write_json
from .foundation_study import read_compressed
from .foundation_study_verify_core import Checker
from .branch_pressure_audit import geometry,independent_proxy
from .mutation_depth_data import *
from .mutation_depth_metrics import summarize,nominate,supply,rank,compare
from .routing_transfer import sha,canonical,lines
from .datasets import seed_for,manifest
from .exposure_selection import organism,record
from .foundation_pair_confirm import normal_row
from .baselines import baseline


def independent_scores(rows,meta,metrics):
    pairs=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family']=='paired':pairs[m['base'],m['pose']].append(r)
    details={(d['base'],d['pose']):d for d in metrics['details']}
    for key,rs in pairs.items():
        ip=independent_proxy(rs,meta);d=details[key]
        for field in ('eligible','score','contrast','strict_both','positive'):assert ip[field]==d[field]
        rs=sorted(rs,key=lambda r:meta[r['case']]['side']);paths=[meta[r['case']]['path'] for r in rs];goals={p[-1] for p in paths};private=[[p for p in paths[k] if p not in paths[1-k] and p not in goals] for k in range(2)]
        normal=all(r['status']=='emitted' for r in rs);bits=[bytes.fromhex(r['mask']) for r in rs]
        at=lambda k,p:bool(bits[k][p//8] & (1<<(p%8)))
        signed=sum(sum(int(at(k,p))-int(at(1-k,p)) for p in private[k])/len(private[k]) for k in range(2))/2 if all(private) and normal else 0.
        assert signed==d['signed'] and normal==d['normal_both']
        assert (any(at(0,p)!=at(1,p) for p in range(81) if p not in goals) and normal)==d['switch_away']
    assert len(pairs)==len(details)


def independent_comparison(child,root):
    cs,rs=child['details'],root['details'];assert [(r['base'],r['pose']) for r in cs]==[(r['base'],r['pose']) for r in rs]
    gains=[a for a,b in zip(cs,rs) if a['eligible'] and a['score']>0 and a['score']>=b['score']+.1-1e-12]
    result=dict(useful=child['mean_score']>=.01 and child['positive_pairs']>=2 and len(gains)>=2,
        mask_changed=child['mask_signature']!=root['mask_signature'],counter_changed=child['counter_signature']!=root['counter_signature'],response_changed=child['response_signature']!=root['response_signature'],
        new_positive_pairs=len(gains),new_positive_templates=len({r['base'] for r in gains}),lost_positive_pairs=sum(b['score']>0 and a['score']==0 for a,b in zip(cs,rs)),
        new_nonadj_pairs=sum(a['complete'] and not b['complete'] and a['kind']!='adjacent' for a,b in zip(cs,rs)),pair_gain=child['pairs']-root['pairs'],corridor_gain=child['corridors']-root['corridors'])
    assert result==compare(child,root);return result


def check_nomination(ids,pool,metrics,aliases,saved):
    ranks={};comparisons={}
    for i in ids:
        e=pool['entries'][i];m=metrics[aliases[i]];c=independent_comparison(m,metrics[aliases[e['reference']]])
        ranks[i]=(m['nonadj_pairs'],int(c['useful']),round(m['mean_score'],10),m['strict_pairs'],m['pairs'],m['corridors'],m['no_path']-m['false_no_path']);comparisons[i]=c
    order=sorted(ids,key=lambda i:(tuple(-v for v in ranks[i]),pool['entries'][i]['program_digest'],i))
    expected=dict(nominees=order[:2],best=order[0],rank=list(ranks[order[0]]),order=order,comparisons={i:comparisons[i] for i in order})
    assert expected==saved==nominate(ids,pool['entries'],metrics,aliases)


def audit():
    from .mutation_depth_study import check_freeze,make_pools,final_panel,discovery_gates,analysis_packet
    from .branch_pressure_study import loaded
    t=time.perf_counter();reg=check_freeze();counts=defaultdict(int)
    for name in ('fork_pressure','routing_transfer','validation_breadth','junction_distance','robustness_pressure','lineage_confirmation','exposure_calibration','branch_pressure_calibration'):
        for p,h in json.loads((ROOT/'results'/name/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/p)==h,p;counts['prior_completion_hashes']+=1
    values=make_pools()
    for name,value in zip(('pools','events','walks','random_rng','models','aliases'),values):assert value==read_compressed(OUT/f'{name}.json.gz'),name
    pool,events,walks,random_states,models,aliases=values;counts['mutation_steps']=len(events);counts['walks']=len(walks);counts['random_draws']=576;counts['preserved_founders']=288
    del events,walks,random_states,values
    previous=exclusions();datasets={};allcases={}
    for scope,path,seed,repeats in [('fixture',FIXTURES,FIXTURE_SEED,1),('discovery',OUT/'discovery',SEED,1),('validation',OUT/'validation',seed_for(SEED,'validation',0,0),1),('confirmation',OUT/'confirmation',seed_for(SEED,'confirmation',0,0),2)]:
        actual=create(seed,scope,previous,repeats);d=loaded(path);counts['graph_cases']+=geometry(d)
        assert canonical(manifest(actual.cache.values()))==read_compressed(path/'mazes.json.gz');assert canonical(actual.contexts)==d.contexts and canonical(actual.metadata)==d.metadata
        if scope!='fixture':
            for p,h in json.loads((path/'generation.json').read_text())['hashes'].items():assert sha(ROOT/p)==h,p
            assert read_compressed(path/'query.json.gz')==query(actual,True)
            assert {m['pose'] for m in d.metadata.values()}==set(range(8))
        previous+=read_compressed(path/'mazes.json.gz');datasets[scope]=d;allcases.update(d.cache)
    counts['whole_layouts_through_O']=len(actual.layouts);del previous,actual
    checker=Checker(allcases);orgs={};metrics={};works={}
    for scope,path,file in [('fixture',FIXTURES,'profiles.jsonl.gz'),('discovery',OUT/'discovery','responses.jsonl.gz'),('validation',OUT/'validation','responses.jsonl.gz'),('confirmation',OUT/'confirmation','responses.jsonl.gz')]:
        current=models if scope=='fixture' else read_compressed(path/'models.json.gz');d=datasets[scope];ids=[cid for cid,m in d.metadata.items() if m['pose']==0] if scope=='fixture' else read_compressed(path/'query.json.gz');order=sorted(current);model_index=0;row_index=0;rows=[];work=0;stage_start=time.perf_counter();compact={}
        saved=None if scope=='fixture' else read_compressed(path/'metrics.json.gz')
        for rec in lines(path/file):
            key,cid=rec['model'],rec['row']['case'];assert key==order[model_index] and cid==ids[row_index]
            if key not in orgs:orgs[key]=organism(current[key])
            o=allcases[cid];m=o.maze;r=record(orgs[key].react(m.cells,m.w,m.h,m.start,m.goal),o);assert canonical(r)==rec['row'],(scope,key,cid)
            checker.row(r);counts['candidate_replays']+=1;work+=r['reads']+r['dispatches']+r['exposure_checks'];rows.append(r);row_index+=1
            if row_index==len(ids):
                if saved is not None:
                    compact[key]=summarize(rows,d.metadata);assert compact[key]==saved[key];independent_scores(rows,d.metadata,compact[key]);counts['independent_model_scores']+=1
                model_index+=1;row_index=0;rows=[]
                if model_index%500==0:print(json.dumps(dict(scope=scope,models=model_index,replays=counts['candidate_replays'],seconds=round(time.perf_counter()-stage_start,2))),flush=True)
        assert model_index==len(order) and row_index==0;counts[scope+'_calls']=len(order)*len(ids);works[scope]=work;metrics[scope]=compact
        if saved is not None:assert set(compact)==set(saved)
        print(json.dumps(dict(scope=scope,complete=True,calls=counts[scope+'_calls'],seconds=time.perf_counter()-stage_start)),flush=True)
    choices=read_compressed(OUT/'discovery_choices.json.gz');selections=read_compressed(OUT/'selections.json.gz');expected_valid=set()
    for rep,arms in pool['groups'].items():
        for top in TOPS:
            key=f'{rep}/{top}'
            for arm,ids in arms.items():
                check_nomination(ids,pool,metrics['discovery'],aliases[top],choices[key][arm]);counts['nominee_ranks']+=len(ids)
                chosen=choices[key][arm]['nominees'];check_nomination(chosen,pool,metrics['validation'],aliases[top],selections[key][arm]);counts['validated_choices']+=1
                for i in chosen:
                    for j in (i,pool['entries'][i]['reference']):expected_valid.add(aliases[top][j])
    assert expected_valid==set(metrics['validation'])
    dg=discovery_gates(pool,metrics['discovery'],aliases);assert dg==json.loads((OUT/'discovery_gates.json').read_text())
    for key,g in dg.items():
        rep,top=key.split('/')
        for arm,ss in g['supply'].items():
            useful=[i for i in pool['groups'][rep][arm] if independent_comparison(metrics['discovery'][aliases[top][i]],metrics['discovery'][aliases[top][pool['entries'][i]['reference']]])['useful']]
            assert useful==ss['useful_ids'] and len(useful)==ss['useful_count']
            assert len({pool['entries'][i]['reference'] for i in useful})==ss['useful_references']
            assert len({metrics['discovery'][aliases[top][i]]['paired_signature'] for i in useful})==ss['useful_behaviors']
        for depth in ('depth4','depth16'):
            s=g['supply'][depth];ok=s['useful_count']>=4 and s['useful_references']>=2 and s['useful_behaviors']>=2 and s['useful_count']>=2+max(g['supply'][a]['useful_count'] for a in ('depth1','single','resample'))
            assert ok==g['passed'][depth]
    fm,fp,control=final_panel();assert fm==read_compressed(OUT/'confirmation/models.json.gz') and fp==read_compressed(OUT/'confirmation/panel.json.gz')
    assert metrics['confirmation'][control]['optimal']==640 and metrics['confirmation'][control]['no_path']==320
    result=analysis_packet();assert result==read_compressed(OUT/'analysis.json.gz');passing={f'{d}/{top}':[] for d in ('depth4','depth16') for top in TOPS}
    for key,r in result['results'].items():
        for depth in ('depth4','depth16'):
            a=r['arms'][depth];c=independent_comparison(a['metrics'],a['reference_metrics']);m=a['metrics'];cs=[r['arms'][k]['metrics'] for k in ('depth1','single','resample')]
            ok=m['mean_score']>=.01 and c['new_positive_pairs']>=4 and c['new_positive_templates']>=2 and c['response_changed'] and (m['nonadj_pairs']>max(x['nonadj_pairs'] for x in cs) or m['mean_score']>=max(x['mean_score'] for x in cs)+.005-1e-12)
            assert bool(ok)==r['gates'][depth]['final_passed'];combined=bool(ok and dg[key]['passed'][depth]);assert combined==r['gates'][depth]['combined_passed']
            if combined:rep,top=key.split('/');passing[f'{depth}/{top}'].append(int(rep))
    assert passing==result['passing_groups'] and result['exploration_ready']==any(len(v)>=2 for v in passing.values())
    seen=set();ids=read_compressed(OUT/'confirmation/query.json.gz')
    for rec in lines(OUT/'confirmation/baselines.jsonl.gz'):
        key,cid=rec['model'],rec['row']['case'];assert (key,cid) not in seen;seen.add((key,cid));o=allcases[cid];m=o.maze;r=canonical(normal_row(baseline(key,m.cells,m.w,m.h,m.start,m.goal),o));assert r==rec['row'] and (r['optimal'] or r['no_path']);checker.row(r)
    assert seen=={(name,cid) for name in ('compiled_bfs','compiled_astar','wave_bit') for cid in ids};counts['baseline_replays']=len(seen)
    profile=json.loads((FIXTURES/'profile.json').read_text());rates=read_compressed(FIXTURES/'rates.json.gz');run=json.loads((OUT/'selection_execution.json').read_text());final=json.loads((OUT/'confirmation/execution.json').read_text())
    assert set(rates)==set(models) and abs(sum(rates.values())*60-profile['budget']['seconds'])<1e-8
    projected=8*profile['budget']['seconds']+(120*480+90*960)*max(rates.values());assert abs(projected-profile['projected_total'])<1e-8 and profile['passed']==(projected<648)
    assert profile['budget']['calls']==counts['fixture_calls'] and profile['budget']['work']==works['fixture'] and profile['budget']['seconds']<120
    assert run['complete'] and final['complete'] and final['initial_budget']==run['budget']
    assert run['budget']['calls']==counts['discovery_calls']+counts['validation_calls'] and run['budget']['work']==works['discovery']+works['validation']
    assert final['budget']['calls']==counts['discovery_calls']+counts['validation_calls']+counts['confirmation_calls']<=3400000 and final['budget']['work']==works['discovery']+works['validation']+works['confirmation'] and final['budget']['seconds']<720
    for packet in (profile,run,final):assert packet['peak_rss_bytes']<4*2**30
    counts['independent_rasters']=checker.rasters
    packet=dict(passed=True,counts=dict(counts),source_hashes=len(reg['sources']),input_hashes=len(reg['inputs']),wall_seconds=time.perf_counter()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(OUT/'verification.json',packet);print(json.dumps(packet,indent=2),flush=True)
