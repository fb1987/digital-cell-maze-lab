"""V12G branch suppression is an external fitness label, never an inference input."""
from collections import deque
import numpy as np
from .foundation_fitness import evaluate as normal_evaluate
from .foundation_fitness import partial
from .regulatory_search import Evaluation
from cellular_maze_lab import neighbors


def branch_score(mask,o,side):
    label=o._foundation_label
    if label is None:return dict(prefix=0.,desired=False,wrong=0.,strict=False,score=partial(mask,o))
    m=o.maze;blocked=set(label['exits']);dist={m.start:0} if mask[m.start] else {};queue=deque(dist)
    while queue:
        p=queue.popleft()
        for q in neighbors(p,m.w,m.h):
            if q not in blocked and mask[q] and q not in dist:
                dist[q]=dist[p]+1;queue.append(q)
    # Shortest incoming path, after removing outgoing exits, cannot use a backwards entry.
    reached=dist.get(label['vertex'])==label['distance']
    prefix=0
    for p in label['prefix']:
        if p not in dist:break
        prefix+=1
    progress=max(0.,(prefix-1)/label['distance'])
    if not reached:progress=min(progress,.999)
    allowed=set(label['allowed'][side]);wrong=set(label['exits'])-allowed
    desired=sum(bool(mask[p]) for p in allowed)==1
    leakage=sum(bool(mask[p]) for p in wrong)/max(1,len(wrong))
    strict=bool(reached and desired and leakage==0)
    score=.2*progress+.4*progress*desired+.35*progress*desired*(1-leakage)+.05*partial(mask,o)
    return dict(prefix=progress,desired=desired,wrong=leakage,strict=strict,score=score)


def ranks(rows,policy):
    complete=all(r['valid'] or r['no_path'] for r in rows)
    raw=(sum(r['valid'] for r in rows),sum(r['optimal'] for r in rows),
        sum(r['no_path'] for r in rows)-sum(r['reachable'] and r['status']=='no_path' for r in rows),
        sum(r['pair_optimal'] and r['fork'] for r in rows)//2,
        round(sum(r['partial']+r['paired_partial'] for r in rows),8),
        -sum(r['reads']+r['dispatches'] for r in rows) if complete else 0)
    k=sum(r['pair_strict'] for r in rows)//2
    shaping=round(sum(r['branch']['score']+r['paired_branch'] for r in rows),8)
    if policy=='current':return (*raw[:4],0,raw[4],raw[5])
    if policy=='branch':return (*raw[:4],k,shaping,raw[5])
    if policy=='pair_archive':return (raw[3],raw[1],raw[0],raw[2],k,shaping,raw[5])
    if policy=='choice_archive':return (k,shaping,raw[3],raw[1],raw[0],raw[2],raw[5])
    raise ValueError(policy)


def annotate(ev,pairs,policy):
    for p_index,pair in enumerate(pairs):
        rows=ev.rows[p_index*2:p_index*2+2]
        for side,(o,r) in enumerate(zip(pair.cases,rows)):
            mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(o.maze.cells)]
            r['branch']=branch_score(mask,o,side)
            r['fork']=o._foundation_label is not None
        pair_strict=all(r['fork'] and r['branch']['strict'] for r in rows)
        weak=min(r['branch']['score'] for r in rows)
        for r in rows:r.update(pair_strict=pair_strict,paired_branch=weak)
    ev.fitness=ranks(ev.rows,policy)
    ev.case_values=[(int(r['valid'] or r['no_path']),int(r['optimal'] or r['no_path']),int(r['pair_optimal'] and r['fork']),
        int(r['pair_strict']) if policy=='branch' else 0,
        r['branch']['score']+r['paired_branch'] if policy=='branch' else r['partial']+r['paired_partial']) for r in ev.rows]
    # Exactly the same diversity descriptor, independent of selection pressure.
    return ev


def evaluate(item,pairs,topology,limits,policy):
    return annotate(normal_evaluate(item,pairs,topology,limits,True),pairs,policy)


def lexicase(rng,ranked):
    survivors=list(ranked);cases=list(range(len(ranked[0][0].case_values)));rng.shuffle(cases)
    for case in cases:
        for field in range(5):
            best=max(ev.case_values[case][field] for ev,_ in survivors)
            epsilon=.02 if field==4 else 0.
            survivors=[(ev,i) for ev,i in survivors if ev.case_values[case][field]>=best-epsilon]
            if len(survivors)==1:return survivors[0][1]
    return rng.choice(survivors)[1]
