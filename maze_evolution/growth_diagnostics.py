"""Post-freeze V11 pulse removal, range ablation and goal-information timecourse.

All selected task/choice and frozen counterparts are fixed before these assays.
The timecourse uses the independent paired final set, not additional selection.
"""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from .growth_runtime import Organism
from .beacon_probe import observe
from .beacon_fitness import evaluate
from .growth_study import selections
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair
from .goal_fitness import goal_metrics
from .junction_fitness import junction_metrics,unpack,decision
from .range_study import output_row
from .growth import Individual
from .runtime import Limits
from .signal_fitness import signal_metrics
from .signal_audit import lines
from .junction_fitness import evaluate as junction_evaluate


def choice_intervention(item,pair,topology,limits,horizon,pulse=True,ablate=False):
    organism=Organism(item.genome,topology,limits,goal_pulse=pulse,ablate_nonlocal=ablate)
    rows=[];masks=[];removed=[];work=0
    for oracle in pair.cases:
        m=oracle.maze;r=organism.react(m.cells,m.w,m.h,m.start,m.goal);assessment=assess(r,oracle)
        a=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True)
        b=observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,False)
        masks.append((a.state[2]>0).astype(np.uint8));removed.append((b.state[2]>0).astype(np.uint8))
        rows.append(dict(case=m.case_id,status=r.status,steps=r.steps,valid=assessment.valid_path,optimal=assessment.optimal,
            no_path=assessment.no_path_correct,partial=assessment.partial,failure=assessment.failure,
            reads=r.range_reads,dispatches=r.dispatches,active=r.active_instructions,
            mask=np.packbits(r.mask,bitorder='little').tobytes().hex(),signal=signal_metrics(a,b,oracle,horizon),
            probe_mask=np.packbits(masks[-1],bitorder='little').tobytes().hex(),source_removed_mask=np.packbits(removed[-1],bitorder='little').tobytes().hex()))
        work+=r.dispatches+r.spatial_reads+a.dispatches+a.reads+b.dispatches+b.reads
    metrics=junction_metrics(masks,removed,pair,aligned=all(r['signal']['aligned'] for r in rows))
    for row,metric in zip(rows,metrics):row['junction']=metric
    return dict(goal_pulse=pulse,ablate_nonlocal=ablate,cases=rows,work=work,
        junction=min(r['score'] for r in metrics),junction_both=float(metrics[0]['pair_both']))


def validation_ancestry(out,config):
    """Preserve strict-choice variants by validation only; never change final selections.

    Planned during V11 training; these post-freeze assays do not affect final selections.
    Replay the first qualifying validation pair in each best strict archive.
    """
    started=time.perf_counter();root=Path(__file__).resolve().parents[1]
    best={}
    for path in sorted((out/'logs').glob('*/*.evaluations.jsonl.gz')):
        for r in lines(path):
            if r['split']!='validation':continue
            rank=[r['junction_both'],r['junction'],r['balanced'],r['goal'],*r['normal_fitness'][:2]]
            if r['condition'] not in best or rank>best[r['condition']]['rank']:
                best[r['condition']]=dict(rank=rank,id=r['id'],generation=r['generation'],cases=r['cases'])
    # Keep only ancestry metadata, then load the few required genomes in a second
    # streaming pass; retaining every128-gene genome would waste hundreds of MiB.
    parents={}
    for path in sorted((out/'logs').glob('*/*.genomes.jsonl.gz')):
        for item in lines(path):parents[item['id']]=(item['parent'],item['birth'])
    needed={r['id'] for r in best.values()}
    for r in best.values():
        if r['rank'][0]<=0:continue
        identity=r['id'];depth=0
        while identity in parents:
            needed.add(identity);parent,birth=parents[identity]
            if birth==0:break
            identity=parent;depth+=1
            if depth>256:raise RuntimeError('Diagnostic ancestry ceiling')
    known={}
    for path in sorted((out/'logs').glob('*/*.genomes.jsonl.gz')):
        for item in lines(path):
            if item['id'] in needed:known[item['id']]=item
    all_oracles={}
    for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read()):
        if r['split']!='validation_goal':continue
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        all_oracles[m.case_id]=Oracle.build(m)
    saved_records={};records=[];work=responses=0
    for key,r in best.items():
        saved_records[key]={k:v for k,v in r.items() if k!='cases'}
        saved_records[key]['individual']=known[r['id']]
        if r['rank'][0]<=0:continue
        a,b=next((a,b) for a,b in zip(r['cases'][::2],r['cases'][1::2]) if a['junction']['pair_both'])
        pair=GoalPair(all_oracles[a['case']],all_oracles[b['case']]);chain=[];item=known[r['id']]
        while True:
            chain.append(item)
            if item['birth']==0 or item['parent'] not in known:break
            item=known[item['parent']]
            if len(chain)>256:raise RuntimeError('Diagnostic ancestry ceiling')
        chain.reverse();nodes=[];previous=None;topology=key.split('/')[1]
        for item in chain:
            ev=junction_evaluate(Individual.load(item),[pair],topology,Limits(**config['eval_limits']),'balanced',config['horizon'])
            work+=ev.work;responses+=2
            genes=item['genome']['genes']
            edits=[] if previous is None else [dict(index=i,before=previous[i] if i<len(previous) else None,
                after=genes[i] if i<len(genes) else None) for i in range(max(len(previous),len(genes)))
                if (previous[i] if i<len(previous) else None)!=(genes[i] if i<len(genes) else None)]
            nodes.append(dict(individual=item,junction=ev.junction,strict_both=ev.junction_both,
                normal_fitness=ev.normal_fitness,work=ev.work,cases=ev.rows,gene_row_changes=edits));previous=genes
        assert nodes[-1]['strict_both']==1.
        interventions=[]
        for pulse,ablate in ((False,False),(True,True)):
            if ablate and topology!='evolved':continue
            result=choice_intervention(Individual.load(chain[-1]),pair,topology,Limits(**config['eval_limits']),config['horizon'],pulse,ablate)
            work+=result['work'];responses+=2;interventions.append(result)
        records.append(dict(condition=key,first=pair.first.maze.case_id,second=pair.second.maze.case_id,
            decision=decision(pair),nodes=nodes,interventions=interventions))
    write_json(out/'strict_validation_archive.json',dict(scope='Replay copy of the preregistered primary strict-choice validation archive; no new selection or training',records=saved_records))
    with gzip.open(out/'choice_ancestry.json.gz','wt',compresslevel=9) as f:json.dump(records,f,separators=(',',':'))
    return dict(ancestry_seconds=time.perf_counter()-started,ancestry_work=work,ancestry_responses=responses,ancestry_probes=2*responses)



def phase_assays(out,champions,config):
    """Fixed boundary leaders: secondary transfer and reused-training replay."""
    oracles={}
    for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read()):
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        oracles[m.case_id]=Oracle.build(m)
    pairs=[GoalPair(oracles[r['first']],oracles[r['second']],r['mixed'])
        for r in json.loads((out/'pairs.json').read_text())]
    rows=[];training=[];work=responses=0;started=time.perf_counter()
    by_first={p.first.maze.case_id:p for p in pairs}
    from .growth_fitness import evaluate as phase_evaluate
    for condition,saved in champions.items():
        c=saved['config'];rep=c['replicate']
        for generation,record in saved['phase_leaders'].items():
            item=Individual.load(record['individual'])
            for split in ('validation_goal','test_pairs'):
                selected=[p for p in pairs if p.first.maze.split==split and f'/r{rep}/' in p.first.maze.case_id]
                ev=phase_evaluate(item,selected,c['topology'],Limits(**config['eval_limits']),'choice',config['horizon'],c['gene_limit'])
                rows.append(dict(condition=condition,generation=int(generation),id=item.identity,split=split,
                    strict_pairs=ev.strict_pairs,selection_credit=ev.selection_credit,choice_families=ev.choice_families,
                    normal_fitness=ev.normal_fitness,junction=ev.junction,junction_both=ev.junction_both,
                    junction_families=ev.junction_families,work=ev.work,cases=ev.rows))
                work+=ev.work;responses+=len(ev.rows)
            selected=[by_first[case] for case in record['cases']]
            for label,model in (('phase_leader',item),('frozen_choice',Individual.load(saved['frozen']['choice']['individual'])),
                                ('final_choice',Individual.load(saved['archives']['choice']['individual']))):
                ev=phase_evaluate(model,selected,c['topology'],Limits(**config['train_limits']),'choice',config['horizon'],c['gene_limit'])
                training.append(dict(condition=condition,generation=int(generation),id=model.identity,selection=label,
                    strict_pairs=ev.strict_pairs,selection_credit=ev.selection_credit,choice_families=ev.choice_families,
                    fitness=ev.fitness,smooth_fitness=ev.smooth_fitness,case_values=ev.case_values,normal_fitness=ev.normal_fitness,
                    junction=ev.junction,junction_both=ev.junction_both,junction_families=ev.junction_families,work=ev.work,cases=ev.rows))
                work+=ev.work;responses+=len(ev.rows)
    for name,records in (('phase_transfer',rows),('phase_training_control',training)):
        with gzip.open(out/(name+'.jsonl.gz'),'wt',compresslevel=9) as f:
            for r in records:f.write(json.dumps(r,separators=(',',':'))+'\n')
    return dict(phase_seconds=time.perf_counter()-started,phase_work=work,phase_responses=responses,phase_probes=2*responses,
        phase_transfer_responses=sum(len(r['cases']) for r in rows),phase_training_responses=sum(len(r['cases']) for r in training))


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
    opportunities=[]
    for pair in pairs:
        if pair.mixed:continue
        label=decision(pair);region=[label['vertex']]+label['exits']
        minima=[min(o.to_goal[v] for v in region) for o in pair.cases]
        opportunities.append(dict(first=pair.first.maze.case_id,decision=label,
            goal_to_decision_region=minima,goal_to_vertex=[o.to_goal[label['vertex']] for o in pair.cases],
            local_goal_inputs_both_outside_16_cones=all(d>config['horizon'] for d in minima),
            scope='Post-freeze structural diagnostic: radius1 influence propagates at most one open edge per tick; identical local decision bits cannot make disjoint strict choices. No selection.'))
    write_json(out/'opportunity_diagnostics.json',opportunities)
    cross=[];ablations=[];timecourse=[];cross_work=ablation_work=timecourse_work=0
    for rep in range(3):
        selected=[p for p in pairs if f'/r{rep}/' in p.first.maze.case_id]
        _,items=selections(champions,rep,limits)
        for arm,(item,topology,mode) in items.items():
            swapped='flag'
            ev=evaluate(item,selected,topology,limits,swapped,config['horizon'])
            minima=[];both=[]
            for j,pair in enumerate(selected):
                rows=ev.rows[2*j:2*j+2];n=len(pair.first.maze.cells)
                metrics=junction_metrics([unpack(r,'probe_mask',n) for r in rows],
                    [unpack(r,'source_removed_mask',n) for r in rows],pair,
                    aligned=all(r['signal']['aligned'] for r in rows))
                for row,metric in zip(rows,metrics):row['junction']=metric
                if not pair.mixed:minima.append(min(r['score'] for r in metrics));both.append(metrics[0]['pair_both'])
            cross.append(dict(junction=float(np.mean(minima)),junction_both=float(np.mean(both)),arm=arm+'->'+swapped,original_arm=arm,input_mode=swapped,replicate=rep,id=item.identity,
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
                    label=decision(pair);v=label['vertex']
                    timecourse.append(dict(junction_exits=label['exits'],junction_exit_states=[a.state[2,label['exits']].tolist(),b.state[2,label['exits']].tolist()],
                        junction_vertex=v,junction_states=[a.state[:,v].tolist(),b.state[:,v].tolist()],
                        junction_changed_channels=np.flatnonzero(a.state[:,v]!=b.state[:,v]).tolist(),arm=arm,replicate=rep,first=first.maze.case_id,second=second.maze.case_id,
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
                choices=junction_metrics(masks,removed,pair,aligned=all(r['signal']['aligned'] for r in current))
                for r,g,j in zip(current,metrics,choices):r['goal']=g;r['junction']=j;ablations.append(r)
    for name,rows in (('cross_input',cross),('nonlocal_ablation',ablations)):
        with gzip.open(out/(name+'.jsonl.gz'),'wt',compresslevel=9) as f:
            for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
    write_json(out/'goal_timecourse.json',timecourse)
    ancestry=validation_ancestry(out,config)
    phase=phase_assays(out,champions,config)
    assert frozen==hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()
    cross_responses=sum(len(r['cases']) for r in cross)
    result=dict(scope='Post-freeze diagnostics on paired final layouts; no training or model selection',
        elapsed_seconds=time.perf_counter()-started,charged_work=cross_work+ablation_work+timecourse_work+ancestry['ancestry_work']+phase['phase_work'],**ancestry,**phase,
        cross_input_work=cross_work,cross_input_responses=cross_responses,cross_input_probes=2*cross_responses,
        ablation_work=ablation_work,ablation_responses=len(ablations),ablation_probes=2*len(ablations),
        timecourse_work=timecourse_work,timecourse_probes=2*len(timecourse),
        champions_sha256=frozen,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        ablation='All radius>1 reads return zero; attempted reads remain charged')
    write_json(out/'diagnostics.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/capacity_growth');diagnose(parser.parse_args().out)
