"""Post-freeze integrity verification; never changes trained genomes or fitness."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from .evaluator import Maze, Oracle, assess
from .experiment import write_json
from .regulatory import Genome
from .regulatory_search import Individual
from .runtime import Reaction


def lines(path):
    with gzip.open(path,'rt') as f:
        for line in f:
            yield json.loads(line)


def audit(out):
    out=Path(out); root=Path(__file__).resolve().parents[1]
    environment=json.loads((out/'environment.json').read_text())
    source_checks={name:hashlib.sha256((root/name).read_bytes()).hexdigest()==value
                   for name,value in environment['source_sha256'].items()}
    assert all(source_checks.values()),source_checks
    assert hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()==environment['champions_sha256']
    forks=json.loads((out/'forks.json').read_text())
    ancestors={}
    for name,value in forks.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value
        checkpoint=json.loads((root/name).read_text())
        assert checkpoint['config']['origin']=='random'
        ancestors.update({v['id']:Genome.from_dict(v['genome']).digest for v in checkpoint['population']})
    known=dict(ancestors); ancestry={}; registry_count=0; maximum_genes=0
    for path in sorted((out/'logs').glob('*/*.genomes.jsonl.gz')):
        for row in lines(path):
            item=Individual.load(row)
            assert item.identity not in known
            assert item.parent is None or item.parent in known,(item.identity,item.parent)
            if item.birth==0:
                assert item.parent in ancestors and item.genome.digest==ancestors[item.parent]
            maximum_genes=max(maximum_genes,len(item.genome.genes))
            known[item.identity]=item.genome.digest
            ancestry[item.identity]=(item.parent,item.birth)
            registry_count+=1
    assert maximum_genes<=128
    champions=json.loads((out/'champions.json').read_text())
    for item in champions.values():
        for field in ('champion','frozen','transmission','frozen_transmission'):
            selected=Individual.load(item[field]); assert known[selected.identity]==selected.genome.digest
    lineages=[]
    for condition,saved in champions.items():
        for field in ('champion','transmission'):
            identity=saved[field]['id']; root_id=identity; depth=0
            while True:
                parent,birth=ancestry[root_id]
                if parent not in ancestry:
                    break
                depth+=1; root_id=parent
            lineages.append(dict(condition=condition,archive=field,id=identity,mutation_depth=depth,
                root_id=root_id,root_birth=birth,root_parent=parent,
                root_type='checkpoint' if parent in ancestors else 'fresh_immigrant'))
    write_json(out/'lineage_audit.json',lineages)
    for topology in ('local','evolved'):
        for rep in range(3):
            assert champions[f'signal/{topology}/current/{rep}']['initial_digests']==champions[f'signal/{topology}/causal/{rep}']['initial_digests']
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read())
    previous=json.loads((root/'results/first_evolution/mazes.json').read_text())
    previous+=json.loads(gzip.open(root/'results/range_and_regulation/mazes.json.gz','rt').read())
    previous_hashes={r['sha256'] for r in previous}
    owners={}; oracles={}
    for row in manifest:
        m=Maze(bytes.fromhex(row['cells_hex']),row['w'],row['h'],row['start'],row['goal'],
               row['family'],row['seed'],row['split'],row['case_id'])
        assert m.digest==row['sha256'] and m.digest not in previous_hashes
        split='train' if row['split'].startswith('train') else row['split']
        if m.digest in owners:
            assert split==owners[m.digest]=='train'
        owners[m.digest]=split
        oracles[m.case_id]=Oracle.build(m)
    checked=0; assessments=Counter()
    for row in lines(out/'holdout.jsonl.gz'):
        oracle=oracles[row['case_id']]; assert oracle.maze.split=='test'
        mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),dtype=np.uint8),bitorder='little')[:len(oracle.maze.cells)]
        result=Reaction(mask,row['status'],row['steps'],row['reads'],row['dispatches'],row['array_bytes'])
        a=assess(result,oracle)
        for field in ('reachable','valid_path','optimal','no_path_correct','path_length','oracle_length','failure'):
            assert getattr(a,field)==row[field],(row['arm'],row['case_id'],field)
        assert abs(a.partial-row['partial'])<1e-10
        assessments['optimal']+=a.optimal; checked+=1
    work=inference_work=probe_work=case_count=evaluations=0
    condition_cost=defaultdict(Counter)
    for path in sorted((out/'logs').glob('*/*.evaluations.jsonl.gz')):
        for row in lines(path):
            assert row['id'] in known
            assert row['work']==row['inference_work']+row['probe_work']
            work+=row['work']; inference_work+=row['inference_work']; probe_work+=row['probe_work']
            case_count+=len(row['cases']); evaluations+=1
            cc=condition_cost[row['condition']]
            cc[row['split']+'_responses']+=len(row['cases'])
            cc['inference_work']+=row['inference_work']; cc['probe_work']+=row['probe_work']
            for case in row['cases']:
                assert oracles[case['case']].maze.split!='test'
    signal_checks=0
    for row in lines(out/'signals.jsonl.gz'):
        expected=max(0.,float(np.mean(list(row['bands'].values())))-row['leakage']) if row['bands'] and row['aligned'] else 0.
        assert abs(expected-row['score'])<1e-10
        assert row['pair_array_bytes'] <= 80*len(oracles[row['case_id']].maze.cells)+65536
        signal_checks+=1
    write_json(out/'training_cost.json',condition_cost)
    ablation_checks=0
    if (out/'nonlocal_ablation.jsonl.gz').exists():
        for row in lines(out/'nonlocal_ablation.jsonl.gz'):
            oracle=oracles[row['case_id']]
            mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),dtype=np.uint8),bitorder='little')[:len(oracle.maze.cells)]
            a=assess(Reaction(mask,row['status'],row['steps'],row['reads'],row['dispatches'],row['array_bytes']),oracle)
            assert all(getattr(a,k)==row[k] for k in ('reachable','valid_path','optimal','no_path_correct','failure'))
            ablation_checks+=1
    assert work==sum(c['work'] for c in champions.values())
    assert case_count==sum(c['maze_evaluations'] for c in champions.values())
    result=dict(all_checks_passed=True,source_files=len(source_checks),external_random_ancestors=len(ancestors),
        new_individuals=registry_count,max_genes=maximum_genes,unique_manifest_hashes=len(owners),
        unique_test_hashes=sum(v=='test' for v in owners.values()),previous_hashes=len(previous_hashes),
        independently_reassessed_outputs=checked,independently_reassessed_ablation_outputs=ablation_checks,signal_arithmetic_checks=signal_checks,
        candidate_evaluations=evaluations,normal_maze_evaluations=case_count,
        developmental_probe_runs=2*case_count,charged_work=work,inference_work=inference_work,probe_work=probe_work)
    write_json(out/'verification.json',result)
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--out',default='results/source_pressure')
    audit(parser.parse_args().out)
