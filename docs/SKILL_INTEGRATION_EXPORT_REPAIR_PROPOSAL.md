# M25 export recovery proposal — awaiting user decision

The registered search ended normally after 319 new rounds, at cumulative generation
562. Its final assessment is complete. Export then raised `FileNotFoundError` for
`results/skill_integration/exclusions.json`. No audit or independent confirmation
started. This is an export failure, not a completed and audited experiment.

The config and journal correctly reference `registered_exclusions.json`. The
registered `write_layouts` function instead expects a compatibility manifest named
`exclusions.json`. Both preparation pipeline and runner rehearsals explicitly created
that compatibility manifest in their temporary output directories; production setup
did not. That difference allowed the missing production prerequisite to escape the
rehearsals. The existing 420 registered hashes remain unchanged.

The original journal, failed workflow status, complete traceback and partial exports
remain intact. A verified SQLite-API backup under both writer locks matches every
row of every original table. Integrity checks pass. The checkpoint hash chain
verifies, all 22,188 tasks are done, no tasks or receipts are pending, and all 18
exported nominee choices and the six exported final states match the final checkpoint.
This verification does not substitute for the registered full search audit.

Preservation evidence is in
`results/skill_integration/failures/export_001/preservation.json`. The original
3,742,313 layouts plus all 208,912 search layout deltas are preserved in a verified
reference export there: 3,951,225 excluded whole layouts in total. The immutable
historical manifests and parts remain required. No confirmation cases were generated.

Proposed recovery, only after approval:

1. Register and push an export-only A1 recovery packet and its explicit workflow.
   Preserve the original failed workflow, source registration, partial exports and
   failure backup. Do not invoke the search runner or select different nominees.
2. Add the missing compatibility manifest as an exact reference to the registered
   layout base. Require equality of the full layout sets and base hashes. Existing
   registered scientific source, configuration, founders and selection remain intact.
3. Replay the existing freeze function into captured values and compare all values
   with the already written choices, ancestry and final states. Do not overwrite
   those exports. Write only the missing search layout export and completion/session
   metadata from the exact stage-339 checkpoint. Mark export completion only after
   these checks. Charge recovery work and elapsed time against the unused portion of
   the original 90-minute search ceiling; never reset or renew that allowance.
4. Publish the complete choice freeze before generating any fresh confirmation.
   Run the original full search audit, then the already authorized 1,680-input
   confirmation, analysis and full native final audit under their original limits.
   A separate recovery status/log records these actions; the failed status/log stays
   immutable. Postprocessing helpers may read the recovery status after its audits.
5. Preserve, review, report and seal the actual results under the original protocol.
   No extra evolution, case generation, reselection, new operator or new phase is
   part of this recovery. Stop again on any error, guard or failed audit.

No repair action has been executed. The pause is required by the registered
[M25 protocol](SKILL_INTEGRATION.md): “Any guard/error/audit failure preserves
tracebacks, pending receipts and artifacts for diagnosis and protocol decision
before any repair/resume.” The follow-up also explicitly forbids automatic failed
workflow resumption. This proposal concerns completing exports and the original
audits/confirmation from preserved data, with no further evolutionary search.
