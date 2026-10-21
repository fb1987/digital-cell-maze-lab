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
'The two-opportunity variant m2/a0/d2/02786 confirms48 new paired successes with no losses:96/400 versus48/400 for its exact anchor, and200/200 corridors retained. It solves9/128 ordinary bases in both poses and passes the registered broad-transfer flag. However, eight of those ordinary routes have only one edge and one has three edges. It still solves zero prefix2/4/8, second-junction and cycle pairs. The formal flag passes, but a general-solver claim is unsupported.','',
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
 'Up to ten local workers. Candidate time is summed across workers, not elapsed time. '
 'Conventional baselines are correctness controls; no latency/speedup claim.','',
 f"Screen audit PASS: all {sa['pool_draws_replayed']:,} pool draws, {sa['mutation_events_replayed']:,} mutation events, "
 f"RNG, corpus, task specs and nominations reproduced; {sa['independent_grades']:,} independent grades and "
 f"{sa['native_replays']:,} fixed native samples, {sa['wall_seconds']:.2f}s additional wall. "
 f"Final audit PASS: all {fa['native_replays']:,} physical candidate responses and {fa['baseline_replays']:,} "
 f"conventional baseline calls replayed; {fa['wall_seconds']:.2f}s additional wall. "
 'Production mutation and VM code are shared in replay; the raster grader is independent, not a second complete VM.','',
 'The first final-audit attempt stopped after all19,936 native replays because intermediate-comparison pair keys were Python tuples versus JSON lists. All scientific values and memberships agreed. A separately committed JSON-only adapter (df6ddaf) reran the unchanged audit; frozen scientific source/results were not edited. The failed attempt adds19,936 native replays and grades; its standalone wall time was not instrumented. See docs/WAVE_ACCESSIBILITY_AUDIT_NOTE.md and the preserved failure packet.','',
 'BFS, A*, bit-wave and separately labelled intact flat/modular controls solve the full confirmation panel. '
 'No known solver enters any candidate ancestry; inference receives only maze cells and endpoints. '
 'The oracle precision diagnostic applies only to unique-route fork/corridor tasks and never repairs emitted rasters.','',
 'Finite generic neighborhoods cannot establish that larger architectures, neutral drift, regulation or sustained '
 'evolution will fail. Conversely, narrow structured improvements do not establish general solving. '
 'The exact nominated candidate capability is the confirmation claim; why a selection policy works remains untested.','']
lines += ['## Mechanism and next research decision','',
 'The successful117-instruction genome changed only output block2: an input-port swap followed by copying an existing XOR node to the output position. It now combines the persistent goal wave with a pre-existing source-flag computation. Six primitive nodes lie in its conservative recurrent output/halt dependency cone. Its emitted raster is exactly a goal-distance ball of radius d-1 plus the source, at2d+1 ticks: all348 reachable development and1,256 reachable confirmation outputs match. This activates previously unused computation, but reaches the same narrow delayed-wave repertoire already present in the other M1 lineage. The immediate intermediate has no new paired successes; no second-edit-only counterfactual was run, so two-mutation necessity is not established.','',
 'Post-hoc terminal-output identity:61–87% of sampled variants match their anchor on every screening raster/status. Across4,096 draws per neighborhood there are only40,107,44 and89 distinct terminal behaviors. This is evidence of many behaviorally neutral sampled changes, not proof of neutrality on all mazes or all internal states.','',
 'Both rankings select the same acquiring variant; the new rule cannot be credited with discovering it. For the delayed-wave anchor, aggregate ranking chooses variants that lose all paired/corridor successes, while retention ranking preserves96 pairs and200 corridors and gains eight ordinary bases. That supports protecting demonstrated skills in this fixed pool, not a causal evolutionary-policy advantage.','',
 'Recommend a separately registered60–90min evolutionary continuation from the preserved random-origin wave lineages, with protected skill archives, neutral behavioral diversity and mixed one/two-opportunity variation. Compare against unchanged variation on equal evaluation allocations. Selection should distinguish longer-route and multiple-junction correctness, not let numerous one-edge examples satisfy a breadth screen. Permit neutral intermediates; no solver primitive or oracle cleanup. Keep the current M2 outcome and its passed flag unchanged. No continuation is launched by this report.','']
(OUT/'report.md').write_text('\n'.join(lines))
print(OUT/'report.md')
