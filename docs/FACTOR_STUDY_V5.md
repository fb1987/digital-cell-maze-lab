# V5: factorized reward curriculum

Preregistered before training or final evaluation, October 18, 2026.
Root seed2026101803. Offline Apple M4 CPU; no external services or new packages.
V1–V4 code/results remain unchanged. This tests reward accessibility, not a
claim that more capacity, time or biological language guarantees emergence.

## Paired conditions and provenance

Fork six V4 **goal-pressure** next populations and RNG checkpoints after40
generations, local/evolvable topologies x three replicates. Each fork starts
two paired arms of96 organisms: `product` and `curriculum`. Both copy the same
genotypes and RNG state. Preserve the fixed V3 signalling elite already carried
by V4 and the V4 validation-selected goal archive as fixed elites. If the latter
is absent by genotype, replace the last non-protected slot identically in both
arms; record IDs, replacements and hashes. Deduplicate identical elite genotypes.
No genome is selected using prior final-test performance. No known solver or
hand-built update rule is introduced.

Eight uint16 channels,64 registers,128 genes and the V2 inference runtime remain
fixed. Training caps256 ticks /4096 attempted reads per site /32768 dispatches
per site; validation/final caps1024 /8192 /131072. Mutation remains1–6 edits,
roughly10% fresh random immigrants and10% uniformly selected parents, otherwise
epsilon lexicase, with behavioural niches and the two fixed elites retained.

## Only the training shaping schedule differs between arms

Use the unchanged V4 normal-response validator and paired source-present/removed
tick16 observer. Let Q be V4 source-dependent, source-connected output quality
(progress, connected fraction and source fraction, divided by1+2*excess degree).
Let S be goal specificity: positive connected progress difference when the goal
changes. G=sqrt(Q*S) is V4's conjunction score. Unreachable or unaligned paired
probes get zero new bonus, even if diagnostic factors are nonzero.

- Product arm: bonus=2G throughout.
- Curriculum generations0–15: bonus=Q+S.
- Generations16–31: bonus=(1-alpha)*(Q+S)+alpha*2G,
  alpha=(generation-15)/16.
- Generations32 onward: bonus=2G, identical to the product objective.

Both bonuses are bounded[0,2], with the same maximum. The arithmetic combination
is larger than the geometric combination away from equal factors, deliberately
providing denser credit. This two-arm test evaluates the **factorization plus
schedule** package; it does not separately identify reward magnitude, scheduling
or a constant additive objective.

Training fitness remains valid routes, optimal routes, no-path utility,
normal partial + V3 source-transmission score + bonus, then inference cost only
for completely correct normal responses. Lexicase adds the same bonus to its
partial field. Ordinary inference never sees the oracle, distances or rewards.
Both arms pay for identical observer calls and caps; report actual work.

Validation always uses alpha=1 for both arms, including initial frozen controls.
Maintain task, goal, transmission, quality and specificity archives. **Task rank
uses common ordinary-route fitness with no source/probe reward**, avoiding
arm-specific diagnostic shaping in final task selection. Other ranks use their
named validation measure, with valid/optimal tie-breaks. Nominate training overall,
source, conjunction, quality and specificity leaders, plus up to three niches
every tenth generation, identically in both arms. New V5 validation archive
members never automatically enter reproduction; only the fixed ancestral elites
receive protection.

## Fresh environments

Exclude whole layouts from all V1–V4 manifests and across V5 splits. A pair shares
only geometry/source, with divergent goals. Reachable source distance>=8;
target-to-target distance>=the larger source distance. Two rotating training
pairs per generation: perfect plus cyclic, replacing the latter with a mixed
reachable/unreachable disconnected pair every fourth generation. Sizes9 through
generation23,17 thereafter; distances8–16 initially,8–32 later. Fixed validation
has six pairs per replicate: sizes9/17 x perfect/cyclic/disconnected.

Use the tested Wilson spanning-tree generator for **all size9 perfect splits**,
avoiding V4's exhausted corner-DFS pool. Larger perfect mazes retain DFS; cyclic,
disconnected and rectangular generators are unchanged. This sampling and the
extra archive nominees apply equally to both arms, so cross-study V4 absolute
scores are not an objective-only comparison. Record every input and rejection.

## Bounded continuation decision

Screen48 generations,96 organisms,12 conditions. This includes16 generations
after both training objectives have become identical. Estimate10–15 minutes of
search plus separately timed fresh evaluation. Reuse **exactly V4's validation
extension thresholds**: extend all paired conditions through128 then192 if:

- One topology gains at least two optimal validation routes in aggregate under
  curriculum relative to both frozen task and product controls; or
- In at least two of three replicates of one topology, curriculum goal archive
  mean G>=0.05, >=frozen+0.04 and >=product+0.03; Q>=0.10; S>=0.05;
  both directions qualify in>=25% regular pairs (each Q>=0.05,S>=0.02);
  positive G in perfect and cyclic families; and retained source signal is
  >=half the initial transmission archive's score.

Search ceiling75 minutes checked at generation boundaries. Preserve exact next
populations/RNG states and report actual generation counts if capped. Increased
Q or S alone cannot trigger an hour-scale extension. Do not change criteria after
inspecting outcomes. Final genomes freeze before generating final tests.

## Primary endpoint, cost and diagnostics

Primary fresh final set264 layouts:216 reachable and48 disconnected, perfect/
cyclic sizes9/17/33/65 and rectangular9/17, unrestricted endpoints. Report exact
valid paths and shortest-path optimality separately, and distance>=8 separately.
Additional paired final set24 layouts/48 inputs:42 reachable at distance>=8 and
six unreachable. Report normal outputs separately from intermediate probe scores.

Evaluate task/goal archives and both initial frozen controls for each arm,
alongside compiled BFS/A*/bit-wave emitting the same full raster. Other archives
remain in checkpoints but are not additional primary selections. Time30 warm
randomized repetitions on fixed17/33 perfect/cyclic tasks; include input decoding,
all updates and raster emission. Failed outputs earn no speed credit. Record
work, range reads, arrays/RSS, Python/dependencies, source and fork hashes.

Audit saved final rasters, probe metrics, fitness decomposition, curriculum
schedule, ancestral elites and layout independence. Record factor co-occurrence
throughout training, not just selected archive scores. Apply a frozen nonlocal
read ablation to the multirange goal archives under both objectives, ablating
both inference and probes without retuning. Save lineage logs, all evaluated
genomes, fixed controls and full RNG/population checkpoints. Keep prior evidence
immutable. A failed bounded run does not close the random-origin research track.
