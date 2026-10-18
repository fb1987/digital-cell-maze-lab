# V4: goal-conditioned path formation

Preregistered before this study's training/final tests, October 18, 2026.
Root seed 2026101802. No V1–V3 code/results are changed. CPU only, no new
packages, external models, arbitrary code generation or remote inference.

## Question and fixed capacity

Can learned random-origin signalling be coupled to a source-connected output
that responds appropriately when the goal changes? A broadcast is not a route.
Keep V2 inference and the eight-channel / 64-register / 128-gene genome fixed.
Training limits remain 256 ticks, 4096 attempted reads/site, 32768 dispatches/site;
selection/final limits remain 1024 / 8192 / 131072. The runtime never sees an
oracle, distance, route, family or seed. Normal completed path correctness is
always assessed by the unchanged independent evaluator.

Fork the six V3 **causal** next populations/RNG states after generation160,
local/evolvable topologies x three replicates. Both pressure arms copy the same
96 genotypes and RNG state. If the V3 transmission archive is absent by genotype,
replace the last initial slot with that learned genome, explicitly recording
provenance. Keep this **fixed V3 genome** as one protected elite in both arms.
New V4 validation archives never automatically enter reproduction. Preserve the
remaining population, behavioural niches and 10% fresh random immigrants. No
known solver, path decoder or manually assembled reaction rule enters a lineage.

Reset every objective/archive score on fresh selection/validation environments.
Retain task, transmission and goal-proxy archives plus all initial frozen
selections. Nominate the training leader, source-signal leader and goal-proxy
leader each generation, plus up to three niche candidates every tenth generation;
use identical nomination rules, mutation and epsilon-lexicase in both arms.

## Paired stimuli and generalization

Each pair uses identical maze bytes, dimensions and source, with two different
goal positions. Ordinary pairs have two reachable targets with source distance
at least8 and target-to-target distance >= the larger source distance. This
avoids nested targets that would make correct goal switching invisible. Oracles
choose environments outside inference; fitness accepts alternate legal routes.

Two pairs/four normal responses per generation: perfect plus cyclic. Every
fourth generation replace the cyclic pair with a disconnected grid containing
one reachable goal and one unreachable goal. Generations0–23 use size9 and
reachable distance8–16; generations24+ use size17 and distance8–32. Both arms get
exactly the same environments. Selection/validation has six fixed pairs per
replicate: size9/17 x perfect/cyclic/disconnected (10 reachable, two unreachable
responses); every reachable target has distance>=8. Tiny endpoint successes
cannot dominate this selection set.

Exclude **whole maze layouts**, not just input/endpoint hashes, used in V1–V3.
Keep layouts disjoint across training, selection, primary final and paired final
sets. Only the two members of an intentional goal pair share a layout. Save maze
and pair manifests and all seeds/rejections.

## Pressure comparison and paid probes

Comparator `transmission` is V3's causal objective under these matched V4
conditions: valid routes, optimal routes, no-path utility, partial+source-signal,
then inference cost only when all normal responses are correct. `goal` adds
**2 x the goal score** to that same intermediate field and to the lexicase partial
field. Earlier priorities and failed-output cost neutrality stay unchanged.
This compares the whole added shaping term; there is no fresh resampling arm.

For each normal response, run the existing V3 observer to fixed tick16 with
source present and removed (initial channel0 and source-flag register9 removed),
stopping disabled and work caps intact. Both objectives pay for all probes.
These same snapshots supply the source score and goal comparison, so no new
probe runtime/capacity is introduced. Retain packed probe rasters, source-removed
rasters and component metrics. Interrupted/unaligned pairs get zero goal bonus.

For each goal's tick16 raster:

1. Find only its illuminated four-neighbour component containing the source.
   Progress is 1 - minimum remaining distance / source-goal distance.
2. Penalize excess degree beyond1 at the source and beyond2 elsewhere, and the
   fraction of illumination disconnected from the source. Multiply by the
   fraction of selected component sites at source-distance>=2 that turn off
   when the source stimulus is removed. A goal-only pattern earns zero.
   Quality = progress x connected_fraction x source_fraction / (1+2 x excess).
3. Specificity = max(0, its progress toward this goal minus the other goal's
   raster-component progress toward this same goal). Detached goal pixels,
   source-only filaments and unchanged floods cannot earn this bonus.
4. Goal score = sqrt(quality x specificity), bounded [0,1]; unreachable goals
   score zero. Average over responses. This is an intermediate probe measure,
   never counted as a completed solution. The normal inference output may differ.

## Bounded screen and conditional continuation

Screen: 40 generations, 96 organisms, 12 paired conditions (two objectives x two
topologies x three replicates). A separate unit-root timing calibration estimates
about10–15 minutes; initial inherited genomes scored zero on that unit pair.

Extend all paired conditions through generations96 and160 if either:

- One topology gains at least two optimal selection routes in aggregate under
  goal pressure relative to both its frozen and transmission controls. All
  reachable selection routes have distance>=8.
- In at least two of three replicates of one topology, its goal archive has mean
  goal score>=0.05, >= initial+0.04 and >= comparator+0.03; quality>=0.10;
  specificity>=0.05; both directions qualify in >=25% of ordinary pairs
  (each quality>=0.05 and specificity>=0.02); positive goal scores in both perfect
  and cyclic families; and retained source signal >= half the initial source
  archive's score. Hidden signalling changes alone do not trigger extension.

Search wall ceiling75 minutes, checked at generation boundaries. Keep next
populations and RNG checkpoints, including if the ceiling binds; report actual
per-arm generations. Model archives freeze before any final test is generated.
Do not adjust objectives, thresholds or hyperparameters against final tests.

## Final endpoints and evidence

Primary fresh test: the same V3 structure, 264 globally distinct layouts,
216 reachable and48 disconnected; perfect/cyclic sizes9/17/33/65, rectangular
9/17. Endpoints are unrestricted; report distance>=8 separately.

Additional independent goal-pair tests: eight pairs per replicate (perfect/cyclic
9/17/33 plus mixed disconnected9/17), 48 normal responses total. Report ordinary
inference correctness separately from tick16 quality, specificity, source
fraction, leakage and score. Use frozen task/goal/source controls and compiled
BFS/A*/bit-wave common raster baselines; 30 warm randomized timing repetitions
on fixed size17/33 examples. Failed outputs receive no speed credit.

Save ancestry, every evaluated genotype/fitness, snapshots, mask outputs,
environment/source hashes and full population/RNG state. Audit saved rasters and
recompute goal metrics from packed snapshots. Diagnose nonlocal dependence at
frozen genomes without replacing them. Any new precursor is limited evidence;
correct shortest paths on unseen long mazes remain the primary research target.
