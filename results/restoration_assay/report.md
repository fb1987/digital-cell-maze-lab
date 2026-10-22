# M16 restoration assay — audited evidence

M16 did not restore the combined capability, but it identified a specific regulatory conflict worth testing next. All four prospectively nominated joint-retention mutation roles fail on fresh confirmation. All 72 fixed diagnostic interventions also fail the full gate. The reference endpoint is nonvacuous: the child again contributes 16 upstream pairs beyond every protected reference, while its actual parent supplies ordinary and disconnection skills that the child lacks.

On this new panel the parent solves 128/400 pairs, 166/200 corridors, 14/256 ordinary bases in both poses, and 168/168 disconnected inputs. The child solves 184 pairs and all 200 corridors, but only eight ordinary bases and zero disconnected inputs. These ordinary totals differ from M15 because the panels differ; they are not evidence of improvement or regression between experiments. The same skill tradeoff is replicated on fresh layouts.

## What the experiment rules out, and what it does not

The fixed screen covered 2,048 generic mutation proposals: 512 one-edit and 512 two-edit proposals around each anchor, plus 1,024 random references. Among those 2,048 mutation proposals, zero simultaneously solved any of the eight development target pairs and any disconnected case while avoiding false reachable no-path responses. That is a stronger local observation than merely finding no winner under the ranking rule. It is development evidence about these sampled neighborhoods, not a proof that a combining genome is impossible.

The joint and aggregate selectors saw identical pools and inputs. On fresh confirmation, joint nominees either preserved the parent's behavior, reproduced the child's tradeoff, or lost additional skills. For example, parent-derived two-edit nominee 0727 matches the child's terminal masks, statuses and ticks on every one of the 1,680 inputs. The child-derived aggregate nominee 0421 similarly matches the parent. These are finite-panel behavioral matches, not global equivalence or additional independent discoveries. Three joint nominees retain all 16 target pairs but lose all 168 required disconnection responses. None of the ten nominated roles solves an ordinary both-pose base with a path of at least 16 edges.

This study sampled short mutation paths from preserved anchors. It did not test a longer evolving population, sexual transfer, a new runtime, or an unlimited number of combinations. The negative result therefore should not close random-origin research or be used to claim that additional evolutionary time cannot help.

## What the traces explain

The parent keeps two different spatial processes. In the three prospectively selected disconnected examples, its C0 field occupies the source's connected component, while C7 occupies the goal's component. The M15 port swap changes C0's input from its source-side neighbor signal C5 to the goal-side signal C7. In the child, C0 remains at just the source cell on the source side and becomes active across the goal's component. This is a loss of separation between signals with different roles.

That change helps the selected prefix-2 cycle and second-junction examples: at tick 13 the parent illuminates eight pixels and is wrong; the child illuminates seven and is correct. Longer prefixes in the recorded panel still fail. On the three disconnected examples, all child output pixels lie in the goal's component and none lie in the source's component. The parent settles to an empty output in 37, 61 and 44 ticks. The child reaches the step limit at 256 ticks or a read limit at 77/74 ticks, with residual output.

The persistence is not an observed oscillation. In these disconnected traces only output channel C2 is still changing at the last completed tick; the other seven channels have settled. A recorded C2 cell counts 245, 246, …, 252 over the last eight ticks of the constructed example. A post-hoc reduction of the unchanged output block explains this: when C1 is positive, non-source sites retain old C2 and add a gated Boolean XOR of C0 and C6, saturating at 65,535. At the source the block uses C1 directly; when C1 is absent its output is zero. This reduced recurrence matches all 291,211 recorded site-ticks. It was derived after inspecting the traces and is labeled as such, separately from the preregistered C0 recurrence and full-history replay.

The mechanism evidence therefore points to altered signal coupling feeding an output accumulator. More runtime by itself has no demonstrated benefit here; within the observed bounds the failing outputs keep accumulating. We did not extend execution or assume that every failure has this exact mechanism.

## Recommended next test

I recommend a small, separately registered test of whether useful regulation can be copied into spare state without overwriting an existing function. The current operator already copies blocks, but it replaces another channel's writer. A generic duplication mechanism with bounded spare channels could preserve the original source-side process while allowing a copied process to change. That is an evolvability hypothesis, not evidence that the current runtime lacks expressive power.

First require an exact behavior-preserving embedding of the old genomes, with additional memory and execution cost exposed. Then compare the new duplication/capacity treatment against the unchanged representation under matched evaluation allocations, using the same routing-plus-retention endpoint and frozen confirmation choices. All new functions must arise from generic mutation of random-origin material; do not supply a hand-written connectivity test, backtrace or route cleanup. Only a confirmed combined gain should justify another longer continuation. This proposal is not launched: M16 is closed and its populations, variants and evidence remain available.

Primary joint-mutation passes: **0/4**. Eligible reference endpoint on fresh confirmation: **True**. These are fixed one-/two-edit neighborhoods of two related random-origin anchors, not independent evolutionary replicates.

## Same-case anchors

| Anchor | Pairs /400 | Corridors /200 | Ordinary both poses /256 | Correct no-path /168 | False reachable no-path |
|---|---:|---:|---:|---:|---:|
| anchor/parent | 128 | 166 | 14 | 168 | 0 |
| anchor/child | 184 | 200 | 8 | 0 | 0 |

## Prospectively frozen nominees

Joint restoration requires the exact union of both anchors’ pair, corridor, ordinary and correct-disconnection successes, all child target pairs beyond protected references, zero false no-path, and nonempty denominators. A diagnostic pass is an intervention result, not an evolved discovery. Aggregate ranking uses the same mutation pool and development inputs. No final-data role substitution.

| Role | Identity | Targets kept | Required ordinary lost | Required disconnections lost | False | Pass |
|---|---|---:|---:|---:|---:|---|
| parent/depth1/joint | parent/mutation/0128 | 0/16 | 0 | 0 | 0 | False |
| parent/depth1/aggregate | parent/mutation/0284 | 0/16 | 1 | 0 | 0 | False |
| parent/depth2/joint | parent/mutation/0727 | 16/16 | 6 | 168 | 0 | False |
| parent/depth2/aggregate | parent/mutation/0135 | 0/16 | 1 | 0 | 0 | False |
| child/depth1/joint | child/mutation/0888 | 16/16 | 6 | 168 | 0 | False |
| child/depth1/aggregate | child/mutation/0098 | 0/16 | 11 | 0 | 0 | False |
| child/depth2/joint | child/mutation/0827 | 16/16 | 8 | 168 | 0 | False |
| child/depth2/aggregate | child/mutation/0421 | 0/16 | 0 | 0 | 0 | False |
| diagnostic/joint | child/ports0/0-1 | 16/16 | 6 | 168 | 0 | False |
| random/joint | random/0953 | 0/16 | 14 | 168 | 0 | False |

All fixed diagnostics were carried forward before confirmation: 72 aliases; 0 pass the full gate. Diagnostic pass identities: `[]`.
Every nominee and fixed diagnostic has full exact-parent/child gains/losses, protected-union comparisons and ordinary length strata in summary.json. Nomination roles can alias the same genome and must not be counted as independent successes.

## Passive regulation traces (development data)

The parent C0 update is min(65535, C0 + max(0, C5 − source flag)); the child substitutes C7 for C5. The recurrence passed at every site of every recorded complete tick. The trace adapter makes no candidate change and stops at the original runtime limits. Terminal fields match production M1 and the saved screen responses; all histories replay in the trace audit. This verifies that recurrence and the recorded behavior, not a universal algorithmic explanation.

| Group | Anchor | Status | Ticks | Path pixels | First state divergence |
|---|---|---|---:|---:|---:|
| corridor | parent | emitted | 5 | 3 | 2 |
| cycle/2 | parent | emitted | 13 | 8 | 2 |
| cycle/4 | parent | emitted | 17 | 12 | 2 |
| cycle/8 | parent | emitted | 25 | 15 | 2 |
| disconnected | parent | no_path | 37 | 0 | 2 |
| ordinary_disconnected/15 | parent | no_path | 61 | 0 | 2 |
| ordinary_disconnected/9 | parent | no_path | 44 | 0 | 2 |
| ordinary_perfect/long | parent | emitted | 43 | 31 | 2 |
| ordinary_perfect/medium | parent | emitted | 19 | 11 | 2 |
| ordinary_perfect/short | parent | emitted | 13 | 9 | 2 |
| ordinary_random/long | parent | emitted | 53 | 97 | 2 |
| ordinary_random/medium | parent | emitted | 29 | 64 | 2 |
| ordinary_random/short | parent | emitted | 15 | 22 | 2 |
| two_junction/2 | parent | emitted | 13 | 8 | 2 |
| two_junction/4 | parent | emitted | 17 | 12 | 2 |
| two_junction/8 | parent | emitted | 25 | 15 | 2 |
| corridor | child | emitted | 5 | 3 | 2 |
| cycle/2 | child | emitted | 13 | 7 | 2 |
| cycle/4 | child | emitted | 17 | 11 | 2 |
| cycle/8 | child | emitted | 25 | 23 | 2 |
| disconnected | child | step_budget | 256 | 2 | 2 |
| ordinary_disconnected/15 | child | read_budget | 77 | 83 | 2 |
| ordinary_disconnected/9 | child | read_budget | 74 | 33 | 2 |
| ordinary_perfect/long | child | emitted | 43 | 39 | 2 |
| ordinary_perfect/medium | child | emitted | 19 | 19 | 2 |
| ordinary_perfect/short | child | emitted | 13 | 7 | 2 |
| ordinary_random/long | child | emitted | 53 | 95 | 2 |
| ordinary_random/medium | child | emitted | 29 | 76 | 2 |
| ordinary_random/short | child | emitted | 15 | 40 | 2 |
| two_junction/2 | child | emitted | 13 | 7 | 2 |
| two_junction/4 | child | emitted | 17 | 11 | 2 |
| two_junction/8 | child | emitted | 25 | 19 | 2 |

## Protocol, ancestry and costs

Mutation proposals: 2,048, comprising 1,024 per exact anchor and 3,072 mutation opportunities; 29 proposals have only genotype-no-op events. Each anchor has 512 one-edit and 512 sequential two-edit variants, plus 1,024 common random references and 72 fixed diagnostic probes. Parent-derived variants have 1–2 M16 edits from the inherited parent; child-derived variants have 1–2 M16 edits after the single M15 edit. No ancestral chain or known solver was silently substituted.

Pool seed 2026102202, development seed 2026102203, confirmation seed 2026102204. All pool variants were published before the common 712-input development panel; all choices were published before the 1,680-input independent panel. Related grammar contexts and poses limit transfer claims. Equal logical evaluations do not imply equal CPU. Separate intact controls are never parents.

| Phase | Calls | Candidate seconds | Worker CPU seconds | Wall seconds | Work | Peak tree RSS GiB |
|---|---:|---:|---:|---:|---:|---:|
| screen | 2,048,424 | 3186.20 | 3261.14 | 370.00 | 1,018,882,919,407 | 3.895 |
| final | 156,240 | 178.25 | 185.08 | 41.65 | 58,944,417,380 | 3.562 |

Passive traces add 64 executions (instrumented plus native), 29,046,204 work, 0.11 instrumented seconds, 0.03 native seconds, and 5.86 wall seconds. Trace audit separately adds 64 executions/29,046,204 work/5.85 wall seconds. Instrumentation allocation is recorded per trace and excluded from production candidate memory.

Screen audit: 2,048,424 independent grades; 122,524 native replays; 188.08s. Final audit: ALL 156,240 native responses/grades and summary, plus 5,040 BFS/A*/bitwave calls; 117.07s. Both intact controls solve every queried input. Shared VM/mutation code, independent raster grader; not a second full interpreter.

Five focused tests passed, not the full suite. Two successful pre-registration artificial-founder rehearsals are preserved, including the initial rehearsal before an exclusion observer was added. The observer records early rejected layouts without changing accepted cases, query order, metadata or RNG; fixture equivalence was checked. Preparation costs in both preflight.json packets are additional, not scientific discoveries. Unit tests additionally execute 15 native/15 instrumented cases per invocation, with two invocations; timing was not separately instrumented. All fixture and test layouts are excluded.

No post-registration scientific repair, new runtime, recombination, solver injection or final-data reselection. Preserve all M15 and M16 records. Any further experiment needs a new protocol; none is launched by this report.

## Preservation and publication

Registration ea90c23, fixed pool 926592b, and choices fab2457 were pushed before their downstream scientific generation. All 346 registration hashes, 401 M15 completion hashes and 11 M15 local records verify. Both SQLite originals and table-by-table verified backups are retained; the phase used 0.146 GiB including backups at preservation, with 52.07 GiB free. All 3,357,403 layouts are excluded through the immutable reference-plus-delta ledger: 3,349,451 initial, 2,448 screen and 5,504 final. Every native candidate call has an independent raster grade; zero uncertain receipts or guard bypasses occurred. No scientific audit failed or registered source changed.
