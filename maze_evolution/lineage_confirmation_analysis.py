"""V12L fixed-model summaries; templates, not poses, are independent units."""
from collections import defaultdict,Counter
import json
from .foundation_calibration import write_json
from .foundation_study import read_compressed
from .routing_transfer import lines
from .lineage_confirmation_data import *


def score(rows,meta):
    pairs=defaultdict(list);groups=defaultdict(list)
    for r in rows:
        m=meta[r['case']]
        if m['family'] in BRANCHES:pairs[(m['template'],m['family'],m['position'],m['pose'])].append(r)
    complete={k for k,rs in pairs.items() if len(rs)==2 and all(r['optimal'] for r in rs)}
    for k in pairs:groups[k[:2]].append(k in complete)
    strata={}
    for field in ('family','goal_shape','prefix','source_shape','long','position'):
        for value in sorted({str(meta[r['case']][field]) for r in rows}):
            ids={k for k,rs in pairs.items() if str(meta[rs[0]['case']][field])==value}
            strata[f'{field}/{value}']=dict(pairs=len(ids&complete),opportunities=len(ids))
    return dict(inputs=len(rows),valid=sum(r['valid'] for r in rows),optimal=sum(r['optimal'] for r in rows),
        pairs=len(complete),pair_opportunities=len(pairs),corridors=sum(r['optimal'] for r in rows if meta[r['case']]['family'].startswith('corridor')),
        corridor_inputs=sum(meta[r['case']]['family'].startswith('corridor') for r in rows),no_path=sum(r['no_path'] for r in rows),
        no_path_inputs=sum(not r['reachable'] for r in rows),false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rows),
        all16_groups=sum(len(v)==16 and all(v) for v in groups.values()),
        any_templates=len({k[0] for k in complete}),all16_templates=len({k[0] for k,v in groups.items() if len(v)==16 and all(v)}),
        strata=strata,pair_keys=[list(k) for k in sorted(complete)],
        all16_keys=[list(k) for k,v in groups.items() if len(v)==16 and all(v)],
        max_paired_edges=max((len(meta[r['case']]['path'])-1 for k in complete for r in pairs[k]),default=0),
        work=sum(r['reads']+r['dispatches'] for r in rows))


def analyze():
    cases,contexts,meta=load(OUT/'confirmation');models=read_compressed(OUT/'panel.json.gz');by=defaultdict(list)
    for rec in lines(OUT/'confirmation/responses.jsonl.gz'):by[(rec['model'],rec['mode'])].append(rec['row'])
    scores={f'{n}/{mode}':score(rs,meta) for (n,mode),rs in by.items()};comparisons={};templates={c['template']:c for c in contexts}
    for (name,mode),rows in by.items():
        if mode=='normal':continue
        normal=[r for r in by[(name,'normal')] if mechanism_case(meta[r['case']])]
        a,b=score(normal,meta),score(rows,meta);pa,pb={tuple(k) for k in a['pair_keys']},{tuple(k) for k in b['pair_keys']}
        ra,rb={r['case']:r for r in normal},{r['case']:r for r in rows}
        lostcorr=[cid for cid,r in ra.items() if meta[cid]['family'].startswith('corridor') and r['optimal'] and not rb[cid]['optimal']]
        gained=pb-pa;lost=pa-pb;tg=Counter(k[0] for k in gained);tl=Counter(k[0] for k in lost)
        gain_templates={t for t,v in tg.items() if v>tl[t]}
        rescue=(len(gain_templates)>=4 and {templates[t]['goal_shape'] for t in gain_templates}==set(SHAPES) and not lost and not lostcorr)
        comparisons[f'{name}/{mode}']=dict(normal=a,intervened=b,gained_pairs=len(gained),lost_pairs=len(lost),lost_corridors=len(lostcorr),
            gained_templates=len(gain_templates),gain_shapes=sorted({templates[t]['goal_shape'] for t in gain_templates}),
            changed_masks=sum(ra[cid]['mask']!=rb[cid]['mask'] for cid in ra),
            changed_work=sum((ra[cid]['reads'],ra[cid]['dispatches'])!=(rb[cid]['reads'],rb[cid]['dispatches']) for cid in ra),
            normal_far_pairs=sum(templates[k[0]]['prefix']>=4 for k in pa),retained_far_pairs=sum(templates[k[0]]['prefix']>=4 for k in pa&pb),
            rescue_screen=bool(rescue))
    lineage={}
    for rep in (1,2):
        target=scores[f'k{rep}_target/normal'];entry=scores[f'k{rep}_entry/normal'];parent=scores[f'k{rep}_parent/normal'];frozen=scores[f'k{rep}_frozen/normal']
        full={t for t,f in target['all16_keys'] if f=='fork'};shapes={templates[t]['goal_shape'] for t in full}
        screen=len(full)>=4 and shapes==set(SHAPES) and target['pairs']>entry['pairs']
        lineage[str(rep)]=dict(target_pairs=target['pairs'],parent_pairs=parent['pairs'],entry_pairs=entry['pairs'],frozen_pairs=frozen['pairs'],
            all16_fork_templates=len(full),all16_fork_shapes=sorted(shapes),normal_confirmation_screen=bool(screen),
            target_parent_identical_masks=sum(a['mask']==b['mask'] for a,b in zip(by[(f'k{rep}_target','normal')],by[(f'k{rep}_parent','normal')])),
            target_parent_identical_reactions=sum(all(a[k]==b[k] for k in ('mask','status','steps','reads','dispatches','active','range_reads')) for a,b in zip(by[(f'k{rep}_target','normal')],by[(f'k{rep}_parent','normal')])))
    result=dict(scores=scores,interventions=comparisons,lineages=lineage,independent_templates=36,
        next_calibration_screen=bool(lineage['2']['normal_confirmation_screen'] and any(comparisons[f'{n}/nonlocal_off']['rescue_screen'] for n in ('branch_narrow','branch_broad'))))
    write_json(OUT/'analysis.json',result)
    print(json.dumps(dict(lineages=lineage,next_calibration_screen=result['next_calibration_screen'],normal={n:{k:scores[f'{n}/normal'][k] for k in ('pairs','all16_templates','corridors','no_path')} for n in models}),indent=2),flush=True)
