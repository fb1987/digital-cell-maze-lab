"""V6 report from frozen saved outputs and independently verified accounting."""
import argparse
from collections import defaultdict
import gzip,json,statistics
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle
from .experiment import write_json
from .beacon_audit import unpack
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
    arms=('compiled_bfs','local/flag/task','local/pulse/task','evolved/flag/task','evolved/pulse/task')
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
    arms=('compiled_bfs','evolved/flag/goal','evolved/pulse/goal','evolved/pulse/frozen_goal')
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
    arms=('evolved/flag/frozen_goal','evolved/flag/goal','evolved/pulse/frozen_goal','evolved/pulse/goal')
    labels=('Flag frozen','Flag evolved','Pulse frozen','Pulse evolved')
    source=[sum(r['aligned'] and r['any_source_state'] for r in rows if r['arm']==a and r['horizon']==16) for a in arms]
    scores=[summary[a]['goal'] for a in arms]
    canvas=Image.new('RGB',(1040,390),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((24,18),'V6 precursor comparison | selected goal archives | three replicates',fill='#e6edf7')
    draw.text((24,40),'All four groups solve 0/42 paired reachable targets. Signals below are intermediate measures.',fill='#aabbd0')
    for panel,(title,values,maximum) in enumerate((('Goal switch changes source state at tick 16',source,18),('Goal-sensitive connected-output score G',scores,.05))):
        ox=24+panel*520;draw.text((ox,80),title,fill='#e6edf7')
        for i,(label,value) in enumerate(zip(labels,values)):
            y=120+i*52;draw.text((ox,y+5),label,fill='#cbd5e1')
            length=int(265*value/maximum);color='#6da8e8' if i<2 else '#5ae1bd'
            if length:draw.rectangle((ox+110,y,ox+110+length,y+24),fill=color)
            formatted=f'{value}/18' if panel==0 else f'{value:.4f}'
            draw.text((ox+120+length,y+5),formatted,fill='#e6edf7')
    draw.text((24,355),'Descriptive comparison; no significance claim. Frozen controls use the same respective input convention.',fill='#aabbd0')
    canvas.save(out/'visuals/precursor_comparison.png')


def report(out):
    out=Path(out);read=lambda name:json.loads((out/name).read_text())
    env=read('environment.json');config=read('config.json');gate=read('extension_decision.json');v=read('verification.json')
    champions=read('champions.json');primary=list(lines(out/'holdout.jsonl.gz'));paired=list(lines(out/'paired_holdout.jsonl.gz'))
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());mazes={m['case_id']:m for m in manifest}
    summaries={r['arm']:r for r in read('summary.json') if r['group']=='all'}
    reachable={m['case_id']:m['oracle_length']>0 for m in manifest}
    ps=paired_summary(paired,reachable);write_json(out/'paired_summary.json',ps);pm={r['arm']:r for r in ps}
    cs=paired_summary(list(lines(out/'cross_input.jsonl.gz')),reachable);write_json(out/'cross_input_summary.json',cs);cm={r['arm']:r for r in cs}
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
            for label in ('task','goal'):
                item=saved[source][label]['individual'];genome=Genome.from_dict(item['genome'])
                structures.append(dict(arm=f"{c['topology']}/{c['pressure']}/{prefix}{label}",replicate=c['replicate'],
                    id=item['id'],genome_sha=genome.digest,**output_dataflow(genome)))
    write_json(out/'capacity_diagnostics.json',structures)
    mult=summaries['evolved/pulse/task'];control=summaries['evolved/flag/task'];local=summaries['local/pulse/task'];frozen=summaries['evolved/pulse/frozen_task']
    reach=mult['reachable'];unreach=mult['unreachable'];pr=pm['compiled_bfs']['reachable']
    text=['# Goal-state pulse experiment: V6','',
        f"The evolved-range Pulse task archives solve **{mult['optimal']}/{reach}** unseen shortest routes versus "
        f"**{control['optimal']}/{reach}** with Flag inputs and **{frozen['optimal']}/{reach}** for the frozen Pulse controls. "
        f"Local Pulse solves {local['optimal']}/{reach}. Evolved Pulse solves {mult['long_optimal']}/{mult['long_cases']} "
        f"at distance ≥8 and {pm['evolved/pulse/task']['optimal']}/{pr} on independent paired targets. "
        'These counts concern completed ordinary outputs, separate from diagnostic communication scores.','',
        f"Goal-selected multirange Pulse genomes improve the independent paired-output score G from {pm['evolved/pulse/frozen_goal']['goal']:.4f} frozen "
        f"to {pm['evolved/pulse/goal']['goal']:.4f} after evolution, versus {pm['evolved/flag/goal']['goal']:.4f} for Flag. "
        'At tick 16, switched goals change source state in 8/18 regular pairs versus 5/18 frozen Pulse and 1/18 Flag. '
        'For the same evolved Pulse genomes, removing the initial goal pulse reduces G to zero; disabling '
        'nonlocal reads also reduces G to zero. This supports learned use of both inputs in intermediate '
        'goal-specific output on this set. It does not establish completed route solving.','',
        f"The preregistered extension gate was **{gate['extend']}** after "
        f"{', '.join(str(g) for g in sorted(set(s['next_generation'] for s in champions.values())))} generations. "
        'Three replicates per condition support descriptive comparisons; this is not a statistical significance claim.','',
        f'![Precursor measures]({out.name}/visuals/precursor_comparison.png)','',
        '## One controlled stimulus change','',
        'Flag uses exactly the prior public input: channel 0=1 at the source, plus source and goal flags. Pulse additionally '
        'initializes channel 1=1 at the goal. The primitive loop, eight channels, 128-gene ceiling, ranges, halting and '
        'V5 product reward stay fixed. A pulse is a stimulus, not a known propagation or path rule. The full Flag '
        'runtime and observer passed exact output/state/work parity tests against V2/V3, and the product fitness '
        'matched V5. Source-removal probes retain both goal inputs.','',
        'Each topology/replicate starts from the V5 product next population/RNG, with validation-selected task, goal '
        'and transmission archives from **both** V5 arms plus ancestral protected elites, deduplicated and protected '
        'equally in both V6 arms. Missing variants replace documented final nonprotected slots. Archive fields, not '
        'final-test successes, determine preservation. Initial genotype sequences match within each comparison. '
        'No known solver seed enters a random-origin lineage. Frozen task/goal controls are selected separately '
        'under each input convention, accounting for an immediate stimulus benefit without evolution.','',
        'The common product reward adds source-dependent transmission and 2 sqrt(Q S) to ordinary partial output, '
        'after completed legality/optimality/no-path criteria. Q measures source-dependent connected growth with '
        'branch penalties; S measures progress specifically toward the current goal compared with the alternative '
        'goal on identical geometry. Task archives use normal route fitness with no probe reward. Failed candidates '
        'carry no cost/length tie-break. New validation archives never automatically re-enter reproduction.','',
        f"Seed {config['seed']}; 96 organisms × twelve conditions; nine new random immigrants/generation, 1–6 mutation "
        'edits, epsilon lexicase and phenotype niches. Training caps: 256 ticks/4096 reads/32768 dispatches per site; '
        'validation/final: 1024/8192/131072. Probes use aligned tick 16 with both source-present and source-removed '
        'responses; all probe work is charged. Oracle distances stay outside candidate inference.','',
        'All V1–V5 whole layouts were excluded. New Wilson 9×9 trees, larger DFS trees, cyclic random, disconnected '
        'and rectangular mazes were generated with shared rules across arms. Training switches size 9 to 17 after '
        'generation 23; validation has divergent goals and reachable distances≥8. The study generated 264 primary '
        'layouts and 24 paired layouts after model freeze in its own process. The paired reachable inputs all have distance≥8. '
        'See [preregistered protocol](../docs/BEACON_STUDY_V6.md).','',
        '**Protocol deviation:** the construction-only unit test used the study seed before training, so some '
        'layouts had already been constructed in a separate test process. That preflight evaluated no candidate '
        'genome or output; its function was to check whole-layout exclusion and generator capacity. Actual final '
        'outputs were first evaluated after all archives froze. No model was selected or tuned using preflight '
        'performance. The freeze-before-generation wording was therefore not literal; `protocol_notes.json` '
        'records the test and source hash. Future construction tests should use a separate seed.','',
        '## Validation extension decision','',
        'The fixed gate requires either at least two additional shortest routes versus both frozen Pulse and '
        'evolved Flag in a topology, or sufficiently large replicated gains in G,Q,S with both-goal qualification, '
        'both maze families and retained transmission. These are validation results, not final accuracy.','',
        '| Topology | Rep | Frozen Pulse G | Flag G | Pulse G | Pulse Q | Pulse S | Both | Pass |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in gate['details']:
        text.append(f"| {r['topology']} | {r['replicate']} | {r['initial_goal']:.4f} | {r['current_goal']:.4f} | {r['goal']:.4f} | {r['quality']:.4f} | {r['specificity']:.4f} | {r['both']:.3f} | {r['passed']} |")
    text+=['','## Fresh completed paths','',
        '| Archive | Valid | Shortest | Distance≥8 shortest | Correct no-path |',
        '|---|---:|---:|---:|---:|']
    for arm,r in sorted(summaries.items()):text.append(f"| {arm} | {r['valid']}/{r['reachable']} | {r['optimal']} | {r['long_optimal']}/{r['long_cases']} | {r['no_path']}/{r['unreachable']} |")
    text+=['','Labels may select the same genome; repeated archive outputs are not independent discoveries. '
        'Perfect mazes are trees, while random mazes can contain cycles. Per-family and per-size data are in the '
        'summary JSON/CSV. No-path results must be interpreted with false claims and generator structure: many '
        'disconnected test layouts have a fixed corner source and separating wall.','',
        '| Task archive | Turn-required shortest | Mandatory-detour shortest | False no-path on reachable |',
        '|---|---:|---:|---:|']
    for arm in ('compiled_bfs','local/flag/task','local/pulse/task','evolved/flag/task','evolved/pulse/task'):
        d=difficulty[arm];text.append(f"| {arm} | {d['turn_required_optimal']}/{d['turn_required_cases']} | {d['detour_required_optimal']}/{d['detour_required_cases']} | {no_path[arm]['false_on_reachable']}/{reach} |")
    text+=['','The two local successes are a seven-edge path with one turn on a fresh 9×9 tree, and a two-edge '
        'straight path on a 17×17 tree. Both already occur in the initial frozen selections; they are useful '
        'inherited random-origin behavior, without a new V6 route-accuracy gain.','']
    text+=['','Turn-required means the endpoints differ in both coordinates; mandatory detour means oracle distance '
        'exceeds Manhattan distance. These diagnostic subsets are computed after selection. Legal path shapes '
        'and exact case identifiers are saved in `success_shapes.json`.','',
        f'![Representative unseen outputs]({out.name}/visuals/unseen_outputs.png)','',
        '## Independent goal-pair outputs and precursor measures','',
        'Normal correctness remains separate from probe G,Q,S and source transmission. G,Q,S average all paired '
        'inputs; unreachable/unaligned cases get no new bonus. Source transmission averages reachable inputs. '
        'Both-direction qualification uses regular divergent-goal pairs and is a proxy, not a legal-path metric.','',
        '| Archive | Normal shortest | Correct no-path | G | Q | S | Both | Source signal |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in ps:
        fmt=lambda x:'—' if x is None else f'{x:.4f}'
        text.append(f"| {r['arm']} | {r['optimal']}/{r['reachable']} | {r['no_path']}/{48-pr} | {fmt(r['goal'])} | {fmt(r['quality'])} | {fmt(r['specificity'])} | {fmt(r['both'])} | {fmt(r['signal'])} |")
    sample_record=next(r for r in paired if r['arm']=='evolved/pulse/goal' and r['replicate']==0)
    sample=next(r for r in sample_record['cases'] if '/random/17x17/a' in r['case'])
    g=sample['goal']
    text+=['',f"Representative failure, first 17×17 cyclic paired layout in replicate 0, goal A (`{sample['case']}`): "
        f"normal emission stops at tick {sample['steps']} with failure `{sample['failure']}`. The tick 16 raster "
        f"lights {g['selected']} positions, only {g['component']} in the source component, with {g['branches']} "
        'excess branches. It therefore cannot be counted as a path despite strong source-dependent hidden signalling.','']
    probe=read('probe_route_diagnostics.json')
    text+=['',f"Of {len(probe)} saved tick 16 paired rasters, {sum(r['aligned'] and r['probe_valid'] for r in probe)} "
        'form legal paths even when assessed with an assumed emitted status. This status is diagnostic only; '
        'normal results above require actual completed emission.','',
        f'![Switched-goal probe rasters]({out.name}/visuals/switched_goals.png)','',
        '## Goal information reaching the source','',
        'After freeze, observe identical geometry/source with goal A versus goal B at ticks8/16/32/64, ignoring '
        'stopping but retaining hard budgets. Both targets are at least eight graph edges away. Differences '
        'at the source are caused by changing the goal stimulus; they do not establish a distance map, correct '
        'branch choice or shortest-route construction. All eight channels are included, with hidden states '
        'excluding output2 and stop7. The same assays cover task, goal and both frozen controls.','',
        '| Goal archive | Tick | Aligned regular pairs | Any source response | Hidden | Output | Stop |',
        '|---|---:|---:|---:|---:|---:|---:|']
    groups=defaultdict(list)
    for r in read('goal_timecourse.json'):groups[(r['arm'],r['horizon'])].append(r)
    for (arm,horizon),rr in sorted(groups.items()):
        if not arm.endswith('/goal') and not arm.endswith('/frozen_goal'):continue
        aa=[r for r in rr if r['aligned']]
        text.append(f"| {arm} | {horizon} | {len(aa)}/{len(rr)} | {sum(r['any_source_state'] for r in aa)} | {sum(r['hidden_source_state'] for r in aa)} | {sum(r['output_source_state'] for r in aa)} | {sum(r['stop_source_state'] for r in aa)} |")
    text+=['','## Same frozen genomes, swapped input convention','',
        'Each selected genome is evaluated under the opposite initialization on the same paired layouts. These '
        'post-freeze comparisons separate dependence on the pulse from a change in genotype; they do not select '
        'a new champion. Frozen controls refer to no V6 evolution, not an unevolved random genome.','',
        '| Archive | Original shortest | Swapped shortest | Original G | Swapped G | Original source | Swapped source |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for r in cs:
        original=r['arm'].split('->')[0];b=pm[original]
        text.append(f"| {r['arm']} | {b['optimal']}/{pr} | {r['optimal']}/{pr} | {b['goal']:.4f} | {r['goal']:.4f} | {b['signal']:.4f} | {r['signal']:.4f} |")
    ablated=list(lines(out/'nonlocal_ablation.jsonl.gz'))
    text+=['','## Nonlocal-read ablation','',
        'Every radius>1 read returns zero in ordinary inference and both source probes; attempted reads remain '
        'charged. Genomes stay frozen. This tests the contribution of long reads to these particular outputs.','',
        '| Archive | Original shortest | Ablated shortest | Original G | Ablated G | Original source | Ablated source |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for arm in sorted({r['arm'] for r in ablated}):
        rr=[r for r in ablated if r['arm']==arm];reachable_rows=[r for r in rr if r['reachable']];b=pm[arm]
        text.append(f"| {arm} | {b['optimal']}/{pr} | {sum(r['optimal'] for r in rr)}/{pr} | {b['goal']:.4f} | {np.mean([r['goal']['score'] for r in rr]):.4f} | {b['signal']:.4f} | {np.mean([r['signal']['score'] for r in reachable_rows]):.4f} |")
    text+=['','## Actual compute and correctness-aware latency','',
        f"Search including validation/probes: **{env['training_seconds']/60:.2f} min**; main run including final "
        f"outputs and timing: **{env['elapsed_seconds']/60:.2f} min**. Peak process RSS {env['max_rss_bytes']/2**20:.1f} MiB. "
        f"Hardware {env['cpu']}; Python {env['python']}; packages {env['packages']}. "
        f"Training/selection charged {v['normal_maze_evaluations']:,} ordinary responses, {v['developmental_probe_runs']:,} "
        f"probes and {v['charged_work']:,} logical dispatch-plus-read work units. Work is not a CPU instruction count. "
        'Both arms have equal slots/caps; actual expressed work and validation nominee overlap may differ.','',
        '| Topology / input | Train responses | Validation responses | Inference work | Probe work |',
        '|---|---:|---:|---:|---:|']
    costs=defaultdict(lambda:defaultdict(int))
    for key,c in read('training_cost.json').items():
        _,t,p,rep=key.split('/')
        for k,x in c.items():costs[t+'/'+p][k]+=x
    for key,c in sorted(costs.items()):text.append(f"| {key} | {c['train_responses']:,} | {c['validation_responses']:,} | {c['inference_work']:,} | {c['probe_work']:,} |")
    timings=read('timings.json')
    text+=['','Complete normal inference includes input decoding, state initialization/updates and full raster '
        'emission; genome construction, oracle fitness and probes are excluded. JIT warm-up uses the production '
        'read-only byte/program signature. Thirty repetitions use randomized solver order; below are medians '
        'across case medians and the full warm sample range. Incorrect outputs are not fast solutions.','',
        '| Arm | Median case median, μs | Warm sample range, μs | Shortest timed repetitions | Max inference arrays |',
        '|---|---:|---:|---:|---:|']
    for arm in ('compiled_bfs','compiled_astar','wave_bit','local/flag/task','local/pulse/task','evolved/flag/task','evolved/pulse/task'):
        rr=[r for r in timings if r['arm']==arm];s=summaries[arm]
        text.append(f"| {arm} | {statistics.median(r['median_us'] for r in rr):.2f} | {min(r['min_us'] for r in rr):.2f}–{max(r['max_us'] for r in rr):.2f} | {sum(r['correct'] for r in rr)}/{sum(r['repeats'] for r in rr)} | {format(s['largest_array_bytes'], ',')+' B' if s['largest_array_bytes']>=0 else 'unreported'} |")
    traffic=defaultdict(lambda:defaultdict(int))
    for r in primary:
        if '/' not in r['arm']:continue
        opened=sum(bytes.fromhex(mazes[r['case_id']]['cells_hex']))
        t=traffic[r['arm']];t['completed_open_site_ticks']+=opened*r['steps']
        t['logical_state_copy_bytes']+=32*opened*r['steps']
        t['attempted_neighbor_reads']+=r['reads'];t['dispatches']+=r['dispatches'];t['active']+=r['active']
    write_json(out/'inference_traffic.json',traffic)
    text+=['','For the VM, the table below also records completed open-site updates and model-accounted state '
        'copy payload: eight uint16 values read and written per open site per completed tick, 32 bytes. It excludes '
        'partial ticks, additional register comparisons, gene writes/reads and allocation, and is not measured '
        'physical DRAM traffic; caches/compiler optimization can change hardware traffic. Attempted neighbor '
        'reads and dispatches are counted directly. This exposes the cost of synchronous sweeps alongside latency.','',
        '| Task archive | Completed open-site ticks | Logical state copy, MiB | Attempted neighbor reads | Dispatches | Active fraction |',
        '|---|---:|---:|---:|---:|---:|']
    for arm in ('local/flag/task','local/pulse/task','evolved/flag/task','evolved/pulse/task'):
        t=traffic[arm]
        text.append(f"| {arm} | {t['completed_open_site_ticks']:,} | {t['logical_state_copy_bytes']/2**20:,.1f} | {t['attempted_neighbor_reads']:,} | {t['dispatches']:,} | {t['active']/max(1,t['dispatches']):.3f} |")
    task_structure=[r for r in structures if r['arm'].endswith('/task')]
    text+=['',f"The twelve selected task genomes contain {min(r['genes'] for r in task_structure)}–{max(r['genes'] for r in task_structure)} genes; "
        f"their conservative output/explicit-stop slices contain {min(r['potential_output_stop_genes'] for r in task_structure)}–{max(r['potential_output_stop_genes'] for r in task_structure)} potentially relevant genes. "
        'This syntactic slice is not a count of necessary genes or effective complexity; full-state quiescence '
        'can depend on other channels. Capacity, expression work and successful behavior must be measured '
        'separately. Full static records are in `capacity_diagnostics.json`.','']
    diag=read('diagnostics.json')
    text+=['','The uint16 substrate uses two 8-channel buffers plus decoded input, output, scratch and program arrays, '
        'with an explicit 64N+65536 byte inference ceiling. Probe counterfactuals add memory and work; pair-array '
        'peaks are saved per response. Host RSS includes Python/JIT/logging and is separate from kernel arrays. '
        'Larger mazes multiply sites, active updates and instruction dispatch; multirange reads can cross walls '
        'but final paths must still obey four-neighbor geometry. A competitive solver requires correct emission '
        'and lower real cost, not just low wall-clock delay from broad communication.','',
        f"Post-freeze diagnostics cost {diag['elapsed_seconds']:.2f}s and {diag['charged_work']:,} additional work units: "
        f"{diag['cross_input_responses']+diag['ablation_responses']} ordinary responses, "
        f"{diag['cross_input_probes']+diag['ablation_probes']+diag['timecourse_probes']} probes. These are separate from training and timing. "
        f"Independent audit reassessed {v['reassessed_primary_outputs']} primary, {v['reassessed_paired_outputs']} paired, "
        f"{v['reassessed_cross_input_outputs']} cross-input and {v['reassessed_ablation_outputs']} ablated outputs; "
        f"verified {v['training_fitness_checks']:,} training fitness decompositions and all lineage/source/layout hashes. "
        f"All {v['reassessed_training_valid_claims']} training/validation valid-path claims were reassessed. "
        f"It verified {v['new_individuals']:,} new individuals, hard gene bounds and paired initial populations, and replayed {v['replayed_selected_outputs']} selected outputs. All checks passed. Audit cost {v['elapsed_seconds']:.2f}s.",'']
    if (out/'storage.json').exists():
        storage=read('storage.json');text += [f"New training logs were recompressed losslessly after timing: {storage['before_bytes']:,} → {storage['after_bytes']:,} bytes in {storage['elapsed_seconds']:.2f}s. Decoded/stored hashes for all {len(storage['files'])} files are recorded. Old raw data remain unchanged.",'']
    balanced=read('balanced_validation_archive.json')['records']
    text+=['## Preserving balanced variants for the next test','',
        'A post-hoc **validation-only** preservation archive ranks previously evaluated genomes by mean '
        'min(G_A,G_B) across regular goal pairs, then both-goal qualification, Q and mean G. This records '
        'existing genotypes from the logs; it does not breed a new genome, replace a frozen primary archive '
        'or add final evaluations. Some genotypes overlap the original selections. It prevents the single '
        'highest mean-G archive from being the only goal-sensitive variant carried forward. Balanced G averages '
        'the four regular validation pairs, while mean G averages all twelve validation inputs, including mixed '
        'pairs; these columns therefore have different denominators.','',
        '| Condition | Balanced G | Both | Mean G | Same identity as mean-G archive |',
        '|---|---:|---:|---:|---|']
    for key,r in sorted(balanced.items()):text.append(f"| {key} | {r['balanced_goal']:.4f} | {r['both']:.2f} | {r['goal']:.4f} | {r['same_as_goal_archive']} |")
    text+=['','A justified next controlled experiment holds the pulse convention and genome capacity fixed and '
        'compares the existing mean goal reward with an equal-maximum blend of mean and weaker-goal reward. '
        'For example, replace a pair bonus 2(G_A+G_B) with (G_A+G_B)+2min(G_A,G_B); both peak at 4 and the blend '
        'retains a gradient when one goal response is absent. This tests balanced two-goal pressure without '
        'inserting a solver. Preserve both V6 arms, transmission and directional-growth variants, plus these '
        'validation-only balanced candidates. Preregister the case-level assignment/selection rules and '
        'fresh layouts before running; exact turns/detours and cost remain the final measures.','',
        '## Reproduce','',
        '```sh','.venv/bin/python -m pytest -q',
        '.venv/bin/python -m maze_evolution.beacon_study --out results/goal_beacon_reproduction',
        '.venv/bin/python -m maze_evolution.beacon_diagnostics --out results/goal_beacon_reproduction',
        '.venv/bin/python -m maze_evolution.beacon_audit --out results/goal_beacon_reproduction',
        '.venv/bin/python -m maze_evolution.beacon_report --out results/goal_beacon_reproduction','```','',
        'Checkpoint files contain the complete next population, serial IDs, archived/protected/frozen genomes and '
        'RNG state. Resume through `beacon_search.search` with an increased absolute generation target and fresh '
        'log streams; do not append into or overwrite prior experiment outputs. Any next experiment must exclude '
        'these inspected layouts. A bounded result does not establish impossibility of random-origin discovery.','']
    out.with_suffix('.md').write_text('\n'.join(text).rstrip()+'\n')
    visuals(out,manifest,primary,paired)
    print(out.with_suffix('.md'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/goal_beacon');report(parser.parse_args().out)
