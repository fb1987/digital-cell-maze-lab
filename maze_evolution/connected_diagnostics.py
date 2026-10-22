"""M18 passive paired-history assay. No candidate changes, continuation or extra cases."""
import time,hashlib,json
import numpy as np
from .connected_trace import respond
from .restoration_trace import respond as old_respond
from .restoration_assay import trace_ids
from .deep_campaign_data import cases_from_manifest
from .exposure_selection import record
from .routing_transfer import canonical


def packet():
    from .connected_copy_assay import check,load,readz,OUT,RUN,guard,organism
    cfg=check();started=time.monotonic();data,rows,models=load();selected=trace_ids(data)
    cases=cases_from_manifest([m for m in data['mazes'] if m['case_id'] in selected.values()])
    items=readz(OUT/'pool.json.gz')['items'];lookup={i['id']:i for i in items}
    relevant=[e for e,rs in models if any(a in lookup or a in ('anchor/parent','anchor/child') for a in e['aliases'])]
    output=[];comparisons=[];calls=work=0;native_seconds=trace_seconds=0.;max_bytes=0
    for group,cid in selected.items():
        o=cases[cid];m=o.maze;histories={}
        for e in relevant:
            assert guard(RUN,dict(cfg,session_wall_seconds=cfg['trace_wall_seconds']),started) is None
            assert calls+2<=cfg['trace_call_cap']
            t=time.perf_counter();r,h,mem=(respond if e['model']['representation']=='connected' else old_respond)(e['model'],m);trace_seconds+=time.perf_counter()-t
            t=time.perf_counter();native=organism(e['model']).react(m.cells,m.w,m.h,m.start,m.goal);native_seconds+=time.perf_counter()-t
            rr=record(r,o);assert rr==record(native,o)==next(x for x in rows[e['aliases'][0]] if x['case']==cid)
            calls+=2;work+=2*(rr['reads']+rr['dispatches']);assert work<=cfg['trace_work_cap']
            max_bytes=max(max_bytes,mem)
            for a in e['aliases']:histories[a]=h
            output.append(dict(case=cid,group=group,aliases=e['aliases'],response=rr,history_shape=list(h.shape),
                history_sha256=hashlib.sha256(h.tobytes()).hexdigest(),instrumentation_bytes=mem))
        for i in items:
            h=histories[i['id']];old=histories['anchor/'+i['anchor']];n=min(len(h),len(old))
            equal=np.all(h[:n,:8]==old[:n],axis=(1,2));divergences=np.flatnonzero(~equal)
            copy_equal=bool(np.array_equal(h[:,i['target']],h[:,i['donor']]))
            v=dict(identity=i['id'],case=cid,common_completed_ticks=n-1,legacy_state_matches=bool(equal.all()),
                first_legacy_divergence=int(divergences[0]) if len(divergences) else None,copy_equals_donor_all_recorded_states=copy_equal)
            if i['kind']=='copy' and i['seeded']:
                assert equal.all() and copy_equal,(i['id'],cid)
            if i['kind']=='intervention':
                pure=histories[i['pure_id']];k=min(len(h),len(pure));diff=np.flatnonzero(np.any(h[:k,:8]!=pure[:k,:8],axis=(1,2)))
                v.update(pure_common_completed_ticks=k-1,zero_changes_legacy_common_tick=bool(len(diff)),first_zero_legacy_divergence=int(diff[0]) if len(diff) else None)
            comparisons.append(v)
        del histories
    assert time.monotonic()-started<cfg['trace_wall_seconds']
    return dict(selected_cases=selected,traces=output,comparisons=comparisons,calls=calls,work=work,
        native_seconds=native_seconds,trace_seconds=trace_seconds,wall_seconds=time.monotonic()-started,max_instrumentation_bytes=max_bytes,
        limitation='Passive copies share primitive semantics; native terminal equality and full history hash replay. Common-prefix comparison never forces execution after either native stopping rule. Zero writer is a prespecified intervention, not evolved behavior.')


def traces():
    from .connected_copy_assay import OUT,writez,writej
    assert not (OUT/'traces.json.gz').exists();p=packet();writez(OUT/'traces.json.gz',p)
    writej(OUT/'trace_session.json',{k:v for k,v in p.items() if k not in ('traces','comparisons')})


def trace_audit():
    from .connected_copy_assay import OUT,readz,writej
    assert not (OUT/'trace_audit.json').exists();saved=readz(OUT/'traces.json.gz');actual=packet()
    for k in ('selected_cases','traces','comparisons','calls','work'):assert canonical(actual[k])==saved[k],k
    writej(OUT/'trace_audit.json',dict(status='PASS',all_history_hashes_and_comparisons_replayed=True,calls=actual['calls'],work=actual['work'],wall_seconds=actual['wall_seconds']))
