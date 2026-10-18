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

Current checkpoint (October 18, 2026): the user-authorized calibration-first
plan is complete. Read `results/foundation_study.md` and
`docs/FOUNDATION_GOAL_PROGRESS.md` first. V12A fails its repair gate; V12B
passes after a validation-selected single-edit policy and balanced orientations.
Known/repaired solver controls remain separate from random-origin lineages.

V12C completes 442 matched generations in 75.15 minutes across 24 conditions
of 96 organisms: native/fresh × local/evolved × evolution/resampling × 3 reps,
plus initial frozen controls. Fresh local primary selections pass the elementary
screen in 2/3 replicates: 86/864 non-adjacent shortest outputs and 9/432 complete
pairs, versus zero for resampling/frozen. These pairs span five independent base
layouts; no fresh-local base works in all eight poses. Earlier selections frozen
before confirmation achieve 0/8/36/86 non-adjacent outputs at generations
48/128/256/442. This secondary time course is correlated evidence that more
stable search helped. Fresh-local primary lineages descend from random
immigrants, never known solvers.

General solving remains unestablished: best ordinary cohort 7/216, every cohort
0/181 distance≥8 and 0/48 no-path; BFS/A*/bit-wavefront 216/216 and 48/48.
No net multirange advantage or speedup: eligible tiny-task outputs have a median
48.95× runtime ratio to BFS. Search: 13.33M responses, 436.0 MiB peak RSS.
Audit passes 397,800 mutations, 1,026,048 fitness records, 5,972,328 search rasters
and all final outputs. 137 current tests are covered by 136 full-suite passes
plus the later time-course test. Preserve all next populations/RNG and raw data.

All **52,424 whole layouts** through V12C must be excluded in a new study,
including unqueried ordinary symmetries and software fixtures. Do not retune
against inspected final cases. The proposed next step is one unchanged
75-minute continuation with current frozen controls and a stronger paired-skill,
retention and orientation criterion. It is not implemented or launched. Use a
new protocol/module/output directory; do not alter immutable V12 source/budgets
or repeat completed work as though it were unfinished.

Historical checkpoint before V12: V1–V11,V8A,V10A are complete.
123 current tests are covered (122 full-suite passes, 4 focused passes after
the final study guard edit, plus 1 separately added exact 256-gene bound test).
Read `results/capacity_growth.md`, `docs/GROWTH_STUDY_V11.md`,
`docs/GROWTH_DIAGNOSTICS_V11.md` and the next-study proposal
`results/capacity_growth/next_experiment.md` first.
Earlier protocols/results below are historical; do not repeat completed work.

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

V9 completes that strict-choice-first comparison. Local/evolved ×Prefix/Choice
×3,96 organisms ×48 generations, fork matching V8 Junction populations/RNG.
Preserve task/J/B/G/source, protected variants, strict-validation selections
and qualifying ancestors from both native V8 arms. No cross-replicate/topology
transfer. Protected counts13/15/15 local,23/19/25 evolved. Same V6 pulse VM,
8 channels,128 genes,unchanged V8 J shaping/caps. Global rank(V,O,N,0,S,W)
versus(V,O,N,K,S,W); K counts strict-both pairs. Normal correctness first.
Case lexicase inserts the pair bit before smooth shaping; zero control
preserves old RNG. Common validation is Prefix; choice archive ranks
(strict-both,J,B,G,valid,optimal). Both arms save all named archives.

All six matched pressure pairs have IDENTICAL ordered genotype populations at
every generation and identical final RNG states. The priority was implemented
and verified, not silently zeroed: each multirange pressure records19 strict-
both training responses across4 batches (rep0:g16/g22,rep1:g2,rep2:g14); local
none.10 positive unprotected-genotype opportunities across3 batches retain5
copies and produce40 mutated offspring under either pressure. All positive
parents (protected included) produce83 offspring per pressure. All four active
pools have the same global best sets;512 post-hoc matched-seed lexicase draws
also choose identical parent IDs/genotypes. Priority is redundant for observed
selection outcomes, NOT proven redundant for every possible population.
Choice primitives already reproduce; transfer is the observed bottleneck.
Full records:`reproductive_priority.json`,`priority_trajectories.json`,
`selection_counterfactual.json` (analysis seeds1139000..1139127,no inference).

Primary task accuracy local1/216,multirange0/216 under both, matching frozen.
All selected models0/18 strict-both final pairs and0/42 paired full routes.
Task distance≥8:local1/171,multirange0/171. Local success9 edges,1 turn, already
in frozen control. Task no-path16/48,no false primary reachable claims. BFS/
A*/wave216/216,42/42,all48/6 no-path. No speed advantage. Do not compare absolute
accuracy across versions as a pressure effect: common archive/seed changes.

Post-hoc inspected-final path assay (NOT another holdout): frozen and current
local task have identical genotype. Original9-edge goal emits tick19; midpoint
5-edge goal emits tick11. Forced probes show identical output concentrations
and source states under both goals at EVERY tick1–19; both halts satisfy the
common source-stop/endpoint conditions. Endpoint-aware halting chooses length
from the same measured growth trajectory here; do not call it goal-guided
routing. `inherited_path_diagnostic.json`,independent replay also passes.
Assay.080s,2 normals/38 probes,2540210 work; replay separately recorded.

Both pressures find the SAME evolved-rep2 validation-only lineage: initial i40
fails the fork; birth3 i218 succeeds; birth5 i324 retained. Different pressure
prefixes are aliases of the same genotype trajectory, not independent finds.
Its9×9 cyclic qualifying pair has source-to-junction4; it needs the goal pulse,
but nonlocal ablation retains J=1/strict-both on THIS case. Unlike the two V8
examples,long reads are not necessary here; this does not imply forcing every
range1 or general local solving. Fresh final paired tests remain0/18. Preserve
this new variant with both V8 primitives, directional growth and neutral drift.
A saved-raster entry diagnostic specified during training removes desired
exits and checks incoming source reachability/shortest-prefix length. All19
strict-both training responses per multirange pressure pass under both goals.
It does not change registered K/primary results. `entry_diagnostics.json`.

V9 seed2026101808,construction seed1094,7502 prior layouts excluded. Freeze
BEFORE264 ordinary/24 paired final layouts. SHA
74b6135000533707aa7fdc367152365e227047044ac92b043648d77e071c5cfb.
Gate failed;search13.90min,main17.09min,main peak200.4MiB. Diagnostics20.30s,
compression10.15s,audit19.51s,post-hoc parent replay2.13s.58998 fitness records,
59046 priority records,267356 junction masks,100 valid training claims,48
selected normal replays,12 each task/choice/J/B archive maxima all pass.
6908 main final/diagnostic normals audited,plus2 path normals/replay. Training
265608 normals+531216 probes,436915640448 dispatch-plus-read units.32258 new
IDs,full next populations/RNG in
`results/choice_priority/checkpoints/choice_{local|evolved}_{prefix|choice}_{0|1|2}.json`.
All70 frozen sources and lineage/layout/storage checks pass. Conditional
changed-genotype neutrality8784/18048 (48.7%) by saved behavioral fingerprint;
work/expression/hidden trajectories can differ. Gene length is not effective
complexity. Prior V1–V8/V8A source/raw data remain immutable.

The next justified test addresses transfer rather than increasing priority
again: a near-to-far GOAL-TO-FORK distance curriculum versus the current minimum-
distance distribution, same capacity/objective/common protected cohorts. Start
with attainable but genuinely source-dependent paired decisions, increase
cue distance on a preregistered schedule. Hold validation/final at the harder
distances; preserve all known variants and neutral diversity. Use new layouts;
report curriculum training AND independent transfer. Capacity, regulation and
longer evolution remain central live hypotheses. No known wavefront/solver
rules enter random-origin lineages. Larger precursor scores alone do not
justify hour-scale extension. Exclude ALL V1–V9/V8A layouts (including V9
manifest):8096 unique layouts. Do not retune against inspected tests; use new
separate version modules.

V10 completed the matched near-to-far cue comparison. New separate distance_*
modules preserve all V1–V9 source/raw data.12 conditions:local/evolved ×Fixed/
Curriculum ×3,96 organisms ×48 generations. Both fork native V9 Choice next
populations/RNG, preserve both V9 arms' task/choice/J/B/G/source/protected,
supplemental strict choices and qualifying ancestors. No cross-topology/replicate
transfer or known-solver insertion. Protected counts15/18/15 local,25/22/29
evolved. Same8 channels,128 genes,V6 pulse VM,Choice-first ranking in both arms,
including common hard validation. All initial DNA/protected cohorts/RNG match.

Fixed uses original hard goals. Curriculum shortens SAME layout/source/fork
branch goals to1/2 edges for generations0–15,2/3 for16–31,far at32 onward.
Mixed pairs unchanged. Short labels only in train_near splits; validation/final
retain original≥4 remaining/≥8 source distance. Near prefix/fork/exits verified
identical,all allowed exits subsets. Shortening also removes deceptive bearing
in both early phases; report that distribution effect. No automatic extension:
common hard-validation gate failed. Native variants and neutral drift remain.

Primary task archives/frozen controls ALL0/216 reachable,0/179 distance≥8,
0/42 paired. Every final selected model0/18 strict-both pairs. Secondary evolved
Curriculum choice archive1/216,adjacent endpoints only (2pixels,4ticks,
rep1 i415,birth6). No other selected success. Task no-path33/48 local,16/48
evolved;no false reachable claims. BFS/A*/wave216/216,42/42,all48/6 no-path.
No speed advantage. These are selection-specific scores,not absence of every
older protected capability; do not compare versions as a pressure-only effect.

Training valid normals local122 Curriculum vs49 Fixed;evolved52 vs4. No regular
training pair has BOTH ordinary outputs valid/shortest. Strict forced16-probe
training responses:local0;evolved Curriculum1,Fixed15 (repeated opportunities).
Phase leaders15/31/47 have0 final choices/routes; all boundary batches contain
one regular tree pair+one mixed disconnected pair,so snapshots miss cyclic
opportunities. Reused-training frozen/leader/final replays are NOT holdouts;
leader replays equal original full training records exactly.

NEW TRAINING-ONLY PRIMITIVE: evolved Curriculum rep2,i1472,birth30,first observed
generation30 on train_near2_goal/r2/p60/s15/perfect/17x17/a|b. Fork vertex90,
source-prefix[156,139,122,105,88,89,90],incoming89,exits91/73,allowedA73,B91,
goals2/3 beyond. Ancestryi94(birth0)→i1213(25)→i1402(29)→i1472(30).
Parent J=.25/strictfalse,child J=1/strictboth; neither ordinary route correct.
Child changes row25 REMOTE dst46→59 (radius2,ch6) androw117 operand3→36.
Counterfactual row25 alone suffices,row117 alone fails; NOT two-edit cooperation.
Goal-pulse removal or nonlocal-read removal each destroys choice,J=.2 on this
training case. Source-removal rasters independently verify causality/entry.
It is unprotected,retained once,produces18 mutants,and exact genotype is absent
from final population. Explicit full genotype/ancestry in
results/distance_curriculum/training_choice_diagnostic.json; preserve it,parent,
root with all earlier native variants in BOTH matching next-test cohorts.
This diagnostic is post-hoc training-selected after main final evaluation;
never evaluated this newly selected candidate on V10's inspected final set.
Original1.166s,12normals/24probes,14988575work; independent replay.128s plus
9447514work for edit reversions. Initial tuple/list assertion attempt extra
ancestry cost recorded separately; no training/raw result changed.

V10A froze child,parent,root BEFORE12 NEW layouts. Seed2026101810,independent
construction/replay preflight1105 (accuracy not inspected),excluded8690 prior
layouts.9/17 ×tree/random ×3;each same source/fork hasnear2/3 andfar≥4 paired
goals. All three genomes0/12 strictboth and0/24 normalroutes at EACH distance;
BFS48/48. ChildnearJ.25,far.2458333.12layouts are independent,not24pairs.
No training/reselection or primary V10 change. Main.877s,144normals/288probes,
143965340work;independent.359s verifies192normals/144Jrasters and replays all
144normals/288probes,equalwork. Model SHA
34329d632b2b551a68ae2b74cd89b409ed4199acc6d132007a95ae7b1d277474.
Preregister/freeze commit833dfe5. Raw:results/distance_confirmation/.
This bounded negative preserves random-origin,regulation,capacity/time hypotheses.

V10 seed2026101809,preflight1104,8096 prior layouts excluded. Freeze before
264 ordinary/24 paired final layouts. Model SHA
c6df4e29f961fcb0e62732c12a2fe34e245cb7710aae8409c35b7287c8ef8733;
prereg4aa60d6. Search829.323s(13.82min),main1017.161s(16.95min),peak203.5MiB.
Diagnostics30.114s(includes1440 phase normals);compression10.400s;audit20.360s.
All79 frozen sources,59004fitness,59232priorityrecords,268848Jrasters,
227validtrainclaims,48selectedreplays,12eachtask/choice/J/Bmaxima pass.
8328 main/diagnostic normals independently assessed,plus post-hoc training
assay/replays/reversions and V10A. Training265680normal+531360probes,
432900048953dispatch+attempted-read units;31417newIDs (not independent finds).
Neutrality8434/18094 changed-DNA matched-parent children (46.6%) by observable
fingerprint; hidden trajectories/work can vary. Full next population/RNG:
results/distance_curriculum/checkpoints/distance_{local|evolved}_{fixed|curriculum}_{0|1|2}.json.
All prior source/raw results stay immutable.8702 unique layouts throughV10A.

HISTORICAL PROPOSAL, COMPLETED AS V11: greater heritable program capacity with copy-and-diverge
structural growth,128vs256-gene ceilings,common block-duplication operator and
Fixed hard-pair objective. Keep eight channels/opcodes/range semantics unchanged;
prove≤128-gene old-program inference equivalence before training. Identical native
starting populations/RNG/protection,including i1472/parent/root in matching
evolved rep2 under BOTH capacities. No cross-topology/rep transfer,no known solver.
Common bounded instruction/read/tick caps; report additional dispatches and any
fewer completed ticks,actual growth/expression/dependency/behavior rather than
claiming effective complexity from ceiling/length. New separate modules/layouts,
exclude ALL8702 throughV10A. No hour extension from precursor scores alone.
Do not keep only optimizing easy-goal curricula at unchanged capacity.

V11 completed the capacity comparison using separate growth* modules. Twelve
conditions: local/evolved × cap128/cap256 × 3, 96 organisms × 48 generations.
Both fork native V10 Fixed populations/RNG and preserve the common native
Fixed/Curriculum archives, strict supplements and all four training-primitive
ancestry nodes in evolved replicate 2. No solver injection or cross-replicate
transfer. Eight channels, hard pair distribution, V9 Choice objective, opcodes,
mutation modes, immigrant lengths and instruction/read/tick limits stay fixed.
V2 already supported block duplication; only the length ceiling changes its
eligibility. Old inference/probe kernels remain unchanged.

V3 serialized genomes support 256 genes; use growth.Genome/Individual when
loading these checkpoints. Legacy parsers reject programs above 128. Preflight
parity verifies 1,052 native program/topology pairs, 7,712 normals, 10,016 probes
and 50 full fitness calls. Exact 256-gene bounds/memory/read accounting pass.

Growth is real: evaluated programs reach 228 genes, the prepared g48 next
population contains 240, and final evaluated expanded populations have 39–66
above128 members. All selected task genomes remain ≤128; one selected local
choice genome has 138. Do not infer every grown genome was tested on holdouts.
Both capacities have primary task accuracy local 0/216 and evolved 1/216,
matching frozen controls. Secondary local choice 4/216 versus frozen 3/216
under both caps. ALL selected successes are adjacent one-edge routes; all
selected models solve 0/180 long cases and 0/42 paired routes, 0/18 strict-both.
BFS/A*/wavefront solve all reachable and no-path cases. Gate false; no extension.
No competitive speedup or capacity-related accuracy advantage is established.

Post-hoc frozen-model region assay (growth_context) finds goal-dependent hidden
states at fork exits in evolved replicate 2: cap128 choice 4/18, cap256 3/18,
frozen 3/18; mostly absent at the vertex. This reuses final pairs and is not a
new accuracy test. Source × goal interaction can be positive with no goal
contrast under source-present inference; do not treat it as correct routing.
312 full-state/mask/counter probe replays and 288 native comparisons pass.

V11 seed 2026101811, preflight 1114, equivalence 1113. Excludes all 8,702 prior
layouts; total unique layouts through V11 is 9,296. Main 1020.317s (17.01min),
search 849.112s (14.15min), peak 213.2MiB. Diagnostics 30.233s, compression
10.26s, initial audit 23.362s and final audit 23.10s (temporal-label correction
only); hidden-context assay .671s and replay .690s, all separately charged.
91 frozen sources, 59,127 fitness records, 23,655 child mutation traces,
270,324 J rasters, 41 valid training claims, 48 selected normal replays,
1,440 phase outputs and archive maxima pass independent verification.
Training: 267,156 normal responses, 534,312 probes, 444,031,737,693 work units.
Genotype changes preserve recorded behavior in 8,396/17,176 coeval opportunities;
this fingerprint does not identify full hidden trajectories or effective complexity.
All earlier source/raw results stay immutable. Full native next populations/RNG:
results/capacity_growth/checkpoints/growth_{local|evolved}_{cap128|cap256}_{0|1|2}.json.

HISTORICAL NEXT-STUDY PROPOSAL, DEFERRED BY THE AUDIT BELOW: retain cap256 capacity and all native random-origin
populations/primitives; compare unchanged pressure against an added bounded
hidden goal-context discrimination term at fork exits. Preregister the exact
paired directional contrast/normalization and prove it on independent fixtures.
Keep correct complete routes and strict paired choice above shaping; raw
hidden-state differences or source × goal interactions alone are insufficient.
Do not insert a known solver or reset the grown populations. Match cohorts,
RNG, caps, sampling and operators; use fresh layouts excluding ALL 9,296.
48-generation screen, extension only for replicated hard-validation transfer.
The proposal is not an executed/preregistered V12. Random-origin discovery,
capacity/regulation and evolutionary time remain open hypotheses.

CURRENT HANDOFF — RESEARCH AUDIT, October 18, 2026:
The user requested a deep reassessment before more experiments. Read
results/research_audit_2026_10_18.md and its analysis/verification packets.
No new evolution, candidate inference or maze generation was run for the audit.
Earlier raw results/source remain unchanged. The hidden-context V12 proposal
above is deferred; it is not the automatically authorized next experiment.

Judgment: local representation works, evolved causal signalling and specific
fork computations exist, but general random-origin solving and competitive
speed remain unestablished. Continue research with searchability/timing
calibration before another shaping term. Keep known working/damaged program
controls strictly separate from all random-origin lineages. Preserve native
populations and useful variants; a fresh modern-convention random cohort, if
tested, must be separately labeled. Exact complete routes remain primary.

Retrospective facts: eleven main runs total208.43min, excluding separate
tests/audits/diagnostics; V3–V11 record2,834,862 normals/5,669,724 probes.
V11 protects18–36/96 organisms, leaving30.5–46.2 mutated children/generation
plus9 immigrants. This is not genetic collapse:95–96 unique genotypes remain.
All211 successful V2 frozen local seed outputs take2D+1 ticks;160 haveD>=8
and finish after16. Tick16 source-connected shaping disfavors that developmental
ordering, although completed solutions still win primary normal fitness.
This is not a universal solver lower bound or proof that timing explains failure.
Both goal positions lie outside the local tick16 fork-region cone on10/252
regular training pairs,1/12 validation,2/18 final; most pairs are within reach.
Independent distance code verifies all564 inputs;39 original input hashes match.

Recommendation, not an executed/preregistered experiment: calibrate current
controls/graded repair and achievable developmental objectives; then consider
one precommitted60–90min stable study of transferable elementary skills with
replication, frozen and evaluation-budget-matched resampling controls. Do not
require early exciting transfer to test a preregistered long-incubation claim,
but do not extend indefinitely. Set the detailed protocol before training.
Exclude all9296 prior whole layouts plus any new calibration layouts. No
claim of general progress from proxy scores, genome length, or isolated cases.

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
