# V12G — minimal fork suppression pilot

Status: preregistration, before any V12G random-origin candidate evaluation.
The user authorized continuation of the V12F proposal. V12F and all older
sources, runs and budgets are closed and immutable. This is a new study.

## Calibration and task grammar

Construction seed **1214**, study seed **2026101902**. All **125,008** older
whole layouts are excluded, then all **2,464** new fixture layouts. Construction
preflight makes 102 base forks, including 96 sampler stress cases. It rejects no
layout collisions. It performs no research candidate evaluation. Its subsequent
six-control calibration evaluates 224 inputs per known control, all separate
from research populations. Intact solves all 192 reachable and 32 disconnected
inputs; damaged controls lose accuracy. 480 synthetic masks verify ordered
credit: blank < connected prefix < both exits < correct-only exit <= full route.

Each stimulus is a 13×13 induced three-arm fork, an interior source, and two
goals on different exits. All eight D4 poses are retained. Source-to-junction
length is 1–2 at stage 0, 1–3 above; goal arms are 1–2, 2–4, or 4–7 edges at
stages 0, 1, 2. Thus shortest routes are 2–4, 3–7, and 5–10 edges. Stage 2 uses
21×21 grids and is withheld from search. Cyclic tasks attach a single loop by a
stem; this can create another junction. “Tree/cyclic” describes the endpoint
component, not all disconnected input cells.

Eight isolated, endpoint-independent background cells are sampled and retained
in both fork and pruned controls. They avoid exhaustion of a finite set of tiny
whole layouts; they are not evidence of novel route topology. Tiny route shapes
can recur. Independent base counts and pose counts must be distinguished.

For every fork-goal input, a matched control removes the competing arms/loop,
retaining the identical full shortest route and eight background cells. These
are paired **single-route controls on different layouts**, not goal-switch pairs.
Their joint completion never counts as completed fork pairs. Disconnected final
controls remove the decision junction from the same fork, separating both goals
from the source. They are diagnostic, not a training reward.

## Frozen comparison and preserved diversity

30 conditions, 96 organisms each: carry/fresh × local/evolved × current/branch
pressure × three replicates (24 evolution conditions), plus six fresh current
resampling conditions (local/evolved × three replicates). Shared founder
populations/RNG across pressure and applicable resampling arms. Fresh local and
multirange populations share random genotype draws within replicate, with no
known solver. “Carry” descends exclusively from the V12C fresh random-origin
track through V12D/E, using V12E Current next-populations/RNG at generation1365.
No V12F final performance selects an entrant.

Carry anchors are the unique validation-selected task/skill/common archives
from V12C, D and both E pressure arms, within replicate/topology. All 9–15 such
anchors remain protected identically in both arms. They replace nonprotected
positions at the tail during setup; exact original populations and replacements
are recorded. Historical V8/V9 primitives remain preserved in their original
packets, outside these fresh-origin lineages. Fresh populations have no inherited
anchors. All conditions protect their four current common validation archives.

Identical runtime and capacity: unchanged V6 goal-pulse VM, eight channels,
256 genes, 256 ticks, 4096 spatial reads/site and 32768 dispatches/site. Public
endpoint flags and endpoint-aware halting remain. No path oracle enters inference.
24 elites include anchors/archives, then the best and behavioral diversity.
Evolution births comprise nine random immigrants and 63 single-edit mutants;
resampling has 72 independent random draws. Parents use 10% uniform draws and
90% lexicase. Full genome, ancestry, population and RNG states are preserved.
This shared elite policy and task distribution differ from V12E: only the two
V12G pressures provide a pressure-only comparison.

## The one pressure contrast

Current ranks (valid routes, shortest routes, correct no-path minus false claims,
complete fork pairs, constant zero, original bidirectional partial sum, work).
Branch replaces only the zero/partial fields with (strict-both choices, branch
score sum). Normal correctness and completed fork pairs still take precedence.
Last-field lexicase tolerance is .02; earlier fields are exact. Case ordering
adds the strict-pair field in the same position. Current's constant zero field
consumes no RNG and cannot filter parents.

For each fork, P is reached shortest incoming-prefix fraction after outgoing
exits are blocked, D indicates exactly one shortest desired exit illuminated,
L is the fraction of wrong exits illuminated, and S is unchanged old partial:
**B=.2P + .4PD + .35PD(1−L) + .05S**. Strict choice requires reaching the junction
by its shortest incoming path, D=1, and L=0. Pair shaping uses individual B plus
the minimum B over its two goals. Corridor shaping remains original S.
Strict choice alone need not be a completed or emitted legal path.

Every generation uses a new shared base per replicate: stage0 on 3/4 rounds,
stage1 on every fourth; cyclic on rounds congruent2 mod4, tree otherwise.
Two fork poses p=(generation+replicate)%8 and p+4 (mod8), plus their two matched
single-route controls at pose p: six input responses per organism. Validation
per replicate has four independent base groups (stage0/1 × tree/cyclic), all
fork poses and every other corridor pose, totaling96 inputs. Four nominees
are validated every eight generations. Common archives in both arms are pair,
choice, task and corridor. Primary is the **pair archive**, evaluated on fork
rows only, ranked complete pairs, shortest, valid, no-path, strict pairs, B, work.
Choice archive is prespecified secondary, never promoted on final performance.

## Budget and extension gate

Exactly one bounded pilot: **720 seconds total search wall budget**, including
initial validation, data construction and saved checkpoints; maximum256 matched
generations. Initial physically identical validation is evaluated once per
origin/topology/replicate, with explicit archive aliases for the other pressures
and resampling; it is not charged multiple times. No automatic budget extension.
A round starts only if elapsed plus 1.25×longest observed round plus3 seconds is
below720; the first reserve is40.5 seconds. A slow final round may finish rather
than invalidate matching; any overrun is reported. Stop at2GiB saved search data
or4GiB RSS as additional guards. Calibration, compilation, confirmation and
audit time are separately reported. Rotate condition order each round.

A larger future run is justified only if the branch primary archive, in at least
2/3 replicates of one origin/topology cohort, completes ≥8 validation fork pairs,
spanning ≥2 bases including ≥1 base complete in all eight poses; exceeds its
matched Current and frozen primary by ≥4 pairs; and retains ≥90% of its frozen
primary's corridor successes (zero baseline is automatically retained). Fresh
must also exceed resampling by ≥4 pairs. These are validation criteria, not a
significance test or permission for an automatic larger run. Repeated data and
poses are correlated. Partial communication cannot pass this gate.

## Frozen final assessment

Freeze and push all primary/secondary/frozen archive identities before generating
any final cases. Shared fresh test:24 base forks (three stages × two families ×
four bases), all eight poses and both goals =384 fork inputs/192 goal pairs;
384 matched corridor inputs;128 disconnected inputs from the eight stage0 bases.
Exclude all old, fixture, validation and training whole layouts. Stage2 is an
untrained length/grid extrapolation test. This pilot does not add an ordinary
large-maze benchmark; prior general-solving failures remain relevant.

Assess pair and choice archives plus their initial frozen counterparts; deduplicate
physical inference by genotype/topology and record every alias. Include intact
known VM and compiled BFS/A*/bit-wavefront separately. For primary selections
with complete final fork pairs only, replay those same pairs with goal pulse off
and with nonlocal values zeroed (read costs retained). These are success-conditioned
causal diagnostics, not new holdouts. Endpoint flags/halting remain.

Time only each primary's first32 successful outputs in fixed final order; three
warmups, five repetitions of ten calls, medians and ranges. Include readonly
input decode, updates and emitted mask; exclude one-time genome setup explicitly.
No failed output enters a speedup ratio. Report real work and memory alongside
accuracy. Timing successes include corridors and must be stratified accordingly.

Audit independently checks every saved search raster, external branch arithmetic,
fitness decomposition, graph labels, D4 transform, and whole-layout exclusions.
Replay every mutation from concrete edits and every recorded reproduction/RNG
transition from verified fitness; the latter reuses production selection code
and is a deterministic replay, not an independent selection implementation.
Replay all final candidate outputs and independently grade all baseline/calibration
rasters. Preserve raw masks, controls, checkpoints and source/input hashes.
