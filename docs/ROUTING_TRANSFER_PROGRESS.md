# V12H completed handoff — October 19, 2026

Current checkpoint (October 19, 2026): **V12H is complete**. Read
`results/routing_transfer.md` and `docs/ROUTING_TRANSFER_PROGRESS.md` first.
Do not repeat H, extend its closed cap, resume G, or tune on inspected final
cases. The validation-breadth follow-up is proposed, not launched.

All 30 G primary + 30 frozen aliases (33 physical random-origin models), plus
2 separate known controls, were frozen/pushed in e5e30e8 BEFORE final generation.
No training or reselection. Seed 2026101903, fixtures 1224. There are 48 independent
contexts, 24 per 5–9/10–18-edge band, each with 8 poses, 2 goals and matched
fork/two-junction/real alternative-cycle graphs: 2,304 branched inputs/1,152 pairs,
768 corridors and 128 no-path controls. Variants/poses are correlated. Prefixes
4–8 versus G≤3, 25×25 boards and new geometry prevent a single-variable
interpretation of G-to-H failure.

G leader fork/carry/evolved/branch/evolution/0/i4549 gives 0/2,304 legal/shortest
branched outputs, 0/1,152 pairs, 690/768 corridors. All 1,152 short branched masks
have branch/cycle defects. G's 68-gene resampling winner gives zero branched
outputs, 768/768 corridors. Only one physical random-origin model completes
pairs: inherited V12E foundation_pair_paired/local/fresh/evolution/1/i109169,
256 genes, birth 1299, G carry/local Current/frozen replicate1. Fork 17/384,
two-junction 15/384, cycle 3/384 pairs; individual shortest 86/768, 69/768, 13/768.
Contexts 6/5/1, none in all eight poses; all paired routes have 5–6 edges. Cycle
pairs are three poses of ONE six/six-edge context with 18/18-edge alternatives.
Every model completes zero long-band pairs; every Branch cohort fails 0/3.
Do not claim a new G evolutionary gain. BFS/A*/bit-wavefront/intact VM solve
3,072/3,072 reachable and 128/128 disconnected inputs. No false normal reachable
no-path claims. General solving and multirange advantage remain unestablished.

Four preselected random-origin mechanism targets plus two controls receive six
interventions on all 2,304 branched inputs. G leader goal-switch source/junction/
output-away responses are 48/36/48 of 48 probed pairs; pulse removal retains them,
flag removal eliminates all three. Full flag-off states still differ at the goal
pulse; both-off forced trajectories are identical. Endpoint-check removal keeps
all 2,304 G-leader reactions identical; pulse removal keeps masks but changes work.
Nonlocal zeroing changes 334 masks and still gives zero correct routes. These
targets fail H normal pairs: the ablations do not establish necessity for G
successes. The successful inherited local H variant was outside the mechanism
subset and was not newly probed after H. All 1,536 forced traces reach 64 ticks,
98,304 frames; no strict-both or two-goal shortest geometry occurs. Fresh local
has 13 normal-input shortest frames after incorrect native emission, 36 pulse-off
and two both-off frames. These are not normal solutions; no stopping retune.

Inference 152.76s/600s cap, total 164.60s, 596.84 MiB RSS, 201,083 calls and
89,746,284,052 work units. The 71 successful timing cases are median 112.91× slower
than BFS (range 11.42–304.01); no speedup. Audit 166.61s, 612.88 MiB RSS verifies
149 source/41 input hashes, 194,944 normal/intervention replays, 1,536 full traces,
768 independent observer checks, 420 native parity checks, 9,600 final baselines,
and all calibration/timing/graph checks. The first audit failed only serializing
a NumPy count after all checks; original source remains. Active entry point
`tools/audit_routing_transfer.py` casts that count to a Python int. Full rerun
passes; failed log/partial packet and approximately 166.68s additional wall time
are preserved. Nine new protocol tests + eight existing tests pass; one audit
regression passes separately. 185 collected tests; NOT a fresh full-suite run.
All previous populations/RNG/source/results remain intact.

Exclude **all 138,712 whole layouts** through H (136,536 old + 192 fixtures + 1,984
final), including every pose and matched control. Do not relabel H final data as
validation. Next proposal: freeze the existing G validation-nominee pool, compare
new equal-budget narrow/broad validation, freeze choices, then use another
untouched final set. Preserve fresh/carry random origins, resampling, local/evolved
controls and useful diversity. Do not automatically launch another unchanged
60–90-minute evolution run.

## Artifact and reproduction guide

The implementation is `maze_evolution/routing_transfer.py`,
`routing_transfer_data.py` and the frozen `routing_transfer_audit.py`.
Static-flag/endpoint diagnostics reuse the unchanged
`route_confirmation_runtime.py`. Production uses the unchanged growth/V6 VM.
Limits: eight channels, 256 genes, 256 ticks, 4,096 reads/site,
32,768 dispatches/site, 65,536-cell ceiling.

The active auditor is `tools/audit_routing_transfer.py`; the original frozen
source deliberately retains its diagnostic serialization bug. The entry point
converts only `strict_both_ticks` to a Python integer. Both audit attempts replay
the same complete packet; no candidate output or numerical assessment changed.
See `results/routing_transfer/audit_serialization_repair.json` and
`execution_logs/` for the failed log/partial temporary packet and successful log.
The first attempt adds approximately 166.68 seconds beyond the successful audit.

The frozen panel, exclusion set and provenance are under
`results/routing_transfer/`. `confirmation/` contains every new maze, paired
context, mask, intervention, full trajectory, timing and execution ledger.
Fixtures are under `results/routing_transfer_fixtures/`. All raw full states are
compressed with decoded hashes; 983,040,000 aggregate decoded bytes are not a
process-RAM estimate. Each 64-tick history occupies 640,000 bytes separately
from candidate array-payload accounting.

`tools/summarize_routing_transfer.py` and `tools/plot_routing_transfer.py` analyze
saved evidence only. Figures are standalone PNG/SVG. The cycle illustration
uses the first successful cycle pair of the inherited local model, chosen post
hoc for display. `forced_geometry_note.json` explains the 13 normal-input
shortest forced frames on four cases after native incorrect emission. It also
lists intervention geometry with the unablated stop time explicitly labeled;
do not mistake that time for the intervention's own stopping time. Neither
artifact adds candidate inference or an independent test.

`compute_accounting.json` separates experimental calls, calibration, two full
audit attempts, baseline/timing calls, warmups and software tests. The experiment
charges 112,000 normal + 82,944 intervention + 1,536 probe + 840 parity + 3,763
timing VM calls. Successful audit separately replays 200,079 VM/observer calls.
Timing uses 71 eligible case/model pairs and 53 calls per solver each. All
288 immutable G source/artifact hashes were checked again and pass.

The exact positive cycle example is `final/band0/g4/s1`, poses 1, 6 and 7:
6/6-edge shortest routes versus 18/18-edge alternatives. The inherited local
model completes no context in all eight poses and no 10–18-edge pair. It has
seven individual long fork outputs and five two-junction outputs. This is a
preserved primitive, not proof of goal-guided general routing. It was outside
the preselected mechanism subset; no post-test ablation was added for it.

The next proposal is `results/routing_transfer/next_experiment.md`. It has not
been preregistered or launched. It freezes G validation-nominated genotypes by
membership, compares new narrow/broad validation with matched input counts,
then freezes selections before another independent final set. Do not select a
pool from H final performance, transfer genomes across lineages, silently add
known solvers, or restart a closed search budget.
