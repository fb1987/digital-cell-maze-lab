"""Posthoc M30 saved-array interpretation only; no inference, new inputs or selection."""
import json,sys,zlib
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.information_flow_m30 import OUT,readz,read_records,writej,check
from maze_evolution.deep_campaign_data import cases_from_manifest
from maze_evolution.evaluator import distances

def main():
    check();assert not (OUT/'interpretation.json').exists();assert json.loads((OUT/'audit.json').read_text())['status']=='PASS'
    d=readz(OUT/'cases.json.gz');s=readz(OUT/'sources.json.gz');cases=cases_from_manifest(d['mazes']);records=read_records()
    native={};rr={};contrasts=[]
    for spec,r,blob in records:
        if spec['phase']=='native':
            native[r['role'],r['case']]=np.frombuffer(zlib.decompress(blob),dtype='<u2').reshape(r['history_shape']);rr[r['role'],r['case']]=r
        else:contrasts.append(r)
    core=[0,1,3,4,5,7];matches=0;core_values=0
    for cid in d['queries']['all']:
        hs=[native[k,cid] for k in s['focal']];end=min(len(h) for h in hs)
        assert all(np.array_equal(hs[0][:end,core],h[:end,core]) for h in hs[1:]);matches+=1;core_values+=hs[0][:end,core].size
    result={};details=[]
    for role in (*s['focal'],'control'):
        cases_with_wrong=cases_with_erasure=0;wrong_never_erased=0;positive_erasures=0;bad_pixels=0;earliest=[];work=[];lengths=[];byfail=Counter();arms=Counter();monotone_c7=True;stable_c1=True
        for cid in d['queries']['new']:
            h=native[role,cid];o=cases[cid];r=rr[role,cid]['row'];mask=h[:,2]>0
            if o.path:
                lengths.append(len(o.path)-1);byfail[r['failure']]+=1
                ds=distances(o.maze,o.maze.start);dg=o.to_goal;distance=len(o.path)-1
                any_shortest=np.array([a>=0 and b>=0 and a+b==distance for a,b in zip(ds,dg)])
                bad=mask&~any_shortest[None,:];bad_times=np.flatnonzero(np.any(bad,axis=1))
                if len(bad_times):
                    cases_with_wrong+=1;earliest.append(int(bad_times[0]));bad_pixels+=int(np.count_nonzero(np.any(bad,axis=0)))
                    erased=np.any(bad[:-1]&~mask[1:]);cases_with_erasure+=bool(erased);wrong_never_erased+=not bool(erased)
                losses=np.count_nonzero(mask[:-1]&~mask[1:]);positive_erasures+=int(losses)
                cs=np.flatnonzero(np.frombuffer(o.maze.cells,np.uint8));monotone_c7 &= bool(np.all(h[1:,7,cs]>=h[:-1,7,cs]))
                stable_c1 &= not bool(np.any((h[:-1,1,cs]>0)&(h[1:,1,cs]==0)&(cs[None,:]!=o.maze.goal)))
                obs=d['metadata'][cid]['observers'];arms[str([bool(mask[-1,obs[1]]),bool(mask[-1,obs[2]])])]+=1
                details.append(dict(role=role,case=cid,variant=d['metadata'][cid]['variant'],oracle_edges=distance,
                    failure=r['failure'],first_off_any_shortest_pixel_tick=int(bad_times[0]) if len(bad_times) else None,
                    any_off_shortest_erasure=bool(np.any(bad[:-1]&~mask[1:])),terminal_off_shortest_pixels=int(np.count_nonzero(bad[-1])),
                    output_pixels=int(np.count_nonzero(mask[-1])),oracle_pixels=len(o.path),steps=r['steps']))
            work.append(r['reads']+r['dispatches'])
        swaps=[c for c in contrasts if c['role']==role and c['kind']=='route_swap']
        routes_correct=sum(c['positive_arms_a']==[True,False] and c['positive_arms_b']==[False,True] for c in swaps)
        # Inspect independent causal contrasts at the FIRST difference; do not imply later mediation.
        intervention=defaultdict(Counter)
        for c in contrasts:
            if c['role']!=role:continue
            for a in c['intervention']:
                intervention[str(a['channel'])]['events']+=1
                intervention[str(a['channel'])]['single_restoration_exists']+=bool(a['single_channel_exact_partner_restorations'])
                for ch in a['single_channel_exact_partner_restorations']:intervention[str(a['channel'])]['single_'+str(ch)]+=1
        result[role]=dict(reachable_presentations=len(lengths),reachable_failure_counts=dict(byfail),cases_ever_off_any_shortest_path=cases_with_wrong,
            cases_erasing_any_wrong_pixel=cases_with_erasure,cases_with_wrong_pixels_never_erased=wrong_never_erased,total_distinct_wrong_pixel_presentations=bad_pixels,
            all_positive_C2_erasure_events=positive_erasures,first_wrong_tick_histogram=dict(Counter(earliest)),
            positive_goal_signal_stays_present_after_first_noninitial_activation=stable_c1,C7_nondecreasing=monotone_c7,
            terminal_arm_patterns=dict(arms),route_swaps_correct_exclusive_arm_choice_both=routes_correct,
            intervention=dict(intervention),native_new_work=sum(work),reachable_edge_lengths=dict(Counter(lengths)))
    # Independent scalar re-count verifies the irreversible-error endpoint for the 720 focal reachable presentations.
    scalar_wrong=scalar_cases=scalar_erasures=0
    for item in details:
        if item['role']=='control':continue
        h=native[item['role'],item['case']];o=cases[item['case']];ds=distances(o.maze,o.maze.start);bad=set()
        for p in range(len(o.maze.cells)):
            if ds[p]<0 or o.to_goal[p]<0 or ds[p]+o.to_goal[p]!=len(o.path)-1:
                ts=[t for t in range(len(h)) if int(h[t,2,p])>0]
                if ts:
                    bad.add(p)
                    for t in ts:
                        if t+1<len(h) and int(h[t+1,2,p])==0:scalar_erasures+=1
        scalar_cases+=bool(bad);scalar_wrong+=len(bad)
    assert scalar_cases==sum(v['cases_ever_off_any_shortest_path'] for k,v in result.items() if k!='control')
    assert scalar_wrong==sum(v['total_distinct_wrong_pixel_presentations'] for k,v in result.items() if k!='control')
    assert scalar_erasures==sum(v['cases_erasing_any_wrong_pixel'] for k,v in result.items() if k!='control')==0
    writej(OUT/'interpretation.json',dict(saved_only_posthoc=True,no_inference_or_new_layout=True,
        common_core=dict(channels=core,all_three_focal_histories_equal_on_common_native_windows=matches,core_site_channel_tick_values_per_reference=core_values,
            algebra='C2 and C6 have no functional return edge into C0/C1/C3/C4/C5/C7. Dead/costing reads remain in native VM. Shared propagation core plus alternative readout, not three independently different propagation mechanisms.'),
        by_role=result,independent_scalar_wrong_pixel_recount=dict(status='PASS',reachable_focal_presentations=len([x for x in details if x['role']!='control']),cases=scalar_cases,pixel_presentations=scalar_wrong,erasures=scalar_erasures),
        limitation='Saved-only secondary analysis, not a preregistered new endpoint or new experiment. Off-shortest means outside the UNION of all shortest paths (not just the selected BFS route). Irreversibility does not prove erasure is required for every general solver; a correct solver can defer irreversible writes.'))
    from maze_evolution.foundation_study import compressed_json
    compressed_json(OUT/'wrong_pixel_details.json.gz',details)

if __name__=='__main__':main()
