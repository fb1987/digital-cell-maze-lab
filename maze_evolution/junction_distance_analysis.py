"""Prespecified matched contrasts; poses, variants and relatives are not replicates."""
from collections import Counter, defaultdict
import json
from .foundation_calibration import write_json
from .foundation_study import read_compressed
from .routing_transfer import lines
from .junction_distance_data import OUT, PREFIXES, BRANCHES


def pair_key(md):
    return (md['base'],md['shape'],md['prefix'],md['family'],md['pose'])


def pairs(rows,meta):
    grouped=defaultdict(list)
    for r in rows:
        md=meta[r['case']]
        if md['family'] in BRANCHES:grouped[pair_key(md)].append(r)
    return {k:len(v)==2 and all(r['optimal'] for r in v) for k,v in grouped.items()}


def transfer_gate(pair_results,rows,meta):
    bases=sorted({m['base'] for m in meta.values()})
    contexts=[b for b in bases if all(pair_results.get((b,shape,p,f,s),False)
        for shape in ('straight','bent') for p in (6,8) for f in ('fork','cycle_4') for s in range(8))]
    corridor=[r for r in rows if meta[r['case']]['family'].startswith('corridor') and meta[r['case']]['prefix'] in (6,8)]
    retention=sum(r['optimal'] for r in corridor)/len(corridor) if corridor else 0.
    false=sum(r['reachable'] and r['status']=='no_path' for r in rows)
    return dict(contexts=contexts,corridor_rate=retention,false_no_path=false,
        passed=len(contexts)>=3 and retention>=.95 and false==0)


def analyze():
    assert json.loads((OUT/'verification.json').read_text())['passed']
    models=read_compressed(OUT/'panel.json.gz');meta=read_compressed(OUT/'confirmation/metadata.json.gz')
    rows=defaultdict(list)
    for e in lines(OUT/'normal.jsonl.gz'):rows[e['model']].append(e['row'])
    result={};allpairs={};normal={n:{r['case']:r for r in rr} for n,rr in rows.items()}
    for name,rr in rows.items():
        ps=pairs(rr,meta);allpairs[name]=ps;table={};contrasts={}
        for shape in ('straight','bent'):
            for family in BRANCHES:
                for p in PREFIXES:
                    keys=[k for k in ps if k[1:4]==(shape,p,family)]
                    perbase={b:sum(ps[k] for k in keys if k[0]==b) for b in sorted({k[0] for k in keys})}
                    table[f'{shape}/{family}/{p}']=dict(pairs=sum(ps[k] for k in keys),opportunities=len(keys),
                        context_counts=perbase,all_pose_contexts=sum(v==8 for v in perbase.values()))
                near=table[f'{shape}/{family}/1']
                for p in (2,4,6,8):
                    far=table[f'{shape}/{family}/{p}']
                    changes={b:far['context_counts'][b]-v for b,v in near['context_counts'].items()}
                    contrasts[f'{shape}/{family}/1_to_{p}']=dict(context_pair_changes=changes,
                        delta_pairs=far['pairs']-near['pairs'],near_pairs=near['pairs'],far_pairs=far['pairs'],
                        decreased=sum(v<0 for v in changes.values()),increased=sum(v>0 for v in changes.values()),
                        distance_screen=near['all_pose_contexts']>=6 and (near['pairs']-far['pairs'])/near['opportunities']>=.5)
        seconds={}
        for shape in ('straight','bent'):
            for p in PREFIXES:
                for kind in ('two','cycle'):
                    a=table[f'{shape}/{kind}_2/{p}'];b=table[f'{shape}/{kind}_4/{p}']
                    seconds[f'{shape}/{kind}/{p}']=dict(delta_pairs=b['pairs']-a['pairs'],
                        context_pair_changes={base:b['context_counts'][base]-a['context_counts'][base] for base in a['context_counts']})
        result[name]=dict(genes=models[name]['genes'],identity=models[name]['item']['id'],lineage_group=models[name]['lineage_group'],
            pairs=sum(ps.values()),pair_opportunities=len(ps),table=table,prefix_contrasts=contrasts,second_junction_contrasts=seconds,
            legal=sum(r['valid'] for r in rr),optimal=sum(r['optimal'] for r in rr),
            legal_nonshortest=sum(r['valid'] and not r['optimal'] for r in rr),no_path=sum(r['no_path'] for r in rr),
            corridor=sum(r['optimal'] for r in rr if meta[r['case']]['family'].startswith('corridor')),
            failures=dict(Counter(r['failure'] for r in rr if not r['optimal'] and not r['no_path'])),
            max_array_bytes=max(r['array_bytes'] for r in rr),work=sum(r['reads']+r['dispatches'] for r in rr),
            gate=transfer_gate(ps,rr,meta))
    intervention=defaultdict(list)
    for e in lines(OUT/'interventions.jsonl.gz'):intervention[e['model'],e['mode']].append(e['row'])
    effects={}
    for (name,mode),rr in intervention.items():
        ps=pairs(rr,meta);ns=allpairs[name];success_keys=[k for k in ps if ns[k]]
        bygroup={}
        for shape in ('straight','bent'):
            for f in BRANCHES:
                for p in PREFIXES:
                    keys=[k for k in ps if k[1:4]==(shape,p,f)];base_success=[k for k in keys if ns[k]]
                    bygroup[f'{shape}/{f}/{p}']=dict(normal_pairs=len(base_success),retained=sum(ps[k] for k in base_success),
                        new_pairs=sum(ps[k] and not ns[k] for k in keys))
        effects[f'{name}/{mode}']=dict(normal_pairs=len(success_keys),retained=sum(ps[k] for k in success_keys),
            new_pairs=sum(ps[k] and not ns[k] for k in ps),total_pairs=sum(ps.values()),opportunities=len(ps),groups=bygroup,
            changed_masks=sum(r['mask']!=normal[name][r['case']]['mask'] for r in rr),
            changed_steps=sum(r['steps']!=normal[name][r['case']]['steps'] for r in rr),
            false_no_path=sum(r['reachable'] and r['status']=='no_path' for r in rr))
    traces=defaultdict(list)
    for e in read_compressed(OUT/'trace_comparisons.json.gz'):traces[e['model'],e['mode']].append(e)
    trace_summary={f'{name}/{mode}':dict(pairs=len(rr),source_responses=sum(r['first_source_difference'] is not None for r in rr),
        junction_responses=sum(r['first_junction_difference'] is not None for r in rr),
        output_away_responses=sum(r['first_output_away_difference'] is not None for r in rr),
        identical=sum(r['identical_full_trajectory'] for r in rr),
        pairs_with_shortest_frame=sum(bool(r['paired_shortest_ticks']) for r in rr),
        shortest_frames=sum(sum(len(x) for x in r['optimal_ticks']) for r in rr)) for (name,mode),rr in traces.items()}
    groups=sorted({r['lineage_group'] for n,r in result.items() if n!='intact' and r['gate']['passed']})
    write_json(OUT/'analysis.json',dict(models=result,interventions=effects,traces=trace_summary,
        passing_lineage_groups=groups,broader_transfer_screen=len(groups)>=2,
        interpretation='I-informed fixed panel; 12 context units, two mechanism contexts, one trace context; no evolutionary or speed inference'))
    print(json.dumps(dict(pairs={n:r['pairs'] for n,r in result.items()},passing_lineage_groups=groups)),flush=True)
