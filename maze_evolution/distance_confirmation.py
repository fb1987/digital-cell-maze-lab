"""V10A: frozen training-selected primitive, fresh matched near/far confirmation."""
import argparse,gzip,hashlib,json,time
from collections import deque
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from cellular_maze_lab import neighbors
from .baselines import baseline,warm_baselines
from .beacon_runtime import Organism,warm_runtime
from .beacon_probe import observe
from .choice_fitness import evaluate
from .distance_data import DistanceData,prior_manifests
from .distance_fitness import decision
from .datasets import manifest
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair,layout_hash
from .regulatory import Genome
from .regulatory_search import Individual
from .runtime import Limits,Reaction


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unpack(value,n):return np.unpackbits(np.frombuffer(bytes.fromhex(value),dtype=np.uint8),bitorder='little')[:n]
def load_oracle(r):return Oracle.build(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id']))


def prepare(out):
    root=Path(__file__).resolve().parents[1];out=Path(out)
    if out.exists() and any(out.iterdir()):raise FileExistsError('Fresh confirmation required')
    original=root/'results/distance_curriculum/training_choice_diagnostic.json';d=json.loads(original.read_text())
    assert len(d['records'])==1;r=d['records'][0];nodes=r['nodes'];models={};digests=set()
    for role,node in (('child',nodes[-1]),('parent',nodes[-2]),('root',nodes[0])):
        item=node['individual'];digest=Genome.from_dict(item['genome']).digest
        if digest not in digests:models[role]=item;digests.add(digest)
    out.mkdir(parents=True);write_json(out/'models.json',models)
    source_paths=[Path(__file__),root/'docs/DISTANCE_CONFIRMATION_V10A.md',original]
    prior=root/'results/distance_curriculum/mazes.json.gz';source_paths.append(prior)
    config=dict(seed=2026101810,models_sha256=sha(out/'models.json'),horizon=16,
        limits=asdict(Limits(max_steps=1024,reads_per_site=8192,instructions_per_site=131072)),
        source_sha256={**json.loads((root/'results/distance_curriculum/environment.json').read_text())['source_sha256'],**{str(p.relative_to(root)):sha(p) for p in source_paths}},
        scope='Frozen training-selected diagnostic models, no training/reselection;12 independent layouts,near/far matched.')
    write_json(out/'config.json',config);print('Models frozen',config['models_sha256'])


def row_layout(r):return hashlib.sha256(f"{r['w']},{r['h']}:".encode()+bytes.fromhex(r['cells_hex'])).hexdigest()


def inputs():
    root=Path(__file__).resolve().parents[1]
    return prior_manifests(root)+json.loads(gzip.open(root/'results/distance_curriculum/mazes.json.gz','rt').read())


def run(out):
    out=Path(out);root=Path(__file__).resolve().parents[1];started=time.perf_counter()
    if (out/'outputs.json').exists():raise FileExistsError('Confirmation already evaluated')
    config=json.loads((out/'config.json').read_text());models=json.loads((out/'models.json').read_text())
    assert sha(out/'models.json')==config['models_sha256']
    for p,h in config['source_sha256'].items():assert sha(root/p)==h
    previous=inputs();data=DistanceData(config['seed'],previous);pairs=[];entries=[];oracles=[]
    specs=[(n,f) for n in (9,17) for f in ('perfect','random') for _ in range(3)]
    for index,(n,family) in enumerate(specs):
        far=data.pair('confirmation_far',0,index,n,family,32);anchor=decision(far);near=[];lengths=(2,3) if index%2==0 else (3,2)
        for o,length in zip(far.cases,lengths):
            m=o.maze;goal=anchor['vertex']
            for _ in range(length):goal=min(q for q in neighbors(goal,m.w,m.h) if m.cells[q] and o.to_goal[q]==o.to_goal[goal]-1)
            near.append(Oracle.build(replace(m,goal=goal,split='confirmation_near',case_id=m.case_id.replace('confirmation_far/','confirmation_near/',1))))
        near=GoalPair(*near)
        for distance,pair in (('far',far),('near',near)):
            label=dict(anchor);v=label['vertex'];label['allowed']=[[q for q in label['exits'] if o.to_goal[q]==o.to_goal[v]-1] for o in pair.cases]
            man=lambda p,g:abs(p%n-g%n)+abs(p//n-g//n)
            label['detours']=[all(man(q,o.maze.goal)>man(v,o.maze.goal) for q in want) for o,want in zip(pair.cases,label['allowed'])]
            assert all(label['allowed']) and not set(label['allowed'][0])&set(label['allowed'][1])
            assert all(set(x)<=set(y) for x,y in zip(label['allowed'],anchor['allowed']))
            assert all(label['distance']+o.to_goal[v]==len(o.path)-1 for o in pair.cases)
            pair.first._junction_label=label;pairs.append(pair);oracles.extend(pair.cases)
            entries.append(dict(first=pair.first.maze.case_id,second=pair.second.maze.case_id,distance=distance,decision=label,
                goal_to_fork=[o.to_goal[v] for o in pair.cases],layout_sha256=layout_hash(pair.first.maze)))
    # Entire environment manifest is saved before any candidate inference.
    with gzip.open(out/'mazes.json.gz','wt',compresslevel=9) as f:json.dump(manifest(oracles),f,separators=(',',':'))
    write_json(out/'pairs.json',entries);warm_runtime();warm_baselines();limits=Limits(**config['limits']);rows=[];work=0;baselines=[]
    for role,saved in models.items():
        ev=evaluate(Individual.load(saved),pairs,'evolved',limits,'choice',config['horizon']);work+=ev.work
        rows.append(dict(role=role,id=saved['id'],junction=ev.junction,strict_pairs=ev.strict_pairs,work=ev.work,cases=ev.rows))
    for o in oracles:
        m=o.maze;r=baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal);a=assess(r,o)
        baselines.append(dict(case=m.case_id,status=r.status,steps=r.steps,mask=np.packbits(r.mask,bitorder='little').tobytes().hex(),valid=a.valid_path,optimal=a.optimal))
    write_json(out/'outputs.json',dict(models=rows,baseline=baselines))
    write_json(out/'environment.json',dict(elapsed_seconds=time.perf_counter()-started,charged_work=work,
        normal_responses=len(oracles)*len(models),probes=2*len(oracles)*len(models),previous_layouts=len({row_layout(r) for r in previous}),
        source_sha256=config['source_sha256'],models_sha256=config['models_sha256'],note='Includes fresh generation/JIT warmup; no latency competition.'))
    print('Confirmation complete')


def verify(out):
    out=Path(out);root=Path(__file__).resolve().parents[1];started=time.perf_counter()
    config=json.loads((out/'config.json').read_text());models=json.loads((out/'models.json').read_text());outputs=json.loads((out/'outputs.json').read_text())
    assert sha(out/'models.json')==config['models_sha256']
    for p,h in config['source_sha256'].items():assert sha(root/p)==h
    prior_layouts={row_layout(r) for r in inputs()}
    oracles={r['case_id']:load_oracle(r) for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read())};entries=json.loads((out/'pairs.json').read_text())
    layouts={layout_hash(o.maze) for o in oracles.values()};assert len(layouts)==12 and not layouts&prior_layouts and len(prior_layouts)==8690
    pairs={};by_case={}
    for entry in entries:
        pair=GoalPair(oracles[entry['first']],oracles[entry['second']]);label=entry['decision'];pairs[entry['first']]=pair;v=label['vertex']
        assert layout_hash(pair.first.maze)==entry['layout_sha256']==layout_hash(pair.second.maze)
        assert pair.first.maze.start==pair.second.maze.start==label['prefix'][0]
        assert len(label['prefix'])-1==label['distance'] and 2<=label['distance']<=8
        assert label['prefix'][-1]==v and all(b in neighbors(a,pair.first.maze.w,pair.first.maze.h) and pair.first.maze.cells[b] for a,b in zip(label['prefix'],label['prefix'][1:]))
        for i,o in enumerate(pair.cases):
            m=o.maze;exact={q for q in neighbors(v,m.w,m.h) if m.cells[q] and o.to_goal[q]==o.to_goal[v]-1}
            assert exact==set(label['allowed'][i])
            assert label['distance']+o.to_goal[v]==len(o.path)-1 and o.to_goal[v]==entry['goal_to_fork'][i]
            if entry['distance']=='near':assert o.to_goal[v] in (2,3)
            else:assert o.to_goal[v]>=4 and len(o.path)-1>=8
            by_case[m.case_id]=(entry,i)
        assert not set(label['allowed'][0])&set(label['allowed'][1])
    normal=rasters=0;work=replayed_work=0;summary=[]
    for record in outputs['models']:
        organism=Organism(Individual.load(models[record['role']]).genome,'evolved',Limits(**config['limits']),goal_pulse=True);aggregates={d:dict(pairs=0,strict=0,valid=0,optimal=0,J=0.) for d in ('near','far')}
        minima=[]
        for row in record['cases']:
            o=oracles[row['case']];m=o.maze;n=len(m.cells);entry,i=by_case[m.case_id];label=entry['decision'];mask=unpack(row['mask'],n)
            a=assess(Reaction(mask,row['status'],row['steps'],0,0,0),o);assert (a.valid_path,a.optimal)==(row['valid'],row['optimal']);normal+=1
            r=organism.react(m.cells,m.w,m.h,m.start,m.goal);on=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],True);off=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],False)
            assert r.status==row['status'] and np.array_equal(r.mask,mask)
            lit=unpack(row['probe_mask'],n);removed=unpack(row['source_removed_mask'],n);assert np.array_equal(on.state[2]>0,lit) and np.array_equal(off.state[2]>0,removed)
            aligned=on.steps==off.steps==config['horizon'];seen={m.start} if lit[m.start] and not any(lit[p] and not m.cells[p] for p in range(n)) else set();queue=deque(seen)
            while queue:
                for q in neighbors(queue.popleft(),m.w,m.h):
                    if lit[q] and q not in seen:seen.add(q);queue.append(q)
            want=set(label['allowed'][i]);wrong=set(label['exits'])-want;desired=want&set(np.flatnonzero(lit));bad=wrong&set(np.flatnonzero(lit));v=label['vertex']
            R=sum(p in seen and not removed[p] for p in label['prefix'][2:])/len(label['prefix'][2:]);causal=sum(not removed[p] for p in desired)/max(1,len(desired))
            C=causal*(1-len(bad)/len(wrong))/len(desired) if desired and v in seen else 0.
            J=(.25*R+.75*C) if aligned else 0.;strict=bool(aligned and v in seen and len(desired)==1 and not bad and causal==1)
            assert abs(J-row['junction']['score'])<1e-12 and strict==row['junction']['strict'];rasters+=1
            group=aggregates[entry['distance']];group['valid']+=a.valid_path;group['optimal']+=a.optimal
            if i==0:minima=[J];group['pairs']+=1;first_strict=strict
            else:group['strict']+=first_strict and strict;group['J']+=min(minima[0],J)
            cost=row['dispatches']+sum(row['reads'])+sum(row['signal']['dispatches'])+sum(row['signal']['reads']);work+=cost
            replayed_work+=r.dispatches+r.spatial_reads+on.dispatches+on.reads+off.dispatches+off.reads
        for distance,counts in aggregates.items():summary.append(dict(role=record['role'],distance=distance,**counts))
    for row in outputs['baseline']:
        o=oracles[row['case']];a=assess(Reaction(unpack(row['mask'],len(o.maze.cells)),row['status'],row['steps'],0,0,0),o);assert a.optimal and row['optimal'];normal+=1
    env=json.loads((out/'environment.json').read_text());assert work==replayed_work==env['charged_work']
    write_json(out/'summary.json',summary);write_json(out/'verification.json',dict(all_checks_passed=True,elapsed_seconds=time.perf_counter()-started,
        reassessed_normal_outputs=normal,independent_junction_rasters=rasters,replayed_normals=rasters,replayed_probes=2*rasters,replayed_work=replayed_work,
        unique_layouts=len(layouts),prior_layouts=len(prior_layouts),models_sha256=config['models_sha256'],source_sha256=sha(__file__)))
    text=['# V10A: frozen short-cue training primitive confirmation','',
        'The child,parent and initial ancestor were frozen before12 fresh matched layouts were generated. Each layout supplies near2/3-edge and far≥4-edge goal pairs. No training or reselection.','',
        '| Frozen model | Goal distance | Strict both /12 | Normal valid /24 | Normal shortest /24 | Mean weaker J |','|---|---|---:|---:|---:|---:|']
    for r in summary:text.append(f"| {r['role']} | {r['distance']} | {r['strict']} | {r['valid']} | {r['optimal']} | {r['J']/r['pairs']:.4f} |")
    text += ['', 'BFS completes all48 near/far goal instances. Independent units are12 layouts,not24 pairs. Each9/17 ×tree/random stratum has3 layouts. '
        'All8690 earlier layouts are excluded. Completed outputs and causal16-tick choices are distinct measures; this small descriptive assay cannot establish impossibility or a significance claim.','',
        f"Seed{config['seed']},frozen model SHA `{config['models_sha256']}`. Main confirmation{env['elapsed_seconds']:.3f}s including fresh generation/JIT warmup; "
        f"{env['normal_responses']} candidate normal responses/{env['probes']} probes,{env['charged_work']:,} work units. Verification{time.perf_counter()-started:.3f}s; "
        f"all{normal} normal outputs and{rasters} junction rasters checked,all{rasters} candidate normals/{2*rasters} probes replayed with equal work. "
        'No latency competition is claimed. Primary V10 results stay unchanged; all genotypes remain preserved.','',
        'Protocol:`docs/DISTANCE_CONFIRMATION_V10A.md`; raw genomes,hashes,manifests,labels,rasters and verification:`results/distance_confirmation/`.']
    (out.parent/(out.name+'.md')).write_text('\n'.join(text)+'\n');print(summary)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/distance_confirmation');group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true');group.add_argument('--run',action='store_true');group.add_argument('--verify',action='store_true');args=parser.parse_args()
    (prepare if args.prepare else run if args.run else verify)(args.out)
