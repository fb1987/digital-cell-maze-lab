# M26 — Rare longer-route abilities appear, but do not accumulate reliably

**The saved records contain useful intermediate evidence that M25's final nominees
missed.** Twenty-eight genotype-changing mutant identities solved ordinary mazes
with routes of 8–16 edges in both tested orientations, beyond the 14 protected
references on the same cases. These wins covered ten distinct fresh mazes. One
variant solved a 16-edge perfect maze. These are training observations, not new
confirmation or evidence of a general solver.

Selection retained at least one solver in every rare-win episode. Thirteen of the
28 changed mutants survived their first observed rare win and subsequently bred,
producing 35 direct offspring after that observation. None of those identities,
their live descendants or their exact identities in the final archive remained at
M25's end. Where a newly correct target could be attributed directly to a mutation
by comparing its actual parent on the same panel, other correct abilities were lost.

This points toward fragile accumulation and transfer as the next questions. It
does not support blaming immediate rejection alone, and the observed rare variants
were below the append-admission capacity limit.

## What was measured

This new packet implements the saved-training audit the user authorized after M25.
The metric definitions, code and eight synthetic saved-row tests were published at
commit **2d91196 before the full scan**. No organism was executed, no maze generated,
no selection changed and no old study resumed. The 100-model M25 final comparison
archive was not evaluated on these training cases and is not used as a comparator.

The complete M25 journal covers 319 training panels per population, cumulative
rounds 243–561, followed by final assessment at 562. Across six related populations,
there were 86,130 mutant births: 85,860 received training and 270 final newborns had
assessment but no subsequent training. The latter are right-censored. Among the
85,860, 81,190 changed genotype and 4,670 were genotype no-ops. Another 13,398 random
immigrants were born; 13,356 received training and 42 were training-censored.

A complete ordinary base requires correct shortest paths in BOTH saved orientations.
Perfect mazes and cyclic/random mazes are reported separately. Eight edges means
nine path pixels, not eight pixels. Individual-pose wins, inherited reference
successes and new complete-base successes are distinct measures. A stricter novelty
check requires at least one pose to be unsolved by the collective reference input
union; all complete rare wins here pass that stronger check too.

Actual-parent and exact-root comparisons use identical panels and are unavailable
when that comparator was not queried. Every first-exposed mutant's actual parent
was present; some parents had left the population before a later rare win became
visible. No missing response is imputed as a failure.

## Appearance, survival and reproduction

| Population | Changed mutants first evaluated | Changed identities ever showing a novel complete 8+ win | Survived first such win and bred afterward |
|---|---:|---:|---:|
| CURRENT 0 | 13,410 | 0 | 0 |
| INTEGRATE 0 | 11,769 | 0 | 0 |
| CURRENT 1 | 13,785 | 0 | 0 |
| INTEGRATE 1 | 14,079 | 10 | 6 |
| CURRENT 2 | 14,108 | 4 | 2 |
| INTEGRATE 2 | 14,039 | 14 | 5 |
| Total | 81,190 | 28 | 13 |

Nineteen of these 28 changed mutants showed their rare complete win on their first
training panel. Nine first showed it on a later panel. A first-exposure-only audit
would therefore have missed important observations. This is later visibility on
rotating inputs, not an organism learning or changing genome during its lifetime.

There was also one genotype-no-op child inheriting a parent's rare 10-edge success,
and one fresh random immigrant with an 8-edge win. Counting all three categories
would give 30 identities, 11 distinct fresh mazes, 14 parents that bred and 39 direct
offspring. The main mutation figures above exclude the immigrant and the no-op.
The immigrant is evidence of an occasional random-genome success on a particular
case, not a demonstrated general procedure.

The 29 mutant identities including the no-op were all compared with their initial
live M25 ancestor on the same rare-win cases: that ancestor was queried and failed
the target in every instance. This supports lineage-level change relative to those
preserved starting backgrounds. It does not identify which earlier mutation first
created an ability that was only tested later.

All 30 identities produced novel complete wins on fresh inputs, not the persistent
ordinary training bank. Collapsing clones and simultaneous presentations yields
12 population/round/base episodes, involving 11 distinct mazes: ten perfect-maze
episodes and two cyclic/random episodes. Their route lengths were 8, 9, 10, 11 and
16 edges. The longest cyclic/random novel complete win was eight edges; the
16-edge result is on a tree maze.

## The 16-edge witness

Exact identity: `m25/connected/2/enabled/integrate/g276/b22`.
Its actual parent is `.../g261/b24`, its exact root and initial live ancestor are
`m14/reference/gated_partial`, and the birth operator was an ordinary operand edit
through balanced-parent allocation. The genome has 108 counted instructions.

The saved maze is 11×11 with 49 open pixels. The candidate emitted a connected,
unbranched 17-pixel path in each orientation, matching the saved shortest length
of 16 edges. It ran 33 ticks in both. Its parent failed both orientations on the
same panel. These actual recorded rasters were independently checked for free
cells, endpoints, connectivity, degrees and shortest length; no candidate was rerun.

| Ability on that same training panel | Parent | Child | Change |
|---|---:|---:|---|
| Complete ordinary bases | 19 | 4 | 3 gained, 18 lost |
| Complete ordinary bases with routes 8+ | 1 | 4 | 3 gained, none lost |
| Correct paired units | 4 | 0 | All 4 lost |
| Correct corridor inputs | 18 | 8 | 10 lost |
| Correct disconnected inputs | 16 | 0 | All 16 lost |
| False no-path claims on reachable inputs | — | 0 | No false-claim shortcut |

The child survived its first selection, received three training exposures and
produced two changed offspring. It and its descendants were absent from the final
live population. Its descendants were not tested on this exact fresh maze again,
so those births alone do not demonstrate transmission of this particular ability.
The case is a real finite-panel success with substantial tradeoffs.

## Was selection throwing away promising abilities?

**Immediate individual rejection was not equivalent to immediate capability loss.**
Some rare-win children were discarded, but another matching solver survived. In
all 12 population/round/base episodes, the selected survivors contained at least
one organism solving that exact two-orientation target. Zero episodes lost every
solver at that selection decision.

For 12 identities, the actual genetic parent was queried and failed the rare target
that the child solved. None of these direct target gainers retained every one of
its parent's correct inputs. Twelve other identities inherited the target from a
same-panel parent already solving it, and six had no parent response available at
the later hit. The inherited-target group includes some apparently loss-free
children; calling those new mutation acquisitions would overstate the evidence.

Longer-route performance was not uniformly absent or uniformly rejected. Among
changed mutants on first exposure, 38,091 solved at least one complete ordinary
8+ base; most were already covered by the references. There were 3,496 gains over
an actual parent's complete ordinary8+ set and 605 such gainers retained all of
that parent's correct inputs without false reachable no-path. Those counts do not
establish new capability beyond the protected portfolio.

All rare-win lineages identified above eventually disappeared from live ancestry
and the final archive. This does not measure the exact generation when an ability
was lost: the fresh target cases were not repeatedly presented, and different
unqueried genotypes might retain a capability. Each identity showing a rare win
received only one to nine training exposures over its life. The defensible finding
is limited persistence and no demonstrated cumulative transfer, rather than proof
of systematic immediate rejection or proof that the ability became impossible.

## Capacity and regulation

Every prospective append was reconciled to the exact parent's production instruction
count and the selected writer's size. This reproduces M25's earlier accounting:
CURRENT 0 blocked 717/3,582 opportunities and INTEGRATE 0 blocked 2,373/3,625, whereas
other populations blocked much less. Every observed block was the total 128-instruction
admission bound; none was solely the 31-node writer bound.

The 29 mutant identities with rare complete wins, including the no-op, had 108–116
instructions. All could admit further growth under the total bound, and all nine
actual prospective append opportunities whose parents exhibited a novel complete
8+ win on that panel were admitted. There is no recorded blocked append directly
explaining the disappearance of these particular rare wins.

This does not prove present capacity is sufficient for a general algorithm. The
admission threshold, global dispatch limit and ordinary 256-instruction cap interact,
and genotype size is not effective algorithmic complexity. It does mean that simply
raising capacity is not the best-supported explanation or first intervention from
these observations. There are expressed variants with new outputs to investigate
before adding more mechanism.

## What this changes about the research direction

The negative M25 final endpoint remains valid: its frozen nominees added no declared
ordinary8+ capability beyond the historical comparison archive on fresh confirmation.
M26 adds evidence that intermediate populations can occasionally produce longer
correct ordinary paths that the preserved controls do not produce. That is more
encouraging than complete local stagnation, while still far short of a general
solver or a speed advantage.

The central unresolved question is whether these rare wins reflect transferable
routing changes or narrow geometric coincidences, and whether they can coexist with
older abilities. Occasional correct paths, including one random immigrant's result,
can occur without a broadly useful mechanism. Related lineages, shared mazes and
posthoc discovery make significance or policy-causality claims inappropriate. The
INTEGRATE concentration in this table does not overturn M25's registered null endpoint.

**Recommended next step: a small, separately registered transfer-and-retention
assay of these exact saved variants, their actual parents and preserved references.**
Freeze the complete comparison pool before generating independent cases. Test unused
matched perfect and cyclic mazes, both poses, longer length strata and disconnected
controls, with explicit retention and real-cost measures. Use the saved witnesses
to explain mechanisms; do not choose a favorable subset on the fresh results.

If rare wins transfer, follow with a bounded evolution comparison that records and
revisits acquired skills while preserving useful specialists and demanding eventual
integration. Both arms should receive the same opportunities and accounting. If
transfer fails, investigate variation access and safe regulatory capacity before
another large search. This preserves the random-origin mission and evolutionary
history without assuming that compute alone, immediate survival quotas or extra
capacity will solve the demonstrated bottleneck. This recommendation is not launched;
no new evolution, capacity change, recombination, solver injection or cloud compute
is authorized by M26.

## Verification, cost and preservation

The primary analysis and independently implemented verifier both completed on their
first attempt. The verifier checked all 99,528 births, 99,216 first training
exposures including immigrants, subsequent novel-hit presentations, immediate
survival, actual reproduction timing and final live descendants. All 22,188 receipt
hashes, 340 input/decision chain links and available checkpoints verified. The
original source native-output/grade audits remain PASS; M26 is not a second VM.

The posthoc witness supplement examined every novel complete8 hit, then a separate
review validated all 60 emitted child rasters and their receipt hashes. It also
clarified that the pooled supplement includes an immigrant and a no-op; the explicit
`changed_mutants_only` group in witness_review.json supplies the main denominators.
The immigrant has no pre-M25 source ancestor; its raw self label is not a retention
comparison. These supplements were written after seeing the primary scan and do not
redefine the registered M25 endpoint.

Primary scan: 74.68 seconds wall/74.24 CPU, 0.662 GiB peak RSS. Independent verifier:
76.14 seconds wall/76.12 CPU, 1.181 GiB peak RSS. Witness extraction and review:
10.58 additional seconds wall. Total recorded scans were about 161.41 seconds, one
worker per scan, zero new candidate inference calls and zero generated layouts.
Interactive inspection and report writing are additional unprofiled bookkeeping,
not scientific compute. Packet storage was about 10.5 MiB before final report/seal,
with about 40 GiB disk free; every recorded scan stayed within the 30-minute,
4 GiB RSS, 512 MiB packet and 16 GiB free-space bounds.

All **507 M25 sealed files and 18 local records** verified unchanged before and
after the primary scan. The source journal byte hash is unchanged:
`cf098e0ccd65aa564fe4517c698c556ca6e6d38514370d6f099463a0d41c6d70`.
Existing original journals, verified backups, failed records and layout ledgers
remain intact. No raw SQLite is included in this packet or in Git.

One read-only console formatting probe assumed a later parent comparison was
available and raised TypeError. It created no output and changed no source or
scientific record. The failed assumption is preserved under
postprocessing_failures/display_001.json; later missing-parent comparisons were
already correctly null in the primary analysis. No analysis or verifier repair,
rerun or overwritten closed output was needed.

Reproduction: run the registered analysis and verifier only into a NEW separate
packet if a future audit is authorized. Do not overwrite this packet or M25 seals.
The primary inputs, definitions, cohorts, witness rasters, code, tests, logs and
review are preserved here and will receive a new completion seal.
