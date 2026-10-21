"""Render completed M2 findings from frozen JSON summaries; no new inference."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.wave_accessibility import OUT

def read(n):return json.loads((OUT/n).read_text())
s=read('screen_summary.json');f=read('final_summary.json');sa=read('screen_audit.json');fa=read('final_audit.json')
ss=read('screen_session.json');fs=read('final_session.json');a=read('anchors.json')
lines=['# M2: wave mutation accessibility and retention','',
'This is a fixed-parent assay around two deliberately selected M1 random-origin lineages. '
'It tests local accessibility under the unchanged generic mutation operator; it is not a continuing '
'evolution run or a replicated policy-efficacy experiment. Both old genomes remain preserved.','',
'## Untouched confirmation','',
f"All frozen nominees and reference models were assessed on {f['queries']:,} new inputs, "
'including 400 complete two-goal pairs, 200 corridors, 256 ordinary reachable queries '
'(128 bases in both poses), and 168 disconnected queries. Sizes15 were absent from M2 screening. '
'Structured tasks reuse the existing grammar; variants and poses are correlated.','',
'| Nomination | Identity | Pairs /400 | Ordinary bases /128 | New / lost pairs vs anchor | Acquisition | Broad |',
'|---|---|---:|---:|---:|---|---|']
for n in f['nominees']:
    v=n['feature']['versus'].get(n['anchor']);m=n['feature']['metrics']
    lines.append(f"| {n['label']} | {n['identity']} | {m['paired']} | {m['ordinary_bases_both_poses']} | {str(v['new_pairs'])+' / '+str(v['lost_pairs']) if v else 'N/A'} | {v['acquisition_gate'] if v else 'N/A'} | {v['broad_transfer_flag'] if v else 'N/A'} |")
lines+=['','Unchanged anchor fallbacks and random draws are never credited as acquired mutant abilities. '
'Acquisition requires eight new complete pairs across two contexts, 90% retention of anchor paired, '
'corridor and ordinary-base successes, and no increase in false no-path. Broad additionally requires '
'four new ordinary bases including both perfect and random families. Partial coverage alone is not a solution.','',
'## Anchor and candidate detail','']
for i,m in f['all_models'].items():
    if i.startswith('control/'):continue
    lines += [f'### {i}','',f"Complete pairs: {m['paired']}; ordinary bases in both poses: {m['ordinary_bases_both_poses']}; false reachable no-path: {m['false_no_path']}.",'',
    '| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |','|---|---:|---:|---:|---:|---:|']
    for domain,v in m['by_domain'].items():
        lines.append(f"| {domain} | {v['inputs']} | {v['optimal']} | {v['valid']} | {v['correct_no_path']} | {v['false_no_path']} |")
    lines+=['','Pair strata: '+', '.join(f"{k}={v['correct']}/{v['opportunities']}" for k,v in m['by_pair_stratum'].items())+'.','']
lines+=['## Development neighborhood frequencies','',
'Each anchor received 4,096 independent one-opportunity and 4,096 independent two-opportunity draws. '
'Two-opportunity intermediates were not evaluated or selected during screening. A separate shared pool '
'contained 4,096 wholly random genomes. Duplicate/no-op draws remain in the records; physical exact '
'genotype evaluations were reused. Original M1 aggregate ranking and retention/selectivity ranking '
'saw the same fixed pool. The latter changes both retention and ordering, so their effects are not isolated.','',
'| Anchor / depth | Draws | Changed genotype | Distinct genotypes | Retains every correct query | Gains any pairs | Acquisition gate | Broad flag |',
'|---|---:|---:|---:|---:|---:|---:|---:|']
for k,v in s['cohorts'].items():lines.append('| '+k+' | '+' | '.join(str(v[c]) for c in ('draws','changed','distinct_genotypes','retained','gained_pairs','acquisition','broad'))+' |')
lines+=['','These are DEVELOPMENT frequencies over highly correlated neighbors, not independent discovery probabilities. '
'One or two mutation opportunities do not guarantee that one or two functional changes survive. '
'All intermediate genomes, operator events and complete initial/final RNG states are saved. '
'Ancestors are the M1 accumulating-wave g24/b39 and delayed-wave g84/b11 genomes, selected before M2 screening.','',
'## Compute, audit and limits','',
'| Phase | Physical calls | Summed candidate seconds | Wall seconds | Work units |',
'|---|---:|---:|---:|---:|']
for label,x in [('Screen',ss),('Confirmation',fs)]:
    u=x['usage'];lines.append(f"| {label} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {x['wall_seconds']:.2f} | {u['work']:,} |")
lines+=['',f"Screen nominal slots: {s['logical_slots']:,} models × {s['queries']} queries. "
 f"Physical models: {s['physical_models']:,} screening; {f['physical_models']} confirmation. "
 f"Observed process-tree RSS peaks: {ss['rss_peak_bytes']/2**30:.3f}GiB screen, {fs['rss_peak_bytes']/2**30:.3f}GiB confirmation. "
 'Ten local workers. Candidate time is summed across workers, not elapsed time. '
 'Conventional baselines are correctness controls; no latency/speedup claim.','',
 f"Screen audit PASS: all {sa['pool_draws_replayed']:,} pool draws, {sa['mutation_events_replayed']:,} mutation events, "
 f"RNG, corpus, task specs and nominations reproduced; {sa['independent_grades']:,} independent grades and "
 f"{sa['native_replays']:,} fixed native samples, {sa['wall_seconds']:.2f}s additional wall. "
 f"Final audit PASS: all {fa['native_replays']:,} physical candidate responses and {fa['baseline_replays']:,} "
 f"conventional baseline calls replayed; {fa['wall_seconds']:.2f}s additional wall. "
 'Production mutation and VM code are shared in replay; the raster grader is independent, not a second complete VM.','',
 'BFS, A*, bit-wave and separately labelled intact flat/modular controls solve the full confirmation panel. '
 'No known solver enters any candidate ancestry; inference receives only maze cells and endpoints. '
 'The oracle precision diagnostic applies only to unique-route fork/corridor tasks and never repairs emitted rasters.','',
 'Finite generic neighborhoods cannot establish that larger architectures, neutral drift, regulation or sustained '
 'evolution will fail. Conversely, narrow structured improvements do not establish general solving. '
 'The exact nominated candidate capability is the confirmation claim; why a selection policy works remains untested.','']
(OUT/'report.md').write_text('\n'.join(lines))
print(OUT/'report.md')
