"""Create factual M29 report once, before explicit interpretation review/seal."""
import json,statistics,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.state_interference import OUT,RUN,check,readz


def main():
    check();p=OUT/'report.md';assert not p.exists()
    s=json.loads((OUT/'summary.json').read_text());i=json.loads((OUT/'interpretation.json').read_text());t=json.loads((OUT/'target_timing_note.json').read_text())
    session=json.loads((OUT/'session.json').read_text());audit=json.loads((OUT/'audit.json').read_text());pres=json.loads((OUT/'preservation.json').read_text())
    launch=json.loads((OUT/'launch.json').read_text());reg=json.loads((OUT/'registration.json').read_text());assert audit['status']=='PASS'
    arrays=[x['array_bytes_model']/x['recipient_array_bytes'] for x in i['isolation_cost_details']]
    work=[x['work']/x['recipient_work'] for x in i['isolation_cost_details']]
    changed=[e for e in i['coupling_edge_details'].values() if e['history_changed']]
    lines=['# M29: what state insulation does—and what it does not explain','',
      '**Insulating the two parental processes preserves them exactly. However, the proposed wrong-context explanation was not detected at the transplanted C6 writer.** The regulated child changes which parental C6 values are emitted; that signal subsequently changes the C2 output. No combined maze solver was produced.','',
      'All results below use previously observed development mazes. This is mechanism evidence, not independent confirmation or a new evolutionary search.','',
      '## Frozen material and questions','',
      f"Registration `{launch['registration_commit'][:7]}` ({len(reg['files'])} hashes) and the full source/corpus/intervention/job manifests were pushed before scientific execution. All 15 complementary parental genotypes from M28, all 38 pairs, and the fixed regulated nominee are retained unchanged: 16 source models. The source ancestry remains random-origin and related; no founder/history reset, known solver, new breeding genome, fitness selection or cloud compute.",'',
      'The fixed 69 used inputs contain all eight opposite-pose target inputs, all 28 focal donor-corridor losses, the 12 new single-sided fork responses and 12 failed alternatives, three metadata-selected disconnections, four metadata-selected longer ordinary inputs, and the old 16-edge witness in two poses. Source-phase namespacing prevents identical old case IDs from aliasing different layouts. Selection uses queried inputs only.','',
      '## Exact insulation feasibility','',
      f"All {s['native']['executions']} passive traces match the original M18 native response and work counters exactly. All {s['native']['saved_row_matches']} available original saved rows also reproduce. All completed-tick states are retained, with normal stopping and no forced continuation.",'',
      f"A separate diagnostic interpreter places the original programs in two insulated ten-channel banks. All {s['isolation']['pair_executions']} executions / {s['isolation']['bank_comparisons']} bank comparisons reproduce **every parent state at every completed tick, all terminal fields and all work counters**, with each bank frozen after its own stop. This includes all 38 pairs on the eight targets and the focal pair on the other 61 cases.",'',
      'The fixture has **20 persistent channels, independent quiet/stop latches and independent original per-bank caps**. The sum of inherited instructions fits 256; primitives and the 31-node writer limit remain unchanged. Each bank still has 256 ticks, 4,096 reads per site and 32,768 dispatches per site. The total permitted work can therefore be twice the single-organism ceiling. It produces **two internal rasters and no selector**. It is not a combined solver, an evolved organism, or a free ensemble.','',
      f"The modeled array footprint excluding trace is {min(arrays):.3f}–{max(arrays):.3f}× the recipient's, median {statistics.median(arrays):.3f}×. Work is exactly the sum of the two original executions: {min(work):.3f}–{max(work):.3f}× the recipient's, median {statistics.median(work):.3f}×. This ratio can exceed two because the other parent can take much more work than the recipient. Maximum modeled pair arrays: {s['isolation']['max_pair_array_bytes']:,} bytes; maximum separate full trace allocation: {s['isolation']['max_trace_allocation_bytes']:,} bytes. Python/wrapper temporaries are outside that array model; sampled process RSS is reported below.",'',
      'A conservative structural sharing construction gives widths of 18 channels for 4 pairs, 19 for 22 pairs, and 20 for 12 pairs. It only shares byte-identical writers/ports/initialization with closed full-execution dependencies. This is a **sufficient direct-copy width, not a semantic minimum**, a proof that ten channels are insufficient, or evidence that evolution needs twenty. Common expressions and semantically irrelevant code could allow a better representation.','',
      '## The C6 shared-state hypothesis did not pass its intended test','',
      '| Contrast against the regulated child | Cases with some state divergence | Cases where the original C6 expression changes on the child’s state | Verified native next-C6 updates |',
      '|---|---:|---:|---:|']
    for role in ('recipient','donor'):
        c=s['contexts'][role];lines.append(f"| {role} | {c['state_divergence_cases']}/{c['cases']} | {c['context_sensitive_writer_cases']} | {c['native_writer_next_tick_checks']:,} |")
    lines += ['',
      'Across 3,150 native next-writer checks and 3,150 matched borrowed-context evaluations, neither original C6 expression changed its result on the fused organism’s state within the common recorded windows. Consequently no scientific channel-restoration intervention was triggered. The positive restoration branch is exercised nonvacuously in the discarded artificial preflight; zero triggered interventions in the real study is not a failed positive control.','',
      'This contradicts the specific expectation that the imported C6 expression would fail because its parent’s state context was missing in these cases. It does **not** rule out state interference at another writer, another stage, later unrecorded ticks, a different genotype, or through global stopping/budget costs.','',
      '## What the saved traces do show','',
      f"The parents' C6 values differ on {i['focal_summary']['cases_with_parent_C6_value_disagreement']}/69 cases. The regulated child uses recipient values at disagreeing sites/ticks on {i['focal_summary']['cases_using_recipient_values']} cases and donor values on {i['focal_summary']['cases_using_donor_values']}. Every recorded regulated C6 value equals one of the two native parent values in the common window. This agrees with M28's actual genotype: two expressions followed by a local SELECT, rather than a preserved second complete process.",'',
      f"Relative to the recipient, the child's first state difference is C6 in 48 cases; there is no state difference in the common window in the other 21. In {t['cases_with_C6_then_C2']} cases, a C2 difference appears after the C6 difference. These timings show propagation, but temporal order alone is not a causal proof of the entire maze failure.",'',
      'The prospective coupling interventions provide a stronger local causal result. All 37 output/halt-cone port positions were tested, each on all eight target inputs. Only four positions change the receiver’s history; each changes the final raster on all eight inputs. All 296 uncoupled donor banks remain exact.','',
      '| Receiving bank | Receiver writer | Crossed physical input channel | History changes | Final raster changes |',
      '|---|---:|---:|---:|---:|']
    for e in changed:lines.append(f"| {e['edge'][0]} | C{e['edge'][1]} | C{e['physical_cross_channel']} | {e['history_changed']}/{e['cases']} | {e['mask_changed']}/{e['cases']} |")
    lines += ['',
      'The four active positions are C2 reading the other bank’s **C2 self-feedback or C6 control signal**, once in each direction. These are controlled port changes with the donor process unchanged, so this establishes an output-sensitive coupling interface on the tested cases. It does not establish a useful solving policy.','',
      'The other 33 port changes preserve both full histories and all response/work fields across the eight targets. They are structurally connected but observationally neutral here; we have not demonstrated that they carry useful information. Do not treat this posthoc neutral subset as a prevalidated set of beneficial future mating sites.','',
      f"An explicitly secondary saved-response check evaluates each diagnostic bank as a fixed bank across all cases: all {len(t['all_fixed_bank_target_results'])} edge/bank combinations solve zero of the four targets in both poses. No bank is chosen per case. There is no hidden successful combination among these one-port interventions, and no new complete solving claim.",'',
      '## Work, verification and preservation','',
      '| Execution category | Science | Audit |',
      '|---|---:|---:|',
      '| Original native VM calls | 311 | 311 |',
      '| Passive trace calls | 311 | 311 |',
      '| Insulated two-bank kernel calls | 365 | 365 |',
      '| Coupled two-bank kernel calls | 296 | 296 |',
      '| Full-grid writer evaluations | 6,300 | 6,300 |','',
      f"Science: {session['totals']['executions']:,} unlike execution units, {session['totals']['counted_work']:,} counted reads+dispatches, {session['totals']['seconds']:.3f} summed execution wall seconds, {session['totals']['cpu_seconds']:.3f} worker CPU seconds, {session['wall_seconds']:.3f} phase wall seconds, {session['rss_peak_bytes']/2**30:.3f} GiB sampled process-tree RSS. Do not interpret the mixed execution-unit count as equal-cost candidate evaluations.",'',
      f"ALL-job audit PASS first attempt: {audit['all_jobs_replayed']:,} job records, all {audit['totals']['executions']:,} execution units, every native field, history byte/hash, source response, grade, work count, structural graph, corpus, job order and summary. Audit wall {audit['wall_seconds']:.3f} s; worker CPU {audit['totals']['cpu_seconds']:.3f} s; peak sampled RSS {audit['rss_peak_bytes']/2**30:.3f} GiB. This is the same diagnostic implementation replay, checked against the frozen original VM and independent raster grader—not a second fully independent VM proof or warmed latency benchmark.",'',
      'Eight focused tests pass, not the full repository suite. Tests cover tight-budget native equivalence, separate stop latches, old-snapshot cross-bank reads, one-way causality, dependency closure, writer execution and bounded divergence windows. The discarded four-phase artificial preflight used two already excluded cases and 74 execution units, including an exact single-channel restoration. Two test-harness failures and one preparation query-filter failure are preserved before registration. No registered scientific failure, source repair, guard bypass or failed resume occurred.','',
      f"All 437 prior M28 sealed files and 25 local records are unchanged. Original history-bearing SQLite and its verified SQLite-API backup pass integrity and ALL-table comparison. Phase storage at preservation: {pres['storage_bytes']/2**20:.2f} MiB; free disk {pres['disk_free_bytes']/2**30:.2f} GiB, within 2 GiB phase storage / 16 GiB disk floor. All {pres['queried_orbit_hashes']} distinct queried pose hashes already belong to the immutable 3,998,785-layout ledger; zero new layouts. Reference bases remain required; raw SQLite is kept out of Git.",'',
      '## Reviewed interpretation and recommendation','',
      'Pending explicit review against the actual records.','']
    p.write_text('\n'.join(lines))


if __name__=='__main__':main()
