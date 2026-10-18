"""V8 decision labels and fitness only. Candidate inference remains V6."""
from dataclasses import dataclass
import numpy as np
from cellular_maze_lab import neighbors
from .balance_fitness import evaluate as balanced_evaluate, pair_bonuses
from .balance_fitness import BalanceEvaluation
from .goal_fitness import source_component


def decision(pair):
    """Deepest shared shortest prefix at distance 2..8 with disjoint exit sets.

    All shortest next steps are accepted, independent of BFS tie order. The
    chosen prefix is a shortest path to BOTH goals. Labels never reach the VM.
    """
    if pair.mixed or not all(o.path for o in pair.cases):return None
    a,b=pair.cases;m=a.maze
    for k in range(min(8,len(a.path)-2),1,-1):
        v=a.path[k]
        if any(o.to_goal[v]<4 or k+o.to_goal[v]!=len(o.path)-1 for o in (a,b)):continue
        exits=[q for q in neighbors(v,m.w,m.h) if m.cells[q] and q!=a.path[k-1]]
        allowed=[[q for q in exits if o.to_goal[q]==o.to_goal[v]-1] for o in (a,b)]
        if not all(allowed) or set(allowed[0])&set(allowed[1]):continue
        man=lambda p,g:abs(p%m.w-g%m.w)+abs(p//m.w-g//m.w)
        detours=[all(man(q,o.maze.goal)>man(v,o.maze.goal) for q in want) for o,want in zip((a,b),allowed)]
        return dict(vertex=v,prefix=list(a.path[:k+1]),incoming=a.path[k-1],exits=exits,
            allowed=allowed,detours=detours,distance=k)
    return None


def junction_metrics(masks,removed,pair,label=None,aligned=True):
    label=decision(pair) if label is None else label
    if label is None:return [dict(eligible=False,score=0.,prefix=0.,choice=0.,strict=False,pair_both=False)]*2
    rows=[];m=pair.first.maze;v=label['vertex'];prefix=label['prefix'][2:]
    for i in (0,1):
        selected,component=source_component(masks[i],m)
        reach=sum(p in component and not removed[i][p] for p in prefix)/len(prefix)
        want=set(label['allowed'][i]);wrong=set(label['exits'])-want
        on=want&selected;bad=wrong&selected
        causal=sum(not removed[i][p] for p in on)/max(1,len(on))
        choice=(int(v in component)*causal*(1-len(bad)/len(wrong))/max(1,len(on))) if on else 0.
        strict=bool(v in component and len(on)==1 and not bad and causal==1 and aligned)
        rows.append(dict(eligible=True,score=(.25*reach+.75*choice) if aligned else 0.,
            prefix=reach,choice=choice,strict=strict,connected=v in component,
            desired_on=sorted(on),wrong_on=sorted(bad),causal=causal,aligned=bool(aligned)))
    for row in rows:row['pair_both']=all(r['strict'] for r in rows)
    return rows


def unpack(row,key,n):
    return np.unpackbits(np.frombuffer(bytes.fromhex(row[key]),dtype=np.uint8),bitorder='little')[:n]


@dataclass
class JunctionEvaluation(BalanceEvaluation):
    junction: float
    junction_both: float
    junction_families: dict


def annotate(ev,pairs,pressure):
    if pressure not in ('balanced','junction'):raise ValueError('Unknown V8 pressure')
    minima=[];both=[];families={};bonuses=[]
    for j,pair in enumerate(pairs):
        rows=ev.rows[2*j:2*j+2];n=pair.first.maze.w*pair.first.maze.h
        if not hasattr(pair.first,'_junction_label'):pair.first._junction_label=decision(pair)
        label=pair.first._junction_label
        metrics=junction_metrics([unpack(r,'probe_mask',n) for r in rows],
            [unpack(r,'source_removed_mask',n) for r in rows],pair,label,
            all(r['goal']['aligned'] for r in rows))
        if label is not None:
            weaker=min(r['score'] for r in metrics);minima.append(weaker);both.append(metrics[0]['pair_both'])
            families.setdefault(pair.first.maze.family,[]).append(weaker)
        for row,metric in zip(rows,metrics):row['junction']=metric
        values=pair_bonuses([r['score'] for r in metrics],'balanced') if pressure=='junction' and label is not None else [r['factor_bonus'] for r in rows]
        for row,value in zip(rows,values):row['factor_bonus']=value;bonuses.append(value)
    if pressure=='junction':
        fit=list(ev.normal_fitness);fit[3]=round(fit[3]+sum(r['signal']['score'] for r in ev.rows)+sum(bonuses),8)
        ev.fitness=tuple(fit)
        ev.case_values=[(a,b,r['partial']+r['signal']['score']+bonus) for (a,b,_),r,bonus in zip(ev.case_values,ev.rows,bonuses)]
    mean=lambda xs:sum(xs)/len(xs) if xs else 0.
    return JunctionEvaluation(**ev.__dict__,junction=mean(minima),junction_both=mean(both),
        junction_families={k:mean(v) for k,v in families.items()})


def evaluate(individual,pairs,topology,limits,pressure,horizon=16):
    return annotate(balanced_evaluate(individual,pairs,topology,limits,'balanced',horizon),pairs,pressure)
