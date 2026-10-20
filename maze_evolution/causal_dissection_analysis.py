"""V12V prespecified contrasts, exact signal-equivalence predictions, and tradeoffs."""
from collections import defaultdict,Counter
import json
from .causal_dissection_data import *
from .causal_dissection_study import EARLY,MODES
from .routing_mechanism_analysis import summarize
from .lineage_mapping_analysis import comparison
from .routing_transfer import lines,canonical
from .foundation_calibration import write_json

CONTRASTS=(('d00','d01'),('d00','dest_only'),('d01','d02'),('dest_only','d02'),
    ('d07','d07_no_store'),('d07_no_store','d08'),('d07','d08'),
    ('d12','d12_no_store'),('d12_no_store','d12_restore_store'),('d12','d12_restore_store'),
    ('d07','d12_restore_store'),('fresh2_root','fresh2'),('broad_root','carry1'))
PREDICTIONS={
    ('d00','channel4_zero'):'dest_only',('d01','channel4_zero'):'d02',
    ('dest_only','channel4_zero'):'dest_only',('d02','channel4_zero'):'d02',
    ('d00','channel4_restore'):'d00',('d01','channel4_restore'):'d01',
    ('dest_only','channel4_restore'):'d00',('d02','channel4_restore'):'d01'}


def equality(rows,reference):
    out=Counter(inputs=len(rows));mismatches=[]
    for cid,r in rows.items():
        q=reference[cid];out['full_record_equal']+=r==q
        out['mask_equal']+=r['mask']==q['mask'];out['status_equal']+=r['status']==q['status'];out['steps_equal']+=r['steps']==q['steps']
        out['behavior_equal']+=all(r[f]==q[f] for f in ('mask','status','steps'))
        if r!=q:mismatches.append(dict(case=cid,fields=[k for k in r if r[k]!=q[k]]))
    return dict(counts=dict(out),mismatches=mismatches)

def compute(panel,meta,events):
    rows=defaultdict(list);native=defaultdict(dict);responses=defaultdict(dict)
    for e in events:
        if e['scope']=='parity':continue
        pid,mode,r=e['model'],e['mode'],e['row'];rows[pid+'|'+mode].append(r);responses[pid,mode][r['case']]=r
        if e['scope']=='normal':native[pid][r['case']]=r
    metrics={k:summarize(v,meta) for k,v in rows.items()};aliases=panel['aliases']
    comparisons={a+'->'+b:comparison(a,b,metrics,native,aliases,meta) for a,b in CONTRASTS}
    normal_equivalence={a+'->'+b:equality(native[aliases[a]],native[aliases[b]]) for a,b in CONTRASTS}
    predictions={}
    for (name,mode),reference in PREDICTIONS.items():
        predictions[name+'|'+mode]=dict(reference=reference,**equality(responses[aliases[name],mode],native[aliases[reference]]))
    context_interactions={};d={n:metrics[aliases[n]+'|normal']['details'] for n in EARLY}
    for pair,info in d['d00'].items():
        if info['prefix']<=0:continue
        s=context_interactions.setdefault(info['template'],Counter())
        values={n:int(d[n][pair]['complete']) for n in EARLY}
        s['destination_without_deletion']+=values['dest_only']-values['d00']
        s['destination_with_deletion']+=values['d02']-values['d01']
        s['deletion_without_destination']+=values['d01']-values['d00']
        s['deletion_with_destination']+=values['d02']-values['dest_only']
        s['interaction']+=values['d02']-values['d01']-values['dest_only']+values['d00']
    interventions={}
    for name in EARLY:
        pid=aliases[name];normal=metrics[pid+'|normal']['details'];interventions[name]={}
        for mode in MODES:
            ds=metrics[pid+'|'+mode]['details'];old={k for k in ds if normal[k]['complete']};new={k for k,d in ds.items() if d['complete']}
            interventions[name][mode]=dict(pair_opportunities=len(ds),normal_success=len(old),retained=len(old&new),lost=len(old-new),new=len(new-old),complete=len(new))
    return canonical(metrics),canonical(dict(comparisons=comparisons,normal_equivalence=normal_equivalence,signal_predictions=predictions,context_interactions=context_interactions,interventions=interventions,
        interpretation='U-informed constructed probes are mechanistic tests, not evolved discoveries. Finite-case equivalence and context-conditional effects do not prove universal semantics, a general solver, evolutionary-policy advantage or speedup. No final-based replacement.'))

def analyze():
    panel=read_compressed(OUT/'panel.json.gz');_,_,meta=load(OUT/'confirmation')
    metrics,analysis=compute(panel,meta,lines(OUT/'confirmation/responses.jsonl.gz'))
    compressed_json(OUT/'metrics.json.gz',metrics);compressed_json(OUT/'analysis.json.gz',analysis)
    brief={a:dict(kind=panel['kinds'][a],pairs=metrics[p+'|normal']['pairs'],positive=metrics[p+'|normal']['positive'],families=metrics[p+'|normal']['families']) for a,p in panel['aliases'].items()}
    write_json(OUT/'summary.json',brief);print(json.dumps(brief,indent=2),flush=True)
