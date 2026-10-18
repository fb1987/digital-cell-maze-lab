"""Post-freeze V7 pulse removal, range ablation and goal-information timecourse.

All selected task/balanced and frozen counterparts are fixed before these assays.
The timecourse uses the independent paired final set, not additional selection.
"""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from .beacon_runtime import Organism
from .beacon_probe import observe
from .beacon_fitness import evaluate
from .balance_study import selections
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair
from .goal_fitness import goal_metrics
from .range_study import output_row
from .regulatory_search import Individual
from .runtime import Limits
from .signal_fitness import signal_metrics


def diagnose(out):
    out=Path(out);started=time.perf_counter();champions=json.loads((out/'champions.json').read_text())
    frozen=hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    config=json.loads((out/'config.json').read_text());limits=Limits(**config['eval_limits'])
    oracles={}
    for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read()):
        if r['split']!='test_pairs':continue
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        oracles[m.case_id]=Oracle.build(m)
    pairs=[GoalPair(oracles[r['first']],oracles[r['second']],r['mixed'])
        for r in json.loads((out/'pairs.json').read_text()) if r['first'] in oracles]
    cross=[];ablations=[];timecourse=[];cross_work=ablation_work=timecourse_work=0
    for rep in range(3):
        selected=[p for p in pairs if f'/r{rep}/' in p.first.maze.case_id]
        _,items=selections(champions,rep,limits)
        for arm,(item,topology,mode) in items.items():
            swapped='flag'
            ev=evaluate(item,selected,topology,limits,swapped,config['horizon'])
            cross.append(dict(arm=arm+'->'+swapped,original_arm=arm,input_mode=swapped,replicate=rep,id=item.identity,
                goal=ev.goal_score,signal=ev.long_signal,quality=ev.goal_quality,specificity=ev.goal_specificity,
                both=ev.pair_both,balanced=float(np.mean([min(ev.rows[2*j+i]['goal']['score'] for i in (0,1)) for j,p in enumerate(selected) if not p.mixed])),work=ev.work,inference_work=ev.inference_work,probe_work=ev.probe_work,cases=ev.rows))
            cross_work+=ev.work
            organism=Organism(item.genome,topology,limits,goal_pulse=True)
            for pair in selected:
                if pair.mixed:continue
                first,second=pair.cases
                for horizon in (8,16,32,64):
                    observations=[]
                    for oracle in pair.cases:
                        m=oracle.maze;o=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
                        observations.append(o);timecourse_work+=o.dispatches+o.reads
                    a,b=observations;m=first.maze;changed=a.state[:,m.start]!=b.state[:,m.start]
                    aligned=a.steps==b.steps==horizon
                    distal=(np.asarray(first.to_goal)>=2)&(np.asarray(second.to_goal)>=2)
                    hidden=np.any(a.state[[0,1,3,4,5,6]]!=b.state[[0,1,3,4,5,6]],axis=0)
                    timecourse.append(dict(arm=arm,replicate=rep,first=first.maze.case_id,second=second.maze.case_id,
                        horizon=horizon,aligned=aligned,source_goal_distances=[len(first.path)-1,len(second.path)-1],
                        source_states=[a.state[:,m.start].tolist(),b.state[:,m.start].tolist()],
                        changed_channels=np.flatnonzero(changed).tolist(),any_source_state=bool(np.any(changed)),
                        hidden_source_state=bool(np.any(changed[[0,1,3,4,5,6]])),output_source_state=bool(changed[2]),
                        stop_source_state=bool(changed[7]),steps=[a.steps,b.steps],
                        distal_sites=int(distal.sum()),distal_hidden_changes=int(np.sum(hidden&distal)),
                        distal_hidden_fraction=float(np.mean(hidden[distal])) if np.any(distal) and aligned else 0.,
                        probe_raster_changes=int(np.sum((a.state[2]>0)!=(b.state[2]>0)))))
                    del observations,a,b
            if topology!='evolved' or '/frozen_' in arm:continue
            organism=Organism(item.genome,topology,limits,ablate_nonlocal=True,goal_pulse=True)
            for pair in selected:
                current=[];masks=[];removed=[]
                for oracle in pair.cases:
                    m=oracle.maze;r=organism.react(m.cells,m.w,m.h,m.start,m.goal)
                    a=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],True)
                    b=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],False)
                    row=output_row(arm,rep,oracle,r,assess(r,oracle));row['signal']=signal_metrics(a,b,oracle,config['horizon'])
                    masks.append((a.state[2]>0).astype(np.uint8));removed.append((b.state[2]>0).astype(np.uint8))
                    row['probe_mask']=np.packbits(masks[-1],bitorder='little').tobytes().hex()
                    row['source_removed_mask']=np.packbits(removed[-1],bitorder='little').tobytes().hex()
                    ablation_work+=r.dispatches+r.spatial_reads+a.dispatches+a.reads+b.dispatches+b.reads
                    current.append(row);del a,b
                metrics=goal_metrics(masks,removed,pair)
                if not all(r['signal']['aligned'] for r in current):
                    for g in metrics:g['score']=0.;g['pair_both']=False
                for r,g in zip(current,metrics):r['goal']=g;ablations.append(r)
    for name,rows in (('cross_input',cross),('nonlocal_ablation',ablations)):
        with gzip.open(out/(name+'.jsonl.gz'),'wt',compresslevel=9) as f:
            for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
    write_json(out/'goal_timecourse.json',timecourse)
    assert frozen==hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    cross_responses=sum(len(r['cases']) for r in cross)
    result=dict(scope='Post-freeze diagnostics on paired final layouts; no training or model selection',
        elapsed_seconds=time.perf_counter()-started,charged_work=cross_work+ablation_work+timecourse_work,
        cross_input_work=cross_work,cross_input_responses=cross_responses,cross_input_probes=2*cross_responses,
        ablation_work=ablation_work,ablation_responses=len(ablations),ablation_probes=2*len(ablations),
        timecourse_work=timecourse_work,timecourse_probes=2*len(timecourse),
        champions_sha256=frozen,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        ablation='All radius>1 reads return zero; attempted reads remain charged')
    write_json(out/'diagnostics.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/balanced_goal');diagnose(parser.parse_args().out)
