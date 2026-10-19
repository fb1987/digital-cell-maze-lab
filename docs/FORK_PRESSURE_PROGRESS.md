# V12G completed handoff — October 19, 2026

Read `results/fork_pressure.md` for findings and `docs/FORK_PRESSURE_V12G.md` for
the frozen protocol. The authorized calibration, bounded pilot, fresh final
assessment, independent audit and report are complete. **Do not repeat or extend
this run.** No new study has been launched.

- Preregistration/initial population freeze: `83f78c6`, pushed before search.
- Final selection freeze: `f1b6bf9`, pushed before final-case generation.
- 30 populations × 96 organisms, 113 matched generations, 706.51 seconds.
- 2,236,032 search responses; 269,773,599,386 work units; 927.14 MiB peak RSS.
- All population/RNG continuations: `results/fork_pressure/checkpoint.latest.json.gz`.
- All frozen pair/choice/task/corridor archives: `frozen_selections.json.gz`.
- Fresh confirmation: `confirmation/`; complete raw lineage/evaluation segments
  in `segments/`; initial states and donor-anchor provenance are retained.

Primary complete pairs across three replicates, each cohort denominator 576:

| Cohort | Frozen | Current | Branch | Resampling |
|---|---:|---:|---:|---:|
| Carry local | 146 | 150 | 128 | — |
| Carry multirange | 124 | 146 | 216 | — |
| Fresh local | 0 | 2 | 6 | 2 |
| Fresh multirange | 0 | 0 | 8 | 32 |

The strongest primary is carry/multirange/Branch replicate 0, birth 64, genotype
`2ba155ca959bcd9ff058`, id `fork/carry/evolved/branch/evolution/0/i4549`. It completes
128/192 pairs, 16 bases in all eight poses, including 6/8,8/7,8/9 and 9/9-edge pairs.
It is a255-gene random-origin descendant of a protected V12E validation variant.
Its successful pairs all survive pulse removal and nonlocal zeroing. Static
flags and endpoint-aware halting remain; do not claim a causal multirange gain.
The fresh multirange resampling control's68-gene random draw completes 32 pairs,
so consistent fresh-evolution superiority is not established.

Only 1/3 carry/local and 1/3 carry/multirange validation replicates pass the
larger-run gate; fresh 0/3. No cohort qualifies. Validation has four independent
bases per replicate, not 32 independent paired poses. The longer challenge has
only eight independent bases. Cycles are dangling loops; every legal route is
unique. No ordinary large-maze or alternative-route shortest-path claim follows.

Audit passes all 2,236,032 search rasters, 328,392 fitness records, 170,856 concrete
mutations, 244,080 deterministic birth/RNG replays, 30 final states and 43,080 final
candidate replays. It checks 146 frozen source and 11 input hashes. Active audit
is `tools/audit_fork_pressure.py`; the original frozen auditor remains intact.
The bounded variant releases already-verified historical objects. A JSON tuple/
list comparator failure was diagnosed and repaired; the complete audit reran
successfully in224.21seconds. See `audit_serialization_repair.json` and
`audit_implementation_note.json`. No candidate inference rule or search changed.

Twelve new tests pass, 175 tests are collected; no fresh full 175-test run is
claimed. Figures were inspected and the raw measurements/report are preserved.
All historical V1–V12F source/results remain untouched. Future studies must
exclude **136,536 whole layouts**, including all fixtures and unused poses.
`results/fork_pressure/next_experiment.md` proposes a bounded fixed-variant
mechanism/transfer test and a separate broader-validation comparison. Neither
has been launched. No retuning against inspected final cases.
