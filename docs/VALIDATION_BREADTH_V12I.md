# V12I — fixed-pool, equal-budget validation breadth

Protocol fixed before new validation evaluation. No evolution, mutation, runtime
change, or use of inspected H cases for selection. Seed **2026101904**; software
fixture seed **1234**. This is a selection-coverage experiment, not a new claim of
evolutionary discovery, general solving, or computational speedup.

## Frozen pool and attribution

Each of the 30 G conditions retains its own origin, topology, policy, method and
replicate. Membership includes all 96 initial validation-screened individuals
(including protected anchors) plus every later validation nominee in that
condition's saved G history. Initial evaluations physically shared across G
policies count as initial screening in each aliased condition. No H performance
filter and no transfer between condition pools. Genotype duplicates within a
condition share one allowance; every identity and nomination generation survives.

This performance-blind rule yields 3,632 identity memberships, 3,612 genotype
memberships and 1,878 physical genome/topology configurations. The actual bytes
are frozen in `results/validation_breadth/pool.json.gz` before any candidate
profiling. G initial states, checkpoint and all 113 lineage segments identify
their exact source. Carry/fresh, local/evolved, Current/Branch and fresh random
resampling remain distinct. Equal availability of anchors is automatic because
both selectors use the identical whole condition pool. No known solver enters it.

## New task distribution

Boards are 25×25. Four strata cross source-to-choice prefix lengths 1–3 / 4–8
with two independently sampled goal-tail lengths 3–4 / 5–9. These are G-like and
H-like prefix ranges under a common new grammar, not literal replications of
either generator. Reachable distances therefore range from 4 to 17 edges.

Each independent context has three matched graphs: one-junction fork,
two-junction tree with an extra dead-end, and one genuine alternative-route
cycle. Source, goals, unique shortest routes, eight isolated clutter sites and
poses are shared. The cycle joins internal vertices on opposite goal arms, at
least two edges from the main choice vertex. Its alternate routes are longer and
also legal illuminated rasters. The truncated connection supplies the dead-end.
Two matched pruned corridors add one input for each goal. Corridor layouts
differ and never count as goal-switch pairs. Cut controls remove the main choice
vertex and disconnect both goals from the source.

All graphs have eight recorded D4 poses. Poses and graph variants are correlated;
the independently constructed context is the unit for generalization summaries.
The source-prefix/goal-tail comparison also changes geometry; the study's causal
contrast concerns validation breadth, not any isolated biological mechanism.

A pre-calibration geometry check found a defect in the initial fixture proposal:
attachments one edge from the choice vertex made the intended alternate raster
contain a chord. Before any genome inference, attachments were constrained to
at least two edges and the short goal-tail range became 3–4. The original four
contexts/192 whole layouts remain in `validation_breadth_preflight`; their 320
inputs received no candidate evaluations. All are excluded along with every
138,712 layout through H and the corrected 192 fixture layouts. This development
correction precedes registration, validation and final generation.

## Equal validation allowance

Three independent draws, one per historical replicate, are shared across all
matched conditions in that replicate. There are not 30 independent draws.

| Selector | Contexts per stratum | Poses per context | Total independent contexts | Inputs |
|---|---:|---:|---:|---:|
| Narrow | 1 | 4 | 4 | 128 |
| Broad | 4 | 1 | 16 | 128 |

Each queried pose has six branched inputs (three two-goal pairs) and two corridor
inputs. Every selector thus evaluates 48 branching pairs and 32 corridor inputs
per genome. The four poses for stratum `s`, replicate `r` are
`((r+s) mod 2) + {0,2,4,6}`. Broad assigns one of these to each context; narrow
uses all four on one context. Family, stratum, side and pose counts match exactly.
Both arms generate and exclude all eight poses, including unqueried ones.
Validation has no disconnected cases; no-path is tested independently at final.

Each genotype receives **128 inputs per selector** in its own replicate draw.
Across condition pools this is 462,336 logical calls per arm. Sharing identical
genotypes/cases between conditions reduces this to 240,384 physical calls per
arm, equally. The independent layouts may induce different actual work and wall
time: equality is of evaluation allowances, not padding CPU time. Those costs
are recorded separately. Arm order alternates across physical models.

## Selection rule and freeze

Both selectors maximize the same lexicographic rank:

1. Complete shortest branching pairs, over all three families.
2. Minimum complete-pair count across the three families.
3. Individual shortest branching outputs.
4. Individual legal branching outputs.
5. Shortest matched corridor outputs.
6. Negative count of false no-path claims on reachable inputs.
7. Sum of the existing bounded partial-route score on branched inputs, rounded
   to eight decimals.

An exact rank tie selects the lexicographically smallest topology/digest. Work
cannot reward an incomplete output. This ordering is fixed across all original
G policies; the isolated contrast is the coverage of the validation data.
No second archive or selection based on final results.

Every normal output mask, status, tick count, work counter and score is saved.
All 60 choices (two per condition), validation scores/data, and hashes are
committed and pushed before final generation. Runtime verifies exact committed
selection bytes and pushed ancestry. Original populations, RNG and archives
are never modified or resumed.

## Untouched final set and primary decision

Generate 16 independent contexts per stratum: **64 contexts**, all eight poses,
all three matched branching graphs and two corridors. The first two contexts
per stratum also receive cut no-path controls. Per selected model: 3,072
branched inputs / **1,536 shortest-pair opportunities**, 1,024 corridors and
128 no-path inputs, totaling 4,224. Evaluate only the frozen selections, with
physical deduplication, plus separate intact and west-return-gate known controls.
Compiled BFS, A* and bit-wavefront receive all final inputs for correctness.

Report each historical replicate and cohort, completed pairs, independent
contexts with any/all-eight-pose success, legality versus optimality, graph and
distance strata, corridor retention, no-path and false-no-path counts. Context
counts spanning matched graphs are unions, not tripled independent observations.
Current G selections are not reevaluated as extra final nominees; this experiment
isolates the two new selectors on the frozen pools.

A replicate passes the broader-selection gate only if all hold on final:

- Broad gains at least eight complete paired poses over narrow.
- Broad gains at least two independent contexts with a complete pair.
- At least one cycle context succeeds under broad but not narrow.
- Pair counts improve in at least one stratum other than short-prefix/short-tail.
- Broad retains at least 95% of narrow's correct corridor outputs.
- Broad does not increase false reachable no-path claims.

A cohort passes only with at least **two of its three** historical replicates.
The ten cohort screens are decision gates, not multiplicity-adjusted statistical
discoveries. No automatic new evolution run or budget extension follows a pass.
Descriptive 95% intervals use 2,000 paired context bootstrap draws, stratified
over the four groups of 16 contexts; all poses, graph variants and selected
replicates stay together. They condition on these fixed selections, do not
estimate new-lineage or new-validation-draw variation, and are not causal
evidence about evolved capacity or nonlocal signals.

## Cost, calibration and audit

Unchanged V6 pulse runtime, up to 256 genes, 256 ticks, 4,096 reads/site and
32,768 dispatches/site. No oracle within candidate inference. Genome construction
and validation cannot execute arbitrary code. Boards fix candidate memory size.

The main validation-plus-final inference cap is **720 candidate-call seconds**,
with a hard maximum of **1,200,000 calls** and a five-second scheduling reserve.
Maximum final calls are 62 physical models × 4,224 = 261,888; actual deduplication
may reduce this. Stop and retain partial data if capped; never compare incomplete
arms or extend the budget. Model construction, external grading, data generation,
serialization, tests, JIT warmup and audit are recorded outside that cap.

Calibration has a separate closed 60-second / 10,000-call ceiling: intact and
damaged controls on all 320 fixture inputs, plus every physical pool model on
one predetermined fork goal/pose per stratum (four inputs). Scores from this
panel never enter selection. Profiling completed in 6.10 candidate seconds and
predicts approximately 388 seconds for validation, leaving final-evaluation
reserve. Exact read-only uint8 production signatures are warmed on saved fixtures.

There is no new speedup benchmark in I. Total candidate seconds, read/dispatch
work, construction time, memory and baseline correctness are reported; they are
not a fair per-solution latency comparison. Prior controlled timings remain slow.

Audit reconstructs the pool from original G provenance; verifies frozen source,
inputs and prior completion hashes; independently checks graph distances,
unique shortest paths, real longer paths, all poses and whole-layout exclusions;
regrades every saved raster and deterministically replays every new candidate
and final baseline response; recomputes exact budgets, ranks and all selections.
Audit inference is separately recorded, not an extra search opportunity. New
tests exercise equal allowances, membership, independent graph/raster checks,
selection ordering, budget guards, freeze enforcement and gate logic.
