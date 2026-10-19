"""V12I independent graph/mask checks and exact fixed-pool replay audit."""
from collections import Counter, defaultdict
import json
import resource
import time

import numpy as np
from .baselines import baseline
from .evaluator import assess
from .foundation_calibration import ROOT, controls, write_json
from .foundation_data import FoundationData, layout_hash
from .foundation_pair_confirm import normal_row
from .foundation_study import compressed_json, read_compressed
from .foundation_study_verify_core import Checker
from .route_confirmation_audit import adjacent, graph_distances
from .routing_transfer_audit import synthetic
from .routing_transfer import canonical, lines, sha
from .validation_breadth_data import (OUT, FIXTURES, N, FAMILIES, PREFIXES, TAILS,
    load, exclusions)
from .validation_breadth import (inventory, read_pool, organism, react, summarize,
    selections, check_freeze, warm, Budget)


def geometry(cases, contexts, metadata):
    counts=Counter(); seen=set(); layouts=set()
    for c in contexts:
        assert len(c['poses'])==8
        stratum=c['stratum']; first=c['poses'][0]
        for pose in c['poses']:
            s=pose['symmetry']; meta=pose['meta']; noise=set(meta['clutter'])
            assert len(noise)==8
            prefix,*tails=meta['lengths']
            assert PREFIXES[stratum//2][0]<=prefix<=PREFIXES[stratum//2][1]
            assert all(TAILS[stratum%2][0]<=t<=TAILS[stratum%2][1] for t in tails)
            fork=set(meta['paths'][0])|set(meta['paths'][1])
            expected=dict(fork=fork,two_junction=fork|set(meta['stub']),
                alternate_cycle=fork|set(meta['detour']),corridor_0=set(meta['paths'][0]),
                corridor_1=set(meta['paths'][1]),disconnected=(fork|set(meta['detour']))-{meta['decision']['vertex']})
            for family,ids in pose['cases'].items():
                assert len(ids)==(1 if family.startswith('corridor_') else 2)
                if len(ids)==2:
                    a,b=[cases[cid].maze for cid in ids]
                    assert a.cells==b.cells and a.start==b.start and a.goal!=b.goal
                hashed=layout_hash(cases[ids[0]].maze)
                assert hashed not in layouts; layouts.add(hashed)
                for cid in ids:
                    assert cid not in seen; seen.add(cid)
                    o=cases[cid]; m=o.maze; md=metadata[cid]; side=md['side']
                    assert md==dict(base=c['id'],index=c['index'],stratum=stratum,
                        family='corridor' if family.startswith('corridor_') else family,side=side,symmetry=s)
                    assert (m.w,m.h,m.start,m.goal)==(N,N,meta['start'],meta['goals'][side])
                    assert set(np.flatnonzero(np.frombuffer(m.cells,np.uint8)))==expected[family]|noise
                    original=cases[first['cases'][family][0 if family.startswith('corridor_') else side]].maze
                    grid=np.frombuffer(original.cells,np.uint8).reshape(N,N); labels=np.arange(N*N).reshape(N,N)
                    if s>=4: grid=np.fliplr(grid); labels=np.fliplr(labels)
                    grid=np.rot90(grid,-(s%4)); labels=np.rot90(labels,-(s%4))
                    assert grid.tobytes()==m.cells
                    assert np.flatnonzero(labels.ravel()==original.start)[0]==m.start
                    assert np.flatnonzero(labels.ravel()==original.goal)[0]==m.goal
                    ds=graph_distances(m.cells,N,m.start); dg=graph_distances(m.cells,N,m.goal)
                    assert ds==o._from_start and dg==o.to_goal
                    assert all(ds[p]<0 and not any(m.cells[q] for q in adjacent(p,N,N*N)) for p in noise)
                    if family=='disconnected':
                        assert ds[m.goal]<0 and not o.path; counts['no_path_cases']+=1
                        continue
                    path=meta['paths'][side]
                    assert o.path==path and len(path)-1==prefix+tails[side]==ds[m.goal]
                    assert path[:prefix+1]==meta['decision']['prefix']
                    assert assess(synthetic(o,path),o).optimal
                    # Independently count shortest paths, not just one BFS path.
                    ways=[0]*(N*N); ways[m.start]=1
                    for p in sorted((p for p,d in enumerate(ds) if d>=0),key=ds.__getitem__):
                        for q in adjacent(p,N,N*N):
                            if ds[q]==ds[p]+1: ways[q]+=ways[p]
                    assert ways[m.goal]==1
                    component={p for p,d in enumerate(ds) if d>=0}
                    degrees={p:sum(q in component for q in adjacent(p,N,N*N)) for p in component}
                    assert sum(degrees.values())//2-len(component)+1==int(family=='alternate_cycle')
                    if family in FAMILIES:
                        assert sum(d==3 for d in degrees.values())==dict(fork=1,two_junction=2,alternate_cycle=3)[family]
                        assert max(degrees.values())==3
                        label=meta['decision']; v=label['vertex']
                        assert o._foundation_label==label and ds[v]==prefix
                        exits={q for q in adjacent(v,N,N*N) if m.cells[q] and q!=label['incoming']}
                        assert exits==set(label['exits'])
                        assert {q for q in exits if dg[q]+1==dg[v]}==set(label['allowed'][side])
                        counts['decision_labels']+=1
                    else:
                        assert max(degrees.values())==2
                    if family=='alternate_cycle':
                        alt=meta['alternatives'][side]; result=assess(synthetic(o,alt),o)
                        assert result.valid_path and not result.optimal
                        assert len(alt)-len(path)==meta['gaps'][side]>0
                        assert set(alt)-set(path) and set(path)-set(alt)
                        counts['legal_longer_masks']+=1
                    counts['reachable_cases']+=1
    assert seen==set(cases)==set(metadata)
    return dict(counts,contexts=len(contexts),whole_layouts=len(layouts),cases=len(cases))


def schedule_check(schedule,metadata):
    for rep,arms in schedule.items():
        counts={}; bases={}
        assert set(arms)=={'narrow','broad'}
        for arm,ids in arms.items():
            assert len(ids)==len(set(ids))==128
            counts[arm]=Counter((metadata[c]['stratum'],metadata[c]['family'],metadata[c]['side'],metadata[c]['symmetry']) for c in ids)
            bases[arm]={metadata[c]['base'] for c in ids}
            grouped=defaultdict(list)
            for cid in ids:
                m=metadata[cid]
                if m['family'] in FAMILIES:
                    grouped[m['base'],m['family'],m['symmetry']].append(m['side'])
            assert len(grouped)==48 and all(sorted(sides)==[0,1] for sides in grouped.values())
        assert counts['narrow']==counts['broad']
        assert len(bases['narrow'])==4 and len(bases['broad'])==16
        assert not bases['narrow']&bases['broad']


def audit():
    assert not (OUT/'verification.json').exists()
    started=time.perf_counter(); prereg=check_freeze(); warmed=warm()
    pool=read_pool(); rebuilt=inventory(); assert canonical(pool)==canonical(rebuilt)
    for name,digest in pool['input_sha256'].items(): assert sha(ROOT/name)==digest
    selection_freeze=json.loads((OUT/'selection_freeze.json').read_text())
    assert sha(OUT/'selections.json.gz')==selection_freeze['selections_sha256']
    for name,digest in selection_freeze['validation_sha256'].items(): assert sha(ROOT/name)==digest
    # Verify every earlier completion artifact without rerunning closed studies.
    prior_verified=0
    for study in ('fork_pressure','routing_transfer'):
        packet=json.loads((ROOT/'results'/study/'completion.json').read_text())
        mapping=packet['source_and_artifact_sha256']
        assert mapping, packet.keys()
        for name,digest in mapping.items():
            assert sha(ROOT/name)==digest,name; prior_verified+=1
    previous=FoundationData(0,exclusions()).layouts
    assert len(previous)==138904
    all_data={}; graphs={}
    for split,path in [('fixtures',FIXTURES),('validation',OUT/'validation'),('final',OUT/'confirmation')]:
        cases,contexts,metadata=load(path); all_data[split]=(cases,contexts,metadata)
        graphs[split]=geometry(cases,contexts,metadata)
        layouts={layout_hash(o.maze) for o in cases.values()}
        assert not previous&layouts; previous.update(layouts)
    schedule=json.loads((OUT/'validation/schedule.json').read_text())
    schedule_check(schedule,all_data['validation'][2])
    budget=Budget(); graded=0; baseline_calls=0; scores={str(r):{a:{} for a in ('narrow','broad')} for r in range(3)}
    baseline_summaries={}; final_summaries={}; seen=set()
    for split,path in [('fixtures',FIXTURES/'outputs.jsonl.gz'),('validation',OUT/'validation/outputs.jsonl.gz'),('final',OUT/'confirmation/outputs.jsonl.gz')]:
        cases,contexts,metadata=all_data[split]; checker=Checker(cases); profile_seen=set()
        for packet in lines(path):
            mk=packet['model']
            entry=(dict(item=controls()[mk.split('/')[1]].save(),topology='local') if mk.startswith('known/') else pool['models'][mk])
            org=organism(entry)
            ids=[r['case'] for r in packet['rows']]
            if split=='validation':
                rep=str(packet['replicate']); arm=packet['arm']
                assert ids==schedule[rep][arm]
                key=(rep,arm,mk); assert key not in seen; seen.add(key)
            elif split=='final':
                assert ids==list(cases)
                assert mk not in final_summaries
            else:
                assert mk not in profile_seen; profile_seen.add(mk)
                expected=list(cases) if mk.startswith('known/') else [c['poses'][0]['cases']['fork'][0] for c in contexts]
                assert ids==expected
            for row in packet['rows']:
                checker.row(row); o=cases[row['case']]
                result=budget.call('replay/'+split,org,o)
                assert canonical(normal_row(result,o))==row
            summary=summarize(packet['rows'],metadata)
            if split=='validation': scores[rep][arm][mk]=summary
            if split=='final': final_summaries[mk]=summary
        if split=='fixtures':
            assert profile_seen==set(pool['models'])|{'known/intact','known/west_return_gate'}
        graded+=checker.rasters
    expected={(str(c['config']['replicate']),arm,m) for c in pool['conditions'].values() for arm in ('narrow','broad') for m in c['models']}
    assert seen==expected
    assert scores==read_compressed(OUT/'validation/scores.json.gz')
    chosen=selections(pool,scores)
    assert chosen==read_compressed(OUT/'selections.json.gz')
    final_models={v['model'] for c in chosen.values() for v in c.values()}|{'known/intact','known/west_return_gate'}
    assert set(final_summaries)==final_models
    cases,_,metadata=all_data['final']; checker=Checker(cases)
    for packet in lines(OUT/'confirmation/baselines.jsonl.gz'):
        assert [r['case'] for r in packet['rows']]==list(cases)
        for row in packet['rows']:
            checker.row(row); o=cases[row['case']]; m=o.maze
            r=baseline(packet['model'],m.cells,m.w,m.h,m.start,m.goal)
            assert canonical(normal_row(r,o))==row; baseline_calls+=1
        baseline_summaries[packet['model']]=summarize(packet['rows'],metadata)
    graded+=checker.rasters
    assert {**final_summaries,**baseline_summaries}==read_compressed(OUT/'confirmation/summaries.json.gz')
    original=json.loads((OUT/'confirmation/summary.json').read_text())['budget']
    profile=json.loads((FIXTURES/'calibration.json').read_text())['budget']
    assert original['calls']+profile['calls']==budget.calls
    assert original['work']+profile['work']==budget.work
    for arm in ('narrow','broad'):
        n=128*sum(len({m for c in pool['conditions'].values() if c['config']['replicate']==rep for m in c['models']}) for rep in range(3))
        assert original['scopes']['validation/'+arm]['calls']==n
    from .validation_breadth_analysis import analyze
    assert analyze(save=False)==json.loads((OUT/'analysis.json').read_text())
    result=dict(passed=True,source_hashes=len(prereg['source_sha256']),input_hashes=len(prereg['input_sha256']),
        pool_source_hashes=len(pool['input_sha256']),prior_completion_hashes=prior_verified,
        geometry=graphs,resulting_layouts=len(previous),graded_rasters=graded,budget=vars(budget),
        baseline_replays=baseline_calls,condition_arm_choices=60,physical_final_models=len(final_models),
        warmup=warmed,wall_seconds=time.perf_counter()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # JSON encoding is checked before installing the completion artifact.
    canonical(result); write_json(OUT/'verification.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__': audit()
