"""V10 matched geometry/source/fork; shorten goal cues only during training."""
from dataclasses import replace
import gzip,json
from cellular_maze_lab import neighbors
from .choice_data import ChoiceData,prior_manifests as earlier_manifests
from .distance_fitness import decision
from .evaluator import Oracle
from .goal_data import GoalPair,layout_hash


def prior_manifests(root):
    return earlier_manifests(root)+json.loads(gzip.open(root/'results/choice_priority/mazes.json.gz','rt').read())


def cue_distances(generation,replicate):
    if generation<0:raise ValueError('Negative generation')
    if generation>=32:return None
    base=1 if generation<16 else 2
    return (base,base+1) if (generation+replicate)%2==0 else (base+1,base)


class DistanceData(ChoiceData):
    def batch(self,replicate,generation,pressure='fixed'):
        if pressure not in ('fixed','curriculum'):raise ValueError('Unknown V10 curriculum')
        pairs=super().batch(replicate,generation)
        distances=cue_distances(generation,replicate) if pressure=='curriculum' else None
        if distances is None:return pairs
        result=[]
        for pair in pairs:
            if pair.mixed:result.append(pair);continue
            phase=1 if generation<16 else 2
            key=('near',replicate,generation,pair.first.maze.family)
            if key not in self.pairs:
                label=decision(pair);cases=[]
                for oracle,length in zip(pair.cases,distances):
                    m=oracle.maze;goal=label['vertex']
                    for _ in range(length):
                        goal=min(q for q in neighbors(goal,m.w,m.h) if m.cells[q] and oracle.to_goal[q]==oracle.to_goal[goal]-1)
                    split=f'train_near{phase}_goal'
                    maze=replace(m,goal=goal,split=split,case_id=m.case_id.replace('train_goal/',split+'/',1))
                    cases.append(Oracle.build(maze))
                near=GoalPair(*cases);new=decision(near)
                if new is None or any(new[k]!=label[k] for k in ('vertex','prefix','incoming','distance','exits')):
                    raise RuntimeError('Shortening changed the common decision anchor')
                if [o.to_goal[new['vertex']] for o in near.cases]!=list(distances):raise RuntimeError('Incorrect goal cue distance')
                if not all(set(a)<=set(b) for a,b in zip(new['allowed'],label['allowed'])):raise RuntimeError('New shortest exit')
                self.pairs[key]=near
                for o in near.cases:self.cache[o.maze.case_id]=o;self.single.owners[o.maze.digest]='train'
            result.append(self.pairs[key])
        return result

    def pair_manifest(self):
        return [dict(first=p.first.maze.case_id,second=p.second.maze.case_id,mixed=p.mixed,
                     layout_sha256=layout_hash(p.first.maze),decision=decision(p)) for p in self.pairs.values()]
