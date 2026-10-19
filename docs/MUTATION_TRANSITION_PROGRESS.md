# V12P — complete and independently audited

Read `results/mutation_transition.md` and frozen
`docs/MUTATION_TRANSITION_V12P.md`. Do not repeat P, extend its closed cap, modify
frozen source, train/reselect on inspected final layouts or resume old searches.
No new mutation or evolution occurred. The shared-prefix evolution proposal in
`results/mutation_transition/next_experiment.md` is NOT launched/preregistered.

## Main result and limits

All seventeen saved states of O group0/founder71/walk0 are tested under both
topologies. Local founder through depth8:0/2080 pairs,120/4160 corridors.
Depth9 through16:544/2080 pairs,4160/4160 corridors,5280/8320 individual reachable
shortest outputs,0/4160 correct no-path,0 false no-path. Within0–8 and within9–16,
all12480 masks/statuses/ticks match; internal states were not recorded and work
counters differ. Depth9 work624400792 versus depth16 work667128216; no latency
benchmark. The first observed paired gain is one insertion at zero-based index112,
130→131 genes: `[3,36,49,44,0,0,64]`, saturating subtraction R36=max(0,R49−R44).
It is causal in the actual depth8 background; transplant/minimality and necessity
of preceding edits were not tested. No targeted edit was made in P.

Posthoc static certificate for depths9/16: R44 never assigned, resets0; R49 at
insertion comes from R55, loaded by opcode15 from prior channel2,range3. Final
channel1 store uses R36. Thus complete-tick channel1 becomes minimum positive
cardinal-neighbor channel2 at radius1 locally,8 nonlocally,or0. This is output
feedback; all-on exposure remains7. Certificates use saved source only.

Posthoc output diagnosis: ALL8320 reachable rasters per state equal the open
positions at goal distance≤shortest source-goal distance. All4160 disconnected
rasters equal the goal component, but do not give correct no-path reports.
An independent deque traversal verifies24960 saved rasters across depths9/16,
with zero new inference. This is output equivalence, NOT proof of internal BFS
or candidate-side oracle access. P's static and wave diagnoses are post-registration,
separate from the registered audit/analysis. Raw outputs are exactly audited.

Core full-stem prefix0:256/256 pairs; prefixes1/2/4 each0/256. No-stem prefix0:
256/256; source spurs at2/4 each0/256. Source at junction succeeds at degree2
or3; matching remote source degree3 does not rescue it. Arms2/3/4/6,straight/
turning,both stem labels,all8poses. Full open graph/goals are identical across
source positions. Stem bends do not rescue prefix4. Prefix contrasts each−1
across all16 core templates; bootstrap intervals degenerate at−1, conditional
on this fixed grammar/lineage, not population certainty.

Stress:prefix0 forks32/32,other forks0/64,two-junction0/96,cycle0/96. Cycle
alternatives12edges longer than shortest.32 extra individual paired successes
do not complete their other goal. Raw544/2080 includes duplicate no-stem labels;
exact cells/source/ordered-goal dedup gives416/1952 distinct paired inputs.
20 seeded templates (16core/4stress), not2080 independent units. Geometry forms
repeat with clutter; no general/ordinary maze claim or competitive speedup.

## Mechanisms and controls

Preselected subset:route founder,depth4,depth15,depth16,intact ×both topologies.
Five interventions, normal outputs first. Local target544 normal successful
eligible pairs: pulse-off544 retained,flag-off0,both-off0,endpoint-check-off544,
nonlocal-zero544;zero newly successful pairs in each. Flag is necessary for these
tested successes; initial pulse/extra endpoint check are not. Nonlocal-zero is
inert in local mode. Ordinary nonlocal target0pairs/0corridors,zeroing fails to
rescue any pair. Nonlocal normal denominator0 means no successful-mechanism
necessity inference. Local radius redirection is different from zeroing.
No forced traces or stopping retune.

Reachability descendants `mutation_depth/r1/f53/walk0/d16` and
`mutation_depth/r2/f69/walk1/d16` each give4160corridors+4160correctNP,0pairs,
0falseNP underboth topologies. Group1 founder/1/4 give0corridors/0NP; group2
founder/1/4 give1040corridors+4160NP but4768falseNP. NPgoals are isolated clutter.
O unmutated adjacent resample gives0pairs/0corridors on this no-adjacent corpus;
its old skill/genome is preserved. M component anchors solve corridors,notpairs.
Intact/BFS/A*/bitwave each8320reachable+4160NP correct. No known solver injected.

## Freeze, execution and verification

Protocol/source/panel/fixtures pushedaf823aa BEFORE any panel inference. Passing
profile and all16120 native parity checks pushedfa9945b BEFORE final generation.
Seed2026101911,fixtures1304.62 models/aliases;10 mechanism models. Original17
routing states,reachability founders/1/4/16,M validation anchors,resample,intact.
All48 relevant mutation events rebuilt from actual parents. All prior genomes,
populations,RNG,anchors and completion packets preserved.

Fixtures10templates,6240savedinputs,1232layouts. Main20templates,12480inputs,
2080pairs,4160corridors,4160NP,2464layouts.19×19 boards. Main all8poses;fixture
profiling pose0. Prefix0/1/2/4,degree controls,matched bend/core/stress graphs.
Main904960calls (773760normal+131200intervention),116.324837candidate seconds,
67248915826work,143.017926wall,846.078125MiBRSS. Shared720s/1500000call/
1200000000000work/4GiB/2GiB caps unextended. Profile72680calls including16120
native parity;12.725484candidate seconds,15.957421wall. Main projection148.167617s.
Warmups7candidate+3baseline calls perstage, separately recorded. Local AppleM4.

Audit PASSES first attempt:175.988019wall,1078MiBRSS;977640 exactcandidate
replays,1015080 independent rasters,37440baseline replays,16120native parity,
10800 independent old-V6 intervention-adapter parity comparisons,112 summaries,
48mutation events,186source/11input/2140prior completion hashes. No frozen-source
repair or protocol deviation.22focused tests pass(11new+11O);263collected,NOTfull
suite. Initial pre-registration test expected alternative-route difference8
instead of12; assertion/protocol corrected before freeze, unchanged geometry,
zero candidate calls at that time.

## Exclusions and next action

Exclude ALL181928 whole layouts:178232throughO +1232Pfixtures +2464Pfinal.
`mutation_transition_data.exclusions()` returns THROUGH O ONLY. Append BOTH
`results/mutation_transition_fixtures/mazes.json.gz` and
`results/mutation_transition/confirmation/mazes.json.gz`, including all poses.
Never relabel final as validation. Preserve raw rasters,static/wave certificates,
all figures and previous completion hashes.

Next proposal only:bounded12-minute controlled shared-prefix curriculum pilot,
fixed initial pools/RNG across curriculum arms, runtime/capacity/scoring unchanged,
protected depth9/depth16/corridor diversity, separate new fresh-random track,
resampling/frozen controls,three search RNG replicates. Explicitly conditional
carried-lineage evolvability; not an O population-gate pass. Common broader
validation,frozen choices before untouched final,strict gain/retention gate before
any longer run. No automatic60–90-minute extension or hand-coded path extraction.
