# M5 conditional-state holding assay — complete, confirmed and audited

October21,2026. Registration **2bf9cc4**, full proposal pool **63e367b**, and
nomination freeze **591870c** were pushed before their downstream scientific
cases were generated. Both audits passed on their first attempt. No old study
was resumed or altered; no additional confirmation or reselection occurred.

**We found a confirmed extension of upstream routing, but it does not support
adding state holding as the next default architecture.** A zero-fallback variant
and a standard-mutation variant each acquired 32 upstream junction/cycle pairs
while preserving their ancestor's paired, corridor and ordinary-maze successes.
Their exact hold counterpart did not acquire those upstream pairs. The new
successes remain narrow and both passing variants lose correct disconnected-maze
detections. These qualifications matter even though the registered gate passes.

## What the comparison tested

M5 adds a condition to each block's existing persistent-state writer. When the
condition is true, the block writes its normal computed value. When false, it
can write zero or retain its OLD value. No new distance, queue, parent pointer,
route cleanup, global information or solver algorithm is supplied. Existing M1
bodies embed with all conditions ALWAYS and preserve masks, statuses, steps and
work. The two extra int32 metadata arrays add64 reported bytes. The current M1
runtime can already express conditional holding through SELECT; this tests
accessibility, not an assumption that holding was fundamentally inexpressible.

The two exact M3/M4-informed random-origin anchors are A0 mixed0 `g669/b31` and
A1 single2 `g800/b15`. For each anchor,1024 matched proposals give the same body
and writer condition to the **hold** and **zero** arms; only their false-condition
fallback differs.512 proposals make a writer change directly,512 first apply one
generic M1 mutation. A **standard** arm gets1024 proposals with matching one/two
mutation-opportunity counts and unchanged M1 mutation rules. A shared1024-genome
random reference pool and unchanged roots/parents/controls complete the study.
Only hold-versus-zero isolates the fallback bit; standard proposals also differ
in how edits are drawn. These are fixed-parent neighborhoods, not populations
undergoing a long evolutionary run.

All7168 proposal aliases were published before the development cases. Including
references,5519 distinct physical models received the same392 inputs. Each of
six anchor/arm conditions had **401,408 logical proposal queries**; the shared
random pool had the same allocation. Exact-genotype deduplication reduced total
physical calls to2,163,448. Repeated genotypes and shared ancestry are not
independent discoveries or experimental replicates.

## Development results and frozen confirmation

The following counts are per1024 proposals, before untouched confirmation.
Retention requires at least90% of the anchor's successful pair/corridor/ordinary
sets and zero false reachable no-path. A1's unchanged anchor therefore does not
itself satisfy that filter: it makes false no-path claims.

| Anchor | Arm | Retained | Passed development gate | Distinct passing genotypes | Passing terminal patterns |
|---|---|---:|---:|---:|---:|
| A0 | Hold | 338 | 0 | 0 | 0 |
| A0 | Zero | 319 | 0 | 0 | 0 |
| A0 | Standard | 514 | 0 | 0 | 0 |
| A1 | Hold | 1 | 0 | 0 | 0 |
| A1 | Zero | 9 | 8 | 6 | 3 |
| A1 | Standard | 6 | 5 | 4 | 1 |

For A0, all319 retained zero proposals also retain under holding, and19 more
retain only under holding. Neither arm gains upstream pairs. For A1, eight
proposals retain only under zero and one under both; none retain only under
holding.874/1024 A0 pairs and837/1024 A1 pairs have identical terminal masks,
statuses and steps under the two fallbacks on this screen. Those are panel-local
observations, not global semantic equivalence or independent statistical trials.

The protocol froze13 nomination aliases: retained/exploratory per anchor/arm,
plus one aggregate random reference. Exact opposite-fallback twins accompany
selected hold/zero variants. Along with references and controls, this produced
24 distinct final models. A fresh1680-input panel followed the pushed choice
freeze and PASS development audit, excluding every old and development layout.

## Actual fresh outcomes

The primary gate requires a changed nominee to acquire at least eight UPSTREAM
pairs beyond its exact anchor across at least two template contexts, retain90%
of that anchor's successful pair/corridor/ordinary sets, and make zero false
reachable no-path claims. Upstream means non-fork prefix>=1 or fork prefix>=2.
This is distinct from M4's stricter requirement to retain BOTH specialists' sets.

| Model | Pairs /400 | New upstream pairs | Corridors /200 | Ordinary bases correct in both poses /256 | Correct no-path /168 | False no-path /1512 | M5 gate |
|---|---:|---:|---:|---:|---:|---:|---|
| A0 unchanged | 96 | — | 200 | 25 | 168 | 0 | Reference |
| A0 standard0434, exploratory | 176 | 48 | 200 | 10 | 0 | 0 | Fail |
| A1 unchanged | 64 | — | 52 | 5 | 20 | 4 | Reference |
| A1 zero0435 | 128 | 32 | 52 | 5 | 0 | 0 | **Pass** |
| A1 standard0191 | 128 | 32 | 52 | 5 | 0 | 0 | **Pass** |
| A1 hold0435, exact zero0435 twin | 64 | 0 | 52 | 5 | 20 | 4 | Fail |
| A1 hold0243, retained nominee | 64 | 0 | 52 | 5 | 0 | 0 | Fail |
| A1 hold0497, exploratory nominee | 96 | 0 | 200 | 8 | 0 | 0 | Fail |
| Random0934, selected reference | 32 | — | 200 | 2 | 0 | 0 | Not an acquisition |

Four passing nomination aliases identify **two distinct genotypes**, not four
independent successes. Each retains all64 anchor pairs, all52 corridors and all
five ordinary bases, and adds64 complete pairs.32 of those additions are easy
prefix1 forks; the qualifying32 are **16 second-junction prefix1 pairs and16
cycle prefix1 pairs across four contexts**. The source is now one step upstream,
rather than at the junction. The successful upstream task routes have5 or7edges.
Poses and related variants are correlated; the evidence remains within this
familiar grammar. Neither passing variant solves second-junction/cycle prefix2,
4 or8, or fork prefix2,4 or8.

The two passers have identical successful pair/corridor/ordinary sets on this
panel, but match terminal masks/statuses/steps on only1304/1680 inputs. They are
not established as the same algorithm. Both retain every previously correct
reachable input and gain70 individual correct inputs, but lose20 correct
no-path detections. The registered gate did **not** require retention of correct
disconnected answers. We honor its PASS while reporting that loss explicitly;
this is not preservation of every prior ability. Both still solve only52/200
corridors and five ordinary bases, all one-edge routes. They do not combine A0's
stronger ordinary/corridor repertoire with A1's new upstream skill.

A0 standard0434 is another useful preserved specialist: a single port mutation
adds48 prefix2 fork pairs across12 contexts, plus32 source-at-junction non-fork
pairs. It retains all96 old pairs and200 corridors, but loses15/25 ordinary bases
and all168 correct no-path detections. It fails the declared gate. Its10 ordinary
successes have1–5edges; its new upstream fork routes have4–8edges. The selected
A0 hold/zero0311 and standard0879 nominees add no paired or ordinary successes
beyond their unchanged anchor on this panel.

A0's unchanged25/256 is not an improvement over M4's21/256: these are different
fresh panels. Its five8+edge successes here are on perfect mazes, with no random
8+edge success. No general solver or ordinary-maze breadth gain is established.

## What the changes actually do

The clearest matched causal result is zero0435 versus hold0435. Their M1 body
and condition are identical. The writer condition is channel1 at block7.
Writing zero when that condition is false permits the new upstream pairs;
retaining the previous channel7 value does not. More persistence is not
universally helpful: controlled clearing matters in this local system.

Static inspection of the preserved code gives the relevant updates below.
Values saturate at65535. These are code-level expressions, not new temporal
traces, and do not prove a full wave or backtrace mechanism.

- Original A1: `C7_next = saturating(C1 + C7_old)`.
- Zero0435: the same addition when `C1 > 0`, otherwise `C7_next = 0`.
- Its hold twin: the same addition when `C1 > 0`, otherwise keep `C7_old`.
- Standard0191: a generic port swap changes the addition to
  `C7_next = saturating(C1 + C6_old)`.

For this particular condition, the hold twin's channel7 update is algebraically
the original accumulator: adding zero already retains the previous value. The
new effective option is clearing that memory when the driving signal is absent.
This does not establish that clearing is preferable for every channel or task.

In this lineage, block6 computes the same gated neighbor-count expression as
output block2: count positive channel4 neighbors only when the site's channel4
is positive. A generic standard mutation therefore brings an existing dormant
computation into the recurrent clock/output-dependent loop. It does not require
the new holding option. Both passing proposals also delete a block0 node outside
its static output cone. No separate deletion ablation was registered, so we do
not assert its complete cost/behavior neutrality; the matched hold/zero test
already keeps that deletion fixed.

Channel7 affects halting and also propagates through other channel dependencies.
Thus it would be premature to describe this solely as “wait one more tick,” a
new general backtrace, or a proven pulse-wave algorithm. Saved normal outputs,
exact code and audit replays support the acquisition and fallback comparison;
no forced internal-state traces were collected in M5. The static dependency
helper in `mechanism_static.json` covers the M1 body and explicitly does not
include added writer guards in its node count.

## Cost, checks and preserved evidence

Development:2,163,448 physical calls,193.75wall seconds,1555.52summed candidate
seconds,1605.25workerCPU seconds,466,198,461,322charged work. Sampled process-tree
RSS peaked at2.678GiB. Final:40,320calls,14.99wall seconds,31.60candidate seconds,
34.46workerCPU seconds,14,156,946,925work;1.614GiB sampled RSS. The combined main
run used **2,203,768calls,208.74wall seconds,1587.12candidate seconds and
480,355,408,247work**. There were zero uncertain attempts, guard stops or budget
bypasses. Different physical deduplication/work costs are reported, not described
as equal CPU budgets. No latency comparison against conventional solvers was run.

Pre-registration discarded checks used47,432 measured calls plus four warm-up
calls on old excluded fixtures. Measured candidate time43.52seconds and wall
7.45seconds exclude those warm-ups and separate unit-test execution. Nine focused
new/modular tests passed, not a fresh full suite. Pool/RNG and nomination replay,
canonical final-summary serialization, anchor embedding and intact controls
were exercised before registration. No new fixture layouts were generated.

First development audit **PASS,164.23seconds**: all2,163,448 outputs independently
regraded,70,588 native replays, all proposals/mutations/writer choices/RNG/corpus/
tasks/nominations exactly regenerated. First final audit **PASS,31.63seconds**:
all40,320 native responses and independent grades, regenerated corpus/tasks and
canonical summary. Legacy and embedded anchors matched, and all four intact
controls solved every final input. Replay shares the production VM; it is not
an independent second interpreter. The development audit's OS-reported maximum
RSS was3.669GiB, below the8GiB ceiling. All registered files/dependency versions
and all302 M4 completion hashes remain unchanged; no post-registration repair.

Both original journals and SQLite-API backups with matching table contents and
successful integrity checks remain under `runs/holding_assay_m5/`. Compact final
responses, complete pools/RNG, nomination features, audits, logs and report are
published; raw journals stay local. The cumulative exclusion packet contains
**1,374,083 whole layouts**, including848 development and5304 final new layouts,
including rejected and unqueried cases. Preserved storage is about1.01GiB under
the6GiB limit, with over37GiB disk free at backup time. Exact measurements and
hashes are in `preservation.json` and `completion.json`. Future re-audits must use
separate output packets, never overwrite existing seals or raw-rerun actions.

## Decision and next recommendation

The acquisition gate passed, so this is a positive result for continued
random-origin research. The proposed holding enhancement did not win: no hold
nominee passed, the exact hold twin loses the new skill, and ordinary M1 mutation
reaches the same successful task set. Keep the current M1 runtime as the main
search representation; preserve M5 as a tested diagnostic option rather than
adopting it on expectation alone.

A bounded longer continuation is now justified from the exact standard0191
body, alongside the stronger retained-skill A0 lineage and preserved alternatives.
The next registered target should be upstream second-junction/cycle prefixes2
and beyond while retaining existing paired/corridor/ordinary successes. Correct
disconnected-answer retention must be explicit in the next protocol, so clearing
false no-path claims cannot conceal loss of disconnection ability. Preserve
strong no-path specialists separately rather than silently treating the new
variant as a replacement for all existing genomes.

These are proposed design constraints, not a launched continuation. Do not seed
known solver logic, silently extend a closed allowance or train/reselect on M5
confirmation cases. There is no reason yet to claim broad generalization,
multirange benefit, speed advantage or successful sexual combination. We do now
have a concrete new inherited skill, a controlled counterfactual explaining why
holding prevents it, and an ordinary-mutation route worth giving evolutionary
time under a newly registered protocol.
