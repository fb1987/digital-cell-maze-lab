"""V4 report from frozen evidence; no selection or parameter changes."""
import argparse
from collections import defaultdict
import gzip,json,statistics
from pathlib import Path
import numpy as np
from .evaluator import Maze,Oracle
from .experiment import write_json
from .goal_audit import unpack
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
    arms=('compiled_bfs','local/transmission/task','local/goal/task','evolved/transmission/task','evolved/goal/task')
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
    record=next(r for r in paired if r['arm']=='evolved/goal/goal' and r['replicate']==0)
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


def report(out):
    out=Path(out)
    read=lambda name:json.loads((out/name).read_text())
    env=read('environment.json');config=read('config.json');gate=read('extension_decision.json');verify=read('verification.json')
    champions=read('champions.json');primary=list(lines(out/'holdout.jsonl.gz'));paired=list(lines(out/'paired_holdout.jsonl.gz'))
    summary={r['arm']:r for r in read('summary.json') if r['group']=='all'}
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());maze_map={m['case_id']:m for m in manifest}
    reachable_cases={m['case_id']:m['oracle_length']>0 for m in manifest}
    ps=paired_summary(paired,reachable_cases);write_json(out/'paired_summary.json',ps);pm={r['arm']:r for r in ps}
    from cellular_maze_lab import neighbors
    shapes=[]
    for r in primary:
        if not r['valid_path'] or '/' not in r['arm']:continue
        m=maze_map[r['case_id']];mask=unpack(r['mask'],m['w']*m['h']);p=m['start'];previous=-1;directions=[]
        while p!=m['goal']:
            q=next(q for q in neighbors(p,m['w'],m['h']) if mask[q] and q!=previous)
            directions.append(q-p);previous,p=p,q
        shapes.append(dict(arm=r['arm'],replicate=r['replicate'],case=r['case_id'],edges=len(directions),
            turns=sum(a!=b for a,b in zip(directions,directions[1:])),optimal=r['optimal']))
    write_json(out/'success_shapes.json',shapes)
    paired_populations=[]
    for t in ('local','evolved'):
        for rep in range(3):
            checkpoints=[read('checkpoints/'+f'goal_{t}_{p}_{rep}.json') for p in ('transmission','goal')]
            get=lambda saved:[Genome.from_dict(i['genome']).digest for i in saved['population']]
            paired_populations.append(dict(topology=t,replicate=rep,identical_final_genotypes=get(checkpoints[0])==get(checkpoints[1])))
    write_json(out/'paired_populations.json',paired_populations)
    factors=read('training_factors.json');factor_groups=defaultdict(lambda:defaultdict(float))
    for key,values in factors.items():
        _,topology,pressure,rep,split=key.split('/')
        group=factor_groups[(topology,pressure,split)]
        for k,v in values.items():group[k]=max(group[k],v) if k.startswith('max_') else group[k]+v
    costs=read('training_cost.json');cg=defaultdict(lambda:defaultdict(int))
    for key,values in costs.items():
        _,t,p,_=key.split('/')
        for k,v in values.items():cg[(t,p)][k]+=v
    task=summary['evolved/goal/task'];control=summary['evolved/transmission/task'];frozen=summary['evolved/goal/frozen_task']
    any_long=sum(summary[a]['long_optimal'] for a in summary if a.endswith('/task'))
    text=['# Goal-conditioned path formation: V4','',
        '**The added goal-output pressure did not produce a general shortest-path solver.**' if not any_long else '**Long-route outcomes require case-level inspection below.**','',
        f"The multirange task archives solve {task['optimal']}/{task['reachable']} primary fresh reachable cases under goal pressure, "
        f"versus {control['optimal']}/{control['reachable']} under transmission pressure and {frozen['optimal']}/{frozen['reachable']} "
        f"for the frozen initial task selections. Goal-pressure task archives solve {task['long_optimal']}/{task['long_cases']} "
        f"at distance>=8. On the separate switched-goal set they solve {pm['evolved/goal/task']['optimal']}/42 reachable targets. "
        'Completed routes and tick16 probe scores are reported separately.','',
        f"Some goal-sensitive branched outputs evolved, but the added pressure has no demonstrated unseen advantage. "
        f"The goal-selected multirange archive scores {pm['evolved/goal/goal']['goal']:.4f} on unseen pairs under goal pressure, "
        f"versus {pm['evolved/transmission/goal']['goal']:.4f} in its transmission control; local scores are "
        f"{pm['local/goal/goal']['goal']:.4f} versus {pm['local/transmission/goal']['goal']:.4f}. "
        'No archive passes the both-directions criterion on any final regular pair. One local validation replicate '
        'rose from zero to0.0387 (control0.0194); its best patterns still had extra branches or failed the normal work budget. '
        'Source-connected output is common during training, while goal-specific progress is rare. '
        'This points to evolutionary credit assignment and path thinning as the next test, rather than an established solver.','',
        '## Controlled continuation','',
        f"Root {config['seed']}, two pressures x two topologies x three replicates, 96 organisms per condition, "
        f"{', '.join(str(g) for g in sorted(set(v['next_generation'] for v in champions.values())))} additional generations. "
        f"The preregistered extension gate was **{gate['extend']}**; it requires replicated goal-output improvement "
        'or additional correct long routes. Existing hidden communication alone does not justify the longer run.','',
        'Forks use six saved V3 causal random-origin populations and their RNG states. If missing from the next population, '
        'the learned V3 transmission archive replaces its last slot identically in both arms and remains a protected elite. '
        'This preserves a discovered precursor; no known solver or hand-built reaction program enters the lineage. '
        'New validation archives never automatically enter reproduction. Full provenance is in `forks.json`, checkpoints and lineage logs.','',
        'Capacity remains eight uint16 channels, 64 registers and 128 typed genes. Training inference caps remain '
        '256 ticks / 4096 reads per site / 32768 dispatches per site; validation/final caps remain '
        '1024 / 8192 / 131072. The comparator retains V3 source-transmission pressure on the new paired environments. '
        'The new pressure adds twice the bounded goal-output score to the intermediate partial field and lexicase field. '
        'Validity, optimality and no-path utility retain priority. Costs break ties only for completely correct responses.','',
        'Each stimulus pair shares a layout and source but changes the goal. All reachable training/validation targets '
        'have distance>=8 and regular pairs have divergent targets. Two training pairs rotate each generation, initially '
        'size9 and then size17; fixed validation has six pairs per replicate. Mixed disconnected pairs include one '
        'reachable and one unreachable target. Layouts are disjoint across all splits and all V1–V3 environments.','',
        'Both arms pay for ordinary inference and two fixed-tick16 probes per response, source present/removed. '
        'The unchanged observer supplies both the old hidden-transmission score and the new output score. '
        'Quality multiplies source-connected progress, connected fraction and binary output source dependence, '
        'with a branch penalty. Specificity compares progress against the other goal raster on the same geometry. '
        'The geometric mean is zero when either factor is absent. Source-only marks, detached goal markers, '
        'goal-only patterns and unchanged floods earn zero. Oracles are confined to data/evaluation. '
        'See the [protocol](../docs/GOAL_STUDY_V4.md) for exact definitions and extension thresholds.','',
        '## Final-generator repair after freezing','',
        'The original final generator failed before evaluating any candidate output: it could not find a fourth '
        'unused size9 perfect layout in4000 corner-start DFS samples. Training and validation already exclude all '
        'earlier layouts, and that small generator has limited diversity. Frozen genomes and all training logs '
        'were preserved. Only final size9 perfect mazes were switched to Wilson loop-erased random-walk spanning '
        'trees, still31 open sites and a connected tree. Larger perfect mazes and all other families keep the '
        'original generators. This changes the size9 perfect sampling distribution and is a protocol deviation, '
        'specified in `final_generation_repair.json` before any final candidate evaluation. No fitness, '
        'hyperparameter or genome was changed. The new generator has deterministic tree/independence tests.','',
        '## Validation gate','',
        '| Topology | Rep | Initial goal | Transmission control | Goal pressure | Quality | Specificity | Both directions | Pass |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in gate['details']:
        text.append(f"| {r['topology']} | {r['replicate']} | {r['initial_goal']:.4f} | {r['current_goal']:.4f} | {r['goal']:.4f} | {r['quality']:.4f} | {r['specificity']:.4f} | {r['both']:.3f} | {r['passed']} |")
    text+=['','## Fresh completed outputs','',
        'All archives were frozen before generating 264 primary tests: 216 reachable, 48 disconnected, '
        'perfect/cyclic sizes9/17/33/65 and rectangular9/17. Endpoints are unrestricted here; long-route counts '
        'are a separate subset. The additional paired final set has 24 distinct layouts, 42 reachable and six '
        'unreachable targets, all reachable at distance>=8. Frozen controls use initial selection, without evolution. '
        'Task/goal/transmission archives are different diagnostic selections, sometimes the same genotype; '
        'archive labels are not independent replicates. No new independent resampling arm was run.','',
        '| Archive | Valid / reachable | Shortest | Distance>=8 shortest | Correct no-path /48 |',
        '|---|---:|---:|---:|---:|']
    for arm,r in sorted(summary.items()):
        text.append(f"| {arm} | {r['valid']}/{r['reachable']} | {r['optimal']} | {r['long_optimal']}/{r['long_cases']} | {r['no_path']}/48 |")
    if shapes:
        text+=['',f"Successful candidate rasters across archive labels span {min(r['edges'] for r in shapes)}–{max(r['edges'] for r in shapes)} edges; "
            f"{sum(r['turns']>0 for r in shapes)}/{len(shapes)} include turns. These are repeated selected outputs, not independent discoveries. "
            '`success_shapes.json` records each case.','']
    text+=['','## Independent switched-goal tests','',
        'Goal/quality/specificity are fixed-tick probe averages over all 48 targets, including zero reward for unreachable goals. '
        'Signal averages use the 42 reachable targets. Both-directions is the fraction of 18 regular pairs meeting the '
        'preregistered quality/specificity thresholds. Hidden signal is not a route metric.','',
        '| Archive | Normal shortest /42 | No-path /6 | Goal score | Quality | Specificity | Both | Hidden signal |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in ps:
        fmt=lambda v:'—' if v is None else f'{v:.4f}'
        text.append(f"| {r['arm']} | {r['optimal']}/42 | {r['no_path']}/6 | {fmt(r['goal'])} | {fmt(r['quality'])} | {fmt(r['specificity'])} | {fmt(r['both'])} | {fmt(r['signal'])} |")
    text+=['','## Where the added pressure acts','',
        f"Final paired population genotype sequences are identical in {sum(r['identical_final_genotypes'] for r in paired_populations)}/6 comparisons. "
        'The following diagnostics count reachable training responses, rather than just archived champions. '
        'They distinguish the output prerequisites from the full multiplicative bonus. Validation has separate raw counts '
        'in `training_factors.json`. A positive component factor need not coincide with the other factor.','',
        '| Topology / pressure | Reachable responses | Component >=3 sites | Source-dependent output | Quality >0 | Specificity >0 | Goal score >0 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for (t,p,s),r in sorted(factor_groups.items()):
        if s!='train':continue
        text.append(f"| {t}/{p} | {int(r['reachable_responses']):,} | {int(r['connected_growth']):,} | {int(r['source_dependent_output']):,} | {int(r['positive_quality']):,} | {int(r['positive_specificity']):,} | {int(r['positive_goal_score']):,} |")
    if (out/'nonlocal_ablation.jsonl.gz').exists():
        ablated=list(lines(out/'nonlocal_ablation.jsonl.gz'));diag=read('diagnostics.json')
        text+=['','## Frozen nonlocal-read ablation','',
            'Each radius>1 read returns zero while attempted reads remain charged. Both ordinary inference and '
            'the source-present/source-removed probes use the ablated runtime. This post-freeze diagnostic changes '
            'no selected genome. Signal is averaged on reachable paired cases; goal score averages all targets.','',
            '| Archive | Normal signal | Ablated signal | Normal goal | Ablated goal | Ablated shortest /42 |',
            '|---|---:|---:|---:|---:|---:|']
        for arm in sorted({r['arm'] for r in ablated}):
            rr=[r for r in ablated if r['arm']==arm];reachable=[r for r in rr if r['reachable']]
            text.append(f"| {arm} | {pm[arm]['signal']:.4f} | {np.mean([r['signal']['score'] for r in reachable]):.4f} | {pm[arm]['goal']:.4f} | {np.mean([r['goal']['score'] for r in rr]):.4f} | {sum(r['optimal'] for r in rr)}/42 |")
        text+=['',f"Ablation cost: {diag['elapsed_seconds']:.1f}s, {diag['normal_responses']} normal responses, "
            f"{diag['developmental_probes']} probes and {diag['charged_work']:,} logical work units.",'']
    text+=['','## Actual cost and timing','',
        f"Search plus validation/probes: **{env['training_seconds']/60:.2f} minutes**. Main run including fresh outputs "
        f"and timing: **{env['elapsed_seconds']/60:.2f} minutes** on {env['cpu']}, Python {env['python']}. "
        'This sums the recorded training window and recovered final process, excluding the failed sampling attempt '
        'and repair-development gap. '
        f"Recovered-final process peak RSS {env['max_rss_bytes']/2**20:.1f} MiB; original training high-water mark "
        'was lost on interruption (observed training RSS about120MiB). '
        f"{verify['normal_maze_evaluations']:,} normal training/selection "
        f"responses plus {verify['developmental_probe_runs']:,} developmental probes. Candidate slots and work caps match; "
        'actual work can differ by phenotype. Logical work counts dispatches plus attempted reads, not machine instructions.','',
        '| Topology / pressure | Train responses | Validation responses | Inference work | Probe work |',
        '|---|---:|---:|---:|---:|']
    for (t,p),r in sorted(cg.items()):
        text.append(f"| {t}/{p} | {r['train_responses']:,} | {r['validation_responses']:,} | {r['inference_work']:,} | {r['probe_work']:,} |")
    text+=['','Thirty randomized warm repetitions per fixed size17/33 perfect/cyclic case per replicate, 12 cases/arm. '
        'Latency includes input decoding, updates and full raster emission; excludes genome construction, oracles and probes. '
        'The table uses the median of case medians and the full observed repetition range. Failed outputs get no speed credit.','',
        '| Arm | Median us | Warm range us | Shortest timed responses /360 |','|---|---:|---:|---:|']
    tg=defaultdict(list)
    for r in read('timings.json'):tg[r['arm']].append(r)
    for arm,rr in sorted(tg.items()):
        text.append(f"| {arm} | {statistics.median(r['median_us'] for r in rr):.2f} | {min(r['min_us'] for r in rr):.2f}–{max(r['max_us'] for r in rr):.2f} | {sum(r['correct'] for r in rr)}/360 |")
    text+=['',f"Largest measured inference array payload {max(r['largest_array_bytes'] for r in summary.values()):,} bytes. "
        'Bounds remain 64 bytes/site +64 KiB for inference and 80 bytes/site +64 KiB for an observer pair. '
        'Arrays exclude Python/JIT/evaluator/allocator overhead, included in RSS. Genome program payload is at most3584 bytes. '
        'A* heap payload is logical; bit-wave memory is uninstrumented. The interpreter scans each open site and '
        'gene each synchronous tick, so work scales with ticks x open sites x genome length, even when many gates '
        'disable expression. Nonlocal reads have no demonstrated efficiency advantage.','',
        '## Fixed visual examples','',
        'First size17 perfect/cyclic primary cases and first size17 paired cases from replicate0; no success filtering. '
        'The probe panels are intermediate rasters, separately labelled.','',
        '![Unseen normal outputs](goal_conditioning/visuals/unseen_outputs.png)','',
        '![Switched goals](goal_conditioning/visuals/switched_goals.png)','',
        '## Verification and limits','',
        f"Verified {verify['source_files']} training source hashes, six ancestor checkpoint hashes, "
        f"{verify['new_individuals']:,} new individuals/parent links, the128-gene bound and protected elite in every final population. "
        f"Reassessed {verify['reassessed_primary_outputs']:,} primary and {verify['reassessed_paired_outputs']:,} paired normal rasters "
        f"with the unchanged strict validator, recomputed {verify['raster_goal_checks']:,} final goal metrics from saved probe rasters, "
        f"and checked {verify['training_fitness_checks']:,} logged fitness decompositions and "
        f"{verify['training_signal_arithmetic_checks']:,} source-score arithmetic records. "
        f"{verify['primary_test_layouts']} primary and {verify['paired_final_layouts']} paired final layouts are disjoint from "
        f"each other and {verify['previous_layouts']:,} unique V1–V3 layouts, as well as new train/validation. "
        'Full next-population/RNG checkpoints allow deterministic continuation; unit tests compare uninterrupted and split replay.','',
        'This is a small paired study under a fixed grammar, mutation/search design and tick16 shaping horizon. '
        'It does not test impossibility or establish statistical significance. For long distances, local causal cones '
        'and the product of several prerequisites can limit useful reward. The primary final distribution differs from '
        'the divergent-goal training distribution, so both are reported. More capacity alone is not established as a remedy.','',
        '## Next controlled experiment','',
        'Preserve these random-origin populations and the learned signalling elite. Test a **factorized curriculum** '
        'against this multiplicative objective: provide separate intermediate credit for source-dependent connected output '
        'growth and goal-dependent modulation before requiring their conjunction. Keep capacity fixed, retain complete '
        'shortest routes as the primary endpoint, record which factors co-occur, and reserve new layouts. '
        'This tests the accessibility of useful evolutionary stepping stones without inserting a known solver.','',
        '## Reproduce','',
        '```bash','.venv/bin/python -m pytest -q',
        '.venv/bin/python -m maze_evolution.goal_recovery --run --out results/repeat_goal',
        '.venv/bin/python -m maze_evolution.goal_diagnostics --out results/repeat_goal',
        '.venv/bin/python -m maze_evolution.goal_audit --out results/repeat_goal',
        '.venv/bin/python -m maze_evolution.goal_report --out results/repeat_goal','```','',
        'Choose a fresh output directory. The study freezes source/config/fork hashes and all selected genomes '
        'before constructing final tests. Raw evidence, masks and per-case timings are in `goal_conditioning/`.']
    if (out/'storage.json').exists():
        storage=read('storage.json')
        text+=['',f"After benchmarking, log packaging took {storage['elapsed_seconds']:.1f}s and reduced "
            f"{storage['before_bytes']/2**20:.2f} to {storage['stored_bytes']/2**20:.2f} MiB. "
            'Decoded bytes were verified identical before/after gzip repacking. Per-file decoded/stored hashes '
            'are in `storage.json`. No record values changed.','']
    out.with_suffix('.md').write_text('\n'.join(text).rstrip()+'\n')
    visuals(out,manifest,primary,paired)
    print(out.with_suffix('.md'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/goal_conditioning')
    report(parser.parse_args().out)
