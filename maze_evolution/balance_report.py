"""V7 report from frozen saved outputs and independently verified accounting."""
import argparse
from collections import defaultdict
import gzip,json,statistics
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle
from .experiment import write_json
from .balance_audit import unpack
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
    arms=('compiled_bfs','local/mean/task','local/balanced/task','evolved/mean/task','evolved/balanced/task')
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
    arms=('compiled_bfs','evolved/mean/balanced','evolved/balanced/balanced','evolved/balanced/frozen_balanced')
    canvas=Image.new('RGB',(960,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Switched goals on identical geometry/source | BFS versus tick 16 output raster, without assumed correctness.',fill='#e6edf7')
    for i,case in enumerate((pair['first'],pair['second'])):
        m=lookup[case]
        for j,arm in enumerate(arms):
            if arm=='compiled_bfs':r=next(r['baseline'] for r in paired if r['arm']==arm and 'baseline' in r and r['baseline']['case_id']==case);mask=unpack(r['mask'],m['w']*m['h']);subtitle='Shortest route'
            else:
                record=next(r for r in paired if r['arm']==arm and r['replicate']==0)
                r=next(r for r in record['cases'] if r['case']==case);mask=unpack(r['probe_mask'],m['w']*m['h']);subtitle=f"Tick16: G={r['goal']['score']:.3f}"
            ox,oy=15+j*240,85+i*245
            draw.text((ox,oy-40),arm,fill='#e6edf7');draw.text((ox,oy-22),f"Goal {'A' if i==0 else 'B'} | {subtitle}",fill='#aabbd0')
            grid(draw,ox,oy,m,mask)
    canvas.save(out/'visuals/switched_goals.png')
    rows=json.loads((out/'goal_timecourse.json').read_text())
    summary={r['arm']:r for r in json.loads((out/'paired_summary.json').read_text())}
    arms=('evolved/mean/frozen_balanced','evolved/mean/balanced','evolved/balanced/frozen_balanced','evolved/balanced/balanced')
    labels=('Mean frozen','Mean evolved','Balanced frozen','Balanced evolved')
    source=[sum(r['aligned'] and r['any_source_state'] for r in rows if r['arm']==a and r['horizon']==16) for a in arms]
    scores=[summary[a]['balanced'] for a in arms]
    canvas=Image.new('RGB',(1040,390),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((24,18),'V7 precursor comparison | common balanced archives | three replicates',fill='#e6edf7')
    draw.text((24,40),'Paired shortest counts: '+', '.join(f"{label} {summary[a]['optimal']}/42" for a,label in zip(arms,labels)),fill='#aabbd0')
    for panel,(title,values,maximum) in enumerate((('Goal switch changes source state at tick 16',source,18),('Regular-pair weaker-goal score B',scores,max(.05,1.1*max(scores))))):
        ox=24+panel*520;draw.text((ox,80),title,fill='#e6edf7')
        for i,(label,value) in enumerate(zip(labels,values)):
            y=120+i*52;draw.text((ox,y+5),label,fill='#cbd5e1')
            length=int(265*value/maximum);color='#6da8e8' if i<2 else '#5ae1bd'
            if length:draw.rectangle((ox+110,y,ox+110+length,y+24),fill=color)
            formatted=f'{value}/18' if panel==0 else f'{value:.4f}'
            draw.text((ox+120+length,y+5),formatted,fill='#e6edf7')
    draw.text((24,355),'Descriptive comparison; no significance claim. All groups use the same pulse input convention.',fill='#aabbd0')
    canvas.save(out/'visuals/precursor_comparison.png')


def report(out):
    out=Path(out);read=lambda name:json.loads((out/name).read_text())
    env=read('environment.json');config=read('config.json');gate=read('extension_decision.json');v=read('verification.json')
    champions=read('champions.json');primary=list(lines(out/'holdout.jsonl.gz'));paired=list(lines(out/'paired_holdout.jsonl.gz'))
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());mazes={m['case_id']:m for m in manifest}
    reachable={m['case_id']:m['oracle_length']>0 for m in manifest}
    def paired_stats(records):
        result=paired_summary(records,reachable)
        for r in result:
            rr=[a for a in records if a['arm']==r['arm'] and 'baseline' not in a]
            r['balanced']=float(np.mean([a['balanced'] for a in rr])) if rr else None
        return result
    ps=paired_stats(paired);write_json(out/'paired_summary.json',ps);pm={r['arm']:r for r in ps}
    cs=paired_stats(list(lines(out/'cross_input.jsonl.gz')));write_json(out/'cross_input_summary.json',cs)
    summaries={r['arm']:r for r in read('summary.json') if r['group']=='all'}
    shapes=[];difficulty=defaultdict(lambda:defaultdict(int));no_path=defaultdict(lambda:defaultdict(int))
    from cellular_maze_lab import neighbors
    def shape(arm,rep,case,mask,optimal,split):
        m=mazes[case];p=m['start'];previous=-1;directions=[]
        while p!=m['goal']:
            q=next(q for q in neighbors(p,m['w'],m['h']) if mask[q] and q!=previous)
            directions.append(q-p);previous,p=p,q
        shapes.append(dict(arm=arm,replicate=rep,case=case,edges=len(directions),
            turns=sum(a!=b for a,b in zip(directions,directions[1:])),optimal=optimal,split=split))
    for r in primary:
        no_path[r['arm']]['correct']+=r['no_path_correct'];no_path[r['arm']]['false_on_reachable']+=bool(r['reachable'] and r['status']=='no_path')
        m=mazes[r['case_id']];sx,sy=m['start']%m['w'],m['start']//m['w'];gx,gy=m['goal']%m['w'],m['goal']//m['w']
        for label,condition in (('turn_required',sx!=gx and sy!=gy),('detour_required',r['edges']>abs(sx-gx)+abs(sy-gy))):
            if r['reachable'] and condition:
                difficulty[r['arm']][label+'_cases']+=1;difficulty[r['arm']][label+'_optimal']+=r['optimal']
        if r['valid_path'] and '/' in r['arm']:shape(r['arm'],r['replicate'],r['case_id'],unpack(r['mask'],m['w']*m['h']),r['optimal'],'primary')
    for record in paired:
        if 'baseline' in record:continue
        for r in record['cases']:
            if r['valid']:shape(record['arm'],record['replicate'],r['case'],unpack(r['mask'],mazes[r['case']]['w']*mazes[r['case']]['h']),r['optimal'],'paired')
    write_json(out/'success_shapes.json',shapes);write_json(out/'difficulty_summary.json',difficulty);write_json(out/'no_path_diagnostics.json',no_path)
    from .regulatory import Genome
    from .range_audit import output_dataflow
    structures=[]
    for saved in champions.values():
        c=saved['config']
        for source,prefix in (('archives',''),('frozen','frozen_')):
            for label in ('task','balanced'):
                item=saved[source][label]['individual'];genome=Genome.from_dict(item['genome'])
                structures.append(dict(arm=f"{c['topology']}/{c['pressure']}/{prefix}{label}",replicate=c['replicate'],
                    id=item['id'],genome_sha=genome.digest,**output_dataflow(genome)))
    write_json(out/'capacity_diagnostics.json',structures)
    mult=summaries['evolved/balanced/task'];control=summaries['evolved/mean/task'];local=summaries['local/balanced/task'];frozen=summaries['evolved/balanced/frozen_task']
    reach=mult['reachable'];pr=pm['compiled_bfs']['reachable'];unreach=mult['unreachable']
    b=pm['evolved/balanced/balanced'];m=pm['evolved/mean/balanced'];f=pm['evolved/balanced/frozen_balanced']
    text=['# Balanced two-goal pressure: V7','',
        f"Multirange task archives solve **{mult['optimal']}/{reach}** unseen shortest routes under Balanced pressure versus "
        f"**{control['optimal']}/{reach}** under Mean and **{frozen['optimal']}/{reach}** frozen. Local Balanced solves "
        f"{local['optimal']}/{reach}. Multirange Balanced solves {mult['long_optimal']}/{mult['long_cases']} at distance≥8 "
        f"and {pm['evolved/balanced/task']['optimal']}/{pr} on independent paired targets. These are completed ordinary outputs.",'',
        f"The common balanced archives score **B={b['balanced']:.4f}** under Balanced pressure, versus **{m['balanced']:.4f}** "
        f"under Mean and **{f['balanced']:.4f}** frozen on independent regular goal pairs. Their mean individual-goal scores "
        f"are G={b['goal']:.4f}, {m['goal']:.4f} and {f['goal']:.4f}. B averages the weaker goal within each regular pair; "
        'G averages all paired inputs, including mixed cases. These are intermediate measures with different denominators, '
        'not path-correctness or significance claims.','',
        f"Both-direction qualification is {round(18*b['both'])}/18 under multirange Balanced pressure, "
        f"{round(18*m['both'])}/18 Mean and {round(18*f['both'])}/18 frozen. The gain is concentrated in replicate 1; "
        'replicate 0 retains its frozen weaker-goal score and replicate 2 declines slightly on this new set. '
        'Local Mean has the higher B score. This does not establish a universally better pressure or a solver.','',
        f"The extension gate was **{gate['extend']}** after "
        f"{', '.join(str(g) for g in sorted(set(s['next_generation'] for s in champions.values())))} generations. "
        'Three replicates per condition support a descriptive controlled comparison.','',
        f'![Precursor comparison]({out.name}/visuals/precursor_comparison.png)','',
        '## What changed','',
        'All organisms use the unchanged V6 goal-pulse runtime, eight uint16 channels and at most 128 typed genes. '
        'The treatment changes only goal reward: Mean gives case i 2G_i; Balanced gives G_i+min(G_A,G_B). '
        'Pair totals are 2(G_A+G_B) versus (G_A+G_B)+2min(G_A,G_B), both at most 4. With one absent goal response '
        'the stronger side retains half its previous credit, while improving the weaker side becomes more valuable. '
        'Mixed reachable/unreachable pairs retain 2G_i in both arms, avoiding an impossible two-route requirement.','',
        'Normal validity, optimality and no-path utility precede shaping. Partial output and source transmission '
        'terms are unchanged; incomplete routes carry no size/cost tie-break. Probe horizon 16, source ablation, '
        'primitive semantics and hard limits are identical. BFS and oracle graph distances remain outside inference.','',
        'The base is each V6 Pulse next population and RNG. Both V6 arms contribute their validation task/goal/source '
        'archives, protected ancestors and supplemental balanced variants. Missing genotypes replace documented last '
        'nonprotected slots. Both V7 arms share the same initial genotype sequence, RNG and fixed protected variants. '
        'All prior raw populations remain intact. No parent is chosen using final-test accuracy and no known solver '
        'is inserted into a random-origin lineage.','',
        'Validation uses Mean scoring in both arms. A common balanced archive ranks regular-pair weaker-goal score, '
        'both-direction qualification, Q, mean G, validity and optimality. Both arms nominate training balanced leaders '
        'alongside the same overall/source/goal/Q/S leaders and niche rule. Task archives use normal route fitness '
        'without probe rewards. Frozen controls are initial common task/balanced selections. New validation archives '
        'never automatically re-enter reproduction. Mean-goal/source/Q/S archives remain saved as validation diagnostics; '
        'final selections here are task and balanced archives. Absolute V6/V7 archive scores are not a pressure-only comparison.','',
        f"Seed {config['seed']}; twelve conditions, 96 organisms each, local/evolvable ranges × Mean/Balanced × three replicates. "
        'Training uses rotating size 9 pairs, then 17 after generation 23; fixed validation has six pairs/replicate, '
        'reachable distances≥8. All V1–V6 whole layouts are excluded. Size 9 perfect mazes use Wilson trees; larger '
        'trees use DFS, alongside cyclic random, disconnected and rectangular cases. The construction preflight '
        'uses seed 1074, separate from this study. All models froze before final layouts and outputs were generated. '
        'See [preregistered protocol](../docs/BALANCE_STUDY_V7.md).','',
        '## Validation continuation gate','',
        'The prior numeric gate now targets the common balanced archive B, with Balanced as candidate and Mean '
        'as control. It requires at least two additional shortest validation routes versus both frozen and control '
        'on a topology, or sufficiently large replicated gains in B,Q,S,both-direction qualification, both maze '
        'families and retained transmission. Transmission or mean G alone cannot trigger extension.','',
        '| Topology | Rep | Frozen B | Mean B | Balanced B | Q | S | Both | Pass |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in gate['details']:text.append(f"| {r['topology']} | {r['replicate']} | {r['initial_goal']:.4f} | {r['current_goal']:.4f} | {r['goal']:.4f} | {r['quality']:.4f} | {r['specificity']:.4f} | {r['both']:.2f} | {r['passed']} |")
    text+=['','## Fresh completed outputs','',
        f"Primary set:264 layouts, {reach} reachable and {unreach} unreachable. Paired set:24 layouts/48 targets, "
        f"{pr} reachable at distance≥8 and {48-pr} unreachable. All arms share inputs. Repeated labels may select "
        'the same genome and are not independent discoveries. Per-family and size summaries remain in JSON/CSV.','',
        '| Archive | Valid | Shortest | Distance≥8 shortest | Correct no-path |',
        '|---|---:|---:|---:|---:|']
    for arm,r in sorted(summaries.items()):text.append(f"| {arm} | {r['valid']}/{r['reachable']} | {r['optimal']} | {r['long_optimal']}/{r['long_cases']} | {r['no_path']}/{r['unreachable']} |")
    text+=['','| Task archive | Turn-required shortest | Mandatory-detour shortest | False no-path on reachable |','|---|---:|---:|---:|']
    for arm in ('compiled_bfs','local/mean/task','local/balanced/task','evolved/mean/task','evolved/balanced/task'):
        d=difficulty[arm];text.append(f"| {arm} | {d['turn_required_optimal']}/{d['turn_required_cases']} | {d['detour_required_optimal']}/{d['detour_required_cases']} | {no_path[arm]['false_on_reachable']}/{reach} |")
    text+=['','Turn-required means endpoints differ in both coordinates; mandatory detour means oracle distance exceeds '
        'Manhattan distance. Perfect mazes are trees and cyclic cases need separate evidence. Disconnected results '
        'also need caution: the family has a separating-wall and fixed-corner-source bias. These subsets describe '
        'already selected outputs and never retune genomes.','']
    if shapes:
        text += [f"Across repeated candidate archive outputs, legal paths span {min(r['edges'] for r in shapes)}–{max(r['edges'] for r in shapes)} edges; "
            f"{sum(r['turns']>0 for r in shapes)} contain turns. Full case/shape records are saved. Compare frozen controls "
            'before attributing a success to V7 evolution.','']
    text += [f'![Unseen outputs]({out.name}/visuals/unseen_outputs.png)','',
        '## Independent paired outputs and probes','',
        'B averages 18 regular pairs;G,Q,S average 48 targets; source signal averages 42 reachable targets. '
        'Both-direction qualification is an intermediate output threshold, separate from complete path legality.','',
        '| Archive | Normal shortest | Correct no-path | B | G | Q | S | Both | Source |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in ps:
        fmt=lambda x:'—' if x is None else f'{x:.4f}'
        text.append(f"| {r['arm']} | {r['optimal']}/{r['reachable']} | {r['no_path']}/{48-pr} | {fmt(r['balanced'])} | {fmt(r['goal'])} | {fmt(r['quality'])} | {fmt(r['specificity'])} | {fmt(r['both'])} | {fmt(r['signal'])} |")
    proxy_replicates=[]
    for r in paired:
        if 'baseline' in r or not (r['arm'].endswith('/balanced') or r['arm'].endswith('/frozen_balanced')):continue
        proxy_replicates.append({k:r[k] for k in ('arm','replicate','id','balanced','goal','both','quality','specificity','signal')})
    write_json(out/'replicate_proxy_summary.json',proxy_replicates)
    text += ['','| Multirange archive | Rep | B | G | Qualified regular pairs |','|---|---:|---:|---:|---:|']
    for r in proxy_replicates:
        if not r['arm'].startswith('evolved/'):continue
        text.append(f"| {r['arm']} | {r['replicate']} | {r['balanced']:.4f} | {r['goal']:.4f} | {round(6*r['both'])}/6 |")
    probe=read('probe_route_diagnostics.json')
    text += ['',f"Of {len(probe)} saved tick 16 paired rasters, {sum(r['aligned'] and r['probe_valid'] for r in probe)} form legal paths "
        'even assuming an emitted status. This diagnostic status never replaces actual normal stopping.','']
    sample_record=next(r for r in paired if r['arm']=='evolved/balanced/balanced' and r['replicate']==0)
    sample=next(r for r in sample_record['cases'] if '/random/17x17/a' in r['case']);g=sample['goal']
    text += [f"Representative first 17×17 cyclic paired case in replicate 0, goal A (`{sample['case']}`): normal status "
        f"`{sample['status']}`, outcome `{sample['failure']}`. The tick 16 raster lights {g['selected']} positions with "
        f"{g['component']} in the source component and {g['branches']} excess branches. The saved raster and BFS route "
        'are shown below; signaling scores do not override path correctness.','',
        f'![Switched goals]({out.name}/visuals/switched_goals.png)','',
        '## Bounded goal-information timecourse','',
        'Fixed genomes observe goal A/B on identical geometry/source, at ticks 8/16/32/64 with stopping disabled '
        'and hard budgets intact. All targets lie at least eight graph edges away. Goal-caused source-state '
        'differences are communication evidence; they do not prove a distance map or correct branch choice. '
        'All eight source channels are compared; hidden excludes output channel 2 and stop channel 7.','',
        '| Balanced archive | Tick | Aligned | Any source response | Hidden | Output concentration | Stop |',
        '|---|---:|---:|---:|---:|---:|---:|']
    groups=defaultdict(list)
    for r in read('goal_timecourse.json'):groups[(r['arm'],r['horizon'])].append(r)
    for (arm,horizon),rr in sorted(groups.items()):
        if not arm.endswith('/balanced') and not arm.endswith('/frozen_balanced'):continue
        aa=[r for r in rr if r['aligned']]
        text.append(f"| {arm} | {horizon} | {len(aa)}/{len(rr)} | {sum(r['any_source_state'] for r in aa)} | {sum(r['hidden_source_state'] for r in aa)} | {sum(r['output_source_state'] for r in aa)} | {sum(r['stop_source_state'] for r in aa)} |")
    junctions=read('junction_diagnostics.json');jg=defaultdict(list)
    for r in junctions:jg[r['arm']].append(r)
    text += ['','## Goal-dependent output choices at a junction','',
        'This diagnostic was added during training, before final output inspection, and never affects selection. '
        'On each perfect-tree pair, find the last shared vertex of the two unique oracle routes and the distinct '
        'next neighbor required by each goal. At tick 16, a correct local choice requires the source-connected '
        'output to include that junction and its wanted neighbor while excluding the other goal’s neighbor. '
        'Both goals must make their respective choice for a pair to qualify. All geometry/oracle work occurs '
        'only in this post-freeze analysis; no extra candidate inference is run. This is a local readout diagnostic, '
        'not a claim of a completed path, and some source-to-junction distances can exceed the probe horizon.','',
        '| Balanced archive | Aligned tree pairs | Both choices correct | Junction connected under both goals | Same three output bits |',
        '|---|---:|---:|---:|---:|']
    for arm,rr in sorted(jg.items()):
        if not arm.endswith('/balanced') and not arm.endswith('/frozen_balanced'):continue
        aa=[r for r in rr if r['aligned']]
        text.append(f"| {arm} | {len(aa)}/{len(rr)} | {sum(r['both_correct'] for r in aa)} | {sum(all(r['junction_source_connected']) for r in aa)} | {sum(r['same_local_output'] for r in aa)} |")
    tested=jg['evolved/balanced/balanced'];aa=[r for r in tested if r['aligned']]
    blocked=sum(all(r['junction_source_connected']) and r['local_output_bits'][0]==[True,True,True] and r['local_output_bits'][1]==[True,True,True] for r in aa)
    text += ['',f"The multirange Balanced selection makes both correct choices in {sum(r['both_correct'] for r in aa)}/{len(aa)} tree pairs. "
        f"In {blocked}, the source reaches the junction under both goals and all three readout positions are lit "
        'under both: the fork remains open in both directions. Thus the current two-goal progress proxy can improve '
        'while a specific junction choice remains absent. A different subset also fails to reach the junction by '
        'tick 16; the saved distance metadata distinguishes that from an incorrect choice.','']
    text += ['','## Frozen pulse-removal and nonlocal-read interventions','',
        'Pulse removal uses the same selected genotype with the original goal flag retained, removing only initial '
        'goal channel 1 activation. Source-present/removed probes use that same convention. This tests learned '
        'dependence on the extra stimulus, without retraining or reselection.','',
        '| Archive | Original B | Pulse removed B | Original G | Pulse removed G | Removed shortest |',
        '|---|---:|---:|---:|---:|---:|']
    for r in cs:
        original=r['arm'].split('->')[0];a=pm[original]
        text.append(f"| {original} | {a['balanced']:.4f} | {r['balanced']:.4f} | {a['goal']:.4f} | {r['goal']:.4f} | {r['optimal']}/{pr} |")
    ablated=list(lines(out/'nonlocal_ablation.jsonl.gz'));pair_defs=[r for r in read('pairs.json') if r['first'].startswith('test_pairs/') and not r['mixed']]
    text += ['','Every radius>1 read returns zero in both ordinary inference and source probes, with attempted reads '
        'charged. This preserves genomes and all other stimuli.','',
        '| Archive | Original B | Nonlocal ablated B | Original source | Ablated source | Ablated shortest |',
        '|---|---:|---:|---:|---:|---:|']
    ablation_summary=[]
    for arm in sorted({r['arm'] for r in ablated}):
        rr=[r for r in ablated if r['arm']==arm];lookup={r['case_id']:r for r in rr}
        minima=[min(lookup[p['first']]['goal']['score'],lookup[p['second']]['goal']['score']) for p in pair_defs if p['first'] in lookup]
        reachable_rows=[r for r in rr if r['reachable']];a=pm[arm]
        value=dict(arm=arm,balanced=float(np.mean(minima)),signal=float(np.mean([r['signal']['score'] for r in reachable_rows])),optimal=sum(r['optimal'] for r in rr))
        ablation_summary.append(value)
        text.append(f"| {arm} | {a['balanced']:.4f} | {value['balanced']:.4f} | {a['signal']:.4f} | {value['signal']:.4f} | {value['optimal']}/{pr} |")
    write_json(out/'ablation_summary.json',ablation_summary)
    text += ['','## Cost, latency, memory and capacity','',
        f"Search including validation/probes took **{env['training_seconds']/60:.2f} min**; main run including final "
        f"outputs/timing **{env['elapsed_seconds']/60:.2f} min**. Peak process RSS **{env['max_rss_bytes']/2**20:.1f} MiB**, "
        f"on {env['cpu']}, Python {env['python']}, packages {env['packages']}. Training/selection used "
        f"{v['normal_maze_evaluations']:,} normal responses and {v['developmental_probe_runs']:,} probes, charging "
        f"{v['charged_work']:,} dispatch-plus-attempted-read units. These are logical work, not CPU instructions. "
        'Slots and hard caps match; actual phenotype work and validation nominee overlap may differ.','',
        '| Condition | Train responses | Validation responses | Inference work | Probe work |','|---|---:|---:|---:|---:|']
    costs=defaultdict(lambda:defaultdict(int))
    for key,r in read('training_cost.json').items():
        _,t,p,rep=key.split('/')
        for k,x in r.items():costs[t+'/'+p][k]+=x
    for key,r in sorted(costs.items()):text.append(f"| {key} | {r['train_responses']:,} | {r['validation_responses']:,} | {r['inference_work']:,} | {r['probe_work']:,} |")
    timings=read('timings.json')
    text += ['','Normal timing includes decoding, stimulus/state initialization, updates and full raster emission; '
        'genome construction, oracle fitness and developmental probes are excluded. JIT warm-up matches production '
        'read-only dtype/signature. Thirty repetitions use randomized solver order; the table reports medians '
        'across 12 case medians plus the full warm sample range. Wrong outputs never count as faster solutions.','',
        '| Arm | Median case median, μs | Warm range, μs | Shortest timed repetitions | Max inference arrays |',
        '|---|---:|---:|---:|---:|']
    for arm in ('compiled_bfs','compiled_astar','wave_bit','local/mean/task','local/balanced/task','evolved/mean/task','evolved/balanced/task'):
        rr=[r for r in timings if r['arm']==arm];a=summaries[arm];mem=format(a['largest_array_bytes'],',')+'B' if a['largest_array_bytes']>=0 else 'unreported'
        text.append(f"| {arm} | {statistics.median(r['median_us'] for r in rr):.2f} | {min(r['min_us'] for r in rr):.2f}–{max(r['max_us'] for r in rr):.2f} | {sum(r['correct'] for r in rr)}/{sum(r['repeats'] for r in rr)} | {mem} |")
    traffic=defaultdict(lambda:defaultdict(int))
    for r in primary:
        if '/' not in r['arm']:continue
        opened=sum(bytes.fromhex(mazes[r['case_id']]['cells_hex']));a=traffic[r['arm']]
        a['completed_open_site_ticks']+=opened*r['steps'];a['logical_state_copy_bytes']+=32*opened*r['steps']
        a['attempted_neighbor_reads']+=r['reads'];a['dispatches']+=r['dispatches'];a['active']+=r['active']
    write_json(out/'inference_traffic.json',traffic)
    text += ['','Each completed open-site update logically copies eight uint16 states old→new: 32 bytes of read/write '
        'payload. The following accounting excludes partial ticks, extra comparisons/register operations, gene '
        'reads/writes and allocation; caches/compiler optimization can change physical DRAM traffic. State buffers '
        'alone occupy 32N bytes; the complete kernel has an explicit 64N+65536 byte ceiling. Probes add work and '
        'counterfactual memory; host RSS separately includes Python/JIT and logging.','',
        '| Task archive | Completed open-site ticks | Logical state copy, MiB | Attempted neighbor reads | Dispatches | Active fraction |',
        '|---|---:|---:|---:|---:|---:|']
    for arm in ('local/mean/task','local/balanced/task','evolved/mean/task','evolved/balanced/task'):
        a=traffic[arm];text.append(f"| {arm} | {a['completed_open_site_ticks']:,} | {a['logical_state_copy_bytes']/2**20:,.1f} | {a['attempted_neighbor_reads']:,} | {a['dispatches']:,} | {a['active']/max(1,a['dispatches']):.3f} |")
    selected=[r for r in structures if r['arm'].endswith('/task')]
    text += ['',f"The twelve task genomes contain {min(r['genes'] for r in selected)}–{max(r['genes'] for r in selected)} genes. "
        f"Conservative output/explicit-stop slices contain {min(r['potential_output_stop_genes'] for r in selected)}–{max(r['potential_output_stop_genes'] for r in selected)} potentially relevant genes. "
        'This is syntactic dependency, not dynamic necessity or effective computational capacity; full-state '
        'quiescence can also depend on other channels. Increasing maze size multiplies sweep and expression work. '
        'Long reads may cross walls, while emitted paths still must obey four-neighbor maze geometry.','']
    mutation=read('mutation_behavior.json');mc=defaultdict(lambda:defaultdict(int))
    for key,r in mutation['counts'].items():
        _,t,p,rep=key.split('/')
        for k,x in r.items():mc[t+'/'+p][k]+=x
    text += ['','### Mutation effects on matched training batches','',
        'For newly born children whose parent is also evaluated on that same rotating batch, compare the saved '
        'normal/probe binary rasters, normal status/steps and partial/source/goal metrics. Hidden trajectories '
        'can differ despite matching these records. This is a conditional subset of mutations, not an unbiased '
        'neutrality estimate. Fitness comparison omits the final cost tie-break. The diagnostic was specified '
        'during training before final inspection and adds no inference runs.','',
        '| Condition | Matched new children | Genotype changed | Same recorded behavior | Changed genotype, same behavior | Higher / lower training fitness |',
        '|---|---:|---:|---:|---:|---:|']
    for key,r in sorted(mc.items()):
        text.append(f"| {key} | {r['coeval_new_children']} | {r['changed_genome']} | {r['same_recorded_behavior']} | {r['changed_genome_same_behavior']} | {r['higher_training_fitness']} / {r['lower_training_fitness']} |")
    diag=read('diagnostics.json')
    total_final=sum(v[k] for k in ('reassessed_primary_outputs','reassessed_paired_outputs','reassessed_cross_input_outputs','reassessed_ablation_outputs'))
    text += ['','## Verification and reproducibility','',
        f"All {total_final:,} final/diagnostic normal outputs were independently reassessed, with {v['raster_goal_checks']} "
        f"saved-raster goal checks and {v['training_fitness_checks']:,} training/validation fitness decompositions. "
        f"The audit also checked every balanced reward/metric, {v['verified_balanced_archives']} archive maxima, "
        f"{v['new_individuals']:,} lineage identities, all source/layout hashes, hard bounds and common initial/frozen "
        f"controls. It replayed {v['replayed_selected_outputs']} selected responses and reassessed all "
        f"{v['reassessed_training_valid_claims']} training/validation legal-path claims. Audit cost {v['elapsed_seconds']:.2f}s; all checks passed.",'',
        f"Post-freeze diagnostics cost {diag['elapsed_seconds']:.2f}s, {diag['cross_input_responses']+diag['ablation_responses']} ordinary responses, "
        f"{diag['cross_input_probes']+diag['ablation_probes']+diag['timecourse_probes']} probes and {diag['charged_work']:,} logical work units, "
        'separate from training and headline latency. Core source and protocol hashes were saved before training; '
        'genome SHA256 was saved before constructing final layouts. V1–V6 source/raw results remain unchanged.','']
    if (out/'storage.json').exists():
        st=read('storage.json');text += [f"New logs were losslessly repacked {st['before_bytes']:,}→{st['after_bytes']:,} bytes in {st['elapsed_seconds']:.2f}s. "
            f"Decoded and stored hashes for all {len(st['files'])} files are preserved.",'']
    text += ['## Next controlled experiment','',
        'Test explicit credit for source-connected, goal-dependent junction choices against the current Balanced '
        'pressure, keeping pulse input, genome capacity and inference limits fixed. Use rotating fresh pairs whose '
        'targets require different next neighbors at a shared decision point; include deceptive detours so direct '
        'goal bearing cannot solve the task. Compute allowed shortest-branch labels only in fitness, never in '
        'candidate inference, and require the chosen branch to belong to the source-connected output while the '
        'wrong branch is suppressed. For cyclic mazes, allow every valid shortest first step instead of rewarding '
        'an arbitrary BFS tie. These implementation/credit details must be preregistered before the next run.','',
        'Preserve both Mean and Balanced lineages, source-signal and directional-growth variants, common balanced '
        'archives, neutral diversity and population/RNG states. The final measure remains completed shortest '
        'paths on fresh mazes, including turns/detours, plus real cost; a junction precursor alone is insufficient. '
        'Capacity stayed fixed in V7, so the capacity hypothesis remains open.','',
        '## Reproduce','']
    text += ['```sh','.venv/bin/python -m pytest -q',
        '.venv/bin/python -m maze_evolution.balance_study --out results/repeat_balance',
        '.venv/bin/python -m maze_evolution.balance_diagnostics --out results/repeat_balance',
        '.venv/bin/python -m maze_evolution.balance_audit --out results/repeat_balance',
        '.venv/bin/python -m maze_evolution.balance_report --out results/repeat_balance','```','',
        'Complete next populations/RNG and all validation archives remain in the checkpoints. Resume with an '
        'increased absolute generation target and new log streams; never overwrite earlier experiment outputs. '
        'Next experiments must exclude all inspected V1–V7 layouts. Random-origin discovery remains central; '
        'bounded failure is not an impossibility result.','']
    out.with_suffix('.md').write_text('\n'.join(text).rstrip()+'\n')
    visuals(out,manifest,primary,paired);print(out.with_suffix('.md'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/balanced_goal');report(parser.parse_args().out)
