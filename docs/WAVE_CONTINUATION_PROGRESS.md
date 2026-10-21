# M3 wave-lineage evolution — live handoff

Launched October21,2026 at09:39:53UTC from registered/pushed commit302cab5.
The user's authorized60–90minute continuation is active with ten local workers.

- Workflow initial PID14955; search initial PID14964; caffeinate PID14956 prevents
  idle sleep only while the workflow lives.
- Journal: `runs/wave_continuation_m3/campaign.sqlite` (scientific data, preserve).
- Workflow: `tools/run_m3_workflow.py`; status under the run directory in
  `workflow_status.json`. Separate logs for search, audits, confirmation/analysis.
- First search log `search_001.log`; outer failure log `workflow_001.log`.
- Launch metadata `results/wave_continuation/launch.json`.
- Read-only status: `.venv/bin/python tools/inspect_wave_continuation.py`.
  Add `--assessment N` for same-panel nominee/frozen/protected comparisons.
- Heartbeat `m3-wave-evolution-follow-through` active every15minutes; quiet on
  routine progress. Old deep campaign monitor stays paused.

Initial assessment completed, followed by six matched training rounds in about27s.
At that checkpoint237,072 completed/charged physical calls,128.22 summed candidate
seconds, sample peak1.99GiB process-tree RSS. No uncertain attempts. These are
launch checks, not final totals. Initial same-panel reference packet is
`results/wave_continuation/initial_assessment.json`; explicitly development data.

The sealed design retains six protected wave/reference genomes and allows neutral
variants. Three pairs compare single versus mixed one/two generic mutation
opportunities. Same48-query training rounds and392-query fixed nomination panel.
See the registered protocol for exact strata, novelty/retention gates and bounds.
The soft target is70minutes before further train admission, with a final
assessment under the90minute cumulative hard ceiling. Audits and fresh confirmation
are separate work. Do not extend time/call/work/storage guards or reset history.

The workflow publishes exact choices and selected ancestry before generating
confirmation, requires the search audit to pass, then evaluates the registered
1,680-query fresh panel and replays every final output. Failure or checkpoint at a
hard guard stops the workflow for inspection. Never start another writer because
progress appears slow. Preserve failed attempts and do not edit registered files.

After both audits pass, review actual capabilities, longer-route strata, root and
protected-union novelty, retained losses, no-path behavior, ancestry and resource
costs. Produce a report, guarded SQLite backups and whole-layout exclusion union,
seal evidence and commit/push. Do not claim general solving or policy causality
from training changes or shared ancestral replicates. No new search phase follows
automatically. Pause the heartbeat once reporting/audits/preservation are complete.
