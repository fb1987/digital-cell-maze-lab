# Deep campaign progress

The user authorized the scientific launch after reviewing the prepared protocol.
The campaign started **2026-10-20 at 14:30:25 UTC** from frozen commit
`7854ada78b70b445e52816ed1e0869265bb5c6f2`. The registered source and configuration
passed verification before launch. No protocol changes were made.

The detached process runs under `caffeinate -i -s` with 10 worker processes.
The initial process ID was 33545; verify the current process and writer lock
rather than assuming an old PID remains valid.

* Scientific journal: `runs/deep_campaign_v1/campaign.sqlite`.
* Session log: `runs/deep_campaign_v1/session_001.log`.
* Launch record: `results/deep_campaign_run/launch.json`.
* Initial development assessment: `results/deep_campaign_run/initial_assessment.json`.
* Frozen design: `docs/DEEP_CAMPAIGN.md`.

The round-zero broad assessment completed and reproduction began successfully.
The first observed populations remained at prefix frontier one. The initial
assessment measures preserved founders, so it is not evidence of newly acquired
campaign abilities. Later 500-round assessments must compare descendants and
frozen references on the same panel; raw counts across different panels are not
paired gains.

Read live progress without touching the writer:

```sh
.venv/bin/python -m maze_evolution.deep_campaign status
```

The thread heartbeat `deep-maze-search-follow-through` checks every 15 minutes.
It stays quiet on routine progress and reports meaningful capability changes,
completion, failure or required user action. It may resume the same journal after
a normal session-wall stop, within the unchanged registered bounds. It must not
bypass other resource guards or launch a concurrent writer.

At 10,000 rounds, preserve and commit/push the frozen choice packet before any
confirmation generation, run the registered reproduction/RNG audit, preserve the
journal and report the actual results and costs. A separate bounded protocol
still governs independent confirmation. No general-solver or speedup claim has
been established by this launch.
