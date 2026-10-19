"""Post-registration saved-data summaries for V12R; no candidate inference."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_accessibility_study import (
    OUT,FIXTURES,ARMS,read_compressed,eligible,identities_for_models,
)
from maze_evolution.mutation_accessibility_metrics import compare
from maze_evolution.foundation_calibration import write_json

def compact(m):
    fields=('pairs','positive','zero','mean_score','target_pairs','corridors',
            'no_path','false_no_path','optimal','valid','active','reads','dispatches','work')
    o={k:m[k] for k in fields}
    groups={}
    for d in m['details']:
        key=f'{"stress" if d["stress"] else "core"}/{d["graph"]}/prefix{d["prefix"]}'
        g=groups.setdefault(key,dict(pairs=0,opportunities=0))
        g['pairs']+=int(d['complete']);g['opportunities']+=1
    o['strata']=groups
    return o

def main():
    p=read_compressed(OUT/'pool.json.gz');a=read_compressed(OUT/'analysis.json.gz')
    dm=read_compressed(OUT/'discovery/metrics.json.gz')
    fm=read_compressed(OUT/'confirmation/metrics.json.gz')
    n=json.loads((FIXTURES/'profile.json').read_text())['walks_per_root_block']
    supply={};byroot={};selections={}
    for arm in ARMS:
        cs=[]
        for label,root in p['roots'].items():
            subset=[]
            for rep in range(3):
                for i in p['groups'][f'{label}/{rep}'][arm][:n]:
                    m=dm[p['aliases'][i]];r=dm[p['aliases'][root['id']]]
                    c=compare(m,r)
                    c.update(positive=m['positive'],score_delta=m['mean_score']-r['mean_score'])
                    subset.append(c)
            def agg(rows):
                return dict(candidates=len(rows),**{k:sum(bool(c[k]) for c in rows) for k in ('changed','counters_changed','retained','correct','partial')},
                    score_increased=sum(c['score_delta']>1e-12 for c in rows),
                    score_decreased=sum(c['score_delta']<-1e-12 for c in rows),
                    score_increased_retained=sum(c['score_delta']>1e-12 and c['retained'] for c in rows),
                    max_positive=max(c['positive'] for c in rows),
                    max_score_delta=max(c['score_delta'] for c in rows))
            byroot.setdefault(label,{})[arm]=agg(subset);cs+=subset
        supply[arm]=agg(cs)
    for key,g in a['results'].items():
        selections[key]={arm:dict(id=x['id'],final=compact(x['final']),validation=compact(x['validation']),
            final_comparison=x['final_comparison'],validation_comparison=x['validation_comparison'],
            gates=x.get('gates')) for arm,x in g.items()}
    physical={pid:compact(m) for pid,m in fm.items()}
    stage_counts={}
    choices=read_compressed(OUT/'discovery_choices.json.gz')
    ids={r['id'] for r in p['roots'].values()}|{p['control']}
    for g in choices.values():
        for arm in ARMS:ids.update(g[arm]['nominees'])
    final=read_compressed(OUT/'final_panel.json.gz')
    for stage,identities,inputs in [('discovery',eligible(p,n),768),('validation',ids,768),('confirmation',final['ids'],5184)]:
        stage_counts[stage]=dict(identities=len(identities),physical_models=len(identities_for_models(p,identities)),
            logical_calls=len(identities)*inputs,physical_calls=len(identities_for_models(p,identities))*inputs)
    out=dict(post_registration=True,candidate_calls=0,roots={label:dict(id=r['id'],final=compact(fm[p['aliases'][r['id']]])) for label,r in p['roots'].items()},
        supply=supply,supply_by_root=byroot,selections=selections,final_physical=physical,
        stage_counts=stage_counts,passing_blocks=a['passing_blocks'],readiness=a['readiness'])
    write_json(OUT/'saved_data_summary.json',out)
    print(json.dumps({k:out[k] for k in ('supply','stage_counts','passing_blocks','readiness')},indent=2))
if __name__=='__main__':main()
