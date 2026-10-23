"""M29 posthoc saved-array interpretation, zero new VM/writer executions."""
import hashlib,json,sqlite3,sys,zlib
from pathlib import Path
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.state_interference import ROOT,OUT,RUN,check,readz,read_records,writej,unpacked
from maze_evolution.state_dependency import divergence


def main():
    check();assert not (OUT/'interpretation.json').exists();sources=readz(OUT/'sources.json.gz');data=readz(OUT/'cases.json.gz');records=read_records()
    natives={(s['model'],s['case']):(r,h) for s,r,h in records if s['phase']=='native'}
    def history(i,c):
        r,blob=natives[(i,c)];raw=zlib.decompress(blob);assert hashlib.sha256(raw).hexdigest()==r['history_sha256']
        return np.frombuffer(raw,dtype='<u2').reshape(r['history_shape'])
    focal=sources['focal'];a,b,r=(focal[k] for k in ('recipient','donor','regulated'));details=[]
    for cid in data['queries']['all']:
        ha,hb,hr=(history(i,cid) for i in (a,b,r));common=min(len(ha),len(hb),len(hr))
        aa,bb,rr=(h[1:common,6] for h in (ha,hb,hr));different=aa!=bb
        neither=(rr!=aa)&(rr!=bb);assert not np.any(neither),'Saved fused C6 must be a local parent-output selection in common window'
        ar=divergence(ha,hr);br=divergence(hb,hr)
        details.append(dict(case=cid,labels=data['metadata'][cid]['labels'],common_completed_ticks=common-1,
            recipient_regulated=ar,donor_regulated=br,
            parent_C6_different_site_ticks=int(np.count_nonzero(different)),
            regulated_equals_recipient_when_parents_differ=int(np.count_nonzero((rr==aa)&different)),
            regulated_equals_donor_when_parents_differ=int(np.count_nonzero((rr==bb)&different)),
            regulated_equals_neither=0))
    coupling={};changes=Counter()
    for s,obs,h in records:
        if s['phase']!='coupling':continue
        bank=s['edge'][0];model=s['parents'][bank];base=natives[(model,s['case'])][0]['row'];row=obs['rows'][bank]
        e=str(s['edge']);c=coupling.setdefault(e,dict(edge=s['edge'],cases=0,history_changed=0,mask_changed=0,status_changed=0,steps_changed=0,work_fields_changed=0,
            parent_native_genome=model,physical_cross_channel=int(__import__('maze_evolution.connected_genome',fromlist=['Genome']).Genome.from_dict(sources['models'][model]['genome']).body.ports[s['edge'][1]][s['edge'][2]])))
        c['cases']+=1;c['history_changed']+=not obs['comparisons'][bank]['full_native_history_equal']
        for label,fields in [('mask_changed',['mask']),('status_changed',['status']),('steps_changed',['steps']),('work_fields_changed',['reads','dispatches'])]:
            c[label]+=any(row[k]!=base[k] for k in fields)
    isolated=[]
    for s,obs,h in records:
        if s['phase']!='isolation':continue
        rr=[natives[(i,s['case'])][0]['row'] for i in s['parents']]
        expected=sum(x['reads']+x['dispatches'] for x in rr);assert obs['counted_work']==expected
        isolated.append(dict(case=s['case'],pair=s['pair'],array_bytes_model=obs['cost']['array_bytes_excluding_history'],
            recipient_array_bytes=rr[0]['array_bytes'],sum_parent_array_bytes=sum(x['array_bytes'] for x in rr),
            work=expected,recipient_work=rr[0]['reads']+rr[0]['dispatches']))
    writej(OUT/'interpretation.json',dict(status='PASS',new_executions=0,scope='Posthoc analysis of saved arrays and frozen task outputs only.',
        focal_case_details=details,coupling_edge_details=coupling,isolation_cost_details=isolated,
        focal_summary=dict(cases=len(details),cases_with_parent_C6_value_disagreement=sum(x['parent_C6_different_site_ticks']>0 for x in details),
            cases_using_recipient_values=sum(x['regulated_equals_recipient_when_parents_differ']>0 for x in details),
            cases_using_donor_values=sum(x['regulated_equals_donor_when_parents_differ']>0 for x in details),
            all_regulated_C6_values_equal_one_parent=True,
            first_regulated_vs_recipient_channel_counts=dict(Counter(str(x['recipient_regulated'].get('first_channel')) for x in details))),
        limitation='Common recorded windows only. Local expression insensitivity does not rule out other-writer, later-time, stopping or budget interference. Direct-copy width is conservative; isolated banks are not a combined solver.'))
    print(json.dumps({e:c for e,c in coupling.items() if c['history_changed']},indent=2),flush=True)


if __name__=='__main__':main()
