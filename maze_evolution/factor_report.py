"""V5 report from frozen evidence; no selection or parameter changes."""
import argparse
from collections import defaultdict
import gzip,json,statistics
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle
from .experiment import write_json
from .factor_audit import unpack
from .regulatory import Genome
from .signal_audit import lines


def paired_summary(records,reachable_cases):
    grouped=defaultdict(list);proxies=defaultdict(list)
    for r in records:
        if 'baseline' in r:
            grouped[r['arm']].append(r['baseline']);continue
        proxies[r['arm']].append(r)
        grouped[r['arm']].extend(r['cases'])
    result=[]
    for arm,cases in sorted(grouped.items()):
        baseline='case_id' in cases[0]
        reachable=sum(r['reachable'] for r in cases) if baseline else sum(reachable_cases[r['case']] for r in cases)
        result.append(dict(arm=arm,reachable=reachable,optimal=sum(r['optimal'] for r in cases),
            valid=sum(r['valid_path' if baseline else 'valid'] for r in cases),
            no_path=sum(r['no_path_correct' if baseline else 'no_path'] for r in cases),
            goal=float(np.mean([r['goal'] for r in proxies[arm]])) if not baseline else None,
            quality=float(np.mean([r['quality'] for r in proxies[arm]])) if not baseline else None,
            specificity=float(np.mean([r['specificity'] for r in proxies[arm]])) if not baseline else None,
            both=float(np.mean([r['both'] for r in proxies[arm]])) if not baseline else None,
            signal=float(np.mean([r['signal'] for r in proxies[arm]])) if not baseline else None))
    return result


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
    arms=('compiled_bfs','local/product/task','local/curriculum/task','evolved/product/task','evolved/curriculum/task')
    canvas=Image.new('RGB',(1200,520),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Unseen normal outputs | green: emitted raster; blue: source; pink: goal. First size17 case per family, replicate0.',fill='#e6edf7')
    for i,m in enumerate(selected):
        for j,arm in enumerate(arms):
            r=next(r for r in primary if r['case_id']==m['case_id'] and r['arm']==arm)
            ox,oy=15+j*240,85+i*245
            draw.text((ox,oy-40),arm,fill='#e6edf7');draw.text((ox,oy-22),m['family']+' | '+('shortest' if r['optimal'] else r['failure']),fill='#aabbd0')
            grid(draw,ox,oy,m,unpack(r['mask'],m['w']*m['h']))
    canvas.save(out/'visuals/unseen_outputs.png')
    lookup={m['case_id']:m for m in manifest}
    pair_defs=[next(p for p in json.loads((out/'pairs.json').read_text()) if '/r0/' in p['first'] and '/17x17/' in p['first'] and f'/{family}/' in p['first'] and p['first'].startswith('test_pairs/')) for family in ('perfect','random')]
    record=next(r for r in paired if r['arm']=='evolved/curriculum/goal' and r['replicate']==0)
    canvas=Image.new('RGB',(960,520),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Same geometry/source, switched goal | BFS route versus goal-selected tick16 raster. First size17 pairs, replicate0.',fill='#e6edf7')
    for i,p in enumerate(pair_defs):
        for j,case in enumerate((p['first'],p['second'])):
            m=lookup[case];base=next(r['baseline'] for r in paired if r['arm']=='compiled_bfs' and 'baseline' in r and r['baseline']['case_id']==case)
            r=next(r for r in record['cases'] if r['case']==case)
            for column,mask,label in ((j,unpack(base['mask'],m['w']*m['h']),'BFS goal '+('A' if j==0 else 'B')),
                                     (j+2,unpack(r['probe_mask'],m['w']*m['h']),f"Goal {'A' if j==0 else 'B'} tick16: {r['goal']['score']:.3f}")):
                ox,oy=15+column*240,85+i*245;draw.text((ox,oy-40),label,fill='#e6edf7')
                draw.text((ox,oy-22),m['family'],fill='#aabbd0');grid(draw,ox,oy,m,mask)
    canvas.save(out/'visuals/switched_goals.png')


def turned_visual(out,manifest):
    from PIL import Image,ImageDraw
    d=json.loads((out/'turned_path_diagnostic.json').read_text());prefix=json.loads((out/'goal_prefix_diagnostic.json').read_text())
    before=next(r['goals'][0] for r in d['ancestry'] if r['id']==prefix['parent']['id'])
    after=next(r['goals'][0] for r in d['ancestry'] if r['id']==prefix['first_successful_child']['id'])
    other=d['ancestry'][-1]['goals'][1]
    rotated=next(r['output'] for r in d['rotations'] if r['rotation_clockwise_degrees']==90 and r['goal_label']=='a')
    mazes={m['case_id']:m for m in manifest};a=mazes[d['case']]
    cells=np.rot90(np.frombuffer(bytes.fromhex(a['cells_hex']),dtype=np.uint8).reshape(9,9),-1).copy()
    rotate=lambda p:(p%9)*9+(8-p//9)
    rotation={**a,'cells_hex':cells.tobytes().hex(),'start':rotate(a['start']),'goal':rotate(a['goal'])}
    panels=[('Parent at generation37','Read budget exhausted',before,a),
        ('Child at generation38','10 edges, 3 turns, shortest',after,a),
        ('Final child: switched goal','Read budget exhausted',other,mazes[other['case_id']]),
        ('Final child: rotated90deg','Read budget exhausted',rotated,rotation)]
    canvas=Image.new('RGB',(1040,275),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Selected isolated success: mutation and orientation diagnostics. Green: output; blue: source; pink: goal.',fill='#e6edf7')
    for column,(title,subtitle,row,m) in enumerate(panels):
        ox,oy=15+260*column,85;draw.text((ox,oy-40),title,fill='#e6edf7');draw.text((ox,oy-22),subtitle,fill='#aabbd0')
        mask=unpack(row['mask'],81)
        for p,opened in enumerate(bytes.fromhex(m['cells_hex'])):
            color='#172235' if not opened else '#5ae1bd' if mask[p] else '#45536a'
            if p==m['start']:color='#72b6ff'
            if p==m['goal']:color='#ff6584'
            x,y=p%9,p//9;draw.rectangle((ox+x*18,oy+y*18,ox+(x+1)*18-1,oy+(y+1)*18-1),fill=color)
    canvas.save(out/'visuals/turned_path_diagnostic.png')


def report(out):
    out=Path(out);read=lambda name:json.loads((out/name).read_text())
    env=read('environment.json');config=read('config.json');gate=read('extension_decision.json');verification=read('verification.json')
    champions=read('champions.json');primary=list(lines(out/'holdout.jsonl.gz'));paired=list(lines(out/'paired_holdout.jsonl.gz'))
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());mazes={m['case_id']:m for m in manifest}
    summaries={r['arm']:r for r in read('summary.json') if r['group']=='all'}
    ps=paired_summary(paired,{m['case_id']:m['oracle_length']>0 for m in manifest})
    write_json(out/'paired_summary.json',ps);pm={r['arm']:r for r in ps}
    shapes=[];difficulty=defaultdict(lambda:defaultdict(int));no_path=defaultdict(lambda:defaultdict(int))
    from cellular_maze_lab import neighbors
    for r in primary:
        no_path[r['arm']]['correct']+=r['no_path_correct']
        no_path[r['arm']]['false_on_reachable']+=bool(r['reachable'] and r['status']=='no_path')
        m=mazes[r['case_id']];sx,sy=m['start']%m['w'],m['start']//m['w'];gx,gy=m['goal']%m['w'],m['goal']//m['w']
        for label,condition in (('turn_required',sx!=gx and sy!=gy),('detour_required',r['edges']>abs(sx-gx)+abs(sy-gy))):
            if r['reachable'] and condition:
                difficulty[r['arm']][label+'_cases']+=1;difficulty[r['arm']][label+'_optimal']+=r['optimal']
        if not r['valid_path'] or '/' not in r['arm']:continue
        mask=unpack(r['mask'],m['w']*m['h']);p=m['start'];previous=-1;directions=[]
        while p!=m['goal']:
            q=next(q for q in neighbors(p,m['w'],m['h']) if mask[q] and q!=previous)
            directions.append(q-p);previous,p=p,q
        shapes.append(dict(arm=r['arm'],replicate=r['replicate'],case=r['case_id'],edges=len(directions),
            turns=sum(a!=b for a,b in zip(directions,directions[1:])),optimal=r['optimal']))
    write_json(out/'success_shapes.json',shapes);write_json(out/'difficulty_summary.json',difficulty)
    write_json(out/'no_path_diagnostics.json',no_path)
    identical=[]
    for topology in ('local','evolved'):
        for rep in range(3):
            checkpoints=[read(f'checkpoints/factor_{topology}_{p}_{rep}.json') for p in ('product','curriculum')]
            digests=lambda saved:[Genome.from_dict(i['genome']).digest for i in saved['population']]
            identical.append(dict(topology=topology,replicate=rep,identical=digests(checkpoints[0])==digests(checkpoints[1])))
    write_json(out/'paired_populations.json',identical)
    phase_groups=defaultdict(lambda:defaultdict(float))
    for key,values in read('training_phases.json').items():
        _,topology,pressure,rep,phase=key.split('/')
        for k,v in values.items():phase_groups[(topology,pressure,phase)][k]+=v
    cost_groups=defaultdict(lambda:defaultdict(int))
    for key,values in read('training_cost.json').items():
        _,topology,pressure,rep=key.split('/')
        for k,v in values.items():cost_groups[(topology,pressure)][k]+=v
    mult=summaries['evolved/curriculum/task'];control=summaries['evolved/product/task'];local=summaries['local/curriculum/task']
    text=['# Factorized reward curriculum: V5','',
        f"Final multirange task archives solve **{mult['optimal']}/{mult['reachable']}** shortest routes under curriculum "
        f"versus **{control['optimal']}/{control['reachable']}** under product pressure. Local curriculum solves "
        f"{local['optimal']}/{local['reachable']}. These are completed ordinary outputs; probe scores below are separate. "
        f"Multirange curriculum solves {mult['long_optimal']}/{mult['long_cases']} at distance>=8 and "
        f"{pm['evolved/curriculum/task']['optimal']}/42 independent paired reachable targets.",'',
        f"On the independent switched-goal set, goal-selected multirange archives have mean conjunction score "
        f"{pm['evolved/curriculum/goal']['goal']:.4f} under curriculum versus {pm['evolved/product/goal']['goal']:.4f} "
        f"under product pressure; local scores are {pm['local/curriculum/goal']['goal']:.4f} versus "
        f"{pm['local/product/goal']['goal']:.4f}. Both-direction qualification rates are "
        f"{pm['evolved/curriculum/goal']['both']:.3f} multirange and {pm['local/curriculum/goal']['both']:.3f} local "
        'under curriculum. These are three-replicate descriptive comparisons, not a significance claim.','',
        '## Controlled continuation','',
        f"Root {config['seed']}; twelve conditions,96 organisms each, "
        f"{', '.join(str(g) for g in sorted(set(s['next_generation'] for s in champions.values())))} additional generations. "
        f"The preregistered continuation gate was **{gate['extend']}**. Six V4 goal-pressure populations and RNG states "
        'were forked into matched product/curriculum arms. Both protect the inherited V3 signalling elite and the '
        'V4 goal archive, deduplicated by genotype. Missing archive genotypes replace a documented last non-protected '
        'slot equally in both arms. No ancestor was chosen by final-test performance, and no known solver entered a lineage.','',
        'The runtime, eight state channels,64 registers and128-gene ceiling are unchanged. Training inference caps are '
        '256 ticks,4096 attempted reads/site and32768 dispatches/site; validation/final caps1024 /8192 /131072. '
        'Both arms pay for the same ordinary inference and two source-present/removed tick16 observer runs per response. '
        'All oracle/path/distance operations remain outside candidate inference.','',
        'Let Q be source-dependent connected-output quality with a branch penalty, S goal-specific progress, and '
        'G=sqrt(Q*S). Product adds2G throughout. Curriculum addsQ+S for generations0–15, blends linearly to2G '
        'during16–31, and uses exactly2G thereafter. Both bonuses share the maximum2, but the separate sum deliberately '
        'gives more credit away from equal factors. Unreachable/unaligned pairs receive zero bonus. This compares '
        'factorization plus schedule; a constant additive arm would be needed to separate those effects.','',
        'Valid routes, optimality and no-path utility precede shaping. Failed outputs carry no cost tie-break. '
        'Validation always uses the product reward. Task archives use common ordinary-route fitness without any '
        'probe reward; goal/source/quality/specificity archives use their named validation statistic. Training overall '
        'and factor leaders are nominated identically in both arms. New V5 validation archives never automatically '
        'enter reproduction. Frozen controls are selected from the initial populations on the same new validation set.','',
        'Training uses two rotating divergent-goal pairs per generation, size9 initially and17 after generation23, '
        'all reachable targets at distance>=8. One mixed disconnected pair replaces the cyclic pair every fourth '
        'generation. Fixed validation has six pairs/replicate. All size9 perfect splits use Wilson spanning trees '
        'from the outset; larger trees retain DFS. Whole layouts from V1–V4 are excluded, and only intentional '
        'goal pairs share a layout. This environment change and added archive nominees apply equally to both arms; '
        'absolute V4/V5 scores are not an objective-only comparison. See the [protocol](../docs/FACTOR_STUDY_V5.md).','',
        '## Validation extension decision','',
        'Thresholds are exactly V4\'s: at least two additional optimal validation routes versus both frozen/product '
        'controls in a topology, or sufficiently large goal/quality/specificity gains in at least two replicates, '
        'with both-direction qualification, both maze families and retained source signalling. Q or S alone cannot '
        'trigger the longer run.','',
        '| Topology | Rep | Frozen G | Product G | Curriculum G | Q | S | Both | Pass |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in gate['details']:
        text.append(f"| {r['topology']} | {r['replicate']} | {r['initial_goal']:.4f} | {r['current_goal']:.4f} | {r['goal']:.4f} | {r['quality']:.4f} | {r['specificity']:.4f} | {r['both']:.3f} | {r['passed']} |")
    text+=['','## Fresh completed outputs','',
        'Models froze before264 new primary layouts (216 reachable,48 disconnected) and24 independent goal-pair '
        'layouts (42 reachable targets,6 unreachable). Every paired reachable target has distance>=8. Primary '
        'sizes are9/17/33/65 perfect/cyclic plus rectangular9/17. Task/goal and frozen archive labels can repeat '
        'genotypes; these are not independent discoveries.','',
        '| Archive | Valid /216 | Shortest | Distance>=8 shortest | Correct no-path /48 |',
        '|---|---:|---:|---:|---:|']
    for arm,r in sorted(summaries.items()):
        text.append(f"| {arm} | {r['valid']}/216 | {r['optimal']} | {r['long_optimal']}/{r['long_cases']} | {r['no_path']}/48 |")
    text+=['','Curriculum task archives classify12/48 primary disconnected grids correctly, versus0/48 for their '
        'frozen selections, with0/216 false no-path claims on reachable primary tasks. Multirange product also '
        'reaches12/48; local product reaches6/48 with one false claim. Curriculum archives handle2/6 paired '
        'unreachable targets. These small gains do not establish general connectivity detection: primary '
        'disconnected sources are fixed at a corner and use a separating wall.','']
    if shapes:
        text+=['',f"Across repeated candidate archive outputs, successes span {min(r['edges'] for r in shapes)}–{max(r['edges'] for r in shapes)} edges; "
            f"{sum(r['turns']>0 for r in shapes)}/{len(shapes)} contain turns. Per-case evidence is in `success_shapes.json`. "
            'A long straight line alone does not establish maze solving. One inherited genome already solved an11-edge '
            'straight validation path before training; that is not a V5 evolutionary gain.','']
    text+=['','Diagnostic subsets: different source/goal rows **and** columns require a turn; oracle distance greater '
        'than Manhattan distance requires a detour. These post-selection analyses do not alter training or model selection.','',
        '| Task archive | Turn-required shortest | Detour-required shortest |','|---|---:|---:|']
    for arm in ('compiled_bfs','local/product/task','local/curriculum/task','evolved/product/task','evolved/curriculum/task'):
        d=difficulty[arm];text.append(f"| {arm} | {d['turn_required_optimal']}/{d['turn_required_cases']} | {d['detour_required_optimal']}/{d['detour_required_cases']} |")
    if (out/'turned_path_diagnostic.json').exists():
        turned=read('turned_path_diagnostic.json');prefix=read('goal_prefix_diagnostic.json')
        from .range_audit import output_dataflow
        dataflow=output_dataflow(Genome.from_dict(turned['individual']['genome']))
        write_json(out/'filament_dataflow.json',dataflow)
        text+=['','## An isolated new filament with turns','',
            'The local product task archive solves one independent paired9x9 perfect maze: **10 edges,3 turns, '
            'two internal junctions**, emitted at tick21. Its initial frozen selections solve0/42 paired targets. '
            'This is separate from the primary table and occurs in the control arm; it is not an advantage of '
            'the factorized curriculum.','',
            'A post-hoc trace of existing frozen ancestors finds the first success at generation38, after three '
            'gene-row edits from its failing generation37 parent. They change a MIN_POS source channel6 to7, '
            'redirect a NEIGHBOR result from scratch register61 to19, and change one XOR input from48 to19. '
            'The mutation set as a whole changes this response; individual necessity was not tested. The final '
            'generation42 descendant is seven mutational links from its inherited V4 root. No solver seed was '
            'introduced and no diagnostic mutant was bred into a population.','',
            'The filament moves only west and south. It fails the alternative goal on identical geometry and '
            'all three90-degree rotations of the successful task. Every state channel is identical under the '
            'two goals at each tick1–21. The common runtime checks whether both output endpoints are lit when '
            'the source stop channel is positive. This explains the successful stopping time without goal-specific '
            'branch choices in the developing state. It is a concrete precursor of growth that follows maze '
            'geometry with a directional bias; goal-guided junction choice and general shortest-path extraction '
            'remain absent.','',
            'These ancestor/rotation/prefix checks were chosen after inspecting this success. They diagnose an '
            'already inspected maze and are not new holdout accuracy. Full genomes, outputs, work and edits are '
            'saved in `turned_path_diagnostic.json` and `goal_prefix_diagnostic.json`.','',
            '![Mutation and orientation diagnostics](factor_curriculum/visuals/turned_path_diagnostic.png)','',
            f"Post-hoc cost {turned['elapsed_seconds']+prefix['elapsed_seconds']:.2f}s, {turned['normal_calls']} "
            f"ordinary calls and {turned['probe_calls']+prefix['probe_runs']} probes, charging "
            f"{turned['charged_work']+prefix['charged_work']:,} additional logical work units.",'']
        text+=['',f"The final filament genome contains {dataflow['genes']} genes. A conservative static slice "
            f"identifies {dataflow['potential_output_stop_genes']} potential output/stop gene dependencies across "
            f"state channels {dataflow['state_channels']}. This is not a minimal program or a count of dynamically "
            'necessary genes; full-state quiescence can depend on additional channels. Genome length alone '
            'does not establish effective regulatory complexity.','']
    text+=['','## Independent goal-pair outputs and probes','',
        'Normal path correctness is separate from fixed-tick probe measures. Q,S,G average all48 targets, with zero '
        'new credit for unreachable/unaligned cases. Source signal averages42 reachable targets; both-direction '
        'rate uses18 regular pairs. No new independent resampling arm was run.','',
        '| Archive | Normal shortest /42 | No-path /6 | G | Q | S | Both | Source signal |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in ps:
        fmt=lambda v:'—' if v is None else f'{v:.4f}'
        text.append(f"| {r['arm']} | {r['optimal']}/42 | {r['no_path']}/6 | {fmt(r['goal'])} | {fmt(r['quality'])} | {fmt(r['specificity'])} | {fmt(r['both'])} | {fmt(r['signal'])} |")
    if (out/'probe_route_diagnostics.json').exists():
        probe=read('probe_route_diagnostics.json')
        text+=['',f"Of {len(probe)} saved tick16 paired rasters, "
            f"{sum(r['aligned'] and r['probe_valid'] for r in probe)} form a legal path even with an assumed "
            'emitted status. Failed tick16 outputs are therefore not merely correct routes awaiting a stop '
            'signal. The isolated turned path forms later, at tick21. Assumed status is diagnostic only.','']
    text+=['','## Factor accessibility through the curriculum','',
        f"Final population sequences are identical in {sum(r['identical'] for r in identical)}/6 paired comparisons. "
        'Counts below are reachable training responses, often repeated organisms, not independent samples. Early '
        'means generations0–15, transition16–31, matched32 onward; the product control always uses alpha=1. '
        'Raw sums, maxima, factor co-occurrence and separate validation counts are saved.','',
        '| Topology / pressure | Phase | Reachable responses | Q>0 | S>0 | G>0 | Mean G |',
        '|---|---|---:|---:|---:|---:|---:|']
    for (t,p,phase),r in sorted(phase_groups.items()):
        text.append(f"| {t}/{p} | {phase} | {int(r['reachable_responses']):,} | {int(r['quality']):,} | {int(r['specificity']):,} | {int(r['joint']):,} | {r['sum_goal']/r['reachable_responses']:.5f} |")
    if (out/'goal_switch_diagnostics.json').exists():
        sg=defaultdict(list)
        for r in read('goal_switch_diagnostics.json'):
            if not r['mixed']:sg[r['arm']].append(r)
        text+=['','## Exploratory goal-information assay at frozen genomes','',
            'This diagnostic was added during training, before final evaluation, and never affects selection. '
            'The same source/maze is observed at tick16 with goalA/B. Count hidden-state differences at open sites '
            'at least two graph edges from both goals, excluding output/stop channels. Differences are caused by '
            'the changed goal stimulus, but are not proof of a distance map or correct route. Mixed disconnected '
            'pairs are saved separately and excluded from this table.','',
            '| Goal archive | Aligned regular pairs | Distal hidden response >0 | Mean distal fraction | Hidden response at source | Raster changes >0 |',
            '|---|---:|---:|---:|---:|---:|']
        for arm,rr in sorted(sg.items()):
            aligned=[r for r in rr if r['aligned']]
            text.append(f"| {arm} | {len(aligned)}/18 | {sum(r['distal_hidden_fraction']>0 for r in aligned)} | {np.mean([r['distal_hidden_fraction'] for r in aligned]):.4f} | {sum(r['source_hidden_changes'] for r in aligned)} | {sum(r['probe_raster_changes']>0 for r in aligned)} |")
    if (out/'validation_timecourse.json').exists():
        tc=read('validation_timecourse.json');groups=defaultdict(list)
        for r in tc['rows']:groups[(r['arm'],r['horizon'])].append(r)
        text+=['','### Validation-only time course','',
            'Added after final inspection without changing genomes or selection. Compare all eight source state '
            'channels under switched goals at ticks8/16/32/64, with stopping disabled, including output/stop '
            'concentrations. Each entry uses12 regular validation pairs per arm. These are exploratory '
            'diagnostics, not another final score.','',
            '| Goal archive | Tick | Aligned | Any source state | Hidden | Output concentration | Stop |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for (arm,horizon),rr in sorted(groups.items()):
            aa=[r for r in rr if r['aligned']]
            text.append(f"| {arm} | {horizon} | {len(aa)}/12 | {sum(r['any_source_state'] for r in aa)} | {sum(r['hidden_source_state'] for r in aa)} | {sum(r['output_source_state'] for r in aa)} | {sum(r['stop_source_state'] for r in aa)} |")
        text+=['','Local goal archives show no source state response through tick64 on these pairs. Multirange '
            'archives show limited delayed responses:3/12 curriculum and2/12 product pairs at tick64. Making '
            'goal information usable at a decision site remains a candidate bottleneck; these measurements '
            'do not prove that a particular initialization change will solve it.','',
            f"Time-course cost {tc['elapsed_seconds']:.2f}s, {tc['probe_runs']} probes, {tc['charged_work']:,} logical work units.",'']
    if (out/'nonlocal_ablation.jsonl.gz').exists():
        ablated=list(lines(out/'nonlocal_ablation.jsonl.gz'));diag=read('diagnostics.json')
        text+=['','## Frozen nonlocal-read ablation','',
            'Every radius>1 read returns zero in both ordinary inference and both source probes; attempted reads '
            'remain charged. Selected genomes are unchanged.','',
            '| Goal archive | Normal source signal | Ablated signal | Normal G | Ablated G | Ablated shortest /42 |',
            '|---|---:|---:|---:|---:|---:|']
        for arm in sorted({r['arm'] for r in ablated}):
            rr=[r for r in ablated if r['arm']==arm];reachable=[r for r in rr if r['reachable']]
            text.append(f"| {arm} | {pm[arm]['signal']:.4f} | {np.mean([r['signal']['score'] for r in reachable]):.4f} | {pm[arm]['goal']:.4f} | {np.mean([r['goal']['score'] for r in rr]):.4f} | {sum(r['optimal'] for r in rr)}/42 |")
        text+=['',f"Post-freeze diagnostics: {diag['elapsed_seconds']:.2f}s, {diag['normal_responses']} normal responses, "
            f"{diag['developmental_probes']+diag['goal_switch_probes']} probes and {diag['charged_work']:,} logical work units.",'']
    text+=['','## Actual compute, latency and memory','',
        f"Training including validation/probes took **{env['training_seconds']/60:.2f} minutes**; whole main run "
        f"including fresh tests/timing **{env['elapsed_seconds']/60:.2f} minutes** on {env['cpu']}, Python {env['python']}. "
        f"Peak process RSS {env['max_rss_bytes']/2**20:.1f} MiB. {verification['normal_maze_evaluations']:,} normal "
        f"training/selection responses plus {verification['developmental_probe_runs']:,} developmental probes. "
        'Work counts dispatches plus attempted reads, not machine instructions. Candidate slots and caps match; '
        'actual work/nominee overlap varies with phenotype.','',
        '| Topology / pressure | Train responses | Validation responses | Inference work | Probe work |',
        '|---|---:|---:|---:|---:|']
    for (t,p),r in sorted(cost_groups.items()):
        text.append(f"| {t}/{p} | {r['train_responses']:,} | {r['validation_responses']:,} | {r['inference_work']:,} | {r['probe_work']:,} |")
    text+=['','Thirty warm randomized repetitions on12 fixed17/33 perfect/cyclic tasks per arm. Input decoding, '
        'internal updates and full raster emission are included; model construction, evaluator and probes are excluded. '
        'Median below is the median of case medians, range spans all repetitions. Failed outputs get no speed credit.','',
        '| Arm | Median us | Warm range us | Shortest timed responses /360 |','|---|---:|---:|---:|']
    tg=defaultdict(list)
    for r in read('timings.json'):tg[r['arm']].append(r)
    for arm,rr in sorted(tg.items()):
        text.append(f"| {arm} | {statistics.median(r['median_us'] for r in rr):.2f} | {min(r['min_us'] for r in rr):.2f}–{max(r['max_us'] for r in rr):.2f} | {sum(r['correct'] for r in rr)}/360 |")
    text+=['',f"Largest reported inference array payload {max(r['largest_array_bytes'] for r in summaries.values()):,} bytes. "
        'Interpreter bounds remain64 bytes/site+64KiB; observer-pair bound80 bytes/site+64KiB; program at most3584 bytes. '
        'These exclude Python/JIT/evaluator/allocator overhead, included in RSS. A* heap payload is logical and '
        'bit-wave memory uninstrumented. Dense genome scans scale with ticks x open sites x gene count; gates '
        'still pay dispatch cost. No invalid output is evidence of computational advantage.','',
        '## Fixed visual samples','',
        'First size17 perfect/cyclic primary and paired cases from replicate0, without success filtering. '
        'Probe panels are intermediate states, separately labelled.','',
        '![Normal unseen outputs](factor_curriculum/visuals/unseen_outputs.png)','',
        '![Switched-goal probes](factor_curriculum/visuals/switched_goals.png)','',
        '## Verification and limits','',
        f"Checked {verification['source_files']} source hashes, six V4 checkpoint hashes, "
        f"{verification['new_individuals']:,} new individual/parent links, all protected elites and the128-gene bound. "
        f"Reassessed {verification['reassessed_primary_outputs']:,} primary, {verification['reassessed_paired_outputs']:,} "
        f"paired and {verification['reassessed_ablation_outputs']:,} ablated normal rasters, plus "
        f"{verification['reassessed_training_valid_claims']:,} valid claims from training/validation. Recomputed "
        f"{verification['raster_goal_checks']} paired probe metrics and checked {verification['training_fitness_checks']:,} "
        'fitness/normal-rank/curriculum decompositions. Final264 primary and24 paired layouts are disjoint from '
        f"{verification['previous_layouts']:,} V1–V4 layouts and new train/validation. Full next populations/RNG states "
        'support exact replay, including curriculum-stage transitions tested by unit tests. '
        'Prior code and raw results remain unchanged.','',
        'The study has three replicates and a fixed grammar, mutation scheme, input initialization and tick16 '
        'probe horizon. Archive labels and repeated response counts are not independent samples. Neither a bounded '
        'negative outcome nor a precursor score establishes impossibility or useful general maze solving. '
        'The source gets initial channel0 activation plus a source flag, while the goal is exposed as a local '
        'read-only input flag; input accessibility is another hypothesis, not resolved by gene count alone.','',
        '## Next controlled experiment','',
        'Test **symmetric source/goal stimulus initialization** against the current convention, at fixed genome '
        'capacity and with the same product objective. The source gets initial channel0 activation and a local '
        'flag, while the goal has only a local flag. Supply an initial goal pulse in channel1 in the treatment '
        'arm, retaining both flags. This supplies stimulus, not a known solver or path rule. Preserve V5 task, '
        'goal and source archives from both pressure arms so the directional filament is retained. Use frozen '
        'controls for each input convention, measure communication to decision sites and exact turning/detour '
        'routes, and reserve new layouts. This tests information accessibility before assuming that larger '
        'genomes alone are the missing ingredient.','',
        '## Reproduce','',
        '```bash','.venv/bin/python -m pytest -q',
        '.venv/bin/python -m maze_evolution.factor_study --out results/repeat_factor',
        '.venv/bin/python -m maze_evolution.factor_diagnostics --out results/repeat_factor',
        '.venv/bin/python -m maze_evolution.factor_timecourse --out results/repeat_factor',
        '.venv/bin/python -m maze_evolution.factor_lineage_diagnostic --out results/repeat_factor',
        '.venv/bin/python -m maze_evolution.factor_prefix_diagnostic --out results/repeat_factor',
        '.venv/bin/python -m maze_evolution.factor_audit --out results/repeat_factor',
        '.venv/bin/python -m maze_evolution.factor_report --out results/repeat_factor','```','',
        'Choose a fresh output directory. Raw masks, probes, full population/RNG checkpoints and all evaluated '
        'genomes/parents/fitnesses are in `factor_curriculum/`.']
    if (out/'storage.json').exists():
        storage=read('storage.json');text+=['',f"After benchmarking, lossless log packaging took {storage['elapsed_seconds']:.1f}s: "
            f"{storage['before_bytes']/2**20:.2f} to {storage['stored_bytes']/2**20:.2f} MiB. Decoded/stored hashes are in `storage.json`. All decoded bytes matched."]
    out.with_suffix('.md').write_text('\n'.join(text).rstrip()+'\n');visuals(out,manifest,primary,paired)
    if (out/'turned_path_diagnostic.json').exists():turned_visual(out,manifest)
    print(out.with_suffix('.md'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/factor_curriculum');report(parser.parse_args().out)
