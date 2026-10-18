"""V11 scientific report and static figures from frozen, independently audited data."""
import argparse,csv,gzip,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from .experiment import write_json
from .factor_report import paired_summary
from .growth import Genome
from .growth_audit import unpack
from .range_audit import output_dataflow
from .signal_audit import lines


def visuals(out,manifest,primary,paired,history):
    from PIL import Image,ImageDraw
    (out/'visuals').mkdir(exist_ok=True);lookup={m['case_id']:m for m in manifest}
    def grid(draw,x,y,m,mask,tile=10):
        for p,opened in enumerate(bytes.fromhex(m['cells_hex'])):
            color='#172235' if not opened else '#5ae1bd' if mask[p] else '#45536a'
            if p==m['start']:color='#72b6ff'
            if p==m['goal']:color='#ff6584'
            xx,yy=x+p%m['w']*tile,y+p//m['w']*tile
            draw.rectangle((xx,yy,xx+tile-1,yy+tile-1),fill=color)
    canvas=Image.new('RGB',(1200,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Unseen normal outputs | green: output; blue: source; pink: goal. First size17 case/family,replicate0.',fill='#e6edf7')
    arms=('compiled_bfs','local/cap128/task','local/cap256/task','evolved/cap128/task','evolved/cap256/task')
    for i,family in enumerate(('perfect','random')):
        m=next(m for m in manifest if m['split']=='test_goal' and m['w']==17 and m['family']==family and '/r0/' in m['case_id'])
        for j,arm in enumerate(arms):
            r=next(r for r in primary if r['arm']==arm and r['case_id']==m['case_id']);x,y=15+j*240,85+i*245
            draw.text((x,y-40),arm,fill='#e6edf7');draw.text((x,y-22),family+' | '+('shortest' if r['optimal'] else r['failure']),fill='#aabbd0')
            grid(draw,x,y,m,unpack(r['mask'],m['w']*m['h']))
    canvas.save(out/'visuals/unseen_outputs.png')
    pair=next(p for p in json.loads((out/'pairs.json').read_text()) if p['first'].startswith('test_pairs/r0/') and '/17x17/' in p['first'] and '/random/' in p['first'])
    arms=('compiled_bfs','evolved/cap128/choice','evolved/cap256/choice','evolved/cap256/frozen_choice')
    canvas=Image.new('RGB',(960,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Switched goals | BFS route vs fixed tick16 raster. Probe output does not imply an emitted complete route.',fill='#e6edf7')
    for i,case in enumerate((pair['first'],pair['second'])):
        m=lookup[case]
        for j,arm in enumerate(arms):
            if arm=='compiled_bfs':r=next(r['baseline'] for r in paired if r['arm']==arm and r['baseline']['case_id']==case);mask=unpack(r['mask'],m['w']*m['h']);subtitle='Shortest'
            else:
                rr=next(r for r in paired if r['arm']==arm and r['replicate']==0);r=next(r for r in rr['cases'] if r['case']==case)
                mask=unpack(r['probe_mask'],m['w']*m['h']);subtitle=f"Tick16 J={r['junction']['score']:.3f}"
            x,y=15+j*240,85+i*245;draw.text((x,y-40),arm,fill='#e6edf7');draw.text((x,y-22),f"Goal{'A' if i==0 else 'B'} | {subtitle}",fill='#aabbd0');grid(draw,x,y,m,mask)
    canvas.save(out/'visuals/switched_goals.png')
    canvas=Image.new('RGB',(1200,470),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((20,15),'Heritable growth | mean across3 replicates | evaluated populations,not the prepared next population',fill='#e6edf7')
    colors={'local/cap128':'#72b6ff','local/cap256':'#5ae1bd','evolved/cap128':'#b996ff','evolved/cap256':'#ffb765'}
    last=max(int(r['generation']) for r in history)
    for panel,(field,title,lo,hi) in enumerate((('median_genes','Population median genes',64,256),('above128','Population fraction above128 genes',0,1))):
        ox=65+panel*600;oy=360;w=485;h=255;draw.text((ox,65),title,fill='#e6edf7')
        for tick in range(5):
            val=lo+(hi-lo)*tick/4;y=oy-h*tick/4;draw.line((ox,y,ox+w,y),fill='#2c394c');draw.text((ox-40,y-5),f'{val:.2f}' if panel else f'{val:.0f}',fill='#aabbd0')
        for tick in (0,last//2,last):
            x=ox+w*tick/max(1,last);draw.text((x-5,oy+10),str(tick),fill='#aabbd0')
        for arm,color in colors.items():
            points=[]
            for generation in range(last+1):
                rr=[r for r in history if '/'.join(r['condition'].split('/')[1:3])==arm and int(r['generation'])==generation]
                val=statistics.mean(float(r[field])/(96 if field=='above128' else 1) for r in rr)
                points.append((ox+w*generation/max(1,last),oy-h*(val-lo)/(hi-lo)))
            draw.line(points,fill=color,width=3)
        draw.text((ox+w//2-30,oy+32),'generation',fill='#aabbd0')
    for j,(arm,color) in enumerate(colors.items()):
        x=30+j*285;draw.line((x,432,x+25,432),fill=color,width=3);draw.text((x+34,425),arm,fill='#e6edf7')
    canvas.save(out/'visuals/genome_growth.png')
    ancestry=json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read())
    if ancestry:
        record=ancestry[0];nodes=record['nodes'];idx=next(i for i,n in enumerate(nodes) if n['strict_both']);parent=nodes[max(0,idx-1)];child=nodes[idx]
        canvas=Image.new('RGB',(1040,350),'#111827');draw=ImageDraw.Draw(canvas)
        draw.text((15,12),'Selected hard-validation choice | gold: decision. Validation example,not unseen generalization.',fill='#e6edf7')
        for j,(node,i) in enumerate(((parent,0),(child,0),(parent,1),(child,1))):
            r=node['cases'][i];m=lookup[r['case']];x,y=15+j*260,100;tile=16 if m['w']<=9 else 11
            draw.text((x,50),('Parent' if j%2==0 else 'First qualifying')+f" | goal{'A' if i==0 else 'B'}",fill='#e6edf7')
            draw.text((x,72),f"J={r['junction']['score']:.3f}; strict={r['junction']['strict']}",fill='#aabbd0')
            grid(draw,x,y,m,unpack(r['probe_mask'],m['w']*m['h']),tile);v=record['decision']['vertex'];xx=x+v%m['w']*tile;yy=y+v//m['w']*tile
            draw.rectangle((xx,yy,xx+tile-1,yy+tile-1),outline='#ffd46a',width=2)
        canvas.save(out/'visuals/validation_choice.png')


def report(out):
    out=Path(out);read=lambda p:json.loads((out/p).read_text());env=read('environment.json');v=read('verification.json');gate=read('extension_decision.json');champions=read('champions.json')
    primary=list(lines(out/'holdout.jsonl.gz'));paired=list(lines(out/'paired_holdout.jsonl.gz'));manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());lookup={m['case_id']:m for m in manifest}
    with (out/'history.csv').open(newline='') as f:history=list(csv.DictReader(f))
    reachable={m['case_id']:m['oracle_length']>0 for m in manifest};ps=paired_summary(paired,reachable)
    for r in ps:
        rr=[a for a in paired if a['arm']==r['arm'] and 'baseline' not in a]
        for key in ('junction','junction_both','balanced'):r[key]=float(np.mean([a[key] for a in rr])) if rr else None
    write_json(out/'paired_summary.json',ps);pm={r['arm']:r for r in ps};summary={r['arm']:r for r in read('summary.json') if r['group']=='all'}
    txt=['# Heritable program-capacity growth: V11','',
        'Twelve matched conditions continue96 random-origin organisms for48 generations,comparing128-versus256-gene ceilings. '
        'Eight channels,opcodes,ranges,fitness,mutation modes,immigrant lengths and work limits stay common. Correct complete shortest outputs remain primary.','',
        '| Primary task archive | Valid / reachable | Shortest | Distance≥8 shortest | Paired shortest /42 | No-path /48 |','|---|---:|---:|---:|---:|---:|']
    taskarms=[f'{t}/{p}/task' for t in ('local','evolved') for p in ('cap128','cap256')]
    for arm in (*taskarms,'compiled_bfs','compiled_astar','wave_bit'):
        r=summary[arm];txt.append(f"| {arm} | {r['valid']}/{r['reachable']} | {r['optimal']} | {r['long_optimal']}/{r['long_cases']} | {pm[arm]['optimal']} | {r['no_path']} |")
    if (out/'discussion.md').exists():txt += ['',(out/'discussion.md').read_text().strip()]
    txt += ['',f"Extension gate **{gate['extend']}** after {sorted({r['next_generation'] for r in champions.values()})} generations. Only replicated hard-validation transfer could extend training. "
        'More genes,prefix scores or one contextual choice alone cannot. Three replicates give descriptive comparisons; repeated archive copies/contexts are not independent discoveries.','',
        '## Controlled implementation and provenance','',
        'V3 lifts only the bounded gene ceiling. Both arms execute the SAME unchanged V6 normal/probe kernels on the same typed instruction arrays. '
        'Old-program state,normal masks,halt/status,counters and memory match exactly before training. V2 already had1–8-gene block duplication; '
        'all seven mutation modes and cap128 RNG behavior are retained. In cap256,only capacity-dependent insertion/duplication eligibility changes. '
        'Both immigrant factories remain64–128 genes,so extra DNA must grow through inheritance. No known solver enters a lineage. '
        'The old length-descriptor bin remains clamped at3,so expanded programs get no extra niche or size bonus. Unfinished phenotypes get no cost/length penalty.','',
        'Fork matching V10 Fixed population/RNG; preserve native task/choice/J/B/G/source and protected variants from both V10 arms, '
        'strict supplements and every node of the short-cue training primitive in evolved replicate2. All initial genotypes/RNG/protection match between capacities. '
        'New validation archives remain saved without automatically breeding. No cross-topology/replicate transfers. '
        'The common cohort/seed changes make cross-version absolute scores unsuitable as capacity effects.','',
        'The unchanged Choice-first rank is(valid,shortest,no-path utility,strict-both K,smooth shaping,cost only when all ordinary outputs correct). '
        'Case selection prioritizes valid/optimal/paired choice before epsilon.02 shaping. J=.25 source-dependent connected prefix+.75 causal correct-exit choice. '
        'All shortest exits are accepted individually; wrong exits must be off. Oracles/decision labels never enter inference. '
        'Same hard pair distribution in both arms,no near-goal curriculum.','',
        f"Seed{read('config.json')['seed']},independent construction1114,equivalence1113;{env['previous_layouts']} prior layouts excluded. "
        f"Preregistration `{env['parent_revision']}`; frozen model SHA `{env['champions_sha256']}` before final generation. "
        '264 ordinary layouts and24 separate paired layouts/48 inputs are common to both capacities,frozen controls and compiled baselines. '
        'Paired inputs:42 reachable≥8,6 unreachable,18 regular decisions. Source-prefix2..8,goals≥4 beyond,disjoint all-shortest exits; '
        'even indices require deceptive bearing. Ordinary sizes9/17/33/65 include trees,cycles,disconnected and rectangles.','',
        f'![Genome growth]({out.name}/visuals/genome_growth.png)','',
        '## Actual growth and expression','',
        '| Condition | Last evaluated median genes | Last max genes | Last above128 /96 | Mutated children grown | Above128 mutant children | Capacity fallbacks |',
        '|---|---:|---:|---:|---:|---:|---:|']
    events=read('mutation_events.json')
    for condition in sorted(champions):
        h=max((r for r in history if r['condition']==condition),key=lambda r:int(r['generation']));e=events[condition]
        txt.append(f"| {condition} | {float(h['median_genes']):.1f} | {h['max_genes']} | {h['above128']} | {e['grew']}/{e['children']} | {e['above128_children']} | {e['capacity_fallbacks']} |")
    txt += ['', 'Last evaluated population precedes the prepared next-generation checkpoint. Counts repeat genotypes/opportunities. '
        'Every child’s concrete trace is independently reconstructed; cap128 fallbacks retain the old operand mutation. '
        'Extra length is potential capacity,not evidence of effective complexity.','',
        '| cap256 training subset | Evaluations | Mean genes | Valid normals / calls | Strict pair responses | Mean completed normal ticks | Normal budget exhaustion | Work |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    factors=read('capacity_training.json')
    for t in ('local','evolved'):
        for group in ('at_most128','above128'):
            rr=[r for r in factors if r['condition'].split('/')[1:3]==[t,'cap256'] and r['size_group']==group];tot=Counter()
            for r in rr:tot.update({k:v for k,v in r.items() if k not in ('condition','size_group')})
            txt.append(f"| {t}/{group} | {tot['organism_evaluations']} | {tot['sum_genes']/max(1,tot['organism_evaluations']):.1f} | {tot['valid_normals']}/{tot['normal_calls']} | {tot['strict_pairs']} | {tot['normal_steps']/max(1,tot['normal_calls']):.2f} | {tot['normal_budget_exhaustions']} | {tot['work']:,} |")
    coeval=read('mutation_behavior.json')['counts']
    txt += ['', '| cap256 topology | Coeval children that grew | Same recorded behavior | Higher fitness | More work | Fewer completed ticks |',
        '|---|---:|---:|---:|---:|---:|']
    for topology in ('local','evolved'):
        ct=Counter()
        for condition,values in coeval.items():
            if condition.split('/')[1:3]==[topology,'cap256']:ct.update(values)
        txt.append(f"| {topology} | {ct['coeval_grew']} | {ct['grew_same_recorded_behavior']} | {ct['grew_higher_fitness']} | {ct['grew_more_work']} | {ct['grew_fewer_completed_ticks']} |")
    txt += ['', 'Grown versus≤128 within cap256 is a CONDITIONAL lineage/selection comparison,not a randomized subcomparison. '
        'Different programs/cases/nomination overlap can change work and completed ticks. Arm assignment is the controlled capacity comparison.','',
        '## All selected unseen outputs','',
        '| Archive | Shortest / reachable | Paired shortest /42 | Strict both /18 | J |','|---|---:|---:|---:|---:|']
    for arm,r in sorted(summary.items()):
        if '/' in arm:txt.append(f"| {arm} | {r['optimal']}/{r['reachable']} | {pm[arm]['optimal']} | {round(18*pm[arm]['junction_both'])} | {pm[arm]['junction']:.4f} |")
    txt += ['',f'![Unseen outputs]({out.name}/visuals/unseen_outputs.png)','',f'![Switched goals]({out.name}/visuals/switched_goals.png)']
    shapes=[];difficulty=defaultdict(Counter);traffic=defaultdict(Counter)
    from cellular_maze_lab import neighbors
    for r in primary:
        m=lookup[r['case_id']];w=m['w'];arm=r['arm'];start=m['start'];goal=m['goal'];md=abs(start%w-goal%w)+abs(start//w-goal//w);d=difficulty[arm]
        d['false_no_path']+=r['reachable'] and r['status']=='no_path'
        for label,condition in (('turn',start%w!=goal%w and start//w!=goal//w),('detour',r['edges']>md)):
            if r['reachable'] and condition:d[label+'_cases']+=1;d[label+'_optimal']+=r['optimal']
        if '/' not in arm:continue
        t=traffic[arm];ticks=sum(bytes.fromhex(m['cells_hex']))*r['steps'];t['site_ticks']+=ticks;t['copy_bytes']+=32*ticks;t['reads']+=r['reads'];t['dispatches']+=r['dispatches'];t['active']+=r['active']
        if r['valid_path']:
            mask=unpack(r['mask'],w*m['h']);p=start;previous=-1;directions=[]
            while p!=goal:
                q=next(q for q in neighbors(p,w,m['h']) if mask[q] and q!=previous);directions.append(q-p);previous,p=p,q
            shapes.append(dict(arm=arm,replicate=r['replicate'],case=r['case_id'],edges=len(directions),turns=sum(a!=b for a,b in zip(directions,directions[1:])),optimal=r['optimal']))
    write_json(out/'success_shapes.json',shapes);write_json(out/'difficulty_summary.json',difficulty);write_json(out/'inference_traffic.json',traffic)
    txt += ['', '| Task archive | Turn-required shortest | Detour-required shortest | False no-path on reachable |','|---|---:|---:|---:|']
    for arm in taskarms:
        d=difficulty[arm];txt.append(f"| {arm} | {d['turn_optimal']}/{d['turn_cases']} | {d['detour_optimal']}/{d['detour_cases']} | {d['false_no_path']} |")
    for arm in taskarms:
        r=next(r for r in primary if r['arm']==arm and r['reachable'] and not r['optimal'] and lookup[r['case_id']]['w']==17)
        txt += ['',f"Representative {arm} failure:`{r['case_id']}`,oracle{r['edges']} edges;status `{r['status']}`,{r['steps']} ticks,`{r['failure']}`."]
    txt += ['', 'Successful shapes are saved; a short inherited path or endpoint-aware halting does not establish general goal-guided routing. '
        'All valid outputs are still counted. Per-size/family/distance records and every failure remain in raw outputs/summary.','',
        '## Fixed-model diagnostics','',
        'Goal-pulse removal retains static goal flags. Nonlocal ablation zeroes radius>1 reads and charges attempted reads. '
        '8/16/32/64-tick source/junction state changes are communication,not correct choices. Forced probes override ordinary halting. '
        'All intervention rasters,costs,structural opportunity labels and training-source entry checks are saved;no reselection.']
    courses=read('goal_timecourse.json')
    txt += ['', '| Current choice archive | Goal switch changes source state at16 /18 | Junction state at16 /18 | Junction state at64 /18 |',
        '|---|---:|---:|---:|']
    for arm in ('local/cap128/choice','local/cap256/choice','evolved/cap128/choice','evolved/cap256/choice'):
        counts=[sum(r['aligned'] and bool(r[field]) for r in courses if r['arm']==arm and r['horizon']==h) for h,field in ((16,'any_source_state'),(16,'junction_changed_channels'),(64,'junction_changed_channels'))]
        txt.append(f"| {arm} | {counts[0]} | {counts[1]} | {counts[2]} |")
    ancestry=json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read())
    if ancestry:
        txt += ['', '| Hard-validation archive | First qualifying birth | Last J | Last strict both | Last ordinary shortest /2 |','|---|---:|---:|---:|---:|']
        for r in ancestry:
            first=next(n for n in r['nodes'] if n['strict_both']);last=r['nodes'][-1]
            txt.append(f"| {r['condition']} | {first['individual']['birth']} | {last['junction']:.3f} | {last['strict_both']} | {sum(c['optimal'] for c in last['cases'])} |")
        txt += ['',f'![Validation choice]({out.name}/visuals/validation_choice.png)']
    else:txt += ['', 'No primary hard-validation choice archive qualifies on both switched goals. All earlier native variants,including i1472,remain protected.']
    phases=list(lines(out/'phase_transfer.jsonl.gz'));txt += ['', '| Topology/capacity | Training leader generation | Hard-validation strict /12 | Final strict /18 | Final shortest /42 |','|---|---:|---:|---:|---:|']
    for t in ('local','evolved'):
        for cap in ('cap128','cap256'):
            for gen in (15,31,47):
                rr=[r for r in phases if r['condition'].split('/')[1:3]==[t,cap] and r['generation']==gen];a=[r for r in rr if r['split']=='validation_goal'];b=[r for r in rr if r['split']=='test_pairs']
                txt.append(f"| {t}/{cap} | {gen} | {sum(r['strict_pairs'] for r in a)} | {sum(r['strict_pairs'] for r in b)} | {sum(c['optimal'] for r in b for c in r['cases'])} |")
    txt += ['', 'Leaders are frozen before final generation. Boundary batches contain one regular tree pair and one mixed pair,so miss cyclic training opportunities. '
        'Reused-training leader/frozen/final replays are not holdouts;leader replay equals its original full training record exactly.']
    structures=[]
    for saved in champions.values():
        c=saved['config']
        for label in ('task','choice'):
            item=saved['archives'][label]['individual'];g=Genome.from_dict(item['genome']);structures.append(dict(arm=f"{c['topology']}/{c['pressure']}/{label}",replicate=c['replicate'],**output_dataflow(g)))
    write_json(out/'capacity_diagnostics.json',structures);tot=Counter()
    for r in read('mutation_behavior.json')['counts'].values():tot.update(r)
    write_json(out/'mutation_summary.json',tot)
    diag=read('diagnostics.json');storage=read('storage.json');proof=read('equivalence.json')
    txt += ['', '## Real cost and capacity limits','',
        f"Search+validation/probes **{env['training_seconds']/60:.2f}min**;main including final correctness/timing **{env['elapsed_seconds']/60:.2f}min**. "
        f"Main peak **{env['max_rss_bytes']/2**20:.1f}MiB**,{env['cpu']},Python{env['python']},packages `{env['packages']}`. "
        f"{v['normal_maze_evaluations']:,} search normal responses/{v['developmental_probe_runs']:,} probes,"
        f"{v['charged_work']:,} logical dispatch+attempted-read units. These are VM units,not hardware instruction counts. "
        'Extra code consumes the SAME bounded budget and can leave fewer complete ticks.','',
        f"Pre-training parity{proof['elapsed_seconds']:.2f}s,{proof['unique_native_program_topology_pairs']} native program/topology pairs,"
        f"{proof['normal_calls']} normals/{proof['probe_calls']} probes,{proof['charged_work']:,} work. "
        f"Post-freeze diagnostics{diag['elapsed_seconds']:.2f}s,{diag['charged_work']:,} units;compression{storage['elapsed_seconds']:.2f}s;"
        f"audit{v['elapsed_seconds']:.2f}s,audit peak{v['audit_peak_rss_bytes']/2**20:.1f}MiB. Separate audits/replays are outside main elapsed/work.",'',
        'Latency includes decoding,initialization,updates and raster emission. Fitness/oracle/probes are excluded and charged separately. '
        'Same production mutability/dtype/signature warmup,30 randomized repetitions/case,12 cases/arm. Median of case medians and full sample range. '
        'Wrong outputs cannot claim speedup;baseline VM counters are uninstrumented placeholders.','',
        '| Arm | Median case median μs | Warm range μs | Correct timed repetitions | Largest explicit arrays |','|---|---:|---:|---:|---:|']
    timings=read('timings.json')
    for arm in ('compiled_bfs','compiled_astar','wave_bit',*taskarms):
        rr=[r for r in timings if r['arm']==arm];mem=summary[arm]['largest_array_bytes'];memory=f'{mem}B' if mem>=0 else 'unreported'
        txt.append(f"| {arm} | {statistics.median(r['median_us'] for r in rr):.2f} | {min(r['min_us'] for r in rr):.2f}–{max(r['max_us'] for r in rr):.2f} | {sum(r['correct'] for r in rr)}/{sum(r['repeats'] for r in rr)} | {memory} |")
    txt += ['', '| Task archive | Completed site-ticks | Logical state-copy MiB | Neighbor reads | Dispatches | Active fraction |','|---|---:|---:|---:|---:|---:|']
    for arm in taskarms:
        a=traffic[arm];txt.append(f"| {arm} | {a['site_ticks']:,} | {a['copy_bytes']/2**20:,.1f} | {a['reads']:,} | {a['dispatches']:,} | {a['active']/max(1,a['dispatches']):.3f} |")
    txt += ['', 'Eight-channel double buffers stay32N bytes;each completed open-site tick copies32 logical bytes old→new. '
        'This excludes partial ticks,register/gene operations and allocation;cache/compiler effects change DRAM traffic. '
        'Max256-gene array7168B,existing explicit memory ceiling64N+65536 unchanged. Grid propagation and repeated updates remain scaling costs.','',
        f"Selected archive genes{min(r['genes'] for r in structures)}–{max(r['genes'] for r in structures)};conservative output/stop slices "
        f"{min(r['potential_output_stop_genes'] for r in structures)}–{max(r['potential_output_stop_genes'] for r in structures)}. "
        'These are syntactic potential dependencies,not proof of useful effective complexity.','',
        f"Conditional coeval changed-DNA neutrality:{tot['changed_genome_same_behavior']}/{tot['changed_genome']} "
        f"({tot['changed_genome_same_behavior']/max(1,tot['changed_genome']):.1%}) match the saved normal/probe/status/partial/source/goal fingerprint. "
        'Hidden state,expression and work can differ. Full population/RNG,all archived genes and neutral variants remain available.','',
        '## Verification and reproduction','',
        f"All checks pass:{v['source_files']} frozen sources,{v['training_fitness_checks']:,} fitness records,{v['mutation_trace_checks']:,} child traces,"
        f"{v['junction_raster_checks']:,} J rasters,{v['reassessed_training_valid_claims']} valid training claims,{v['replayed_selected_outputs']} selected normal replays,"
        f"{v['phase_reassessed_outputs']} phase-assay outputs,12 each task/choice/J/B archive maxima. "
        'Source/model/lineage/protection/layout/storage and arm ceilings are verified. Unit checks cover exact old mutation RNG,trace replay,bounds,full-state/fitness parity,common primitive cohorts,exact resume,gate and independent full construction through192 generations.','',
        'Commands/protocol:`docs/GROWTH_STUDY_V11.md`;raw results:`results/capacity_growth/`. Earlier source/raw data remain immutable. '
        'Random-origin emergence stays central. A negative bounded experiment cannot establish impossibility of greater capacity,regulation or longer evolution.']
    if (out/'next_experiment.md').exists():txt += ['',(out/'next_experiment.md').read_text().strip()]
    (out.parent/(out.name+'.md')).write_text('\n'.join(txt)+'\n');visuals(out,manifest,primary,paired,history);print(out.parent/(out.name+'.md'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/capacity_growth');report(parser.parse_args().out)
