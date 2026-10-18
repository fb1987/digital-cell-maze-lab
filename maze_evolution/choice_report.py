"""V9 report generated from frozen outputs and independently checked accounting."""
import argparse
from collections import defaultdict
import gzip,json,statistics
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle
from .experiment import write_json
from .choice_audit import unpack
from .factor_report import paired_summary
from .signal_audit import lines
def visuals(out,manifest,primary,paired):
    from PIL import Image,ImageDraw
    (out/'visuals').mkdir(exist_ok=True)
    def grid(draw,ox,oy,m,mask,tile=10):
        for p,opened in enumerate(bytes.fromhex(m['cells_hex'])):
            color='#172235' if not opened else '#5ae1bd' if mask[p] else '#45536a'
            if p==m['start']:color='#72b6ff'
            if p==m['goal']:color='#ff6584'
            x,y=p%m['w'],p//m['w'];draw.rectangle((ox+x*tile,oy+y*tile,ox+(x+1)*tile-1,oy+(y+1)*tile-1),fill=color)
    selected=[next(m for m in manifest if m['split']=='test_goal' and m['w']==17 and m['family']==f and '/r0/' in m['case_id']) for f in ('perfect','random')]
    arms=('compiled_bfs','local/prefix/task','local/choice/task','evolved/prefix/task','evolved/choice/task')
    canvas=Image.new('RGB',(1200,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Unseen ordinary outputs | green: output; blue: source; pink: goal. First size17 case per family, replicate 0.',fill='#e6edf7')
    for i,m in enumerate(selected):
        for j,arm in enumerate(arms):
            r=next(r for r in primary if r['case_id']==m['case_id'] and r['arm']==arm)
            ox,oy=15+j*240,85+i*245
            draw.text((ox,oy-40),arm,fill='#e6edf7');draw.text((ox,oy-22),m['family']+' | '+('shortest' if r['optimal'] else r['failure']),fill='#aabbd0')
            grid(draw,ox,oy,m,unpack(r['mask'],m['w']*m['h']))
    canvas.save(out/'visuals/unseen_outputs.png')
    if (out/'inherited_path_diagnostic.json').exists():
        d=json.loads((out/'inherited_path_diagnostic.json').read_text())
        if 'individual' in d:
            m=d['case'];canvas=Image.new('RGB',(840,315),'#111827');draw=ImageDraw.Draw(canvas)
            draw.text((15,15),'Inherited growth on an inspected unseen maze | goal switch changes stopping, not the measured output trajectory.',fill='#e6edf7')
            variants=[('Original goal | normal halt19',m,unpack(d['ordinary'][0]['mask'],m['w']*m['h'])),
                ('Midpoint goal | normal halt11',{**m,'goal':d['alternate_goal']},unpack(d['ordinary'][1]['mask'],m['w']*m['h'])),
                ('Midpoint goal | forced tick 19',{**m,'goal':d['alternate_goal']},np.asarray(d['snapshots'][-1]['output_states'][1])>0)]
            for j,(label,maze,mask) in enumerate(variants):
                x=15+j*280;draw.text((x,55),label,fill='#e6edf7');grid(draw,x,85,maze,mask,tile=16)
            draw.text((15,280),'Post-hoc diagnostic, not an additional holdout. The nine-edge, one-turn success is present in the frozen control.',fill='#aabbd0')
            canvas.save(out/'visuals/inherited_path.png')

    lookup={m['case_id']:m for m in manifest}
    pairs=json.loads((out/'pairs.json').read_text())
    pair=next(p for p in pairs if '/r0/' in p['first'] and '/17x17/' in p['first'] and '/random/' in p['first'] and p['first'].startswith('test_pairs/'))
    arms=('compiled_bfs','evolved/prefix/choice','evolved/choice/choice','evolved/choice/frozen_choice')
    canvas=Image.new('RGB',(960,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Switched goals on identical geometry/source | BFS versus tick 16 output raster, without assumed correctness.',fill='#e6edf7')
    for i,case in enumerate((pair['first'],pair['second'])):
        m=lookup[case]
        for j,arm in enumerate(arms):
            if arm=='compiled_bfs':r=next(r['baseline'] for r in paired if r['arm']==arm and 'baseline' in r and r['baseline']['case_id']==case);mask=unpack(r['mask'],m['w']*m['h']);subtitle='Shortest route'
            else:
                record=next(r for r in paired if r['arm']==arm and r['replicate']==0)
                r=next(r for r in record['cases'] if r['case']==case);mask=unpack(r['probe_mask'],m['w']*m['h']);subtitle=f"Tick16: J={r['junction']['score']:.3f}"
            ox,oy=15+j*240,85+i*245
            draw.text((ox,oy-40),arm,fill='#e6edf7');draw.text((ox,oy-22),f"Goal {'A' if i==0 else 'B'} | {subtitle}",fill='#aabbd0')
            grid(draw,ox,oy,m,mask)
    canvas.save(out/'visuals/switched_goals.png')
    ancestry=json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read())
    if ancestry:
        record=ancestry[0];nodes=record['nodes'];index=next(i for i,r in enumerate(nodes) if r['strict_both'])
        child=nodes[index] if index else nodes[-1];parent=nodes[max(0,index-1)];lookup={m['case_id']:m for m in manifest}
        canvas=Image.new('RGB',(1040,320),'#111827');draw=ImageDraw.Draw(canvas)
        draw.text((15,12),('Validation precursor | first strict transition' if index else 'Validation precursor | qualification already present in frozen ancestor')+' | gold: decision.',fill='#e6edf7')
        for j,(node,goal_index) in enumerate(((parent,0),(child,0),(parent,1),(child,1))):
            r=node['cases'][goal_index];m=lookup[r['case']];ox=15+j*260;oy=95
            draw.text((ox,48),(('Parent' if index else 'Initial qualifying ancestor') if j%2==0 else ('First qualifying child' if index else 'Final saved variant'))+(' | goal A' if goal_index==0 else ' | goal B'),fill='#e6edf7')
            draw.text((ox,68),f"Tick16 J={r['junction']['score']:.3f}; strict={r['junction']['strict']}",fill='#aabbd0')
            tile=16 if m['w']<=9 else 10
            grid(draw,ox,oy,m,unpack(r['probe_mask'],m['w']*m['h']),tile=tile)
            v=record['decision']['vertex'];x=ox+tile*(v%m['w']);y=oy+tile*(v//m['w']);draw.rectangle((x,y,x+tile-1,y+tile-1),outline='#ffd46a',width=2)
        draw.text((15,290),'This is a selected validation example, not unseen route success. Whole normal outputs remain independently assessed.',fill='#aabbd0')
        canvas.save(out/'visuals/validation_choice.png')
    rows=json.loads((out/'goal_timecourse.json').read_text())
    summary={r['arm']:r for r in json.loads((out/'paired_summary.json').read_text())}
    arms=('evolved/prefix/frozen_choice','evolved/prefix/choice','evolved/choice/frozen_choice','evolved/choice/choice')
    labels=('Prefix frozen','Prefix evolved','Choice frozen','Choice evolved')
    source=[sum(r['aligned'] and r['any_source_state'] for r in rows if r['arm']==a and r['horizon']==16) for a in arms]
    scores=[summary[a]['junction'] for a in arms]
    canvas=Image.new('RGB',(1040,390),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((24,18),'V9 precursor comparison | common strict-choice archives | three replicates',fill='#e6edf7')
    draw.text((24,40),'Paired shortest counts: '+', '.join(f"{label} {summary[a]['optimal']}/42" for a,label in zip(arms,labels)),fill='#aabbd0')
    for panel,(title,values,maximum) in enumerate((('Goal switch changes source state at tick 16',source,18),('Regular-pair weaker-choice score J',scores,max(.05,1.1*max(scores))))):
        ox=24+panel*520;draw.text((ox,80),title,fill='#e6edf7')
        for i,(label,value) in enumerate(zip(labels,values)):
            y=120+i*52;draw.text((ox,y+5),label,fill='#cbd5e1')
            length=int(265*value/maximum);color='#6da8e8' if i<2 else '#5ae1bd'
            if length:draw.rectangle((ox+110,y,ox+110+length,y+24),fill=color)
            formatted=f'{value}/18' if panel==0 else f'{value:.4f}'
            draw.text((ox+120+length,y+5),formatted,fill='#e6edf7')
    draw.text((24,355),'Descriptive comparison; no significance claim. All groups use the same pulse input convention.',fill='#aabbd0')
    canvas.save(out/'visuals/precursor_comparison.png')


def verify_inherited_path(out):
    import hashlib,time
    from .beacon_runtime import Organism
    from .beacon_probe import observe
    from .runtime import Limits
    from .regulatory_search import Individual
    from .evaluator import assess
    started=time.perf_counter();out=Path(out);root=Path(__file__).resolve().parents[1]
    d=json.loads((out/'inherited_path_diagnostic.json').read_text())
    if 'individual' not in d:return
    assert hashlib.sha256((root/'maze_evolution/choice_path_diagnostic.py').read_bytes()).hexdigest()==d['source_sha256']
    assert hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()==d['champions_sha256']
    r=d['case'];m=Maze(bytes.fromhex(r['cells_hex']),r['w'],r['h'],r['start'],r['goal'],r['family'],r['seed'],r['split'],r['case_id'])
    original=Oracle.build(m);assert list(original.path)==d['original_oracle_path']
    alternate=Maze(m.cells,m.w,m.h,m.start,d['alternate_goal'],m.family,m.seed,'diagnostic',m.case_id+'/midpoint_goal')
    oracles=[original,Oracle.build(alternate)];config=json.loads((out/'config.json').read_text())
    organism=Organism(Individual.load(d['individual']).genome,'local',Limits(**config['eval_limits']),goal_pulse=True)
    work=0
    for o,saved in zip(oracles,d['ordinary']):
        mm=o.maze;a=organism.react(mm.cells,mm.w,mm.h,mm.start,mm.goal);assessment=assess(a,o)
        assert np.array_equal(a.mask,unpack(saved['mask'],len(mm.cells)))
        assert (a.status,a.steps,a.dispatches,a.spatial_reads)==(saved['status'],saved['steps'],saved['dispatches'],saved['reads'])
        assert (assessment.valid_path,assessment.optimal,assessment.failure)==(saved['valid_path'],saved['optimal'],saved['failure'])
        work+=a.dispatches+a.spatial_reads
    for snapshot in d['snapshots']:
        observations=[]
        for i,o in enumerate(oracles):
            mm=o.maze;a=observe(organism,mm.cells,mm.w,mm.h,mm.start,mm.goal,snapshot['tick'],True)
            assert a.state[2].tolist()==snapshot['output_states'][i] and a.state[7].tolist()==snapshot['stop_states'][i]
            assert a.state[:,mm.start].tolist()==snapshot['source_states'][i]
            observations.append(a);work+=a.dispatches+a.reads
        assert np.sum(observations[0].state!=observations[1].state,axis=1).tolist()==snapshot['changed_sites_by_channel']
    assert work==d['charged_work']
    assert d['output_concentrations_identical']==all(s['output_states'][0]==s['output_states'][1] for s in d['snapshots'])
    endpoints=[]
    for i,(o,normal) in enumerate(zip(oracles,d['ordinary'])):
        snapshot=d['snapshots'][normal['steps']-1];mask=np.asarray(snapshot['output_states'][i])>0
        assert np.array_equal(mask,unpack(normal['mask'],len(mask)))
        endpoints.append(bool(snapshot['source_states'][i][7]>0 and mask[o.maze.start] and mask[o.maze.goal]))
    assert all(endpoints)
    write_json(out/'inherited_path_verification.json',dict(all_checks_passed=True,normal_replays=2,probe_replays=2*d['horizon'],
        replayed_work=work,endpoint_stop_conditions=endpoints,elapsed_seconds=time.perf_counter()-started,
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))


def report(out):
    out=Path(out);read=lambda name:json.loads((out/name).read_text())
    env=read('environment.json');config=read('config.json');gate=read('extension_decision.json');v=read('verification.json')
    champions=read('champions.json');primary=list(lines(out/'holdout.jsonl.gz'));paired=list(lines(out/'paired_holdout.jsonl.gz'))
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());mazes={m['case_id']:m for m in manifest}
    reachable={m['case_id']:m['oracle_length']>0 for m in manifest};pairs=read('pairs.json')
    def paired_stats(records):
        result=paired_summary(records,reachable)
        for r in result:
            rr=[a for a in records if a['arm']==r['arm'] and 'baseline' not in a]
            for k in ('balanced','junction','junction_both'):r[k]=float(np.mean([a[k] for a in rr])) if rr else None
        return result
    ps=paired_stats(paired);write_json(out/'paired_summary.json',ps);pm={r['arm']:r for r in ps}
    cs=paired_stats(list(lines(out/'cross_input.jsonl.gz')));write_json(out/'cross_input_summary.json',cs)
    summaries={r['arm']:r for r in read('summary.json') if r['group']=='all'}
    difficulty=defaultdict(lambda:defaultdict(int));no_path=defaultdict(lambda:defaultdict(int));shapes=[]
    from cellular_maze_lab import neighbors
    for r in primary:
        arm=r['arm'];m=mazes[r['case_id']];w=m['w'];start=m['start'];goal=m['goal']
        no_path[arm]['correct']+=r['no_path_correct'];no_path[arm]['false_on_reachable']+=bool(r['reachable'] and r['status']=='no_path')
        md=abs(start%w-goal%w)+abs(start//w-goal//w)
        for label,condition in (('turn_required',start%w!=goal%w and start//w!=goal//w),('detour_required',r['edges']>md)):
            if r['reachable'] and condition:
                difficulty[arm][label+'_cases']+=1;difficulty[arm][label+'_optimal']+=r['optimal']
        if r['valid_path'] and '/' in arm:
            mask=unpack(r['mask'],w*m['h']);p=start;previous=-1;directions=[]
            while p!=goal:
                q=next(q for q in neighbors(p,w,m['h']) if mask[q] and q!=previous)
                directions.append(q-p);previous,p=p,q
            shapes.append(dict(arm=arm,replicate=r['replicate'],case=r['case_id'],edges=len(directions),turns=sum(a!=b for a,b in zip(directions,directions[1:])),optimal=r['optimal']))
    write_json(out/'success_shapes.json',shapes);write_json(out/'difficulty_summary.json',difficulty);write_json(out/'no_path_diagnostics.json',no_path)
    from .regulatory import Genome
    from .range_audit import output_dataflow
    structures=[]
    for saved in champions.values():
        c=saved['config']
        for source,prefix in (('archives',''),('frozen','frozen_')):
            for label in ('task','choice'):
                item=saved[source][label]['individual'];g=Genome.from_dict(item['genome'])
                structures.append(dict(arm=f"{c['topology']}/{c['pressure']}/{prefix}{label}",replicate=c['replicate'],id=item['id'],genome_sha=g.digest,**output_dataflow(g)))
    write_json(out/'capacity_diagnostics.json',structures)
    current=pm['evolved/choice/choice'];control=pm['evolved/prefix/choice'];frozen=pm['evolved/choice/frozen_choice']
    task=summaries['evolved/choice/task'];ct=summaries['evolved/prefix/task'];ft=summaries['evolved/choice/frozen_task']
    text=['# Strict paired-choice priority: V9','',
        f"Multirange task archives complete **{task['optimal']}/{task['reachable']}** unseen shortest paths with Choice-first pressure, "
        f"versus **{ct['optimal']}/{ct['reachable']}** with Prefix and **{ft['optimal']}/{ft['reachable']}** frozen. "
        f"Choice-first solves **{task['long_optimal']}/{task['long_cases']}** at distance ≥8 and **{pm['evolved/choice/task']['optimal']}/42** paired reachable targets. "
        f"Compiled BFS, A* and wavefront complete {pm['compiled_bfs']['optimal']}/42 paired and {summaries['compiled_bfs']['optimal']}/{task['reachable']} ordinary routes. "
        'Correctness remains the primary measure; no competitive speedup is established.','',
        f"The common strict-choice archives make correct choices under both switched goals on **{round(18*current['junction_both'])}/18** pairs under Choice-first pressure, "
        f"**{round(18*control['junction_both'])}/18** under Prefix and **{round(18*frozen['junction_both'])}/18** frozen. "
        f"Their weaker-choice scores are J={current['junction']:.4f}, {control['junction']:.4f}, {frozen['junction']:.4f}. "
        'J includes partial source-dependent prefix credit; it is not route correctness. Three replicates support a descriptive comparison, without a significance claim.','',
        f"The preregistered extension gate was **{gate['extend']}** after {sorted({s['next_generation'] for s in champions.values()})} generations. "
        'A negative bounded experiment does not establish impossibility of random-origin discovery.','',
        'All six matched pressure pairs have identical ordered genotype populations throughout and identical final RNG states. '
        'Paired training successes already reproduce under the existing score; raising their priority changes neither the observed trajectories nor the sampled counterfactual parent choices. '
        'The bottleneck identified here is transfer across contexts.','',
        f'![Precursor comparison]({out.name}/visuals/precursor_comparison.png)','',
        '## Controlled comparison and provenance','',
        'The V6 pulse VM is unchanged: eight uint16 channels,128 typed genes, source/goal pulses and flags, output2,stop7. '
        'Both pressures call the exact V8 Junction evaluator, preserving J=.25 source-dependent connected prefix +.75 shortest-exit choice, '
        'normal partial output and hidden source-transmission shaping. All cyclic shortest-exit ties are accepted individually; wrong exits must be off. '
        'Mixed pairs keep their prior goal shaping. Oracle labels remain outside inference.','',
        'The isolated selection change is global rank(V,O,N,0,S,W) for Prefix versus(V,O,N,K,S,W) for Choice-first: '
        'V=valid routes,O=shortest routes,N=no-path utility,K=number of strict-both pairs,S=unchanged continuous score,W=old cost tie-break. '
        'Normal correctness dominates every precursor; cost/length does not penalize unfinished phenotypes. '
        'Per-case lexicase ranks validity,optimality,paired strict bit,then smooth score with epsilon.02. '
        'Prefix inserts a constant zero and reproduces the old decisions/RNG. Choice-first gives both cases the same pair-level bit.','',
        'Both arms fork the same matching V8 Junction next population/RNG, protect validation-selected task/junction/balanced/goal/source variants '
        'and prior protected ancestors from both V8 arms, supplemental strict-choice selections and saved qualifying ancestors. '
        'Variants remain in their native topology/replicate. Both arms have identical initial genotypes, protection, eight nomination criteria and common validation objective(Prefix). '
        'The primary choice archive ranks strict-both rate,then mean minJ,B,G,validity,optimality; the task archive uses normal fitness only. '
        'New validation archives do not automatically breed. Fresh immigrants, neutral diversity and full continuation checkpoints remain preserved.','',
        f"Preregistration commit `{env['parent_revision']}`; frozen model SHA256 `{env['champions_sha256']}`. "
        f"Seed{config['seed']}, independent full-capacity construction seed1094; all {env['previous_layouts']} V1–V8/V8A layouts excluded. "
        'Final layouts were constructed only after selection freeze.264 ordinary layouts and24 separate paired layouts/48 inputs are common to both arms. '
        'The paired set has42 reachable targets≥8 and6 unreachable, including18 eligible regular decisions. '
        'Sampling matches V8: shared shortest prefix at source distance2..8,goals≥4 beyond,disjoint shortest-exit sets; even indices require misleading Manhattan bearing. '
        'Between-version comparisons also change common starting/archival policy and seeds; only the within-V9 pressure comparison isolates the priority.','',
        '## Completed unseen outputs','',
        '| Arm | Valid / reachable | Shortest | Distance≥8 shortest | Correct no-path /48 | False no-path |',
        '|---|---:|---:|---:|---:|---:|']
    for arm,a in sorted(summaries.items()):
        text.append(f"| {arm} | {a['valid']}/{a['reachable']} | {a['optimal']} | {a['long_optimal']}/{a['long_cases']} | {a['no_path']}/48 | {no_path[arm]['false_on_reachable']} |")
    text += ['','| Task archive | Turn-required shortest | Mandatory-detour shortest | Paired shortest /42 |','|---|---:|---:|---:|']
    taskarms=[f'{t}/{p}/task' for t in ('local','evolved') for p in ('prefix','choice')]
    for arm in taskarms:
        a=difficulty[arm];text.append(f"| {arm} | {a['turn_required_optimal']}/{a['turn_required_cases']} | {a['detour_required_optimal']}/{a['detour_required_cases']} | {pm[arm]['optimal']}/42 |")
    successes=[r for r in shapes if not '/frozen_' in r['arm']]
    text += ['',f"Selected current task/choice successes span {min((r['edges'] for r in successes),default=0)}–{max((r['edges'] for r in successes),default=0)} edges "
        f"and at most {max((r['turns'] for r in successes),default=0)} turns. Full successful shapes are in `success_shapes.json`; a success can be inherited or supplied by common endpoint-aware halting. "
        'It is not automatically an evolved goal-guided algorithm. Per-size/family results and all failures are in the raw summary/output records.','',
        f'![Ordinary unseen outputs]({out.name}/visuals/unseen_outputs.png)','',
        '## Paired decisions and communication','',
        '| Arm | Weaker-choice J | Strict both /18 | Old balanced B | Mean G | Source transmission | Paired shortest /42 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for a in ps:
        if a['junction'] is not None:text.append(f"| {a['arm']} | {a['junction']:.4f} | {round(18*a['junction_both'])}/18 | {a['balanced']:.4f} | {a['goal']:.4f} | {a['signal']:.4f} | {a['optimal']}/42 |")
    text += ['','B=min of old G scores within each regular pair; G averages all inputs, including mixed ones. J averages regular pairs only. Denominators differ. '
        'Every regular final pair is eligible for the decision assay. Choice selection ranks strict-both before J, so a higher J alone is not a victory.','',
        '| Multirange strict-choice archive | Replicate | J | Strict both /6 | Mean G |','|---|---:|---:|---:|---:|']
    for p in ('prefix','choice'):
        for rep in range(3):
            r=next(r for r in paired if r['arm']==f'evolved/{p}/choice' and r['replicate']==rep)
            text.append(f"| {p} | {rep} | {r['junction']:.4f} | {round(6*r['junction_both'])}/6 | {r['goal']:.4f} |")
    jf=read('junction_factors.json')
    text += ['', '| Training pressure/topology | Source-connected decisions | Positive choice C | Strict individual | Strict both pairs |',
        '|---|---:|---:|---:|---:|']
    for t in ('local','evolved'):
        for p in ('prefix','choice'):
            entries=[v for k,v in jf.items() if k.startswith(f'choice/{t}/{p}/') and k.endswith('/train')]
            total=lambda key:sum(x.get(key,0) for x in entries)
            text.append(f"| {t}/{p} | {total('source_connected_junction')}/{total('eligible_cases')} | {total('positive_choice')} | {total('strict_choice')} | {total('strict_both_pairs')}/{total('regular_pairs')} |")
    text += ['', 'These counts include repeated genomes and rotating training cases. They diagnose the selection landscape, not independent discoveries or unseen success.']
    reproduction=read('reproductive_priority.json')['records'];reproductive_summary=[]
    text += ['', '## Reproductive use of paired choices','',
        'This diagnostic was specified during training before final inspection. A positive genome has K>0 on that generation’s rotating batch. '
        'Unprotected means its genotype differs from every fixed protected variant. Track actual retention and mutation-parent use in the next population. '
        'Counts repeat genotypes/contexts; the ratios describe repeated selection opportunities rather than independent replications. In this run all paired ordered genotype populations and final RNG states are identical.','',
        '| Condition | Generations with unprotected positive | Positive individual opportunities | Retained | Offspring from positive parents / all mutant offspring |',
        '|---|---:|---:|---:|---:|']
    for t in ('local','evolved'):
        for pressure in ('prefix','choice'):
            entries=[r for r in reproduction if r['condition'].startswith(f'choice/{t}/{pressure}/')]
            total=lambda key:sum(r[key] for r in entries)
            row=dict(condition=t+'/'+pressure,generations=sum(r['positive_unprotected_genotype_individuals']>0 for r in entries),
                opportunities=total('positive_unprotected_genotype_individuals'),retained=total('retained_unprotected_positive'),
                offspring=total('offspring_from_unprotected_positive'),all_mutant_offspring=total('mutated_offspring'))
            reproductive_summary.append(row)
            text.append(f"| {row['condition']} | {row['generations']}/{len(entries)} | {row['opportunities']} | {row['retained']} | {row['offspring']}/{row['all_mutant_offspring']} |")
    write_json(out/'reproductive_summary.json',reproductive_summary)
    trajectories=read('priority_trajectories.json')
    text += ['', '| Topology | Replicate | First strict opportunity | First population divergence |', '|---|---:|---:|---:|']
    for r in trajectories:
        text.append(f"| {r['topology']} | {r['replicate']} | {r['first_strict_opportunity']} | {r['first_population_divergence']} |")
    text += ['', 'None means no event in the recorded generations. Every matched pair remains identical through the full run, including its final RNG state. The audit verifies equality before the first opportunity as a control check. '
        'A new priority has no selective effect when every candidate has K=0.']
    entry=read('entry_diagnostics.json')['records']
    text += ['', 'A second diagnostic, specified during training, removes the desired exits from each saved strict-choice raster and checks source can still reach the junction. '
        'This tests arrival from the incoming side rather than connection through the desired branch itself; a shortest incoming prefix is also recorded. '
        'It does not change the preregistered K or primary measures.','',
        '| Condition | Strict-both training responses | Incoming side correct under both goals | Both shortest incoming prefixes |',
        '|---|---:|---:|---:|']
    for t in ('local','evolved'):
        for pressure in ('prefix','choice'):
            rr=[r for r in entry if r['condition']==f'choice/{t}/{pressure}/0' or r['condition']==f'choice/{t}/{pressure}/1' or r['condition']==f'choice/{t}/{pressure}/2']
            rr=[r for r in rr if r['split']=='train']
            text.append(f"| {t}/{pressure} | {len(rr)} | {sum(r['both_enter_from_source'] for r in rr)} | {sum(r['both_shortest_prefixes'] for r in rr)} |")

    counter=read('selection_counterfactual.json')
    text += ['', f"A post-hoc selection replay uses the {counter['active_pools']} observed Prefix pools with K>0. "
        f"Across {counter['draws']} matched-seed lexicase draws, {counter['changed_parent_ids']} parent IDs and {counter['changed_parent_genotypes']} parent genotypes change. "
        f"Global best sets change in {counter['changed_global_top_sets']} pools. First-case route/strict/smooth filtering is saved for inspection. "
        f"This is conditional on these observed pools, not a claim that strict priority is redundant in every possible population. No candidate inference or training is added. This analysis took{counter['elapsed_seconds']:.2f}s."]
    if (out/'inherited_path_diagnostic.json').exists():
        verify_inherited_path(out);d=read('inherited_path_diagnostic.json');pv=read('inherited_path_verification.json')
        if 'individual' in d:
            text += ['', '## Inherited nine-edge path: goal-switch diagnostic','',
                'The frozen local task genome completes a nine-edge path with one turn. The current task archive has the same genotype. '
                'This capability predates V9. On this inspected final layout, move the target to the oracle-path midpoint without changing the genome or geometry. '
                'It emits a five-edge shortest prefix at tick 11 instead of the original nine-edge path at tick 19. '
                'Forced probes show identical complete output concentrations and source states under both targets at every ticks 1–19. '
                'Both ordinary stops satisfy the common runtime’s source-stop and endpoint conditions. Thus the measured tissue follows the same growth trajectory; '
                'endpoint-aware stopping picks the path length on this example. This is preserved as inherited growth, without claiming goal-guided routing.','',
                f'![Inherited path diagnostic]({out.name}/visuals/inherited_path.png)','',
                f"This is post-hoc on an inspected final case, not another holdout or a tuned genome. Original assay:{d['elapsed_seconds']:.3f}s, "
                f"2 normal responses/{d['probes']} probes,{d['charged_work']:,} work units; independent replay:{pv['elapsed_seconds']:.3f}s, "
                f"{pv['replayed_work']:,} units. All rasters, trajectories and source/model hashes are saved."]
    text += ['', '## Paired output details','']
    choices=read('choice_diagnostics.json');courses=read('goal_timecourse.json')
    choice_summary=[]
    for arm in sorted({r['arm'] for r in choices}):
        rr=[r for r in choices if r['arm']==arm and r['assay']=='native']
        if not rr:continue
        metrics=[x for r in rr for x in r['metrics']]
        choice_summary.append(dict(arm=arm,pairs=len(rr),both=sum(r['both'] for r in rr),single_strict=sum(x['strict'] for x in metrics),
            junction_connected=sum(x['connected'] for x in metrics),prefix=float(np.mean([x['prefix'] for x in metrics])),
            choice=float(np.mean([x['choice'] for x in metrics])),wrong_exits_lit=sum(bool(x['wrong_on']) for x in metrics)))
    write_json(out/'choice_summary.json',choice_summary)
    text += ['','| Strict-choice archive | Connected junction /36 goals | Mean prefix R | Mean choice C | Strict individual /36 | Wrong exits lit /36 |','|---|---:|---:|---:|---:|---:|']
    for a in choice_summary:
        if a['arm'].endswith('/choice') or a['arm'].endswith('/frozen_choice'):
            text.append(f"| {a['arm']} | {a['junction_connected']}/36 | {a['prefix']:.3f} | {a['choice']:.3f} | {a['single_strict']}/36 | {a['wrong_exits_lit']}/36 |")
    text += ['','| Strict-choice archive | Goal changes source state at16 /18 | Goal changes junction state at16 /18 | Junction state at64 /18 |','|---|---:|---:|---:|']
    for arm in ('local/prefix/choice','local/choice/choice','evolved/prefix/choice','evolved/choice/choice','evolved/choice/frozen_choice'):
        counts=[]
        for h,field in ((16,'any_source_state'),(16,'junction_changed_channels'),(64,'junction_changed_channels')):
            counts.append(sum(r['aligned'] and bool(r[field]) for r in courses if r['arm']==arm and r['horizon']==h))
        text.append(f"| {arm} | {counts[0]}/18 | {counts[1]}/18 | {counts[2]}/18 |")
    opportunities=read('opportunity_diagnostics.json')
    unavailable=sum(r['local_goal_inputs_both_outside_16_cones'] for r in opportunities)
    ties=sum(any(len(w)>1 for w in r['decision']['allowed']) for r in opportunities)
    detours=sum(any(r['decision']['detours']) for r in opportunities)
    text += ['',f"The final18 regular pairs contain {ties} with multiple valid shortest exits and {detours} with a deceptive detour at the chosen decision. "
        f"For{unavailable}/18, both goal inputs lie beyond16 open edges from every decision-region site. Radius1 rules cannot distinguish those local exit bits by tick16; "
        'at least one goal input is within that radius on the remaining pairs. This is a post-freeze structural opportunity diagnostic, not an accuracy adjustment. '
        'Multirange reads can shorten geometric influence chains but must demonstrate actual useful choice.']
    text += ['', 'Hidden goal-dependent state at a junction is distinct from a correct exit and from a complete route. Fixed-horizon probes ignore ordinary halting, so their rasters are diagnostics. '
        'The saved probe-route audit tests hypothetical tick16 emission separately; it cannot turn a nonhalting normal organism into a solver.','',
        f'![Switched-goal output]({out.name}/visuals/switched_goals.png)','',
        '## Fixed-genome interventions','',
        '| Strict-choice archive | Native J | Goal pulse removed J | Native strict both /18 | Removed /18 |','|---|---:|---:|---:|---:|']
    cm={r['arm'].removesuffix('->flag'):r for r in cs}
    for arm in ('local/prefix/choice','local/choice/choice','evolved/prefix/choice','evolved/choice/choice'):
        a=pm[arm];b=cm[arm];text.append(f"| {arm} | {a['junction']:.4f} | {b['junction']:.4f} | {round(18*a['junction_both'])}/18 | {round(18*b['junction_both'])}/18 |")
    ablated=list(lines(out/'nonlocal_ablation.jsonl.gz'));absummary=[]
    for arm in sorted({r['arm'] for r in ablated}):
        rr=[r for r in ablated if r['arm']==arm];lookup={r['case_id']:r for r in rr}
        minimum=[min(lookup[p['first']]['junction']['score'],lookup[p['second']]['junction']['score']) for p in pairs if p['first'] in lookup and not p['mixed']]
        absummary.append(dict(arm=arm,junction=float(np.mean(minimum)),signal=float(np.mean([r['signal']['score'] for r in rr if r['reachable']])),optimal=sum(r['optimal'] for r in rr)))
    write_json(out/'ablation_summary.json',absummary)
    text += ['','| Multirange archive | Native J | Nonlocal reads removed J | Native source | Removed source | Shortest /42 |','|---|---:|---:|---:|---:|---:|']
    for a in absummary:
        b=pm[a['arm']];text.append(f"| {a['arm']} | {b['junction']:.4f} | {a['junction']:.4f} | {b['signal']:.4f} | {a['signal']:.4f} | {a['optimal']}/42 |")
    ancestry=json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read())
    if ancestry:
        text += ['', '## Validation-only emergence and ancestry','',
            'The validation replay archive equals the preregistered primary choice archive, independently checked against every nomination. Both pressure labels here describe the same evolved genotype trajectory, not separate discoveries. It does not alter breeding or final selections. '
            'Post-freeze replays follow each qualifying archive’s ancestry on its first qualifying validation pair. '
            'The example is selected by validation qualification and cannot establish unseen generalization. Its paired choice survives nonlocal ablation here but disappears without the goal pulse; this is specific to the qualifying case.','',
            '| Condition | First qualifying birth | Parent→child row changes | Ancestry nodes | Final strict both | Normal shortest /2 |',
            '|---|---:|---:|---:|---:|---:|']
        for r in ancestry:
            first=next(n for n in r['nodes'] if n['strict_both']);last=r['nodes'][-1]
            text.append(f"| {r['condition']} | {first['individual']['birth']} | {len(first['gene_row_changes'])} | {len(r['nodes'])} | {last['strict_both']} | {sum(x['optimal'] for x in last['cases'])}/2 |")
        text += ['', 'Row differences are not necessarily individual mutation operations: insertion/deletion can shift subsequent rows. '
            'Birth0 means qualification was already present in the initial genotype. Later parent/child transitions are context-specific and do not isolate which changed row is necessary.','',
            '| Same validation organism | Goal pulse | Nonlocal reads ablated | J | Strict both | Shortest /2 |','|---|---:|---:|---:|---:|---:|']
        for r in ancestry:
            for a in r['interventions']:
                text.append(f"| {r['condition']} | {a['goal_pulse']} | {a['ablate_nonlocal']} | {a['junction']:.4f} | {a['junction_both']} | {sum(x['optimal'] for x in a['cases'])}/2 |")
        text += ['', f'![Validation ancestry]({out.name}/visuals/validation_choice.png)','',
            f"These ancestry/intervention assays add {v['ancestry_reassessed_outputs']} independently reassessed normal outputs across {v['ancestry_nodes']} replayed ancestry nodes, "
            'with their full source probes and cost recorded in `diagnostics.json`. `strict_validation_archive.json` preserves the validation-only genotypes for a fresh continuation.']
    text += ['','Removing the goal pulse retains the static goal flag. Nonlocal ablation returns zero for radius>1 reads while charging attempted reads. '
        'These post-freeze interventions reuse final layouts without reselection; they diagnose dependence, not a separately selected treatment.','',
        '## Real cost and capacity','',
        f"Search with validation/probes: **{env['training_seconds']/60:.2f} minutes**. Main experiment including final accuracy/timing: **{env['elapsed_seconds']/60:.2f} minutes**. "
        f"Main-run peak RSS **{env['max_rss_bytes']/2**20:.1f} MiB**, {env['cpu']}, Python{env['python']}, {env['packages']}. "
        f"Training/selection charged {v['normal_maze_evaluations']:,} normal responses and {v['developmental_probe_runs']:,} source probes, "
        f"with {v['charged_work']:,} logical dispatch-plus-attempted-read units. These are not hardware CPU instruction counts. Conventional solvers’ VM counters are uninstrumented placeholders, not zero hardware work. "
        'Same slots/caps need not yield equal actual work because phenotypes and validation nominee overlap differ.','',
        'Full inference timing includes decoding, initialization, updates and raster emission; fitness/oracle/probe cost is outside these latency samples. '
        'JITs warm matching production signatures.30 repetitions per case, randomized solver order,12 cases/arm across3 replicates. '
        'The table gives the median of case medians and the full sample range; failed paths confer no speed advantage.','',
        '| Arm | Median case median μs | Warm range μs | Correct timed repetitions | Largest inference arrays |','|---|---:|---:|---:|---:|']
    timings=read('timings.json')
    for arm in ('compiled_bfs','compiled_astar','wave_bit',*taskarms):
        rr=[r for r in timings if r['arm']==arm];a=summaries[arm];mem=str(a['largest_array_bytes'])+'B' if a['largest_array_bytes']>=0 else 'unreported'
        text.append(f"| {arm} | {statistics.median(r['median_us'] for r in rr):.2f} | {min(r['min_us'] for r in rr):.2f}–{max(r['max_us'] for r in rr):.2f} | {sum(r['correct'] for r in rr)}/{sum(r['repeats'] for r in rr)} | {mem} |")
    traffic=defaultdict(lambda:defaultdict(int))
    for r in primary:
        if '/' not in r['arm']:continue
        a=traffic[r['arm']];opened=sum(bytes.fromhex(mazes[r['case_id']]['cells_hex']))
        a['completed_open_site_ticks']+=opened*r['steps'];a['logical_state_copy_bytes']+=32*opened*r['steps']
        a['attempted_neighbor_reads']+=r['reads'];a['dispatches']+=r['dispatches'];a['active']+=r['active']
    write_json(out/'inference_traffic.json',traffic)
    text += ['','Each completed open-site tick copies eight uint16 states old→new,32 bytes of logical read/write payload. '
        'This excludes partial ticks, gene/register operations and allocations; caches/compiler optimization change physical DRAM traffic. '
        'State buffers alone are32N bytes; the kernel’s explicit array ceiling is64N+65536. Host RSS includes Python/JIT/logging.','',
        '| Task archive | Completed open-site ticks | Logical copy MiB | Neighbor reads | Dispatches | Active fraction |','|---|---:|---:|---:|---:|---:|']
    for arm in taskarms:
        a=traffic[arm];text.append(f"| {arm} | {a['completed_open_site_ticks']:,} | {a['logical_state_copy_bytes']/2**20:,.1f} | {a['attempted_neighbor_reads']:,} | {a['dispatches']:,} | {a['active']/max(1,a['dispatches']):.3f} |")
    selected=[r for r in structures if r['arm'].endswith('/task')]
    counts=read('mutation_behavior.json')['counts'];totals={k:sum(r.get(k,0) for r in counts.values()) for k in next(iter(counts.values()))}
    write_json(out/'mutation_summary.json',totals)
    text += ['',f"Task genomes contain {min(r['genes'] for r in selected)}–{max(r['genes'] for r in selected)} genes, with conservative output/stop dependency slices "
        f"of {min(r['potential_output_stop_genes'] for r in selected)}–{max(r['potential_output_stop_genes'] for r in selected)} genes. "
        'These are syntactic potential dependencies; semantic redundancy and full-state quiescence can differ. Genome length is not effective complexity.','',
        f"Among {totals['coeval_new_children']:,} newly born children with a parent evaluated on the same training batch, "
        f"{totals['changed_genome']:,} change genotype and {totals['changed_genome_same_behavior']:,} of those match the behavioral fingerprint of normal/probe rasters, status/steps and partial/source/goal scores "
        f"({totals['changed_genome_same_behavior']/max(1,totals['changed_genome']):.1%}). "
        f"Fitness excluding cost is higher for {totals['higher_training_fitness']:,}, lower for {totals['lower_training_fitness']:,}, equal for {totals['equal_training_fitness']:,}. "
        'This conditional subset is not an unbiased neutrality estimate; work/expression counters and hidden trajectories may differ. Preserve these variants.','',
        'The observed cost offers no advantage over conventional solvers. Larger grids increase per-tick state traffic and graph-distance propagation time; '
        'long reads only help if their causal information produces valid output. Capacity, regulation, time and new selection pressures remain testable hypotheses.','',
        '## Verification and reproduction','',
        f"All {v['source_files']} frozen source hashes, prior layout exclusions, {v['new_individuals']:,} new individual lineages, protected variants and shared initial cohorts verify. "
        f"Independently reassessed {v['reassessed_primary_outputs']:,} ordinary, {v['reassessed_paired_outputs']:,} paired, "
        f"{v['reassessed_cross_input_outputs']:,} pulse-removed and {v['reassessed_ablation_outputs']:,} nonlocal-ablated normal outputs. "
        f"Replayed {v['replayed_selected_outputs']} selected normal outputs. Checked {v['training_fitness_checks']:,} fitness records, "
        f"{v['verified_priority_records']:,} priority records,{v['junction_raster_checks']:,} junction rasters and {v['reassessed_training_valid_claims']} valid training claims, "
        f"plus all {v['verified_choice_archives']} strict-choice,{v['verified_task_archives']} task,{v['verified_junction_archives']} junction and{v['verified_balanced_archives']} balanced validation archive maxima. "
        'Complete next populations/RNG, immutable earlier results, all rasters and lossless compressed logs are saved. 112 tests passed before training.','',
        f"Post-freeze diagnostics took {read('diagnostics.json')['elapsed_seconds']:.2f}s, audit {v['elapsed_seconds']:.2f}s and lossless recompression "
        f"{read('storage.json')['elapsed_seconds']:.2f}s. Stored and decoded log hashes are in `storage.json`. "
        'Audit source hashes, cost breakdowns, manifests/labels, environment, protocol and archive provenance are independently inspectable.','',
        '```sh','.venv/bin/python -m pytest -q',
        '.venv/bin/python -m maze_evolution.choice_study --out results/choice_priority_reproduction',
        '.venv/bin/python -m maze_evolution.choice_diagnostics --out results/choice_priority_reproduction',
        '.venv/bin/python -m maze_evolution.choice_audit --out results/choice_priority_reproduction --repack',
        '.venv/bin/python -m maze_evolution.choice_path_diagnostic --out results/choice_priority_reproduction',
        '.venv/bin/python -m maze_evolution.choice_selection_diagnostic --out results/choice_priority_reproduction',
        '.venv/bin/python -m maze_evolution.choice_report --out results/choice_priority_reproduction','```','',
        'Use a fresh directory; historical output directories reject overwrites. Full protocol: `docs/CHOICE_STUDY_V9.md`. '
        'Machine-readable raw results: `results/choice_priority/`. Frozen source revisions/hashes fix this experiment; future continuations must use new modules/seeds.','']
    text += ['## Interpretation and next experiment','',
        'Choice-first priority did not change the evolutionary trajectory in this screen. All six matched pressure pairs have identical ordered genotype populations at every generation and identical final RNG states. '
        'The field was implemented and exercised: each multirange arm recorded 19 strict-both training responses across four active batches, while local arms recorded none. '
        'Unprotected positive genotypes had 10 repeated opportunities, survived unchanged 5 times and produced 40 mutated offspring under either pressure. '
        'All four active pools have the same global best sets; 512 post-hoc matched-seed parent draws also select the same IDs/genotypes. '
        'The new discrete priority was redundant for the observed selection outcomes. This does not establish redundancy in every possible population.','',
        'The bottleneck observed here is transfer across contexts. Qualifying primitives already reproduce, and both pressures discover the same validation-only lineage at birth 3 (retained at birth 5). '
        'It requires the goal pulse on its qualifying 9×9 fork, but survives zeroing nonlocal reads on that example. '
        'All19 strict-both training responses per multirange pressure also have correct incoming source connections and shortest incoming prefixes in the additional entry diagnostic. '
        'Nevertheless selected models solve 0/18 unseen paired choices and 0/42 paired full routes. '
        'The sole long ordinary task success is a frozen nine-edge directional-growth capability whose measured output trajectory does not change when the goal moves.','',
        'A justified next controlled experiment tests a near-to-far goal-distance curriculum against the current minimum-distance training distribution, with the same capacity, protected lineages and common objective. '
        'Start with genuinely source-dependent two-goal decisions where goals are close to the fork, then increase goal-to-fork distance on a fixed preregistered schedule. '
        'Keep validation and final mazes at the harder distances, preserve all known variants and neutral diversity, and use new layouts excluding every inspected corpus. '
        'This tests whether repeated, attainable goal-control subfunctions can compose across distance; it must not insert wavefront rules or routes. '
        'Capacity/regulation/longer evolutionary time remain open hypotheses. A longer run should require reproducible transfer rather than a larger precursor scalar.','']
    target=out.with_suffix('.md');target.write_text('\n'.join(text));visuals(out,manifest,primary,paired)
    print(target)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/choice_priority')
    args=parser.parse_args();report(args.out)
