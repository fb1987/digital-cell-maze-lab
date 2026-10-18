"""Post-freeze V4 provenance, saved-output and accounting verification."""
import argparse
from collections import Counter,defaultdict
import gzip,hashlib,json,math
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair,layout_hash,prior_manifests
from .goal_fitness import goal_metrics
from .regulatory import Genome
from .regulatory_search import Individual
from .runtime import Reaction
from .signal_audit import lines


def unpack(value,n):
    return np.unpackbits(np.frombuffer(bytes.fromhex(value),dtype=np.uint8),bitorder='little')[:n]


def audit(out):
    out=Path(out);root=Path(__file__).resolve().parents[1]
    env=json.loads((out/'environment.json').read_text())
    assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in env['source_sha256'].items())
    assert hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()==env['champions_sha256']
    if (out/'final_generation_repair.json').exists():
        repair=json.loads((out/'final_generation_repair.json').read_text())
        assert repair['frozen_champions_sha256']==env['champions_sha256'] and repair['training_unchanged']
        assert hashlib.sha256((root/'maze_evolution/goal_recovery.py').read_bytes()).hexdigest()==repair['source_sha256']
    packed_files=0
    if (out/'storage.json').exists():
        for r in json.loads((out/'storage.json').read_text())['files']:
            p=out/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['stored_sha256']
            digest=hashlib.sha256();size=0
            with gzip.open(p,'rb') as f:
                while chunk:=f.read(1<<20):digest.update(chunk);size+=len(chunk)
            assert digest.hexdigest()==r['decoded_sha256'] and size==r['decoded_bytes']
            packed_files+=1
    ancestors={};learned={}
    for p,h in json.loads((out/'forks.json').read_text()).items():
        assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h
        saved=json.loads((root/p).read_text());assert saved['config']['origin']=='random'
        for item in saved['population']+[saved['transmission']]:
            ancestors[item['id']]=Genome.from_dict(item['genome']).digest
        learned[(saved['config']['topology'],saved['config']['replicate'])]=Genome.from_dict(saved['transmission']['genome']).digest
    known=dict(ancestors);ancestry={};maximum_genes=0
    for p in sorted((out/'logs').glob('*/*.genomes.jsonl.gz')):
        for r in lines(p):
            item=Individual.load(r);assert item.identity not in known
            assert item.parent is None or item.parent in known
            if item.birth==0:assert item.parent in ancestors and item.genome.digest==ancestors[item.parent]
            known[item.identity]=item.genome.digest;ancestry[item.identity]=(item.parent,item.birth)
            maximum_genes=max(maximum_genes,len(item.genome.genes))
    assert maximum_genes<=128
    champions=json.loads((out/'champions.json').read_text());lineages=[]
    for key,saved in champions.items():
        c=saved['config'];p=out/'checkpoints'/(key.replace('/','_')+'.json');checkpoint=json.loads(p.read_text())
        assert len(checkpoint['population'])==96
        protected=Individual.load(checkpoint['protected'])
        assert protected.genome.digest==learned[(c['topology'],c['replicate'])]
        assert protected.identity in {i['id'] for i in checkpoint['population']}
        for source in ('archives','frozen'):
            for label,record in saved[source].items():
                item=Individual.load(record['individual']);assert known[item.identity]==item.genome.digest
                if source=='frozen':continue
                identity=item.identity;depth=0
                while True:
                    parent,birth=ancestry[identity]
                    if parent not in ancestry:break
                    depth+=1;identity=parent
                lineages.append(dict(condition=key,archive=label,id=item.identity,mutation_depth=depth,
                    root_id=identity,root_birth=birth,root_parent=parent,
                    root_type='checkpoint' if parent in ancestors else 'fresh_immigrant'))
    for t in ('local','evolved'):
        for rep in range(3):
            assert champions[f'goal/{t}/goal/{rep}']['initial_digests']==champions[f'goal/{t}/transmission/{rep}']['initial_digests']
    write_json(out/'lineage_audit.json',lineages)
    previous=prior_manifests(root)
    previous_layouts={hashlib.sha256(f"{r['w']},{r['h']}:".encode()+bytes.fromhex(r['cells_hex'])).hexdigest() for r in previous}
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());oracles={};layouts=defaultdict(list);digests=set()
    for r in manifest:
        m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
        assert m.digest==r['sha256'] and m.digest not in digests
        digests.add(m.digest);lh=layout_hash(m);assert lh not in previous_layouts
        layouts[lh].append(m.case_id);oracles[m.case_id]=Oracle.build(m)
    pairs={};pair_entries=json.loads((out/'pairs.json').read_text())
    for r in pair_entries:
        pair=GoalPair(oracles[r['first']],oracles[r['second']],r['mixed'])
        a,b=pair.cases;assert layout_hash(a.maze)==r['layout_sha256']
        assert set(layouts[r['layout_sha256']])=={r['first'],r['second']}
        assert len(a.path)-1>=8
        if pair.mixed:assert not b.path
        else:assert len(b.path)-1>=8 and a.to_goal[b.maze.goal]>=max(len(a.path)-1,len(b.path)-1)
        pairs[(r['first'],r['second'])]=pair
    for lh,ids in layouts.items():
        assert len({oracles[i].maze.split for i in ids})==1
        assert len(ids)==(1 if oracles[ids[0]].maze.split=='test_goal' else 2)
    def check_output(r,paired=False):
        oracle=oracles[r['case'] if paired else r['case_id']];mask=unpack(r['mask'],len(oracle.maze.cells))
        result=Reaction(mask,r['status'],r['steps'],0,0,0);a=assess(result,oracle)
        fields={'valid':'valid_path','optimal':'optimal','no_path':'no_path_correct','failure':'failure'} if paired else {k:k for k in ('reachable','valid_path','optimal','no_path_correct','path_length','oracle_length','failure')}
        assert all(r[k]==getattr(a,v) for k,v in fields.items()),(r,fields)
        assert abs(r['partial']-a.partial)<1e-9
    primary=paired_outputs=goal_checks=signal_checks=0
    for r in lines(out/'holdout.jsonl.gz'):
        assert oracles[r['case_id']].maze.split=='test_goal';check_output(r);primary+=1
    for r in lines(out/'paired_holdout.jsonl.gz'):
        if 'baseline' in r:check_output(r['baseline']);paired_outputs+=1;continue
        cases=r['cases'];scores=[]
        for a,b in zip(cases[::2],cases[1::2]):
            pair=pairs[(a['case'],b['case'])];assert pair.first.maze.split=='test_pairs'
            masks=[unpack(v['probe_mask'],len(pair.first.maze.cells)) for v in (a,b)]
            removed=[unpack(v['source_removed_mask'],len(pair.first.maze.cells)) for v in (a,b)]
            expected=goal_metrics(masks,removed,pair)
            if not(a['signal']['aligned'] and b['signal']['aligned']):
                for v in expected:v['score']=0.;v['pair_both']=False
            for actual,want in zip((a,b),expected):
                check_output(actual,True);paired_outputs+=1;goal_checks+=1;scores.append(want['score'])
                for k,v in want.items():
                    assert abs(actual['goal'][k]-v)<1e-9,(actual['case'],k)
        assert abs(r['goal']-np.mean(scores))<1e-9
    ablation_outputs=ablation_goals=0
    if (out/'nonlocal_ablation.jsonl.gz').exists():
        grouped=defaultdict(dict)
        for r in lines(out/'nonlocal_ablation.jsonl.gz'):
            check_output(r);ablation_outputs+=1
            grouped[(r['arm'],r['replicate'])][r['case_id']]=r
        for rows in grouped.values():
            for (first,second),pair in pairs.items():
                if first not in rows:continue
                a,b=rows[first],rows[second];n=len(pair.first.maze.cells)
                expected=goal_metrics([unpack(r['probe_mask'],n) for r in (a,b)],
                    [unpack(r['source_removed_mask'],n) for r in (a,b)],pair)
                if not(a['signal']['aligned'] and b['signal']['aligned']):
                    for r in expected:r['score']=0.;r['pair_both']=False
                for actual,want in zip((a,b),expected):
                    for k,v in want.items():assert abs(actual['goal'][k]-v)<1e-9
                    ablation_goals+=1
    costs=defaultdict(Counter);factors=defaultdict(Counter);evaluations=responses=work=0
    for p in sorted((out/'logs').glob('*/*.evaluations.jsonl.gz')):
        for r in lines(p):
            assert r['id'] in known and r['work']==r['inference_work']+r['probe_work']
            c=costs[r['condition']];c[r['split']+'_responses']+=len(r['cases'])
            c['inference_work']+=r['inference_work'];c['probe_work']+=r['probe_work']
            evaluations+=1;responses+=len(r['cases']);work+=r['work']
            partial=source=goal=0.;valid=optimal=no_path=0
            for case in r['cases']:
                oracle=oracles[case['case']];assert oracle.maze.split in ('train_goal','validation_goal')
                if oracle.path:
                    f=factors[r['condition']+'/'+r['split']];g=case['goal'];f['reachable_responses']+=1
                    for label,positive in (('nonempty',g['selected']>0),('connected_growth',g['component']>=3),
                        ('source_dependent_output',g['source_fraction']>0),('positive_quality',g['quality']>0),
                        ('positive_specificity',g['specificity']>0),('positive_goal_score',g['score']>0)):
                        f[label]+=int(positive)
                    for field in ('quality','specificity','score','source_fraction'):
                        f['sum_'+field]+=g[field];f['max_'+field]=max(f['max_'+field],g[field])
                s=case['signal'];expected=max(0.,float(np.mean(list(s['bands'].values())))-s['leakage']) if s['bands'] and s['aligned'] else 0.
                assert abs(expected-s['score'])<1e-9
                assert s['pair_array_bytes']<=80*len(oracle.maze.cells)+65536
                signal_checks+=1;partial+=case['partial'];source+=s['score'];goal+=case['goal']['score']
                valid+=case['valid'];optimal+=case['optimal']
                no_path+=case['no_path']-bool(oracle.path and case['status']=='no_path')
            weight=2 if r['condition'].split('/')[2]=='goal' else 0
            assert r['fitness'][:3]==[valid,optimal,no_path]
            assert abs(r['fitness'][3]-(round(partial,8)+source+weight*goal))<2e-8
    assert work==sum(v['work'] for v in champions.values())
    assert responses==sum(v['maze_evaluations'] for v in champions.values())
    result=dict(all_checks_passed=True,source_files=len(env['source_sha256']),verified_packed_files=packed_files,external_random_ancestors=len(ancestors),
        new_individuals=len(ancestry),max_genes=maximum_genes,unique_inputs=len(digests),unique_layouts=len(layouts),
        previous_layouts=len(previous_layouts),primary_test_layouts=sum(oracles[v[0]].maze.split=='test_goal' for v in layouts.values()),
        paired_final_layouts=sum(oracles[v[0]].maze.split=='test_pairs' for v in layouts.values()),
        reassessed_primary_outputs=primary,reassessed_paired_outputs=paired_outputs,raster_goal_checks=goal_checks,
        reassessed_ablation_outputs=ablation_outputs,ablation_goal_checks=ablation_goals,
        training_signal_arithmetic_checks=signal_checks,training_fitness_checks=evaluations,
        normal_maze_evaluations=responses,developmental_probe_runs=2*responses,charged_work=work,
        inference_work=sum(v['inference_work'] for v in costs.values()),probe_work=sum(v['probe_work'] for v in costs.values()))
    write_json(out/'training_cost.json',costs);write_json(out/'training_factors.json',factors)
    write_json(out/'verification.json',result)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/goal_conditioning')
    audit(parser.parse_args().out)
