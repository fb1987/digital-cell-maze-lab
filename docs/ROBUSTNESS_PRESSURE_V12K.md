# V12K — context consistency pressure, with a fixed runtime

Status: preparation and software calibration; registration is the hashed packet
`results/robustness_pressure/preregistration.json`, committed and pushed before
independent diagnostic/search generation. Seed 2026101906; fixtures 1254.

## Question and causal scope

Does prioritizing complete goal-switch pairs across poses improve generalization
and retention, given identical input budgets, initial states, runtime and mutation?
The Pair comparator ranks complete branched pairs first. This implements the
pair-count comparator in the J proposal; it is **not identical to G Current's
valid-output-first breeding policy**. No G-to-K score difference identifies a
selection effect. Only the matched K Pair/Context contrast does.

The Context policy inserts the count of context × graph-family groups solved on
**every queried pose** ahead of Pair's common rank. Training queries four poses
per context; validation and final query eight. Remaining fields are pair count,
shortest individual count, legal count, correct-minus-false no-path count, common
bidirectional partial output shaping, and work only after all outputs are correct.
Lexicase uses the same case shuffle/RNG and tolerance, with one extra leading
consistency field (zero in Pair); following fields are paired, shortest, legal,
and common partial credit. No runtime, capacity, pulse, stopping or gate changes.

## Frozen foundations, not resumed old experiments

Thirty conditions: carry/fresh × local/evolved × Pair/Context × three replicates
(24 evolution), plus fresh resampling per topology and replicate (six). Each has
96 organisms, 24 elites, 72 births, nine random immigrants, single-edit mutation,
256-gene limit and the unchanged V6 pulse runtime/LIMITS. Resampling redraws all
72 births and uses Pair nomination. Random genomes use the established rich
64–128-gene distribution. Fresh random seeds match across topologies, but no known
solver enters any lineage. Carried organisms are copies of G Branch generation
113 populations/RNG. Existing protected anchors, G archives and BOTH I selectors
from that same G condition are deduplicated by genotype and protected (13–18).
Missing anchors replace only unprotected tail slots, identically in paired arms;
unmodified donor populations and additions are saved. This is a new study, not
an extension of closed G. Fresh foundations contain no injected saved genomes.

All fourteen J panel identities (thirteen random-origin and separate intact)
are retained unchanged as explicitly **J-informed** controls, including parents,
shared ancestor, rare long-prefix/local exceptions and the unmutated 68-gene draw.
No selection uses K diagnostic/final outcomes. All old populations/RNG remain.

## Geometry, exposure and independence

Balanced straight and turning goal arms, source prefixes 1/2/3/4 during training,
straight or bent at far prefixes. A context has fork, matched extra dead end,
genuine longer opposite-arm cycle, two pruned corridors and disconnected controls,
eight D4 poses and two goal stimuli. Source and goal are endpoints on reachable
inputs. At prefix one the disconnected source is isolated. Eight identical isolated
clutter cells accompany each context's graph variants. Unique shortest routes and
legal longer alternatives are independently checked. This is a restricted grammar,
not a general-maze benchmark. Shapes, poses and graph variants are correlated;
the independently seeded context is the sampling unit.

Training has two independent contexts per batch, one per goal-arm shape. Each
queries one graph family, four balanced poses × two goals, plus two matched
corridor inputs at one pose: twenty responses/organism. Graph families rotate
modulo three, source prefixes 1/1/2/(3 or 4) modulo four; far straight/bent alternates.
This crosses rather than confounds the graph/prefix schedules. All 80 generated
inputs per context are retained/excluded, even unqueried poses and controls.

Validation per replicate has four independent contexts: both goal shapes ×
prefix-one straight/prefix-four bent; three graph families × eight poses × two
goals plus four corridor inputs/context = 208 inputs. Common validation archives
in BOTH arms are context-first, pair-first, corridor, and far-prefix-pair-first.
Every eighth generation nominates exactly four distinct genotypes (identity
fallback) per condition. Archive tie-break is smallest genome digest. All archives
are protected in the common elite rule; all nominees/rows are saved. Primary final
selection is the common context archive, secondary the common pair archive;
initial frozen selections use these same rules. No final reselection.

Initial identical screens are computed once physically per foundation class
(twelve) and aliased across policies/resampling; every condition has the same
logical call allowance. Later every condition performs exactly 96×20 training
calls per matched round and 4×208 validation calls every eighth round. Population
and mutation opportunities, including resampling, stay equal.

## Calibration and fixed diagnostic

Software calibration precedes registration. Intact must solve every reachable
and disconnected fixture. At least one frozen random-origin panel member must
complete at least four of eight prefix-one fork pairs for EACH goal-arm shape.
These need not be the same genome; this is a usable starting-skill gate, not a
claim of universal near competence. No geometry or panel filtering by candidate
performance after registration. Fixed positions 0,12,…,84 from all twelve founder
classes profile production signatures. Project initialization (96×208/class)
and each condition's 96×20 plus amortized validation separately, weighted by
planned calls. Require sixteen projected rounds plus initialization <620 candidate
seconds and diagnostic projection <180 seconds. These estimates exclude Python
selection/logging overhead; the wall guard remains authoritative.

Independent diagnostic: 24 new 21×21 contexts, both goal shapes × source
(1 straight,2 straight,4 straight,4 bent,8 straight,8 bent) × short/long goal tails.
All fourteen models, normal and nonlocal-zero, all 1,920 inputs/model/configuration.
53,760 calls, 180 candidate-second cap. Nonlocal reads remain charged. Both models
and cases are fixed before generation; diagnostic results cannot change search.
Rescue screen per target: positive pair gain on at least four independent contexts,
including BOTH goal shapes, at least two newly all-eight-pose context/family groups,
no corridor decrease, and no loss of any normally solved prefix-four-or-eight pair.
Report rescue and losses even if the conjunctive screen fails. External zeroing
is not a heritable or evolved regulatory mechanism.

## Pilot cap and fresh gate

Search: 720 seconds wall including initial validation, all candidate inference,
selection, logging, training generation and checkpointing. Validation construction,
JIT warming and preparation are timed separately. At most 64 matched rounds,
4 million physical calls, 2 GiB saved study files and 4 GiB process RSS.
Reserve 1.3×longest round +8 seconds before launching; 716-second inner deadline
leaves checkpoint time. Per-response cap guard; if interrupted, retain partial
rows/states and use only the last complete matched round, never restart/extend.
A result with fewer than sixteen completed rounds is explicitly underpowered.

Freeze all selections/populations/RNG and push BEFORE final corpus generation.
Final uses another 24 contexts under the same prespecified 21×21 strata as the
diagnostic, excluding diagnostic/validation/training/fixtures/all prior layouts.
Normal inference only for all unique primary, secondary, frozen and fourteen
panel controls; maximum 360 candidate seconds. BFS/A*/bit-wave are correctness
controls. No latency-speedup claim from search or this assay.

Expansion gate, separately per origin/topology (three replicates), on common
context-archive primaries: Context exceeds Pair by >=2 all-eight-pose
context/family groups AND >=16 complete pairs; also exceeds its frozen initial
by these same thresholds; corridor count >=95% of BOTH Pair and frozen counts;
retains every independently tested context/pose/graph pair with prefix>=4 solved
by either Pair or frozen (case identities, not just totals); no extra false
reachable no-path. Require at least two of three replicates AND at least sixteen
completed rounds. These correlated matched comparisons are a numerical screen,
not a significance test or proof of generalization. Failure does not close the
fresh random-origin track. No automatic 60–90-minute extension.

## Audit and preservation

Save all masks/counters, fitness, nominees, concrete mutation events, RNG states,
protected anchors, aliases, histories, next populations and full generated layouts.
Independent graph/raster grading, exact candidate replays, mutation event replay
and deterministic full reproduction replay verify all matched search rounds and
final outputs. Verify old G/H/I/J completion hashes and freeze hashes. Unit geometry
fixtures receive no candidate inference and are also retained in exclusions.
Do not repair frozen code silently or label a partial audit as a full pass.
