"""M18 prespecified mechanical endpoints, independent of candidate inference."""
from collections import defaultdict
from .restoration_metrics import summarize as skill_summary
from .routing_transfer import canonical


def summarize(items,rows,data,protected):
    # All variants are fixed interventions; no winners are selected.
    skills=skill_summary(items,[],rows,data,protected);reports={};groups=defaultdict(list)
    for i in items:
        if i['kind'] not in ('copy','intervention'):continue
        ref=rows['anchor/'+i['anchor']];rs=rows[i['id']]
        assert [r['case'] for r in rs]==[r['case'] for r in ref]
        differences={f:sum(r[f]!=b[f] for r,b in zip(rs,ref)) for f in ('mask','status','steps','optimal','no_path')}
        bad_cases=[r['case'] for r,b in zip(rs,ref) if any(r[f]!=b[f] for f in ('mask','status','steps'))]
        losses=sum((b['optimal'] or b['no_path']) and not (r['optimal'] or r['no_path']) for r,b in zip(rs,ref))
        gains=sum((r['optimal'] or r['no_path']) and not (b['optimal'] or b['no_path']) for r,b in zip(rs,ref))
        v=dict(kind=i['kind'],arm=i['arm'],anchor=i['anchor'],reader=i['reader'],donor=i['donor'],target=i['target'],
            bounded_response_neutral=not bad_cases,differing_cases=bad_cases,differences=differences,
            correct_losses=losses,correct_gains=gains,
            work=sum(r['reads']+r['dispatches'] for r in rs),anchor_work=sum(r['reads']+r['dispatches'] for r in ref),
            memory_max=max(r['array_bytes'] for r in rs),anchor_memory_max=max(r['array_bytes'] for r in ref),
            skill_metrics=skills['models'][i['id']])
        if i['kind']=='intervention':
            pure=rows[i['pure_id']];v['versus_pure']={f:sum(r[f]!=b[f] for r,b in zip(rs,pure)) for f in ('mask','status','steps','optimal','no_path')}
        reports[i['id']]=v
        if i['kind']=='copy':groups[i['arm']].append(i['id'])
    return canonical(dict(models=reports,reference_metrics={i:v for i,v in skills['models'].items() if i not in reports},
        inputs=len(data['queries']['all']),copy_groups={arm:dict(aliases=len(ids),bounded_neutral=[i for i in ids if reports[i]['bounded_response_neutral']],
            preserve_all_correct=[i for i in ids if reports[i]['correct_losses']==0],any_correct_loss=[i for i in ids if reports[i]['correct_losses']]) for arm,ids in groups.items()},
        reference_joint_gate_eligible=skills['reference_eligible'],
        limitation='All copies/zeros are prespecified mechanical interventions, not evolved discoveries. Common-tick state equality is distinct from equal bounded responses; related aliases are not independent replicates.'))
