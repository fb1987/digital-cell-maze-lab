"""Post-freeze V5 provenance, saved-output and accounting verification."""
import argparse
from collections import Counter,defaultdict
import gzip,hashlib,json,math
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .goal_data import GoalPair,layout_hash
from .factor_data import prior_manifests
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
    for file,module in (('diagnostics.json','factor_diagnostics.py'),('validation_timecourse.json','factor_timecourse.py'),
                        ('turned_path_diagnostic.json','factor_lineage_diagnostic.py'),('goal_prefix_diagnostic.json','factor_prefix_diagnostic.py')):
        if (out/file).exists():
            diagnostic=json.loads((out/file).read_text())
            assert hashlib.sha256((root/'maze_evolution'/module).read_bytes()).hexdigest()==diagnostic['source_sha256']
            if 'champions_sha256' in diagnostic:assert diagnostic['champions_sha256']==env['champions_sha256']
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
        for item in saved['population']+[saved['protected'],saved['archives']['goal']['individual']]:
            ancestors[item['id']]=Genome.from_dict(item['genome']).digest
        learned[(saved['config']['topology'],saved['config']['replicate'])]={Genome.from_dict(i['genome']).digest for i in (saved['protected'],saved['archives']['goal']['individual'])}
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
        protected=[Individual.load(i) for i in checkpoint['protected']]
        assert {i.genome.digest for i in protected}==learned[(c['topology'],c['replicate'])]
        assert {i.identity for i in protected} <= {i['id'] for i in checkpoint['population']}
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
            assert champions[f'factor/{t}/curriculum/{rep}']['initial_digests']==champions[f'factor/{t}/product/{rep}']['initial_digests']
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
    primary=paired_outputs=goal_checks=signal_checks=0;probe_routes=[];saved_probes={}
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
                oracle=oracles[actual['case']]
                saved_probes[(r['arm'],r['replicate'],actual['case'])]=unpack(actual['probe_mask'],len(oracle.maze.cells))
                probe_result=Reaction(unpack(actual['probe_mask'],len(oracle.maze.cells)),'emitted',16,0,0,0)
                probe_assessment=assess(probe_result,oracle)
                probe_routes.append(dict(arm=r['arm'],replicate=r['replicate'],case=actual['case'],
                    reachable=bool(oracle.path),aligned=actual['goal']['aligned'],
                    probe_valid=probe_assessment.valid_path,probe_shortest=probe_assessment.optimal,
                    normal_valid=actual['valid'],normal_shortest=actual['optimal'],normal_status=actual['status'],
                    diagnostic='Tick16 raster assessed with assumed emitted status; no actual halt is asserted'))
                for k,v in want.items():
                    assert abs(actual['goal'][k]-v)<1e-9,(actual['case'],k)
        assert abs(r['goal']-np.mean(scores))<1e-9
    switch_checks=timecourse_checks=0
    if (out/'goal_switch_diagnostics.json').exists():
        for r in json.loads((out/'goal_switch_diagnostics.json').read_text()):
            a,b=oracles[r['first']],oracles[r['second']]
            distal=(np.asarray(a.to_goal)>=2)&(np.asarray(b.to_goal)>=2)
            assert int(distal.sum())==r['distal_sites'] and 0<=r['distal_hidden_changes']<=r['distal_sites']
            fraction=r['distal_hidden_changes']/r['distal_sites'] if r['aligned'] and r['distal_sites'] else 0.
            assert abs(fraction-r['distal_hidden_fraction'])<1e-12
            masks=[saved_probes[(r['arm'],r['replicate'],case)] for case in (r['first'],r['second'])]
            assert int(np.sum(masks[0]!=masks[1]))==r['probe_raster_changes'];switch_checks+=1
    if (out/'validation_timecourse.json').exists():
        for r in json.loads((out/'validation_timecourse.json').read_text())['rows']:
            assert oracles[r['first']].maze.split==oracles[r['second']].maze.split=='validation_goal'
            channels=set(r['changed_channels']);assert channels <= set(range(8))
            assert r['any_source_state']==bool(channels)
            assert r['hidden_source_state']==bool(channels-{2,7})
            assert r['output_source_state']==(2 in channels) and r['stop_source_state']==(7 in channels)
            assert r['aligned']==(r['steps'][0]==r['steps'][1]==r['horizon']);timecourse_checks+=1
    turned_outputs=0
    if (out/'turned_path_diagnostic.json').exists():
        d=json.loads((out/'turned_path_diagnostic.json').read_text())
        assert known[d['individual']['id']]==Genome.from_dict(d['individual']['genome']).digest
        for ancestor in d['ancestry']:
            assert known[ancestor['id']]==ancestor['genome_sha']
            for r in ancestor['goals']:check_output(r);turned_outputs+=1
        pair=next(p for p in pairs.values() if d['case'] in (p.first.maze.case_id,p.second.maze.case_id))
        for rotation in d['rotations']:
            initial=pair.first if rotation['goal_label']=='a' else pair.second;m=initial.maze;n=m.w
            grid=np.frombuffer(m.cells,dtype=np.uint8).reshape(n,n).copy();start,goal=m.start,m.goal
            for _ in range(rotation['rotation_clockwise_degrees']//90):
                grid=np.rot90(grid,-1).copy();start=(start%n)*n+(n-1-start//n);goal=(goal%n)*n+(n-1-goal//n)
            row=rotation['output'];split=m.split if rotation['rotation_clockwise_degrees']==0 else 'rotation_diagnostic'
            oracles[row['case_id']]=Oracle.build(Maze(grid.tobytes(),n,n,start,goal,m.family,m.seed,split,row['case_id']))
            check_output(row);turned_outputs+=1
        prefix=json.loads((out/'goal_prefix_diagnostic.json').read_text())
        for key in ('parent','first_successful_child'):
            assert known[prefix[key]['id']]==Genome.from_dict(prefix[key]['genome']).digest
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
    costs=defaultdict(Counter);factors=defaultdict(Counter);phases=defaultdict(Counter);evaluations=responses=work=0
    valid_claims=0;valid_shapes={}
    for p in sorted((out/'logs').glob('*/*.evaluations.jsonl.gz')):
        for r in lines(p):
            assert r['id'] in known and r['work']==r['inference_work']+r['probe_work']
            c=costs[r['condition']];c[r['split']+'_responses']+=len(r['cases'])
            c['inference_work']+=r['inference_work'];c['probe_work']+=r['probe_work']
            evaluations+=1;responses+=len(r['cases']);work+=r['work']
            partial=source=bonus=0.;valid=optimal=no_path=0
            pressure=r['condition'].split('/')[2]
            alpha=1. if r['split']=='validation' or pressure=='product' else max(0.,min(1.,(r['generation']-15)/16))
            assert r['alpha']==alpha
            phase='early' if r['generation']<16 else 'transition' if r['generation']<32 else 'matched'
            for case in r['cases']:
                oracle=oracles[case['case']];assert oracle.maze.split in ('train_goal','validation_goal')
                if case['valid']:
                    from cellular_maze_lab import neighbors
                    check_output(case,True);valid_claims+=1
                    mask=unpack(case['mask'],len(oracle.maze.cells));m=oracle.maze;p=m.start;previous=-1;directions=[]
                    while p!=m.goal:
                        q=next(q for q in neighbors(p,m.w,m.h) if mask[q] and q!=previous)
                        directions.append(q-p);previous,p=p,q
                    valid_shapes.setdefault((r['id'],case['case']),dict(condition=r['condition'],id=r['id'],generation=r['generation'],
                        split=r['split'],case=case['case'],edges=len(directions),turns=sum(a!=b for a,b in zip(directions,directions[1:])),
                        optimal=case['optimal'],family=m.family))
                if oracle.path:
                    f=factors[r['condition']+'/'+r['split']];g=case['goal'];f['reachable_responses']+=1
                    if r['split']=='train':
                        phase_counts=phases[r['condition']+'/'+phase];phase_counts['reachable_responses']+=1
                        for label,positive in (('quality',g['quality']>0),('specificity',g['specificity']>0),('joint',g['score']>0)):
                            phase_counts[label]+=int(positive)
                        phase_counts['sum_goal']+=g['score'];phase_counts['sum_quality']+=g['quality'];phase_counts['sum_specificity']+=g['specificity']
                    for label,positive in (('nonempty',g['selected']>0),('connected_growth',g['component']>=3),
                        ('source_dependent_output',g['source_fraction']>0),('positive_quality',g['quality']>0),
                        ('positive_specificity',g['specificity']>0),('positive_goal_score',g['score']>0)):
                        f[label]+=int(positive)
                    for field in ('quality','specificity','score','source_fraction'):
                        f['sum_'+field]+=g[field];f['max_'+field]=max(f['max_'+field],g[field])
                s=case['signal'];expected=max(0.,float(np.mean(list(s['bands'].values())))-s['leakage']) if s['bands'] and s['aligned'] else 0.
                assert abs(expected-s['score'])<1e-9
                assert s['pair_array_bytes']<=80*len(oracle.maze.cells)+65536
                signal_checks+=1;partial+=case['partial'];source+=s['score']
                g=case['goal'];expected_bonus=((1-alpha)*(g['quality']+g['specificity'])+alpha*2*g['score']) if oracle.path and g['aligned'] else 0.
                assert abs(case['factor_bonus']-expected_bonus)<1e-12
                bonus+=expected_bonus
                valid+=case['valid'];optimal+=case['optimal']
                no_path+=case['no_path']-bool(oracle.path and case['status']=='no_path')
            assert r['fitness'][:3]==r['normal_fitness'][:3]==[valid,optimal,no_path]
            assert abs(r['normal_fitness'][3]-round(partial,8))<1e-12
            complete=all(c['valid'] or c['no_path'] for c in r['cases'])
            assert r['fitness'][-1]==r['normal_fitness'][-1]==(-r['inference_work'] if complete else 0)
            assert abs(r['fitness'][3]-(round(partial,8)+source+bonus))<2e-8
    assert work==sum(v['work'] for v in champions.values())
    assert responses==sum(v['maze_evaluations'] for v in champions.values())
    result=dict(all_checks_passed=True,source_files=len(env['source_sha256']),verified_packed_files=packed_files,external_random_ancestors=len(ancestors),
        new_individuals=len(ancestry),max_genes=maximum_genes,unique_inputs=len(digests),unique_layouts=len(layouts),
        previous_layouts=len(previous_layouts),primary_test_layouts=sum(oracles[v[0]].maze.split=='test_goal' for v in layouts.values()),
        paired_final_layouts=sum(oracles[v[0]].maze.split=='test_pairs' for v in layouts.values()),
        reassessed_primary_outputs=primary,reassessed_paired_outputs=paired_outputs,raster_goal_checks=goal_checks,
        reassessed_ablation_outputs=ablation_outputs,ablation_goal_checks=ablation_goals,
        training_signal_arithmetic_checks=signal_checks,training_fitness_checks=evaluations,
        reassessed_training_valid_claims=valid_claims,
        goal_switch_arithmetic_checks=switch_checks,validation_timecourse_checks=timecourse_checks,
        reassessed_ancestry_rotation_outputs=turned_outputs,
        normal_maze_evaluations=responses,developmental_probe_runs=2*responses,charged_work=work,
        inference_work=sum(v['inference_work'] for v in costs.values()),probe_work=sum(v['probe_work'] for v in costs.values()))
    write_json(out/'training_cost.json',costs);write_json(out/'training_factors.json',factors);write_json(out/'training_phases.json',phases)
    write_json(out/'training_valid_shapes.json',list(valid_shapes.values()))
    write_json(out/'probe_route_diagnostics.json',probe_routes)
    write_json(out/'verification.json',result)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/factor_curriculum')
    audit(parser.parse_args().out)
