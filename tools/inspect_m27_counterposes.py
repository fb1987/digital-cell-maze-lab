"""Posthoc orientation/failure description from audited M27 saved rows only."""
import json,sys,time
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.transfer_retention import OUT,check,readz,writej,load


def main():
    check();assert not (OUT/'counterpose_diagnostics.json').exists()
    assert json.loads((OUT/'audit.json').read_text())['status']=='PASS';start=time.monotonic()
    d=json.loads((OUT/'saved_diagnostics.json').read_text());pool=readz(OUT/'pool.json.gz')
    panels,rows,models,usage,chain=load();data=panels['fresh'];meta=data['metadata'];wanted=set(data['queries']['all'])
    bybase=defaultdict(list)
    for cid in wanted:
        m=meta[cid]
        if m['family'] in ('ordinary_perfect','ordinary_random'):bybase[m['base']].append(cid)
    conditions={c['id']:c for c in pool['conditions']};records=[]
    for i,c in d['conditions'].items():
        lookup={r['case']:r for r in rows['fresh'][i]}
        for cid in c['new_individual8_keys']:
            m=meta[cid];other,=[q for q in bybase[m['base']] if q!=cid]
            assert lookup[cid]['optimal'] and not lookup[other]['optimal']
            records.append(dict(identity=i,cohort=conditions[i]['cohort'],case=cid,base=m['base'],family=m['family'],size=m['size'],
                edges=len(m['path'])-1,panel_group=m['panel_group'],correct_pose=m['pose'],counterpose=meta[other]['pose'],
                failed_case=other,failure=lookup[other]['failure'],status=lookup[other]['status'],partial=lookup[other]['partial']))
    primary=[r for r in records if r['cohort']=='changed_mutant']
    def summarize(rs):return dict(identities=len({r['identity'] for r in rs}),identity_input_presentations=len(rs),
        unique_successful_inputs=len({r['case'] for r in rs}),unique_bases=len({r['base'] for r in rs}),
        lengths=dict(Counter(str(r['edges']) for r in rs)),families=dict(Counter(r['family'] for r in rs)),
        successful_poses=dict(Counter(str(r['correct_pose']) for r in rs)),
        counterpose_failures=dict(Counter(r['failure'] for r in rs)),counterpose_statuses=dict(Counter(r['status'] for r in rs)))
    writej(OUT/'counterpose_diagnostics.json',dict(scope='Posthoc description of fresh-case single-pose novelty; not the primary endpoint, no causal explanation from terminal rasters alone.',
        primary_changed_mutants=summarize(primary),all_rare_variants=summarize(records),records=records,
        no_new_inference=True,no_new_cases=True,wall_seconds=time.monotonic()-start))
    print(json.dumps(summarize(primary),indent=2))


if __name__=='__main__':main()
