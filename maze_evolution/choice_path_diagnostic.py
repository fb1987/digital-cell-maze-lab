"""Post-hoc V9 inherited-path assay; no training, selection or new holdout claim."""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from .signal_audit import lines
from .evaluator import Maze,Oracle,assess
from .beacon_runtime import Organism
from .beacon_probe import observe
from .regulatory_search import Individual
from .runtime import Limits
from .range_study import output_row
from .experiment import write_json


def diagnose(out):
    started=time.perf_counter();out=Path(out)
    target=out/'inherited_path_diagnostic.json'
    if target.exists():raise FileExistsError('Diagnostic already exists')
    frozen=hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    config=json.loads((out/'config.json').read_text());champions=json.loads((out/'champions.json').read_text())
    record=next((r for r in lines(out/'holdout.jsonl.gz') if r['arm']=='local/choice/frozen_task' and r['optimal'] and r['edges']>=8),None)
    if record is None:
        write_json(target,dict(scope='Post-hoc inspected-final diagnostic; no qualifying inherited long local success',elapsed_seconds=time.perf_counter()-started));return
    saved=next(r for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read()) if r['case_id']==record['case_id'])
    m=Maze(bytes.fromhex(saved['cells_hex']),saved['w'],saved['h'],saved['start'],saved['goal'],saved['family'],saved['seed'],saved['split'],saved['case_id'])
    original=Oracle.build(m);alternate_goal=original.path[len(original.path)//2]
    altered=Oracle.build(Maze(m.cells,m.w,m.h,m.start,alternate_goal,m.family,m.seed,'diagnostic',m.case_id+'/midpoint_goal'))
    selected=champions[f"choice/local/choice/{record['replicate']}"]
    item=Individual.load(selected['frozen']['task']['individual']);current=Individual.load(selected['archives']['task']['individual'])
    organism=Organism(item.genome,'local',Limits(**config['eval_limits']),goal_pulse=True)
    ordinary=[];work=0
    for oracle in (original,altered):
        mm=oracle.maze;r=organism.react(mm.cells,mm.w,mm.h,mm.start,mm.goal)
        ordinary.append(output_row('frozen_inherited_diagnostic',record['replicate'],oracle,r,assess(r,oracle)))
        work+=r.dispatches+r.spatial_reads
    assert ordinary[0]['mask']==record['mask'] and ordinary[0]['status']==record['status'] and ordinary[0]['steps']==record['steps']
    horizon=min(64,record['steps']);snapshots=[]
    for tick in range(1,horizon+1):
        states=[]
        for oracle in (original,altered):
            mm=oracle.maze;o=observe(organism,mm.cells,mm.w,mm.h,mm.start,mm.goal,tick,True)
            states.append(o);work+=o.dispatches+o.reads
        a,b=states
        snapshots.append(dict(tick=tick,aligned=a.steps==b.steps==tick,
            output_states=[a.state[2].tolist(),b.state[2].tolist()],
            stop_states=[a.state[7].tolist(),b.state[7].tolist()],
            changed_sites_by_channel=np.sum(a.state!=b.state,axis=1).tolist(),
            source_states=[a.state[:,m.start].tolist(),b.state[:,m.start].tolist()]))
    aligned=all(r['aligned'] for r in snapshots)
    equal_binary=aligned and all(np.array_equal(np.asarray(r['output_states'][0])>0,np.asarray(r['output_states'][1])>0) for r in snapshots)
    equal_output=aligned and all(r['output_states'][0]==r['output_states'][1] for r in snapshots)
    result=dict(scope='Post-hoc diagnostic on the first inspected inherited local success at distance>=8. Midpoint target reuses that final layout; not an independent holdout. No genome edits or reselection.',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),champions_sha256=frozen,
        case=saved,individual=item.save(),current_task_same_genotype=item.genome.digest==current.genome.digest,
        original_oracle_path=list(original.path),alternate_goal=alternate_goal,ordinary=ordinary,
        horizon=horizon,truncated=record['steps']>64,every_probe_aligned=aligned,
        output_binary_identical=equal_binary,output_concentrations_identical=equal_output,
        source_state_identical=aligned and all(r['source_states'][0]==r['source_states'][1] for r in snapshots),
        snapshots=snapshots,normal_responses=2,probes=2*horizon,charged_work=work,elapsed_seconds=time.perf_counter()-started)
    assert frozen==hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    write_json(target,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('snapshots','individual','case','original_oracle_path')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/choice_priority');diagnose(parser.parse_args().out)
