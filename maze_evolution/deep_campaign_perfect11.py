"""Wilson loop-erased walks on a 5x5 room grid, with uniform open-cell endpoints."""
import random
from .datasets import seed_for
from .evaluator import Maze, Oracle


def wilson_case(root,split,replicate,index):
    seed=seed_for(root,split+'-wilson-11-a1',replicate,index);rng=random.Random(seed)
    n=11;side=5;tree={rng.randrange(25)};edges=[]
    adjacent=lambda p:[q for q in (p-1,p+1,p-side,p+side) if 0<=q<25 and abs(p%side-q%side)+abs(p//side-q//side)==1]
    while len(tree)<25:
        path=[next(p for p in range(25) if p not in tree)];positions={path[0]:0}
        while path[-1] not in tree:
            q=rng.choice(adjacent(path[-1]))
            if q in positions:
                path=path[:positions[q]+1];positions={p:i for i,p in enumerate(path)}
            else:positions[q]=len(path);path.append(q)
        edges.extend(zip(path,path[1:]));tree.update(path)
    cells=bytearray(121)
    pixel=lambda p:(2*(p//side)+1)*n+2*(p%side)+1
    for p in tree:cells[pixel(p)]=1
    for a,b in edges:cells[(pixel(a)+pixel(b))//2]=1
    opened=[p for p,v in enumerate(cells) if v];start,goal=rng.sample(opened,2)
    case=f'{split}/r{replicate}/{index}/perfect/11x11/wilson-a1'
    return Oracle.build(Maze(bytes(cells),11,11,start,goal,'perfect',seed,split,case))
