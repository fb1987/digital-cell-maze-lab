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
