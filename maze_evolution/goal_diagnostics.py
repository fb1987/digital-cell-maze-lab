"""Frozen-genome V4 range ablation; both inference and probes are ablated."""
import argparse,gzip,json,time
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair
from .goal_fitness import goal_metrics
from .range_study import output_row
from .regulatory import Genome
from .regulatory_runtime import Organism
from .runtime import Limits
from .signal_fitness import signal_metrics
from .signal_probe import observe


def diagnose(out):
    out=Path(out);started=time.perf_counter();work=0;rows=[]
    champions=json.loads((out/'champions.json').read_text())
    config=json.loads((out/'config.json').read_text());limits=Limits(**config['eval_limits'])
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());oracles={}
    for r in manifest:
        if r['split']!='test_pairs':continue
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        oracles[m.case_id]=Oracle.build(m)
    all_pairs=[GoalPair(oracles[r['first']],oracles[r['second']],r['mixed'])
        for r in json.loads((out/'pairs.json').read_text()) if r['first'] in oracles]
    for rep in range(3):
        pairs=[p for p in all_pairs if f'/r{rep}/' in p.first.maze.case_id]
        for pressure in ('transmission','goal'):
            saved=champions[f'goal/evolved/{pressure}/{rep}']
            for label in ('goal','transmission'):
                arm=f'evolved/{pressure}/{label}'
                item=saved['archives'][label]['individual']
                organism=Organism(Genome.from_dict(item['genome']),'evolved',limits,ablate_nonlocal=True)
                for pair in pairs:
                    current=[];masks=[];removed=[]
                    for oracle in pair.cases:
                        m=oracle.maze;r=organism.react(m.cells,m.w,m.h,m.start,m.goal)
                        a=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],True)
                        b=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],False)
                        row=output_row(arm,rep,oracle,r,assess(r,oracle));row['signal']=signal_metrics(a,b,oracle,config['horizon'])
                        masks.append((a.state[2]>0).astype(np.uint8));removed.append((b.state[2]>0).astype(np.uint8))
                        row['probe_mask']=np.packbits(masks[-1],bitorder='little').tobytes().hex()
                        row['source_removed_mask']=np.packbits(removed[-1],bitorder='little').tobytes().hex()
                        work+=r.dispatches+r.spatial_reads+a.dispatches+a.reads+b.dispatches+b.reads
                        current.append(row)
                    metrics=goal_metrics(masks,removed,pair)
                    if not all(r['signal']['aligned'] for r in current):
                        for g in metrics:g['score']=0.;g['pair_both']=False
                    for r,g in zip(current,metrics):r['goal']=g;rows.append(r)
    with gzip.open(out/'nonlocal_ablation.jsonl.gz','wt',compresslevel=9) as f:
        for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
    result=dict(elapsed_seconds=time.perf_counter()-started,charged_work=work,normal_responses=len(rows),
                developmental_probes=2*len(rows),ablation='Every radius>1 read returns zero; attempted reads remain charged')
    write_json(out/'diagnostics.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/goal_conditioning')
    diagnose(parser.parse_args().out)
