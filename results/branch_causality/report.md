# M24: what caused the M23 six-edge result?

The six-edge result came from a conditional readout correction, not a newly added
branch acting as a standalone pathfinder. The last C2 port edit lets stale output
marks disappear. Both added branches can be bypassed while retaining this specific
success. Branch0 nevertheless preserves many other correct routes; bypassing it
exposes three new two-pose perfect-maze results on this development panel, while
losing over half the corridor tests. We have active, context-dependent mechanisms
and strong skill tradeoffs, rather than evidence of an integrated general solver.


This is a fixed causal assay of one selected lineage on the already-used M23 panel. It contains no new evolution, no new mazes and no independent confirmation. The eight interventions and all seventeen ancestral states were frozen and pushed before inference (registration b0d07ed).

All branches retain their instructions, payload calculations, gates and initialization. Bypass changes SELECT(condition,payload,old) to SELECT(condition,old,old). The final output-writer edit exchanges input slots8 and3, redirecting live slot3 from C2 to the unwritten, unseeded C8. Material and opcode costs match within the factorial; changed states and termination can still change total work.

| Branch0 bypass | Branch7 bypass | Final C2 port swap | Known pose4 correct | Pose0 correct | Paired units /400 | Ordinary bases /256 | Correct no-path /168 |
|---|---|---|---|---|---|---|---|
| False | False | False | False | False | 102 | 25 | 168 |
| False | False | True | True | False | 104 | 25 | 168 |
| False | True | False | False | False | 102 | 25 | 168 |
| False | True | True | True | False | 104 | 25 | 168 |
| True | False | False | True | True | 112 | 27 | 168 |
| True | False | True | True | True | 120 | 19 | 168 |
| True | True | False | True | True | 112 | 27 | 168 |
| True | True | True | True | True | 120 | 19 | 168 |

The first saved ancestor correct on the known pose4 input is `m23/connected/0/enabled/g190/b50`. Root plus the final port swap: pose4 correct=False, counterpose correct=False. This is conditional sufficiency on that background, not a claim about all mazes.

| Ancestral position | Exact identity | Edit | Known pose4 correct | Paired units | Ordinary bases | Correct no-path |
|---|---|---|---|---|---|---|
| 0 | m14/reference/gated_partial | root | False | 112 | 22 | 168 |
| 1 | m23/connected/0/enabled/g159/b48 | enabled_extension C0 | False | 0 | 2 | 168 |
| 2 | m23/connected/0/enabled/g160/b18 | activation_expression_edit C0 | False | 16 | 6 | 168 |
| 3 | m23/connected/0/enabled/g162/b12 | payload_expression_edit C0 | False | 112 | 23 | 168 |
| 4 | m23/connected/0/enabled/g163/b20 | payload_expression_edit C0 | False | 0 | 3 | 92 |
| 5 | m23/connected/0/enabled/g166/b15 | activation_expression_edit C0 | False | 12 | 6 | 22 |
| 6 | m23/connected/0/enabled/g169/b14 | operand C5 | False | 12 | 6 | 22 |
| 7 | m23/connected/0/enabled/g171/b8 | activation_expression_edit C0 | False | 112 | 23 | 168 |
| 8 | m23/connected/0/enabled/g172/b42 | enabled_extension C7 | False | 104 | 26 | 168 |
| 9 | m23/connected/0/enabled/g173/b18 | duplicate_node C6 | False | 104 | 26 | 168 |
| 10 | m23/connected/0/enabled/g174/b29 | operand C6 | False | 104 | 26 | 168 |
| 11 | m23/connected/0/enabled/g175/b41 | ports C4 | False | 104 | 26 | 168 |
| 12 | m23/connected/0/enabled/g177/b21 | payload_expression_edit C0 | False | 120 | 28 | 168 |
| 13 | m23/connected/0/enabled/g178/b41 | payload_expression_edit C0 | False | 132 | 28 | 168 |
| 14 | m23/connected/0/enabled/g187/b30 | ports C1 | False | 132 | 28 | 168 |
| 15 | m23/connected/0/enabled/g188/b39 | payload_expression_edit C0 | False | 102 | 25 | 168 |
| 16 | m23/connected/0/enabled/g190/b50 | ports C2 | True | 104 | 25 | 168 |

## Same-panel gains, losses and scope

| Variant | Correct inputs | New/lost paired vs root | New/lost ordinary vs root | False no-path | Exact focal mask/status/steps /1680 | Counted work |
|---|---|---|---|---|---|---|
| m14/reference/gated_partial | 660 | +0/−0 | +0/−0 | 0 | 738 | 460,275,032 |
| m23/connected/0/enabled/g190/b50 | 693 | +6/−14 | +4/−1 | 0 | 1680 | 473,268,638 |
| sufficiency/root_plus_final_port_swap | 558 | +8/−0 | +0/−1 | 0 | 472 | 460,163,786 |
| factorial/bypass0=0/bypass7=0/ports=0 | 694 | +4/−14 | +4/−1 | 0 | 1615 | 473,397,460 |
| factorial/bypass0=0/bypass7=0/ports=1 | 693 | +6/−14 | +4/−1 | 0 | 1680 | 473,268,638 |
| factorial/bypass0=0/bypass7=1/ports=0 | 694 | +4/−14 | +4/−1 | 0 | 1527 | 478,643,542 |
| factorial/bypass0=0/bypass7=1/ports=1 | 693 | +6/−14 | +4/−1 | 0 | 1592 | 478,514,720 |
| factorial/bypass0=1/bypass7=0/ports=0 | 562 | +16/−16 | +7/−2 | 0 | 797 | 474,068,332 |
| factorial/bypass0=1/bypass7=0/ports=1 | 554 | +24/−16 | +2/−5 | 0 | 599 | 473,957,304 |
| factorial/bypass0=1/bypass7=1/ports=0 | 562 | +16/−16 | +7/−2 | 0 | 709 | 479,314,414 |
| factorial/bypass0=1/bypass7=1/ports=1 | 554 | +24/−16 | +2/−5 | 0 | 511 | 479,203,386 |

Full response sets, domain counts and terminal records are in summary.json/responses.json.gz. Posthoc saved-only interpretation.json adds all factorial gained/lost sets and corrected reachable-only ordinary length strata. The generic raw summary also bins ordinary_disconnected empty paths under 0to7; these are no-path tests, not zero-length paths. Raw records are preserved; disconnected cases are excluded from the corrected length tables. Novel individual inputs are measured against the same declared103-alias/73-genotype historical archive as M23. This archive is not every historical mutant. No result on these reused inputs establishes generalization or a new campaign acquisition.

## Passive traces and independent saved-state observation

All 240 fixed passive executions equal the corresponding native reactions; all 240 histories replay exactly. Only completed ticks under the unchanged VM limits are saved. Ten fixed cases include the known gain/counterpose, old gains/losses, a correct no-path case and long ordinary cases. No case was chosen from M24 outcomes.

The scalar observer checked 354,496 branch-frame predictions against the next saved state; ALL match. Observation audit reproduces all statistics without new inference. Branch activity is separated from selected payload differing from the old expression; complete contrast records and first channel divergences are in branch_observation.json.

## Validation, costs and preservation

Five focused preparation tests pass (not the full suite). One initial missing-reference identity test failure is preserved with exact source; reference sourcing was corrected before registration and before scientific inference. Synthetic rehearsal used 21 calls/0.0640 candidate seconds plus 21 native checks and 15 traces on three already excluded fixture inputs. Rehearsal native-check timings were not separately instrumented.

Evaluation: 67,200 physical calls, 59.89 candidate seconds,65.10 worker CPU seconds, 20,738,912,817 counted work, 27.21s wall, 2.966GiB sampled peak process-tree RSS, 0 uncertain attempts. Forty physical models represent42aliases; all receive1680cases. No evolutionary births or random draws occurred.

Evaluation audit: first PASS, 67,200 ALL-native outputs and independent grades, 31,920 unchanged M23 response comparisons, all transformations/panel/tasks/summary/chain replay, 48.60s. All three intact controls are correct. Production VM is shared; the raster grader is independent. This is not a second full VM implementation.

Passive traces: 240 calls/106,678,046work/4.24s; trace audit 240calls/106,678,046work/4.09s. Saved-state scalar observation 3.38s; replay 3.41s. Trace wall includes observation/storage overhead and is not candidate latency. Audit candidate timings are not separately instrumented; no speed claim.

Registered bounds: ten local workers;900s per execution/audit/trace/observer action,150kcalls/1e14evaluation work,600calls/1e13 per trace action,8GiB RSS,3GiB total phase storage including backups,16GiB free floor. Epoch/monotonic max clock includes host sleep. No guard bypass, scientific repair, extra case or selection. All prior M23 completion hashes and original local records remain unchanged. Original journal, verified SQLite-API backup and immutable layout references are preserved; see preservation.json. Zero new layouts.

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
