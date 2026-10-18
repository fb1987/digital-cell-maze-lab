# Source-dependent transmission pressure, V3

Preregistered October 18, 2026, before the study starts. V1/V2 source and raw
results remain unchanged. Root seed 2026101801; CPU only; no new dependencies.

## Controlled comparison

Fork the **next populations and RNG states** at V2 rich generation 120, separately
for local/evolvable topology and three replicates. Each fork has 96 random-origin
genomes. Re-evaluate every individual on fresh validation, discarding old fitness
and champions. Pair current/causal arms on identical starting genomes, RNG state,
rotating training environments and work limits. Fresh immigrants use the same
random grammar. No known solver enters these lineages.

Capacity, inference, mutation, diversity retention and epsilon lexicase are V2's:
eight uint16 channels, 64 registers, at most 128 genes, 4 KiB binary genome,
64 bytes/site +64 KiB interpreter ceiling. Both arms run and pay for identical
observers and validation nomination rules. Current-objective selection is V2's
(valid paths, shortest paths, no-path utility, partial progress, conditional cost).
Causal selection adds the signal score to partial progress only. All earlier
priorities remain intact. Case-wise lexicase uses the same sum for its partial
field. No automatic complexity/cost reward for unsuccessful outputs.

Training continues V2's late curriculum: four size-17 cases per generation,
perfect/cyclic pairs, disconnected last case every fourth generation. Limits:
256 ticks / 4096 attempted reads per site / 32768 dispatches per site. Validation
and final inference: 1024 / 8192 / 131072. New validation: 12 reachable size9/17
and two disconnected per replicate. All prior V1/V2 maze hashes excluded.

## Precursor measurement

Separate developmental probes run the unchanged primitive loop to a **fixed
16 ticks**, disabling output/quiescence stops but retaining work caps. Compare
ordinary source input with removed source input (both initial channel0 source
mark and source-flag register9 removed). Goal input remains. No distance or
oracle enters either runtime. Actual inference always uses unmodified V2 stops.

At tick16, a site carries source-dependent hidden activation if any of channels
0,1,3,4,5,6 is positive and differs from the ablated probe. Channels2 (output) and7
(stop) earn no reward. For each existing geodesic band distance>=2, >=4 and >=8,
compute the affected fraction of source-reachable sites. Signal score is the
mean of these fractions minus affected fraction in other open components,
clamped to [0,1]. Unaligned/budget-interrupted probes score zero. Source-only
marks and source-independent constants score zero. This rewards transmission,
not a complete route; a flood can score highly and still fail maze solving.

Observer arrays are evaluation overhead, separately reported. While the second
probe runs the first retains 16 bytes/site. Pair bound: 80 bytes/site+64 KiB;
this does not expand the organism's working state. Count both probes' attempted
reads and dispatches in training work. Final inference timings exclude evaluator
probes and include input decoding plus full output raster emission.

## Archives, attention and extension rule

Both arms keep a task champion under their own selection objective and a
**diagnostic transmission archive** ranked by mean signal on reachable validation
cases with endpoint distance>=8, then valid and optimal route counts. Record
both frozen initial champions. Neither transmission archive enters reproduction
unless it is independently retained/selected by the ordinary search. Nominate
the training leader and transmission leader each generation, plus V2's three
niche candidates every tenth generation, equally in both arms.

First screen: **32 additional generations**, 12 conditions (two pressures x two
topologies x three replicates), 147456 population-maze evaluations before
validation. Extend all paired arms to **160 additional generations** if at least
one topology has two of three replicates whose transmission archive improves
>=0.10 over its initial archive and >=0.05 over the paired current objective,
with positive distance>=8 signal in both perfect and cyclic validation families.
Alternatively extend if causal task champions have at least two additional valid
validation routes in aggregate per topology relative to both frozen and current
champions. This second trigger includes all route lengths and is recorded as
such. Neither trigger establishes general maze solving.

Hard search wall ceiling: 85 minutes, checked at generation boundaries; checkpoint
all populations and RNG state. The initial profile estimates 10–15 minutes for
the screen; extension is conditional, as authorized by the user. Record actual
per-arm generations if the wall ceiling binds. No testing against final mazes
until all selected genomes are frozen. No changes to objectives/hyperparameters
based on final results.

## Final measurements

Generate fresh shared tests only after freeze: perfect/cyclic sizes9/17/33/65,
rectangular9/17, disconnected9/17/33/65, eight samples per reachable size/family
plus the V2 test structure (88 per replicate). Exclude every earlier experiment,
training and validation hash. Assess task, transmission and frozen archives;
report validity, optimality, distance>=8 performance, no-path correctness,
work/memory, signal coverage/leakage, and failure examples. Compiled BFS/A* and
bit-wave emit the same raster; use 30 warm randomized timing repetitions.

Interpret a positive precursor outcome as evidence about selection pressure;
exact complete shortest routes remain the primary research endpoint. Preserve
full random ancestry, logs, genome and RNG/population checkpoints for continuation.
