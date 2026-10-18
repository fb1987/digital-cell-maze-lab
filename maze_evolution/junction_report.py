"""V8 report generated from frozen outputs and independently checked accounting."""
import argparse
from collections import defaultdict
import gzip,json,statistics
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle
from .experiment import write_json
from .junction_audit import unpack
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
    arms=('compiled_bfs','local/balanced/task','local/junction/task','evolved/balanced/task','evolved/junction/task')
    canvas=Image.new('RGB',(1200,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Unseen ordinary outputs | green: output; blue: source; pink: goal. First size17 case per family, replicate 0.',fill='#e6edf7')
    for i,m in enumerate(selected):
        for j,arm in enumerate(arms):
            r=next(r for r in primary if r['case_id']==m['case_id'] and r['arm']==arm)
            ox,oy=15+j*240,85+i*245
            draw.text((ox,oy-40),arm,fill='#e6edf7');draw.text((ox,oy-22),m['family']+' | '+('shortest' if r['optimal'] else r['failure']),fill='#aabbd0')
            grid(draw,ox,oy,m,unpack(r['mask'],m['w']*m['h']))
    canvas.save(out/'visuals/unseen_outputs.png')
    lookup={m['case_id']:m for m in manifest}
    pairs=json.loads((out/'pairs.json').read_text())
    pair=next(p for p in pairs if '/r0/' in p['first'] and '/17x17/' in p['first'] and '/random/' in p['first'] and p['first'].startswith('test_pairs/'))
    arms=('compiled_bfs','evolved/balanced/junction','evolved/junction/junction','evolved/junction/frozen_junction')
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
        child=nodes[index];parent=nodes[max(0,index-1)];lookup={m['case_id']:m for m in manifest}
        canvas=Image.new('RGB',(1040,320),'#111827');draw=ImageDraw.Draw(canvas)
        draw.text((15,12),'Validation precursor | first strict choice in saved ancestry | green: output; blue: source; pink: goal; gold: decision.',fill='#e6edf7')
        for j,(node,goal_index) in enumerate(((parent,0),(child,0),(parent,1),(child,1))):
            r=node['cases'][goal_index];m=lookup[r['case']];ox=15+j*260;oy=95
            draw.text((ox,48),('Parent' if j%2==0 else 'First qualifying child')+(' | goal A' if goal_index==0 else ' | goal B'),fill='#e6edf7')
            draw.text((ox,68),f"Tick16 J={r['junction']['score']:.3f}; strict={r['junction']['strict']}",fill='#aabbd0')
            grid(draw,ox,oy,m,unpack(r['probe_mask'],m['w']*m['h']))
            v=record['decision']['vertex'];x=ox+10*(v%m['w']);y=oy+10*(v//m['w']);draw.rectangle((x,y,x+9,y+9),outline='#ffd46a',width=2)
        draw.text((15,290),'This is a selected validation example, not unseen route success. Whole normal outputs remain independently assessed.',fill='#aabbd0')
        canvas.save(out/'visuals/validation_choice.png')
    rows=json.loads((out/'goal_timecourse.json').read_text())
    summary={r['arm']:r for r in json.loads((out/'paired_summary.json').read_text())}
    arms=('evolved/balanced/frozen_junction','evolved/balanced/junction','evolved/junction/frozen_junction','evolved/junction/junction')
    labels=('Balanced frozen','Balanced evolved','Junction frozen','Junction evolved')
    source=[sum(r['aligned'] and r['any_source_state'] for r in rows if r['arm']==a and r['horizon']==16) for a in arms]
    scores=[summary[a]['junction'] for a in arms]
    canvas=Image.new('RGB',(1040,390),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((24,18),'V8 precursor comparison | common junction archives | three replicates',fill='#e6edf7')
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


def confirmation_report(out):
    from PIL import Image,ImageDraw
    out=Path(out);read=lambda name:json.loads((out/name).read_text())
    rows=read('summary.json');env=read('environment.json');v=read('verification.json')
    interactions=json.loads(gzip.open(out/'interaction.json.gz','rt').read())
    text=['# Frozen fork-choice confirmation: V8A','',
        'Two evolved, random-origin variants make source-dependent, goal-dependent fork choices on selected validation pairs. '
        'Both lose those choices when either the goal pulse or nonlocal reads is removed. '
        'On the new confirmation corpus, **both variants make correct choices under both goals on 0/12 pairs and complete 0/24 routes**. '
        'Their roots/parents also score 0/12 and 0/24. The confirmation therefore finds no transferred solver or paired-choice advantage.','',
        'The second validation primitive requires two cooperating changes relative to its immediate parent: swapping instruction rows27/60, '
        'and redirecting row66 from scratch register63 to43. The swap moves a neighbor-count instruction and a nonlocal minimum read. '
        'Neither change group alone produces the strict paired choice on this validation example; the combined child does. '
        'This establishes a context-specific interaction between these two changes. It does not establish a general regulatory strategy or identify each individual row as necessary.','',
        '## Fresh confirmation','',
        'This exploratory confirmation was registered after V8’s primary results and ancestry inspection, before generating its own new corpus. '
        'No training or model reselection follows. Root, pre-qualification parent and final strict-choice variant are frozen from validation ancestry. '
        'Identical parent/root genotypes share aliases and one evaluation. All five distinct genotypes see the same12 new layouts/24 inputs: '
        '9/17/33 ×tree/cyclic ×two layouts, all reachable at distance ≥8 with near-source disjoint-choice junctions and tied shortest exits allowed. '
        'Even indices require a deceptive detour. Seed2026101807; every V1–V8 layout excluded. This is a selected two-lineage confirmation, not replicated population evidence.','',
        '| Lineage | Roles | Weaker-choice J | Strict both /12 | Valid /24 | Shortest /24 |','|---|---|---:|---:|---:|---:|']
    for r in rows:text.append(f"| {r['condition']} | {', '.join(r['roles'])} | {r['junction']:.4f} | {r['strict_both']}/12 | {r['valid']}/24 | {r['optimal']}/24 |")
    text += ['', 'BFS completes 24/24 confirmation routes. The new variants’ partial-choice scores do not improve over their roots here. '
        'All rasters, branch labels and frozen model IDs/hashes are retained. V8’s primary accuracy and extension decision remain unchanged.','',
        '## Selected validation interaction','',
        '| Instruction swap | Register redirection | J | Strict both goals | Normal shortest /2 |','|---|---|---|---|']
    for r in interactions:
        tests=[(False,False,r['parent']),(True,False,r['trials'][0]),(False,True,r['trials'][1]),(True,True,r['child'])]
        for swap,redirect,a in tests:
            score=a['junction'];strict=a.get('strict_both',a.get('junction_both'))
            text.append(f"| {swap} | {redirect} | {score:.4f} | {bool(strict)} | {sum(x['optimal'] for x in a['cases'])}/2 |")
        (out/'visuals').mkdir(exist_ok=True)
        canvas=Image.new('RGB',(840,430),'#111827');draw=ImageDraw.Draw(canvas)
        draw.text((20,15),'Cooperating regulatory changes on one selected validation fork',fill='#e6edf7')
        draw.text((20,40),'The child chooses both goals correctly here; both changes are required in this parent context.',fill='#aabbd0')
        draw.text((210,80),'No instruction swap',fill='#e6edf7');draw.text((490,80),'Instruction swap',fill='#e6edf7')
        for swap,redirect,a in tests:
            x=200+280*swap;y=115+125*redirect;strict=bool(a.get('strict_both',a.get('junction_both')))
            draw.rectangle((x,y,x+250,y+100),fill='#17584e' if strict else '#273449')
            draw.text((x+20,y+18),f"J={a['junction']:.4f}",fill='#e6edf7')
            draw.text((x+20,y+45),'Correct under both goals' if strict else 'No paired correct choice',fill='#e6edf7')
        draw.text((20,145),'Register unchanged',fill='#e6edf7');draw.text((20,270),'Register redirected',fill='#e6edf7')
        draw.text((20,390),'Fresh confirmation: 0/12 paired choices, 0/24 complete routes. This interaction has not generalized.',fill='#aabbd0')
        canvas.save(out/'visuals/cooperating_changes.png')
    text += ['', f'![Cooperating changes]({out.name}/visuals/cooperating_changes.png)','',
        'The readout is a fixed16-tick source-dependent fork-choice assay, not a correctly halted whole path. '
        'The four-cell comparison tests two groups of edits. Other cooperating changes and different contexts remain possible.','',
        '## Cost, checks and next experiment','',
        f"Run took {env['elapsed_seconds']:.2f}s and verification {v['elapsed_seconds']:.2f}s, peak RSS{env['max_rss_bytes']/2**20:.1f}MiB. "
        f"{env['normal_responses']} normal candidate responses and{env['probe_runs']} source probes charged{env['charged_work']:,} dispatch-plus-attempted-read units, "
        f"plus{env['baseline_responses']} BFS responses. The auditor independently checks{v['verified_normal_outputs']} normal outputs and junction masks, "
        'BFS correctness, model/source/input hashes and whole-layout exclusion. VM instruction/read counters do not instrument BFS hardware work.','',
        'Preserve both strict-choice variants and their ancestors. A justified next controlled experiment protects them in a common starting cohort and compares '
        'strict paired-choice-first selection with the current prefix-weighted reward, at unchanged capacity. Correct full routes stay ahead of all precursor scores. '
        'The reason is concrete: V8’s archive can prefer broad prefix growth over a correct choice on one context. '
        'Test transfer across rotating fork contexts and fresh independent mazes before spending an hour on extension. '
        'Heritable capacity/regulation/time remain open hypotheses; this cooperative validation example supports investigating them without establishing a solver.','',
        'Protocol: `docs/JUNCTION_CONFIRMATION_V8A.md`. Raw data: `results/junction_confirmation/`. '
        'Future studies must also exclude this confirmation manifest. Preserve V8’s original data.','']
    out.with_suffix('.md').write_text('\n'.join(text))
    return text


def report(out,confirmation=None):
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
            for label in ('task','junction'):
                item=saved[source][label]['individual'];g=Genome.from_dict(item['genome'])
                structures.append(dict(arm=f"{c['topology']}/{c['pressure']}/{prefix}{label}",replicate=c['replicate'],id=item['id'],genome_sha=g.digest,**output_dataflow(g)))
    write_json(out/'capacity_diagnostics.json',structures)
    current=pm['evolved/junction/junction'];control=pm['evolved/balanced/junction'];frozen=pm['evolved/junction/frozen_junction']
    task=summaries['evolved/junction/task'];ct=summaries['evolved/balanced/task'];ft=summaries['evolved/junction/frozen_task']
    text=['# Source-dependent junction choices: V8','',
        f"Multirange task archives complete **{task['optimal']}/{task['reachable']}** unseen shortest paths with Junction pressure, "
        f"versus **{ct['optimal']}/{ct['reachable']}** with Balanced and **{ft['optimal']}/{ft['reachable']}** frozen. "
        f"Junction solves **{task['long_optimal']}/{task['long_cases']}** at distance ≥8 and **{pm['evolved/junction/task']['optimal']}/42** paired reachable targets. "
        f"Compiled BFS, A* and wavefront complete {pm['compiled_bfs']['optimal']}/42 paired and {summaries['compiled_bfs']['optimal']}/{task['reachable']} ordinary routes. "
        'Correctness remains the primary measure; no competitive speedup is established.','',
        f"The common junction archive has held-out weaker-choice score **J={current['junction']:.4f}** under Junction pressure, "
        f"**{control['junction']:.4f}** under Balanced and **{frozen['junction']:.4f}** frozen. Strict correct choices under both switched goals "
        f"are **{round(18*current['junction_both'])}/18**, **{round(18*control['junction_both'])}/18** and **{round(18*frozen['junction_both'])}/18**, respectively. "
        'J includes partial source-dependent prefix credit; it is not route correctness. Three replicates support a descriptive comparison, without a significance claim.','',
        f"The preregistered extension gate was **{gate['extend']}** after {sorted({s['next_generation'] for s in champions.values()})} generations. "
        'A negative bounded experiment does not establish impossibility of random-origin discovery.','',
        f'![Precursor comparison]({out.name}/visuals/precursor_comparison.png)','',
        '## Controlled comparison and provenance','',
        'The unchanged V6 VM uses eight uint16 channels,128 bounded typed genes, source channel0 and goal channel1 pulses, output2 and stop7. '
        'Local and evolvable-range treatments have identical capacity and budgets. BFS labels are restricted to generation/fitness; candidate inference receives only maze/source/goal inputs. '
        'The only pressure change within V8 is Balanced G_i+minG versus Junction J_i+minJ. Both maxima are 2 per case. Mixed pairs keep2G. '
        'Ordinary correctness/optimality/no-path utility precede shaping, and unfinished genomes have no cost or length penalty.','',
        'J=.25R+.75C: R measures the source-connected, source-dependent shortest prefix beyond distance1. C rewards one desired shortest exit at a source-connected junction, '
        'with wrong exits suppressed and the chosen exit off under source removal. Strict choice requires all these exit conditions; both goals must choose correctly. '
        'All tied shortest neighbors are accepted individually on cyclic grids. Lighting multiple valid alternatives still forms a branch and is penalized. '
        'A high prefix score alone cannot open the extension gate.','',
        'Both arms fork the same V7 Balanced next population/RNG and protect validation-selected task, balanced, goal and transmission variants plus protected ancestors '
        'from both V7 Balanced and Mean. Missing genotypes replace last nonprotected slots; no final performance selects parents. Rich random immigrants and neutral diversity continue. '
        'Both arms nominate the same seven leaders/niche rule; validation uses the common Balanced objective. The junction archive uses mean regular-pair minJ, '
        'then strict-both, balanced G score, validity and optimality. Matching initial archives are frozen no-evolution controls. '
        'New validation archives do not automatically breed. Full populations, RNG and lineage remain available.','',
        f"The preregistration commit is `{env['parent_revision']}`; model freeze SHA256 is `{env['champions_sha256']}`. "
        f"Final generation follows the model freeze. Seed{config['seed']}, independent construction seed1084; all {env['previous_layouts']} V1–V7 layouts excluded. "
        'Primary evaluation uses264 ordinary layouts; the paired set uses24 additional layouts/48 inputs, with42 reachable goals≥8 and6 unreachable. '
        'V8 regular pairs require a shared shortest prefix ending at source distance2..8, goals≥4 edges beyond it and disjoint shortest exit sets. '
        'Even pair indices require a misleading Manhattan bearing for at least one goal; odd indices have no extra requirement. '
        'Both V8 arms share this sampling change. V8 versus V7 therefore changes environments as well as pressure. '
        'Full construction feasibility through192 generations was checked on a different seed before training.','',
        '## Completed unseen outputs','',
        '| Arm | Valid / reachable | Shortest | Distance≥8 shortest | Correct no-path /48 | False no-path |',
        '|---|---:|---:|---:|---:|---:|']
    for arm,a in sorted(summaries.items()):
        text.append(f"| {arm} | {a['valid']}/{a['reachable']} | {a['optimal']} | {a['long_optimal']}/{a['long_cases']} | {a['no_path']}/48 | {no_path[arm]['false_on_reachable']} |")
    text += ['','| Task archive | Turn-required shortest | Mandatory-detour shortest | Paired shortest /42 |','|---|---:|---:|---:|']
    taskarms=[f'{t}/{p}/task' for t in ('local','evolved') for p in ('balanced','junction')]
    for arm in taskarms:
        a=difficulty[arm];text.append(f"| {arm} | {a['turn_required_optimal']}/{a['turn_required_cases']} | {a['detour_required_optimal']}/{a['detour_required_cases']} | {pm[arm]['optimal']}/42 |")
    successes=[r for r in shapes if not '/frozen_' in r['arm']]
    text += ['',f"Selected current task/junction successes span {min((r['edges'] for r in successes),default=0)}–{max((r['edges'] for r in successes),default=0)} edges "
        f"and at most {max((r['turns'] for r in successes),default=0)} turns. Full successful shapes are in `success_shapes.json`; a success can be inherited or supplied by common endpoint-aware halting. "
        'It is not automatically an evolved goal-guided algorithm. Per-size/family results and all failures are in the raw summary/output records.','',
        f'![Ordinary unseen outputs]({out.name}/visuals/unseen_outputs.png)','',
        '## Paired decisions and communication','',
        '| Arm | Weaker-choice J | Strict both /18 | Old balanced B | Mean G | Source transmission | Paired shortest /42 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for a in ps:
        if a['junction'] is not None:text.append(f"| {a['arm']} | {a['junction']:.4f} | {round(18*a['junction_both'])}/18 | {a['balanced']:.4f} | {a['goal']:.4f} | {a['signal']:.4f} | {a['optimal']}/42 |")
    text += ['','B=min of old G scores within each regular pair; G averages all inputs, including mixed ones. J averages regular pairs only. Denominators differ. '
        'Every regular final pair is eligible for the new decision assay, unlike V7’s post-training tree-only diagnostic.','',
        '| Multirange junction archive | Replicate | J | Strict both /6 | Mean G |','|---|---:|---:|---:|---:|']
    for p in ('balanced','junction'):
        for rep in range(3):
            r=next(r for r in paired if r['arm']==f'evolved/{p}/junction' and r['replicate']==rep)
            text.append(f"| {p} | {rep} | {r['junction']:.4f} | {round(6*r['junction_both'])}/6 | {r['goal']:.4f} |")
    jf=read('junction_factors.json')
    text += ['', '| Training pressure/topology | Source-connected decisions | Positive choice C | Strict individual | Strict both pairs |',
        '|---|---:|---:|---:|---:|']
    for t in ('local','evolved'):
        for p in ('balanced','junction'):
            entries=[v for k,v in jf.items() if k.startswith(f'junction/{t}/{p}/') and k.endswith('/train')]
            total=lambda key:sum(x.get(key,0) for x in entries)
            text.append(f"| {t}/{p} | {total('source_connected_junction')}/{total('eligible_cases')} | {total('positive_choice')} | {total('strict_choice')} | {total('strict_both_pairs')}/{total('regular_pairs')} |")
    text += ['', 'These counts include repeated genomes and rotating training cases. They diagnose the selection landscape, not independent discoveries or unseen success.']
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
    text += ['','| Junction archive | Connected junction /36 goals | Mean prefix R | Mean choice C | Strict individual /36 | Wrong exits lit /36 |','|---|---:|---:|---:|---:|---:|']
    for a in choice_summary:
        if a['arm'].endswith('/junction') or a['arm'].endswith('/frozen_junction'):
            text.append(f"| {a['arm']} | {a['junction_connected']}/36 | {a['prefix']:.3f} | {a['choice']:.3f} | {a['single_strict']}/36 | {a['wrong_exits_lit']}/36 |")
    text += ['','| Junction archive | Goal changes source state at16 /18 | Goal changes junction state at16 /18 | Junction state at64 /18 |','|---|---:|---:|---:|']
    for arm in ('local/balanced/junction','local/junction/junction','evolved/balanced/junction','evolved/junction/junction','evolved/junction/frozen_junction'):
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
        '| Junction archive | Native J | Goal pulse removed J | Native strict both /18 | Removed /18 |','|---|---:|---:|---:|---:|']
    cm={r['arm'].removesuffix('->flag'):r for r in cs}
    for arm in ('local/balanced/junction','local/junction/junction','evolved/balanced/junction','evolved/junction/junction'):
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
            'A supplemental archive preserves the strongest strict-both validation variants by strict-both, J, B and G, without changing current training, extension gates or frozen final selections. '
            'This diagnostic was planned during training before inspecting final outputs. Replay each qualifying archive’s ancestry on its first qualifying validation pair. '
            'The example is selected by validation qualification and cannot establish unseen generalization.','',
            '| Condition | First qualifying birth | Parent→child row changes | Ancestry nodes | Final strict both | Normal shortest /2 |',
            '|---|---:|---:|---:|---:|---:|']
        for r in ancestry:
            first=next(n for n in r['nodes'] if n['strict_both']);last=r['nodes'][-1]
            text.append(f"| {r['condition']} | {first['individual']['birth']} | {len(first['gene_row_changes'])} | {len(r['nodes'])} | {last['strict_both']} | {sum(x['optimal'] for x in last['cases'])}/2 |")
        text += ['', 'Row differences are not necessarily individual mutation operations: insertion/deletion can shift subsequent rows. '
            'Parent/child replays establish the transition along that lineage; they do not isolate which changed row is necessary.','',
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
        f"{v['junction_raster_checks']:,} junction rasters and {v['reassessed_training_valid_claims']} valid training claims, "
        f"plus all {v['verified_junction_archives']} junction and{v['verified_balanced_archives']} balanced validation archive maxima. "
        'Complete next populations/RNG, immutable earlier results, all rasters and lossless compressed logs are saved. 106 tests passed before training.','',
        f"Post-freeze diagnostics took {read('diagnostics.json')['elapsed_seconds']:.2f}s, audit {v['elapsed_seconds']:.2f}s and lossless recompression "
        f"{read('storage.json')['elapsed_seconds']:.2f}s. Stored and decoded log hashes are in `storage.json`. "
        'Audit source hashes, cost breakdowns, manifests/labels, environment, protocol and archive provenance are independently inspectable.','',
        '```sh','.venv/bin/python -m pytest -q',
        '.venv/bin/python -m maze_evolution.junction_study --out results/junction_choice_reproduction',
        '.venv/bin/python -m maze_evolution.junction_diagnostics --out results/junction_choice_reproduction',
        '.venv/bin/python -m maze_evolution.junction_audit --out results/junction_choice_reproduction --repack',
        '.venv/bin/python -m maze_evolution.junction_report --out results/junction_choice_reproduction','```','',
        'Use a fresh directory; historical output directories reject overwrites. Full protocol: `docs/JUNCTION_STUDY_V8.md`. '
        'Machine-readable raw results: `results/junction_choice/`. Frozen source revisions/hashes fix this experiment; future continuations must use new modules/seeds.','']
    text += ['## Interpretation and next experiment','',
        'This screen finds no unseen paired-choice or long-route advantage from Junction pressure. '
        'It does find two narrow validation primitives with source-dependent choices under switched goals. '
        'One arises after an instruction reorder and a scratch-register redirection cooperate. '
        'The main mean-J archive misses that second primitive because broad prefix growth can rank higher across the whole set. '
        'These observations motivate preserving useful regulatory subfunctions; they do not establish general routing.','',
        'The next controlled test should protect both validation primitives in the same initial cohorts, then compare strict paired-choice-first selection with current prefix-weighted selection. '
        'Keep normal route correctness primary, preserve neutral diversity, hold capacity/input/caps fixed and require transfer on fresh layouts. '
        'Larger capacity and longer evolution remain hypotheses to test after a reproducible transfer signal; no known solver should enter these lineages.','']
    if confirmation:
        confirmation=Path(confirmation);confirmation_report(confirmation)
        text += [f"An exploratory [V8A confirmation]({confirmation.name}.md) tested both validation variants and their roots/parents on 12 additional fresh layouts. "
            'Neither variant makes strict choices under both goals on any pair (0/12) or completes a route (0/24); no reselection follows. '
            'Two mutation groups cooperate on the original validation example: neither the instruction swap alone nor register redirection alone suffices. '
            'This is narrow regulatory cooperation without demonstrated generalization. The confirmation has its own preregistration, model freeze, seeds, costs and audit.','']
    target=out.with_suffix('.md');target.write_text('\n'.join(text));visuals(out,manifest,primary,paired)
    print(target)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/junction_choice');parser.add_argument('--confirmation')
    args=parser.parse_args();report(args.out,args.confirmation)
