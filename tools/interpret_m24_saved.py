"""Posthoc M24 saved-only contrasts. No calls, selection or new cases."""
import sys,json,base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.branch_causality import *


def main():
    import numpy as np
    check();assert not (OUT/'interpretation.json').exists()
    data,rows,models=load();meta=data['metadata'];items=readz(OUT/'variants.json.gz')['items'];lookup={i['id']:i for i in items}
    caps={i:capabilities_plus(rs,meta) for i,rs in rows.items()};comparisons=[]
    for item in items:
        if item['kind']!='factorial':continue
        for factor in ('bypass0','bypass7','saved_ports'):
            if item[factor]:continue
            other=next(v['id'] for v in items if v['kind']=='factorial' and all(v[k]==(not item[k] if k==factor else item[k]) for k in ('bypass0','bypass7','saved_ports')))
            a=item['id'];b=other;aa=caps[a];bb=caps[b]
            comparisons.append(dict(left=a,right=b,factor=factor,
                capabilities={k:dict(gained=sorted(bb[k]-aa[k]),lost=sorted(aa[k]-bb[k])) for k in ('pairs','corridors','ordinary_bases','success','correct_no_path','false')},
                same_mask=sum(x['mask']==y['mask'] for x,y in zip(rows[a],rows[b])),
                same_mask_status=sum(all(x[k]==y[k] for k in ('mask','status')) for x,y in zip(rows[a],rows[b])),
                same_mask_status_steps=sum(all(x[k]==y[k] for k in ('mask','status','steps')) for x,y in zip(rows[a],rows[b])),
                left_work=aa['summary']['work'],right_work=bb['summary']['work']))
    root=caps[ROOT_ID];final=caps[FOCAL];strata={};rootcomparisons={}
    for item in items:
        i=item['id'];c=caps[i]
        rootcomparisons[i]={k:dict(gained=sorted(c[k]-root[k]),lost=sorted(root[k]-c[k])) for k in ('pairs','corridors','ordinary_bases','success','correct_no_path','false')}
        by={}
        for cid in data['queries']['all']:
            m=meta[cid]
            if m['family'] not in ('ordinary_perfect','ordinary_random'):continue
            length=len(m['path'])-1;label=m['family']+'/'+('16plus' if length>=16 else '8to15' if length>=8 else '0to7')
            cell=by.setdefault(label,dict(bases=set(),correct=set()));cell['bases'].add(m['base'])
            if m['base'] in c['ordinary_bases']:cell['correct'].add(m['base'])
        strata[i]={label:dict(bases=len(v['bases']),correct_both_poses=len(v['correct'])) for label,v in by.items()}
    traces=readz(OUT/'traces.json.gz')['records'];gain_histories={};spare_checks=0
    for record0 in traces:
        h=np.frombuffer(base64.b64decode(record0['history_base64']),np.uint16).reshape(record0['shape'])
        assert not h[:,8:].any();spare_checks+=h[:,8:].size
        if record0['case']==GAIN:
            for alias in record0['aliases']:gain_histories[alias]=h
    finalh=gain_histories[FOCAL];pre=gain_histories['factorial/bypass0=0/bypass7=0/ports=0']
    cells=[]
    for t in range(min(len(finalh),len(pre))):
        gained=np.flatnonzero((finalh[t,2]>0)&(pre[t,2]==0)).tolist()
        cleared=np.flatnonzero((pre[t,2]>0)&(finalh[t,2]==0)).tolist()
        if gained or cleared:cells.append(dict(tick=t,newly_lit_vs_parent=gained,cleared_vs_parent=cleared))
    finalcases={r['case']:r for r in rows[FOCAL]};parentcases={r['case']:r for r in rows['factorial/bypass0=0/bypass7=0/ports=0']}
    g=Genome.from_dict(lookup[FOCAL]['model']['genome']);assert not g.body.blocks[8] and not g.initialization[8]
    result=dict(status='saved_only_posthoc',inference_calls=0,new_cases=0,independent_confirmation=False,
        pairwise_factorial_contrasts=comparisons,versus_root=rootcomparisons,ordinary_reachable_length_strata=strata,
        raw_summary_length_label_caveat='Generic raw summary also bins ordinary_disconnected empty paths under 0to7. They are no-path tests, not length-zero paths; corrected reachable-only strata are here. Raw summary preserved.',
        spare_zero_saved_values_checked=spare_checks,gain_output_differences_vs_direct_parent=cells,
        gain=dict(final=finalcases[GAIN],direct_parent=parentcases[GAIN],path=meta[GAIN]['path']),
        output_recurrence=dict(
            context='Exact block2 of direct-parent and final; output write uses last private register23. Other instructions do not feed that terminal.',
            condition='If old C1[p] is zero, C2_next[p]=0 (terminal gate). If source, C2_next[p]=old C1[p]. Otherwise:',
            final='C2_next[p]=int(bool(old C0[p]) != bool(old C6[p])) if old C4[p] else 0',
            parent='C2_next[p]=min(65535, old C2[p] + (int(bool(old C0[p]) != bool(old C6[p])) if old C4[p] else 0))',
            domain='Completed ticks, open cells only, channel8 stays zero. This is a readout recurrence, not a shortest-path algorithm proof.'),
        limitations='Posthoc saved-only contrasts and static interpretation; no new confirmation, no general/speed/operator-policy inference.')
    # Static expression assertions guard the reported recurrence.
    b=g.body.blocks[2];assert b[-1].row()==[12,23,9,1,14,0,1]
    assert b[0].row()==[16,12,0,7,0,0,5] and b[2].row()==[2,14,12,3,0,0,64]
    assert g.body.ports[2][:8]==(0,1,3,8,5,4,7,6)
    writej(OUT/'interpretation.json',result)

if __name__=='__main__':main()
