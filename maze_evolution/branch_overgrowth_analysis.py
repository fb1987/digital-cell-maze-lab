"""V13A descriptive paired outcomes and bounded trajectory diagnostics only."""
import json
from collections import defaultdict,Counter
import numpy as np
from .branch_overgrowth_data import *
from .routing_transfer import lines,canonical
from .foundation_calibration import write_json
from .foundation_study_verify_core import grade
from .evaluator import distances
from .routing_mechanism_study import unpack_history

def pairkey(m):return m['base']+'/pose'+str(m['pose'])

def summarize(rows,meta):
    pairs=defaultdict(list);families={};strata={};lengths=Counter()
    for r in rows:
        m=meta[r['case']];s=families.setdefault(m['family'],Counter());s['inputs']+=1
        for key in ('valid','optimal','no_path'):s[key]+=r[key]
        s['false_no_path']+=r['reachable'] and r['status']=='no_path'
        if r['optimal']:lengths[len(m['path'])-1]+=1
        if m['family']=='paired':pairs[pairkey(m)].append(r)
    detail={}
    for k,rs in pairs.items():
        assert len(rs)==2;m=meta[rs[0]['case']];good=all(r['optimal'] for r in rs)
        detail[k]=dict(complete=good,template=m['template'],prefix=m['prefix'],graph=m['graph'],shape=m['shape'],pose=m['pose'])
        for name in (f'prefix/{m["prefix"]}',f'graph/{m["graph"]}',f'cross/{m["prefix"]}/{m["graph"]}'):
            s=strata.setdefault(name,Counter());s['pairs']+=1;s['complete']+=good
    return canonical(dict(families=families,strata=strata,details=detail,pairs=sum(d['complete'] for d in detail.values()),positive=sum(d['complete'] and d['prefix']>0 for d in detail.values()),pair_opportunities=len(detail),shortest_lengths=lengths))

def frame_details(history,o,native):
    m=o.maze;prepared=(np.frombuffer(m.cells,np.uint8),m.w,m.start,m.goal,np.asarray(o.to_goal,np.int32),np.asarray(distances(m,m.start),np.int32),len(o.path))
    route=np.zeros(len(m.cells),bool);route[o.path]=True;correct=[];valid=[];extras=[];missing=[];seen={};repeat=None
    for tick,state in enumerate(history,1):
        mask=(state[2]>0).astype(np.uint8);v,g,*_=grade(*prepared,mask,0)
        if v:valid.append(tick)
        if g:correct.append(tick)
        extras.append(int(np.count_nonzero(mask & ~route)));missing.append(int(np.count_nonzero(route & ~mask.astype(bool))))
        blob=state.tobytes()
        if repeat is None and blob in seen:repeat=dict(first=seen[blob],again=tick,period=tick-seen[blob])
        seen.setdefault(blob,tick)
    nt=native['steps'];matched=False
    if 0<nt<=len(history):
        matched=np.packbits(history[nt-1,2]>0,bitorder='little').tobytes().hex()==native['mask']
    return dict(native_steps=nt,native_optimal=native['optimal'],native_mask_at_tick_matches=matched,
        shortest_ticks=correct,legal_ticks=valid,later_shortest_ticks=[t for t in correct if t>nt],extra_cells=extras,missing_cells=missing,
        repeated_full_state=repeat,frames=len(history))

def compute():
    panel=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(OUT/'confirmation');rows=defaultdict(list);native={};traces=[];stats={};pending={};raster={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        pid,mode,r=e['model'],e['mode'],e['row'];cid=r['case'];o=cases[cid];m=meta[cid]
        if e['scope']!='trace':
            rows[pid+'|'+mode].append(r);native[pid,mode,cid]=r
            if e['scope']=='normal' and m['family']=='paired':
                mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(o.maze.cells)].astype(bool)
                route=np.zeros(len(mask),bool);route[o.path]=True;extra=int(np.count_nonzero(mask & ~route));miss=int(np.count_nonzero(route & ~mask))
                z=raster.setdefault(pid,{}).setdefault(f'{m["graph"]}/{m["prefix"]}',Counter());z['inputs']+=1;z['optimal']+=r['optimal'];z['path_contained']+=miss==0;z['one_extra_complete_path']+=miss==0 and extra==1
            continue
        h=unpack_history(e['history']);normal=native[pid,'normal',cid];own=native[pid,mode,cid];v=frame_details(h,o,own)
        if own['steps']<=len(h):assert v['native_mask_at_tick_matches'],(pid,mode,cid)
        v.update(case=cid,normal_optimal=normal['optimal'],normal_steps=normal['steps'],after_normal_shortest=[t for t in v['shortest_ticks'] if t>normal['steps']])
        key=pid+'|'+mode;s=stats.setdefault(key,Counter());s['traces']+=1;s['frames']+=len(h);s['full_horizon']+=len(h)==96;s['shortest_frames']+=len(v['shortest_ticks']);s['normal_failed']+=not normal['optimal'];s['normal_failed_later_correct']+=not normal['optimal'] and bool(v['after_normal_shortest']);s['native_failed_later_correct']+=not own['optimal'] and bool(v['later_shortest_ticks']);s['repeated_full_state']+=v['repeated_full_state'] is not None;s['final_shortest']+=len(h) in v['shortest_ticks'];s['native_tick_comparable']+=0<own['steps']<=len(h)
        pk=(pid,mode,pairkey(m))
        if pk in pending:
            other,oh=pending.pop(pk);same=np.array_equal(h,oh);both=sorted(set(v['shortest_ticks'])&set(other['shortest_ticks']));later=sorted(set(v['after_normal_shortest'])&set(other['after_normal_shortest']))
            if mode=='both_off':assert same
            s['pairs']+=1;s['paired_shortest_same_tick']+=bool(both);s['normal_failed_pair_later_both']+=not (v['normal_optimal'] and other['normal_optimal']) and bool(later);s['identical_two_goal_states']+=same
            traces.append(dict(model=pid,mode=mode,pair=pk[2],same_tick_shortest=both,identical_states=same,tasks=[other,v]))
        else:pending[pk]=(v,h.copy())
    assert not pending
    metrics={k:summarize(v,meta) for k,v in rows.items()};comparisons={};interventions={}
    for name,c in panel['chains'].items():
        if name.startswith('resample'):continue
        ds=metrics[panel['aliases'][name]+'|normal']['details'];good={k for k,v in ds.items() if v['complete']};comp={}
        for suffix in ('root','parent'):
            old={k for k,v in metrics[panel['aliases'][name+'_'+suffix]+'|normal']['details'].items() if v['complete']}
            comp[suffix]=dict(pairs=len(old),gained=sorted(good-old),lost=sorted(old-good))
        comparisons[name]=comp
    from .branch_overgrowth_study import TARGETS,MODES
    for name in TARGETS:
        pid=panel['aliases'][name];normal=metrics[pid+'|normal']['details'];interventions[name]={}
        for mode in MODES[1:]:
            ds=metrics[pid+'|'+mode]['details'];old={k for k in ds if normal[k]['complete']};new={k for k,v in ds.items() if v['complete']}
            interventions[name][mode]=dict(normal_success=len(old),retained=len(old&new),lost=len(old-new),new=len(new-old),complete=len(new),opportunities=len(ds))
    return canonical(dict(metrics=metrics,comparisons=comparisons,interventions=interventions,trace_details=traces,trace_summary=stats,raster_diagnostics=raster))

def analyze():
    p=compute();compressed_json(OUT/'analysis.json.gz',p)
    panel=read_compressed(OUT/'panel.json.gz')
    print(json.dumps({a:dict(pairs=p['metrics'][pid+'|normal']['pairs'],positive=p['metrics'][pid+'|normal']['positive']) for a,pid in panel['aliases'].items()},indent=2),flush=True)
