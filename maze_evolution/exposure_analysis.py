"""V12M prespecified activation/readiness screens and transparent fixed controls."""
import json
from collections import defaultdict
from .foundation_calibration import write_json
from .foundation_study import read_compressed
from .routing_transfer import lines
from .exposure_data import *
from .exposure_selection import stats
from .exposure_genome import Individual
from .exposure_runtime import ARMS


def comparison(a,b,meta):
    """A=treatment, B=reference on the exact same inputs."""
    aa,bb=stats(a,meta),stats(b,meta);pa,pb={tuple(k) for k in aa['pair_keys']},{tuple(k) for k in bb['pair_keys']}
    ar,br={r['case']:r for r in a},{r['case']:r for r in b};assert ar.keys()==br.keys()
    gained,lost=pa-pb,pb-pa;base_meta={m['base']:m for m in meta.values()}
    gain_templates={base_meta[k[0]]['template'] for k in gained}
    return dict(treatment=aa,reference=bb,gained_pairs=len(gained),lost_pairs=len(lost),retained_pairs=len(pa&pb),
        gained_templates=len(gain_templates),gain_shapes=sorted({base_meta[k[0]]['goal_shape'] for k in gained}),
        lost_corridors=sum(r['optimal'] and not ar[cid]['optimal'] for cid,r in br.items() if meta[cid]['family'].startswith('corridor')),
        changed_masks=sum(ar[cid]['mask']!=br[cid]['mask'] for cid in ar),
        normal_far_pairs=sum(base_meta[k[0]]['prefix']>=4 for k in pb),retained_far_pairs=sum(base_meta[k[0]]['prefix']>=4 for k in pa&pb))


def two_partial(rows,meta):
    rs=[r for r in rows if meta[r['case']]['family']=='paired' and meta[r['case']]['kind']!='adjacent']
    return sum(r['partial'] for r in rs)/len(rs)


def analyze():
    pools=read_compressed(OUT/'pools.json.gz');aliases=read_compressed(OUT/'aliases.json.gz');choices=read_compressed(OUT/'calibration_choices.json.gz')
    selections=read_compressed(OUT/'selections.json.gz');fa=read_compressed(OUT/'confirmation/aliases.json.gz');by={};metadata={}
    for scope in ('calibration','validation','confirmation'):
        by[scope]=defaultdict(dict);metadata[scope]={o:load(OUT/scope/o)[2] for o in ('carry','fresh')}
        for rec in lines(OUT/scope/'responses.jsonl.gz'):by[scope][rec['origin']].setdefault(rec['model'],[]).append(rec['row'])
    activation={};fresh={};final={};retention={}
    for key,p in pools.items():
        origin=p['origin'];items={i['id']:Individual.load(i) for i in p['items']};c=choices[key]
        aa,nn=c['active']['True'],c['neutral']['True']
        activation[key]=dict(parent_identity_changes=sum(a!=b for a,b in zip(aa['parents'],nn['parents'])),
            parent_program_changes=sum(items[a].genome.program.digest!=items[b].genome.program.digest for a,b in zip(aa['parents'],nn['parents'])),
            elite_changed=set(aa['elite'])!=set(nn['elite']),nominees_changed=set(aa['nominees'])!=set(nn['nominees']),
            behavioral_variant_count=sum(any(a['mask']!=b['mask'] for a,b in zip(by['calibration'][origin][aliases[key]['active'][i]],by['calibration'][origin][aliases[key]['neutral'][i]])) for i in items))
        if origin=='fresh':
            fresh[key]={};meta=metadata['calibration'][origin]
            for arm in ARMS:
                shaped,unshaped=c[arm]['True'],c[arm]['False'];partial={i:two_partial(by['calibration'][origin][aliases[key][arm][i]],meta) for i in items}
                uniform=sum(partial.values())/len(partial);selected=sum(partial[i] for i in shaped['parents'])/64
                changes=sum(a!=b for a,b in zip(shaped['parents'],unshaped['parents']))
                better=sum(v>.10 for v in partial.values());elite=set(shaped['elite'])!=set(unshaped['elite'])
                ok=better>=8 and max(partial.values())>=.15 and changes>=16 and elite and selected>=uniform+.02
                fresh[key][arm]=dict(above_endpoint_only=better,best_two_edge_partial=max(partial.values()),uniform_partial=uniform,parent_partial=selected,
                    shaping_parent_changes=changes,shaping_elite_changed=elite,gradient_screen=bool(ok),complete_calibration_pairs=sum(stats(by['calibration'][origin][aliases[key][arm][i]],meta)['pairs'] for i in items))
        rows=by['confirmation'][origin];meta=metadata['confirmation'][origin]
        final[key]={label:dict(item=entry['item'],arm=entry['arm'],model=entry['model'],stats=stats(rows[entry['model']],meta)) for label,entry in fa[key].items()}
        active=rows[fa[key]['selected_active']['model']]
        retention[key]={label:comparison(active,rows[fa[key][label]['model']],meta) for label in ('selected_neutral','selected_zero','selected_local','active_as_neutral','active_as_zero','active_as_local','base_neutral','base_zero','base_local')}
        if origin=='fresh':
            for arm in ARMS:
                selected=rows[fa[key]['selected_'+arm]['model']];base=rows[fa[key]['base_neutral']['model']]
                fresh[key][arm]['final_two_edge_partial']=two_partial(selected,meta)
                fresh[key][arm]['base_neutral_two_edge_partial']=two_partial(base,meta)
                fresh[key][arm]['final_partial_gain_vs_base_neutral']=two_partial(selected,meta)-two_partial(base,meta)
                fresh[key][arm]['final_two_edge_pairs']=stats([r for r in selected if meta[r['case']]['kind']!='adjacent'],meta)['pairs']
    broad=activation['carry/branch_broad'];rescue=retention['carry/branch_broad']['active_as_neutral']
    protected=('carry/k2_target','carry/local_long','carry/resampled')
    carry_screen=(broad['parent_identity_changes']>=16 and broad['elite_changed'] and broad['nominees_changed'] and broad['behavioral_variant_count']>0
        and rescue['gained_pairs']>=4 and rescue['gained_templates']>=2 and len(rescue['gain_shapes'])>=2 and rescue['lost_pairs']==0 and rescue['lost_corridors']==0
        and all(retention[k]['base_neutral']['lost_pairs']==0 and retention[k]['base_neutral']['lost_corridors']==0 for k in protected))
    fresh_pass=[key for key,v in fresh.items() if v['neutral']['gradient_screen'] and (v['neutral']['final_two_edge_pairs']>0 or v['neutral']['final_partial_gain_vs_base_neutral']>=.02)]
    packet=dict(activation=activation,fresh=fresh,final=final,retention=retention,carried_pilot_screen=bool(carry_screen),
        fresh_pilot_screen=len(fresh_pass)>=2,fresh_passing_replicates=fresh_pass,protected=list(protected),
        inference='Fixed neighborhoods and simulated selection only; no evolutionary trajectory or causal multirange discovery.')
    write_json(OUT/'analysis.json',packet)
    print(json.dumps(dict(carried_pilot_screen=bool(carry_screen),fresh_passing_replicates=fresh_pass,
        activation=activation,fresh=fresh,selected={k:{a:dict(mask=selections[k][a]['item']['genome']['exposure'],id=selections[k][a]['item']['id'],pairs=final[k]['selected_'+a]['stats']['pairs']) for a in ARMS} for k in pools}),indent=2),flush=True)
