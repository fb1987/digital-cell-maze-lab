# V12V — controlled dissection of two historical mutations

This is an explicitly U-informed fixed mechanistic assay. No evolution, selection,
solver injection, prior-primary replacement or reuse of inspected layouts occurs.
Synthetic probes are labeled as constructed, not evolutionary discoveries.

## Frozen models and questions

Six exact historical nodes: d00, d01, d02, d07, d08, d12. Six controls: fresh2 and
its exact immigrant root, carry1 and broadroot, unmutated random68, and separate
intact solver. Preserve all thirteen U intermediates and their populations/RNG.
Add exactly four one-instruction synthetic variants, with parent/event manifests:

- dest_only: change destination44 to32 at gene103 in d00, retaining the deletion
  site. This completes the 2×2 first-deletion/destination-change experiment with
  d00, d01 and d02. The destination edit must be identical to the historical edit.
- d07_no_store: replace gated output STORE at222 by COPY scratch34 to itself.
  Comparing d07 with this probe removes the store without adding EQ. Comparing
  the probe with exact d08 adds EQ in the store's absence.
- d12_no_store: replace EQ at221 in d12 by the same self-COPY.
- d12_restore_store: replace EQ at221 by the exact historical gated STORE. This
  reverses edit8 in the later background, while all other edits remain present.

All sixteen identities are physically distinct. Programs stay within 256 genes;
exposure7, local topology, native runtime and all per-site limits remain fixed.
The self-COPY is a semantic no-op with a charged dispatch, zero spatial reads and
no change in gene count. Its active-instruction counter can differ from a gated
store. There is no added 257th instruction or uncharged compound operation.
This three-state STORE/no-op/EQ dissection does not include STORE+EQ simultaneously;
EQ's effect in that untested combination is not identified.

Primary outcomes: complete shortest goal-switch pairs with a positive shared
prefix, gains AND losses, per independent context. Report all pairs, correct
individual outputs, full-eight-pose groups, ordinary/corridor/no-path retention,
status/mask/tick changes and work. Compute destination effects with and without
the deletion and the difference-in-differences interaction. No significance claim
based on treating poses or related variants as independent samples.

## Channel4 test and falsifiable predictions

Only d00, d01, d02 and dest_only receive channel4_zero and channel4_restore.
A separate bounded adapter overrides the final channel4 STORE at108. Zero writes
zero. Restore uses the neighboring old-channel3 minimum already computed by
instruction103, with its original spatial reads/checks charged. It uses the value
in the instruction's actual destination register, so it works in both backgrounds.
No extra neighbor lookup, inferred answer, oracle access, hidden extra step or
stopping change. All other instructions execute. Changes in subsequent execution
and work are measured, not artificially equalized.

Prespecified full-record predictions on every diagnostic input:

| Model | Zero-channel4 prediction | Restore-channel4 prediction |
|---|---|---|
| d00 | dest_only normal | d00 normal (sham) |
| d01 | d02 normal | d01 normal (sham) |
| dest_only | dest_only normal (sham) | d00 normal |
| d02 | d02 normal (sham) | d01 normal |

Compare raw masks, statuses, ticks, validity and counters, with all exceptions
preserved. Predictions may fail; failure does not abort or trigger adaptive
repair. Normal adapter parity is a software requirement, distinct from these
scientific predictions. Forced traces are used only in bounded fixture software
tests to check internal channel semantics, never as experimental successes.
Main and calibration schedules use normal stopping only.

## New corpus and schedule

Seed2026101917; fixture1364. Exclude every233432whole layout through U, then all
new fixture layouts. Use the unchanged corrected T geometry supplier and U query
predicate. Save and exclude all constructed variants, including unqueried cases.
Matched source prefixes0/1/2/4/8 straight and4 bent; fork0, two-junction2 and true
alternative-cycle2; all8poses and both goals; corridors and nonisolated no-path.
Add48ordinary reachable and16partition-no-path independent bases, all8poses.
Contexts/ordinary bases are independent units; poses/goals/variants are correlated.
Shapes and tail lengths remain confounded. No training corpus in this assay.

Fixture: four contexts, one per shape; query pose0 only for calibration.
Final: choose12contexts (3per shape), or8 (2per shape), by the timing-only
pre-registration feasibility rule below. All native inference finishes before
interventions. Diagnostic subset is fixed to variant0 in each of the four shapes,
plus all ordinary cases:2368inputs/model. It is not filtered by model success.
All16models receive every normal input. All4early models receive both interventions
on every diagnostic input. All fixture normal inputs additionally receive adapter
parity. Three compiled baselines receive every queried input; intact is separate.

If12contexts:6080native inputs/model,1728pairs (1440positive),1152corridors,
960structured no-path,384ordinary reachable and128ordinary no-path. Native97280
+18944diagnostic =116224main calls. If8contexts:4224native inputs/model,
1152pairs (960positive),768corridors,640structured no-path,384ordinary reachable,
128ordinary no-path. Native67584+18944diagnostic =86528main calls.
Fixture4736native+2368diagnostic+4736parity=11840calls. Warmups logged separately.

## Budgets, registration and audit

Main cap720candidate seconds,400000calls,2trillion read+dispatch+exposure-check
work,4GiB RSS,2GiB artifacts. Calibration180candidate seconds separate. No closed
cap extension. Warm JIT signatures match readonly maze bytes and production arrays.
No latency-race claim; report candidate and wall seconds, data/output and work.

Before any final generation, calculate native fixture structured cost×(8×repeats),
native ordinary cost×8, diagnostic cost×8; exclude separately logged adapter parity
from the main projection. Multiply total by2 for safety. Choose the first of
3then2 repeats per shape whose projection is below650seconds. No fixture score
influences models, contexts, modes or schedule. If neither fits, stop and preserve
calibration. Freeze source/protocol/tests/panel/fixture records, commit and push,
then generate final. Any later source repair must be disclosed and original kept.

Audit all prior completion hashes, exact historical and synthetic probe programs,
all new corpus geometry and exclusions, every fixture/final candidate response and
baseline, independently graded masks, normal parity, schedules and cost totals.
Independently tally the signal-equivalence predictions from raw records; recompute
all prespecified analysis. Preserve masks/counters and exact exceptions. Scientific
completion follows the full audit, report and consolidated layout exclusion seal.

Next research design depends on whether the restoration and store decomposition
work. Neither a large evolutionary run nor recombination enhancement is automatic.
