# V12X-R1: dependency-preserving crossover activation pilot

**The 32-generation pilot is complete. The preregistered activation gate fails
for every sexual condition, so the longer efficacy experiment is not launched.**
The result identifies a reproduction-design bottleneck; it does not decide
whether random-origin evolution can eventually produce a general solver.

![All registered activation outcomes](linkage_restart/activation.png)

The valid restart was frozen and pushed in `7bee1a6` before training generation.
Its [protocol](../docs/LINKAGE_RESTART_V12X.md) compares dependency-preserving
crossover, unrestricted crossover from the same structural pool, a matched
random-boundary control, single-edit mutation, resampling and frozen founders.
Carry and fresh origins each have three search replicates and 96 organisms per
condition. All 36 conditions receive exactly 18,432 evaluations, or 663,552 total.
No known solver or synthetic W diagnostic genome enters an evolving lineage.

## What actually transferred

An accepted splice can copy a 16-instruction block while changing only one row.
The activation endpoint therefore requires **at least two changed donor
instructions to remain after the child's subsequent mutation**.

Each row below pools three replicates, with 3,072 scheduled mating births.
Replicate decisions use 1,024 attempts each, not the pooled fraction.

| Origin | Crossover policy | Any accepted splice | Retained multi-instruction transfers | Fraction of attempts | Passing replicates |
|---|---|---:|---:|---:|---:|
| Carry | Dependency preserved | 547 | 8 | 0.26% | 0/3 |
| Carry | Unlinked | 1,675 | 65 | 2.12% | 0/3 |
| Carry | Matched random boundary | 614 | 9 | 0.29% | 0/3 |
| Fresh | Dependency preserved | 560 | 30 | 0.98% | 0/3 |
| Fresh | Unlinked | 1,272 | 126 | 4.10% | 0/3 |
| Fresh | Matched random boundary | 421 | 33 | 1.07% | 0/3 |

The frozen threshold is at least 10% of attempts, with transfers in at least
eight generations, in two of three replicates for each sexual policy within
each origin. Both origins must qualify before the proposed joint longer run.
Even the highest individual fraction, fresh/unlinked replicate 2 at 59/1,024
(5.76%), falls short. The threshold is an operational decision rule for this
experiment, not a universal biological requirement.

The system does transmit multigene material: the final fresh linked populations
contain 0, 42 and 64 members with such a transfer in their recorded ancestry.
That includes the last unevaluated newborn generation. It establishes inheritance,
not useful skill composition, and does not rescue the failed activation gate.
All these populations and their RNG states remain available for future work.

## Why activation is limited

The [post-hoc diagnostics](linkage_restart/diagnostics.json) reconstruct the
recorded parent pairs and segment pools without additional candidate inference.
They are descriptive training evidence, not a second experiment.

First, many shortlists contain no eligible related variant. In the linked arms,
this occurs for 1,353/3,072 carried attempts and 1,891/3,072 fresh attempts.
“No eligible donor” refers to the recorded eight-draw shortlist and operator
rules, not proof that no suitable donor exists anywhere in the population.
Unrelated random founders deliberately do not acquire homology merely because
instructions look similar.

Second, dependency closure removes most multi-change opportunities:

| Linked-arm recorded proposals | Carry | Fresh |
|---|---:|---:|
| Scheduled mating births | 3,072 | 3,072 |
| Eligible donor available | 1,719 | 1,181 |
| Some multi-change segment at proposed length, before closure | 439 | 333 |
| Some multi-change segment at proposed length, after closure | 22 | 61 |
| Actual multi-change transfer retained after mutation | 8 | 30 |

Thus, even choosing the best permitted segment for every one of these recorded
linked proposals could not approach 10% activation. This is a conditional bound
for the observed parents and proposed lengths, not a counterfactual prediction
for a different evolutionary trajectory.

Most multi-change transfers in the unlinked arms cut the conservative dependency
groups: 63/65 carried and 114/126 fresh transfers. That does not establish that
those transfers damage function; the groups describe possible dependencies.
Linked and matched-sham rates are similarly low, so no special benefit from
dependency semantics is demonstrated here. Subsequent mutation removes the
multi-change property in only three accepted events across all sexual arms;
it is not the dominant source of the shortfall.

The [static historical diagnostic](linkage_restart/static_diagnostic.json)
illustrates why the rule can be too restrictive. In exact d07, the transitive
scratch-dependency group for output STORE 222 contains 18 instructions spread
across 220 positions. A contiguous block capped at 16 cannot carry that group.
The d07/d12 common pool has multi-change segments but no dependency-closed ones.
This does **not** prove that a functional module really needs 220 instructions:
conditional reaching definitions deliberately overapproximate possible influence.

## What this changes in the research plan

W supplied evidence that instruction combinations can help or harm routing.
X-R1 shows that preserving every transitive scratch dependency in a short
contiguous segment exercises too little multigene recombination in this design.
Simply allocating 75 minutes would spend most mating births on failed attempts
or single-change exchanges. It would not be a strong test of combining abilities.

I recommend one bounded operator-opportunity study before another evolution run:
compare the current closure with **immediate gate-writer linkage**, using the
same parents and segment-length opportunities, and explicitly measure the supply
of related multi-change variants. Test a 32-instruction allowance as a separate
common-pool factor. Do not encode d07's circuit or transplant known solver genes.
The [next proposal](linkage_restart/next_experiment.md) sets out the controls and
the decision about whether lineage diversity also needs changing.

This preserves the random-origin track and the user's hypothesis that evolution
needs time, capacity and pressure. It narrows a more immediate requirement:
the proposed reproduction operator must have enough genuine genetic variation
to act on. More time may help that supply, but this pilot does not establish how
much, and old populations must not be silently discarded.

## Scope and software correction

This is a training activation pilot, with 32 changing structured contexts and
only the first four poses of the 72-generation schedule. There is no new
independent efficacy holdout, final champion selection, ordinary-maze improvement
claim, multirange comparison or speed benchmark. Carried replicates share protected
historical anchors; they are not independent rediscoveries of those lineages.
Raw training scores across changing batches cannot measure generalization.

The original X attempt (`aedb017`) reused historical offspring identity names.
An assertion exposed the collision after 28 full rounds and a partial 29th.
Identity-keyed records could refer to the wrong genotype, invalidating the
comparison. That was an implementation error, not an evolutionary result.
Its [failure report](linkage_pilot.md), frozen source, raw records and partial
states are preserved and explicitly excluded from scientific conclusions.

The clean restart uses new seeds, unique study-specific offspring IDs, and
checks for unique population identities, intact protected individuals and
consistent gene maps. Regression tests reproduce the old collision. All layouts
generated by the invalid attempt are excluded. The restart retains the same
operator, gate and 32-generation target, and uses only the remaining candidate
allowance. A protocol-path typo was corrected before the restart's registration;
the [registration note](linkage_restart/registration_note.txt) records it.

Detailed per-replicate results, costs and audit evidence follow.

## Complete activation results

Gate: at least 10% of all scheduled attempts retain two changed donor instructions after mutation, with such transfers in at least eight generations. Each origin needs at least two passing replicates for each of linked, unlinked and matched-sham crossover.

| Origin | Policy | Rep | Attempts | Donor available | Accepted | Multi before mutation | Multi retained | Retained / attempts | Active generations | Pass |
|---|---|---|---|---|---|---|---|---|---|---|
| carry | linked | 0 | 1024 | 593 | 216 | 3 | 3 | 0.29% | 2 | False |
| carry | linked | 1 | 1024 | 557 | 165 | 2 | 2 | 0.20% | 1 | False |
| carry | linked | 2 | 1024 | 569 | 166 | 3 | 3 | 0.29% | 3 | False |
| carry | unlinked | 0 | 1024 | 636 | 636 | 26 | 26 | 2.54% | 19 | False |
| carry | unlinked | 1 | 1024 | 529 | 529 | 18 | 18 | 1.76% | 12 | False |
| carry | unlinked | 2 | 1024 | 510 | 510 | 22 | 21 | 2.05% | 13 | False |
| carry | sham | 0 | 1024 | 669 | 223 | 5 | 5 | 0.49% | 4 | False |
| carry | sham | 1 | 1024 | 530 | 192 | 3 | 3 | 0.29% | 3 | False |
| carry | sham | 2 | 1024 | 583 | 199 | 1 | 1 | 0.10% | 1 | False |
| fresh | linked | 0 | 1024 | 310 | 116 | 4 | 4 | 0.39% | 4 | False |
| fresh | linked | 1 | 1024 | 394 | 241 | 20 | 20 | 1.95% | 10 | False |
| fresh | linked | 2 | 1024 | 477 | 203 | 6 | 6 | 0.59% | 6 | False |
| fresh | unlinked | 0 | 1024 | 265 | 265 | 26 | 26 | 2.54% | 15 | False |
| fresh | unlinked | 1 | 1024 | 398 | 398 | 41 | 41 | 4.00% | 20 | False |
| fresh | unlinked | 2 | 1024 | 609 | 609 | 59 | 59 | 5.76% | 25 | False |
| fresh | sham | 0 | 1024 | 234 | 104 | 6 | 6 | 0.59% | 5 | False |
| fresh | sham | 1 | 1024 | 339 | 212 | 23 | 21 | 2.05% | 13 | False |
| fresh | sham | 2 | 1024 | 355 | 105 | 6 | 6 | 0.59% | 4 | False |

## Proposed and accepted segment lengths

| Origin | Policy | Length | Proposed with donor | Accepted | Multi retained |
|---|---|---|---|---|---|
| carry | linked | 2 | 431 | 310 | 3 |
| carry | linked | 4 | 414 | 202 | 5 |
| carry | linked | 8 | 434 | 33 | 0 |
| carry | linked | 16 | 440 | 2 | 0 |
| carry | unlinked | 2 | 444 | 444 | 4 |
| carry | unlinked | 4 | 403 | 403 | 7 |
| carry | unlinked | 8 | 421 | 421 | 20 |
| carry | unlinked | 16 | 407 | 407 | 34 |
| carry | sham | 2 | 468 | 343 | 2 |
| carry | sham | 4 | 415 | 247 | 5 |
| carry | sham | 8 | 462 | 23 | 2 |
| carry | sham | 16 | 437 | 1 | 0 |
| fresh | linked | 2 | 277 | 195 | 2 |
| fresh | linked | 4 | 313 | 205 | 7 |
| fresh | linked | 8 | 297 | 127 | 10 |
| fresh | linked | 16 | 294 | 33 | 11 |
| fresh | unlinked | 2 | 291 | 291 | 3 |
| fresh | unlinked | 4 | 341 | 341 | 15 |
| fresh | unlinked | 8 | 328 | 328 | 39 |
| fresh | unlinked | 16 | 312 | 312 | 69 |
| fresh | sham | 2 | 217 | 167 | 1 |
| fresh | sham | 4 | 222 | 139 | 10 |
| fresh | sham | 8 | 247 | 77 | 10 |
| fresh | sham | 16 | 242 | 38 | 12 |

Linked/sham length and feasibility matching is exact for the same parents and RNG snapshot. Evolving populations diverge, so these marginal distributions are not forced to match. The unlinked policy retains all common-pool segments. Genetic transfer counts do not demonstrate combined solving abilities.

## Cost, reproducibility and scope

The pilot completed **32 matched generations** of 32 planned, stopping with `planned_generations`. Main inference: 663,552 calls, 341.61/422.29 candidate seconds, 200,233,097,994 charged work units. Total main wall: 590.41/720 seconds, including 130.55s in reproduction; peak RSS 515.25 MiB.

Calibration separately: 5,504 native calls, 0.910 candidate seconds and 4.40s wall. Its 2,160 discarded births were not seeded into search. Warmups are separately recorded. The restart held the original 32-generation target fixed; its timing-only projection was 512.48s, below the 600s planning threshold and remaining candidate allowance. No fitness-based sizing or cap extension.

Audit passes **669,056 logical candidate responses**, checked against **549,272 newly executed distinct genotype/case replays**; exact duplicates are reused only within each generation (and within calibration). Every logical candidate raster is independently graded: 669,056. Baselines add 576 exact replays and independent grades.

Original invalid attempt separately: 297.71 candidate seconds and 512.71 wall seconds, plus 5,504 calibration calls in 0.815 candidate seconds and 4.34s wall. Combined main candidate time is 639.32/720 seconds; combined main wall 1103.12s. Including both calibrations adds 1.725 candidate seconds. This extra wall cost is a disclosed software restart, not an extension based on scientific results. Audit replay costs are additional and reported below.

Full selection/RNG/population replay includes 20,736 random births, 48,384 concrete mutations, 5,089 independently reconstructed accepted splices and 48,384 independently checked gene identity maps. Accepted dependency groups are independently scanned backwards. All 6,166 prior completion entries and 231 source/22 input hashes verify. Audit wall 521.27s; peak RSS 987.41 MiB.

Nineteen restart tests and19related tests pass (38), including the historical-namespace collision regression. This is not a fresh full-suite run. The restart protocol and all inputs were pushed before training generation. Its source and gate were not changed after registration. The original aedb017 attempt was invalidated by the disclosed identity bug and is preserved separately.

Exclude **255,356 whole layouts through X-R1**, including every unqueried generated orientation and software fixture, using the sealed exclusion hash set. The data.exclusions() helper returns only 253,316 through the invalid original attempt. All populations, complete reproduction records, RNG checkpoints and final next populations are preserved; the last newborn population has not yet been evaluated.

All outcomes concern a training activation pilot. There is no independent efficacy holdout, final champion selection, general-solver claim, multirange comparison or latency benchmark. Frozen founder controls were evaluated on the same batches; differing training tasks across generations prohibit interpreting raw score changes as generalization.
