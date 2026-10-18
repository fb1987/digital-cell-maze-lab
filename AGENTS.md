# Instructions for Codex and other coding agents

## Mission

Build an experimental, low-cost **digital-cell maze solver** that can evolve compact local reaction rules. The core research claim to test is whether an evolvable, biological-style regulatory/local rule system can find **correct shortest paths on unseen mazes** with an advantageous combination of CPU/GPU compute, latency, and memory when compared with conventional implementations.

This is a scientific prototype, not a startup website, an AWS agent swarm, or a request for generic LLM-powered reasoning. Avoid remote API calls and expensive infrastructure.

## Critical user intent

- Each *organism* contains a spatial array (a "tissue" or reaction substrate), accepts one entire 2D maze as stimulus, and emits an output raster in which illuminated positions represent the path.
- The genome defines the shared or structured local update rules and expression/regulatory behaviour; local sites are not each fully autonomous LLM agents.
- A **population** of organisms with different genomes competes over many mazes. Organisms with stronger general performance are selected, mutated and reproduced over generations. Test both a fully random starting population and populations seeded with useful known rules.
- Explore sparse expression, negative feedback, concentration/decay, time, context accessibility, and perhaps multiple signalling scales *only if experiments justify their cost*. Do not force elaborate biological metaphors into the implementation.
- Eventually support much larger mazes and 3D grid mazes, but **do not start there**.
- User prioritizes **efficiency** over the spectacle of parallelism: the target is useful computational performance, not raw swarm size.
- **Random-origin discovery remains a central, ongoing research track.** The user
  explicitly does not want a small negative pilot to close this direction. Test
  whether greater heritable capacity, regulation, evolutionary time and pressure
  help. Preserve population/RNG checkpoints and useful diversity. Do not silently
  insert a known solver into a supposedly random-origin lineage. More complexity
  is a hypothesis, not a guarantee; record effective behaviour and real cost.

## Invariants

1. **Algorithm not answer**: no genome may store the correct route for a particular maze. Train and evaluate across separately seeded environments.
2. **Independent evaluation**: BFS may produce oracle paths for fitness/tests only. It must never operate inside candidate inference.
3. **Fair benchmarks**: compare completed valid path outputs; include input decoding, internal updates and final raster/path emission (or report separate timings transparently). Warm JITs with the same array mutability/dtype/signature as production. Benchmark multiple warm repetitions and report medians and ranges.
4. **Correctness precedes speed**: wrong or partial routes are not faster solutions. A legal path and shortest-path optimality are separate metrics. Disconnected grids must be handled explicitly.
5. **Budget bounded**: genome size, memory footprint, instruction count, update cycles and population size all have hard limits. No arbitrary generated code execution, no arbitrary system access, no recursive spawning.
6. **Reproducibility**: record RNG seeds, maze family, CPU/GPU, Python and dependency versions, training iteration, fitness and runtime; isolate holdout seeds.
7. **Avoid hidden advantages**: perfect mazes are trees where pruning finds the unique path; cyclic mazes invalidate the same method. Report both. Report data movement and total work alongside latency.
8. **Local first**: no cloud, LLM API, model downloads or paid providers without an explicit later user instruction.

## Immediate first task

Current checkpoint (October 18, 2026): V1–V5 are complete; **88 tests pass**.
Read `results/factor_curriculum.md` and `docs/FACTOR_STUDY_V5.md` first, then
`results/goal_conditioning.md` and `docs/GOAL_STUDY_V4.md`, then
`results/source_pressure.md`,
`docs/SIGNAL_PRESSURE_V3.md`, then the earlier `results/range_and_regulation.md`,
`docs/RANGE_STUDY_V2.md` and `results/first_evolution.md` for context.

V3 pairs current/causal objectives from six saved V2 random-origin populations,
96 organisms x 160 additional generations. Capacity and V2 inference stay fixed.
It ran 60.45 minutes of search including source-removal probes, 64.22 minutes with
fresh holdouts/timing, plus separately recorded post-freeze diagnostics. Mean
source-dependent transmission on 174 unseen long-route cases improves from
0.2480 frozen to 0.4185 current / 0.5090 causal with evolvable ranges; local arms
both reach 0.3071. Causal wins two of three held-out replicates, with higher
component leakage. Zeroing nonlocal reads reduces its score to 0.0809.

This is a signalling precursor, not a solver. Final multirange task archives
solve 2/216 reachable cases under either objective (initial frozen task: 4/216).
Local task archives solve 2/216 current / 0/216 causal. All final task arms solve
0/174 distance>=8 cases; all successful outputs are straight 1–2-edge routes. Compiled BFS/A* solve 216/216 and 48/48 no-path. No
competitive speedup or evolutionary path-accuracy advantage is established.

V1/V2 source/results remain untouched. V3 uses separate `signal_*` modules and
`results/source_pressure/`; logs are losslessly repacked with decoded hashes in
`storage.json`. Full next-population/RNG checkpoints and lineage records permit
deterministic continuation. Do not retune against any inspected final tests.

V4 preserves six V3 causal populations/RNG states, adds the saved signalling
archive as a fixed elite in both arms, and compares transmission/goal-output
pressure at unchanged capacity for 40 further generations (96 organisms,
two topologies x three replicates). The validation extension gate did not pass.
Search took 9.67 minutes; training plus recovered final outputs/timing took15.32
minutes, excluding the sampling failure/repair-development gap. The corner-DFS
size9 perfect final generator ran out of unused layouts before any final output
evaluation. Only final size9 perfect cases changed to Wilson spanning trees;
frozen archives, training and fitness are unchanged. This deviation is explicit
in `final_generation_repair.json`; `goal_recovery --run` reproduces it.

Goal-sensitive branched output emerged weakly but did not generalize better:
multirange goal-archive score0.0022 vs0.0071 transmission control on independent
goal pairs; local0.0033 vs0.0035. No final pair meets both-direction criteria.
Task archives solve local1/216 (same frozen control), multirange0/216 under either
objective, all0/174 at distance>=8, and0/42 separate paired reachable targets.
The one local success is adjacent. BFS/A*/bit-wave solve all reachable/no-path
cases. Audited7128 primary +1296 paired +192 ablated normal rasters,1152 final
goal metrics,47998 fitness decompositions; source/layout/provenance checks pass.
V1–V3 code/raw results are untouched. V4 checkpoints, full next populations/RNG
states, source snapshots and losslessly repacked logs remain available.

V5 tests that factorized curriculum: six V4 goal-pressure next populations/RNG
states, product/curriculum arms, local/evolvable ranges, 96 organisms x48 further
generations. Both arms preserve fixed signalling and V4 goal elites. Generations
0–15 reward Q+S,16–31 blend to2*sqrt(Q*S),32+ share the product objective. Task
archives use common ordinary-route fitness without probe reward. All size9
perfect splits use Wilson trees; all V1–V4 layouts are excluded. No extension
criterion passed. Training13.02 minutes; main run16.05; peak RSS162.8MiB.

Curriculum task archives solve local1/216 and multirange1/216 primary reachable
cases, versus product2/216 local /1/216 multirange; all0/177 distance>=8 and
0/197 turn-required primary cases. Curriculum paired routes0/42; local product
1/42. The latter is a10-edge,3-turn shortest path through two internal junctions.
Existing-ancestor analysis finds its first success at generation38 after three
gene-row edits; its parent fails. It grows west/south, fails the other goal and
all90/180/270-degree rotations, and has identical state under both goals at
every tick1–21. The common endpoint-aware runtime halt explains the successful
stopping time. Preserve this directional filament as a precursor, without
claiming goal-guided routing. The analysis is post-hoc on an inspected final
case and is not another holdout test or a tuned genome.

V5 goal-proxy scores multirange0.0068 curriculum /0.0089 product; local both0.0106.
Curriculum task archives handle12/48 primary disconnected cases, no false claims
on216 primary reachable cases, versus frozen0/48; disconnected endpoints have
a corner/partition bias. BFS/A*/bit-wave solve all reachable/no-path tasks.
Exploratory validation time courses show local goal archives have no source
state response to switched goals through tick64; multirange responses remain
limited (3/12 curriculum,2/12 product). No competitive speedup is established.
V1–V4 source/raw results remain unchanged. V5 next populations/RNG states, all
validation archives and source/lineage/diagnostic records are preserved.

Random-origin emergence remains central. Preserve signalling, goal-sensitive
and directional-growth variants from **both** V5 arms, selecting archives by
their recorded validation criterion, not inspected final-test performance.
A justified next controlled test holds capacity and product objective fixed
while comparing **symmetric source/goal stimulus initialization** with the
current convention. The source has initial channel0 activation plus a local
flag; the goal has only a flag. Add an initial goal pulse in channel1 in the
treatment, retaining public flags. This supplies stimulus, not a known solver.
Include frozen controls for each input convention, track communication to
decision sites and exact turning/detour paths, and reserve fresh layouts.
Do not insert a solver or retune against any inspected V1–V5 final tests.
Treat capacity, time and regulation as hypotheses rather than guarantees.
Original mission steps below are historical; do not repeat them as unfinished.

1. Inspect and run `cellular_maze_lab.py` and `tests/`.
2. Implement a **minimal bounded evolvable organism** with a small, typed genome and 2–4 internal per-site state channels. Define a compact grammar of deterministic local instructions. Consider a finite-state/Boolean rule table or small linear program; avoid implementing a giant neural network.
3. Add separate organism and evaluator modules, ideally isolating maze generation, reference solvers, execution, selection, and scoring. Preserve baseline behaviour.
4. Implement selection and mutation over a small population; evaluate candidates on rotating training mazes and fixed unseen holdouts.
5. Run a short **two-arm** experiment: purely random initial genomes versus genomes seeded with a functional wavefront-style rule. Use the same fitness and compute limits. Include a no-evolution ablation.
6. Produce `results/first_evolution.md` (accuracy, optimality, runtime, steps, memory, failure cases), machine-readable raw results, and simple visual samples of the best output.
7. Commit/leave runnable code, deterministic tests and instructions. Do not report success without an accurate holdout result.

## Sensible ordering

Phase 0: reproduce baseline -> Phase 1: simple genome runtime -> Phase 2: evolution and fitness -> Phase 3: stress-test larger and cyclic mazes -> Phase 4: multiscale or 3D only when justified.

Avoid spending the first iteration on a GUI, cloud orchestration, genetic text compression, or expensive GPU kernels. A good negative result is valuable. State what failed.

## What to report when done

Summarize: files changed; commands/tests run; accuracy on unseen mazes; baseline comparisons; representative failure; time/memory cost and scalability implications; and one well-justified next experiment.
