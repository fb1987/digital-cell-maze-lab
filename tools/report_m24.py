"""Saved M24 outcomes only. No inference or case generation."""
import sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.branch_causality import ROOT,OUT,RUN,FOCAL,ROOT_ID,readz,writej,sha,check


def main():
    check();assert not (OUT/'report.md').exists()
    s=json.loads((OUT/'summary.json').read_text());obs=json.loads((OUT/'branch_observation.json').read_text())
    session=json.loads((OUT/'session.json').read_text());audit=json.loads((OUT/'audit.json').read_text())
    trace=json.loads((OUT/'trace_session.json').read_text());ta=json.loads((OUT/'trace_audit.json').read_text())
    osession=json.loads((OUT/'observation_session.json').read_text());oa=json.loads((OUT/'observation_audit.json').read_text())
    prep=json.loads((OUT/'preflight.json').read_text());preparation=json.loads((OUT/'preparation.json').read_text())
    data=readz(OUT/'panel.json.gz');variants=readz(OUT/'variants.json.gz');usage=session['usage']
    assert audit['status']==ta['status']==oa['status']=='PASS'
    lines=['# M24: what caused the M23 six-edge result?', '',
        'This is a fixed causal assay of one selected lineage on the already-used M23 panel. It contains no new evolution, no new mazes and no independent confirmation. The eight interventions and all seventeen ancestral states were frozen and pushed before inference (registration b0d07ed).', '',
        'All branches retain their instructions, payload calculations, gates and initialization. Bypass changes SELECT(condition,payload,old) to SELECT(condition,old,old). The final output-writer edit exchanges input slots8 and3, redirecting live slot3 from C2 to the unwritten, unseeded C8. Material and opcode costs match within the factorial; changed states and termination can still change total work.', '',
        '| Branch0 bypass | Branch7 bypass | Final C2 port swap | Known pose4 correct | Pose0 correct | Paired units /400 | Ordinary bases /256 | Correct no-path /168 |',
        '|---|---|---|---|---|---|---|---|']
    for c in s['factorial']:
        m=s['models'][c['identity']]
        lines.append(f"| {c['bypass0']} | {c['bypass7']} | {c['saved_ports']} | {c['gain']} | {c['counterpose']} | {m['metrics']['paired']} | {m['metrics']['ordinary_bases_both_poses']} | {m['correct_no_path']} |")
    suff=s['models']['sufficiency/root_plus_final_port_swap']
    lines += ['',f"The first saved ancestor correct on the known pose4 input is `{s['first_successful_ancestor']}`. Root plus the final port swap: pose4 correct={suff['gain']['optimal']}, counterpose correct={suff['counterpose']['optimal']}. This is conditional sufficiency on that background, not a claim about all mazes.", '',
        '| Ancestral position | Exact identity | Edit | Known pose4 correct | Paired units | Ordinary bases | Correct no-path |',
        '|---|---|---|---|---|---|---|']
    for c in s['lineage']:
        event=c['events'][0] if c['events'] else {};label=event.get('kind','root')
        if 'block' in event:label+=f" C{event['block']}"
        lines.append(f"| {c['position']} | {c['identity']} | {label} | {c['gain']} | {c['pairs']} | {c['ordinary']} | {c['correct_no_path']} |")
    lines += ['', '## Same-panel gains, losses and scope', '',
        '| Variant | Correct inputs | New/lost paired vs root | New/lost ordinary vs root | False no-path | Exact focal mask/status/steps /1680 | Counted work |',
        '|---|---|---|---|---|---|---|']
    for i in [ROOT_ID,FOCAL,'sufficiency/root_plus_final_port_swap']+[c['identity'] for c in s['factorial']]:
        m=s['models'][i];r=m['versus_root'];lines.append(f"| {i} | {m['correct_inputs']} | +{r['pairs']['gained']}/−{r['pairs']['lost']} | +{r['ordinary_bases']['gained']}/−{r['ordinary_bases']['lost']} | {m['metrics']['false_no_path']} | {m['same_focal_terminal']} | {m['counted_work']:,} |")
    lines += ['', 'Full lost/gained response sets, ordinary length strata, domain counts, terminal records and all costs are in summary.json/responses.json.gz. Novel individual inputs are measured against the same declared103-alias/73-genotype historical archive as M23. This archive is not every historical mutant. No result on these reused inputs establishes generalization or a new campaign acquisition.', '',
        '## Passive traces and independent saved-state observation', '',
        f"All {trace['calls']} fixed passive executions equal the corresponding native reactions; all {ta['calls']} histories replay exactly. Only completed ticks under the unchanged VM limits are saved. Ten fixed cases include the known gain/counterpose, old gains/losses, a correct no-path case and long ordinary cases. No case was chosen from M24 outcomes.", '',
        f"The scalar observer checked {obs['scalar_frames']:,} branch-frame predictions against the next saved state; ALL match. Observation audit reproduces all statistics without new inference. Branch activity is separated from selected payload differing from the old expression; complete contrast records and first channel divergences are in branch_observation.json.", '',
        '## Validation, costs and preservation', '',
        f"Five focused preparation tests pass (not the full suite). One initial missing-reference identity test failure is preserved with exact source; reference sourcing was corrected before registration and before scientific inference. Synthetic rehearsal used {prep['fixture_calls']} calls/{prep['candidate_seconds']:.4f} candidate seconds plus {prep['extra_native_checks']} native checks and {prep['trace_checks']} traces on three already excluded fixture inputs. Rehearsal native-check timings were not separately instrumented.", '',
        f"Evaluation: {usage['calls']:,} physical calls, {usage['candidate_seconds']:.2f} candidate seconds, {usage['work']:,} counted work, {session['wall_seconds']:.2f}s wall, {session['rss_peak_bytes']/2**30:.3f}GiB sampled peak process-tree RSS, {usage['uncertain_attempts']} uncertain attempts. Forty physical models represent42aliases; all receive1680cases. No evolutionary births or random draws occurred.", '',
        f"Evaluation audit: first PASS, {audit['native_replays']:,} ALL-native outputs and independent grades, {audit['m23_exact_response_comparisons']:,} unchanged M23 response comparisons, all transformations/panel/tasks/summary/chain replay, {audit['wall_seconds']:.2f}s. All three intact controls are correct. Production VM is shared; the raster grader is independent. This is not a second full VM implementation.", '',
        f"Passive traces: {trace['calls']} calls/{trace['counted_work']:,}work/{trace['wall_seconds']:.2f}s; trace audit {ta['calls']}calls/{ta['counted_work']:,}work/{ta['wall_seconds']:.2f}s. Saved-state scalar observation {osession['wall_seconds']:.2f}s; replay {oa['wall_seconds']:.2f}s. Trace wall includes observation/storage overhead and is not candidate latency. Audit candidate timings are not separately instrumented; no speed claim.", '',
        'Registered bounds: ten local workers;900s per execution/audit/trace/observer action,150kcalls/1e14evaluation work,600calls/1e13 per trace action,8GiB RSS,3GiB total phase storage including backups,16GiB free floor. Epoch/monotonic max clock includes host sleep. No guard bypass, scientific repair, extra case or selection. All prior M23 completion hashes and original local records remain unchanged. Original journal, verified SQLite-API backup and immutable layout references are preserved; see preservation.json. Zero new layouts.', '']
    (OUT/'report.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
