# V12O cumulative mutation — complete and independently audited

Read `results/mutation_depth.md`, the frozen protocol
`docs/MUTATION_DEPTH_V12O.md`, and the unlaunched proposal
`results/mutation_depth/next_experiment.md`. Do not repeat O, extend its closed
cap, alter frozen source, resume old searches or train/reselect on final cases.
No evolution pilot was launched. Preserve every intermediate genome and RNG.

## Confirmed new lineage

The local target `mutation_depth/r0/f71/walk0/d16` (137 genes) descends from the
original M random founder `exposure/fresh/0/founder71` (128 genes). On final data
it completes 96/160 shortest pairs:32 adjacent and 64 non-adjacent. It also
completes 320/320 corridors and 512/640 individual reachable inputs. It identifies
0/320 disconnected cases and makes zero false no-path claims.

The 64 non-adjacent pairs split equally between two- and three-edge arms, both
straight and turning forms, across eight clutter contexts of four route-shape
types, all eight poses each. The founder and the SAME WALK's depth-1/depth-4
states each complete zero pairs and 32 corridors. All 960 masks at those early
states match the founder; work/counters differ. The target adds 96 pairs and
288 corridors. Only depths 1/4/16 were queried. Skill is present by 16 and absent
at 4; the first causal edit is not localized and all sixteen edits need not be
necessary. The immediate depth-15 parent is saved, NOT queried in O.

Both shared-prefix fork classes fail. Their shared prefix is ONE edge; total
routes are two or three edges. Successful choices are at the source. Source
degree, branches and tails also differ, so this is not an isolated prefix cause.
No new mechanism ablations or forced traces occurred. General solving,
beneficial multirange use and speedup remain unestablished.

Only group 0/local/depth 16 has a new useful interior response in discovery:
one candidate, reference and behavior. Its final-transfer gate PASSES, but its
discovery gate FAILS (requires four useful candidates, two references/behaviors,
and two more than EACH control). All combined gates fail; no cohort qualifies
in two of three groups. This rare positive is not population-level readiness or
fitness-guided evolution.

## Controls and secondary gains

All other frozen arm choices have zero non-adjacent pairs. Group 0 local
depth-1/depth-4/one-edit choices each retain eight adjacent pairs, 72 corridors
and proxy .03125, matching founder 81. Group 0 nonlocal mutation choices retain
12 adjacent pairs, 10 corridors and zero proxy. Group 2's unmutated resample
has 32 adjacent pairs and 64 corridors under both topologies. Preserve it;
consistent mutation superiority over random resampling is not established.

Group 1 `mutation_depth/r1/f53/walk0/d16` has 320 corridors and 320 correct
no-path reports under both topologies, versus founder zero/zero. Group 2
`mutation_depth/r2/f69/walk1/d16` also has 320 corridors and 320 correct no-path
reports. Its founder has 80 corridors and 320 correct no-path reports, but
432 false no-path claims on reachable inputs. Both descendants have zero pairs
and zero false no-path claims. All thirty selected choices have zero false
no-path claims. Disconnected goals are isolated clutter cells; these are limited
corridor/reachability gains.

On DISCOVERY, the same f71 target has 32 non-adjacent pairs and 160 corridors
locally, versus zero/zero with nonlocal ranges. That is selection evidence,
not an independent final intervention. The final nonlocal choice is a different
genome. Local topology redirects remote operations to radius one, not zero.

## Frozen design and execution

Seed 2026101910; fixtures 1294. Protocol/source/pools/fixtures pushed in f08484c
BEFORE any candidate call. All selection evidence and choices pushed in 21d5bfb
BEFORE final generation. No frozen-source repair or protocol deviation.

All 96 original founders in each of three M groups are retained. Two independent
16-edit walks per founder are queried at depths 1/4/16, alongside two independent
one-edit children and two random draws. Each terminal arm has 192 identities per
group. Totals:3,168 evaluated identities, 6,246 physical configurations, 576 walks,
9,792 events and 576 random draws. Random reference slots are not ancestry.
There is no performance feedback between edits. Every intermediate and replayable
RNG state is preserved. All-on M runtime/pulse/limits stay fixed; exposure bits
are inert. Median gene counts at depths 1/4/16 are 96/97/105; the deepest range
is 64–169, below the unchanged 256-gene ceiling.

Discovery and validation each have ten contexts, 480 inputs and 80 pairs per
model, all eight poses. Final has twenty contexts, 960 inputs, 160 pairs,
320 corridors and 320 no-path inputs. Fixtures save all eight poses but profiling
queries pose zero (60 inputs/model). This is a 9×9 tree grammar with repeated
route forms and new clutter, not a cycle/general-maze test. Poses, goals,
variants, related walks and depths are correlated; groups share cases.

Discovery uses 2,998,080 physical calls. Each terminal arm receives 552,960
logical discovery calls across groups/topologies. Validation uses 42,720 physical
calls and 57,600 logical nominee/reference slot evaluations. Final uses 62 models
and 59,520 physical calls, plus 2,880 baseline calls. Intact VM, BFS, A* and
bit-wavefront each solve all 640 reachable and 320 disconnected final inputs.
There is no repeated warm latency benchmark.

Main inference:349.144576 seconds of the shared 720-second cap; 3,100,320 calls
of the 3,400,000-call cap; 203,251,399,805 work units. Wall time:414.934834 seconds;
peak RSS:1,249.609375 MiB. Final continues the exact selection budget. Profiling
is separate:374,760 calls, 42.448760 candidate seconds, 48.411014 wall seconds.
Preparation takes 9.579615 wall seconds with zero inference. Warmups are recorded
separately. Local Apple M4, ten cores, 16 GiB; Python 3.13.15, NumPy 2.5.4,
Numba 0.68.0, llvmlite 0.50.0. No cloud/API/model download.

Audit PASSES first attempt:495.573369 wall seconds, 1454.140625 MiB peak RSS;
3,475,080 exact candidate replays;3,477,960 independent raster grades;
2,880 baseline replays;all 9,792 mutation steps,576 walks and576 random draws;
6,397 model summaries;5,760 nominee ranks;all30 validation choices. All181 source,
12 input and1,883 prior completion hashes pass. See verification.json. No repair.

Twenty-two distinct focused tests are covered (eleven new, eleven related N).
252 tests collected; NOT a fresh full suite. Posthoc diagnosis and plotting use
saved data only. Three figures have PNG/SVG/PDF versions and the illustration
has saved raster certificates. Prior completion packets contain 1,883 immutable
hash entries; recheck them after handoff updates before final commit.

## Exclusions and next proposal

Exclude ALL 178,232 whole layouts:177,032 through N, then 240 fixtures,
240 discovery, 240 validation and 480 final. The helper
`mutation_depth_data.exclusions()` returns THROUGH N ONLY. Append the four
`mazes.json.gz` files in `results/mutation_depth_fixtures/` and
`results/mutation_depth/{discovery,validation,confirmation}/`, including unqueried
fixture poses. Never relabel final data as validation.

Next proposal only:freeze all seventeen states of the f71 walk, plus the
reachability lineages, anchors, resample and intact controls. Use a new matched
all-pose corpus with downstream geometry fixed and source prefix/degree/bends
and goal-arm distances separated. Establish normal outputs before preselected
pulse/flag/endpoint/nonlocal probes; forced states never count as solutions.
Bound candidate inference to at most twelve minutes after a fixture cost profile.
No unchanged 60–90-minute evolution extension and no reinterpretation of O's gate.
