"""Post-hoc V10 short-cue training primitive: preserve and replay, no final tests."""
import argparse,gzip,hashlib,json,time
from pathlib import Path
from collections import deque
import numpy as np
from cellular_maze_lab import neighbors
from .beacon_runtime import Organism
from .beacon_probe import observe
from .distance_fitness import evaluate,decision
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair
from .junction_fitness import junction_metrics,unpack
from .regulatory_search import Individual
from .runtime import Limits
from .signal_audit import lines


def intervention(item,pair,topology,limits,horizon,pulse,ablate):
    organism=Organism(item.genome,topology,limits,goal_pulse=pulse,ablate_nonlocal=ablate)
    rows=[];masks=[];removed=[];work=0
    for oracle in pair.cases:
        m=oracle.maze;r=organism.react(m.cells,m.w,m.h,m.start,m.goal);a=assess(r,oracle)
        on=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
        off=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,False)
        masks.append((on.state[2]>0).astype(np.uint8));removed.append((off.state[2]>0).astype(np.uint8))
        rows.append(dict(case=m.case_id,status=r.status,steps=r.steps,valid=a.valid_path,optimal=a.optimal,failure=a.failure,
            mask=np.packbits(r.mask,bitorder='little').tobytes().hex(),
            probe_mask=np.packbits(masks[-1],bitorder='little').tobytes().hex(),
            source_removed_mask=np.packbits(removed[-1],bitorder='little').tobytes().hex(),
            aligned=on.steps==off.steps==horizon,dispatches=r.dispatches,reads=r.spatial_reads,
            probe_dispatches=[on.dispatches,off.dispatches],probe_reads=[on.reads,off.reads]))
        work+=r.dispatches+r.spatial_reads+on.dispatches+on.reads+off.dispatches+off.reads
    metrics=junction_metrics(masks,removed,pair,decision(pair),all(r['aligned'] for r in rows))
    for r,j in zip(rows,metrics):r['junction']=j
    return dict(goal_pulse=pulse,ablate_nonlocal=ablate,cases=rows,work=work,
        strict_both=metrics[0]['pair_both'],junction=min(r['score'] for r in metrics))


def diagnose(out):
    out=Path(out);target=out/'training_choice_diagnostic.json'
    if target.exists():raise FileExistsError('Diagnostic already exists')
    started=time.perf_counter();config=json.loads((out/'config.json').read_text());champions=json.loads((out/'champions.json').read_text())
    candidates=[];inputs={}
    for p in sorted((out/'logs').glob('*/*curriculum*.evaluations.jsonl.gz')):
        for r in lines(p):
            if r['split']=='train' and r['strict_pairs']:
                candidates.append(r);inputs[str(p.relative_to(out))]=hashlib.sha256(p.read_bytes()).hexdigest()
    records=[];work=responses=probes=0
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());by_case={r['case_id']:r for r in manifest}
    for record in candidates:
        condition=record['condition'];tag=condition.replace('/','_');known={}
        for p in sorted((out/'logs').glob(f'*/{tag}.genomes.jsonl.gz')):
            inputs[str(p.relative_to(out))]=hashlib.sha256(p.read_bytes()).hexdigest()
            for item in lines(p):known[item['id']]=item
        first,second=next((a,b) for a,b in zip(record['cases'][::2],record['cases'][1::2]) if a['junction']['pair_both'])
        def oracle(case):
            r=by_case[case];return Oracle.build(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id']))
        pair=GoalPair(oracle(first['case']),oracle(second['case']));label=decision(pair)
        assert pair.first.maze.split.startswith('train_near')
        chain=[];item=known[record['id']]
        while True:
            chain.append(item)
            if item['birth']==0 or item['parent'] not in known:break
            item=known[item['parent']]
            if len(chain)>256:raise RuntimeError('Ancestry ceiling')
        chain.reverse();nodes=[];previous=None;topology=condition.split('/')[1];limits=Limits(**config['train_limits'])
        for item in chain:
            ev=evaluate(Individual.load(item),[pair],topology,limits,'choice',config['horizon'])
            genes=item['genome']['genes'];edits=[] if previous is None else [dict(index=i,before=previous[i] if i<len(previous) else None,
                after=genes[i] if i<len(genes) else None) for i in range(max(len(previous),len(genes)))
                if (previous[i] if i<len(previous) else None)!=(genes[i] if i<len(genes) else None)]
            nodes.append(dict(individual=item,junction=ev.junction,strict_both=bool(ev.strict_pairs),cases=ev.rows,work=ev.work,gene_row_changes=edits))
            work+=ev.work;responses+=2;probes+=4;previous=genes
        assert json.loads(json.dumps(nodes[-1]['cases']))==[first,second] and nodes[-1]['strict_both']
        interventions=[]
        for pulse,ablate in ((False,False),(True,True)):
            r=intervention(Individual.load(chain[-1]),pair,topology,limits,config['horizon'],pulse,ablate)
            work+=r['work'];responses+=2;probes+=4;interventions.append(r)
        records.append(dict(condition=condition,generation=record['generation'],first=first['case'],second=second['case'],
            decision=label,goal_to_fork=[o.to_goal[label['vertex']] for o in pair.cases],nodes=nodes,interventions=interventions,
            selected_model_was_in_final_population=record['id'] in {r['id'] for r in json.loads((out/'checkpoints'/(tag+'.json')).read_text())['population']}))
    for name in ('champions.json','mazes.json.gz','pairs.json','config.json'):inputs[name]=hashlib.sha256((out/name).read_bytes()).hexdigest()
    result=dict(scope='Post-hoc training-selected diagnostic, after main final evaluation. No new mazes, no final-set evaluation, no training/reselection or generalization claim.',
        records=records,elapsed_seconds=time.perf_counter()-started,charged_work=work,normal_responses=responses,probes=probes,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=inputs)
    write_json(target,result);print({k:v for k,v in result.items() if k not in ('records','input_sha256')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/distance_curriculum');diagnose(parser.parse_args().out)
