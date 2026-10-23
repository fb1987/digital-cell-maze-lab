"""Write M28 factual report once; human-readable interpretation reviewed separately."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.integration_accessibility import ROOT,OUT,RUN,readz,check


def main():
    check();path=OUT/'report.md';assert not path.exists()
    s=json.loads((OUT/'summary.json').read_text());d=json.loads((OUT/'saved_diagnostics.json').read_text());p=json.loads((OUT/'preservation.json').read_text())
    reg=json.loads((OUT/'registration.json').read_text());launch=json.loads((OUT/'launch.json').read_text());freeze=json.loads((OUT/'choice_freeze.json').read_text())
    sessions={n:json.loads((OUT/(n+'_session.json')).read_text()) for n in ('development','final')}
    audits={n:json.loads((OUT/(n+'_audit.json')).read_text()) for n in ('development','final')};assert all(a['status']=='PASS' for a in audits.values())
    pool=readz(OUT/'pool.json.gz');choices=readz(OUT/'choices.json.gz')
    lines=['# M28 integration-accessibility assay','',
      'All three arms failed the registered integration test. No proposal solved both poses of any of the four reused complementary bases, even before retention gates. See the fixed fresh nominees below for independent transfer results.','',
      'This is a bounded sexual-variation neighborhood assay around preserved random-origin lineages, with no evolutionary generations or selection-driven reproduction.','',
      '## Frozen design','',
      f"Registration `{launch['registration_commit'][:7]}` ({len(reg['files'])} hashes), all parent material, operators and the full pool were pushed before development inference. Choice freeze `{freeze['commit'][:7]}` was pushed before fresh case generation; all nomination decisions replayed exactly.", '',
      'All38 distinct complementary genotype pairs from M27,15 parental genotypes, both recipient directions and eight draws per direction:608 proposals per arm,1824 total. ALL208 M27 aliases include205 noncontrol historical comparison aliases and three intact controls. Parent aliases are selected by a fixed lexicographic rule among identical genotypes; all aliases remain recorded. The M27 source ancestry closure and original histories are preserved. These related forks do not constitute independent origins.','',
      'MUTATION uses one existing ordinary edit. SPLICE exchanges one contiguous homologous writer segment with its ports/initialization. REGULATED imports a homologous private expression DAG into one recipient writer, alpha-renames registers, rebinds physical ports, and appends an ordinary random local expression plus SELECT. Every operator has one opportunity; edit size and material differ. No fitness/oracle/case ID enters inference or variation.','',
      'The existing ten-channel M18 VM and limits are unchanged:256instructions,31nodes/writer,256ticks,4096reads/site,32768dispatches/site. Both branches of fused expressions consume real dispatch/read work. A fusion may be rejected rather than retried.','',
      '## Development: used cases only','',
      'Identical454 development inputs for every alias: all four complementary bases, all22 prior witnesses, metadata-balanced samples of the six existing M27 families. No new development cases were generated.','',
      '| Arm | Proposals | Changed from recipient | Distinct genotypes | Raw complementary-base gains | Retention gate passes |',
      '|---|---:|---:|---:|---:|---:|']
    for arm in ('mutation','splice','regulated'):
        a=d['arms'][arm];lines.append(f"| {arm} | {a['proposals']} | {a['changed']} | {a['distinct_genotypes']} | {a['max_complementary']} maximum | {a['gates']['passes']} |")
    lines+=['',f"Valid regulated fusions: {d['arms']['regulated']['kinds'].get('regulated_fusion',0)}; rejection reasons: `{d['arms']['regulated']['rejection_reasons']}`. All raw complementary successes were zero, so the negative integration result does not depend on the strict gate. All1,824 proposals have zero worst-domain retention against the registered parent/root/entry set on development. This is a coarse domain minimum, not a statement that every skill was lost.", '',
      'The three roles(INTEGRATED, COMPLEMENT, RETENTION) collapsed to the same identity within each arm. Nine fixed role nominations therefore represent three candidate identities. They were frozen despite the negative screen; no role substitution or final-data re-selection occurred. The splice nominee is a genotype no-op, explicitly counted rather than discarded.','',
      f"All{d['old_saved_source_row_matches']:,} reused source/reference/control response records match saved M27 records exactly. All original complementary source responses are therefore reproduced. This rules out silently changing the parental input or execution convention as an explanation for the screen result.",'',
      '## Independent confirmation','',
      f"Fresh2128 inputs:1680 standard+448 targeted, {s['ordinary_bases']} ordinary bases, {s['ordinary8_bases']} with8+edges and{s['ordinary16_bases']} with16+edges, both poses0/4. Targeted ordinary cases include perfect and cyclic-random families,11/15grids,8–31edge bins. ALL prior/preparation layouts and proposal orbits were excluded.",'',
      'Primary score is fixed INTEGRATED-role novel complete ordinary8+ beyond ALL205 historical comparison aliases and both parents/root/entry; zero unless genotype changed, every nonempty parental domain retains90%, A0 correct-disconnection retains90%(nonempty), and no false reachable no-path.','',
      '| Arm | Raw new complete8+ | Gated primary | Correct ordinary(both poses) | Correct no-path | False no-path | Parent/root retention90% |',
      '|---|---:|---:|---:|---:|---:|---|']
    for x in s['choices']:
        if x['role']!='INTEGRATED':continue
        c=x['final'];e=c['endpoint'];lines.append(f"| {x['arm']} | {e['raw_novel_complete8']} | {e['primary_score']} | {c['metrics']['ordinary_bases_both_poses']} | {c['correct_no_path']} | {c['false_no_path']} | {e['gate']['domain_retention90']} |")
    lines+=['',f"Historical complete8+ portfolio coverage on these SAME fresh cases: {s['historical_complete8']}/{s['ordinary8_bases']}. Raw totals across M27/M28 panels are not acquisition or loss. Full exact-parent/root/entry gains/losses, all model/domain metrics, status counts, and ordinary family/size/length strata are in summary.json.",'',
      'Fixed nominees and actual genetic parents:','']
    for x in s['choices']:
        if x['role']!='INTEGRATED':continue
        c=x['final'];profile=d['final_profiles'][x['id']]
        lines += [f"- **{x['arm']}** `{x['id']}`; recipient `{c['recipient']}`, donor `{c['donor']}`. Event `{c['event']['kind']}`;{profile['instructions']}instructions. Prior-genotype matches:{len(profile['genotype_matches'])}; full fresh mask/status/steps profile matches:{len(profile['terminal_mask_status_steps_matches'])} historical aliases. These matches exclude cost; work is separately recorded."]
    lines += ['', '## Actual compute and checks','',
      '| Stage | Physical calls | Logical queries | Candidate seconds | Worker CPU seconds | Wall seconds | Peak sampled GiB |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for name,session in sessions.items():
        u=session['usage'];lines.append(f"| {name} | {u['calls']:,} | {session['logical_queries']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {session['wall_seconds']:.2f} | {session['rss_peak_bytes']/2**30:.3f} |")
    lines+=['',f"Science total:{sum(x['usage']['calls'] for x in sessions.values()):,} physical calls;{sum(x['usage']['work'] for x in sessions.values()):,} counted work(reads+dispatches+exposure checks). Zero uncertain attempts. Equal nominal development budgets:{608*454:,} queries per arm. Physical deduplication and overlapping arm/reference genotypes prevent a unique per-arm CPU allocation; saved_diagnostics.json reports physical membership buckets and nominal work including aliases.",'',
      'Candidate timers include input decoding, internal updates and raster emission, excluding organism construction, grading and serialization. Worker CPU/wall include broader costs. No warmed repeated end-to-end speed benchmark was conducted.','',
      f"Both ALL-native audits PASS first attempt: development{audits['development']['all_native_replays']:,} replays/{audits['development']['wall_seconds']:.2f}s; final{audits['final']['all_native_replays']:,}/{audits['final']['wall_seconds']:.2f}s. ALL grades/work/rows, pool/operator/RNG, task specifications, nomination, corpus and complete summary replay. All{sum(a['conventional_calls'] for a in audits.values()):,} BFS/A*/bitwave control calls and all intact control responses correct. Shared frozen VM/evaluator with independent raster grader; not a second VM.",'',
      'Eight focused tests pass; not the full suite. Discarded preflight:40 previously excluded inputs,360 calls+360 native replays+40warmups,25.06wall seconds; pool/RNG and artificial nomination reconstruction pass. One pre-registration port-range test failure and original files are preserved; an unpublished registration packet was preserved before strengthening full-summary audit. No scientific source repair, guard bypass or failed-workflow resume.','',
      f"All416 prior M27 completion hashes and15 local records unchanged. Original development/final journals preserved; backup status `{p['status']}` with SQLite-API integrity and ALL-table comparison. Complete layout ledger:{p['whole_layouts']:,}={p['initial_layouts']:,} inherited+{p['new_layouts']:,} generated/rejected/unqueried orbit hashes. Reference+delta manifest requires immutable historical bases. Phase storage at preservation:{p['storage_bytes']/2**20:.2f}MiB; free disk:{p['disk_free_bytes']/2**30:.2f}GiB, within6GiB/16GiB guards. Raw SQLite stays local and out of Git.",'',
      '## Interpretation and next recommendation','',
      'Pending explicit review of actual outcomes; see report_review.json after review.','']
    path.write_text('\n'.join(lines))


if __name__=='__main__':main()
