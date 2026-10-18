"""V8A: frozen validation primitives on a new confirmation corpus, no evolution."""
import argparse,gzip,hashlib,json,resource,time
from itertools import combinations
from pathlib import Path
import numpy as np
from .junction_data import JunctionData,prior_manifests
from .junction_fitness import evaluate,decision
from .junction_diagnostics import choice_intervention
from .junction_audit import unpack
from .goal_data import GoalPair,layout_hash
from .goal_fitness import source_component
from .regulatory_search import Individual
from .regulatory import Genome
from .runtime import Limits,Reaction
from .evaluator import Maze,Oracle,assess
from .experiment import write_json
from .datasets import manifest
from .baselines import baseline,warm_baselines
from .beacon_runtime import warm_runtime


def run(out):
    started=time.perf_counter();root=Path(__file__).resolve().parents[1];out=Path(out)
    if out.exists() and any(out.iterdir()):raise FileExistsError('Choose a fresh output directory')
    out.mkdir(parents=True);source=root/'results/junction_choice'
    ancestry=json.loads(gzip.open(source/'choice_ancestry.json.gz','rt').read())
    config=json.loads((source/'config.json').read_text());config={k:config[k] for k in ('horizon','eval_limits')}
    config.update(seed=2026101807,pairs=12,scope='Exploratory fresh confirmation of validation-selected primitives; no training or model reselection')
    write_json(out/'config.json',config);models=[];group_tests=[]
    for record in ancestry:
        nodes=record['nodes'];first=next(i for i,n in enumerate(nodes) if n['strict_both'])
        roles={}
        for role,node in (('root',nodes[0]),('parent',nodes[max(0,first-1)]),('variant',nodes[-1])):
            item=node['individual'];digest=Genome.from_dict(item['genome']).digest
            if digest not in roles:roles[digest]=dict(condition=record['condition'],roles=[],individual=item)
            roles[digest]['roles'].append(role)
        models.extend(roles.values())
        child=nodes[first];parent=nodes[max(0,first-1)];changes=child['gene_row_changes']
        if len(changes)==3:
            swap=next(((a,b) for a,b in combinations(changes,2) if a['before']==b['after'] and b['before']==a['after']),None)
            if swap:
                remaining=[r for r in changes if r not in swap]
                group_tests.append((record,parent,child,swap,remaining))
    write_json(out/'models.json',models)
    frozen=hashlib.sha256((out/'models.json').read_bytes()).hexdigest()
    inputs={'results/junction_choice/'+n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ('choice_ancestry.json.gz','strict_validation_archive.json','mazes.json.gz','config.json')}
    sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        (Path(__file__),root/'docs/JUNCTION_CONFIRMATION_V8A.md')}
    write_json(out/'freeze.json',dict(models_sha256=frozen,input_sha256=inputs,source_sha256=sources))
    previous=prior_manifests(root)+json.loads(gzip.open(source/'mazes.json.gz','rt').read())
    data=JunctionData(config['seed'],previous)
    specs=[(n,f) for n in (9,17,33) for f in ('perfect','random') for _ in range(2)]
    pairs=[data.pair('confirmation_pairs',0,i,n,f,64) for i,(n,f) in enumerate(specs)]
    with gzip.open(out/'mazes.json.gz','wt',compresslevel=9) as f:json.dump(manifest(data.cache.values()),f,separators=(',',':'))
    write_json(out/'pairs.json',data.pair_manifest());limits=Limits(**config['eval_limits'])
    warm_runtime();warm_baselines();outputs=[];summary=[];work=responses=0
    for index,model in enumerate(models):
        item=Individual.load(model['individual']);ev=evaluate(item,pairs,'evolved',limits,'junction',config['horizon'])
        outputs.append(dict(index=index,condition=model['condition'],roles=model['roles'],id=item.identity,
            junction=ev.junction,junction_both=ev.junction_both,work=ev.work,cases=ev.rows))
        summary.append(dict(index=index,condition=model['condition'],roles=model['roles'],junction=ev.junction,
            strict_both=sum(ev.rows[2*j]['junction']['pair_both'] for j in range(len(pairs))),
            valid=sum(r['valid'] for r in ev.rows),optimal=sum(r['optimal'] for r in ev.rows)))
        work+=ev.work;responses+=len(ev.rows)
    reference=[]
    for pair in pairs:
        for o in pair.cases:
            m=o.maze;r=baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal);a=assess(r,o)
            reference.append(dict(case=m.case_id,status=r.status,mask=np.packbits(r.mask,bitorder='little').tobytes().hex(),optimal=a.optimal))
    interaction=[]
    for record,parent,child,swap,remaining in group_tests:
        pair=GoalPair(*[Oracle.build(Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id']))
            for case in (record['first'],record['second']) for r in json.loads(gzip.open(source/'mazes.json.gz','rt').read()) if r['case_id']==case])
        trials=[]
        for name,changes in (('swap_only',swap),('register_change_only',remaining)):
            genes=[list(g) for g in parent['individual']['genome']['genes']]
            for change in changes:genes[change['index']]=change['after']
            genome=Genome.from_dict(dict(version=2,genes=genes));item=Individual('diagnostic/'+name,genome,parent['individual']['id'],0)
            result=choice_intervention(item,pair,'evolved',limits,config['horizon']);result.update(name=name,individual=item.save())
            trials.append(result);work+=result['work'];responses+=2
        interaction.append(dict(condition=record['condition'],first=record['first'],second=record['second'],
            parent=parent,child=child,swap_rows=[r['index'] for r in swap],other_rows=[r['index'] for r in remaining],trials=trials))
    for name,value in (('outputs',outputs),('reference',reference),('interaction',interaction)):
        with gzip.open(out/(name+'.json.gz'),'wt',compresslevel=9) as f:json.dump(value,f,separators=(',',':'))
    write_json(out/'summary.json',summary)
    write_json(out/'environment.json',dict(elapsed_seconds=time.perf_counter()-started,max_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        normal_responses=responses,probe_runs=2*responses,baseline_responses=len(reference),charged_work=work,
        models_sha256=frozen,prior_layouts=len({hashlib.sha256(f"{r['w']},{r['h']}:".encode()+bytes.fromhex(r['cells_hex'])).hexdigest() for r in previous})))
    audit(out)
    print(json.dumps(dict(summary=summary,interaction=[dict(condition=r['condition'],trials=[{k:t[k] for k in ('name','junction','junction_both')} for t in r['trials']]) for r in interaction]),indent=2))


def audit(out):
    started=time.perf_counter();out=Path(out);root=Path(__file__).resolve().parents[1]
    freeze=json.loads((out/'freeze.json').read_text());env=json.loads((out/'environment.json').read_text())
    assert hashlib.sha256((out/'models.json').read_bytes()).hexdigest()==freeze['models_sha256']==env['models_sha256']
    for key in ('source_sha256','input_sha256'):
        for p,h in freeze[key].items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h
    previous=prior_manifests(root)+json.loads(gzip.open(root/'results/junction_choice/mazes.json.gz','rt').read())
    excluded={hashlib.sha256(f"{r['w']},{r['h']}:".encode()+bytes.fromhex(r['cells_hex'])).hexdigest() for r in previous}
    all_oracles={}
    for source in (out/'mazes.json.gz',root/'results/junction_choice/mazes.json.gz'):
        for r in json.loads(gzip.open(source,'rt').read()):
            m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id']);assert m.digest==r['sha256']
            if source.parent==out:assert layout_hash(m) not in excluded
            all_oracles[m.case_id]=Oracle.build(m)
    pairs=json.loads((out/'pairs.json').read_text());assert len(pairs)==12
    for i,r in enumerate(pairs):
        pair=GoalPair(all_oracles[r['first']],all_oracles[r['second']]);label=decision(pair);assert label==r['decision']
        assert all(len(o.path)-1>=8 for o in pair.cases)
        if i%2==0:assert any(label['detours'])
    verified=0
    def check(record):
        nonlocal verified
        cases=record['cases'];minima=[];both=[]
        for a,b in zip(cases[::2],cases[1::2]):
            pair=GoalPair(all_oracles[a['case']],all_oracles[b['case']]);label=decision(pair);scores=[];strict=[]
            aligned=all(r['signal']['aligned'] for r in (a,b))
            for i,r in enumerate((a,b)):
                o=pair.cases[i];n=len(o.maze.cells);mask=unpack(r['probe_mask'],n);off=unpack(r['source_removed_mask'],n)
                _,component=source_component(mask,o.maze);prefix=label['prefix'][2:];wanted=set(label['allowed'][i]);wrong=set(label['exits'])-wanted
                lit=[q for q in wanted if mask[q]];bad=[q for q in wrong if mask[q]]
                R=sum(q in component and not off[q] for q in prefix)/len(prefix)
                C=(sum(not off[q] for q in lit)/len(lit))*(1-len(bad)/len(wrong))/len(lit) if lit and label['vertex'] in component else 0.
                score=(.25*R+.75*C) if aligned else 0.;qualifies=bool(aligned and label['vertex'] in component and len(lit)==1 and not bad and not off[lit[0]])
                assert abs(r['junction']['score']-score)<1e-12 and r['junction']['strict']==qualifies
                result=assess(Reaction(unpack(r['mask'],n),r['status'],r['steps'],0,0,0),o)
                assert (r['valid'],r['optimal'],r['no_path'])==(result.valid_path,result.optimal,result.no_path_correct)
                assert r['failure']==result.failure and abs(r['partial']-result.partial)<1e-12
                scores.append(score);strict.append(qualifies);verified+=1
            minima.append(min(scores));both.append(all(strict))
        assert abs(record['junction']-sum(minima)/len(minima))<1e-12
        assert abs(record['junction_both']-sum(both)/len(both))<1e-12
    for r in json.loads(gzip.open(out/'outputs.json.gz','rt').read()):check(r)
    for r in json.loads(gzip.open(out/'interaction.json.gz','rt').read()):
        for t in r['trials']:check(t)
    baseline_checks=0
    for r in json.loads(gzip.open(out/'reference.json.gz','rt').read()):
        o=all_oracles[r['case']];result=assess(Reaction(unpack(r['mask'],len(o.maze.cells)),r['status'],0,0,0,0),o)
        assert result.optimal and r['optimal'];baseline_checks+=1
    write_json(out/'verification.json',dict(all_checks_passed=True,verified_normal_outputs=verified,verified_junction_masks=verified,
        baseline_outputs=baseline_checks,confirmed_layouts=12,elapsed_seconds=time.perf_counter()-started,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/junction_confirmation');parser.add_argument('--audit',action='store_true')
    args=parser.parse_args();audit(args.out) if args.audit else run(args.out)
