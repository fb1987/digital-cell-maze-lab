"""M21 post-audit interpretation of saved responses and histories; no inference."""
import base64,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.readout_causality import OUT,PRIOR,RUN,check,readz,writej,sha,SPECIALISTS,Genome
from maze_evolution.deep_campaign_store import hashed,packed

def main():
    check();assert not (OUT/'interpretation.json').exists()
    for f in ('audit.json','trace_audit.json'):assert json.loads((OUT/f).read_text())['status']=='PASS'
    items=readz(OUT/'variants.json.gz')['items'];lookup={x['id']:x for x in items}
    data=readz(OUT/'panel.json.gz');mazes={m['case_id']:m for m in data['mazes']}
    traces=readz(OUT/'traces.json.gz');hist={};response={}
    for x in traces['records']:
        a=np.frombuffer(base64.b64decode(x['history_base64']),np.uint16).reshape(x['shape'])
        for i in x['aliases']:hist[i,x['case']]=a;response[i,x['case']]=x['row']
    panel=json.loads((OUT/'trace_panel.json').read_text());summ=json.loads((OUT/'summary.json').read_text())
    parent=Genome.from_dict(readz(PRIOR/'sources.json.gz')['anchors']['parent']['genome'])
    formula={};comparisons={};signals={}
    for identity in SPECIALISTS:
        base=identity+'/intact/saved';g=Genome.from_dict(lookup[base]['model']['genome'])
        assert g.body.blocks[6][:7]==parent.body.blocks[6][:7]
        assert (g.body.blocks[6][-1].op,g.body.blocks[6][-1].a,g.body.blocks[6][-1].b,g.body.blocks[6][-1].gate)==(3,15,13,64)
        signal=g.body.ports[6][7];gate=g.body.ports[6][1];assert gate==5
        checked=0;cc={};ss={}
        for cid in panel['selected_cases']:
            a=hist[base,cid];m=mazes[cid];open_sites=np.frombuffer(bytes.fromhex(m['cells_hex']),np.uint8).astype(bool)
            old=a[:-1].astype(np.int32)
            expected=np.where(old[:,signal]>0,np.maximum(0,old[:,gate]-4),0).astype(np.uint16)
            assert np.array_equal(expected[:,open_sites],a[1:,6][:,open_sites]), (identity,cid)
            checked+=int(len(old)*sum(open_sites))
            other={}
            for variant in ('bypass_keep/saved','remove_only/saved','bypass_remove/saved','intact/restore_old'):
                b=hist[identity+'/'+variant,cid];shared=min(len(a),len(b));per=[]
                for k in range(10):
                    dif=np.any(a[:shared,k]!=b[:shared,k],axis=1);loc=np.flatnonzero(dif)
                    per.append(int(loc[0]) if len(loc) else None)
                other[variant]=dict(shared_ticks=shared-1,original_eight_states_equal=bool(np.array_equal(a[:shared,:8],b[:shared,:8])),
                    first_differing_completed_tick_by_channel=per,
                    same_mask_status_steps=all(response[base,cid][k]==response[identity+'/'+variant,cid][k] for k in ('mask','status','steps')))
            cc[cid]=other
            if cid in panel['gained_inputs']:
                # Preserve complete small histories in original trace packet; these
                # compact summaries help connect recurrence to a particular raster.
                ss[cid]=dict(start=m['start'],goal=m['goal'],width=m['w'],height=m['h'],
                    path=data['metadata'][cid]['path'],signal_channel=signal,
                    ticks=[dict(t=t,source_c6=int(h[6,m['start']]),goal_c6=int(h[6,m['goal']]),
                        c6_positive_sites=np.flatnonzero(h[6]).tolist(),output_positive_sites=np.flatnonzero(h[2]).tolist(),
                        signal_max=int(h[signal].max()),gate_c5_positive_sites=int(sum(h[5]>0))) for t,h in enumerate(a)])
        formula[identity]=dict(status='PASS',checked_open_site_transitions=checked,signal_channel=signal,
            recurrence=f'C6[t+1,p] = (C{signal}[t,p] > 0) * max(0, C5[t,p] - 4)',
            proof='Unchanged first seven C6 nodes: scratch13=4; scratch15 = (local1 if local7>0 else scratch12), gated by local1. scratch12 also gated by local7, so zero if local7=0. Last SUB15,13 ungated. Therefore positive C5 above4 passes only if signal>0.',
            scope='All completed-tick transitions on ALL eight preregistered trace cases; posthoc symbolic simplification, no new inference')
        comparisons[identity]=cc;signals[identity]=ss
    writej(OUT/'interpretation.json',dict(scope='Saved audited M21 evidence only; mechanism/development, no new cases or inference',
        recurrence_checks=formula,state_comparisons=comparisons,gain_timecourses=signals,causal_tests=summ['causal_tests'],
        all_native_audit=json.loads((OUT/'audit.json').read_text()),trace_audit=json.loads((OUT/'trace_audit.json').read_text())))
    print('M21 saved interpretation PASS',sum(x['checked_open_site_transitions'] for x in formula.values()),'site transitions')

if __name__=='__main__':main()
