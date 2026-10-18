"""Resolve goal dependence through the isolated successful stopping tick."""
import argparse,difflib,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from .evaluator import Maze
from .experiment import write_json
from .regulatory import Genome,NAMES
from .regulatory_runtime import Organism
from .runtime import Limits
from .signal_audit import lines
from .signal_probe import observe


def diagnose(out):
    out=Path(out);started=time.perf_counter();work=0
    prior=json.loads((out/'turned_path_diagnostic.json').read_text());config=json.loads((out/'config.json').read_text())
    pair=next(p for p in json.loads((out/'pairs.json').read_text()) if prior['case'] in (p['first'],p['second']))
    manifest={r['case_id']:r for r in json.loads(gzip.open(out/'mazes.json.gz','rt').read())}
    cases=[]
    for key in ('first','second'):
        r=manifest[pair[key]];cases.append(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal']))
    organism=Organism(Genome.from_dict(prior['individual']['genome']),prior['arm'].split('/')[0],Limits(**config['eval_limits']))
    stop_tick=next(r['goals'][0]['steps'] for r in reversed(prior['ancestry']) if r['id']==prior['individual']['id'])
    rows=[]
    for horizon in range(1,stop_tick+1):
        a,b=[observe(organism,m.cells,m.w,m.h,m.start,m.goal,horizon,True) for m in cases]
        work+=a.dispatches+a.reads+b.dispatches+b.reads
        rows.append(dict(horizon=horizon,aligned=a.steps==b.steps==horizon,all_state_equal=bool(np.array_equal(a.state,b.state))))
        del a,b
    transition=next((a,b) for a,b in zip(prior['ancestry'],prior['ancestry'][1:]) if not a['goals'][0]['optimal'] and b['goals'][0]['optimal'])
    wanted={r['id'] for r in transition};saved={}
    for p in sorted((out/'logs').glob('*/*.genomes.jsonl.gz')):
        for r in lines(p):
            if r['id'] in wanted:saved[r['id']]=r
    parent,child=[saved[r['id']] for r in transition]
    before=[tuple(r) for r in parent['genome']['genes']];after=[tuple(r) for r in child['genome']['genes']]
    edits=[]
    for kind,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if kind!='equal':edits.append(dict(kind=kind,parent_indices=[i,j],child_indices=[k,l],
            before=[dict(op=NAMES[r[0]],row=r) for r in before[i:j]],after=[dict(op=NAMES[r[0]],row=r) for r in after[k:l]]))
    result=dict(scope='Post-hoc existing-genome diagnosis only; no mutants selected or optimized on the inspected case',
        elapsed_seconds=time.perf_counter()-started,charged_work=work,probe_runs=2*len(rows),rows=rows,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),champions_sha256=prior['champions_sha256'],
        parent=parent,first_successful_child=child,edits=edits)
    write_json(out/'goal_prefix_diagnostic.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','parent','first_successful_child')},indent=2))
    print('All successful-prefix states match under the two goals:',all(r['aligned'] and r['all_state_equal'] for r in rows))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/factor_curriculum');diagnose(parser.parse_args().out)
