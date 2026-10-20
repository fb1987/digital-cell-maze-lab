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

## Round 1,500 development assessment

Checked at 15:17–15:22 UTC; the active run reached round 1,942 during inspection.
The writer remains active with zero uncertain/retried batches. Observed
process-tree RSS was 1.49 GiB, run storage 1.40 GiB and free disk 62.5 GiB.
Frozen setup hashes verified. All islands remain at frontier two. No source,
selection, budget or inference changes were made.

The three primaries still complete 104/200 pairs and 14/96 ordinary inputs,
with the same correct-case membership as the best protected aggregate reference.
However, island two preserves an interesting ordinary/no-path specialist:
`deep_v1/island2/i51989`, born at round 1,000 and retained in the behavioral archive.

| Same round-1,500 development panel | Specialist | Best individual protected reference |
|---|---:|---:|
| Ordinary reachable inputs | 20/96 | 14/96 |
| Complete structured pairs | 26/200 | 104/200 |

The specialist's ordinary successes span ten base mazes in two poses each.
Seven successful ordinary inputs are missed by the union of all 20 protected
references. It also correctly reports all 52 disconnected inputs, makes zero
false no-path claims on reachable inputs, and solves all 100 corridors.
Its paired successes are 24 source-at-junction fork pairs and two
source-at-junction second-junction pairs; it solves no positive-prefix pair.
This is a substantial tradeoff, not an aggregate winner.

One successful ordinary base has a **14-edge shortest route with an internal
degree-three branch junction**, ten edges from the source and four from the
goal. Both poses succeed. The output contains exactly the 15 route cells in
a 31-cell connected component. The eight- and nine-edge successes on two
other bases have no internal branch junction. The 14-edge case therefore
demonstrates more than a long corridor on this panel, but remains one base
in two correlated poses, without a matched goal-switch test.

All 648 saved outputs for this specialist were independently regraded;
successful ordinary masks and geometry were checked against the oracle paths.
Its campaign ancestry contains 789 mutation births, replayed exactly back to
initial B founder `selectivity_v13b/carry/2/current/i238`. Its genotype does not
match any of the 288 initial genomes. These facts establish a changed descendant,
**not functional acquisition attributable to those mutations**: exact ancestors
and all initial genomes have not been compared on this panel. No additional
candidate inference was performed.

This is promising retained specialist coverage worth reporting, with unchanged
limitations: assessment cases are development/selection data, protected-reference
novelty is not full-founder novelty, and no general solver or speed advantage
has been demonstrated. Continue the registered campaign unchanged.

Saved packets: `results/deep_campaign_run/assessment_01500.json`,
`checkin_01500.json` and `specialist_01500.json.gz`. The specialist packet includes
saved successful ordinary rasters/geometry and the exact campaign ancestral
events; lossless gzip round-trip verified. The authoritative journal remains
preserved locally.

## Round 2,000 development assessment

Checked at 15:33 UTC with the active run at round 2,348, all frontiers two and
zero uncertain/retried batches. Observed process-tree RSS 1.65 GiB, run storage
1.69 GiB and free disk 62.3 GiB. Frozen setup and assessment hashes verified;
the monitor performed zero candidate inference.

Primary pair counts remain 104/200 on all islands. Ordinary primary counts
are 13, 13 and 14/96 versus 13/96 for the best protected aggregate reference.
Island two's extra correct case belongs to unchanged initial B individual
`selectivity_v13b/carry/2/current/i1543`, so it is not campaign acquisition.
The strongest ordinary score is 25/96 in every island, matching historical
protected reference `foundation_pair_current/local/fresh/evolution/1/i114696`;
island zero selects a descendant with identical successful-case membership.

The previously reported specialist `deep_v1/island2/i51989` remains archived.
On this different panel it solves 12/96 ordinary inputs (six bases), including
four inputs missed by all protected references, with a longest correct route
of seven edges. It again gives 26/200 pairs, 100/100 corridors and 52/52 correct
disconnected responses with zero false reachable no-path claims. The different
ordinary count is not evidence of regression: the genome is unchanged and the
panel changed. Its earlier 20/96 advantage does not persist against the best
protected ordinary reference on this panel.

Complementary long-prefix coverage persists. Island-one archived descendant
`deep_v1/island1/i100769` completes six prefix-eight fork pairs missed by the
protected-reference union, but only 76/200 pairs overall, two ordinary inputs,
and 20/52 disconnected inputs. Across island-one candidates there are thirteen
distinct prefix-eight pairs missed by the protected references; that union is
not a single organism's ability. These remain correlated development cases,
without exact-ancestor comparisons or independent confirmation.

No new broad capability change or protocol intervention is warranted.
Continue the frozen campaign. Same-panel comparisons and retention details are
saved in `results/deep_campaign_run/assessment_02000.json`,
`retention_02000.json` and `checkin_02000.json`.

## Round 2,500 development assessment

Checked at 15:48 UTC with the active writer at round 2,905. All frontiers remain
two, with no uncertain/retried batches. Observed process-tree RSS was 1.64 GiB,
run storage 2.09 GiB and free disk 61.9 GiB. Frozen setup and completed assessment
hashes verified. No additional candidate inference or intervention occurred.

All primaries still solve 104/200 pairs. Ordinary primary counts are 21, 21 and
24/96 versus 21/96 for the protected aggregate reference. All three primaries
are inherited B genomes; island two's three additional ordinary successes are
not campaign acquisition. Best ordinary scores are 28, 26 and 24/96 versus
24/96 for the best protected ordinary reference on this same panel. Island zero's
28-success descendant has a longest correct route of only three edges; island
one's 26-success descendant solves only 34/200 structured pairs. The higher
ordinary counts do not demonstrate broad solving.

Archived specialist `deep_v1/island2/i51989` retains 26/200 pairs, 100/100 corridors
and 52/52 disconnected responses with zero false reachable no-path claims.
It solves 22/96 ordinary inputs (eleven bases), five missed by all protected
references, with a longest correct route of nine edges. Counts across panels
are not direct gains or losses because the cases change.

Small complementary second-junction successes now appear in island one:
archived `deep_v1/island1/i127951` completes two prefix-two second-junction pairs
missed by the reference union, one pose in each of two structured contexts,
while completing 70/200 pairs overall. Archived `deep_v1/island1/i129988`
completes two other such poses in one context, with 62/200 pairs overall.
Together these cover four distinct pairs, not four successes by one organism.
Long-prefix fork specialists also persist. These observations warrant retention
and follow-up at later assessments, but remain narrow development coverage
without exact-ancestor/full-founder comparisons or independent confirmation.

Continue unchanged. No broad capability change or required user action.
Saved `results/deep_campaign_run/assessment_02500.json`,
`retention_02500.json` and `checkin_02500.json`.

## Round 3,000 development assessment

Checked at 16:03 UTC; the active writer reached round 3,474. All frontiers remain
two, with zero uncertain/retried batches. Observed process-tree RSS 1.67 GiB,
run storage 2.49 GiB and free disk 61.5 GiB. Frozen setup and assessment hashes
verified. This read-only monitoring performed zero candidate inference.

All three primaries solve 104/200 pairs and 8/96 ordinary inputs, with exactly
the protected aggregate reference's correct-case membership. Best ordinary
counts are 17, 15 and 15/96 versus 15/96 for the strongest individual protected
ordinary reference. Island zero's 17-success specialist also makes 62 false
reachable no-path claims (two correct disconnected responses yield its net
no-path fitness of -60). Its ordinary advantage is not reliable broad solving.
Island one's best ordinary descendant matches the historical reference's
successful-case membership.

The retained ordinary/no-path specialist `deep_v1/island2/i51989` gives 14/96
ordinary successes on seven bases, longest route ten edges, alongside its
unchanged 26/200 pairs, 100/100 corridors and 52/52 disconnected successes with
zero false reachable no-path claims on this panel.

Both tracked second-junction specialists remain archived, retaining their two
prefix-two second-junction pairs apiece and aggregate totals 70 and 62/200.
However, `deep_v1/island1/i127951` makes 44 false reachable no-path claims on
this panel; `deep_v1/island1/i129988` makes none. Retained paired successes
therefore must not be presented as reliable disconnection handling. Prefix-eight
fork coverage also persists, without broader primary progress.

Continue the frozen campaign unchanged. These are development comparisons,
not independent confirmation or proof of acquisition relative to exact ancestors.
Saved `results/deep_campaign_run/assessment_03000.json`,
`retention_03000.json` and `checkin_03000.json`.

## Rounds 3,500 and 4,000 development assessments

Checked at 16:18 UTC with the active writer at round 4,021. All islands remain
at frontier two, with zero uncertain/retried batches. Observed process-tree
RSS 1.56 GiB, run storage 2.89 GiB and free disk 61.1 GiB. Frozen setup,
assessment inputs, receipts and checkpoint hashes verified. No search
intervention or additional candidate inference occurred.

At 3,500, all primaries complete 104/200 pairs and 8/96 ordinary inputs,
versus 104 and 7 for the best protected aggregate reference. The single extra
ordinary case is also solved by unchanged inherited B primaries; it is not
evidence of new campaign acquisition. Best ordinary scores are 8/96 throughout,
matching the strongest protected ordinary reference.

At 4,000, all primaries complete 104/200 pairs and 12/96 ordinary inputs, exactly
matching the protected aggregate reference's correct-case membership. The
best ordinary performer in each island is historical protected genome
`foundation_pair_paired/evolved/fresh/evolution/0/i108890`, with 19/96.
No broad primary advantage has appeared.

There is a meaningful specialist observation. Archived island-two descendant
`deep_v1/island2/i207989` (born 4,000, parent `deep_v1/island2/i207946`, 254 genes)
solves **8/8 prefix-two second-junction goal-switch pairs**, all missed by the
union of 20 protected references. These are only **two structured contexts in
four poses each**, within the existing grammar, not eight independent contexts.
It also solves six prefix-four fork pairs, three missed by the references.

The same genome solves ordinary shortest paths of **11 and 14 edges**, each
in two poses, missed by every protected reference on this panel. The 11-edge
route passes two internal degree-three junctions (at distances one and seven
from the source). The 14-edge route passes one degree-four and two degree-three
junctions (distances two, six and eight). These are two base mazes and four
correlated outputs. They demonstrate normal emitted paths through multiple
branches, beyond a long corridor or a single internal junction.

All 648 saved outputs for this specialist were independently regraded with
`foundation_study_verify_core.Checker`; no new candidate inference was run.
Its genome, saved rows, input hash and successful ordinary geometry are preserved
in `results/deep_campaign_run/specialist_04000.json.gz`. The original journal
retains the complete input manifests and ancestry.

The tradeoffs remain substantial: **94/200 pairs overall**, below the reference's
104; **10/96 ordinary inputs**, below the strongest reference's 19; 100/100
corridors; only 20/52 correct disconnected responses, with zero false reachable
no-path claims on this panel. It fails all positive-prefix cycle pairs and
prefix-one second-junction pairs, despite the prefix-two successes. This
nonmonotonic pattern is not evidence of a general algorithm. Exact ancestor
and full-founder capability comparisons remain outstanding; changed lineage
identity alone does not establish acquired functionality.

Earlier specialist `deep_v1/island2/i51989` remains archived, with 6/96 ordinary
successes at 3,500 and 18/96 at 4,000; both panels retain 26/200 pairs, 100/100
corridors and 52/52 disconnected successes, with zero false reachable no-path
claims. The ordinary counts vary with the assessment cases.

Continue unchanged. This new specialist coverage warrants a concise user
notification, while all results remain development/selection data. Independent
confirmation, general-solving and speed claims remain unestablished.
Saved `assessment_03500.json`, `assessment_04000.json`, `retention_03500.json`,
`retention_04000.json` and `checkin_04000.json` under
`results/deep_campaign_run/`.
