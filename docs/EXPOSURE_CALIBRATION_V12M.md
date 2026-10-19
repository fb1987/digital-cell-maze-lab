# V12M — calibration of inherited nonlocal exposure and elementary selection

Freeze and push protocol, software, fixed pools, RNG/events and fixture profiles
BEFORE generating scientific calibration/validation cases. Freeze and push every
validation-selected choice BEFORE generating final cases. No previous run resumes;
no L final cases become training. This study is fixed-neighborhood calibration,
not multigeneration evolution. Seed2026101908,fixtures1274.

## Runtime and genome

V4 wraps an unchanged V3 instruction tuple (1–256 genes) with exactly three
inherited bits enabling radius2/4/8 values. Local values remain available. The
existing V6 kernel is copied into a separate file; only exposure checks and their
accounting change. Existing sources remain immutable. Only active opcodes14/15
can be suppressed. Suppression returns zero while still executing the instruction,
writing the destination, and charging every original lookup/dispatch. Old register
expression gates and emission/cap rules remain. Goal pulse is TRUE in all M arms,
matching L normal inference; do not attribute comparisons with older experiments
solely to this new field or silently infer their training defaults were identical.

Base work counters must match old all-on and external nonlocal-zero runtimes
exactly. Add one explicit `exposure_checks` work unit per executed opcode14/15,
including local-radius instances, in EVERY M arm. Track `suppressed_reads` as
requested blocked lookup slots, including unavailable neighbors; this diagnostic
is not an extra charge. Total declared work=reads+dispatches+exposure_checks.
The read-only uint8 mask buffer and two int64 counters add17 substrate-array bytes;
this overhead is reported separately from Python object memory and RSS. No speed
claim from operation counts. Account for real end-to-end implementation overhead
before any eventual latency claim. Existing per-response limits remain256ticks,
4096reads/site,32768instructions/site,65536cells; CPU only.

Four equal-budget arms share exactly the same candidate identities/metadata:
active mask; neutral metadata with all values enabled; fixed-zero with all nonlocal
values blocked; local runtime. Neutral is also the fixed all-on exposure control.
Local means all remote opcodes use radius1, not zero-valued distant reads. All four
arms store bits, execute the same exposure accounting, and have the same mutation
opportunities. This is static inherited suppression, NOT dynamic/contextual
regulation or evidence that multiple ranges are useful.

A single mutation opportunity is a bit flip with probability1/5 (uniform bit),
otherwise exactly one existing V3 edit with probability4/5. It replaces, rather
than supplements, an instruction-edit opportunity. Concrete events, RNG states,
serialization, strict bounds and mask-sensitive genotype digests must replay.
All-on/old and all-off/external-zero parity is required across real25×25 and9×9
geometry classes and early budget caps. Intermediate masks get independent
single-tick opcode/bit tests. No arbitrary code execution.

## Performance-blind pools

Sixteen carried foundations: all thirteen random-origin J panel entries plus K2
target, immediate parent and entry ancestor. For each, enumerate all eight mask
states of its original program, then draw eight single-edit siblings independently
from the all-on wrapped foundation, using the above mutation distribution. The
eight-state enumeration is an intervention grid, not eight one-mutation births.
Preserve all outcomes. Each foundation has16 logical candidates; related
foundations are not independent evolutionary replicates.

Fresh track: three independently seeded groups of96 rich random64–128-gene
founders, with mask bits drawn from separate seeded RNGs. Programs never contain
injected known rules. No fitness-guided mutation, reproduction or model replacement
occurs in this study. All founder and neighborhood RNG states are saved.

Every pool is identical across the four arms. Deduplicate only physically
identical inference (program, effective topology, effective mask), recording
aliases and equal LOGICAL case budgets. Ignore bits in the physical key only
when local topology makes them inert. The all-on intact solver remains a separate
software/final control and is never a founder or selection nominee.

## New datasets and split discipline

Exclude all170840 prior whole layouts through L. Pools freeze before fixture
construction; all fixture layouts are excluded from main. Generate calibration,
validation and final with independently namespaced seeds, checking whole layouts
including all D4 poses and unqueried matched cases. Save every accepted layout.

Carry calibration and validation:9independent25×25templates, three goal shapes
(straight/symmetric/asymmetric) ×prefix1straight/2straight/4bent, long6–9edge tails.
Use L's graph constructor for matchedfork/two-junction/realalternativecycle,
pruned corridors and disconnected controls. Save both exact translated locations
and all8poses. Calibration queries centredlocation poses0/4 only:180inputs/54branch
pairs,36corridors,36disconnected per candidate. Validation queries centredlocation
poses0/2/4/6:360inputs/108branchpairs,72corridors,72disconnected per nominee. This is a new sample of an
L-informed grammar; no general-maze claim. Final uses12templates, addingprefix8
straight, and alternates the queried centre/off-centre location by template index,
with the same four poses:480inputs/144branchpairs,96corridors,96disconnected.
All unqueried variants are still saved and excluded.

Fresh calibration and validation: six independent9×9templates, adjacent goals,
two-edge arms and two-edge shared-prefix forks, each in two orientation/shape
forms. Every template includes six isolated clutter cells, paired goals, matched
pruned corridors, and two unreachable goals on isolated cells. Disconnected
controls deliberately share the paired layout with different goals; both endpoints
remain open. Save8poses, query0/2/4/6:144inputs/24paired tasks,48corridors and48
unreachable inputs. Final has four new templates per stratum (24total), all8poses:
1152inputs/192paired tasks,384corridors,384disconnected. Adjacent tasks alone are
not evidence of nontrivial path propagation.

The templates are independent units. Poses, translated copies, goals and graph
variants are correlated. Holdout is generated only after every choice is frozen.
No main fixture/model/selection choice may be revised from inspected scores.

## Rank, simulated selection and validation

Use one common paired-first rank: complete shortest goal pairs, individual
shortest outputs, individual legal outputs, correct no-path minus false no-path,
then summed bidirectional partial credit plus twice each pair's weaker partial.
No work tie-break while correctness is incomplete. Digest then identity resolves
rank ties. These are explicit M calibration choices, not a claim to reproduce all
previous selection policies. The ordinary-output partial score is unchanged;
BFS/oracle labels are evaluator-only.

Apply the same selection function to each fixed pool: top quarter as elites,
**top two nominees**, and64lexicase parent draws using a common starting RNG across
arms. Lexicase fields: paired correctness, shortest/no-path, legal/no-path, partial
plus weaker paired partial; epsilon.02 only on partial. Repeat these simulated
choices with partial credit zeroed on the SAME saved evaluations. Save ranks,
identities, RNG before/after and parent draws. This measures activation of actual
selection routines; it is not a bred or evaluated next generation.

Evaluate two nominees per pool/arm on a NEW validation corpus with equal budgets
across arms (carry validation has twice its calibration pose coverage), choose
one by the same rank/digest, freeze/push it. Final evaluates all four selected
arms; the selected active program additionally under neutral/zero/local exposure;
and the original unedited foundation (fresh founder0 for fresh pools) under
neutral/zero/local. These extra diagnostics do not feed selection. Physical
aliases can reduce calls but not logical selector budgets. Include a separate
intact solver and compiled BFS/A*/bit-wavefront on every queried final input.

## Gates declared before scientific calls

Software gate: all parity/bounds/mutation tests pass. Preflight profiles every
physical model on pose0 of every eligible fixture stratum at production board
sizes/dtypes. Twofold carried and fourfold fresh full-pool inference projection plus an intentionally
conservative validation projection (eight nominees per pool times the slowest
profiled model rate) must be <432candidate seconds. Final projection uses ten
physical-model slots per pool times the slowest rate and must be <270seconds.
These are projections, not guarantees; no score affects scope or pool membership.

Carried pilot screen: broad Branch has at least16/64 different active-versus-neutral
parent identities, changed elite and nominee sets, and at least one candidate with
changed masks. On final, its selected active program gains at least4pairs versus
that SAME program under neutral exposure, across at least2independent templates
and2goal forms, with zero lost normal pairs/corridors. Additionally, selected active
K2target/local_long/68-gene foundations must retain every paired/corridor success
of their original all-on bases on identical final inputs. Report zero-opportunity
far retention as vacuous. This is a narrow calibration gate, not two independent
evolutionary replications or a general solver screen.

Fresh gradient screen, per replicate/arm: at least8founders have mean two-edge
paired-input partial>.10, best mean≥.15, shaping changes≥16/64parent identities
and the elite set, and shaped parents' mean exceeds uniform-founder mean by≥.02.
The .10 endpoint-only contribution is insufficient by itself. The fresh pilot
screen needs at least2/3NEUTRAL replicates to pass that gradient screen and also
show either a final two-edge complete pair or≥.02mean two-edge partial gain over
fresh founder0 under neutral exposure. Report all other arms, complete adjacent/
two-edge outcomes and failures. This tests a usable elementary starting gradient,
not evolution or discovery. A failed gate must not be relaxed after observation.

All-off parity is suppression. A selective nonzero mask is not beneficial
communication unless its SAME program loses normal successes with all nonlocal
values zeroed and yields a better net outcome versus fixed-zero/local controls.
No latency/speedup claim. Later60–90min search still requires a separately frozen
bounded pilot and held-out gains in≥2/3independent evolutionary replicates with
protected-skill retention. No evolutionary pilot launches automatically in M.

## Performance-only revision before registration

The original fixture profile projected310.125seconds for four calibration poses
plus140.176seconds conservative validation work, exceeding the fixed432second
preflight threshold. It PASSED no scientific performance screen and generated no
scientific case. Preserve `calibration.json` and its log as the failed timing gate.
The prospective protocol now queries only poses0/4 for CARRIED calibration;
validation/final and fresh queries, every pool/model, all arm comparisons and all
readiness thresholds remain as specified above. Derive `calibration_revised.json`
from the exact saved per-model timings, with no extra candidate call and no score
inspection/reselection. Freeze both records before main generation. This is a
pre-registration computational scope revision, not a post-registration deviation.

## Hard caps, preservation and audit

Fixture profile/parity cap240candidate seconds/130000calls, separately recorded.
Scientific calibration+validation cap480candidate seconds/600000physical calls;
final cap300candidate seconds/exact planned calls, **13candidate minutes maximum**
combined, plus separate software checks/audit.4GiBRSS and2GiBoutput allowance.
Save partial evidence and stop on any cap; no rerun or extension. Warm-ups use
production read-only arrays and are separately reported. Preserve all raw masks,
base and exposure counters, aliases, programs, RNG, choices and discarded nominees.

Audit frozen sources/inputs and every prior completion packet; regenerate all
accepted corpora, independently grade graph labels and rasters, replay every raw
profile/normal/parity/baseline response and work count, reproduce random founders,
mutations, both simulated selection policies, validation choices, final aliases
and exact coverage. Report audit time/RSS separately. Tests regenerate saved
fixtures only, so no hidden extra unit-geometry layouts enter the exclusion set.
