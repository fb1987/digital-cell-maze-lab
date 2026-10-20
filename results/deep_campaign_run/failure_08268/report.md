# Deep campaign stop at 8,268 rounds

October 20, 2026. **Stopped; no restart or protocol change has been made.**
The heartbeat `deep-maze-search-follow-through` is paused pending a documented
generator amendment. This is a software/design capacity failure, not an
organism-performance stopping gate or a compute-budget stop.

## What happened

All three islands completed 8,268 replacement rounds. The next call was
`batch(config['seed'], 'train', 8268, previous, [2, 2, 2])`, constructing inputs
for the round that would advance the populations to 8,269.
`ordinary_training` raised `RuntimeError('Ordinary training construction exhausted')`
on the second ordinary **perfect** base (`index=1`) after salt 3,999.
The failure occurred before `journal.prepare`, task dispatch, inference,
selection or reproduction for that batch.

Replaying the frozen input constructor against the saved exclusion set
reproduced the same exception. All 4,000 attempted draws were rejected for
layout overlap; none was rejected for endpoint isolation. They represented
3,442 distinct symmetry orbits. The first perfect base had been accepted at
salt 341. The incomplete batch existed only in memory; its diagnostic replay
and exclusion hashes are now preserved separately, without modifying the journal.

## Root cause: insufficient finite topology support

The frozen Wilson generator embeds a 4×4 room grid in a 9×9 raster. Exact
Matrix-Tree calculation and exhaustive topology enumeration agree that this
grid has **100,352 oriented spanning trees**, forming **12,600 distinct
rotation/reflection orbits**. The frozen novelty rule rejects an entire orbit
when any pose overlaps an excluded layout; endpoint changes do not change
layout identity.

At the stopped checkpoint, **12,589 orbits were blocked and only 11 remained
eligible**. The remaining schedule needs **866 training perfect bases plus
96 assessment perfect bases: 962 total**, each previously unseen. Therefore
the registered generator cannot reach 10,000 rounds under its existing
whole-layout novelty rule. Raising the 4,000-draw retry cap cannot fix that
capacity deficit. This does not imply all possible 9×9 mazes are exhausted:
the limitation is the particular 4×4-room perfect-maze family and its exclusions.

`tools/inventory_deep_perfect_support.py` performs the read-only support
inventory. It enumerates tree topologies and hashes only: no endpoint-assigned
test cases, candidate inference, confirmation corpus or journal mutations.
The proposed 11×11 raster / 5×5-room family has **557,568,000** oriented trees,
verified by an exact integer Matrix-Tree determinant; no new cases were generated.

## Preservation and integrity

* No active campaign writer remains; its single-writer lock is available.
* All **255,744 task batches are done**; there are no pending stages or
  incomplete task receipts and zero uncertain/retried attempts.
* All populations, RNG states, genomes, ancestry, archives, input manifests,
  rasters and prior checkpoints remain in the original journal.
* Latest complete stage: **8,284**; generation: **8,268** on all islands.
* Chain: `1f06d3a2ecdf38224c017b0fa23737cca142bef5678e6bdc62fe8939a3550da5`.
* Saved population checkpoint SHA-256:
  `a91b916899351935a5927c5d2c6f4c8830ccef03b949d060d463d89d31fb82a0`.
* Frozen setup hashes/dependencies, all completed input/receipt/decision-chain
  hashes and all saved population checkpoint hashes pass verification.
* A SQLite backup made with the backup API is preserved at
  `runs/deep_campaign_v1/backups/failure_08268.sqlite`: 6,348,865,536 bytes,
  SHA-256 `62f197a970d62a030db89347733160a719a07479a027b6b71c1d501663c18bfc`.
  Its `PRAGMA quick_check` returns `ok`, and its latest checkpoint hash matches.
  It is a second local copy, not protection against loss of the laptop/disk.
* Original log remains untouched; a compressed copy and exact traceback are in
  this packet. The log SHA-256 is in `preservation.json`.

This is hash/SQLite integrity verification, **not the full registered
selection/mutation/RNG replay** and not a replay of all candidate inference.
The milestone has not been reached, no milestone choices have been frozen,
and no independent confirmation cases have been generated.

## Recorded compute and scientific status

The durable journal charges **30,707,970 candidate calls**,
**13,645,276,223,118 work units**, **39,720.35 summed candidate seconds** and
**41,631.95 summed worker CPU seconds**. Last completed-round log time was
13,164.46 session wall seconds (3h 39m 24s). These are different measures;
worker time is summed across concurrent workers. The final constructor failure,
shutdown and diagnostic/backup time are additional. Because the exception
bypassed normal session closure, `last_session` is null: no completed-session
peak RSS or total process-tree CPU report exists, and neither should be invented.

The common 44-survivor/52-birth schedule implies 1,289,808 births across the
three islands: 1,116,180 mutation births and 173,628 random immigrants. These
are schedule-derived counts, not a substitute for the pending full event audit.
The latest broad assessment is round 8,000; normal training through 8,268 does
not create another broad assessment or a new final nominee.

Round-8,000 primaries still give 104/200 structured pairs and 14/96 ordinary
inputs, matching the protected aggregate reference's successful-case membership.
Retained specialists demonstrate complementary second-junction/longer-prefix
routing and some ordinary multi-junction paths, with substantial losses
elsewhere. No general solver, policy-causality result or speed advantage has
been established. The generator failure does not invalidate those saved
observations, but independent confirmation and ancestral capability comparisons
remain outstanding.

## Recommended repair, not implemented

Prepare and register a clearly named continuation amendment from the **exact
8,268-round checkpoint**, retaining the cumulative journal/history and bounds:

1. Expand only the ordinary-perfect generator from 9×9 / 4×4 rooms to
   **11×11 / 5×5 rooms** for subsequent training and development assessments.
   Keep counts, endpoint-sampling rule, all-pose exclusions and novelty checks.
   Leave structured contexts, random/disconnected families, selection,
   reproduction, runtime limits, founders and RNG history unchanged.
2. Implement through versioned new sources/registration, preserving the original
   frozen files and failure packet. Preflight generation capacity, deterministic
   replay/resume, runtime compatibility and cost on discarded fixtures before
   launch. Retain all existing call/work/memory/storage/session bounds and the
   10,000-round endpoint; do not reset charged usage or extend the milestone.
3. Treat results after the domain change as an explicit new phase. Compare
   candidates and frozen references on the same new panels; do not interpret
   old 9×9 and new 11×11 raw ordinary counts as acquisition. Preserve the original
   observations and full audit obligations.

This changes a registered stimulus distribution and therefore must be documented
before restarting. No implementation, registration or resumed scientific run
is included in this diagnosis. Merely skipping the failing task, recycling
excluded layouts, dropping perfect cases or increasing retry limits is not an
acceptable silent repair.

Future independent exclusions must include the journal's **822,608** layouts
plus **6,079** diagnostic topology/partial-batch hashes not already present:
**828,687 total**. The extra hashes are in `all_diagnostic_exclusions.json.gz`;
the stopped journal itself has not been edited. Preserve them even though no
organism was evaluated on these diagnostics.
