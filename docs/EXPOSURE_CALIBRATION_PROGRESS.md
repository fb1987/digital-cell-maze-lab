# V12M inherited exposure calibration handoff

V12M is complete and audited. Read `results/exposure_calibration.md` first.
Do not rerun or extend M, resume older closed runs, or train/reselect on inspected
M final cases. The next pressure-calibration proposal is not launched.

## Frozen design and provenance

Protocol/source/pools/fixtures were pushed in b85c25e before scientific generation.
All 76 validation choices and their evidence were pushed in e5fdf70 before final
generation. Seed 2026101908; fixtures 1274. All prior sources/results remain intact.
No evolutionary trajectory occurred: fixed neighborhoods and simulated selection.

V4 adds three inherited bits for radii 2/4/8 to the unchanged V3 program. A zero
bit returns zero for remote opcode 14/15 values, retaining dispatch, destination
assignment and read charges. Radius 1 stays available. Every arm charges one
exposure check per active remote opcode; suppressed lookup slots are diagnostic.
Added substrate buffers total 17 bytes; process RSS is separate. Bits are static
during a response, not dynamic regulation. Goal pulse is enabled in all M arms.
A mutation opportunity is 1/5 one uniform bit flip, 4/5 one existing V3 edit.

Active inherited exposure, neutral/all-on inert bits, fixed-zero nonlocal values,
and local-radius redirection share storage/accounting and candidate identities.
Local redirection differs from zeroing. Limits: 256 genes, 256 ticks, 4,096 reads
per site, 32,768 instructions per site, 65,536 cells. No solver injection.

Sixteen explicitly L-informed carried foundations each have eight enumerated mask
states and eight sampled one-edit siblings from the all-on base. Enumeration is
not reproduction. Three fresh groups each contain 96 random 64–128-gene founders
with independent program/bit RNGs. Total 544 logical genotypes, 1,438 physical
configurations across arms (354 carry, 1,084 fresh). Exact duplicates share physical
calls through explicit aliases; all logical candidate budgets remain equal.

Common pair-first ranking selects top-quarter elites, 64 lexicase parent draws
and two nominees per pool/arm. Replay with partial credit zeroed uses the same
saved responses. New validation selects one of each pair of nominees. All actual
records/RNG are saved; the reproductive draws do not create a new generation.

## Geometry and budgets

Carry calibration/validation: nine independent 25×25 templates, three goal forms
crossed with prefixes 1 straight / 2 straight / 4 bent. Matched forks, two-junction
and real alternative cycles, corridors and disconnected goals. All two locations
and eight poses are saved. Calibration queries center poses 0/4: 180 inputs,
54 pairs. Validation queries center poses 0/2/4/6: 360 inputs, 108 pairs.
Final adds prefix 8 straight: twelve templates, alternating location, four poses,
480 inputs / 144 pairs / 96 corridors / 96 no-path inputs per model.

Fresh calibration/validation: six independent 9×9 templates, adjacent choice,
two-edge arms and two-edge shared-prefix fork in two forms. Six isolated clutter
cells; disconnected goals are on open isolated cells. Query four poses: 144 inputs,
24 pairs, 48 corridors, 48 no-path. Final uses 24 templates and all eight poses:
1,152 inputs, 192 pairs, 384 corridors, 384 no-path. Founder groups share the case
corpus but have independent RNGs. Poses/variants/translations are correlated.

Original software timing preflight failed: four-pose calibration plus conservative
validation projected 450.301 seconds, over the 432-second threshold. Before main
generation and registration, only carry calibration poses were reduced to two.
No additional candidate calls, score tuning or change to scientific gates occurred.
The original failed log/record remains; derived revised projection 303.423 passes.
All pools, validation/final and fresh queries stayed fixed. No postregistration
protocol deviation or frozen-source repair occurred.

Calibration/validation: 253,368 physical calls, 233.838 candidate seconds / 480 cap,
139,647,255,671 work units, 258.539 seconds wall, 1,387.59 MiB peak RSS.
Logical calibration/validation calls: 350,208 / 49,536, equal across arms per pool.
Final: 60,096 calls, 83.742 candidate seconds / 300 cap, 49,728,170,044 work units,
85.822 seconds wall, 947.72 MiB peak RSS. Main combined: 313,464 calls, 317.580
candidate seconds, 189,375,425,715 work units. No latency comparison was performed.
Software profile/parity separately: 77,436 calls, 89.388 candidate seconds,
92.156 seconds wall; 3,276 old/new comparisons use two calls each. Warm-ups separately
record two candidate and three baseline calls per stage. CPU Apple M4, 10 cores,
16 GiB; Python 3.13.15, numpy 2.5.4, numba 0.68.0, llvmlite 0.50.0, pytest 9.1.1.

## Outcomes and interpretation

Carried pilot screen FAILS. Broad active changes 47/64 parent identities (26 program
changes); narrow 55/64 (24 programs), with elite/nominee changes. Related parents
also activate. For the SAME selected program, broad active versus neutral improves
32→48 complete pairs and 64→96 corridors; narrow 34→48 and 64→96. Neither loses
normal pairs/corridors. Both active programs match all 480 all-zero masks exactly.
Broad selects unedited base mask 4; narrow mask 2. Nonzero retained bits do not
establish useful nonlocal signalling. Gains occupy two straight-goal templates,
failing the requirement for at least two goal forms. No carried expansion allowed.

Active broad/narrow each complete 24 fork + 12 two-junction + 12 cycle pairs across
six short-prefix templates. K2 target and parent each complete 24 fork pairs and
96 corridors; the 68-gene unmutated draw completes 12 fork pairs / 96 corridors.
Protected local exception retains 44 corridors but has zero final pairs, so paired
retention is vacuous. Selected models complete zero prefix 4/8 pairs. Old useful
variants are preserved. No general solver or beneficial multirange effect emerges.

Fresh numerical gradient screen PASSES 3/3 in the neutral arm. Respect the recorded
pass; do not retroactively rewrite its criterion. Above-endpoint partial founders:
16/96,14/96,14/96. Shaping changes 46/64,47/64,27/64 parent draws and all elite sets.
Selected-parent two-edge partial rises from uniform .051/.048/.044 to .189/.238/.205.
Final selections each have .300 versus founder0 .050/.052/.000.

But saved-output diagnosis shows all three neutral selections emit the entire
source-connected component on 384/384 paired inputs, with identical output for
both goals on 192/192 pairs. They complete ZERO pairs, all 384 corridors, and no
no-path reports. Active/fixed-zero selections match this behavior. These are
unmutated random founders: group0 founder14 (89 genes), group1 founder62 (123),
group2 founder14 (84). The numeric score rewards component growth without routing.
This is evidence about the objective, not a test rejecting greater capacity/time.

Separate local group0 selection: unmutated founder81, 96 genes, completes 16 adjacent
pairs on four independently seeded turning templates in four poses each (0,1,5,6),
128/384 corridors and zero complete two-edge pairs. Preserve it as a control,
not an evolved discovery. Fresh exposure affects only two parent draws in group0;
no broad evidence for exposure utility in fresh founders.

All selected random-origin models fail explicit no-path reporting, with no false
reachable no-path claims. Every legal selected output is shortest. Intact VM/BFS/
A*/bit-wavefront solve all 1,152 reachable and 480 disconnected final inputs.

## Audit and preservation

First audit attempt PASSES: 451.514 seconds wall, 1,702.05 MiB peak RSS; 390,900
exact candidate replays, 395,796 independently graded rasters, 4,896 baseline
replays, 3,276 adapter comparisons, 128 mutations, 288 founders, 9,728 parent draws,
152 selection records and 76 validation choices. Regenerates 8,256 graph cases;
verifies 173 source / 16 input hashes and 1,390 prior G–L completion entries.
Ten new plus sixteen related focused tests pass; 230 collected, NOT a fresh full
suite. Raw masks, scores, counters, choices, RNG, mutations and old checkpoints
are preserved. The component diagnosis and plots use saved data only and are
explicitly post-registration analyses, without candidate inference.

Exclude ALL 175,592 whole layouts through M: 170,840 through L + 1,008 fixtures +
1,008 calibration + 1,008 validation + 1,728 final, including unqueried variants.
`exposure_data.exclusions()` returns THROUGH L ONLY. Future code must also add
`all_manifests()` for `results/exposure_calibration_fixtures` and M's `calibration`,
`validation`, `confirmation` directories (carry/fresh maze manifests in each).

## Next proposal only

See `results/exposure_calibration/next_experiment.md`. Calibrate one prospective
change to paired goal-conditioned branch-exclusion pressure on NEW cases, with
explicit tests separating component floods, endpoints, correct-arm partial progress
and complete routes. Require ordinary-output decision improvement and actual
selection changes, not just more distinct scores. Preserve component growers and
founder81 through equal anchor rules; use saved M pools as explicitly M-informed,
never select using M finals. Exposure stays fixed across the pressure comparison.
Only after preflight: approximately 12-minute matched current/new-pressure pilot,
resampling/local controls, checkpoint preservation and untouched final cases.
Require normal non-adjacent paired gains in at least 2/3 evolutionary replicates
with protected-skill retention before 60–90 minutes. No next experiment launched.
