# M11 retention-bank calibration: audited results

Descriptive bank support: **True**. Readiness for a separately registered evolutionary protocol: **True**. No evolution or new solver discovery occurred in M11.

This tests whether a fixed scoring panel rejects severe ordinary-skill losses in the preserved M10 diagnostic pool. The exact pool was frozen before new cases:30physical models, including two intact controls; aliases are preserved and counted once per genotype. The parent used to construct every bank is the unchanged M10 quota_parent. Neither gated reference nor any diagnostic candidate chose bank cases.

Each of three current panels and its matched bank scores392inputs/model. The344nonordinary inputs are identical; only24ordinary bases/two poses change. The current distribution follows M10. Bank quotas are4parent-successful bases each for P11/P15/R9/R15short andP11/P15medium. This is explicitly biased reference-conditioned fitness design. It is not an unbiased maze performance benchmark. Shared scoring inputs are physically deduplicated, and all reference-construction calls are additional.

Every bank uses exactly1024raw draws per stratum, selects the first4optimal-both-pose reference successes, and retains all generated/rejected/unqueried layouts. No quota, score, pool or bound was changed after registration. Banks/predictions were published before the independent1680-input corpus; all models were tested, with no nominee reselection.

## Independent classification

The fixed parent solves 18/256 ordinary bases in both poses on fresh confirmation. Of 28 diagnostic genotypes, 25 retain less than90% of those successes. This sample-based severe-loss definition is the registered truth criterion; it is not universal semantic equivalence.

| Panel | Current parent successes | Bank parent successes | Current severe false accepts | Bank severe false accepts | Current false rejects | Bank false rejects | Nonvacuous | Bank ready |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 3 | 24 | 0 | 0 | 0 | 0 | True | True |
| 1 | 1 | 24 | 11 | 0 | 0 | 0 | True | True |
| 2 | 7 | 24 | 1 | 0 | 0 | 0 | True | True |

False accept: a genotype with severe loss on confirmation passes complete ordinary retention on the scoring panel. False reject: a genotype retaining all parental ordinary successes on confirmation fails the panel. Counts exclude the two intact controls, deduplicate genotypes, and refer to sampled behavior. Positive checks separately require the fixed parent and both intact controls to pass in both methods.

All three comparisons must meet declared nonvacuity: >=16parental confirmation successes, >=2severe genotypes including shared_child, nonempty current-panel parent denominator,24bank parent successes, and >=8bank ordinary successes for each gated reference. Descriptive support additionally needs strict improvement in2/3panels and positive total reduction. Readiness requires ZEROsevere false accepts in ALLthree banks plus positive checks. This is a descriptive calibration on related genomes, not a significance test or proof about future mutations.

## Gated-reference coverage and ranking

| Panel | Gated partial bank successes | Gated specialist bank successes | Current top-ranked genotype retention on confirmation | Bank top-ranked genotype retention on confirmation |
|---|---:|---:|---:|---:|
| 0 | 19 | 11 | 1.000 | 1.000 |
| 1 | 19 | 15 | 0.444 | 1.000 |
| 2 | 17 | 16 | 0.833 | 1.000 |

The ranking uses the unchanged M10 integration rank on each panel. All rankings were frozen before confirmation and never selected a different tested pool. Full genotype/alias prediction matrices and integration capability diagnostics are in calibration_freeze.json.gz and summary.json. Existing M10 mutation depth does not imply M11 acquisition; M11 has zero births.

## Construction coverage

| Bank | Family | Size | Edges | Raw bases | Length-eligible | Parent solved both poses | Selected |
|---|---|---:|---|---:|---:|---:|---:|
| 0 | perfect | 11 | 1–7 | 1024 | 352 | 215 | 4 |
| 0 | perfect | 15 | 1–7 | 1024 | 212 | 129 | 4 |
| 0 | random | 9 | 1–7 | 1024 | 558 | 148 | 4 |
| 0 | random | 15 | 1–7 | 1024 | 283 | 69 | 4 |
| 0 | perfect | 11 | 8–15 | 1024 | 401 | 32 | 4 |
| 0 | perfect | 15 | 8–15 | 1024 | 317 | 19 | 4 |
| 1 | perfect | 11 | 1–7 | 1024 | 392 | 261 | 4 |
| 1 | perfect | 15 | 1–7 | 1024 | 189 | 108 | 4 |
| 1 | random | 9 | 1–7 | 1024 | 567 | 150 | 4 |
| 1 | random | 15 | 1–7 | 1024 | 259 | 59 | 4 |
| 1 | perfect | 11 | 8–15 | 1024 | 437 | 26 | 4 |
| 1 | perfect | 15 | 8–15 | 1024 | 280 | 18 | 4 |
| 2 | perfect | 11 | 1–7 | 1024 | 369 | 226 | 4 |
| 2 | perfect | 15 | 1–7 | 1024 | 212 | 134 | 4 |
| 2 | random | 9 | 1–7 | 1024 | 587 | 138 | 4 |
| 2 | random | 15 | 1–7 | 1024 | 259 | 61 | 4 |
| 2 | perfect | 11 | 8–15 | 1024 | 418 | 31 | 4 |
| 2 | perfect | 15 | 8–15 | 1024 | 279 | 11 | 4 |

There was no16+quota. Long-route capabilities remain sparse; diagnostics.json reports queried-only confirmation length strata for the parent, both gated references and shared_child. Complete ordinary coverage means both sampled poses, not arbitrary transformations or maze families.

## Costs, audit and preservation

| Stage | Kind | Replicate | Physical calls | Candidate seconds | Worker CPU seconds | Work |
|---|---|---:|---:|---:|---:|---:|
| 0 | draw | 0 | 4,246 | 2.657 | 6.482 | 808,335,828 |
| 1 | panel | 0 | 13,200 | 4.667 | 5.595 | 1,949,383,157 |
| 2 | draw | 1 | 4,248 | 1.798 | 5.404 | 785,872,016 |
| 3 | panel | 1 | 13,200 | 4.584 | 5.453 | 1,907,060,752 |
| 4 | draw | 2 | 4,248 | 1.801 | 5.442 | 786,968,376 |
| 5 | panel | 2 | 13,200 | 4.453 | 5.362 | 1,883,928,919 |
| 6 | final | 3 | 50,400 | 40.883 | 45.105 | 15,204,112,250 |

calibration: 36.82s wall, 3.037GiB sampled process-tree RSS. First audit PASS in 35.91s (35.90CPU seconds): ALL 52,342native outputs and independent grades; corpus/task/selection/metric/hash/chain replay. Audit work is additional.

final: 9.54s wall, 2.248GiB sampled process-tree RSS. First audit PASS in 30.57s (30.26CPU seconds): ALL 50,400native outputs and independent grades; corpus/task/selection/metric/hash/chain replay. Audit work is additional.

Both intact controls solve every panel and final input; BFS/A*/bitwave solve all1680final queries (5040calls). The audit uses the production native VM and selection implementation with independent raster grading, not a second interpreter. No uncertain attempts, automatic resumes, budget extensions or scientific source repairs occurred.

Six focused software tests pass, not a full-suite claim. The first attempt had4passes/1failure because the test redirected output but not its temporaryROOT; the test-only fix and failed log are preserved. The discarded success-branch fixture intentionally substitutes an intact control for the parent alias, only in that labeled fixture. It does not alter the scientific pool or create a solver lineage. Its13012calls/5.90candidate seconds and4124generated layouts are excluded from scientific results.

Registration13d94e2 was pushed before scientific generation. Banks/predictions were pushed at 5bb5937 before independent generation. All312registration and356priorM10completion hashes verify. The original SQLite journal and verified API backup match every table and pass integrity checks. Preservation uses 1.136GiB, with 20.49GiBfree, inside4GiBtotal/16GiBfree bounds. All 2,840,891layouts are preserved (2,684,467initial, 150,944calibration, 5,480final). Checksummed gzip chunks and whole_layout_exclusions.json retain the full ledger without exceeding per-file upload limits. Future phases must load every part via retention_bank.load_layouts.

No new search, model promotion, case generation, temporal inference or phase beyond M11 was performed for this report. The diagnostic pool is informed by past failures and shares ancestry; passing this assay would justify a better-specified experiment, not establish general maze solving.

## Interpretation and recommendation

**The retention bank passes the registered calibration.** It rejects every one
of the 25 severe-loss diagnostic genotypes in each of three fresh bank panels,
with no false rejections under the sampled confirmation definition. The current
panels falsely accept 0, 11 and 1 respectively. Thus two panels improve strictly
and the summed reduction is12. All nonvacuity and positive-control checks pass.
The current panel works well in replicate0; this is evidence of variable detection
under sparse successful-case coverage, not a claim that the old scoring always fails.

The central change is the denominator. Current panels contain3,1and7 ordinary
bases the parent solves in both poses. Each bank contains24, explicitly spread
across six size/family/length strata. The quotas were feasible without extensions:
even the least productive stratum had11 qualifying parental successes among its
1,024unique ordinary base draws. All length-eligible reference responses were
computed before choosing the first4. Internal uniqueness retries remain subject
to the original generator limit and are recorded in the stage inputs; they are
not additional quota slots. Gated-partial successes in the banks are19,19,17;
gated-specialist successes are11,15,16. Both exceed the declared minimum8 in all
three banks, so the test does not depend on empty gated-reference denominators.

Fresh confirmation contains18 parental ordinary successes. The older shared
specialist retains8/18, the gated partial15/18 and gated specialist13/18. All are
severe-loss cases under the preregistered <90% definition, despite retaining useful
routing skills. The old scoring can overlook these losses: its top-ranked genome
retains18/18,8/18and15/18 across the three panels. The bank's top-ranked existing
genome retains18/18 in every panel. Its identity is the already-frozen M10
immediate-parent record m10/modular/1/rotating/g15/b17. This is a diagnostic ranking,
not a newly selected or evolved M11 solver. It has96pairs/200corridors/18ordinary/
168correct-disconnections/0false, matching the fixed parent's capability totals
on these same cases. It does not supply the missing combined specialist repertoire.

The comparison is not free extra information. Both methods score392inputs per
model per bank:35,280nominal queries per method across the30physical models and
three panels,70,560combined. The440-input union costs39,600physical scoring calls;
12,742additional fixed-parent calls construct the banks. Independent testing adds
50,400calls. The resulting102,742scientific calls cost60.84summed candidate seconds;
46.36seconds of phase wall time includes generation/evaluation overhead, while
commit/push and the66.48seconds of audits are additional. Native replay verified
every scientific response, rather than a sampled subset.

This result answers a narrower question than solver viability: on this frozen,
related, historically informed pool, positive-reference coverage reliably reveals
the large ordinary-skill losses that a small unconditioned panel sometimes misses.
It does not establish sensitivity to all future mutants, all maze families or every
small loss. The independent truth set has18 parental successes, the bank omits a
16+quota, and the three comparisons reuse the same28diagnostic genotypes and the
same final corpus. Do not turn these into75independent evolutionary observations
or infer statistical significance. Bank conditioning and the chosen diagnostic
pool are explicit design biases; unbiased final evaluation remains necessary.

**Next recommendation:** a separately registered, bounded matched evolution
comparison using persistent bank-based retention measurement versus the existing
measurement, with the same founders, runtime, mutation operator and prospective
query budgets. Use the bank for survivor scoring and nomination, while keeping
neutral and complementary-specialist capacity so imperfect intermediates can
still reproduce. Passing full retention should govern claims and nomination,
not require every newborn to be an already complete solver. Freeze the resulting
choices before new independent tests, and retain the separate requirement for
new deeper-prefix routing beyond exact roots and the protected union.

That experiment would test whether improved measurement helps evolution accumulate
skills. M11 establishes that the proposed measurement can distinguish the current
tradeoffs; it supplies no evidence yet that evolution will overcome them. The
random-origin lineages remain preserved, and no known-solver code has entered them.
No next evolution run has been launched or authorized by this calibration itself.
