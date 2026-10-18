"""V10 evaluator labels permit short training cues; unchanged V6 inference VM."""
from cellular_maze_lab import neighbors
from .choice_fitness import evaluate as choice_evaluate,lexicase


def decision(pair):
    """Deepest shared shortest prefix at distance 2..8 with disjoint exit sets.

    Only train_near splits permit remaining distance1; all other splits retain4.

    All shortest next steps are accepted, independent of BFS tie order. The
    chosen prefix is a shortest path to BOTH goals. Labels never reach the VM.
    """
    if pair.mixed or not all(o.path for o in pair.cases):return None
    minimum=1 if pair.first.maze.split.startswith("train_near") else 4
    a,b=pair.cases;m=a.maze
    for k in range(min(8,len(a.path)-2),1,-1):
        v=a.path[k]
        if any(o.to_goal[v]<minimum or k+o.to_goal[v]!=len(o.path)-1 for o in (a,b)):continue
        exits=[q for q in neighbors(v,m.w,m.h) if m.cells[q] and q!=a.path[k-1]]
        allowed=[[q for q in exits if o.to_goal[q]==o.to_goal[v]-1] for o in (a,b)]
        if not all(allowed) or set(allowed[0])&set(allowed[1]):continue
        man=lambda p,g:abs(p%m.w-g%m.w)+abs(p//m.w-g//m.w)
        detours=[all(man(q,o.maze.goal)>man(v,o.maze.goal) for q in want) for o,want in zip((a,b),allowed)]
        return dict(vertex=v,prefix=list(a.path[:k+1]),incoming=a.path[k-1],exits=exits,
            allowed=allowed,detours=detours,distance=k)
    return None



def evaluate(individual,pairs,topology,limits,pressure,horizon=16):
    if pressure not in ('fixed','curriculum','choice'):
        raise ValueError('Unknown V10 condition')
    # Explicit evaluation-only label cache. No labels/oracles enter Organism.
    for pair in pairs:pair.first._junction_label=decision(pair)
    return choice_evaluate(individual,pairs,topology,limits,'choice',horizon)
