"""Post-registration summaries from saved O data; zero new inference/selection."""
import json,sys,statistics
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.mutation_depth_data import OUT,TOPS,ARMS
from maze_evolution.foundation_study import read_compressed
from maze_evolution.mutation_depth_metrics import compare
from maze_evolution.routing_transfer import lines


def main():
    pool=read_compressed(OUT/'pools.json.gz');aliases=read_compressed(OUT/'aliases.json.gz');ms=read_compressed(OUT/'discovery/metrics.json.gz');walks=read_compressed(OUT/'walks.json.gz');costs={}
    for rec in lines(OUT/'discovery/responses.jsonl.gz'):
        r=rec['row'];c=costs.setdefault(rec['model'],dict(calls=0,work=0,emitted=0,max_array_bytes=0))
        c['calls']+=1;c['work']+=r['reads']+r['dispatches']+r['exposure_checks'];c['emitted']+=r['status']=='emitted';c['max_array_bytes']=max(c['max_array_bytes'],r['array_bytes'])
    cohorts={}
    for rep,arms in pool['groups'].items():
        for top in TOPS:
            aa=aliases[top];out={}
            for arm,ids in arms.items():
                lengths=[len(pool['entries'][i]['item']['genome']['genes']) for i in ids]
                comparisons={i:compare(ms[aa[i]],ms[aa[pool['entries'][i]['reference']]]) for i in ids}
                out[arm]=dict(gene_range=[min(lengths),statistics.median(lengths),max(lengths)],genetically_changed=sum(pool['entries'][i]['program_digest']!=pool['entries'][pool['entries'][i]['reference']]['program_digest'] for i in ids),
                    mask_changes=sum(c['mask_changed'] for c in comparisons.values()),counter_changes=sum(c['counter_changed'] for c in comparisons.values()),
                    useful=sum(c['useful'] for c in comparisons.values()),logical_calls=sum(costs[aa[i]]['calls'] for i in ids),logical_work=sum(costs[aa[i]]['work'] for i in ids),
                    emitted_calls=sum(costs[aa[i]]['emitted'] for i in ids),max_array_bytes=max(costs[aa[i]]['max_array_bytes'] for i in ids),
                    corridor_loss_candidates=sum(c['corridor_gain']<0 for c in comparisons.values()),pair_loss_candidates=sum(c['pair_gain']<0 for c in comparisons.values()))
            first={name:Counter() for name in ('mask','counter','response','useful','new_nonadj')}
            for w in walks:
                if str(w['rep'])!=rep:continue
                root=ms[aa[w['root']]];cs={int(d):compare(ms[aa[i]],root) for d,i in w['checkpoints'].items()}
                for name,field in [('mask','mask_changed'),('counter','counter_changed'),('response','response_changed'),('useful','useful'),('new_nonadj','new_nonadj_pairs')]:
                    first[name][str(next((d for d in (1,4,16) if cs[d][field]),'none'))]+=1
            cohorts[f'{rep}/{top}']=dict(arms=out,first_queried_depth={k:dict(v) for k,v in first.items()})
    analysis=read_compressed(OUT/'analysis.json.gz');lineages={}
    for key,r in analysis['results'].items():
        lineages[key]={}
        for arm,a in r['arms'].items():
            identity=a['selected'];e=pool['entries'][identity];m=a['metrics'];root=a['reference_metrics'];c=a['comparison']
            lineages[key][arm]=dict(id=identity,reference=e['reference'],parent=e['item']['parent'],genes=len(e['item']['genome']['genes']),same_program_as_reference=e['program_digest']==pool['entries'][e['reference']]['program_digest'],
                pairs=m['pairs'],nonadj=m['nonadj_pairs'],mean_score=m['mean_score'],mean_signed=m['mean_signed'],strict=m['strict_pairs'],corridors=m['corridors'],reference_pairs=root['pairs'],reference_corridors=root['corridors'],reference_score=root['mean_score'],comparison=c,
                checkpoints={i:{f:x[f] for f in ('pairs','nonadj_pairs','mean_score','strict_pairs','corridors')} for i,x in a['checkpoints'].items()})
    result=dict(post_registration=True,new_candidate_calls=0,discovery=cohorts,final_lineages=lineages)
    (OUT/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(discovery=cohorts,final={k:{a:{f:v[f] for f in ('id','pairs','nonadj','mean_score','strict','corridors','same_program_as_reference')} for a,v in r.items()} for k,r in lineages.items()}),indent=2))
if __name__=='__main__':main()
