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

## First 500-round assessment

Checked October 20 at 14:50 UTC; the live run had reached round 770 with no
uncertain/retried evaluation batches. Observed process-tree RSS was 1.90 GiB,
run storage 0.58 GiB and free disk 63.4 GiB. The writer remains active; no restart,
configuration change or additional candidate inference was performed by this check.

The round-500 development panel has 200 complete-pair opportunities, 96 ordinary
reachable inputs (48 independent bases in two poses), 100 corridors and 52
disconnected inputs. All three islands advanced to frontier two. This requires
two passing assessments but does not itself demonstrate acquired ability:
preserved genomes can satisfy the promotion rule.

| Island | Primary pairs | Best protected reference pairs | Primary ordinary | Best protected ordinary specialist |
|---|---:|---:|---:|---:|
| 0 | 104/200 | 104/200 | 13/96 | 15/96 |
| 1 | 104/200 | 104/200 | 13/96 | 15/96 |
| 2 | 104/200 | 104/200 | 14/96 | 15/96 |

All three primaries are exact inherited B individuals already in the starting
populations. Their ordinary results therefore cannot be attributed to this
campaign. The best protected aggregate reference gives 13/96 ordinary outputs;
the stronger ordinary specialist is a different genome. No aggregate gain is
established at this checkpoint.

There are complementary observations worth preserving. Island-zero descendant
`deep_v1/island0/i23031` (born 443) completes one prefix-eight fork pair missed by
the union of 20 protected references on this panel, but completes only 92/200
pairs overall. Descendant `deep_v1/island0/i25021` (born 482) completes two
prefix-four fork pairs missed by those references, with only 61/200 total pairs.
Both are retained in the behavioral archive. Some descendants also cover ordinary
cases missed by the protected references.

These are new descendants with complementary development-case coverage, **not
yet demonstrated acquisition relative to their exact ancestors or all 96 starting
genomes**. Protected-reference novelty is not novelty relative to the whole
founder pool. Likewise, some no-path coverage already exists in unprotected
historical founders; it must not be labeled a new campaign discovery. Some
archived variants trade successes for false no-path claims, which remain failures.

Full same-panel metrics and successful-case differences are saved in
`results/deep_campaign_run/assessment_00500.json`. The read-only helper
`tools/inspect_deep_campaign.py GENERATION --save` verifies input, receipt and
checkpoint hashes, recomputes capability counts from saved outputs, and performs
zero inference. The complete journal remains authoritative. Continue the frozen
campaign; no intervention or new confirmation is justified by this routine check.

## Round 1,000 development assessment

Checked at 15:03 UTC with the active run at round 1,231. No uncertain/retried
batches; observed process-tree RSS 1.53 GiB, storage 0.90 GiB, free disk 63.1 GiB.
All islands remain at frontier two. The frozen source/configuration and completed
assessment input, receipt and checkpoint hashes verified. No new inference or
search intervention was performed by the monitor.

All three primaries complete **104/200 pairs and 14/96 ordinary inputs**, exactly
matching the successful-case membership of the best protected aggregate reference
on this panel. Island two now selects descendant `deep_v1/island2/i51960`, but its
selection is supported by partial-score differences, not additional correct
outputs. The other primary identities remain inherited B variants.

The strongest ordinary specialists in islands zero and one reach 18/96 versus
14/96 for the best individual protected reference. However, all those successes
are covered by the union of protected references, and island one's selected
ordinary specialist is inherited B individual `selectivity_v13b/carry/1/current/i610`.
This does not establish a new campaign capability. Island two's best ordinary
score remains 14/96.

Complementary prefix-four/eight fork cases persist among archived descendants.
Some other descendants combine paired routing with correct disconnected-case
responses and no false reachable no-path claims on this panel. They remain
specialists with substantial reachable-case failures; acquisition relative to
their exact ancestors or the complete founder pool has not been tested.

Saved summary: `results/deep_campaign_run/assessment_01000.json`. Current evidence
does not warrant a user alert or protocol change. Continue the registered run.
