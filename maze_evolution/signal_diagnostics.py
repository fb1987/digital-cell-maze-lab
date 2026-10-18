"""Post-freeze validation diagnostics; no selection or final-test retuning."""
import argparse
import gzip
import json
from pathlib import Path
import time
import numpy as np
from .evaluator import Maze, Oracle, distances, assess
from .experiment import write_json
from .regulatory import Genome
from .regulatory_search import Individual
from .runtime import Limits
from .signal_audit import lines
from .signal_fitness import evaluate, signal_metrics
from .signal_probe import observe
from .regulatory_runtime import Organism
from .range_study import output_row


def run(out):
    out=Path(out); started=time.perf_counter()
    config=json.loads((out/'config.json').read_text())
    champions=json.loads((out/'champions.json').read_text())
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read())
    oracles={}
    for r in manifest:
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        oracles[m.case_id]=Oracle.build(m)
    # This is an interpretive ceiling, never a selection reward. Local rules cannot
    # carry source dependence farther than one graph edge per synchronous tick.
    cone=[]
    for r in lines(out/'signals.jsonl.gz'):
        if not r['arm'].startswith('local/') or r['edges']<8:
            continue
        oracle=oracles[r['case_id']]
        d=np.array(distances(oracle.maze,oracle.maze.start))
        ceiling=float(np.mean([np.mean(d[d>=k]<=config['horizon']) for k in (2,4,8) if np.any(d>=k)]))
        assert r['max_distance']<=config['horizon'],r
        assert r['score']<=ceiling+1e-10,(r,ceiling)
        cone.append(dict(arm=r['arm'],case_id=r['case_id'],score=r['score'],local_ceiling=ceiling,
                         fraction_of_local_ceiling=r['score']/ceiling if ceiling else 0.))
    ablations=[]; work=0
    for topology,rep in ((t,r) for t in ('local','evolved') for r in range(3)):
        saved=champions[f'signal/{topology}/causal/{rep}']['transmission']
        item=Individual.load(saved)
        validation=[o for o in oracles.values() if o.maze.split=='validation' and f'/r{rep}/' in o.maze.case_id]
        limits=Limits(**config['eval_limits'])
        base=evaluate(item,validation,topology,limits,'causal',config['horizon'])
        work+=base.work
        rows=[]
        for index in range(len(item.genome.genes)):
            genes=item.genome.genes[:index]+item.genome.genes[index+1:]
            if not genes: continue
            modified=Individual(f'analysis/r{rep}/delete{index}',Genome(genes),None,0)
            ev=evaluate(modified,validation,topology,limits,'causal',config['horizon'])
            work+=ev.work
            rows.append(dict(deleted=index,gene=item.genome.genes[index].row(),digest=modified.genome.digest,
                signal=ev.long_signal,delta=ev.long_signal-base.long_signal,work=ev.work))
        ceilings=[]
        for oracle in validation:
            if len(oracle.path)-1 < 8: continue
            d=np.array(distances(oracle.maze,oracle.maze.start))
            ceilings.append(float(np.mean([np.mean(d[d>=k]<=config['horizon']) for k in (2,4,8) if np.any(d>=k)])))
        ablations.append(dict(topology=topology,replicate=rep,id=item.identity,genes=len(item.genome.genes),
            validation_local_ceiling=float(np.mean(ceilings)) if ceilings else 0.,
            baseline_signal=base.long_signal,single_deletions_reducing_signal=sum(r['delta'] < -1e-9 for r in rows),
            single_deletions_improving_signal=sum(r['delta'] > 1e-9 for r in rows),deletions=rows))
        print(f'Validation gene ablations complete for {topology} causal replicate {rep}.',flush=True)
    nonlocal_rows=[]
    for rep in range(3):
        tests=[o for o in oracles.values() if o.maze.split=='test' and f'/r{rep}/' in o.maze.case_id]
        for pressure in ('current','causal'):
            selected=champions[f'signal/evolved/{pressure}/{rep}']
            for field,label in (('champion','task'),('transmission','transmission')):
                o=Organism(Genome.from_dict(selected[field]['genome']),'evolved',Limits(**config['eval_limits']),True)
                for oracle in tests:
                    m=oracle.maze
                    r=o.react(m.cells,m.w,m.h,m.start,m.goal)
                    row=output_row(f'evolved/{pressure}/{label}',rep,oracle,r,assess(r,oracle))
                    a=observe(o,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],True)
                    b=observe(o,m.cells,m.w,m.h,m.start,m.goal,config['horizon'],False)
                    row['signal']=signal_metrics(a,b,oracle,config['horizon'])
                    row['probe_work']=a.dispatches+a.reads+b.dispatches+b.reads
                    work+=row['probe_work']+r.dispatches+r.spatial_reads
                    nonlocal_rows.append(row)
                    del a,b
    with gzip.open(out/'nonlocal_ablation.jsonl.gz','wt',compresslevel=9) as f:
        for row in nonlocal_rows:
            f.write(json.dumps(row,separators=(',',':'))+'\n')
    result=dict(elapsed_seconds=time.perf_counter()-started,charged_work=work,
        caveat='Post-freeze diagnostics only. Single-gene dispensability does not imply joint removability. No genomes were replaced.',
        nonlocal_ablation_cases=len(nonlocal_rows),local_cone=cone,gene_ablations=ablations,
        local_causal_gene_ablations=[r for r in ablations if r['topology']=='local'],
        evolved_causal_gene_ablations=[r for r in ablations if r['topology']=='evolved'])
    write_json(out/'diagnostics.json',result)
    print(f'Diagnostics complete: {result["elapsed_seconds"]:.1f}s.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/source_pressure')
    run(parser.parse_args().out)
