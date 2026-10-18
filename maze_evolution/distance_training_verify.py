"""Verify the post-hoc training primitive; isolate its two observed edits."""
import argparse,hashlib,json,time
from collections import deque
from pathlib import Path
import numpy as np
from cellular_maze_lab import neighbors
from .beacon_runtime import Organism
from .beacon_probe import observe
from .distance_fitness import decision,evaluate
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair
from .regulatory import Genome,Gene
from .regulatory_search import Individual
from .runtime import Reaction,Limits


def unpack(value,n):return np.unpackbits(np.frombuffer(bytes.fromhex(value),dtype=np.uint8),bitorder='little')[:n]


def verify(out):
    out=Path(out);started=time.perf_counter();root=Path(__file__).resolve().parents[1]
    d=json.loads((out/'training_choice_diagnostic.json').read_text())
    assert d['source_sha256']==hashlib.sha256((root/'maze_evolution/distance_training_diagnostic.py').read_bytes()).hexdigest()
    for path,h in d['input_sha256'].items():assert hashlib.sha256((out/path).read_bytes()).hexdigest()==h
    import gzip
    by_case={r['case_id']:r for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read())}
    config=json.loads((out/'config.json').read_text());limits=Limits(**config['train_limits']);champions=json.loads((out/'champions.json').read_text())
    work=counter_work=normals=rasters=0;interactions=[]
    for record in d['records']:
        assert champions[record['condition']]['config']['train_limits']==config['train_limits']
        def oracle(case):
            r=by_case[case];return Oracle.build(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id']))
        pair=GoalPair(oracle(record['first']),oracle(record['second']));label=decision(pair);assert label==record['decision']
        topology=record['condition'].split('/')[1];last=record['nodes'][-1]['individual'];parent=None
        for node in record['nodes']:
            item=Individual.load(node['individual'])
            if parent is not None:assert item.parent==parent
            parent=item.identity
        variants=[(n['individual'],n,True,False) for n in record['nodes']]+[(last,r,r['goal_pulse'],r['ablate_nonlocal']) for r in record['interventions']]
        for saved,recorded,pulse,ablate in variants:
            item=Individual.load(saved);organism=Organism(item.genome,topology,limits,goal_pulse=pulse,ablate_nonlocal=ablate);scores=[];strict=[];variant_work=0
            for o,row in zip(pair.cases,recorded['cases']):
                m=o.maze;n=len(m.cells);r=organism.react(m.cells,m.w,m.h,m.start,m.goal);a=assess(r,o)
                assert r.status==row['status'] and r.steps==row['steps'] and np.array_equal(r.mask,unpack(row['mask'],n))
                assert (a.valid_path,a.optimal,a.failure)==(row['valid'],row['optimal'],row['failure'])
                on=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],True)
                off=observe(organism,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],False)
                mask=unpack(row['probe_mask'],n);removed=unpack(row['source_removed_mask'],n)
                assert np.array_equal(on.state[2]>0,mask) and np.array_equal(off.state[2]>0,removed)
                aligned=on.steps==off.steps==config['horizon'];seen=set();queue=deque()
                if mask[m.start] and not any(mask[p] and not m.cells[p] for p in range(n)):seen.add(m.start);queue.append(m.start)
                while queue:
                    for q in neighbors(queue.popleft(),m.w,m.h):
                        if mask[q] and q not in seen:seen.add(q);queue.append(q)
                i=len(scores);want=set(label['allowed'][i]);wrong=set(label['exits'])-want;lit={p for p in want if mask[p]};bad={p for p in wrong if mask[p]}
                R=sum(p in seen and not removed[p] for p in label['prefix'][2:])/len(label['prefix'][2:])
                causal=sum(not removed[p] for p in lit)/max(1,len(lit))
                C=causal*(1-len(bad)/len(wrong))/len(lit) if lit and label['vertex'] in seen else 0.
                score=(.25*R+.75*C) if aligned else 0.;correct=bool(aligned and label['vertex'] in seen and len(lit)==1 and not bad and causal==1)
                assert abs(row['junction']['score']-score)<1e-12 and row['junction']['strict']==correct
                scores.append(score);strict.append(correct);rasters+=1;normals+=1
                variant_work+=r.dispatches+r.spatial_reads+on.dispatches+on.reads+off.dispatches+off.reads
            assert recorded['strict_both']==all(strict) and abs(recorded['junction']-min(scores))<1e-12
            assert variant_work==recorded['work'];work+=variant_work
        # Counterfactuals are reversions of the two actual row changes, not bred genomes.
        previous=record['nodes'][-2]['individual'];changes=record['nodes'][-1]['gene_row_changes'];results=[]
        assert len(changes)==2 and len(previous['genome']['genes'])==len(last['genome']['genes'])
        for indices in ((),(0,),(1,),(0,1)):
            genes=[Gene(*row) for row in previous['genome']['genes']]
            for i in indices:genes[changes[i]['index']]=Gene(*changes[i]['after'])
            ev=evaluate(Individual('diagnostic/'+str(indices),Genome(tuple(genes)),None,0),[pair],topology,limits,'choice',config['horizon'])
            counter_work+=ev.work
            results.append(dict(changed_rows=[changes[i]['index'] for i in indices],junction=ev.junction,strict_both=bool(ev.strict_pairs),work=ev.work,cases=ev.rows))
        assert results[0]['strict_both']==record['nodes'][-2]['strict_both'] and results[-1]['strict_both']
        interactions.append(dict(condition=record['condition'],first=pair.first.maze.case_id,changes=changes,results=results))
    assert work==d['charged_work'] and normals==d['normal_responses']
    write_json(out/'training_edit_interaction.json',dict(scope='Post-hoc reversions on the selected training pair only. Artificial diagnostic variants never breed; no generalization claim.',records=interactions))
    result=dict(all_checks_passed=True,elapsed_seconds=time.perf_counter()-started,replayed_normal_responses=normals,replayed_probes=2*normals,
        independent_junction_rasters=rasters,replayed_work=work,counterfactual_work=counter_work,counterfactual_normals=8*len(interactions),
        counterfactual_probes=16*len(interactions),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        diagnostic_sha256=hashlib.sha256((out/'training_choice_diagnostic.json').read_bytes()).hexdigest())
    write_json(out/'training_choice_verification.json',result);print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/distance_curriculum');verify(parser.parse_args().out)
