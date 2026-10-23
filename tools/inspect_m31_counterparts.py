"""Quantify saved failed counterparts; no repaired output or new inference."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import OUT,check,readz,writej,panel_stream,entries
from maze_evolution.deep_campaign_data import cases_from_manifest
from tools.review_m31_witness import bits

def main():
    check();assert not (OUT/'witness_counterpart_note.json').exists();review=json.loads((OUT/'witness_review.json').read_text());identity=review['id']
    con,data,_,_=panel_stream('development');rows=None
    for e,r in entries(con):
        if identity in e['aliases']:rows={x['case']:x for x in r['rows']};break
    con.close();assert rows;ids={x['failed_counterpart'] for x in review['matched_pairs']};mazes={m['case_id']:m for m in data['mazes']};cases=cases_from_manifest([mazes[c] for c in sorted(ids)])
    details=[];hist=Counter()
    for cid,o in cases.items():
        row=rows[cid];selected=bits(row,len(o.maze.cells));target=set(o.path);assert target and not row['optimal']
        extra=selected-target;missing=target-selected;hist[(len(extra),len(missing))]+=1;m=data['metadata'][cid];obs=m['observers'][1:3]
        details.append(dict(case=cid,oracle_edges=len(o.path)-1,status=row['status'],failure=row['failure'],extra_pixels=sorted(extra),missing_pixels=sorted(missing),
            oracle_pixels=len(target),selected_pixels=len(selected),correct_selected_pixels=len(selected&target),
            observer_arm_pixels_selected=[p in selected for p in obs],observer_arm_pixels_on_correct_path=[p in target for p in obs]))
    writej(OUT/'witness_counterpart_note.json',dict(saved_only_posthoc=True,new_inference=0,new_cases=0,id=identity,
        counterpart_presentations=len(details),distinct_full_stimuli=len({cases[c].maze.digest for c in cases}),
        extra_missing_pixel_histogram={f'extra{a}/missing{b}':n for (a,b),n in sorted(hist.items())},details=details,
        limitation='Oracle-relative saved-raster error only. No pixels were repaired or fed to an organism. Three raster errors are not three genetic edits, a validated repair mechanism, or a general-solver result. These are simple used rectilinear fixtures and the variant was not independently confirmed.'))

if __name__=='__main__':main()
