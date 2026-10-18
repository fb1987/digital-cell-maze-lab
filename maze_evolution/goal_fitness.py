"""Goal-conditioned source-connected output shaping, never candidate inference."""
from collections import deque
from dataclasses import dataclass
import math
import numpy as np
from cellular_maze_lab import neighbors
from .evaluator import distances
from .regulatory_runtime import Organism
from .regulatory_search import Evaluation,evaluate as route_evaluate
from .signal_fitness import signal_metrics
from .signal_probe import observe


def source_component(mask,maze):
    selected=set(np.flatnonzero(mask).tolist())
    if maze.start not in selected or any(not maze.cells[p] for p in selected):return selected,set()
    component={maze.start}; queue=deque([maze.start])
    while queue:
        for q in neighbors(queue.popleft(),maze.w,maze.h):
            if q in selected and q not in component:component.add(q);queue.append(q)
    return selected,component


def progress(component,oracle):
    distance=len(oracle.path)-1
    if distance<=0 or not component:return 0.
    remaining=[oracle.to_goal[p] for p in component if oracle.to_goal[p]>=0]
    return max(0.,1.-min(remaining)/distance) if remaining else 0.


def goal_metrics(masks,source_removed,pair):
    """Each target is compared against the other target on identical geometry.

    Specificity uses connected-component progress only, so changing detached
    goal markers cannot increase it. Output source dependence is binary-raster
    dependence at distance>=2, not a hidden concentration difference.
    """
    cases=pair.cases; maze=cases[0].maze
    components=[source_component(masks[0],maze)]
    components.append(components[0] if np.array_equal(masks[0],masks[1]) else source_component(masks[1],maze))
    if not hasattr(cases[0],'_source_distances'):
        cases[0]._source_distances=np.asarray(distances(maze,maze.start))
    d=cases[0]._source_distances
    rows=[]
    for i,oracle in enumerate(cases):
        selected,component=components[i]
        own=progress(component,oracle); cross=progress(components[1-i][1],oracle)
        if i==0 or components[0] is not components[1]:
            degrees={p:sum(q in component for q in neighbors(p,maze.w,maze.h)) for p in component}
            branches=sum(max(0,v-(1 if p==maze.start else 2)) for p,v in degrees.items())
        distal=[p for p in component if d[p]>=2]
        causal=float(np.mean([not bool(source_removed[i][p]) for p in distal])) if distal else 0.
        connected=len(component)/max(1,len(selected))
        quality=own*connected*causal/(1+2*branches)
        specificity=max(0.,own-cross)
        score=math.sqrt(quality*specificity) if oracle.path else 0.
        rows.append(dict(score=score,progress=own,cross_progress=cross,specificity=specificity,
            quality=quality,branches=branches,source_degree=degrees.get(maze.start,0),
            component=len(component),selected=len(selected),source_fraction=causal,
            connected_fraction=connected))
    both=(not pair.mixed and all(r['quality']>=.05 and r['specificity']>=.02 for r in rows))
    for r in rows:r['pair_both']=bool(both)
    return rows


@dataclass
class GoalEvaluation(Evaluation):
    signal: float
    long_signal: float
    family_signals: dict
    inference_work: int
    probe_work: int
    goal_score: float
    goal_families: dict
    goal_quality: float
    goal_specificity: float
    pair_both: float


def evaluate(individual,pairs,topology,limits,pressure,horizon=16):
    if pressure not in ('transmission','goal'):raise ValueError('Unknown V4 objective')
    cases=[case for pair in pairs for case in pair.cases]
    if not cases:raise ValueError('Empty goal evaluation')
    base=route_evaluate(individual,cases,topology,limits)
    organism=Organism(individual.genome,topology,limits)
    signals=[]; long=[]; families={}; goal_families={}; goals=[]; regular=[]; work=0
    for j,pair in enumerate(pairs):
        masks=[]; removed=[]; aligned=True
        for i,oracle in enumerate(pair.cases):
            m=oracle.maze
            a=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
            b=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,False)
            metrics=signal_metrics(a,b,oracle,horizon)
            masks.append((a.state[2]>0).astype(np.uint8))
            removed.append((b.state[2]>0).astype(np.uint8))
            aligned &= metrics['aligned']
            row=base.rows[2*j+i]; row['signal']=metrics
            row['probe_mask']=np.packbits(masks[-1],bitorder='little').tobytes().hex()
            row['source_removed_mask']=np.packbits(removed[-1],bitorder='little').tobytes().hex()
            signals.append(metrics['score'])
            if oracle.path:
                long.append(metrics['score']);families.setdefault(m.family,[]).append(metrics['score'])
            work+=a.dispatches+a.reads+b.dispatches+b.reads
            del a,b
        metrics=goal_metrics(masks,removed,pair)
        if not aligned:
            for r in metrics:r['score']=0.;r['pair_both']=False
        for i,(oracle,r) in enumerate(zip(pair.cases,metrics)):
            r['aligned']=bool(aligned)
            base.rows[2*j+i]['goal']=r
            goals.append(r)
            if oracle.path:goal_families.setdefault(oracle.maze.family,[]).append(r['score'])
        if not pair.mixed:regular.append(metrics[0]['pair_both'])
    fitness=list(base.fitness)
    fitness[3]=round(fitness[3]+sum(signals)+(2*sum(r['score'] for r in goals) if pressure=='goal' else 0.),8)
    values=[(v,o,p+s+(2*g['score'] if pressure=='goal' else 0.))
            for (v,o,p),s,g in zip(base.case_values,signals,goals)]
    mean=lambda vals:float(np.mean(vals)) if vals else 0.
    return GoalEvaluation(tuple(fitness),values,base.descriptor,base.rows,base.work+work,
        mean(signals),mean(long),{k:mean(v) for k,v in families.items()},base.work,work,
        mean([r['score'] for r in goals]),{k:mean(v) for k,v in goal_families.items()},
        mean([r['quality'] for r in goals]),mean([r['specificity'] for r in goals]),mean(regular))
