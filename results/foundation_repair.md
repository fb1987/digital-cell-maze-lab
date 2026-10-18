# V12B: reliable bounded repair supports the longer search

The preregistered repair gate passes. The single-edit policy was selected on validation before fresh confirmation: six exact validation repairs versus four for the 1–6-edit policy. On fresh layouts it repairs all three west-return defects, two of three output-register defects, and one of three two-return defects. The intact solver and BFS pass every confirmation input. This establishes bounded repair capability in known-solver descendants, not random-origin discovery.

| Defect / policy / replicate | Generations | Validation shortest | Frozen fresh shortest | Selected fresh shortest | Complete fresh shortest pairs |
|---|---:|---:|---:|---:|---:|
| west_return_gate/wide/r0 | 33 | 96/96 | 40/96 | 96/96 | 48/48 |
| west_return_gate/single/r0 | 9 | 96/96 | 40/96 | 96/96 | 48/48 |
| west_return_gate/wide/r1 | 17 | 96/96 | 52/96 | 96/96 | 48/48 |
| west_return_gate/single/r1 | 49 | 96/96 | 52/96 | 96/96 | 48/48 |
| west_return_gate/wide/r2 | 64 | 38/96 | 44/96 | 44/96 | 10/48 |
| west_return_gate/single/r2 | 17 | 96/96 | 44/96 | 96/96 | 48/48 |
| output_register/wide/r0 | 64 | 2/96 | 0/96 | 4/96 | 0/48 |
| output_register/single/r0 | 64 | 2/96 | 0/96 | 0/96 | 0/48 |
| output_register/wide/r1 | 64 | 2/96 | 0/96 | 8/96 | 0/48 |
| output_register/single/r1 | 9 | 96/96 | 0/96 | 96/96 | 48/48 |
| output_register/wide/r2 | 64 | 0/96 | 0/96 | 0/96 | 0/48 |
| output_register/single/r2 | 9 | 96/96 | 0/96 | 96/96 | 48/48 |
| two_return_gates/wide/r0 | 64 | 36/96 | 18/96 | 40/96 | 12/48 |
| two_return_gates/single/r0 | 9 | 96/96 | 18/96 | 96/96 | 48/48 |
| two_return_gates/wide/r1 | 9 | 96/96 | 28/96 | 96/96 | 48/48 |
| two_return_gates/single/r1 | 64 | 42/96 | 28/96 | 52/96 | 16/48 |
| two_return_gates/wide/r2 | 41 | 96/96 | 20/96 | 96/96 | 48/48 |
| two_return_gates/single/r2 | 64 | 14/96 | 20/96 | 20/96 | 2/48 |

Each replicate has six independent base layouts × eight symmetries × two goals: 96 responses and 48 pairs. Policies/defects share that replicate's corpus. The 1–6-edit policy passes two west-return and two two-return replicates, but no output-register replicates. With only three replicates per defect, the experiment does not establish universal superiority of single edits. Both policies received four rotations per training batch, with reflection alternating. Differences from V12A also include those batches and new layouts, so its improvement cannot be attributed solely to mutation size.

The single policy passes the fixed requirement of at least two successful replicates in at least two defect types. Each passing replicate has ≥95% fresh shortest outputs, ≥95% complete shortest pairs, and ≥25 percentage-point gain over its initial frozen control. No threshold was changed after confirmation. Failed conditions remain in the table.

Main cost: 4.87 minutes, 245.6 MiB peak RSS. Search/validation: 513,792 ordinary responses and 130,509,835,369 dispatch-plus-read work units. Fresh candidate/reference-organism confirmation: 3,744 responses. Independent audit: 39.90s, 47,240 fitness records, 39,984 replayed mutation traces, 3,744 selected normal replays, 288 BFS rasters, 105 source and 17 input hashes. All checks pass. Two focused tests verify single-edit traces, unchanged wide-arm parity, equal response counts and exact checkpoint continuation.

Seed 2026101814; preregistration commit `26fdd12`. This study adds 1,824 whole layouts across 228 base groups. Future studies exclude all **17,700** whole layouts through V12B, including unused constructed transforms. Full prepared populations, RNG state, founder identity and every mutation are retained.

Proceed with a separately preregistered 75-minute random-origin study using the selected single-edit policy, ordinary-output fitness and orientation coverage. Retain native populations and include fresh random cohorts, matched resampling and frozen controls. The repaired programs are excluded from every random-origin founder pool.

Protocol: [V12B](../docs/FOUNDATION_REPAIR_V12B.md). Raw packet: [summary](foundation_repair/summary.json), [verification](foundation_repair/verification.json).
