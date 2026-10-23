# Proposed M32 A1: export-only recovery — awaiting user approval

M32 completed62generations and its last811-case development assessment, within
the30minute search ceiling. It then failed before exporting choices because the
registered `freeze()` passed `role` explicitly and again through `**c`.
All6,882,689completed native search evaluations/11,628receipts, final checkpoint,
RNG states, saved nominees and chain remain intact; no pending/uncertain tasks.
Original source measurement and its ALL-native audit passed. Search audit and
independent descendant confirmation have NOT run. No final cases were generated.

This is an implementation error in serialization, not evidence of an evolutionary
failure or permission to rerun the search. The original registered source,
journal, traceback and FAILED workflow status remain immutable. Verified
SQLite-API backups and a failure seal preserve every table/settings/receipt.

## Concrete proposed change

Use a NEW gated exporter `tools/m32_export_recovery_a1.py`. It copies the18exact
already saved nominees, their ancestry closure and final states. The only logical
export fix is to attach population/replicate/arm to `c`, allowing its existing
`role` key to appear once. No nomination, variation, RNG advancement, genome
editing, inference or maze generation occurs in the exporter. Draft payloads and
semantic hashes are in results/repair_evolution_m32/recovery_a1/rehearsal/ and
rehearsal.json. The rehearsal reproduces the original TypeError, checks the fixed
serialization round-trip, verifies original journal SHA unchanged and rejects
unapproved apply. Gzip headers can differ; decoded payload hashes must match.

After explicit approval, register/push A1 code/protocol/rehearsal and exact payload
hashes, with user_approved=true. Finish these exports and metadata-only
search_session.json; leave the original SQLite journal bytes/settings unchanged,
including its absent finished flag. Charge the conservative original search
subprocess interval1655.456024seconds plus rehearsal/export time against the
existing1800second ceiling. Inactive user-decision time is not computation; no
ceiling extension or extra evolutionary round is permitted.

Publish exact choices/ancestry/states/session BEFORE any independent final case.
Continue the originally registered ALL-native search/selection/variation/RNG
audit, original fresh-final generator/seed/cases, final analysis and ALL-native
audit under the same bounds. A NEW recovery workflow/status preserves the
original FAILED status and does not invoke search again. Source measurement/audit
will not be repeated. Any new guard/audit/error stops; no automatic failed resume.

Existing unregistered reporting/preservation helpers may be adapted to read the
separate approved recovery status and timing, preserving any failed packets and
raw summary. No registered scientific source is edited. The known queried-only
denominator interpretation and invariant endpoint checks remain unchanged.
Review/report/preserve/seal/publish using the original endpoint, fixed roles,
losses and limitations. No M33 or further evolution is authorized by this proposal.

## Preservation detail

The failure preservation helper included its own redirected stdout log before
printing its final success line. The original failure seal remains unchanged;
stdout_seal_addendum_001.json seals that one completed administrative log. All
scientific files/journal bytes and every other sealed local record match exactly.
This additive log correction changes no scientific record or result.
