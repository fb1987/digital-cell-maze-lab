"""Secondary fixed-bank accuracy/timing description; no new executions or choices."""
import sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.state_interference import OUT,check,readz,read_records,writej


def main():
    check();assert not (OUT/'target_timing_note.json').exists();sources=readz(OUT/'sources.json.gz');data=readz(OUT/'cases.json.gz');records=read_records()
    native={(s['model'],s['case']):r['row'] for s,r,h in records if s['phase']=='native'}
    groups=defaultdict(lambda:defaultdict(list))
    for s,r,h in records:
        if s['phase']=='coupling':
            for bank,row in enumerate(r['rows']):groups[(tuple(s['edge']),bank)][data['metadata'][s['case']]['base']].append(row['optimal'])
    fixed=[]
    for (edge,bank),bb in sorted(groups.items()):
        assert len(bb)==4 and all(len(v)==2 for v in bb.values())
        fixed.append(dict(edge=list(edge),bank=bank,correct_two_pose_bases=sum(all(v) for v in bb.values()),base_results={b:all(v) for b,v in bb.items()}))
    interpretation=__import__('json').loads((OUT/'interpretation.json').read_text());f=sources['focal'];details=[]
    for d in interpretation['focal_case_details']:
        cid=d['case'];a,r=(native[(f[k],cid)] for k in ('recipient','regulated'))
        details.append(dict(case=cid,state_divergence=d['recipient_regulated']['first_tick'],
            first_C6=d['recipient_regulated']['channels']['6'],first_C2=d['recipient_regulated']['channels']['2'],
            recipient_status=a['status'],regulated_status=r['status'],recipient_steps=a['steps'],regulated_steps=r['steps'],
            mask_changed=a['mask']!=r['mask'],status_changed=a['status']!=r['status']))
    writej(OUT/'target_timing_note.json',dict(status='PASS',new_executions=0,scope='Exploratory saved diagnostic accuracy; not a registered solving endpoint or selected output.',
        all_fixed_bank_target_results=fixed,positive_fixed_bank_counts=sum(x['correct_two_pose_bases']>0 for x in fixed),
        focal_timing=details,cases_with_C6_then_C2=sum(d['first_C6'] is not None and d['first_C2'] is not None and d['first_C6']<d['first_C2'] for d in details),
        cases_with_identical_common_state_but_different_terminal_mask=sum(d['state_divergence'] is None and d['mask_changed'] for d in details),
        limitation='Each bank is fixed across all cases; never choose a bank per case. Histories stop normally; no claim about unobserved later ticks.'))


if __name__=='__main__':main()
