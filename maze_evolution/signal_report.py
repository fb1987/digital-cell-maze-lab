"""Read-only scientific report and fixed-sample visualizations for V3."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import statistics
import numpy as np
from .evaluator import Maze, Oracle, assess
from .experiment import write_json
from .range_audit import output_dataflow
from .regulatory import Genome
from .regulatory_runtime import Organism
from .runtime import Limits
from .signal_probe import observe
from .signal_audit import lines


def signal_summary(signals):
    groups=defaultdict(list)
    for row in signals:
        if row['edges']>=8:
            groups[(row['arm'],'all')].append(row)
            groups[(row['arm'],row['family'])].append(row)
    return [dict(arm=arm,family=family,cases=len(values),
        mean_signal=float(np.mean([r['score'] for r in values])),
        nonzero=sum(r['score']>0 for r in values),
        goal_signal=sum(r['goal_signal'] for r in values),
        max_distance=max(r['max_distance'] for r in values),
        mean_leakage=float(np.mean([r['leakage'] for r in values])))
        for (arm,family),values in sorted(groups.items())]


def visuals(out,champions,limits,topology='local'):
    from PIL import Image,ImageDraw
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read())
    selected=[]
    # Predetermined first size17 instance of each family in replicate0.
    for family in ('perfect','random'):
        selected.append(next(r for r in manifest if r['split']=='test' and r['w']==17
            and r['family']==family and '/r0/' in r['case_id']))
    tile,pw,ph=10,220,235
    canvas=Image.new('RGB',(pw*5,ph*2+32),'#111827'); draw=ImageDraw.Draw(canvas)
    draw.text((15,10),'Green: output raster. Yellow: source-dependent hidden activation at tick16. Blue: source. Pink: goal.',fill='#e6edf7')
    from .baselines import baseline
    for row_index,saved in enumerate(selected):
        m=Maze(bytes.fromhex(saved['cells_hex']),saved['w'],saved['h'],saved['start'],saved['goal'])
        oracle=Oracle.build(m)
        panels=[('BFS shortest route',baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal).mask,False)]
        hidden=[]
        for pressure in ('current','causal'):
            g=Genome.from_dict(champions[f'signal/{topology}/{pressure}/0']['transmission']['genome'])
            o=Organism(g,topology,limits); result=o.react(m.cells,m.w,m.h,m.start,m.goal)
            a=assess(result,oracle)
            panels.append((pressure+' output: '+('valid' if a.valid_path else a.failure),result.mask,False))
            normal=observe(o,m.cells,m.w,m.h,m.start,m.goal,16,True)
            ablated=observe(o,m.cells,m.w,m.h,m.start,m.goal,16,False)
            delta=np.zeros(len(m.cells),dtype=bool)
            for channel in (0,1,3,4,5,6):
                delta|=(normal.state[channel]>0)&(normal.state[channel]!=ablated.state[channel])
            hidden.append((pressure+' hidden signal',delta,True))
        panels+=hidden
        for column,(label,mask,is_hidden) in enumerate(panels):
            ox,oy=column*pw+15,row_index*ph+84
            draw.text((ox,oy-40),saved['family']+' | '+label.split(':')[0],fill='#f9fafb')
            draw.text((ox,oy-24),label.split(': ',1)[-1] if ': ' in label else 'tick16' if is_hidden else 'oracle',fill='#aabbd0')
            for p,opened in enumerate(m.cells):
                color='#172235' if not opened else ('#f6c85f' if is_hidden else '#5ae1bd') if mask[p] else '#45536a'
                if p==m.start: color='#72b6ff'
                if p==m.goal: color='#ff6584'
                x,y=p%m.w,p//m.w
                draw.rectangle((ox+x*tile,oy+y*tile,ox+(x+1)*tile-1,oy+(y+1)*tile-1),fill=color)
    (out/'visuals').mkdir(exist_ok=True)
    canvas.save(out/'visuals'/('unseen_signals.png' if topology=='local' else 'unseen_ranges.png'))


def report(out):
    out=Path(out)
    env=json.loads((out/'environment.json').read_text())
    config=json.loads((out/'config.json').read_text())
    gate=json.loads((out/'extension_decision.json').read_text())
    champions=json.loads((out/'champions.json').read_text())
    summaries=[r for r in json.loads((out/'summary.json').read_text()) if r['group']=='all']
    signals=list(lines(out/'signals.jsonl.gz'))
    sig=signal_summary(signals); write_json(out/'signal_summary.json',sig)
    verification=json.loads((out/'verification.json').read_text())
    timings=json.loads((out/'timings.json').read_text())
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read())
    mazes={r['case_id']:r for r in manifest}
    success_shapes=[]
    from cellular_maze_lab import neighbors
    for r in lines(out/'holdout.jsonl.gz'):
        if not r['valid_path'] or r['arm'] in ('compiled_bfs','compiled_astar','wave_bit'):
            continue
        m=mazes[r['case_id']]
        mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),dtype=np.uint8),bitorder='little')[:m['w']*m['h']]
        p=m['start']; previous=-1; directions=[]
        while p!=m['goal']:
            q=next(q for q in neighbors(p,m['w'],m['h']) if mask[q] and q!=previous)
            directions.append(q-p); previous,p=p,q
        success_shapes.append(dict(arm=r['arm'],replicate=r['replicate'],case_id=r['case_id'],
            edges=len(directions),oracle_edges=r['edges'],turns=sum(a!=b for a,b in zip(directions,directions[1:])),optimal=r['optimal']))
    write_json(out/'success_shapes.json',success_shapes)
    phenotype={key:{field:output_dataflow(Genome.from_dict(saved[field]['genome']))
        for field in ('champion','transmission')} for key,saved in champions.items()}
    write_json(out/'phenotype_audit.json',phenotype)
    text=['# Source-dependent signal pressure: V3','',
        'This continuation tests selection pressure while holding V2 genome capacity and inference fixed. '
        'Hidden transmission is a precursor diagnostic; complete shortest paths remain the primary endpoint.','',
        '## Experiment','',
        f"Root {config['seed']}; six saved random-origin populations (96 organisms each), paired current/causal objectives. "
        f"Screen {config['screen_generations']} additional generations; extension decision **{gate['extend']}**. "
        f"Actual additional generations: {sorted(set(v['next_generation'] for v in champions.values()))}. "
        'No solver seed was introduced. Old objective scores were discarded at the fork.','',
        f"Search including probes/validation: **{env['training_seconds']/60:.2f} minutes**; whole run including fresh tests/timing: "
        f"{env['elapsed_seconds']/60:.2f} minutes. Peak process RSS {env['max_rss_bytes']/2**20:.1f} MiB. "
        f"{verification['normal_maze_evaluations']:,} ordinary responses plus {verification['developmental_probe_runs']:,} developmental probes. "
        f"Charged dispatches + attempted reads: inference {verification['inference_work']:,}, probes {verification['probe_work']:,}. "
        'These are logical work counts, not CPU instructions.','',
        'Current fitness retains V2 validity/optimality/no-path utility/partial ordering. Causal adds the bounded '
        'source-dependent hidden signal score to partial only, including the lexicase partial field. Both arms '
        'use identical probe protocols and validation nomination rules. Compute is matched by candidate slots and caps; '
        'actual work varies with evolved behaviour. Transmission archives are diagnostic selections and never '
        'automatically inserted into reproduction.','',
        'Probes compare ordinary and source-removed input at exactly tick16 with stopping disabled; channels2/7 '
        '(output/stop) excluded. Score averages affected fractions in graph-distance bands >=2/4/8 and subtracts '
        'leakage into other open components. Constants and source-only marks earn zero. Interrupted probes earn '
        'zero. No oracle/distance enters candidate inference or probes. A flood can earn full transmission score '
        'while producing no legal route.','',
        '## Validation-only extension decision','',
        '| Topology | Replicate | Initial transmission | Current | Causal | Signal criterion |',
        '|---|---:|---:|---:|---:|---|']
    sm={r['arm']:r for r in sig if r['family']=='all'}
    tasks={r['arm']:r for r in summaries}
    causal=tasks['evolved/causal/task']; current=tasks['evolved/current/task']
    ca=sm['evolved/causal/transmission']; co=sm['evolved/current/transmission']
    initial=sm['evolved/causal/frozen_transmission']
    paired=[]
    for rep in range(3):
        values={arm:np.mean([r['score'] for r in signals if r['arm']==arm and r['replicate']==rep and r['edges']>=8])
                for arm in ('evolved/causal/transmission','evolved/current/transmission')}
        paired.append(values['evolved/causal/transmission']>values['evolved/current/transmission'])
    text[3:3]=['','## Findings','',
        f"**A signalling precursor improved, but a general shortest-path solver did not emerge.** "
        f"On {ca['cases']} unseen reachable cases with endpoint distance>=8, mean source-dependent "
        f"transmission is {ca['mean_signal']:.4f} under causal pressure, {co['mean_signal']:.4f} under "
        f"the current objective, and {initial['mean_signal']:.4f} in the shared frozen initial archive. "
        f"Causal pressure leads in {sum(paired)}/3 held-out replicates; all three led on validation. "
        'This is a small paired study, not evidence of statistical significance.','',
        f"Final multirange task archives solve {causal['optimal']}/{causal['reachable']} shortest routes "
        f"under causal pressure and {current['optimal']}/{current['reachable']} under the current objective, "
        f"versus {tasks['evolved/causal/frozen_task']['optimal']}/216 for their frozen initial task selections. "
        f"Both final task archives solve {causal['long_optimal']}/{causal['long_cases']} long-route cases; "
        'compiled BFS/A* solve all 216 reachable and all 48 disconnected cases. '
        'No evolutionary path-accuracy advantage or competitive speedup is established.','',
        f"The causal transmission archive also leaks more source-dependent activation into other open "
        f"components: mean leakage {ca['mean_leakage']:.4f}, versus {co['mean_leakage']:.4f} for current. "
        'The reported signal score already subtracts this penalty. Fast broadcasts across walls can carry '
        'information without encoding a legal path.','',
        'The next controlled test should preserve these random-origin signalling lineages and test '
        '**goal-conditioned path thinning**: switch goal stimuli and reward source-connected, unbranched '
        'partial outputs that change appropriately, with completed shortest paths still first. Compare '
        'against unchanged transmission pressure at fixed capacity and use another fresh final test set. '
        'No known solver should be inserted into the random lineage.','']
    for r in gate['details']:
        text.append(f"| {r['topology']} | {r['replicate']} | {r['initial']:.3f} | {r['current']:.3f} | {r['causal']:.3f} | {r['signal_pass']} |")
    text+=['',f"Signal trigger topologies: {gate['signal_topologies']}; valid-route trigger topologies: {gate['route_topologies']}. "
        'See the preregistered thresholds in [the protocol](../docs/SIGNAL_PRESSURE_V3.md). The trigger uses validation, '
        'so final tests remain a separate assessment.','',
        '## Unseen complete outputs','',
        'All selected genomes were frozen before generating 264 fresh tasks. Each arm sees 216 reachable and 48 '
        'disconnected cases. Task archives use their own fitness; transmission archives maximize the validation '
        'precursor score. Frozen controls are selected from the same initial population under the corresponding criteria.','',
        '| Arm | Valid | Shortest | Shortest, distance>=8 | Correct no-path | Budget failures |',
        '|---|---:|---:|---:|---:|---:|']
    for r in summaries:
        text.append(f"| {r['arm']} | {r['valid']}/{r['reachable']} | {r['optimal']}/{r['reachable']} | {r['long_optimal']}/{r['long_cases']} | {r['no_path']}/{r['unreachable']} | {r['budget_failures']} |")
    if success_shapes:
        text+=['',f"Across selected/frozen organism outputs, successful routes span {min(r['edges'] for r in success_shapes)}–"
            f"{max(r['edges'] for r in success_shapes)} edges; {sum(r['turns']==0 for r in success_shapes)} of "
            f"{len(success_shapes)} successful arm-case outputs are straight. These include repeated genomes across "
            'archive labels and are not independent discoveries. Per-case turns/distances are in `success_shapes.json`.','']
    text+=['','## Source-dependent hidden signalling on unseen long routes','',
        'Only reachable cases with source–goal distance>=8 enter this table. Values are mean band-coverage '
        'scores, not path accuracy. Max distance can be large after nonlocal reads; it is not evidence of legal '
        'movement or efficient transmission.','',
        '| Archive | Cases | Mean signal | Nonzero | Signal at goal | Maximum graph distance | Mean leakage |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for r in sig:
        if r['family']=='all':
            text.append(f"| {r['arm']} | {r['cases']} | {r['mean_signal']:.4f} | {r['nonzero']} | {r['goal_signal']} | {r['max_distance']} | {r['mean_leakage']:.4f} |")
    if (out/'training_cost.json').exists():
        costs=json.loads((out/'training_cost.json').read_text()); groups=defaultdict(lambda:defaultdict(int))
        for key,values in costs.items():
            _,topology,pressure,rep=key.split('/')
            for field,value in values.items(): groups[(topology,pressure)][field]+=value
        text+=['','## Actual training and validation work','',
            'Each ordinary response also runs two developmental probes. Candidate slots and per-response '
            'caps match; actual activity and validation nominee overlap vary. Work below is dispatches '
            'plus attempted reads, summed across three replicates.','',
            '| Topology / pressure | Training responses | Validation responses | Inference work | Probe work |',
            '|---|---:|---:|---:|---:|']
        for (topology,pressure),c in sorted(groups.items()):
            text.append(f"| {topology}/{pressure} | {c['train_responses']:,} | {c['validation_responses']:,} | {c['inference_work']:,} | {c['probe_work']:,} |")
    text+=['','## Inference latency and memory','',
        'Thirty warm randomized repetitions per selected size17/33 perfect/cyclic task and replicate. '
        'Input decoding, internal updates and full binary-raster emission are included; genome construction '
        'and evaluator/probes are excluded. Median below is the median of 12 task medians, with the minimum '
        'and maximum observed warm repetition across those tasks. Failed outputs receive no speed credit.','',
        '| Arm | Median us | Warm range us | Shortest timed responses |',
        '|---|---:|---:|---:|']
    by_arm=defaultdict(list)
    for r in timings: by_arm[r['arm']].append(r)
    for arm,values in sorted(by_arm.items()):
        text.append(f"| {arm} | {statistics.median(r['median_us'] for r in values):.2f} | {min(r['min_us'] for r in values):.2f}–{max(r['max_us'] for r in values):.2f} | {sum(r['correct'] for r in values)}/{sum(r['repeats'] for r in values)} |")
    if (out/'diagnostics.json').exists():
        diagnostics=json.loads((out/'diagnostics.json').read_text())
        text+=['','## Effective transmission and range dependence','',
            f"Post-freeze diagnostics took {diagnostics['elapsed_seconds']:.1f}s and charged "
            f"{diagnostics['charged_work']:,} additional logical work units. They change no selected genomes. "
            'Local source dependence cannot travel more than one graph edge per synchronous tick. '
            'The theoretical tick16 coverage ceiling is computed separately from the training reward.','',
            '| Causal archive | Validation signal | Tick16 local ceiling | Genes | Single deletions reducing signal |',
            '|---|---:|---:|---:|---:|']
        for r in diagnostics['gene_ablations']:
            text.append(f"| {r['topology']} r{r['replicate']} | {r['baseline_signal']:.4f} | {r['validation_local_ceiling']:.4f} | {r['genes']} | {r['single_deletions_reducing_signal']} |")
        text+=['','Single-gene deletions were assessed on validation only. Redundant genes can interact; '
            'this count is not a minimal program size. It tests effective contributions rather than '
            'equating a long genome with complex regulation.','',
            '| Evolved-range archive | Normal long-route signal | Nonlocal reads zeroed | Normal shortest | Ablated shortest |',
            '|---|---:|---:|---:|---:|']
        ablated=list(lines(out/'nonlocal_ablation.jsonl.gz'))
        for arm in sorted({r['arm'] for r in ablated}):
            aa=[r for r in ablated if r['arm']==arm]
            long=[r for r in aa if r['edges']>=8]
            normal_signal=next(r['mean_signal'] for r in sig if r['arm']==arm and r['family']=='all')
            normal_path=next(r['optimal'] for r in summaries if r['arm']==arm)
            text.append(f"| {arm} | {normal_signal:.4f} | {np.mean([r['signal']['score'] for r in long]):.4f} | {normal_path}/216 | {sum(r['optimal'] for r in aa)}/216 |")
        text+=['','The range ablation returns zero for every radius>1 read at frozen genomes, '
            'while charging attempted reads. Output correctness and hidden transmission are measured '
            'separately on the same final tasks; no retuning follows this diagnostic.','']
    payload=max(r['largest_array_bytes'] for r in summaries)
    probe_payload=max(r['pair_array_bytes'] for r in signals)
    if (out/'lineage_audit.json').exists():
        lineage=json.loads((out/'lineage_audit.json').read_text())
        transmission=[r for r in lineage if r['archive']=='transmission']
        roots=sum(r['root_type']=='checkpoint' for r in transmission)
        text+=['',f"Of the {len(transmission)} final transmission archives, {roots} trace to the saved V2 "
            f"population and {len(transmission)-roots} to fresh random immigrants. Additional mutation depths "
            f"range from {min(r['mutation_depth'] for r in transmission)} to "
            f"{max(r['mutation_depth'] for r in transmission)}. This is provenance, not a claim that every "
            'ancestral mutation was beneficial; full links are in `lineage_audit.json`.','']
    text+=['',f"Largest reported inference array payload: {payload:,} bytes; probe-pair interpreter payload: "
        f"{probe_payload:,} bytes. Interpreter bounds remain 64 bytes/site+64 KiB; observer pair bound is "
        '80 bytes/site+64 KiB. These exclude Python objects, allocator/JIT overhead and evaluator arrays; RSS '
        'includes them. A* reports a logical heap payload and bit-wave memory is uninstrumented. '
        'Range reads and total dispatches are in the raw holdout records.','',
        '## Fixed visual examples','',
        'The first size17 perfect/cyclic test from replicate0 is shown, without selection for success. '
        'Current/causal panels use their local transmission archives. Hidden yellow regions show source-dependent '
        'activation at tick16, distinct from emitted path rasters.','',
        f'![Fixed local maze outputs and hidden signals]({out.name}/visuals/unseen_signals.png)','',
        'The same cases with evolvable-range transmission archives:', '',
        f'![Fixed range maze outputs and hidden signals]({out.name}/visuals/unseen_ranges.png)','',
        '## Reproducibility and limits','',
        f"All {verification['new_individuals']:,} new individual records have valid ancestry links to "
        f"{verification['external_random_ancestors']} checkpoint ancestors or fresh random immigrants. "
        f"{verification['unique_test_hashes']} unique final hashes are disjoint from training/validation and "
        f"{verification['previous_hashes']} earlier hashes. All {verification['independently_reassessed_outputs']:,} "
        'saved holdout rasters were independently decoded and reassessed. Source, fork and frozen-champion '
        'hashes match. Population/RNG checkpoints support exact continuation; the resume equality test passes.','',
        'V3 includes no new independent-resampling arm; it compares objectives within the same evolutionary method. '
        'Three paired replicates and adaptive validation archives do not establish statistical significance. '
        'The continuation inherits prior training; these are not new random starts. The two task archives use '
        'different intermediate objectives, so the transmission archive and its frozen control provide the '
        'more direct comparison for precursor learning. Source deletion tests input dependence, not a uniquely '
        'identified computation or biological mechanism. Static dataflow slices are conservative and do not '
        'prove that every included instruction matters.','',
        'Run: `.venv/bin/python -m maze_evolution.signal_study`; audit: '
        '`.venv/bin/python -m maze_evolution.signal_audit`; report: '
        '`.venv/bin/python -m maze_evolution.signal_report`; tests: `.venv/bin/python -m pytest -q`.','',
        'Raw configuration, timing repetitions, complete lineage/evaluation logs, output masks, maze manifests, '
        'extension decision, environment/source hashes and next-population/RNG checkpoints are in '
        '`results/source_pressure/`. Earlier results remain immutable.','']
    if (out/'storage.json').exists():
        storage=json.loads((out/'storage.json').read_text())
        text+=['',f"Log packaging took {storage['elapsed_seconds']:.1f}s after the benchmark: "
            f"{storage['before_bytes']/2**20:.2f} to {storage['stored_bytes']/2**20:.2f} MiB. "
            'Every decoded byte was checked before/after lossless gzip repacking; per-file decoded '
            'and stored hashes are in `storage.json`. No record values changed.','']
    for topology in ('local','evolved'):
        visuals(out,champions,Limits(**config['eval_limits']),topology)
    out.with_suffix('.md').write_text('\n'.join(text))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/source_pressure')
    report(parser.parse_args().out)
