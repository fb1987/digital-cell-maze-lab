"""Build descriptive M9 tables from audited evidence, with no new evaluation."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.conditional_regulation import OUT,check,readz
check()
assert not (OUT/'report.md').exists()
s=json.loads((OUT/'summary.json').read_text());d=json.loads((OUT/'saved_diagnostics.json').read_text());p=json.loads((OUT/'preservation.json').read_text())
sessions={k:json.loads((OUT/f).read_text()) for k,f in [('search','session.json'),('final','final_session.json')]}
audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in sessions}
assert all(a['status']=='PASS' for a in audits.values())
f=json.loads((OUT/'choices_freeze.json').read_text());policy=s['policy_comparison'];conditions=s['conditions']
primary=[c for c in conditions if c['rank']==0]
passes=sum(c['integration']['integration_pass'] for c in primary)
lines=['# M9 conditional-regulation evolution: audited results','',
f"The fixed primary comparison yields **{passes}/6 integrated nominees passing full integration**, with regulation support **{policy['regulation_support']}** under the registered three-pair rule. These counts concern six nominee roles, not independent origins. Search completed {sessions['search']['generation']} matched rounds and stopped for `{sessions['search']['stop']['reason']}`.",'',
'## What was tested','',
'Three paired populations per arm, six populations of96. Each pair began with identical ordered genomes and RNG:43clones each of exact M7 quota0 child and its immediate parent, plus ten protected references including the shared0 repair. M9 inherited these random-origin lineages explicitly; it did not insert a known solver or promote an M8 intervention. Histories share origins.','',
'The regulation arm used a 50/50 mixture of a uniformly chosen valid gate for the last C6 writer and the unchanged generic mutation operator forced to destination block6. Global used the unchanged M1 whole-genome operator. Both produced45mutation births and7random immigrants perround, with44survivors and16archive slots. The M1 runtime remained unchanged. The combined operator changes both locality and gate frequency; this is not a gate-only causal test.','',
'Both arms used a new common integration-oriented ranking, finite-batch neutral reserve, coverage preservation and lexicase. Ranking favored no false disconnection, minimum nonempty fixed-parent skill retention, specialist-only pair coverage, mean retention, then the existing domain-balanced score. Neutral intermediates could still survive and reproduce. Both curricula mixed short-route retention tasks with longer challenges. Thus only the operator differs between arms, while comparisons to M7 also involve common selection/curriculum changes.','',
'Nominal allocations are identical:96×48 queries pertraininground and115×392 perassessment perpopulation, including nonselectable A0 padding. Identical genotype/query work is physically deduplicated. Equal logical budgets are not equal CPU. Fresh confirmation has1680inputs:400completepairs,200corridors,256ordinarybases in two poses,168disconnected. All prior and setup/search layouts were excluded. Familiar grammars and correlated poses limit generalization claims.','',
f"Registration `7d1199a` was pushed before search. Exact choices, roots, parents, ancestry and final states were pushed as `{f['commit'][:7]}` BEFORE fresh confirmation generation. The fixed integrated, upstream-exploratory and ordinary roles were not changed on final data.",'',
'## Primary integration endpoint','',
'Passing requires positive M9 mutation depth, zero false no-path,100% retention of fixed-parent complete pairs/corridors/ordinary-both-pose/correct-disconnection sets, and ALL specialist-only complete pairs. Every parent denominator must be nonempty; specialist targets must contain at least8pairs across2templates. Primary score is specialist-pair count only on full PASS, otherwise0. Descriptive arm support requires positive differences in2/3pairs and a positive sum; secondary roles cannot rescue it.','',
'| Pair | Global score | Regulation score | Difference |','|---|---:|---:|---:|']
for q in policy['pairs']:lines.append(f"| {q['replicate']} | {q['global']} | {q['regulation']} | {q['difference']} |")
lines+=['',f"Positive pairs: {policy['positive_pairs']}/3; summed difference: {policy['total_difference']}. This is a descriptive pilot criterion, not a significance test.",'',
'| Integrated role | M9 mutation depth | Pairs /400 | Corridors /200 | Ordinary /256 | Correct no-path /168 | False no-path | Specialist targets retained | Full gate |',
'|---|---:|---:|---:|---:|---:|---:|---:|---|']
for c in primary:
 m=c['metrics'];v=c['integration'];lines.append(f"| {c['condition']} | {c['mutations']} | {m['paired']} | {m['by_domain']['corridor']['optimal']} | {m['ordinary_bases_both_poses']} | {m['correct_no_path']} | {m['false_no_path']} | {v['specialist_pairs_retained']}/{v['specialist_new_pairs']} | {v['integration_pass']} |")
lines+=['','## Fixed references on the same confirmation cases','',
'| Reference | Pairs | Corridors | Ordinary both poses | Correct no-path | False no-path |','|---|---:|---:|---:|---:|---:|']
for key in ('m9/reference/quota_parent','m9/reference/quota_child','m9/reference/shared_child','m9/reference/anchor/0'):
 m=s['all_models'][key];lines.append(f"| {key} | {m['paired']} | {m['by_domain']['corridor']['optimal']} | {m['ordinary_bases_both_poses']} | {m['correct_no_path']} | {m['false_no_path']} |")
lines+=['','Cross-phase raw totals are not acquisitions. All gains/losses below compare the same M9 inputs. Protected references have zero new M9 mutation births; reference integration diagnostics are capability comparisons only.','',
'## All fixed nomination roles and separate deeper endpoint','',
'| Condition/role | Genome | Integration | New deeper pairs beyond root+union | Deeper gate | Long-ordinary gate |',
'|---|---|---|---:|---|---|']
for c in conditions:
 lines.append(f"| {c['condition']}/{c['role']} | {c['child']} | {c['integration']['integration_pass']} | {c['beyond_root_and_protected_union']['new_upstream_pairs']} | {c['upstream_acquisition']} | {c['long_ordinary_acquisition']} |")
lines+=['',
'The separate deeper criterion requires8new nonforkprefix2+ pairs across2contexts absent from exact root AND all ten protected references,90% own-root skills and nonempty A0 correct-disconnection retention, zero false no-path and positive M9 mutation depth. Long ordinary requires4new8+edge bases, including16+ and both perfect/random families, under those retention conditions. Integration of prefix0/1skills alone does not pass either endpoint.','',
f"The18nominee roles represent {d['nominee_identities']} identities and {d['nominee_genotypes']} distinct genotypes. These aliases are not independent replications. Full fixed-parent/specialist/own-root/immediate-parent/frozen-reference comparisons and queried-only length strata are in summary.json; saved_diagnostics.json records individual new/lost pair classes, corridor losses and ordinary route lengths.",'',
'## Ancestry, persistence and actual operator allocation','',
f"M9 created {d['birth_counts'].get('mutation',0):,} mutation births and {d['birth_counts'].get('immigrant',0):,} new random immigrants. Preserved M7/M6/M3/M2 ancestry is not counted as M9 acquisition. A clonal founder also contributes no new mutation. Same-panel neutral behavior does not establish universal equivalence.",'',
'| Population | Actual mutation operators |','|---|---|']
for pop,ops in sorted(audits['search']['reserved_birth_counts'].items()):lines.append(f"| {pop} | {json.dumps(ops,sort_keys=True)} |")
lines+=['',
'The audit field reserved_birth_counts is a retained storage-field name; in M9 its keys count actual mutation operators, not breeding quotas. M9 has no quota. Saved diagnostics export per-root birth counts, parent-depth histograms and live/archive persistence at each assessment, so repeated root sampling can be distinguished from sustained descendants.','',
'## Evaluation, audits and preservation','',
'| Phase | Physical calls | Candidate seconds | Worker CPU seconds | Wall seconds | Recorded work | Sampled RSS GiB |',
'|---|---:|---:|---:|---:|---:|---:|']
for name,x in sessions.items():
 u=x['usage'];lines.append(f"| {name} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {x['wall_seconds']:.2f} | {u['work']:,} | {x['rss_peak_bytes']/2**30:.3f} |")
lines+=['',f"Per-population nominal counts: `{json.dumps(next(iter(audits['search']['logical_query_counts'].values())),sort_keys=True)}`. All six allocations match. There were zero uncertain attempts or guard bypasses. Audit work is additional, not included in these inference figures; these are not warmed conventional-solver latency benchmarks.",'',
f"First search audit PASS: {audits['search']['independent_grades']:,} independent saved grades, {audits['search']['native_replays']:,} fixed native samples, all {audits['search']['births_replayed']:,} births and {audits['search']['stages']} stage transitions/RNG, frozen artifacts and corpus/chain verification, in {audits['search']['wall_seconds']:.2f}s. First final audit PASS: ALL {audits['final']['native_replays']:,} native candidate responses plus {audits['final']['conventional_calls']:,} conventional evaluations, in {audits['final']['wall_seconds']:.2f}s. Shared production VM/reproduction with an independent raster grader, not a second interpreter.",'',
'Both intact controls and BFS/A*/bit-wave solve every final input. Nine focused software checks passed; not a full-suite claim. The discarded preflight replayed1,248births and used54,752candidate calls,35.14candidate seconds, plus784assessment-control and3,360final-control calls. Its8,304generated/rejected/unqueried layouts were excluded. No scientific source repair or failed scientific audit occurred.','',
f"All310registration hashes and326priorM8completion hashes verify. Guarded SQLite-API search/final backups match every table and pass integrity checks. Preservation uses {p['storage_bytes']/2**30:.3f}GiB with {p['disk_free_bytes']/2**30:.2f}GiBfree, within6GiBtotal/16GiBfree bounds. All {p['whole_layouts']:,} cumulative layouts are exported: {p['initial_layouts']:,}initial, {p['search_new_layouts']:,}search and {p['final_new_layouts']:,}final generated/rejected/unqueried layouts. Original journals remain local scientific records; compact evidence is published.",'',
'No final-data reselection, new inference, temporal tracing, recombination or further evolution was performed for this report. No general-solver, multirange or speed advantage is established by this experiment. See the interpretation in this report for the next recommendation; no phase beyond M9 has launched.','']
(OUT/'report.md').write_text('\n'.join(lines))
print('Wrote audited M9 tables; review and append interpretation before sealing.')
