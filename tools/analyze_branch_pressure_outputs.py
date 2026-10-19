"""Post-registration saved-output diagnosis; no inference, ranking changes or new cases."""
import json,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.routing_transfer import lines
from maze_evolution.foundation_study import read_compressed
from maze_evolution.branch_pressure_data import OUT
from maze_evolution.branch_pressure_fitness import measurements


def summarize(rows,meta):
    groups=defaultdict(list);out=dict(normal_pairs=0,normal_goal_switch=0,normal_switch_away_from_goals=0,normal_eligible_pairs=0,normal_interior_switch=0,positive_signed_contrast=0,negative_signed_contrast=0,zero_signed_contrast=0,strict_both=0,missing_correct_raster_overlap=0)
    for row in rows:
        m=meta[row['case']]
        if m['family']=='paired':groups[m['base'],m['pose']].append(row)
    for rs in groups.values():
        a,b=sorted(rs,key=lambda r:meta[r['case']]['side'])
        if a['status']!='emitted' or b['status']!='emitted':continue
        out['normal_pairs']+=1;x,y=[int.from_bytes(bytes.fromhex(r['mask']),'little') for r in (a,b)];pa,pb=[set(meta[r['case']]['path']) for r in (a,b)];goals={meta[r['case']]['path'][-1] for r in (a,b)}
        away=((1<<81)-1)^sum(1<<g for g in goals);out['normal_goal_switch']+=x!=y;out['normal_switch_away_from_goals']+=bool((x^y)&away)
        aa=(pa-pb)-goals;bb=(pb-pa)-goals
        if not aa or not bb:continue
        out['normal_eligible_pairs']+=1;out['normal_interior_switch']+=any(((x^y)>>p)&1 for p in aa|bb)
        da=sum(((x>>p)&1)-((y>>p)&1) for p in aa)/len(aa);db=sum(((y>>p)&1)-((x>>p)&1) for p in bb)/len(bb)
        out['positive_signed_contrast']+=da+db>0;out['negative_signed_contrast']+=da+db<0;out['zero_signed_contrast']+=da+db==0;out['strict_both']+=da>0 and db>0
        out['missing_correct_raster_overlap']+=not any((x>>p)&1 for p in pa) or not any((y>>p)&1 for p in pb)
    return out


def main():
    meta=read_compressed(OUT/'calibration/metadata.json.gz');models=read_compressed(OUT/'models.json.gz');pools=read_compressed(OUT/'pools.json.gz');aliases=read_compressed(OUT/'aliases.json.gz');summaries={};masks={};current=None;rows=[]
    def save(key,rs):
        summaries[key]=summarize(rs,meta);masks[key]=[(r['mask'],r['status'],(r['steps'],r['active'],r['reads'],r['dispatches'],tuple(r['range_reads']),r['exposure_checks'])) for r in rs]
    for rec in lines(OUT/'calibration/responses.jsonl.gz'):
        if current is not None and current!=rec['model']:save(current,rows);rows=[]
        current=rec['model'];rows.append(rec['row'])
    save(current,rows);cohorts={}
    for key,aa in aliases.items():
        pool=pools[key.split('/')[0]];totals={f:sum(summaries[aa[i['id']]][f] for i in pool['items']) for f in next(iter(summaries.values()))}
        anymodel={f:sum(summaries[aa[i['id']]][f]>0 for i in pool['items']) for f in next(iter(summaries.values()))}
        differences=[]
        for i in pool['items'][96:]:
            child,parent=aa[i['id']],aa[i['parent']];different=sum(a[:2]!=b[:2] for a,b in zip(masks[child],masks[parent]));counterchanges=sum(a[2]!=b[2] for a,b in zip(masks[child],masks[parent]));differentmask=sum(a[0]!=b[0] for a,b in zip(masks[child],masks[parent]));genotype=models[child]['genome']['genes']!=models[parent]['genome']['genes']
            differences.append(dict(child=i['id'],parent=i['parent'],genotype_changed=genotype,mask_or_status_changes=different,mask_changes=differentmask,counter_changes=counterchanges))
        cohorts[key]=dict(logical_candidates=len(pool['items']),pair_counts=totals,candidates_with_any=anymodel,
            mutant_genotype_changes=sum(d['genotype_changed'] for d in differences),mutants_with_counter_changes=sum(d['counter_changes']>0 for d in differences),mutants_with_mask_changes=sum(d['mask_changes']>0 for d in differences),mutants_with_response_changes=sum(d['mask_or_status_changes']>0 for d in differences),mutation_comparisons=differences)
    finalmeta=read_compressed(OUT/'confirmation/metadata.json.gz');finalrows=defaultdict(list)
    for rec in lines(OUT/'confirmation/responses.jsonl.gz'):finalrows[rec['model']].append(rec['row'])
    fa=read_compressed(OUT/'confirmation/aliases.json.gz');comparisons={}
    for key,aa in fa.items():
        child=aa['selected_choice'];parent=next((v for v in aa.values() if v['item']['id']==child['item']['parent']),None)
        if parent:
            cr,pr=finalrows[child['model']],finalrows[parent['model']];cm,pm=measurements(cr,finalmeta),measurements(pr,finalmeta)
            good=lambda m:{(x['base'],x['pose']) for x in m['details'] if x['complete']}
            cg,pg=good(cm),good(pm);comparisons[key]=dict(child=child['item']['id'],parent=parent['item']['id'],child_pairs=cm['pairs'],parent_pairs=pm['pairs'],gained_pairs=len(cg-pg),lost_pairs=len(pg-cg),retained_pairs=len(cg&pg),child_corridors=cm['corridors'],parent_corridors=pm['corridors'],mask_changes=sum(a['mask']!=b['mask'] for a,b in zip(cr,pr)))
    result=dict(post_registration=True,additional_candidate_calls=0,calibration=cohorts,final_parent_comparisons=comparisons)
    (OUT/'output_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(calibration={k:{f:v for f,v in d.items() if f!='mutation_comparisons'} for k,d in cohorts.items()},final_parent_comparisons=comparisons),indent=2))
if __name__=='__main__':main()
