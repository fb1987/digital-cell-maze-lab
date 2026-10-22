"""One-time actual M18 report draft, reviewed before completion seal."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.connected_copy_assay import OUT,check,verify_prior,readz


def main():
    check();assert not (OUT/'report.md').exists()
    s=json.loads((OUT/'summary.json').read_text());i=json.loads((OUT/'interpretation.json').read_text())
    sessions={k:json.loads((OUT/f'{k}_session.json').read_text()) for k in ('screen','final')}
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('screen','trace','final')}
    assert all(a['status']=='PASS' for a in audits.values())
    trace=json.loads((OUT/'trace_session.json').read_text());pres=json.loads((OUT/'preservation.json').read_text())
    prior=verify_prior();reg=json.loads((OUT/'registration.json').read_text())
    p=json.loads((OUT/'pool_counts.json').read_text());choice=json.loads((OUT/'choices_freeze.json').read_text());launch=json.loads((OUT/'launch.json').read_text())
    t=['# M18: initialized connected-copy assay','',
       'This is a fixed mechanical experiment on two preserved random-origin genomes. It tests whether generic duplication can preserve an existing computation while connecting its copy to an existing reader. It is not an evolutionary search, and designed interventions are not acquired skills.','',
       f"Registration `{launch['registration_commit'][:7]}` was pushed before generation. The entire {p['aliases']}-alias proposal panel and all reference choices were pushed together at `{choice['commit'][:7]}` before any fresh scientific cases. There was no nomination, adaptive selection or reselection. All {p['physical_models']} distinct models received 712 development and 1,680 fresh final inputs.", '',
       '## Prespecified mechanical outcomes','',
       '| Pure-copy condition | Aliases | Distinct genomes | Exact mask/status/steps on all final inputs | Retains every correct response | Zero-writer coupling in sampled shared ticks | Neutral AND coupled |',
       '|---|---:|---:|---:|---:|---:|---:|']
    for arm,g in i['groups'].items():
        t.append(f"| {arm} | {g['aliases']} | {g['distinct_genomes']} | {g['bounded_neutral']} | {g['retain_all_correct']} | {g['trace_aliases_with_zero_coupling']} | {g['bounded_neutral_AND_trace_coupling']} |")
    t+=['',f"Every initialized pure copy preserved the original eight channels at every shared completed tick and matched its donor at every recorded state: {i['pure_initialized_trace_comparisons']:,} alias/case comparisons over {i['trace_cases']} metadata-selected development cases. Full histories were hashed and replayed in a separate pass of the passive trace implementation. Its terminal outputs matched the production VM and the saved development responses.", '',
        'Coupling counts above mean that zeroing the copied writer changed an original-channel state at a tick completed by both the intervention and its matched pure copy. Different stopping times alone do not count. No effect on these cases does not establish global inertness. Structural edges include gates and both conditional branches; a structural connection need not be dynamically active in every stimulus.', '',
        '## Initialization and execution cost','',
        '| Condition | Variants with mask / status / step differences vs anchor | Correct-loss range across variants | Work ratio min / median / max vs anchor |',
        '|---|---:|---:|---:|']
    for arm,g in i['groups'].items():
        t.append(f"| {arm} | {g['any_mask_difference']} / {g['any_status_difference']} / {g['any_step_difference']} | {g['correct_loss_range']} | {g['work_ratio_min']:.3f} / {g['work_ratio_median']:.3f} / {g['work_ratio_max']:.3f} |")
    c=[c for c in i['initialization_contrasts'] if c['donor_initially_nonzero']]
    t+=['',f"There are {len(c)} seeded/zero pure-copy contrasts whose donors initially contain stimulus information; {sum(any(v for v in c['differences'].values()) for c in c)} have at least one final mask/status/step difference. Other donors are initially zero, so the two initialization settings coincide there. Full paired contrasts and gain/loss counts are in `interpretation.json`.", '',
        f"The fixed variants contain {i['instruction_range'][0]}–{i['instruction_range'][1]} instructions. Empty M18 embedding adds 8 bytes per site plus 162 metadata bytes relative to M1; copied writers add their program storage. Production caps were unchanged. Exact common-tick state equivalence does not guarantee equal bounded behavior: a focused test demonstrates an earlier instruction-cap stop. Final costs and every differing case are retained in `summary.json`.", '',
        '## Inherited solving ability and limitations','',
        '| Exact anchor | Complete pairs / 400 | Corridors / 200 | Ordinary bases correct in both poses / 256 | Correct disconnected / 168 | False no-path on reachable |',
        '|---|---:|---:|---:|---:|---:|']
    for a in ('parent','child'):
        m=s['reference_metrics']['anchor/'+a]['metrics'];t.append(f"| {a} | {m['paired']} | {m['by_domain']['corridor']['optimal']} | {m['ordinary_bases_both_poses']} | {m['correct_no_path']} | {m['false_no_path']} |")
    t+=['','The parent is the exact `m14/reference/gated_specialist`; the child is the exact M15 `m14/modular/1/explore/g320/b48`. M18 created no mutation births or new ancestry. All twelve protected references remain present. Preserving an anchor also preserves its limitations; it does not combine the two repertoires.', '',
        f"The old combined restoration gate is retained descriptively: {len(i['designed_intervention_strict_joint_passes'])} proposal aliases pass. Reference eligibility is {s['reference_joint_gate_eligible']}. Any such result is a designed intervention result, not evolutionary acquisition. See the complete exact-parent, child and protected-union comparisons, losses and no-path counts for every variant in `summary.json`.", '',
        '| Ordinary family/size/length | Parent correct / bases | Child correct / bases |', '|---|---:|---:|']
    a=s['reference_metrics']['anchor/parent']['ordinary_length_strata'];b=s['reference_metrics']['anchor/child']['ordinary_length_strata']
    for k in sorted(set(a)|set(b)):
        t.append(f"| {k} | {a.get(k,{}).get('correct_both_poses',0)} / {a.get(k,{}).get('bases',0)} | {b.get(k,{}).get('correct_both_poses',0)} / {b.get(k,{}).get('bases',0)} |")
    t+=['','All intact controls and BFS/A*/bit-wave baselines pass every final input. No general-solver, speed advantage, independent-replicate, statistical significance or selection-policy claim follows. Aliases include physical duplicates and related interventions. Same-panel comparisons are valid; differences from earlier panels are not acquisition. This measures two fixed neighborhoods, not whether sustained random-origin evolution can exploit them.', '',
        '## Actual resource use and audit','',
        '| Phase | Physical calls | Candidate seconds | Worker CPU seconds | Work units | Wall seconds | Sampled tree RSS GiB |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for k,x in sessions.items():
        u=x['usage'];t.append(f"| {k} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {u['work']:,} | {x['wall_seconds']:.2f} | {x['rss_peak_bytes']/2**30:.3f} |")
    t+=['',f"Science totals: {sum(x['usage']['calls'] for x in sessions.values()):,} physical calls and {sum(x['usage']['work'] for x in sessions.values()):,} work units. Zero uncertain attempts. Each pure-copy condition has 72 aliases and equal nominal case allocations, but physical deduplication and execution costs differ. `physical_cost_buckets.json` partitions actual costs by all alias labels without double-counting. Cold JIT cost may be included; these are accounting measurements, not warm speed benchmarks.", '',
        '| Audit | Native/trace executions | Independent grades | Wall seconds |', '|---|---:|---:|---:|']
    for k,a in audits.items():t.append(f"| {k}: PASS | {a.get('native_replays',a.get('calls')):,} | {a.get('independent_grades',0):,} | {a['wall_seconds']:.2f} |")
    t+=['',f"Passive trace measurement separately used {trace['calls']:,} executions, {trace['work']:,} work units and {trace['wall_seconds']:.2f} seconds; maximum history instrumentation allocation was {trace['max_instrumentation_bytes']:,} bytes. The trace audit charged the same calls/work again. Final audit additionally evaluated 5,040 conventional control responses. Both native audits replayed ALL scientific responses/independent grades, pool, corpus, tasks and journal chains; the final audit reproduced the complete summary. Trace replay checked all saved full-history hashes and comparisons. These audits share the native VM/operator; raster grading is independent.", '',
        'Five focused tests passed (not the entire historical suite). Two preparation-only failures were retained: a rectangular fixture was sent to a square-only symmetry helper, then a premature artificial preflight reached the missing-exclusion write. The failed preflight consumed 1,760 fixture calls plus 22 trace executions; its timing was not preserved. The corrected preflight repeated those calls/traces and passed 128 embedding checks. No scientific source or output repair occurred after registration.', '',
        f"All {len(reg['files'])} registration hashes, {len(prior['files'])} M17 completion hashes and {len(prior['local_records'])} M17 local-record hashes verified. The registration and choice freeze are published. SQLite-API backups: {pres['status']}; all table contents match. Preserved M18 storage before report/seal: {pres['storage_bytes']/2**30:.3f} GiB; free disk {pres['disk_free_bytes']/2**30:.2f} GiB, within 6/16 GiB bounds. The whole-layout ledger contains {pres['whole_layouts']:,} hashes, including rejected and unqueried generation. Its immutable referenced bases are required for restoration. Raw journals and backups remain local; compact evidence and copied logs are committed. Future audits need separate output paths; never overwrite these records.", '']
    (OUT/'report.md').write_text('\n'.join(t))

if __name__=='__main__':main()
