from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.branch_causality import OUT,RUN,ROOT,writej,sha,FOCAL,ROOT_ID,prior_check
p=OUT/'report.md';s=p.read_text();a=s.index('\n\n');s=s[:a]+'''

The six-edge result came from a conditional readout correction, not a newly added
branch acting as a standalone pathfinder. The last C2 port edit lets stale output
marks disappear. Both added branches can be bypassed while retaining this specific
success. Branch0 nevertheless preserves many other correct routes; bypassing it
exposes three new two-pose perfect-maze results on this development panel, while
losing over half the corridor tests. We have active, context-dependent mechanisms
and strong skill tradeoffs, rather than evidence of an integrated general solver.
'''+s[a:]
s=s.replace('Full lost/gained response sets, ordinary length strata, domain counts, terminal records and all costs are in summary.json/responses.json.gz.',
'''Full response sets, domain counts and terminal records are in summary.json/responses.json.gz. Posthoc saved-only interpretation.json adds all factorial gained/lost sets and corrected reachable-only ordinary length strata. The generic raw summary also bins ordinary_disconnected empty paths under 0to7; these are no-path tests, not zero-length paths. Raw records are preserved; disconnected cases are excluded from the corrected length tables.''')
s=s.replace('59.89 candidate seconds,','59.89 candidate seconds,65.10 worker CPU seconds,')
s+='''
## Mechanistic interpretation reviewed against the saved states

**The final edit makes the output retractable.** In both direct parent and final
organism, on an open cell with C1=0 the output writer produces zero. At the source,
when C1>0, it writes C1. Elsewhere, while C1>0, the direct parent writes:

`C2_next = saturate(C2_old + (bool(C0_old) XOR bool(C6_old) if C4_old else 0))`

The final genotype replaces the C2 feedback term with the persistently zero C8:

`C2_next = bool(C0_old) XOR bool(C6_old) if C4_old else 0`

This is an exact local readout recurrence for these genomes, not a shortest-path
algorithm proof. The two gate expressions and source exception matter. The C2
terminal is unchanged; the port exchange changes its upstream ADD input. A separate
posthoc saved-state audit verifies the recurrence at **594,542 open site-ticks**
across all240 passive histories, with zero new inference. On the known six-edge
pose4 case, parent and child both stop at13 ticks with142,493 dispatched instructions.
At the final tick the child clears pixel127, the parent's extra spur. All seven
oracle-path pixels remain lit. The first C2 difference occurs at tick10. This is
an output-state change within the same execution duration, not a longer rollout.

**Branch0 contributes useful behavior, but also interferes.** Its actual payload
selection changes the C0 writer at21 open site-ticks on the six-edge case. Bypass
first changes C0 at tick7 and C2 at tick10. With branch0 intact the last port edit is
required for the known pose4 success; with branch0 bypassed it is not required, and
both poses work with either C2 map. This is a conditional interaction, not universal
necessity of the port edit or universal irrelevance of branch0.

The four predeclared branch0-bypass variants solve the known six-edge base in both
poses. With the pre-final C2 map, they additionally solve both poses of two11x11
perfect mazes of8 and9 edges. These six individual responses are beyond the declared
historical comparison archive. They were exposed by fixed interventions on reused
data, not evolved in M24 and not independently confirmed. The cost is substantial:
relative to the intact final organism, branch0 bypass with the old C2 map gains18
correct individual responses but loses149, including108/200 corridors; ordinary
bases rise25→27 with4gained/2lost. With the final C2 map it gains24 responses but
loses163, including116corridors; ordinary bases fall25→19 with2gained/8lost. Both
retain168/168 correct no-path and zero false no-path. Neither is an integrated
replacement. All ancestral and causal variants remain0/79 ordinary16+ bases in
both poses; no general or long-route progress is established here.

**Branch7 changes state and timing, with no correctness change on this panel.**
Its payload differs from its old expression at103 site-ticks on the known case;
bypassing it first changes C7 at tick4. Across all1,680 inputs, in each of the four
matched branch0/port backgrounds, branch7 bypass preserves ALL terminal masks and
statuses and the exact successful-case sets. Steps differ on88inputs; bypass adds
5,246,082 counted work in each background. Its presence has a measured termination/
work effect here, not a demonstrated new route-solving ability. This does not prove
that C7 can never influence routing in other genotypes or environments.

**Accumulated ancestry matters, but more material is not automatically integrated
skill.** The final port swap alone on the106-instruction root solves neither pose.
No earlier saved ancestor solves the known pose4 case; the16-birth descendant has
113instructions. Yet both added branch outputs are dispensable for that case in
the final background, and some earlier ancestors have better aggregate same-panel
counts than the final organism. This is evidence of context dependence among changes,
not a claim that all16edits are necessary or that any particular untested subset is
minimal. Added branches are neither all silent passengers nor a general solving
module. Random-origin evolution has produced useful regulatory effects and a
retractable readout, while integration and transfer remain the bottlenecks.

## Next recommendation, not launched

The next experiment should test **selection for integrated skill retention**, using
the preserved M23 populations and a matched continuation with the existing selector.
Keep runtime, variation operators, starting material, common training panels and
nominal evaluation budgets fixed. Compare a proposed training allocation that
explicitly revisits complete corridor/ordinary/no-path skill sets with the existing
allocation; retain a bounded imperfect-intermediate niche so temporary losses can
still be explored. Apply strict acquisition/retention gates to independent frozen
confirmation, not as a blanket ban on intermediate mutations. A separately registered
60–90minute continuation can test this without adding another genome primitive.
The choice of exact selection rule and resource/session bounds must be reviewed and
frozen before launch. Preserve whole populations/RNG/ancestry; do not seed the search
with hand-edited M24 ablations or pick a favored ancestor using this panel.

This recommendation tests whether selection can combine the useful alternatives
already visible. It does not assume that more compute or a new selection scheme
will produce a general solver. Capacity and longer evolutionary time remain open
hypotheses; recombination is premature as the immediate next lever because these
branches have strong background-dependent effects. No next phase is running.
'''
p.write_text(s)
rec=json.loads((OUT/'readout_recurrence_audit.json').read_text());assert rec['status']=='PASS' and rec['open_site_predictions']==594542
pr=prior_check();wf=json.loads((RUN/'workflow_status.json').read_text())
writej(OUT/'report_review.json',dict(status='PASS',report_sha256=sha(p),reviewed_actual_factorial=True,reviewed_all17_ancestors=True,
    reviewed_gain_loss_no_path_and_lengths=True,reviewed_all_audits=True,reviewed_readout_recurrence=True,
    phase_vs_inherited_distinguished=True,mechanism_data_not_confirmation=True,all_ablation_successes_costs_and_losses_disclosed=True,
    raw_disconnection_length_label_caveat_disclosed=True,no_new_inference_for_interpretation=True,
    workflow_seconds=wf['ended_epoch']-wf['started_epoch'],prior=pr,next_phase_launched=False,
    recommendation='Separately preregister matched skill-retention/integration selection continuation from preserved M23 populations, unchanged runtime/operators, imperfect intermediates preserved.'))
print('reviewed',sha(p),pr)
