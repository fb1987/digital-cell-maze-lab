# V12A: runtime works, reliable repair remains unestablished

The current runtime/goal-pulse convention passes the intact solver controls. **Only one of nine damaged-program runs passes fresh repair confirmation**, so the preregistered reliability gate is **false**. The long random-origin experiment is deferred while search stability is tested. These are known-solver repair controls, not random-origin discoveries.

The intact program solves all 136 reachable matrix inputs optimally and correctly reports all 8 disconnected targets, under both local/evolved topology and goal pulse off/on. The matrix comprises independent base layouts with correlated rotations/reflections; the four input/topology settings reuse the same inputs. All earlier source/raw results remain unchanged.

| Damage / replicate | Generations | Selected validation shortest | Frozen fresh shortest | Selected fresh shortest | Fresh complete shortest pairs |
|---|---:|---:|---:|---:|---:|
| west_return_gate/r0 | 128 | 50/96 | 42/96 | 42/96 | 14/48 |
| west_return_gate/r1 | 128 | 38/96 | 44/96 | 42/96 | 12/48 |
| west_return_gate/r2 | 128 | 48/96 | 46/96 | 46/96 | 18/48 |
| output_register/r0 | 128 | 8/96 | 0/96 | 2/96 | 0/48 |
| output_register/r1 | 128 | 6/96 | 0/96 | 8/96 | 0/48 |
| output_register/r2 | 9 | 96/96 | 0/96 | 96/96 | 48/48 |
| two_return_gates/r0 | 128 | 50/96 | 20/96 | 42/96 | 14/48 |
| two_return_gates/r1 | 128 | 40/96 | 20/96 | 38/96 | 10/48 |
| two_return_gates/r2 | 128 | 26/96 | 24/96 | 24/96 | 8/48 |

Each replicate's fresh confirmation is six independent base layouts, each tested in eight symmetries under two goals. Thus 96 responses and 48 pairs are **not 96 independent layouts**. The three damage types share each replicate's confirmation corpus. The one successful output-register lineage reaches 96/96 shortest outputs and 48/48 complete pairs; its initial frozen control solves 0/96. The other conditions do not establish reliable repair. BFS solves all 288 confirmation responses across the three replicates.

The repair founders contain the exact stated defect and no intact program. Every child is traced to a damaged founder through recorded bounded edits. No solver genotype, repaired or otherwise, may enter any native/fresh random-origin population. Exact genotype identity is not required for functional repair; genotype counts in `report_analysis.json` are descriptive only.

The new ordinary-output score recognizes coherent growth back from the goal that the source-only partial score misses. Counts of invalid ordinary outputs receiving positive new credit while old partial credit is zero, for the local/pulse setting: `{'intact': 0, 'west_return_gate': 66, 'parent_gate': 128, 'output_register': 0, 'two_return_gates': 98, 'two_dependencies': 0}`. This demonstrates that useful partial traces can be visible to the new score, but the failed repair gate shows that this change alone is insufficient for reliable search.

For the intact program, bounded observations with ordinary stopping give:

| Observation cap | Raster-only legal paths | Incomplete traces with new credit and zero old credit |
|---|---:|---:|
| 8 | 56/144 | 48 |
| 16 | 104/144 | 24 |
| 32 | 128/144 | 8 |
| 64 | 136/144 | 0 |

These are diagnostic snapshots, including truncated trajectories. Their raster legality is not a claim of ordinary emission at that cap. Selection uses only the actual normal response under the full bound; forced development never contributes fitness. Full state hashes and ordinary/forced observations at 8/16/32/64 are saved and replayed.

The first two west-gate searches never recreate the exact original intact genotype, although they produce some perfect four-input training batches. This does not exclude equivalent repairs elsewhere. It motivates testing smaller mutations and more orientation coverage within each training batch, rather than assuming extra runtime alone will solve retention.

Main calibration: **5.18 minutes**, peak process RSS **267.7 MiB**. Matrix: 3,456 ordinary responses/27,648 probes; repair search/validation: 369,664 ordinary responses; fresh organism confirmation: 1,728 responses. Logical repair work: 137,514,121,329 dispatch-plus-read units. This is calibration cost, separate from a future 60–90-minute random-origin study. It is not an inference-speed comparison.

Independent audit: **67,208 fitness records**, **57,848 mutation traces**, all selected confirmation outputs, and **27,648 full-state probe replays** pass. Audit time: 48.76s, charged separately. All 101 frozen source hashes and 13 prior-manifest hashes match. Original regression run: 128 passes; six focused checks after final additions cover the 129 then-current tests. Those test runs preceded the experiment; the independent audit follows it.

Seed 2026101812; preregistration/final control-score revision `81f74a4`. Every selected model was frozen before fresh confirmation construction. The study excludes 9,376 prior/fixture whole layouts and constructs 6,500 additional whole layouts across 813 base groups; future studies must exclude all **15,876**. Data were generated in advance of repair, including all symmetries, so constructed-layout counts exceed the layouts actually queried in training. Some orbits contain symmetric duplicates.

Next: [V12B repair protocol](../docs/FOUNDATION_REPAIR_V12B.md), comparing one-edit versus 1–6-edit mutation on identical orientation-balanced batches. This uses fresh layouts and preserves V12A's negative outcome. It changes the learning conditions without placing a known solver in a random lineage.

Protocol: [V12A](../docs/FOUNDATION_CALIBRATION_V12A.md). Raw data, checkpoints, source/input hashes and verification: [packet](foundation_calibration/summary.json).
