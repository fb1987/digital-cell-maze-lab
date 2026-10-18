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

Current checkpoint (October 18, 2026): V1–V8 and V8A are complete; **106 tests pass**.
Read `results/junction_choice.md`, `docs/JUNCTION_STUDY_V8.md`,
`results/junction_confirmation.md`, `docs/JUNCTION_CONFIRMATION_V8A.md` first,
then `results/balanced_goal.md` and `docs/BALANCE_STUDY_V7.md` first, then
`results/goal_beacon.md` and `docs/BEACON_STUDY_V6.md`, then
`results/factor_curriculum.md` and `docs/FACTOR_STUDY_V5.md`, then
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

V6 completes that symmetric-stimulus test. Twelve conditions (local/evolved ×
flag/pulse ×3),96 organisms ×48 generations, fork the V5 product next population
and RNG, preserving validation-selected task/goal/transmission archives from
**both** V5 arms plus ancestral protected elites. Both use fixed V5 product
pressure. Pulse adds channel1=1 at the goal; source channel0 and public flags
are unchanged. Flag-mode normal/probe output/state/work and product-fitness
parity tests pass. Source-removal probes retain the goal pulse and goal flag.

On independent paired layouts, multirange goal archives improve G to0.0390
versus0.0135 frozen Pulse and0.0137 evolved Flag. Goal-switch source-state
responses at tick16:8/18 regular pairs Pulse,5/18 frozen Pulse,1/18 Flag.
Removing the pulse from those evolved Pulse genomes reduces G to0; zeroing
nonlocal reads also reduces G to0. These are goal-dependent output precursors,
not correct routes. Both-direction qualification remains0/18 final regular
pairs. Local goal scores both0.0052 and no source response through tick64.

Primary task archives: local2/216 each (same frozen),multirange0/216 each;
all0/178 distance>=8 and0/133 mandatory-detour cases. One inherited local
seven-edge path has one turn on a new maze; the other success is two straight
edges. Both occur before V6 training. All candidate arms solve0/42 paired
reachable targets, and all768 tick16 output rasters fail legality even with
assumed emission. Compiled BFS/A*/wavefront solve all216 primary and42 paired
reachable targets,48 primary and6 paired no-path cases. No speed advantage.
Local task no-path16/48 and multirange Flag12/48 match their frozen controls;
Pulse multirange0/48. No false primary reachable no-path claims in task arms.

The extension gate failed. Search13.11min;main16.31min;peak180.1MiB RSS onM4.
Audited5016 primary +912 paired +768 cross-input +192 ablated normal outputs,
58100 training fitness decompositions,254832 source arithmetic records,
49 training/validation valid claims,48 selected replays; all checks passed.
There are35907 new individuals and full population/RNG continuations under
`results/goal_beacon/checkpoints/beacon_{local|evolved}_{flag|pulse}_{0|1|2}.json`.
Prior V1–V5 source/raw results remain unchanged. New `beacon_*` modules are
separate; do not patch old runtimes or silently use the wrong input convention.
V6 config `pressure` names the input mode (`flag`/`pulse`); the objective is fixed
product pressure in both.

One recorded protocol deviation: the construction-only test used the study
seed before training, so freeze-before-generation was not literal. It evaluated
no candidate genomes or outputs; actual final inference began after all models
froze. See `protocol_notes.json`. Do not claim no prefreeze layouts were ever
constructed. Use a separate seed for future construction/preflight tests.

Random-origin emergence remains central. Preserve signalling, goal-sensitive,
and directional-growth variants from both V6 arms, by recorded validation
criteria. Also preserve `balanced_validation_archive.json`: a post-hoc archive
of existing validation-evaluated genotypes ranked by mean per-pair min(G_A,G_B),
then both-goal rate,Q,mean G. It did not alter primary archives or add final
assays; some identities overlap original selections. Its source/code hashes
and full genotypes are saved. Mean-G selection discarded some more balanced
variants (e.g. Pulse replicate1 has validation both=0.5 in the supplemental
archive but0 in the final mean-G archive). Do not present that as unseen accuracy.

V7 completes that balanced-pressure comparison. Twelve conditions,
local/evolved ×mean/balanced ×3,96 organisms ×48 additional generations. Both
use the unchanged V6 pulse runtime and8-channel/128-gene limits. Per regular
pair, Mean rewards2(G_A+G_B); Balanced rewards(G_A+G_B)+2min(G_A,G_B), assigning
case i the bonusG_i+min. Both maxima4. Mixed unreachable pairs retain2G_i in
both. Normal correctness/no-path priority, source reward and costs stay fixed.

Base next populations/RNG are V6 Pulse. Both V6 arms' validation task/goal/source
archives, protected ancestors and supplemental balanced variants are injected
by recorded criteria and protected equally. Validation uses Mean in both arms;
common balanced archives rank B=mean regular-pair minG,then both,Q,meanG,
validity/optimality. Both nominate balanced training leaders. Task archives use
normal fitness. Final selections are task/balanced plus their frozen controls;
mean-goal/source/Q/S archives remain saved. Absolute V6/V7 archive scores are
not a pressure-only comparison because the common archival policy changed.

On independent paired tests, multirange Balanced B0.0310 vsMean0.0048 vsfrozen
0.0215; individual G0.0509 /0.0386 /0.0352. Both-direction qualification2/18
versus0/18 Mean and1/18 frozen. Gain concentrates in replicate1;replicate0
retains B,replicate2 is slightly below frozen. Local Mean B0.0127 versusBalanced
0.0031, frozen0.0031. These are intermediate measures, not completed routes.
Removing the goal pulse reduces multirange Balanced B to0 (G remains0.0060);
zeroing nonlocal reads reduces B to0,source score0.4911→0.0831. Do not claim
all mean-G or source signals vanish. Mean's nonlocal-ablated B remains0.0038.

Primary task accuracy:local4/216 under both (same frozen);multirange Balanced
1/216 (same frozen),Mean2/216 (frozen1/216). All0/165 distance>=8 and0/42 paired
reachable targets. Candidate task successes are1–5 edges; an inherited local
five-edge route has two turns. Do not claim a new general route algorithm from
the extra short straight Mean success. BFS/A*/wavefront solve all216 primary,
42 paired reachable targets,48 primary and6 paired no-path cases. No speedup.

Diagnostic added during training before final inspection: on9 perfect-tree
pairs, locate the last shared oracle-prefix vertex and distinct next neighbor
for each goal. A correct local choice requires source-connected output at the
junction and desired neighbor, with the other branch off. Both-choice success
is0/9 in every selected archive. Multirange Balanced reaches the junction under
both goals and illuminates all three positions in6/9;source-to-junction distance
can exceed16 in another case. This reuses saved tick16 rasters, without new
inference, and is not another final accuracy measure. Source state changes at
tick16:Mean11/18,Balanced4/18,frozen4/18. Communication at source is distinct
from useful goal-dependent output. Full records:`junction_diagnostics.json`.

A matched-parent mutation diagnostic (also specified during training) observes
18628 newly born children whose parent is evaluated on the same rotating batch.
18423 change genotype;8585 of those (46.6%) match the saved normal/probe rasters,
status/steps and scalar fitness traits. Hidden trajectories may still differ.
1484 have higher,7196 lower training fitness (cost tie-break excluded). This is
a conditional subset, not an unbiased neutrality estimate. Preserve neutral
variation; gene length is not effective complexity. Task genomes126–128 genes,
conservative output/stop slices21–57; full-state quiescence may depend on others.

Gate failed;search13.18min,main16.18min,peak192.2MiB onM4. Audited5016 primary,
912 paired,768 pulse-removed and192 range-ablated normal outputs;58240 fitness
records,256512 source arithmetic records,99 valid training claims,48 replays,
12 archive maxima and all provenance/layout checks passed. There are34822 new
individuals and complete next populations/RNG in
`results/balanced_goal/checkpoints/balance_{local|evolved}_{mean|balanced}_{0|1|2}.json`.
Separate `balance_*` modules reuse unchanged V6 inference. Source hashes,
lossless decoded/stored log hashes and full prior populations are preserved.
Construction seed1074 differs from study2026101805; final layouts were generated
only after model freeze. V1–V6 code/raw results remain unchanged.

V7's proposed junction-pressure test is now complete as V8. At unchanged V6
pulse input/runtime, eight channels and128 genes, local/evolved ×Balanced/
Junction ×3 ran96 organisms for48 generations. Common decision-rich pairs
require a shared shortest prefix at source distance2..8 and goals≥4 beyond,
with disjoint sets of all valid shortest exits. Half of pair indices require
an initially misleading Manhattan bearing. Both arms share this sampling;
V8 versus V7 is not a pressure-only comparison. J=.25 causal connected prefix
+.75 branch choice; Junction uses J_i+minJ in place of Balanced G_i+minG.
All shortest-next-step ties are accepted; wrong exits must be suppressed for
strict qualification. Labels stay in fitness, never candidate inference.
Study seed2026101806, independent construction-test seed1084;6896 prior whole
layouts excluded. Models froze before264 ordinary and24 paired final layouts.

V8 primary task accuracy: multirange Junction3/216 versus Balanced0/216 and
frozen1/216; local Junction1/216 versus Balanced0/216 and frozen1/216. All task
arms0/174 at distance≥8,0/42 paired and0/144 mandatory detours. Multirange
Junction's3 successes span1–3 edges, two with one turn. BFS/A*/wave all216/216,
42/42 and all48/6 unreachable inputs. Correct no-path varies0..32/48, with
no false no-path claims on reachable primary cases. No competitive speedup.

Primary selected junction archives make0/18 strict-both choices on fresh
regular pairs. Their multirange J scores: treatment.2345, Balanced.1877,
frozen.2433, dominated by prefix credit. Goal switch changes junction state
at tick16 in6/18 treatment,9/18 Balanced and7/18 frozen, distinct from useful
exit choice. Only1/18 pairs has BOTH goals outside every local decision
site's16-edge influence cone; this cannot explain the overall failure.

A validation-only strict-choice archive, planned during training before final
inspection, finds two qualifying multirange variants. Both are preserved in
`results/junction_choice/strict_validation_archive.json` along with complete
ancestry replay at `choice_ancestry.json.gz`. They are NOT selected by final
performance or used to alter V8 breeding/gates/primary selections.
Balanced replicate2: birth4 id `junction/evolved/balanced/2/i284`, after three
ancestral mutation steps, makes proper paired choices on a cyclic17×17
validation case with goal distances17/8 and source-to-junction2. Junction
replicate1: birth7 id `junction/evolved/junction/1/i472`, from initial i3,
qualifies on a17×17 tree with goal distances23/10 and source-to-junction4.
Both lose the choice under either goal-pulse removal or nonlocal ablation;
neither completes either validation route. Gene rows may shift during
insertion/deletion; do not interpret83 changed rows in the first lineage as
83 independent mutations.

V8A separately preregistered a tiny confirmation AFTER V8 results/ancestry,
BEFORE its new layouts. Seed2026101807,12 new shared regular layouts/24 inputs,
all7490 V1–V8 layouts excluded. Five unique root/parent/variant genotypes from
the two validation-selected lineages all score0/12 strict-both and0/24 valid/
shortest outputs; BFS24/24. No training, tuning or reselection follows.
The Junction variant differs from its parent by swapping rows27/60 (neighbor
count and nonlocal minimum) and redirecting row66's destination63→43.
Counterfactual groups on the original validation pair: parent J=.0833;
swap alone.0833; register change alone.0833; combined child.8333 and strict
both true. This supports a context-specific cooperative interaction between
two change groups, NOT a general solver or necessary individual-gene proof.
Full raw data/provenance are in `results/junction_confirmation/`.

The mean-J archive can discard a useful choice on one pair in favor of broad
prefix growth across all pairs; the strict validation supplement rescued the
second primitive. Training recorded27 strict-both pair responses under
multirange Balanced and24 under Junction, zero local (repeated genomes/cases,
not independent discoveries). A matched-parent diagnostic finds9158/18610
changed-genotype children (49.2%) match its saved behavioral fingerprint;
work/active counters and hidden trajectories can differ. Preserve neutral
variation and these cooperating primitives. Task genomes114–128 genes,
conservative output/stop slices10–61; length is not effective complexity.

Gate failed. Search13.47min, main16.54min, peak main208.2MiB; diagnostics20.92s,
compression9.82s, audit18.04s, V8A4.07s plus.17s verification. Audited6908 main
final/diagnostic normal outputs,58686 fitness records,263612 junction masks,
29 valid training claims,48 selected replays,12 junction and12 balanced archive
maxima. V8A verifies124 candidate outputs/masks plus24 BFS outputs. Main
charged427687305596 dispatch-plus-read units.33334 new individuals; all source,
layout and lineage checks pass. Full next populations/RNG checkpoints are
`results/junction_choice/checkpoints/junction_{local|evolved}_{balanced|junction}_{0|1|2}.json`.
V1–V7 code/raw results remain immutable. V8A raw results also remain immutable.

A justified next experiment preserves BOTH V8 strict-choice variants and all
useful prior task/source/goal/neutral lineages in common initial cohorts, then
compares strict paired-choice-first pressure against current prefix-weighted
pressure at unchanged capacity/input/caps. Keep complete-route correctness
first. Explicitly preserve strict-choice validation archives in both arms and
record their independence from final testing. Require transfer across rotating
fork contexts and new holdouts before hour-scale extension. Capacity, regulation,
modular cooperation and longer evolution remain live hypotheses. Do not insert
known solver rules into random-origin lineages. Exclude ALL V1–V8 and V8A layouts
(including BOTH new manifests;7502 unique layouts total) from future work.
Do not retune against already inspected tests. Use new separate version modules.
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
