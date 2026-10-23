"""Saved-only check of every novel fresh ordinary individual response; no reselection."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import OUT,check,readz,writej,load
from maze_evolution.deep_campaign_data import cases_from_manifest
from tools.review_m31_witness import strict_saved

def main():
    check();assert not (OUT/'fresh_pose_review.json').exists();note=json.loads((OUT/'saved_diagnostics.json').read_text());data,rows,_,_,_=load('final');meta={c:data['metadata'][c] for c in data['queries']['all']};mazes={m['case_id']:m for m in data['mazes']};details=[]
    for nominee in note['nominees']:
        lookup={r['case']:r for r in rows[nominee['id']]}
        for cid in nominee['new_individual_ordinary_cases']:
            o=cases_from_manifest([mazes[cid]])[cid];edges=strict_saved(lookup[cid],o);m=meta[cid]
            peers=[c for c,mm in meta.items() if mm.get('base')==m['base'] and c!=cid];assert len(peers)==1 and not lookup[peers[0]]['optimal']
            parent=next(r for r in rows[nominee['parent']] if r['case']==cid);assert not parent['optimal']
            details.append(dict(id=nominee['id'],case=cid,family=m['family'],size=m['size'],pose=m['pose'],oracle_edges=edges,
                counterpart=peers[0],counterpart_failure=lookup[peers[0]]['failure'],counterpart_status=lookup[peers[0]]['status'],
                parent=nominee['parent'],parent_failure=parent['failure'],parent_only_gate=nominee['actual_parent_only_gate'],source_comparators=nominee['comparators']))
    assert len(details)==1 and details[0]['oracle_edges']==11
    writej(OUT/'fresh_pose_review.json',dict(status='PASS',saved_only=True,new_inference=0,new_cases=0,independent_scalar_saved_rasters=len(details),details=details,
        limitation='One pre-frozen nominee solves one fresh11-edge perfect-maze pose beyond all208 declared historical aliases; the other pose fails. This is independently observed individual capability, not a complete two-pose base, primary endpoint success, broad transfer or significance.'))

if __name__=='__main__':main()
