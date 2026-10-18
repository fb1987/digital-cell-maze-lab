# Digital Cell Maze Lab

An experimental, **offline-first**, biologically inspired computing project. The aim is to discover whether a compact, evolvable genome can control the local reactions of a spatial substrate and solve previously unseen mazes more efficiently than conventional pathfinding. **No such speed improvement has yet been demonstrated here.**

The central distinction: **one organism solves one entire maze.** The many grid sites are the organism's internal computing medium, *not* independent intelligent agents. Dozens or thousands of organisms, each possessing a different genome, can be evaluated in a population and selectively reproduced/mutated.

## Current checkpoint — October 18, 2026

The [research audit after V11](results/research_audit_2026_10_18.md) is complete.
It recommends continuing random-origin research, while calibrating the search
and developmental timing before adding another reward term. Evolved causal
signalling and context-specific fork choices are real; transferable general
solving and competitive efficiency remain unestablished. The retrospective
audit finds a tick-16 shaping bias against the known two-stage wavefront
development and quantifies the limited number of new mutants per generation.
No evolution or candidate inference was run for this audit.

The recommended next step is a separate positive-control/repair calibration,
followed by a stable, bounded random-origin study if calibration succeeds.
Known solver controls must never enter random-origin lineages. The earlier
hidden-context reward proposal below is deferred, not executed. The report
includes evidence, limitations, compute totals, and decision criteria.

## Latest completed experiment — V11

The [heritable capacity study V11](results/capacity_growth.md) is complete.
Twelve conditions continue 96 random-origin organisms for 48 generations,
comparing 128- and 256-gene ceilings at identical state capacity, objective,
mutation modes and inference work limits. Both start with the same native
populations, RNG states and protected variants. Old-program inference parity
was verified before training; no known solver enters these lineages.

**Programs grew; unseen path accuracy did not improve.** Evaluated programs
reach 228 genes, with a 240-gene program saved in the prepared next population.
Both capacities solve local **0/216** and evolved-range **1/216** using the
primary task archives, matching frozen controls. Secondary local choice
archives solve 4/216 versus 3/216 frozen under either cap. Every success is a
one-edge route. All selected models solve **0/180 distance ≥8** cases and
**0/42 paired routes**, with 0/18 strict paired choices. BFS/A*/wavefront solve
all reachable and disconnected cases. No competitive speedup is established.

A wider fixed-model diagnostic finds inherited goal-dependent hidden state
at fork exits on 3–4 of 18 pairs in one evolved-range lineage. It does not
produce correct choices. These are post-hoc observations on reused final
layouts, not new accuracy results. The signal was already present in a frozen
control; greater capacity did not establish better use of it.

Main run: **17.01 minutes, 213.2 MiB peak**. Tests: 122 full-suite passes,
4 focused passes after the final study guard edit, plus one extra exact
256-gene bound regression; all 123 current tests are covered. Independent
audits pass for 23,655 child mutation traces, 59,127 fitness records, saved
rasters, archive selection, lineage, layouts and source/model/storage hashes.
All population/RNG checkpoints and earlier results are preserved.

The next test proposed at V11 completion, now deferred by the research audit:
keep the larger capacity and compare current pressure with an added,
bounded hidden-context discrimination term at the exits. Keep complete routes
and strict paired choices above shaping. Preregister the term and fresh-layout
test before training; exclude all **9,296 whole layouts** seen through V11.
The [next-study proposal](results/capacity_growth/next_experiment.md) is not an
executed experiment. Random-origin discovery remains central.

See the [V11 protocol](docs/GROWTH_STUDY_V11.md) and
[diagnostic specification](docs/GROWTH_DIAGNOSTICS_V11.md). Use a new output
directory for reproduction; saved study directories refuse overwrite.

```bash
.venv/bin/python -m maze_evolution.growth_equivalence --out results/repeat_capacity_equivalence.json
.venv/bin/python -m maze_evolution.growth_study --out results/repeat_capacity
.venv/bin/python -m maze_evolution.growth_diagnostics --out results/repeat_capacity
.venv/bin/python -m maze_evolution.growth_audit --out results/repeat_capacity --repack
.venv/bin/python -m maze_evolution.growth_context --out results/repeat_capacity
.venv/bin/python -m maze_evolution.growth_context --out results/repeat_capacity --verify
.venv/bin/python -m maze_evolution.growth_report --out results/repeat_capacity
```

The study requires the canonical pre-training parity packet
`results/capacity_equivalence.json`; the repeated parity command above provides
a separate comparison. The saved study's report additionally includes its
editorial discussion/next-study files and the initial audit record.

## Goal-distance curriculum V10 and confirmation V10A — historical

The [matched goal-distance curriculum V10](results/distance_curriculum.md) and
[frozen-primitive confirmation V10A](results/distance_confirmation.md) are complete.
Twelve conditions continue96 organisms for48 generations, comparing Fixed hard
goals with near1/2→2/3→far goals on **identical maze/source/fork geometry**.
Capacity stays8 channels/128 genes; both use the same Choice-first objective.

**The curriculum did not establish transfer.** Primary task archives and frozen
controls solve0/216 unseen reachable mazes and0/179 at distance≥8. All selected
models make0/18 strict paired choices and0/42 paired complete routes. The
secondary multirange Curriculum choice archive solves one adjacent-endpoint
case. BFS/A*/wavefront solve all216 ordinary/42 paired targets and all no-path
cases. There is no competitive speedup.

Curriculum has more valid short training outputs, but no regular training
pair has both ordinary routes correct. Multirange strict training responses:
1 Curriculum versus15 Fixed; local0. Early shortened cues remove deceptive
fork bearings. Boundary-leader and frozen-control replays distinguish training
completion from independent transfer.

**One new training-only choice is preserved.** Native multirange replicate2,
birth30 genome i1472, chooses both proper exits at a fork6 edges from source,
with goals2/3 farther. A radius-2 read destination46→59 is sufficient on that
case; the other changed row is unnecessary there. Goal pulse and long reads
are both needed. It produced18 mutated offspring but left the final population;
its full genotype/ancestry is saved explicitly. V10A froze child,parent,root and
tested12 new matched near/far layouts:0/12 strict choices and0/24 routes at
either distance for all three. BFS48/48. The training response is real but
context-specific; random-origin discovery remains central.

Search13.82min; main16.95min; peak203.5MiB. Full suite116 passed, then4 focused
checks passed after final edits (117 current tests covered). Independent audits
verify59004 fitness records,268848 junction rasters,227 valid training claims,
48 selected normal replays and1440 boundary-assay outputs. Main and V10A
source/model/layout/lineage/storage checks pass; all populations/RNG and useful
neutral variants remain saved. Earlier source/raw results are unchanged.

The next test proposed then, now completed as V11: test128-versus256-gene capacity with a common copy-and-diverge block
mutation operator, matched native populations/protection and hard objective.
First verify old-genome inference equivalence; keep caps/work explicit. All
8702 saved layouts must be excluded. No known solver enters these lineages.

```bash
.venv/bin/python -m maze_evolution.distance_study --out results/repeat_distance
.venv/bin/python -m maze_evolution.distance_diagnostics --out results/repeat_distance
.venv/bin/python -m maze_evolution.distance_audit --out results/repeat_distance --repack
.venv/bin/python -m maze_evolution.distance_training_diagnostic --out results/repeat_distance
.venv/bin/python -m maze_evolution.distance_training_verify --out results/repeat_distance
.venv/bin/python -m maze_evolution.distance_report --out results/repeat_distance
```

See [V10 protocol](docs/DISTANCE_STUDY_V10.md),
[training-time diagnostic detail](docs/DISTANCE_DIAGNOSTICS_V10.md), and
[V10A protocol](docs/DISTANCE_CONFIRMATION_V10A.md). V10A's freeze/confirmation
commands use the recorded canonical V10 training assay; primary V10 outputs
never change in response to post-hoc diagnostics.

## Strict paired-choice priority V9 — October 18, 2026

The [strict paired-choice study V9](results/choice_priority.md) is complete;
**112 tests pass**. Twelve conditions evolved 96 organisms for 48 generations,
comparing Prefix scoring with a strict paired-choice priority below complete
route correctness. Both use the same V8 populations/ancestors, archives,
eight-channel/128-gene capacity and unchanged V6 pulse runtime.

**The new priority did not change evolution.** All six matched pressure pairs
have identical ordered genotype populations throughout and identical final RNG
states. Multirange training has 19 strict-both responses per pressure across
four batches; local has none. Unprotected positive genotypes produce the same
40 mutated offspring under both pressures. Global best sets match in all four
active pools, and 512 post-hoc matched-seed parent draws agree. These rare
choices already reproduce; transfer is the current bottleneck.

Primary task archives solve local **1/216** and multirange **0/216**, matching
frozen controls. All selected models make **0/18** paired fork choices and
0/42 paired complete routes. BFS/A*/wavefront solve all 216 ordinary and 42
paired reachable targets plus all no-path cases. No speed advantage is found.

The inherited local success has nine edges and one turn. Moving its goal to
an intermediate path site leaves output concentrations/source states identical
at every tick 1–19; the common endpoint-aware halt emits a five-edge prefix at
tick 11 instead of nine edges at tick 19. It remains a growth precursor.

Both pressures find the same validation-only fork lineage at births 3/5. It
needs the goal pulse but retains its paired choice when nonlocal reads are
zeroed on that case. It does not transfer to the fresh paired set. All 19
strict training responses have proper incoming source connections and
shortest incoming prefixes in an additional raster diagnostic.

The gate failed. Search **13.90 minutes**, main **17.09 minutes**, main peak
**200.4 MiB**. Audits cover 58,998 fitness records, 59,046 priority records,
267,356 junction masks and 6,908 final/diagnostic normal outputs. Full population/
RNG checkpoints, 32,258 new IDs and neutral diversity remain saved. V1–V8/V8A
source and raw results are unchanged.

Next: test a near-to-far goal-distance curriculum at fixed capacity/objective,
keeping validation and final tasks difficult and independent. This tests
whether attainable goal-control subfunctions can compose across distance.
Random-origin discovery, capacity, regulation and evolutionary time remain
open research tracks; no known solver rules enter these lineages.

```bash
.venv/bin/python -m maze_evolution.choice_study --out results/repeat_choice
.venv/bin/python -m maze_evolution.choice_diagnostics --out results/repeat_choice
.venv/bin/python -m maze_evolution.choice_audit --out results/repeat_choice --repack
.venv/bin/python -m maze_evolution.choice_path_diagnostic --out results/repeat_choice
.venv/bin/python -m maze_evolution.choice_selection_diagnostic --out results/repeat_choice
.venv/bin/python -m maze_evolution.choice_report --out results/repeat_choice
```

See the [V9 protocol](docs/CHOICE_STUDY_V9.md) and
[`results/choice_priority/`](results/choice_priority/). Post-hoc path/selection
assays are labelled and do not alter primary selection or accuracy.

## Junction choices V8 and confirmation V8A — October 18, 2026

The [junction-choice study V8](results/junction_choice.md) and its
[frozen-primitive confirmation V8A](results/junction_confirmation.md) are complete;
**106 tests pass**. Twelve conditions evolved 96 organisms for 48 more generations,
comparing current Balanced pressure with source-dependent fork-choice credit.
The runtime, 128-gene/eight-channel capacity and input stayed fixed. Both V7
lineages and their protected diversity remain preserved.

Multirange Junction task archives solve **3/216** unseen shortest paths, versus
0/216 Balanced and 1/216 frozen. All task arms solve **0/174** long cases and
0/42 paired targets. The three Junction successes are only 1–3 edges, including
two paths with one turn; no mandatory detour is solved. BFS/A*/wavefront solve
all 216 ordinary and 42 paired reachable inputs and all no-path cases. There is
no competitive speedup or established general solver.

**Two validation-only fork-choice primitives emerged**, one per multirange
pressure. They choose the proper source-connected exit under switched goals;
both need the goal pulse and nonlocal reads on their qualifying examples.
One primitive requires an instruction reorder **and** a scratch-register
redirection: either change alone fails, while their combination succeeds.
This demonstrates cooperating changes in that parent/context, not a general
regulatory strategy. Full validation routes remain wrong.

Neither primitive transfers to the 12 new V8A confirmation layouts: **0/12**
paired fork choices and 0/24 complete routes, also 0/12 and 0/24 for their roots/
parents. The primary final selections make 0/18 unseen paired choices. A
supplemental validation archive preserves both primitives, including one the
mean-J archive missed because broad prefix growth ranked higher.

The extension gate failed. Search 13.47 minutes; main 16.54 minutes; main peak
RSS 208.2 MiB. Full population/RNG and 33,334 new individual lineages are saved.
All 6,908 main final/diagnostic normal outputs and 58,686 fitness records were
audited; V8A additionally verifies 124 candidate and 24 BFS outputs. V1–V7
source/raw data remain unchanged. These bounded negatives leave the capacity,
regulation and longer-evolution hypotheses open.

Next test: protect both cooperating variants in common initial cohorts, then
compare strict paired-choice-first selection with the current prefix-weighted
reward on new layouts, keeping full route correctness primary. Preserve
neutral diversity and require transfer before an hour-scale extension.

```bash
.venv/bin/python -m maze_evolution.junction_study --out results/repeat_junction
.venv/bin/python -m maze_evolution.junction_diagnostics --out results/repeat_junction
.venv/bin/python -m maze_evolution.junction_audit --out results/repeat_junction --repack
.venv/bin/python -m maze_evolution.junction_report --out results/repeat_junction
.venv/bin/python -m maze_evolution.junction_confirmation --out results/repeat_confirmation
```

See the [V8 protocol](docs/JUNCTION_STUDY_V8.md),
[V8A protocol](docs/JUNCTION_CONFIRMATION_V8A.md),
[`results/junction_choice/`](results/junction_choice/) and
[`results/junction_confirmation/`](results/junction_confirmation/).

## Balanced two-goal pressure V7 — October 18, 2026

The [balanced two-goal study V7](results/balanced_goal.md) is complete; **100 tests
pass**. Twelve conditions continued V6 random-origin populations for 48 further
generations with 96 organisms each. Both arms use the same goal pulse, genome
capacity, starting genotypes and archive-selection rules. Balanced pressure
adds credit for the weaker of two goal responses, alongside the existing
credit for the stronger response. Both reward maxima match; mixed unreachable
pairs retain their original scoring.

**Multirange two-goal output improved:** weaker-goal score B is 0.0310 versus
0.0215 frozen and 0.0048 under Mean pressure. Both-direction qualification is
2/18 unseen regular pairs, versus 1/18 frozen and 0/18 Mean. The improvement is
concentrated in one replicate; local Mean performs better than local Balanced.
Removing the goal pulse or nonlocal reads reduces the multirange Balanced B
score to zero. These are intermediate output measures, not correct routes.

Primary task archives solve local 4/216 under either pressure (same frozen),
multirange 1/216 Balanced and 2/216 Mean (frozen 1/216). All task arms solve 0/165
long cases and 0/42 paired targets. An existing local genome produces a five-edge
path with two turns; completed task successes span 1–5 edges. BFS/A*/wavefront
solve all 216 primary and 42 paired reachable targets plus all no-path cases.
No competitive speedup is demonstrated.

The new junction diagnostic finds 0/9 pairs with both required choices correct.
In 6/9 multirange Balanced tree pairs, source-connected output reaches the fork
under both goals and illuminates both outgoing alternatives. Goal-sensitive
growth is still missing useful branch suppression. Mean changes source state
in 11/18 pairs at tick 16 versus 4/18 Balanced; more source response alone does not
predict the better paired output here.

The extension gate failed. Search 13.18 minutes; main run 16.18 minutes; peak RSS
192.2 MiB. All 6,888 final/diagnostic normal outputs and 58,240 fitness records
were audited. Population/RNG, lineage, balanced/goal/task/source archives and
neutral diversity remain preserved. V1–V6 source and raw data are unchanged.
Construction tests used a separate seed; models froze before final layouts.

The next controlled experiment should reward source-connected, goal-dependent
junction choices, including suppression of the wrong branch, against the
current pressure. Include cyclic shortest-step ties and deceptive detours,
keep all oracle labels in fitness, and reserve fresh layouts. Preserve both
lineages; capacity stayed fixed in V7, so the capacity hypothesis remains open.

```bash
.venv/bin/python -m maze_evolution.balance_study --out results/repeat_balance
.venv/bin/python -m maze_evolution.balance_diagnostics --out results/repeat_balance
.venv/bin/python -m maze_evolution.balance_audit --out results/repeat_balance
.venv/bin/python -m maze_evolution.balance_report --out results/repeat_balance
```

See the [V7 protocol](docs/BALANCE_STUDY_V7.md) and
[`results/balanced_goal/`](results/balanced_goal/). Exact unseen shortest paths,
latency and memory remain the mission's final measures.

## Goal-state pulse V6 — October 18, 2026

The [goal-state pulse study V6](results/goal_beacon.md) is complete; **95 tests
pass**. Twelve conditions continued random-origin populations for 48 generations
with 96 organisms each. Both input arms use identical initial genotypes and the
same product objective. The treatment adds an initial goal pulse in channel 1;
all primitive rules, eight channels and the 128-gene limit stay fixed. Both V5
arms' validation-selected task/goal/transmission variants are preserved.

**Goal communication improved on unseen paired layouts.** Multirange goal
archives score 0.0390 versus 0.0135 frozen Pulse and 0.0137 evolved Flag. Changing
the goal changes source state by tick 16 in 8/18 regular pairs, versus 5/18
frozen Pulse and 1/18 Flag. Removing the pulse from those evolved genomes, or
zeroing nonlocal reads, reduces the intermediate goal score to zero. These are
precursor measures; no paired output is a legal route.

Route accuracy remains unchanged: local task archives solve 2/216 primary
reachable mazes, matching frozen controls; multirange arms solve 0/216. All task
arms solve 0/178 distance≥8 cases, 0/133 mandatory-detour cases and 0/42 paired
targets. One inherited local success spans seven edges with a turn on a new
maze. It is present before V6 evolution. BFS/A*/wavefront solve all 216 primary
and 42 paired reachable targets, and all disconnected cases. No competitive
speedup is established.

The extension gate did not pass. Search took 13.11 minutes; the main run with
holdouts/timing took 16.31 minutes, with 180.1 MiB peak RSS on the M4. All 6,888
final/diagnostic normal outputs and 58,100 training fitness records were audited.
Full population/RNG, lineage and frozen controls remain available. The report
records one protocol deviation: a construction-only test used the study seed
before training, without evaluating a candidate; actual final output evaluation
occurred only after model freeze. Future construction tests should use a
separate seed. V1–V5 source/raw results are unchanged.

The next controlled test should compare mean versus balanced two-goal pressure
at fixed pulse input and capacity. Higher mean score can favor one direction
while losing the other. A supplemental validation-only archive preserves
balanced variants from both V6 arms without additional final evaluation. Keep
these, the transmission variants and inherited directional growth; reserve
fresh layouts and retain exact path correctness as the final measure.

```bash
.venv/bin/python -m maze_evolution.beacon_study --out results/repeat_beacon
.venv/bin/python -m maze_evolution.beacon_diagnostics --out results/repeat_beacon
.venv/bin/python -m maze_evolution.beacon_audit --out results/repeat_beacon
.venv/bin/python -m maze_evolution.beacon_report --out results/repeat_beacon
```

See the [V6 protocol](docs/BEACON_STUDY_V6.md) and
[`results/goal_beacon/`](results/goal_beacon/). Random-origin discovery remains
central; this bounded experiment identifies a useful signalling change and an
unresolved route-construction problem.

## Factorized curriculum V5 — October 18, 2026

The [factorized curriculum study V5](results/factor_curriculum.md) is complete;
**88 tests pass**. Twelve paired conditions continued six V4 populations for
48 generations with 96 organisms each. Both arms protect inherited signalling
and goal-sensitive variants. One arm rewards connected growth and goal response
separately, then transitions to the same product reward as its control.

**An isolated new filament appeared in the control arm:** it emits a correct
10-edge shortest path with three turns through two junctions on one independent
paired 9×9 maze. Ancestry analysis links its first success to three gene-row
edits from a failing parent. It moves west/south, fails the other goal and all
three rotated versions, and develops identically under both goals through its
successful stopping tick. The shared runtime's endpoint check supplies the
different stopping time. This is a concrete precursor of growth following maze
geometry; goal-directed branch choice is still absent.

The curriculum has no demonstrated unseen advantage. Its local/multirange task
archives each solve 1/216 primary reachable cases, versus 2/216 local and 1/216
multirange controls. Every task arm solves 0/177 distance≥8 primary cases and
0/197 cases requiring a turn. The isolated turned success is on the separate
paired set: local control 1/42; curriculum arms 0/42. BFS/A*/bit-wave solve all
reachable and disconnected cases. Curriculum task archives classify 12/48
primary no-path cases, with no false claims on reachable primary cases, versus
0/48 frozen; the disconnected family has a corner/partition bias.

Multirange goal-archive probe scores are 0.0068 curriculum versus 0.0089 control;
local scores both 0.0106. These are intermediate scores, not completed paths.
The extension gate did not pass. Search took 13.02 minutes; the full main run
took 16.05 minutes on the M4, with 162.8 MiB peak RSS. Full population/RNG and
lineage checkpoints are preserved. V1–V4 code/results remain unchanged.

Exploratory validation probes show limited goal information reaching the source,
even by tick64. The next controlled test should compare symmetric source/goal
initialization with the existing convention, at fixed capacity and objective.
The source has an initial state pulse plus a local flag; the goal currently has
only a flag. A goal pulse supplies public stimulus, without inserting a solver.
Keep all validation-selected archives from both arms and reserve fresh layouts.

```bash
.venv/bin/python -m maze_evolution.factor_study --out results/repeat_factor
.venv/bin/python -m maze_evolution.factor_diagnostics --out results/repeat_factor
.venv/bin/python -m maze_evolution.factor_timecourse --out results/repeat_factor
.venv/bin/python -m maze_evolution.factor_lineage_diagnostic --out results/repeat_factor
.venv/bin/python -m maze_evolution.factor_prefix_diagnostic --out results/repeat_factor
.venv/bin/python -m maze_evolution.factor_audit --out results/repeat_factor
.venv/bin/python -m maze_evolution.factor_report --out results/repeat_factor
```

See the [preregistered protocol](docs/FACTOR_STUDY_V5.md) and
[`results/factor_curriculum/`](results/factor_curriculum/). The time-course and
isolated-success analyses are explicitly post-hoc diagnostics, not new accuracy
tests or model tuning. Raw rasters, gene edits, costs and source hashes are saved.

## Goal-conditioned study V4 — October 18, 2026

The [goal-conditioned continuation V4](results/goal_conditioning.md) is complete;
**84 tests pass**. Twelve paired conditions continued six V3 random-origin
populations for 40 generations with 96 organisms each, comparing the existing
transmission objective against an added goal-dependent output reward. Genome
capacity and inference limits stayed fixed. Each population protects its learned
V3 signalling elite; no known solver was inserted.

Some goal-sensitive, branched outputs evolved, but their validation gains did
not establish an unseen advantage. On separate goal-pair tests, the multirange
goal archive scores 0.0022 under goal pressure versus 0.0071 in its transmission
control; local scores are 0.0033 versus 0.0035. No archive meets the
both-directions criterion on a final pair. These scores are intermediate output
diagnostics, not completed routes.

| Final task archive | Shortest / reachable | Distance ≥8 shortest |
| --- | ---: | ---: |
| Local, either objective | 1/216 | 0/174 |
| Evolvable ranges, either objective | 0/216 | 0/174 |
| Compiled BFS / A* / bit-wave | 216/216 | 174/174 |

The one local success is an adjacent endpoint and matches its frozen control.
All candidates fail the separate 42 reachable paired-goal tests; conventional
baselines solve all 42 and all six no-path cases. No competitive speedup emerged.

Search took 9.67 minutes; recorded training plus recovered final evaluation and
timing took 15.32 minutes. The original final generator exhausted its unused
9×9 corner-DFS layouts before evaluating any final output. Only final 9×9
perfect mazes changed to Wilson spanning trees, after genomes were frozen.
The report records that sampling deviation, timing scope and memory limits.
All 7,128 primary, 1,296 paired and 192 ablated normal outputs were rechecked.
Logs preserve every evaluated genotype, fitness, snapshot, parent and RNG state.

The next controlled test should provide separate intermediate credit for
source-dependent connected growth and goal-dependent modulation, then require
their conjunction. Training shows connected output is common but goal-specific
progress is rare. Keep random-origin discovery central, capacity fixed and
reserve fresh layouts; these finite negative runs do not establish impossibility.

```bash
.venv/bin/python -m maze_evolution.goal_recovery --run --out results/repeat_goal
.venv/bin/python -m maze_evolution.goal_diagnostics --out results/repeat_goal
.venv/bin/python -m maze_evolution.goal_audit --out results/repeat_goal
.venv/bin/python -m maze_evolution.goal_report --out results/repeat_goal
```

See the [preregistered design](docs/GOAL_STUDY_V4.md) and
[`results/goal_conditioning/`](results/goal_conditioning/). V1–V3 code/results
remain unchanged. The recovery runner handles the documented sampling failure
without restarting training or changing frozen genomes.

## Source-pressure study V3 — October 18, 2026

The [source-dependent pressure continuation](results/source_pressure.md) is complete;
**76 tests pass**. It forks six saved random-origin populations, pairs current and
causal signalling objectives, and runs 96 organisms for 160 additional generations
per condition. The genome capacity and inference runtime remain fixed. Search
including probes took 60.45 minutes on the M4; fresh tests and timing brought the
main run to 64.22 minutes. No known solver entered the random-origin lineages.

A measurable precursor improved on 174 unseen reachable cases with endpoint
distance at least eight:

| Transmission archive | Frozen initial | Current objective | Causal pressure |
| --- | ---: | ---: | ---: |
| Local mean signal score | — | 0.3071 | 0.3071 |
| Evolvable ranges mean signal score | 0.2480 | 0.4185 | 0.5090 |

The score measures source-dependent hidden activation and subtracts leakage into
other components. Causal pressure leads in two of three held-out replicates.
Zeroing nonlocal reads reduces its score to 0.0809. Leakage is higher than under
the current objective, and a broadcast does not encode a legal path.

**No general shortest-path solver or speed advantage emerged.** Final multirange
task archives solve 2/216 reachable mazes under either objective, versus 4/216 for
their initial frozen task selections. Local task archives solve 2/216 under the
current objective and 0/216 under causal pressure. Every final task arm solves
0/174 cases at distance>=8. All observed organism successes are straight paths
of only 1–2 edges. Compiled BFS/A* solve all 216 reachable and all 48
disconnected cases. The report distinguishes diagnostic transmission archives
from task archives and reports complete outputs, latency and real work.

Random-origin discovery remains active. Populations, RNG states and ancestry are
preserved in [`results/source_pressure/`](results/source_pressure/). A justified
next experiment preserves these signalling lineages and tests goal-conditioned
path thinning, with completed shortest paths still first and another fresh final
set. More complexity remains a hypothesis; it is not inferred from gene count.

```bash
.venv/bin/python -m maze_evolution.signal_study --out results/repeat_source_pressure
.venv/bin/python -m maze_evolution.signal_diagnostics --out results/repeat_source_pressure
.venv/bin/python -m maze_evolution.signal_audit --out results/repeat_source_pressure
.venv/bin/python -m maze_evolution.signal_report --out results/repeat_source_pressure
```

See the [preregistered design](docs/SIGNAL_PRESSURE_V3.md). V1/V2 raw results and
runtime/search modules are unchanged.

## Range/regulation study V2 — October 18, 2026

The [range/regulation continuation](results/range_and_regulation.md) is complete:
**63 tests pass**. V2 adds eight state channels, up to 128 typed genes, conditional
expression, local/fixed/evolvable signalling radii, diversity-preserving search,
independent resampling controls and exact population/RNG checkpoints.

The study ran 656,640 training responses (724,176 including validation) in about
12 minutes on the M4. All models were frozen before 264 entirely fresh test cases.
The expanded random-origin cohort used 96 organisms × 120 generations × three
seeds for each topology, 14.4× V1's population-generation slots per run.

| Rich random-origin population | Evolved shortest / reachable | Independent sampling | Initial frozen |
| --- | ---: | ---: | ---: |
| Local | 2/216 | 2/216 | 0/216 |
| Evolvable ranges | 1/216 | 2/216 | 0/216 |

All random-cohort successes were adjacent endpoints. None solved the 165 cases
with distance at least eight. Large genomes and improved partial scores did not
yet produce a general algorithm. **Random-origin discovery remains an active
track**: checkpoints retain the populations for longer continuation rather than
restart them. Greater capacity, time and regulatory pressure remain hypotheses.

Seeded local/fixed/evolvable arms each solved 211/216, with five budget failures
and 48/48 correct no-path outputs. Their champions did not use nonlocal reads.
The same frozen local seed solves 189/216 at the old work cap, so its gain to
211 comes from inference budget, not evolved range use. No speed advantage over
compiled BFS was found. See the [preregistered protocol](docs/RANGE_STUDY_V2.md).

```bash
.venv/bin/python -m maze_evolution.range_study --out results/repeat_ranges
.venv/bin/python -m maze_evolution.range_audit results/repeat_ranges
```

Defaults reproduce the saved design. Full compressed lineage/fitness/output logs,
initial controls, timing samples and 48 continuation checkpoints are in
[`results/range_and_regulation/`](results/range_and_regulation/). The new runtime
permits a broad initial activation to develop/prune before stopping; V1's immediate
endpoint halt is preserved in V1 but removed in V2. V2 gates still pay dispatch
cost, and all ranges share hard work and memory caps.

## First local experiment — October 17, 2026

The context bundle is imported and the project is prepared for development on an
Apple M4 Mac with 16 GiB memory and Python 3.13.15. Its **41 tests passed**, including
genome validation, synchronous execution, independent raster validation and
deterministic evolution replay. Maze generation is reproducible, the compiled
baseline runs, and the NumPy-only fallback was checked. See the local
[smoke output](results/local_setup_2026-10-17.txt) and
[environment/source metadata](results/local_setup_2026-10-17.json).

The first bounded genome runtime, evaluator and evolutionary pilot are complete.
Read [the full experiment and phenotype audit](results/first_evolution.md).
Three runs of 32 organisms over 25 generations compared random and wavefront-seeded
populations with their frozen initial champions. All champions were frozen before
generating the final test set.

| Initialization | Evolved shortest paths / reachable tests | Frozen control |
| --- | ---: | ---: |
| Random | 4/240 | 4/240 |
| Wavefront seed | 200/240 | 200/240 |

The random successes simply light every open pixel on unbranched snake corridors.
They do not demonstrate learned maze solving. Seeded organisms solve all 96
same-size unseen cases and all 48 disconnected cases. Forty larger/structural
cases exhaust the common read budget. Two runs delete a redundant persistence
instruction (29→28 genes, 2.22% less counted work), with unchanged accuracy.
The generic interpreter is about 150× slower than compiled BFS in the sampled
17×17 timings. These are pilot implementation comparisons, not a competitive win.

This checkpoint motivated the local/fixed/evolvable multi-distance continuation
above. The [original range proposal](docs/MULTIDISTANCE_PLAN.md) remains available;
the actual V2 design and changed limits are recorded separately.

## Start here (for Codex)

1. Read [`AGENTS.md`](AGENTS.md) (repository coding-agent instructions).
2. Read [`docs/THREAD_CONTEXT.md`](docs/THREAD_CONTEXT.md), then [`docs/EXPERIMENT_SPEC.md`](docs/EXPERIMENT_SPEC.md).
3. Run the existing baseline and tests.
4. Give Codex the prompt in [`CODEX_START_HERE.md`](CODEX_START_HERE.md).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python cellular_maze_lab.py --sizes 33,65,129 --samples 6 --render --out-dir output
```

Only `numpy` is essential for the reference script. `numba` provides a compiled BFS baseline. `Pillow` renders image triptychs; `pytest` runs tests. The reference implementation is CPU-only and makes **no network or LLM calls**.

For the verified local environment, activate the existing `.venv`. To recreate
its exact package versions with `uv` on Python 3.13:

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements-lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python cellular_maze_lab.py --sizes 33,65 --samples 3 --seed 1729
```

`requirements-lock.txt` records the packages tested on macOS arm64; dependency
and wheel compatibility on other platforms still needs verification. `.venv`
and generated `output/` images stay out of Git.

## Run the evolutionary experiment

The interpreter uses Numba from `requirements-dev.txt`. It evaluates four local
uint16 channels with a closed 14-operation instruction set; genomes cannot execute
Python or call the evaluator. See [the genome](maze_evolution/genome.py),
[runtime](maze_evolution/runtime.py), [evaluator](maze_evolution/evaluator.py),
and [selection/experiment harness](maze_evolution/experiment.py).

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m maze_evolution.experiment --out results/repeat_evolution --seed 20261017 --replicates 3 --population 32 --generations 25 --samples 8 --benchmark-repeats 30
.venv/bin/python -m maze_evolution.inspect_results results/repeat_evolution
```

Choose a fresh output directory for each run. The saved pilot took about 25 seconds
after cached JIT warm-up. This includes evolution, final tests and timing; a first
compilation may take longer. Raw genomes/parents, all training fitnesses, exact
maze inputs, output masks, timings and environment metadata are in
[`results/first_evolution/`](results/first_evolution/).

## Files

| Path | Purpose |
|---|---|
| `cellular_maze_lab.py` | Runnable baseline: Python BFS, Numba BFS (optional), bit-packed wavefront, dead-end retraction; random/perfect/snake/comb maze generators |
| `tests/` | Core solver correctness tests, including cyclic and disconnected mazes |
| `maze_evolution/` | Typed genome, bounded interpreter, datasets, independent evaluator, evolution, baselines and audit |
| `AGENTS.md` | Repo-wide guardrails and next mission for coding agents |
| `CODEX_START_HERE.md` | Ready-to-paste Codex instruction |
| `docs/THREAD_CONTEXT.md` | Conversation handoff and user intentions |
| `docs/ARCHITECTURE.md` | Biological-to-computational mapping, organism vs cell and runtime model |
| `docs/EXPERIMENT_SPEC.md` | Initial evolution experiment, fitness, measures, baselines, phases, acceptance tests |
| `docs/RESEARCH.md` | Prior art and scientific cautions |
| `docs/MULTIDISTANCE_PLAN.md` | Proposed local/multi-distance experiment and validation sequence |
| `requirements-lock.txt` | Exact package versions used in the local setup check |
| `results/local_setup_2026-10-17.*` | This Mac's setup checks, metadata and smoke timings |
| `examples/` | Example 65×65 maze/result images from prior work |
| `results/baseline_smoke.txt` | A smoke run on this environment; **not** a scientific performance study |

## What exists vs what remains

**Existing**: standard/compiled BFS, compiled A*, exact bit-parallel wavefront,
leaf-pruning toy baseline, maze generators, bounded heritable programs, local
organism runtime, deterministic mutation/selection, frozen controls, independent
holdout validation, full-raster timing and recorded visual results.

**Also implemented in V2**: multi-distance sensing, conditional gene expression,
larger random-origin genomes, diversity/lexicase search, training-sample-matched
independent search controls and exact checkpoint resumption.

**Not yet built**: a reliable random-origin solver, hierarchical or 3D substrates,
exact CPU-budget-matched search controls, a broad optimized conventional baseline
audit, or a competitive result.

## Experiment boundaries

- No paid APIs, cloud services, AWS deployment, foundation-model inference or unneeded dependencies.
- Do not use BFS or a precomputed solution *inside* the organism at inference time. Ground truth may be computed offline for scoring.
- Do not benchmark naive Python BFS alone and call a win; include compiled baselines and complete end-to-end wall-clock cost.
- Do not confuse millions of logically simultaneous grid updates with millions of CPU/GPU cores or zero-cost computation.
- Preserve reproducibility: fixed seeds, explicit environmental metadata, unseen tests and detailed result logs.
