# Preregistered range/regulation continuation

The user explicitly wants random-origin discovery to remain a central track.
The first negative pilot is not treated as a verdict. Complexity, regulatory
capacity, evolutionary time and selection pressure are hypotheses to investigate.
This document records the next design before its final test set is generated.

V1 files and results remain unchanged and reproducible at Git `510a00c`.
V2 uses separate modules, schema and output directory.

## Substrate

- Eight uint16 channels, 64 local registers, 1–128 typed genes, 4 KiB binary
  genome ceiling; 64 bytes per site plus 64 KiB substrate/scratch ceiling.
- Every gene has an expression gate. Inactive gates skip primitive execution
  and spatial reads; dispatch, scanning and register reset still cost work.
- The 14 V1 primitives remain local. REMOTE and REMOTE_MIN add nonlocal sensing;
  XOR and neighbour count add generic Boolean/structural operations.
- Local topology interprets remote operations at radius 1. Fixed topology cycles
  remote radius 1/2/4/8 by tick. Evolvable topology uses a heritable per-gene radius.
  These are supplied communication possibilities, not spontaneously invented wiring.
- All reads observe previous-tick state. Nonlocal sensing can cross intervening
  walls, but wall sites hold zero. Movement/output validity remains four-neighbour.
- Stop on a source-local channel-7 regulatory request with both output endpoints
  lit, or four unchanged full-state ticks. Endpoint activation alone does not halt
  development. The shared evaluator independently judges every output.
- Four-phase quiescence handles the time-dependent fixed schedule. Budgets that
  interrupt a tick charge its work and discard its partial next state.

## Two cohorts

Controlled cohort: three topologies × random/seeded origins, 24 organisms,
30 generations and three independent seeds. Each has an initial frozen champion
and a training-sample-matched independent resampling control. Seeded genomes port
the same local wavefront rules and add one explicit stop instruction (30 genes).
No nonlocal algorithm or oracle route is inserted into the seed.

Rich random-origin cohort: local/evolvable topologies, 96 organisms,
120 generations and three independent seeds; random initial lengths 64–128.
No organism in this cohort derives from a known solver. Include frozen and
independent random-sampling controls. This supplies 14.4× the population-generation
slots of V1's 32×25 random evolution per topology/run, plus more regulatory capacity.
Changes are bundled, so a benefit cannot be attributed to capacity alone.

Rich search retains behavioural niches including code-length bins and conditional
activity, adds 10% fresh random immigrants and uses epsilon-lexicase parent
selection (epsilon .02 on partial scores, exact successful-path priority).
Ten percent of parent choices are uniform. Mutation makes 1–6 bounded edits and
can duplicate short blocks. Preserve up to one third of niches as elites.
There is no automatic cost tie-break among unfinished phenotypes.

Curriculum boundaries are absolute so continuation is reproducible: generations
0–39 use sizes 5/9; 40–79 use 9/17; 80+ use size 17. Each rotating batch has four
mazes, perfect and cyclic, with a disconnected example every fourth generation.
The controlled cohort always uses sizes 9/17. All cohorts use the same separate
validation set at sizes 9/17; no tiny training-case success substitutes for that.

Training caps: 256 ticks, 4,096 attempted reads/site and 32,768 dispatches/site.
Validation/test caps: 1,024 ticks, 8,192 reads/site and 131,072 dispatches/site.
Limits match across topologies and search methods. Resampling matches training
candidate slots/cases, not exact CPU time; actual work/validation attention is logged.

## Outcomes and data separation

Freeze all champions before generating a shared fresh final test: perfect/random
sizes 9/17/33/65, disconnected grids and rectangular grids. Exclude every input/
endpoint hash used in V1 and every new training/validation hash. Exclude V1's
deterministic snake/comb shapes rather than call them new unseen examples.

Report path validity and optimality, no-path accuracy, budget failures, long-route
performance (distance ≥8), actual range reads and active/dispatch counts. Zero
nonlocal observations at frozen genomes to test dependence, charging the same reads.
Compare the frozen local seed at V1 and V2 work caps to expose budget-only gains.
Benchmark common full-raster outputs against compiled BFS/A* and bit-wave,
30 warm randomized repetitions on selected 17/33 instances. Failed outputs receive
no successful-speed credit. Inspect all-open/source-only phenotypes explicitly.

Root seed: 2026101751. Final set is not generated during training or validation.
Smoke/unit-test roots are separate. Complete lineage, candidate fitness, genomes,
maze manifests, output masks and RNG/population checkpoints are retained. Raw
JSON-lines logs are gzip-compressed to limit disk use. Checkpoint resumption is
tested against uninterrupted evolution; continued research needs new final tests.

No cloud, APIs, paid services, arbitrary generated code or background schedule.
Additional time and complexity are being tested, not assumed sufficient.
