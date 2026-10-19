# V12D continuation progress

User authorized this follow-up after the completed V12 calibration-first goal.
The new study was preregistered and pushed in `7e30e60` before launch on
October18,2026. It resumes all24 V12C states at generation442 under an unchanged
75-minute wall-time budget. See `FOUNDATION_CONTINUATION_V12D.md`.

Search is running locally with:

```bash
caffeinate -i .venv/bin/python -u -m maze_evolution.foundation_continuation --out results/foundation_continuation
```

Live progress is in ignored `output/foundation_continuation.log`; global atomic
state is `results/foundation_continuation/checkpoint.latest.json.gz`.
If interrupted before `search_summary.json` exists, use the same command with
`--resume`; do not restart founders or add time. Parent V12C data is immutable.

Preflight:4 tests pass, all24 full restored states match, five representative
next steps match uninterrupted execution on already excluded fixtures.
Two additional confirmation regressions pass. No new software maze layouts
were introduced. The early read-only integration audit through generation472
passes69,408 fitness records and427,380 independently graded saved rasters.
All119 frozen source hashes and36 input hashes are unchanged. Auxiliary code
was committed in `f5bf208`; it does not change the search.

After search finishes, freeze and commit every primary/control/time-course
selection **before** final generation, then complete the following stages:

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

Write the evidence-based interpretation in the new packet's `discussion.md`,
regenerate the report, visually inspect figures, update current docs and sync
all completed raw data with GitHub. No final cases have yet been generated.
Do not call the stronger criterion passed from validation or proxy scores.
