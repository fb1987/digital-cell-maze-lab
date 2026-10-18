"""Post-hoc ancestry/rotation diagnosis of the first turned paired success.

Transformed versions of an inspected maze are diagnostics, not fresh holdouts.
No genome or selection setting is changed.
"""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from cellular_maze_lab import neighbors
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_audit import unpack
from .range_study import output_row
from .regulatory import Genome
from .regulatory_runtime import Organism
from .runtime import Limits
from .signal_audit import lines
from .signal_probe import observe


def route_shape(mask,maze):
    p=maze.start;previous=-1;directions=[];route=[p]
    while p!=maze.goal:
        q=next(q for q in neighbors(p,maze.w,maze.h) if mask[q] and q!=previous)
        directions.append(q-p);previous,p=p,q;route.append(p)
    names={-1:'west',1:'east',-maze.w:'north',maze.w:'south'}
    return dict(edges=len(directions),turns=sum(a!=b for a,b in zip(directions,directions[1:])),
        directions=sorted({names[d] for d in directions}),route=route,
        internal_junctions=sum(sum(maze.cells[q] for q in neighbors(p,maze.w,maze.h))>=3 for p in route[1:-1]))


def diagnose(out):
    out=Path(out);started=time.perf_counter();work=0;calls=0
    config=json.loads((out/'config.json').read_text());limits=Limits(**config['eval_limits'])
    champions=json.loads((out/'champions.json').read_text());frozen=hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    manifest={r['case_id']:r for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read())}
    def oracle(case):
        r=manifest[case]
        return Oracle.build(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],case))
    successes=[]
    for r in lines(out/'paired_holdout.jsonl.gz'):
        for c in r.get('cases',[]):
            if c['valid']:
                m=oracle(c['case']).maze;shape=route_shape(unpack(c['mask'],len(m.cells)),m)
                if shape['turns']>0:successes.append((r['arm'],r['replicate'],c['case'],shape))
    if not successes:raise RuntimeError('No turned paired candidate success to diagnose')
    arm,rep,case,shape=sorted(successes,key=lambda r:r[:3])[0];topology,pressure,label=arm.split('/')
    item=champions[f'factor/{topology}/{pressure}/{rep}']['archives'][label]['individual']
    pair=next(p for p in json.loads((out/'pairs.json').read_text()) if case in (p['first'],p['second']))
    a,b=[oracle(pair[k]) for k in ('first','second')]
    parents={}
    paths=sorted((out/'logs').glob('*/*.genomes.jsonl.gz'))
    for path in paths:
        for r in lines(path):parents[r['id']]=r['parent']
    chain=[];identity=item['id']
    while identity in parents:chain.append(identity);identity=parents[identity]
    needed=set(chain);genomes={}
    for path in paths:
        for r in lines(path):
            if r['id'] in needed:genomes[r['id']]=r
    cache={};ancestry=[]
    def run(saved,o):
        nonlocal work,calls
        genome=Genome.from_dict(saved['genome']);key=(genome.digest,o.maze.digest)
        if key not in cache:
            m=o.maze;r=Organism(genome,topology,limits).react(m.cells,m.w,m.h,m.start,m.goal)
            row=output_row(arm,rep,o,r,assess(r,o));work+=r.dispatches+r.spatial_reads;calls+=1
            if row['valid_path']:row['shape']=route_shape(r.mask,m)
            cache[key]=row
        return cache[key]
    for identity in reversed(chain):
        saved=genomes[identity]
        ancestry.append(dict(id=identity,parent=saved['parent'],birth=saved['birth'],genome_sha=Genome.from_dict(saved['genome']).digest,
            goals=[run(saved,o) for o in (a,b)]))
    rotations=[]
    for rotation in range(4):
        grid=np.frombuffer(a.maze.cells,dtype=np.uint8).reshape(a.maze.h,a.maze.w).copy()
        start,goals=a.maze.start,[a.maze.goal,b.maze.goal];n=a.maze.w
        for _ in range(rotation):
            grid=np.rot90(grid,-1).copy();start=(start%n)*n+(n-1-start//n)
            goals=[(p%n)*n+(n-1-p//n) for p in goals]
        for label,goal in zip(('a','b'),goals):
            m=Maze(grid.tobytes(),n,n,start,goal,'perfect',a.maze.seed,'rotation_diagnostic',f'{case}/rotation{rotation}/{label}')
            rotations.append(dict(rotation_clockwise_degrees=rotation*90,goal_label=label,output=run(item,Oracle.build(m))))
    organism=Organism(Genome.from_dict(item['genome']),topology,limits);switch=[]
    for horizon in (16,32,64):
        x=observe(organism,a.maze.cells,a.maze.w,a.maze.h,a.maze.start,a.maze.goal,horizon,True)
        y=observe(organism,b.maze.cells,b.maze.w,b.maze.h,b.maze.start,b.maze.goal,horizon,True)
        work+=x.dispatches+x.reads+y.dispatches+y.reads
        switch.append(dict(horizon=horizon,aligned=x.steps==y.steps==horizon,
            all_state_equal=bool(np.array_equal(x.state,y.state)),binary_output_equal=bool(np.array_equal(x.state[2]>0,y.state[2]>0))))
        del x,y
    assert frozen==hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    result=dict(scope='Post-hoc diagnosis of an inspected final case, not new accuracy tests; no retuning',
        elapsed_seconds=time.perf_counter()-started,charged_work=work,normal_calls=calls,probe_calls=6,
        champions_sha256=frozen,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        arm=arm,replicate=rep,case=case,individual=item,shape=shape,external_ancestor=parents[chain[-1]],
        ancestry=ancestry,rotations=rotations,goal_switch=switch)
    write_json(out/'turned_path_diagnostic.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('individual','ancestry','rotations')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/factor_curriculum');diagnose(parser.parse_args().out)
