"""Post-hoc V9 selection counterfactual on saved training pools; no inference."""
import argparse,copy,gzip,hashlib,json,random,time
from pathlib import Path
from types import SimpleNamespace
from .choice_fitness import lexicase
from .signal_audit import lines
from .experiment import write_json
from .regulatory import Genome


def diagnose(out):
    started=time.perf_counter();out=Path(out);target=out/'selection_counterfactual.json'
    if target.exists():raise FileExistsError('Diagnostic already exists')
    groups={};source_files={}
    for p in sorted((out/'logs').glob('*/*_prefix_*.evaluations.jsonl.gz')):
        source_files[str(p.relative_to(out))]=hashlib.sha256(p.read_bytes()).hexdigest()
        for r in lines(p):
            if r['split']=='train':groups.setdefault((r['condition'],r['generation']),[]).append(r)
    # Drop inactive pools before retaining case rasters/metrics unnecessarily.
    active={k:v for k,v in groups.items() if any(r['strict_pairs'] for r in v)}
    needed={r['id'] for pool in active.values() for r in pool};digests={}
    del groups
    for p in sorted((out/'logs').glob('*/*_prefix_*.genomes.jsonl.gz')):
        source_files[str(p.relative_to(out))]=hashlib.sha256(p.read_bytes()).hexdigest()
        for r in lines(p):
            if r['id'] in needed:digests[r['id']]=Genome.from_dict(r['genome']).digest
    records=[];draws=changed=changed_genotype=top_changed=0
    for (condition,generation),pool in sorted(active.items()):
        before=[];after=[]
        for r in pool:
            values=r['case_values'];choice=[(a,b,int(row['junction']['pair_both']),score) for (a,b,_,score),row in zip(values,r['cases'])]
            before.append((SimpleNamespace(case_values=values),r['id']))
            after.append((SimpleNamespace(case_values=choice),r['id']))
        prefix_top=max(tuple(r['smooth_fitness']) for r in pool)
        choice_top=max(tuple(r['smooth_fitness'][:3]+[r['strict_pairs']]+r['smooth_fitness'][3:]) for r in pool)
        left={r['id'] for r in pool if tuple(r['smooth_fitness'])==prefix_top}
        right={r['id'] for r in pool if tuple(r['smooth_fitness'][:3]+[r['strict_pairs']]+r['smooth_fitness'][3:])==choice_top}
        top_changed+=left!=right
        pairs=[]
        for seed in range(128):
            a=lexicase(random.Random(1139000+seed),before);b=lexicase(random.Random(1139000+seed),after)
            pairs.append(dict(seed=1139000+seed,prefix=a,choice=b,same_genotype=digests[a]==digests[b]))
        differences=sum(r['prefix']!=r['choice'] for r in pairs);different_genotypes=sum(not r['same_genotype'] for r in pairs)
        draws+=len(pairs);changed+=differences;changed_genotype+=different_genotypes
        # For each case considered FIRST, separate route filtering from strict filtering.
        cases=[]
        for i in range(len(pool[0]['cases'])):
            survivors=list(pool)
            for field in (0,1):
                best=max(r['case_values'][i][field] for r in survivors)
                survivors=[r for r in survivors if r['case_values'][i][field]==best]
            positives=[r for r in survivors if r['cases'][i]['junction']['pair_both']]
            oldbest=max(r['case_values'][i][3] for r in survivors)
            oldsurvive={r['id'] for r in survivors if r['case_values'][i][3]>=oldbest-.02}
            if positives:
                newbest=max(r['case_values'][i][3] for r in positives)
                newsurvive={r['id'] for r in positives if r['case_values'][i][3]>=newbest-.02}
            else:newsurvive=oldsurvive
            cases.append(dict(case=pool[0]['cases'][i]['case'],route_survivors=len(survivors),strict_surviving_routes=len(positives),
                same_first_case_survivor_set=oldsurvive==newsurvive))
        records.append(dict(condition=condition,generation=generation,strict_pair_responses=sum(r['strict_pairs'] for r in pool),
            prefix_top=sorted(left),choice_top=sorted(right),same_global_top_set=left==right,
            draws=len(pairs),changed_parent_ids=differences,changed_parent_genotypes=different_genotypes,cases=cases,draws_detail=pairs))
    result=dict(scope='Post-hoc counterfactual on observed V9 Prefix training populations with K>0; identical pools are independently verified across pressures.128 matched-seed parent draws/pool, no new candidate inference or training. Not an estimate over unseen genotype populations.',
        active_pools=len(active),draws=draws,changed_parent_ids=changed,changed_parent_genotypes=changed_genotype,
        changed_global_top_sets=top_changed,analysis_seeds='1139000..1139127; selection only, no maze generation',records=records,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=source_files,
        elapsed_seconds=time.perf_counter()-started)
    write_json(target,result);print(json.dumps({k:v for k,v in result.items() if k not in ('records','input_sha256')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/choice_priority');diagnose(parser.parse_args().out)
