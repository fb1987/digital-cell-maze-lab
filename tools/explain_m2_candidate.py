"""Check a source-derived M2 terminal-mask prediction against saved responses only."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.wave_accessibility import OUT,connect,entries,writej
from maze_evolution.deep_campaign_data import cases_from_manifest
identity='m2/a0/d2/02786';result={}
for final in (False,True):
    if final and not (OUT/'final_summary.json').exists():continue
    db,data,_,_=connect(final)
    rr=next(rows for s,rows in entries(db) if identity in s['aliases']);db.close()
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in {r['case'] for r in rr}])
    checked=matched=0;failures=[];other=Counter();ordinary=[]
    for r in rr:
        o=cases[r['case']];m=o.maze;meta=data['metadata'][r['case']]
        if r['reachable'] and r['status']=='emitted':
            d=o.to_goal[m.start];pred=sum(1<<p for p,ds in enumerate(o.to_goal) if 0<=ds<d)|(1<<m.start)
            actual=int.from_bytes(bytes.fromhex(r['mask']),'little');checked+=1
            ok=actual==pred and r['steps']==2*d+1;matched+=ok
            if not ok:failures.append(dict(case=r['case'],distance=d,steps=r['steps'],mask_matches=actual==pred))
        else:other[r['status']]+=1
        if meta['family'] in ('ordinary_perfect','ordinary_random') and r['optimal']:
            ordinary.append(dict(case=r['case'],family=meta['family'],size=meta['size'],base=meta['base'],pose=meta['pose'],edges=len(o.path)-1))
    result['confirmation' if final else 'development']=dict(checked_emitted_reachable=checked,matched=matched,mismatches=failures,other_statuses=dict(other),ordinary_successes=ordinary)
writej(OUT/'candidate_mechanism.json',dict(label='Post-hoc source-derived prediction checked on already saved rasters; zero new inference',identity=identity,
    equations=['C1(next)=positive-neighbor minimum of C6','C6(next)=C1 OR C6','C7(next)=C1 OR C7',
               'C3(next)=source flag (COPY plus MUX)','C2(next)=C7 XOR C3'],
    mutations=['swap output-block input ports3 and7','copy existing XOR node1 to the final output position'],
    prediction='At native halt2d+1, emit goal-distance ball radius d-1 plus source, for reachable distance d>=1.',
    interpretation='A delayed exploration ball with explicit source inclusion, not a parent-chain backtrace. This independently reaches the narrow prefix1 repertoire already present in the other M1 lineage.',
    limitations=['No second-edit-only counterfactual was run; two sampled mutations do not prove that two are necessary.',
                 'Source-derived prediction and saved native-output agreement do not constitute a new general-solver claim.'],panels=result))
print(json.dumps(result,indent=2))
