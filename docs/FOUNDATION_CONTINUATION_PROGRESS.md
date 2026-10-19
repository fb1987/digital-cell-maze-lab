# Completed V12D continuation

User authorized this follow-up after the completed V12 calibration-first goal.
The new study was preregistered and pushed in `7e30e60` before launch on
October 18, 2026. It resumes all 24 V12C states at generation 442 under an unchanged
75-minute wall-time budget. See `FOUNDATION_CONTINUATION_V12D.md`.

Search completed 423 additional matched generations (442→865) in 4519.379 seconds
(75.32 minutes, including the final matched round and saves). It evaluated
12,427,776 additional responses, 517,824 per condition, with 472.05 MiB peak RSS.
All curricula remain at level 1. The full search packet and every final/control/
time-course selection were committed and pushed in `1c22023` before any new
confirmation layouts were generated. Confirmation, independent audit, time
course, interventions, report and figure inspection are complete.

Fresh-origin evolved-range primary selections pass the stronger screen in 2/3
replicates: 28/432 complete non-adjacent shortest pairs, versus zero for their
V12C checkpoint and continued resampling on the same new cases. Three independent
base layouts work under all eight paired poses; all 144 adjacent pairs are
retained. Individual non-adjacent shortest outputs rise 30/864→103/864. Most
successes have two-edge routes; no primary model completes a pair in dedicated
4–8- or 8–16-edge levels. The same-corpus time course gives 0/0/8/22/28 pairs at
additional generations 0/48/128/256/423. These are correlated observations.

Goal-pulse removal eliminates all 28 paired successes; zeroing nonlocal values
preserves all of them. This successful-case intervention supports dependence on
the pulse, not a causal multirange advantage. Every current primary cohort
solves 0/176 ordinary distance≥8 cases. Best ordinary cohort: 7/216 reachable;
BFS/A*/bit-wavefront: 216/216 and 48/48 disconnected. Eligible random-origin
elementary timings are median 63.25× slower than compiled BFS.

The audit passes 380,700 new mutations, 979,680 fitness records, 6,274,032
independently graded search rasters, all 63,840 final raster aliases, 33,912
distinct candidate replays and 792 reference replays. It verifies every saved
fitness calculation, every validation raster and training success, plus a
1/512 sample of other training records. Source/input/ancestry/layout/archive/
schedule/counter checks pass. Costs beyond search: confirmation 81.99 s,
audit 350.56 s, time-course inference/replay 10.36 s, interventions 2.49 s.
The preconfirmation time-course selection freeze took 30.11 s. Audit peak RSS
was 1009.3 MiB. Reporting, figures, software checks and Git operations are
additional, not included in the 75.32-minute search cost.

All **85,548 whole layouts** through V12D are excluded from future independent
studies. New training/final generation excluded all 52,424 older layouts;
V12C validation was intentionally reused for selection. Full populations/RNG,
raw data, all selected/ancestral variants and prior studies remain preserved.
The recommended matched complete-pair-first selection test has not been launched.

The completed command was:

```bash
caffeinate -i .venv/bin/python -u -m maze_evolution.foundation_continuation --out results/foundation_continuation
```

The ignored `output/foundation_continuation.log` retains execution progress;
global atomic state is `results/foundation_continuation/checkpoint.latest.json.gz`.
The completed output refuses overwrite. A reproduction uses a new directory
and the original environment seed, so it is not a new independent experiment.
Do not restart founders or add time to this completed packet. Parent V12C data
and all completed V12D search/final records are immutable.

Preflight: 4 tests pass, all 24 full restored states match, five representative
next steps match uninterrupted execution on already excluded fixtures.
Two additional confirmation regressions pass. No new software maze layouts
were introduced. The early read-only integration audit through generation472
passes 69,408 fitness records and 427,380 independently graded saved rasters.
All 119 frozen source hashes and 36 input hashes are unchanged. Auxiliary code
was committed in `f5bf208`; it does not change the search. There are six new
regression passes beyond the 137 previously covered project tests; no fresh
full 143-test run is claimed. See `software_checks.json`.

The following stages were completed in order. These are the recorded commands,
not instructions to overwrite the finished packet. For reproduction, substitute
a new output directory throughout and freeze/commit selections before final
generation:

```bash
.venv/bin/python -m maze_evolution.foundation_continuation_timecourse --out results/foundation_continuation --freeze
# Commit and push the selection packets before the next command.
.venv/bin/python -m maze_evolution.foundation_continuation_confirm --out results/foundation_continuation
.venv/bin/python -m maze_evolution.foundation_continuation_audit --out results/foundation_continuation
.venv/bin/python -m maze_evolution.foundation_continuation_timecourse --out results/foundation_continuation
.venv/bin/python -m maze_evolution.foundation_continuation_interventions --out results/foundation_continuation
.venv/bin/python -m maze_evolution.foundation_continuation_report --out results/foundation_continuation
PYTHONPATH=output/plot-libs .venv/bin/python tools/plot_foundation_continuation.py --out results/foundation_continuation
```

The interpretation is saved in `results/foundation_continuation/discussion.md`
and incorporated into `results/foundation_continuation.md`. Figures show both
short-pair successes and ordinary-maze failures. Illustration cohort/case choices
are labelled post hoc and do not constitute another assay. Current project
documentation and the completed evidence packet are synced with GitHub.
