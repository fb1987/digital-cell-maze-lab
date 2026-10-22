"""Initial M22 report from actual audited evidence; review before sealing."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.guarded_extension import OUT,RUN,check,writej
from maze_evolution.guarded_extension_genome import ARMS

def main():
    check();assert not (OUT/'report.md').exists()
    s=json.loads((OUT/'summary.json').read_text());d=json.loads((OUT/'saved_diagnostics.json').read_text());b=json.loads((OUT/'branch_usage.json').read_text())
    p=json.loads((OUT/'preservation.json').read_text());wf=json.loads((RUN/'workflow_status.json').read_text())
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('screen','final','trace')}
    sessions={k:json.loads((OUT/f'{k}_session.json').read_text()) for k in ('screen','final','trace')}
    assert all(a['status']=='PASS' for a in audits.values()) and wf['state']=='audited_ready_for_report'
    primary={a:len(s['primary_passes'][a]) for a in ARMS}
    lines=['# M22: guarded-expression accessibility comparison','',
        f"**Registered descriptive guarded support: {s['policy_comparison']['descriptive_guard_support']}.** Strict fresh primary passes: "
        +', '.join(f'{a} {primary[a]}/6' for a in ARMS)+'.',
        '', 'The fixed protocol compared a conditional expression extension with a material-matched unconditional extension and the existing '
        'ordinary mutation grammar. Sources are the preserved M15 parent, M15 child and known M10 threshold-readout variant in the unchanged '
        'M18 VM. They are related historical backgrounds, not independent random origins.256fresh random M1 bodies are baseline controls, '
        'not a sustained random-founder evolution arm.',
        '', '## Registered design and novelty accounting','',
        '768endpoints /3,072unselected opportunities per arm; three or five opportunities per draw; same source and initial RNG seed within '
        'each trio. Every extension appends a payload and either SELECT(old,new) with random condition/polarity or COPY(new). Payload, '
        'length, active-writer choice, port maps, seeds and RNG trajectory are identical in the extension pair. The terminal wrapper differs. '
        'All ancestral expression prefixes remain intact. Half payloads reuse a uniformly random private expression through COPY; half '
        'use the unchanged generic node grammar. No favored writer, gate, maze coordinate or threshold expression was installed.',
        '', 'Preserving old code is not preserving old behavior: changed recurrent state, quiet termination and resource use can still lose '
        'skills. Guarded versus overwrite tests the selector package at equal code length, while ordinary differs in edit scope/material. '
        'No selection occurs between these opportunities. This is a local accessibility assay, not evidence about many generations of accumulation.',
        '', f"All arms saw the same712fresh development inputs. The frozen nonselectable archive has {d['archive_aliases']}aliases /"
        f"{d['archive_genotypes']}distinct genomes, including all thirteen preserved references, known M10 threshold, M20nominees and M21"
        'noncontrol diagnostic models. These extra diagnostics are comparisons, not injected founders. Novel units subtract the entire '
        'archive on the SAME cases. Intact solver controls are excluded from that novelty union.',
        '', 'Fixed primary/exploratory roles for each arm/source/depth were committed and pushed before independent1680-input confirmation. '
        'The best development random control was also frozen. No final-data reselection. Strict pass requires ALL correct source responses, '
        'zero false reachable no-path, >=90%of a NONEMPTY A0 correct-disconnection set and a complete new skill unit beyond source AND archive. '
        'Source-preserving recovery of archive skills is reported separately from novelty. A novel complete unit can combine individual '
        'responses already handled by different archived models; individual-input novelty is reported separately.',
        '', '## Development: retention versus additions','',
        '| Arm | Proposals | Clean full-source retention | Additive including archive recovery | Strict archive-novel additive | Any novel complete unit before retention gates |',
        '|---|---:|---:|---:|---:|---:|']
    for a in ARMS:
        c=d['allocation'][a];lines.append(f"| {a} | {c['proposals']} | {c['screen/clean_source_retention']} | {c['screen/additive_including_archive_recovery']} | {c['screen/strict_novel_additive_pass']} | {c['screen/novel_complete_unit_gainer']} |")
    lines += ['', '| Matched source/depth | Both extensions retain | Only guarded | Only overwrite | Neither | Ordinary retains |',
              '|---|---:|---:|---:|---:|---:|']
    for label,c in d['matched'].items():lines.append(f"| {label} | {c['both_extension_arms_clean']} | {c['guarded_only_clean']} | {c['overwrite_only_clean']} | {c['neither_extension_clean']} | {c['ordinary_clean']} |")
    lines += ['', 'Each matched stratum has128draws. These are correlated proposals around fixed backgrounds, not independent evolutionary replicates. '
        'Retention without a useful new unit does not satisfy the endpoint.',
        '', '## Fixed fresh-confirmation primary roles','',
        '| Arm / source / depth | Pairs | Corridors | Ordinary both poses | Correct no-path | Source correct responses lost | Novel units | Strict pass |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for n in s['nominations']:
        if n['role']!='primary':continue
        f=n['result'];m=f['metrics'];corr=m['by_domain']['corridor']['optimal']
        lines.append(f"| {n['arm']} / {n['anchor']} / {n['depth']} | {m['paired']} | {corr} | {m['ordinary_bases_both_poses']} | {sum(x['correct_no_path'] for x in m['by_domain'].values())} | {f['lost_source_correct']} | {sum(f['novel_units_beyond_archive'].values())} | {f['strict_novel_additive_pass']} |")
    lines += ['', 'Registered score counts novel complete units for each fixed PRIMARY nominee only when strict pass holds, otherwise zero. '
        'Depth3/5scores are summed within background and can overlap in skill identity; they are not counts of independent discoveries. '
        'Guarded support needs positive guarded-minus-overwrite differences in at least2/3related backgrounds and positive total. '
        'It is descriptive, not a significance test. Exploratory roles cannot substitute.',
        '', '| Source | Ordinary score | Overwrite score | Guarded score | Guarded − overwrite |',
        '|---|---:|---:|---:|---:|']
    for row in s['policy_comparison']['backgrounds']:
        c=row['scores'];lines.append(f"| {row['anchor']} | {c['ordinary']} | {c['overwrite']} | {c['guarded']} | {row['guarded_minus_overwrite']} |")
    lines += ['', '## All exploratory roles and random baseline','',
        '| Arm / source / depth | Source responses lost | New individual inputs beyond archive | Novel upstream pairs | Novel ordinary8+ /16+ | Strict pass |',
        '|---|---:|---:|---:|---:|---|']
    for n in s['nominations']:
        if n['role']!='exploratory':continue
        f=n['result'];lines.append(f"| {n['arm']} / {n['anchor']} / {n['depth']} | {f['lost_source_correct']} | {len(f['new_individual_inputs_beyond_archive'])} | {f['novel_upstream']} | {f['novel_long8']} / {f['novel_long16']} | {f['strict_novel_additive_pass']} |")
    random=next(n for n in s['nominations'] if n['role']=='random_control');rm=random['metrics']
    lines += ['', f"Frozen random baseline {random['identity']}: {rm['paired']}complete pairs, {rm['by_domain']['corridor']['optimal']}corridors, "
        f"{rm['ordinary_bases_both_poses']}ordinary both-pose bases, {sum(v['correct_no_path'] for v in rm['by_domain'].values())}correct no-path, "
        f"{rm['false_no_path']}false reachable no-path. Its successful lengths and any archive-novel inputs are preserved in saved_diagnostics.json. "
        'This is one development-selected random genome, evaluated once on untouched confirmation; not population evolution from a random founder.',
        '', f"Final reachable ordinary denominator256;16+denominator{d['long16_denominator']}. Full perfect/random size/length strata, source/"
        'archive comparisons, false no-path and disconnection losses are in summary.json and saved_diagnostics.json. Ancestral route lengths '
        'are not new acquisition. Distinct genotypes and event counts alone do not establish new behavior.',
        '', '## Effective behavior and branch usage','',
        f"There are {len(d['nominees'])}selected identities across37fixed roles. Exact-genotype, full mask/status/tick profile, correct-set and "
        'source-profile matches are recorded for every identity. This explicitly recognizes known M10 threshold behavior and more recent '
        'archive behaviors on identical cases.',
        '', f"The independent saved-frame observer verified {b['verified_module_site_ticks']:,}module-site-ticks, reconstructing "
        f"{b['scalar_node_dispatches']:,}node dispatches, in {b['wall_seconds']:.2f}s. It used ALLsaved guarded-nominee histories on12metadata-selected "
        'cases (upstream/fork/corridor/perfect16+/random16+/disconnected). This is posthoc private-register reconstruction, not new candidate '
        'trajectories or confirmation cases. Counters separate outermost branch selections with unequal old/new values from equal-value or '
        'private nested calculations. Branch use is not by itself evidence of useful innovation.',
        '', '| Guarded nominee | Outermost observations | Old chosen with unequal values | New chosen with unequal values |',
        '|---|---:|---:|---:|']
    for i,v in b['models'].items():
        c=v['totals'];lines.append(f"| {i} | {c.get('outermost_observations',0)} | {c.get('outermost_old_with_unequal_values',0)} | {c.get('outermost_new_with_unequal_values',0)} |")
    lines += ['', '## Material, cost and validation','',
        '| Arm | Phase opportunities | Genotype-no-op opportunities | Ending instruction range |',
        '|---|---:|---:|---|']
    for a,c in d['allocation'].items():lines.append(f"| {a} | {c['opportunities']} | {c['genotype_noop_opportunities']} | {d['ending_instruction_ranges'][a]} |")
    lines += ['', 'Each arm has546,816nominal development proposal queries and20,160nominal final role queries. Random bodies and archive/source/'
        'intact comparisons are separate. Physical deduplication and ALL-sharing-label cost buckets are in saved_diagnostics.json; '
        'they partition actual calls/work/time without double counting. Worker CPU is available per phase, not per model. Equal logical '
        'budgets do not imply equal CPU. Timing here is accounting, not a repeated warm speed benchmark.',
        '', '| Phase | Calls | Candidate seconds | Worker CPU seconds | Wall seconds | Counted work | RSS GiB |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for phase in ('screen','final'):
        r=sessions[phase];u=r['usage'];lines.append(f"| {phase} | {u['calls']:,} | {u['candidate_seconds']:.2f} | {u['cpu_seconds']:.2f} | {r['wall_seconds']:.2f} | {u['work']:,} | {r['rss_peak_bytes']/2**30:.3f} |")
    lines += ['', f"Workflow through all audits {wf['ended_epoch']-wf['started_epoch']:.2f}s. "
        f"First screen audit PASS: ALL{audits['screen']['independent_grades']:,}grades, complete pool/intermediates/events/RNG/cases/tasks/selection, "
        f"{audits['screen']['native_replays']:,}fixed native replays;{audits['screen']['wall_seconds']:.2f}s. "
        f"First final audit PASS: ALL{audits['final']['native_replays']:,}native outputs/grades/summary plus5,040BFS/A*/bitwavecalls;"
        f"{audits['final']['wall_seconds']:.2f}s. Allintact/conventionalcontrols correct. Shared production VM/operator, independent raster grader, "
        'not a second full inference implementation.',
        '', f"Passive traces {sessions['trace']['calls']}executions/{sessions['trace']['counted_work']:,}work/"
        f"{sessions['trace']['wall_seconds']:.2f}s;ALL-historyaudit{audits['trace']['calls']}sameoutputs/histories/"
        f"{audits['trace']['wall_seconds']:.2f}s. No forced continuation. Scientific source hashes unchanged, no post-final reselection. "
        'Registered wall/call/work/RSS/storage/free-disk limits apply to all phases; guard and uncertainty records are preserved.',
        '', 'Preparation: five focused synthetic tests passed0.35s,notfullhistoricalsuite. Successful fake-source rehearsal59,544calls/'
        '9.86candidate seconds/19.91wall,64,328independentaliasgrades/2,062native samples,threepassivefixtures/1,760scalarobservermodule-site-ticks. '
        'All fixture cases were already excluded; no preparation descendants seeded research.',
        '', f"Preservation status {p['status']}; storage {p['storage_bytes']/2**20:.2f}MiB, free disk {p['disk_free_bytes']/2**30:.2f}GiB. "
        f"Complete ledger {p['whole_layouts']:,}layouts including ALL generated/rejected/unqueried inputs; initial{p['initial_layouts']:,}, "
        f"screennew{p['search_new_layouts']:,}, finalnew{p['final_new_layouts']:,}. Original journals and SQLite-API verified backups preserved "
        'under locks; immutable base manifests/parts remain required. Read full ledgers through referenced_campaign_store.load_layouts, '
        'not raw delta tables. All400M20/386M21completion files and13/9localrecords unchanged. No rawSQLite in Git. Future audits new packets.',
        '', '## Reviewed interpretation and next recommendation','',
        'Interpret the actual fixed endpoints, branch use, novelty/profile matches and retention losses here before completion sealing. '
        'No later experiment or long run is authorized by M22. Random-origin discovery remains open; a bounded local neighborhood cannot '
        'establish eventual success or impossibility.'
    ]
    with (OUT/'report.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    print('M22 initial actual-evidence report created; review required')

if __name__=='__main__':main()
