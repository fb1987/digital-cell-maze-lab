"""Write a reviewed M21 report from saved audited evidence, no candidate calls."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.readout_causality import ROOT,OUT,PRIOR,RUN,check,readz,writej,sha,SPECIALISTS,Genome
from maze_evolution.connected_genome import embed
from maze_evolution.modular_genome import Genome as M1

def main():
    check();assert not (OUT/'report.md').exists() and not (OUT/'historical_matches.json').exists()
    s=json.loads((OUT/'summary.json').read_text());interp=json.loads((OUT/'interpretation.json').read_text())
    session=json.loads((OUT/'session.json').read_text());audit=json.loads((OUT/'audit.json').read_text())
    trace=json.loads((OUT/'trace_session.json').read_text());ta=json.loads((OUT/'trace_audit.json').read_text())
    preservation=json.loads((OUT/'preservation.json').read_text());wf=json.loads((RUN/'workflow_status.json').read_text())
    assert wf['state']=='audited_ready_for_report' and audit['status']==ta['status']=='PASS'
    minimal_id=SPECIALISTS[0]+'/terminal_only/source/append';items=readz(OUT/'variants.json.gz')['items']
    model=Genome.from_dict(next(i['model']['genome'] for i in items if i['id']==minimal_id))
    history_path=ROOT/'results/retention_pressure/choices.json.gz'
    seal=json.loads((history_path.parent/'completion.json').read_text())
    assert seal['files'][str(history_path.relative_to(ROOT))]==sha(history_path)
    historical=readz(history_path);matches=[]
    for identity,c in historical['items'].items():
        if historical['representations'][identity]=='modular' and embed(M1.from_dict(c['genome']))==model:matches.append(identity)
    assert sorted(matches)==['m10/modular/1/control/g128/b35','m10/modular/2/rotating/g32/b7']
    writej(OUT/'historical_matches.json',dict(status='PASS',scope='Posthoc static comparison, no old/new candidate executions',
        m21_identity=minimal_id,m21_genome=model.to_dict(),m10_exact_matches_after_standard_zero_spare_embedding=sorted(matches),
        historical_choices_sha256=sha(history_path),historical_seal_sha256=sha(history_path.parent/'completion.json'),
        historical_choice_hash_verified=True,novel_algorithm_claim=False))
    lines=['# M21: the short-maze gain comes from changing the readout',
        '', '**The copied process is not required for this gain when its reader is reconnected to the original donor.** '
        'Changing the original parent’s C6 terminal alone reproduces the gained four-edge maze in both poses. '
        'Restoring the old terminal removes that success in all four saved specialists. '
        'The terminal-only model loses 252 original correct responses while gaining 34; only two gained inputs are beyond all thirteen protected references.',
        '', 'A historical check also identifies the minimal appended-terminal genome as an EXACT match, after standard empty-spare embedding, '
        'to two saved M10 nominees. M20 rediscovered this mechanism in new variants and on new cases. M21 provides causal attribution; '
        'it does not establish a new evolved solver mechanism or new confirmation evidence.',
        '', '## Frozen scope',
        '', 'The user authorized the bounded copy/readout assay recommended after M20. Registration `9d8e121` containing all exact variants, '
        'cases and trace choices was pushed before execution. There were 76 aliases / 64 distinct physical models on ALL 1,680 reused M20 '
        'inputs. These are mechanism/development data for M21, not untouched confirmation. Four specialists were selected in M20 for the '
        'same short-maze gain; they are related backgrounds, not independent discoveries.',
        '', 'For every specialist: saved versus restored original terminal crossed with intact copy, reader bypass with copy retained, '
        'copy removal without bypass, and bypass plus removal. Bypass swaps the reader’s live copy port with the dormant original donor '
        'port. Removal clears the copied writer and its seed. Terminal restoration adapts only the destination scratch address. '
        'Full original-reader restoration and terminal-only append/replace controls distinguish expression, port and instruction-count effects. '
        'All thirteen protected references, exact anchors/copy bases and intact flat/M1/M18 controls were evaluated on identical cases.',
        '', 'No generations, nominations, fresh cases, solver injection, mating or runtime extensions were used. The bounded M18 VM is unchanged.',
        '', '## Causal comparisons',
        '', 'Each cell below means correct shortest path on BOTH gained-maze poses. Restoring the old terminal fails this same endpoint in all four.',
        '', '| Specialist | Saved | Bypass, keep copy | Remove, keep attachment | Bypass + remove | Terminal only in original parent |',
        '|---|---|---|---|---|---|']
    for i in SPECIALISTS:
        c=s['causal_tests'][i];m=c['copy_modes'];yn=lambda x:'yes' if x else 'no'
        lines.append(f"| {i} | {yn(c['observed_both_poses'])} | {yn(m['bypass_keep'])} | {yn(m['remove_only'])} | {yn(m['bypass_remove'])} | {yn(c['terminal_only']['source/append'])} |")
    lines += ['', 'Simply deleting the copy breaks generic/parent/d3 because its reader still requests the now-empty slot. '
        'Reconnecting the existing donor restores the success. This is dependence on an attached signal, not evidence that a distinct copied '
        'computation is required. The other three preserve the gain even with the copy deleted and the original attachment left in place.',
        '', 'Bypass with the copy retained preserves every mask/status/tick record on all 1,680 inputs for ALL four specialists. '
        'Bypass plus removal preserves all 1,680 records for both local specialists, and changes only four or two no-path records for '
        'the two generic specialists, recovering those correct decisions. Counted work can differ even when these terminal fields agree. '
        'The copy may still affect quiet detection, budgets or untested inputs; this is conditional evidence on the frozen panel.',
        '', '## Gain and loss together',
        '', '| Model / intervention | Correct individual inputs | Original correct inputs lost | New correct vs original | Complete pairs / 400 | Corridors / 200 | Ordinary both poses / 256 | Correct no-path / 168 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    show=[('Original parent','anchor/parent'),('Terminal only, append',minimal_id),('Terminal only, replace',SPECIALISTS[0]+'/terminal_only/source/replace'),
          ('Generic d3 saved',SPECIALISTS[0]+'/intact/saved'),('Generic d3 bypass + remove',SPECIALISTS[0]+'/bypass_remove/saved'),
          ('Generic d3 old terminal + bypass/remove',SPECIALISTS[0]+'/bypass_remove/restore_old'),
          ('Local d3 saved',SPECIALISTS[2]+'/intact/saved'),('Local d3 old terminal',SPECIALISTS[2]+'/intact/restore_old')]
    for label,i in show:
        r=s['models'][i];m=r['metrics'];corr=m['by_domain']['corridor']['optimal']
        lines.append(f"| {label} | {r['correct_inputs']} | {r['source_correct_lost']} | {r['source_correct_gained']} | {m['paired']} | {corr} | {m['ordinary_bases_both_poses']} | {r['correct_no_path']} |")
    lines += ['', 'The minimal terminal-only model is identical in mask/status/ticks to BOTH local specialists on ALL 1,680 inputs. '
        'Appending and replacing the old terminal also yield identical masks/status/ticks on this panel, with different executed work. '
        'Both solve the gained maze after nine ticks, but neither is an additive solver. The apparent 14→15 ordinary-base change hides '
        'two original ordinary bases lost and three gained; only one gained base, with two poses, is beyond the protected union.',
        '', 'All original-reader restoration controls lose the shared gain and recover the original path repertoire, except for '
        'the two generic copies’ two/four no-path losses when those copies remain. Removing those copies also restores all 636 original '
        'correct responses in the displayed comparisons. Swapping readout alternatives trades capabilities; it does not combine them.',
        '', 'Generic d3 removal without reconnection reaches 22 ordinary bases, but adds ZERO correct individual inputs beyond the '
        'protected portfolio and still loses 49 original correct responses. It is a fixed ablation result, not a nominated improvement. '
        'The terminal-only model solves none of the 77 ordinary bases with routes of at least 16 edges in both poses (52 perfect / 25 random). '
        'Complete model-level metrics, false no-path and every ordinary length stratum are in summary.json.',
        '', '## What the terminal is doing',
        '', 'The original parent already computed the subtraction internally. The shared duplicate-node event appended that existing '
        'private expression as the C6 writer’s final value, replacing which expression becomes visible to other channels. '
        'It did not invent a new arithmetic primitive. For the minimal original-parent variant, the expression simplifies to:',
        '', '```text', 'C6[t+1,p] = (C1[t,p] > 0) × max(0, C5[t,p] − 4)', '```',
        '', 'Three saved specialists use C1 directly for that condition; generic d3 uses its copied C1 signal in C8. '
        'The thresholded magnitude comes from C5. The output raster is still C2, which responds through the inherited recurrent network; '
        'C6 is an intermediate signal, not the final path mask. The four-edge route length was not encoded in a genome or supplied to '
        'inference. The constant four was already present in the ancestral expression. Success on this particular maze does not turn '
        'that threshold into a general shortest-path procedure.',
        '', f"This posthoc recurrence matches ALL {sum(x['checked_open_site_transitions'] for x in interp['recurrence_checks'].values()):,} "
        'open-site, completed-tick transitions across the four specialists and eight preregistered trace cases. '
        'All four bypass-plus-removal comparisons preserve the original eight channel states at every shared completed tick on all '
        'eight cases: 32/32 comparisons. For all specialists, restoring the old terminal changes those states on six cases and '
        'preserves them on the two selected disconnected cases. The full histories, including their different lifetimes, are retained.',
        '', 'On the gained maze, the output is empty through tick6, begins with one lit site at tick7, has two at tick8 and emits '
        'the exact five-site/four-edge path at tick9. This observation explains the actual bounded reaction, not a general algorithm '
        'or behaviour after forced continuation. No incomplete interrupted tick is counted as a history state.',
        '', '## Historical identity and research implication',
        '', 'The terminal-only appended genome is exactly the standard M18 embedding of M10 control1 g128/b35 and rotating2 g32/b7. '
        'historical_matches.json records both complete genome comparisons and verifies the old choices file against its original seal. '
        'No old study was rerun. M10 already reported the same C6 duplication, a short ordinary gain and losses of paired/corridor skills. '
        'The M20 cases were fresh at M20 evaluation, so their measured capability remains valid; algorithmic novelty does not follow '
        'from succeeding on another fresh case. Repeated discovery across these related lineages is not evidence of cumulative construction.',
        '', 'This result shifts the immediate emphasis from adding whole copied processes to preserving and composing alternative '
        'readouts. The arithmetic needed for the short specialist was already in the scaffold; evolution exposed it by changing the '
        'writer’s terminal expression, at a large retention cost. It remains possible that copies help other mutations or longer '
        'searches; M21 addresses these four backgrounds and this mechanism only. Random-origin solver discovery remains open.',
        '', 'My next recommendation is a separately registered, bounded accessibility test of a **generic guarded-expression '
        'extension**: retain the old expression as an addressable branch while adding a mutable alternative and mutable local selector, '
        'compared with the present replacement grammar. Existing M9 gate-only work changed the activation of one readout; this would '
        'test retention of both expression alternatives. The selector must use only ordinary internal/local state, never case IDs, '
        'oracle routes or a rule choosing whichever completed mask grades better. Require retained skills and fresh gains, then '
        'decide whether sustained evolution is justified. Do not count recovered protected skills or another four-edge rediscovery '
        'as a general-solver milestone. This is a proposal only; no next phase or long run is running.',
        '', '## Cost, audits and preservation',
        '', '| Phase | Calls | Candidate seconds | Worker CPU seconds | Wall seconds | Counted work |',
        '|---|---:|---:|---:|---:|---:|',
        f"| Evaluation | {session['usage']['calls']:,} | {session['usage']['candidate_seconds']:.2f} | {session['usage']['cpu_seconds']:.2f} | {session['wall_seconds']:.2f} | {session['usage']['work']:,} |",
        f"| ALL-native output audit | {audit['native_replays']:,} | separately unmeasured | separately unmeasured | {audit['wall_seconds']:.2f} | {audit['native_counted_work']:,} |",
        f"| Passive traces | {trace['calls']:,} | separately unmeasured | separately unmeasured | {trace['wall_seconds']:.2f} | {trace['counted_work']:,} |",
        f"| ALL-history audit | {ta['calls']:,} | separately unmeasured | separately unmeasured | {ta['wall_seconds']:.2f} | {ta['counted_work']:,} |",
        '', f"The durable workflow took {wf['ended_epoch']-wf['started_epoch']:.2f}s through both audits. "
        f"Evaluation peak sampled tree RSS {session['rss_peak_bytes']/2**30:.3f}GiB; traces {trace['rss_peak_bytes']/2**30:.3f}GiB; "
        f"trace audit {ta['rss_peak_bytes']/2**30:.3f}GiB. Zero uncertain attempts, no scientific repair or guard bypass. "
        'All registered wall/call/work/memory/storage/free-disk bounds respected. These are accounting costs, not repeated warm latency benchmarks.',
        '', f"First output audit PASS: all {audit['independent_grades']:,} independent grades and native outputs, complete transformations, "
        f"tasks, panel, trace-selection and summary replay; {audit['m20_exact_response_comparisons']:,} unchanged-M20 response comparisons. "
        f"First trace audit PASS: all {ta['calls']} complete histories and production reactions exactly equal. All intact controls correct. "
        'M21 did not repeat conventional baseline calls; those were already checked in M20. Shared production VM, independent raster grader, '
        'not an independently implemented second VM.',
        '', 'Five focused synthetic transformation tests PASS0.11s, not the full historical suite. Preflight27discarded-fixture calls, '
        '48extra native/trace checks,0.072candidate seconds/0.087wall; no new layouts or scientific variants executed in preparation. '
        'An unregistered postprocessing helper initially reversed the SELECT operands in its handwritten algebra and failed its '
        'saved-history assertion before producing interpretation output. The failed script and diagnosis are preserved in '
        'postprocessing_attempt_001. Correcting the algebra passed all110,480saved transitions, with zero new executions. '
        'Scientific sources, outputs and first-pass audits were unchanged.',
        '', f"All 400 M20 completion files and 13 local records remain unchanged. Original evaluation journal and SQLite-API backup "
        f"are preserved locally under writer lock; integrity checks and ALL tables match. Preservation size {preservation['storage_bytes']/2**20:.2f}MiB, "
        f"disk free {preservation['disk_free_bytes']/2**30:.2f}GiB, within2GiB/16GiB limits. "
        f"The reference+delta whole-layout ledger still contains {preservation['whole_layouts']:,} hashes; ZERO new layouts. "
        'Immutable historical manifests/parts are required; use referenced_campaign_store.load_layouts. '
        'Raw journals remain outside Git. Completion seals never overwrite prior records; future audits require new packets.'
    ]
    with (OUT/'report.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    print('M21 report drafted from actual evidence; historical matches',matches)

if __name__=='__main__':main()
