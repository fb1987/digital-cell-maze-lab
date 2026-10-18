"""Exploratory validation-only goal-to-source timecourse after final inspection.

No genome, selection score or training parameter is changed. All eight state
channels are included so concentration changes in output/stop are not missed.
"""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle
from .experiment import write_json
from .regulatory import Genome
from .regulatory_runtime import Organism
from .runtime import Limits
from .signal_probe import observe


def diagnose(out):
    out=Path(out);started=time.perf_counter();work=0;rows=[]
    champions=json.loads((out/'champions.json').read_text());config=json.loads((out/'config.json').read_text())
    frozen=hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());oracles={}
    for r in manifest:
        if r['split']!='validation_goal':continue
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        oracles[m.case_id]=Oracle.build(m)
    pairs=[p for p in json.loads((out/'pairs.json').read_text()) if p['first'] in oracles and not p['mixed']]
    for saved in champions.values():
        c=saved['config'];item=saved['archives']['goal']['individual']
        organism=Organism(Genome.from_dict(item['genome']),c['topology'],Limits(**config['eval_limits']))
        for pair in pairs:
            if f"/r{c['replicate']}/" not in pair['first']:continue
            first,second=[oracles[pair[k]] for k in ('first','second')]
            for horizon in (8,16,32,64):
                m=first.maze;a=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
                m=second.maze;b=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
                work+=a.dispatches+a.reads+b.dispatches+b.reads
                changed=a.state[:,m.start]!=b.state[:,m.start];aligned=a.steps==b.steps==horizon
                rows.append(dict(arm=f"{c['topology']}/{c['pressure']}/goal",replicate=c['replicate'],
                    first=pair['first'],second=pair['second'],horizon=horizon,aligned=aligned,
                    source_goal_distances=[len(first.path)-1,len(second.path)-1],
                    changed_channels=np.flatnonzero(changed).tolist(),any_source_state=bool(np.any(changed)),
                    hidden_source_state=bool(np.any(changed[[0,1,3,4,5,6]])),output_source_state=bool(changed[2]),
                    stop_source_state=bool(changed[7]),steps=[a.steps,b.steps]))
                del a,b
    assert frozen==hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    result=dict(scope='Exploratory after primary final inspection; validation pairs only; no model selection or retuning',
        elapsed_seconds=time.perf_counter()-started,charged_work=work,probe_runs=2*len(rows),
        champions_sha256=frozen,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows)
    write_json(out/'validation_timecourse.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/factor_curriculum');diagnose(parser.parse_args().out)
