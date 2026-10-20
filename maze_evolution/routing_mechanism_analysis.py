"""V12T predeclared descriptive comparisons, no adaptive selection."""
import json
from collections import defaultdict,Counter
import numpy as np
from .routing_mechanism_data import *
from .routing_transfer import lines,canonical
from .foundation_calibration import write_json
from .foundation_study_verify_core import grade

PREDICTOR_K={'fresh2':1,'spliced':2,'carry0':3}

def pairkey(m):return m['base']+'/pose'+str(m['pose'])

def summarize(rows,meta):
    pairs=defaultdict(list);families={};strata={};lengths=Counter()
    for r in rows:
        m=meta[r['case']];f=m['family'];s=families.setdefault(f,Counter())
        s['inputs']+=1
        for name in ('optimal','valid','no_path'):s[name]+=r[name]
        s['false_no_path']+=r['reachable'] and r['status']=='no_path'
        if r['optimal']:lengths[len(m['path'])-1]+=1
        if f=='paired':pairs[pairkey(m)].append(r)
    details={};full=defaultdict(list)
    for k,rr in pairs.items():
        assert len(rr)==2
        m=meta[rr[0]['case']];good=all(r['optimal'] for r in rr)
        details[k]=dict(complete=good,template=m['template'],prefix=m['prefix'],shape=m['shape'],source_shape=m['source_shape'],graph=m['graph'],second=m['second'],pose=m['pose'],route_lengths=[len(meta[r['case']]['path'])-1 for r in rr])
        full[m['base']].append(good)
        for label in (f"prefix/{m['prefix']}/{m['source_shape']}",f"shape/{m['shape']}",f"graph/{m['graph']}/{m['second']}",f"cross/{m['prefix']}/{m['source_shape']}/{m['graph']}/{m['second']}"):
            s=strata.setdefault(label,Counter());s['opportunities']+=1;s['complete']+=good
    return canonical(dict(families=families,details=details,strata=strata,shortest_lengths=dict(lengths),
        pairs=sum(d['complete'] for d in details.values()),pair_opportunities=len(details),
        positive=sum(d['complete'] and d['prefix']>0 for d in details.values()),
        full_groups=sum(len(v)==8 and all(v) for v in full.values())))

def predictions(o):
    m=o.maze;ds=np.asarray(o.to_goal);mask=((ds>=0)&(ds<=ds[m.start])).reshape(m.h,m.w)
    fixed=np.zeros(mask.size,bool);fixed[[m.start,m.goal]]=True;fixed=fixed.reshape(mask.shape);values=[]
    for k in range(7):
        values.append(np.packbits(mask.ravel(),bitorder='little').tobytes().hex())
        degree=np.zeros(mask.shape,np.uint8);degree[:-1]+=mask[1:];degree[1:]+=mask[:-1];degree[:,:-1]+=mask[:,1:];degree[:,1:]+=mask[:,:-1]
        mask &= (degree>1)|fixed
    return values

def context_interval(values):
    # Context-conditional uncertainty; not independent discovery or a lineage CI.
    a=np.asarray(values,float);rng=np.random.default_rng(2026101915001)
    return np.quantile(np.mean(a[rng.integers(0,len(a),(10000,len(a)))],axis=1),[.025,.975]).tolist()

def packet(panel,metrics):
    aliases=panel['aliases'];comparisons={}
    roots={'fresh0':['fresh0_root'],'fresh2':['fresh2_root'],'carry0':['narrow_root'],'carry1':['broad_root'],'spliced':['narrow_root','broad_root','shared_root']}
    for name,rr in roots.items():
        ds=metrics[aliases[name]+'|normal']['details'];rootsets=[{k for k,d in metrics[aliases[r]+'|normal']['details'].items() if d['complete']} for r in rr];union=set().union(*rootsets)
        good={k for k,d in ds.items() if d['complete']};templates=sorted({d['template'] for d in ds.values()});deltas=[]
        for t in templates:deltas.append(sum((k in good)-(k in union) for k,d in ds.items() if d['template']==t and d['prefix']>0))
        comparisons[name]=dict(roots=rr,gained=sorted(good-union),lost=sorted(union-good),root_union=len(union),descendant=len(good),
            positive_delta_by_context=deltas,mean_positive_delta_interval=context_interval(deltas),
            caveat='Conditional on these selected lineages and grammar; contexts are sampled units, poses/variants correlated. Not a replicated policy or causal splice test.')
    interventions={}
    from .routing_mechanism_runtime import MODES
    for name,pid in aliases.items():
        normal=metrics[pid+'|normal']['details'];interventions[name]={}
        for mode in MODES[1:]:
            if pid+'|'+mode not in metrics:continue
            ds=metrics[pid+'|'+mode]['details'];old={k for k in ds if normal[k]['complete']};new={k for k,d in ds.items() if d['complete']}
            interventions[name][mode]=dict(opportunities=len(ds),normal_success=len(old),retained=len(old&new),lost=len(old-new),new=len(new-old),complete=len(new))
    return canonical(dict(comparisons=comparisons,interventions=interventions))

def analyze():
    from .routing_mechanism_study import unpack_history
    panel=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(OUT/'confirmation');rows=defaultdict(list);normal={};traces=[]
    predictor={cid:predictions(o) for cid,o in cases.items() if o.path};fits={};trace_stats={};pending={};frame_prepared={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        pid,mode,r=e['model'],e['mode'],e['row'];cid=r['case'];m=meta[cid];o=cases[cid]
        if e['scope']!='trace':
            rows[pid+'|'+mode].append(r)
            if e['scope']=='normal':
                normal[pid,cid]=r
                if cid in predictor:
                    for label in ('all_reachable',m['family'],f"shape/{m.get('shape','ordinary')}"):
                        s=fits.setdefault(pid,{}).setdefault(label,dict(inputs=0,matches=[0]*7,emitted_matches=[0]*7));s['inputs']+=1
                        for k,v in enumerate(predictor[cid]):s['matches'][k]+=r['mask']==v;s['emitted_matches'][k]+=r['mask']==v and r['status']=='emitted'
            continue
        h=unpack_history(e['history']);s=trace_stats.setdefault(pid+'|'+mode,Counter());s['traces']+=1;s['frames']+=len(h);s['full64']+=len(h)==64
        n=normal[pid,cid];native_tick=n['steps'];correct=[];after=[]
        maze=o.maze
        if cid not in frame_prepared:frame_prepared[cid]=(np.frombuffer(maze.cells,np.uint8),maze.w,maze.start,maze.goal,np.asarray(o.to_goal,np.int32),np.asarray(distances(maze,maze.start),np.int32),len(o.path))
        for tick,state in enumerate(h,1):
            mask=(state[2]>0).astype(np.uint8);graded=grade(*frame_prepared[cid],mask,0)
            if graded[1]:correct.append(tick)
            if tick>native_tick and graded[1]:after.append(tick)
            if mode=='normal' and tick==native_tick:
                assert np.packbits(mask,bitorder='little').tobytes().hex()==n['mask'];s['native_emission_mask_matches']+=1
        s['shortest_geometry_frames']+=len(correct);s['traces_with_shortest_geometry']+=bool(correct)
        s['normal_failed_with_later_shortest_geometry']+=not n['optimal'] and bool(after)
        pkey=(pid,mode,pairkey(m))
        item=dict(case=cid,normal_optimal=n['optimal'],native_tick=native_tick,shortest_geometry_ticks=correct,later_shortest_geometry_ticks=after)
        if pkey in pending:
            other,oh=pending.pop(pkey);both=sorted(set(correct)&set(other['shortest_geometry_ticks']));equal=np.array_equal(h,oh)
            if mode=='both_off':assert equal
            s['pairs']+=1;s['identical_two_goal_states']+=equal;s['paired_shortest_geometry_at_same_tick']+=bool(both)
            s['both_goals_have_some_shortest_frame']+=bool(correct) and bool(other['shortest_geometry_ticks'])
            traces.append(dict(model=pid,mode=mode,pair=pairkey(m),same_tick_shortest=both,identical_states=equal,tasks=[other,item]))
        else:pending[pkey]=(item,h.copy())
    assert not pending
    metrics={k:summarize(v,meta) for k,v in rows.items()}
    compressed_json(OUT/'metrics.json.gz',metrics);compressed_json(OUT/'analysis.json.gz',packet(panel,metrics))
    compressed_json(OUT/'trace_details.json.gz',traces)
    write_json(OUT/'trace_summary.json',dict(diagnostic_only=True,interpretation='Forced trajectories never count as normal inference; budgets still bind. No stopping retune.',results=trace_stats))
    write_json(OUT/'predictor_fit.json',dict(prospective_fixed_k=PREDICTOR_K,models=fits,interpretation='Oracle-based observer only. Prospective fixed-k fits are tests of the S hypothesis; other k values are descriptive, not selected algorithms. No oracle enters candidate inference.'))
    print(json.dumps({a:dict(pairs=metrics[p+'|normal']['pairs'],positive=metrics[p+'|normal']['positive'],families=metrics[p+'|normal']['families']) for a,p in panel['aliases'].items()},indent=2))
