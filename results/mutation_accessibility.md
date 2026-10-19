# V12R — mutation accessibility beyond the emitted wave

Completed and independently audited, October 19, 2026. Local Apple M4 CPU.

**Longer random mutation walks produce more behavioral changes, but this assay
finds no reproducible improvement in routing through an internal junction.**
The result narrows the problem: this sample contains little useful mutation
supply for the current selection process to amplify. It does not establish that
random-origin discovery, more expressive regulation, or longer evolution cannot work.

All 63 physical random-origin models in untouched confirmation complete zero
paired routes with a positive shared prefix, and zero two-junction or genuine
alternative-cycle pairs. Both the correctness and partial-progress gates fail
in all 15 root/replicate blocks at depths 4 and 16. No larger run is launched.

One frozen 16-edit selection improves partial geometry only on the broader final
set. Its 152 newly correct outputs are corridors; it does not solve any new paired
branch task. Preserve it as useful diversity, not a confirmed branch-isolation gain.

![Mutation supply and final partial scores](mutation_accessibility/mutation_supply.png)

## What was tested

Five roots were explicitly chosen using earlier P/Q evidence: P's depth-9 routing
genome; Q fresh/mixed replicate 0; Q fresh/current replicate 1; Q fresh/mixed
replicate 2; and Q's unmutated 95-gene random resample. Their exact ancestry remains
random-origin. The intact known solver is a separate correctness control and never
an ancestor. Root labels below are short labels for these frozen identities.

For each root, three independently seeded blocks contain 16 random walks of 16
single edits and 16 fresh random draws. All genomes, 3,840 concrete mutation events,
and RNG states were generated and frozen before scoring. The timing amendment
selected the first eight walks/draws per block without using performance:
120 walks, their 360 checkpoints at depths 1/4/16, and 120 fresh draws enter the
scientific comparison. All remaining genomes and intermediate states stay saved.
The scientific subset contains 1,920 accumulated mutation steps. There is no
selection feedback between edits and no breeding in this assay.

The established local runtime, goal inputs, stopping, mutation operator and
256-gene ceiling are unchanged. Queried mutant sizes span 91–151 genes; the
capacity ceiling is not reached. Three depth-1 identities duplicate their root
genotype; all depth-4/16 identities differ. Genotype change is not necessarily
output change. Internal counters are instruction/read/work observations, not
full trajectories or per-channel causal measurements. Static channel/opcode
summaries are labeled static.

Discovery and separate validation each use 768 inputs: eight new clutter contexts,
straight or turning asymmetric arms, matched source-at-junction/one-edge-prefix
placements, eight poses, two goals, paired branches, pruned corridors and isolated
unreachable goals. The common discovery rank nominates two candidates per arm;
validation chooses one. All choices and data were pushed in **74d6d17 before
final generation**. No final-based replacement occurs.

Confirmation uses 28 new clutter contexts and 5,184 inputs/model: 1,728 branched,
1,728 corridors and 1,728 no-path controls. It adds arm lengths 4/6 and 6/4, two
clutter replicates per core form, prefixes 0/1/2, and matched forks, second junctions
and true alternative-route cycles. All boards are 19×19. These are structured
diagnostic geometries, not a general maze benchmark. Route forms recur; poses,
goals, nested mutation depths and variants are correlated. RNG blocks share their
root and are not independent rediscoveries of it.

## Mutation supply on discovery

Each row contains 120 candidate memberships, evaluated on the same cases.
“Retained” means at least 95% of the root's junction pairs and corridor successes,
with no increase in false no-path claims. Output change compares complete raster
and status sequences; counter change also includes ticks and internal work.

| Arm | Counters changed | Output changed | Root skills retained | Partial score increased |
|---|---:|---:|---:|---:|
| 1 edit | 87 | 7 | 113 | 0 |
| 4 edits | 116 | 26 | 94 | 0 |
| 16 edits | 120 | 75 | 46 | 0 |
| Fresh random | 120 | 120 | 0 | 0 |

Every one of the 360 mutant checkpoints and 120 fresh random draws completes
zero one-edge-prefix pairs. No mutant increases the registered mean partial
score over its root, even before requiring the larger preregistered improvement.
Of 120 sixteen-edit checkpoints, 45 preserve the entire output/status sequence;
74 reduce the mean partial score; one changes output while leaving that score
unchanged. This last candidate is the final-only exception discussed below.

The partial score uses goal-specific occupancy of private arm interiors multiplied
by the weaker path F1 of the two outputs. It includes all 361 board positions and
counts only normal emissions. It is a diagnostic proxy, not correctness: a wave
can score positively while still emitting an extra branch. Greater scores across
discovery and final are not themselves a gain, because the geometry distributions
differ. Only within-stage matched comparisons support improvement claims.

The existing variation changes behavior increasingly often as edits accumulate.
Most such changes in this sample degrade the useful primitive. Selection cannot
amplify a measured improvement that this particular pool does not contain. This
does not exonerate every possible fitness design, nor prove an inaccessible
global fitness landscape: only 24 walks/root and three depths were scientifically
queried, and many intermediate genotypes were never evaluated on research cases.

## Untouched confirmation

Root performance on the same final set:

| Frozen root | Core junction pairs | Core one-edge-prefix pairs | Correct corridors | Correct no-path |
|---|---:|---:|---:|---:|
| P9 | 192/192 | 0/192 | 1728/1,728 | 0/1,728 |
| Qfresh0 | 96/192 | 0/192 | 1448/1,728 | 1728/1,728 |
| Qcurrent1 | 144/192 | 0/192 | 1728/1,728 | 1728/1,728 |
| Qfresh2 | 192/192 | 0/192 | 1728/1,728 | 1728/1,728 |
| Qrandom95 | 192/192 | 0/192 | 1728/1,728 | 1728/1,728 |

All 15 one-edit and 15 four-edit selections match their corresponding root's final
pair/corridor counts and mean partial score. Among the 15 sixteen-edit selections,
12 also match these metrics; the three exceptions all descend from Qfresh0.
Two lose substantial old skills. The third improves partial geometry and corridors.
All 15 selected fresh random controls complete zero branched pairs; three solve all
corridors. None of the final random-origin models falsely declares a reachable
input disconnected. Correct no-path results apply only to the tested isolated-goal
controls, not arbitrary disconnected components.

The stronger frozen wave roots retain 192/192 core source-at-junction pairs and
32 stress-fork junction pairs, for 224/864 total pairs. They still complete
0/192 core one-edge-prefix pairs, 0/192 core two-edge-prefix pairs, and zero
second-junction/cycle pairs. This preserves useful local behavior without resolving
the missing branch suppression.

BFS, A*, bit-wavefront and the intact VM each correctly solve all 3,456 reachable
and 1,728 disconnected final inputs. No candidate latency benchmark was run.
General solving, a causal multirange advantage and a competitive speedup remain
unestablished.

## The final-only exception: preserve it, interpret narrowly

The frozen selection `accessibility/Qfresh0/1/walk2/d16` descends from Q's
`fresh/0/mixed/i1151`. Its validation raster/status sequence is exactly equal to
its root's, while internal counters differ. Its validation partial score remains
0.262205 and there are no new pairs. It was selected by the fixed rank/tie-break;
the final set played no role in its selection.

On final, its mean core one-edge-prefix score rises from 0.302841 to 0.400445;
32 pairs across eight clutter contexts exceed the individual improvement threshold.
Corridors rise from 1,448 to 1,600, with all 96 existing core junction pairs and
1,728 no-path results retained. Both genomes still complete zero positive-prefix
pairs. The gain is confined to the new 4/6 and 6/4 arm geometries. It passes the
root-relative partial criterion on final only, not validation, so the registered
two-stage gate fails.

A separately labeled post-hoc saved-data diagnostic uses an independent deque
traversal outside candidate inference. All 304 changed mutant rasters equal the
open cells at goal distance no greater than the source–goal distance. Eighty
previous budget-exhausted cases now emit; 224 change an already emitted output.
Exactly 152 responses become correct, all corridors; the other 152 remain wrong.
Across all reachable cases, goal-ball matches rise from 2,936/3,456 to 3,200/3,456.
The mutant is therefore not an exact wave on every case. These are output
comparisons, not proof of identical hidden dynamics or the causal necessity of
any particular edit. No extra candidate calls, forced traces or stopping retunes
were made. The full walk remains available for a future independently designed
mechanism test.

## Timing amendment, costs and verification

Original registration **dea1f0f** used twice the slowest group's mean fixture rate
for every planned evaluation. Its preflight failed and stopped with zero scientific
calls. The original profile and original auditor remain preserved. An explicit
timing-only amendment **abff7b9**, pushed before discovery, instead sums measured
individual discovery costs and each group's worst possible nominee cost. It retains
the factor of two, 600-second planning threshold, all eight orientations, frozen
pool and 720-second hard cap. Sixteen walks project to 648.06 seconds and fail;
eight project to 458.44 and pass. No fixture scores were inspected for scheduling.
This is a disclosed preregistration amendment, not a claim of an unchanged protocol.
The active amended auditor changes only the timing verification and associated
amendment checks. There is no post-data repair to frozen scientific source.

| Stage | Identity memberships | Physical models | Logical alias calls | Physical calls |
|---|---:|---:|---:|---:|
| discovery | 486 | 483 | 373,248 | 370,944 |
| validation | 126 | 124 | 96,768 | 95,232 |
| confirmation | 66 | 64 | 342,144 | 331,776 |

Main inference totals **797,952 physical calls**, 812,160 logical alias calls,
**133.24 candidate seconds** under the 720-second cap, and
**78,071,507,543 work units** (reads + dispatches + exposure checks).
Selection and final wall time total 164.22 seconds; peak main RSS
1141.39 MiB. The fixture profile
separately uses 91,776 calls/12.35 candidate seconds,
15.48 seconds wall. Three one-call candidate JIT warmups
and their nine baseline warmups are separate. Timing uses production immutable
byte inputs. Mutation preparation, oracle construction, grading, serialization,
analysis and audit are not represented as candidate compute. Unused allowance
was not spent after inspecting outcomes.

The independent audit passes on its first attempt: **889,728
exact candidate replays**, **905,280 independently graded
rasters**, 15,552 baseline replays, all 240 saved walks/
3,840 mutation events/240 random draws and their RNG, all choices, all corpus
geometry and exclusion hashes, 194 registered source hashes, 11 input hashes,
amendment hashes and **2,644 prior completion entries**. Audit wall
206.79 seconds, peak RSS 1189.19 MiB,
reported separately. The main audit independently checks full-board partial
score/spill/missing arithmetic as well as normal raster correctness.

Nine new core protocol tests, one timing-amendment test and ten related Q tests
passed during implementation (20 focused tests). The scoped repository collection
contains 283 tests; this is **not a fresh full-suite run**. Python 3.13.15,
NumPy 2.5.4, Numba 0.68.0, llvmlite 0.50.0, pytest 9.1.1, macOS 15.6 arm64.

## Research decision and next independent work

This result weighs against simply running the same operator longer as the next
expense. It also weighs against explaining failure solely as selection discarding
available improvements. It does **not** test a larger capacity ceiling, a new
regulatory representation, or sustained selection along a different path. More
capacity remains a hypothesis; the present programs never approach 256 genes.

Keep random-origin discovery central and preserve every original population/RNG,
all roots, the final-only exception, and useful archives. The next proposed step
is a bounded comparison of uniform mutation with an execution-informed mutation
operator, using the same random edit vocabulary and fresh random controls. First
verify observer/native parity and freeze the targeting rule without final-case
feedback. Test whether it increases **useful** changed behavior while preserving
the wave primitive, not merely activity or destructive changes. Normal paired
shortest outputs and fresh confirmation remain decisive. Exact parameters and
gates require a new preregistration; no next experiment or long search has begun.
See [the proposal](mutation_accessibility/next_experiment.md).

Exclude **191,784 whole layouts** next: 187,416 through Q + 464 R fixtures + 1,632
software fixtures + 320 discovery + 320 validation + 1,632 final. The helper
`mutation_accessibility_data.exclusions()` returns through Q only; append all five
R manifests, including software fixtures. Inspected final cases cannot become new
validation. Raw masks, every mutation/RNG, all selections and original timing
failure remain saved under `results/mutation_accessibility*`.
