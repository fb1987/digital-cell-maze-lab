# V12F — independent confirmation of the preserved longer-route primitive

Protocol fixed October 19, 2026, after construction-only preflight with seed
1204 and **before candidate inference or generation of confirmation layouts**.
The source, protocol, fixture packet and exact genomes must be committed and
pushed before the `run` command permits the study to begin. This follows the
user-authorized V12E recommendation; there is no further evolution here.

## Question and frozen models

Does local genome `foundation_study/local/fresh/evolution/1/i72095` (born 858,
digest `aff6fc1a635d3c279d26`) transfer to longer, goal-switched maze tasks, and
does goal information alter useful propagation before endpoint-aware emission?
Its already inspected V12E 9/24/25-edge tree outputs motivate the question but
are excluded from this confirmation. Freeze it, immediate parent `i72029`,
original V12D local/fresh/evolution/r1 champion, and the final V12E Paired/local/r1
primary. Include intact wavefront and compiled BFS as separate known controls.
The exact IDs, full genotypes, lineage events and input hashes are in `models.json`,
`lineage.json` and `freeze.json`. Verify the target mutation from its parent.
No mutation, training, ranking, archive changes or model replacement is allowed.
This tests one lineage, not an independently replicated evolutionary effect.

## Fresh cases, fixed after construction-only preflight

Study seed **2026101901**; construction seed **1204**. Exclude all **124,392**
previous whole layouts through V12E, including old fixtures and unqueried
ordinary symmetries. Also exclude all new software fixture orbits. Reject
whole-layout overlap regardless of endpoints. Save the complete new D4 orbits.

There are **48 independent reachable bases /384 paired poses /768 inputs**:
2 families × 3 distance bands × 2 endpoint strata × 2 bearing strata × 2 bases.
Every base is tested in all eight rotations/reflections. Both goals in each
pair lie in the same band. Both endpoints are reachable from the same source;
they have disjoint sets of ALL shortest next exits at a shared prefix vertex
1–6 edges from the source, with at least two remaining edges to each goal.

- Tree family: Wilson spanning trees on an odd-coordinate lattice.
- Cyclic family: independent open probability .72 on an interior obstacle grid;
  explicitly require a cycle in the source component. Both families have a
  closed outer rim. These are intentionally new generators/distributions.
- Distance bands 4–8, 9–16 and 17–32 edges; dimensions 17, 17 and 33 respectively.
  EVERY shortest path must require at least 1, 2 or 3 turns respectively.
- Placement: half have source distance one from the outer rim; half have all
  three endpoints at least three cells from it. Goals in the rim-source
  stratum have no further boundary requirement.
- Bearing: half require at least one goal's EVERY shortest exit at the labelled
  junction to move away from that goal in Manhattan distance; the other half
  allow a toward-goal shortest exit for both goals. This is a junction bearing
  constraint, not a requirement at the source.

Add **four disconnected bases /64 inputs** (two unreachable interior goals per
source, eight poses); the separating column is transformed with the layout.
These controls are reported separately. They do not count as route successes.
Do not repair the dataset based on candidate performance. Construction failure
stops before inference; any necessary deviation must be separately documented.

## Runtime, primary outcomes and transfer screen

All four random-origin models use unchanged V6 pulse/local inference, eight
uint16 channels and at most 256 genes; no nonlocal reads are enabled. Limits:
1024 steps, 8192 reads/site, 131072 instruction dispatches/site, 65536 cells.
Normal input-to-full-raster outputs alone supply primary legality, shortestness,
complete shortest-pair counts, false no-path claims, steps, work and payload.
Report every model, band, family, placement and pose; group by independent base.
Intact wavefront uses the same pulse convention. BFS is only a reference/oracle.

The target passes the **exploratory transfer screen** only if its normally
emitted paired shortest successes at distances 9–32 span, in EACH family:

1. At least three independent base layouts.
2. At least one base successful in all eight paired poses.
3. At least one successful interior-endpoint base and one misleading-bearing base.
4. At least one successful base in the 17–32-edge band.

All criteria apply to the frozen target. Controls cannot substitute for it.
No significance claim is attached to this deliberately small screen. Report
partial evidence even if it fails; do not treat poses as independent replicates.

## Mechanism interventions (prespecified, secondary)

Run the target on every input with: pulse removed / static goal flag retained;
flag removed / pulse retained; both removed; and ordinary inputs with the
endpoint checks removed from the runtime stopping policy. The last control
emits on source stop request plus source output, without checking output at the
goal; its quiescence rule likewise uses source output alone. Other instruction
semantics, quiet-four rule, caps and costs stay identical. These are alternate
runtime responses, not primary accuracy under the native interface.

For ALL 768 reachable inputs, additionally record all eight channels at EVERY
completed tick 1–96 under forced-time execution, for normal/pulse-off/flag-off/
both-off input variants. Disable BOTH endpoint stopping and quiescent stopping
for these probes; retain instruction/read caps and costs. Save raw losslessly
compressed trajectories, not just illustrative outputs. Static goal flags are
explicit in every variant. A forced-time path is never counted as a normally
emitted route. Record trajectory memory separately from substrate payload.

At fixed ticks 8/16/32/64/96 and over the full recorded trajectory, compare
switched-goal output rasters and source/junction states. A strict exit choice
requires exactly one permitted shortest exit, every other exit off, and a
source-to-junction output connection of shortest prefix length with outgoing
exits removed. Report both-goal choices at the SAME tick, and separately choices
strictly before the earlier normal emission (or stopping time) for that pair.
Compare these diagnostics across input interventions. Establish whether emitted
successes also exist at their emission tick in the forced trajectories, and
whether removing endpoint checks changes emission. Do not infer a general
routing algorithm merely from pulse dependence, state change or any one success.

## Cost, audit and preservation

Hard candidate-inference allowance: **600 seconds total**, with no extension.
Each call is independently step/work/memory bounded; reserve at least five
seconds (or twice the longest observed call) before starting another call.
Stop and preserve an incomplete packet if the reserve is exhausted. Count all
normal, intervention, trace and repeated timing VM calls, including the intact
control. Setup/JIT, construction, grading, compression and the separately
reported replay audit are outside this allowance. No cloud or API inference.
Warm on saved software fixtures with production bytes/readonly-array signatures.

If successes exist, benchmark the first two target successes in manifest order
per band/family, never select by speed. Use 31 warm repetitions, seeded randomized
method order, full bytes-to-raster inference; compare target, intact VM and BFS,
verifying all timed outputs. Report all samples, medians and ranges, conditional
on success. Model construction/JIT are separate; VM budget-wrapper overhead is
included. No inference of speed for failed tasks or overall solving superiority.

Independently check exclusions, transformed labels, true cycle rank, mandatory
turns across shortest paths, target-parent reproduction, hashes and all saved
normal rasters. Replay every distinct normal response and every trajectory;
compare standard adapter outputs to the unchanged runtime and forced states to
the established observer where applicable. Independently grade all recorded
trace rasters as geometry only. Run focused semantics, cap and isolation tests.
Preserve the complete packet and historical populations/RNG without modification.
After final inspection, no retuning, reselection, new holdout or extended search
is allowed within V12F. A subsequent experiment requires a new protocol.
