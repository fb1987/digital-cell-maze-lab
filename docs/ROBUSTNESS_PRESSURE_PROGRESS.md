# V12K progress

Active study: robustness pressure, authorized by “Continue with the proposal.”
Protocol/foundations/panel/fixtures were committed and pushed in **b1eee27** before
main generation. Closed V12G–J remain untouched. See
`docs/ROBUSTNESS_PRESSURE_V12K.md` for the frozen numerical rules.

Calibration passes: eight new scientific fixtures (640 inputs), retained unit
geometry cases separately preserved in `geometry_test_mazes.json.gz`; known-control
correctness, both near goal-arm shapes, class-weighted profile. 10,880 calibration
calls, 8.394 candidate seconds. Twenty-nine focused tests passed (eight K, nine J,
twelve G); not a fresh full suite. Early pre-registration syntax/geometry-check
errors were fixed before candidate calibration; the disconnected prefix-one source
correctly has degree zero. No fixture construction was changed.

Independent diagnostic complete: 24 contexts, 1,920 inputs/model/mode, fourteen
fixed J-informed models, normal/nonlocal-zero, 53,760 calls, 93.345 candidate seconds
inside the 180-second cap. Branch narrow 96→128 pairs and broad 88→128. Broad gains
on four contexts across both goal shapes; narrow only two straight-goal contexts.
Neither gains prefix-four/eight pairs. No modifications to the frozen search
based on these results. Exact replay audit pending.

The 720-second matched search is running. At eight generations, only carry/local
replicate two has genetically diverged between policies; this weak activation of
the pressure contrast must be reported, not treated as twelve distinct treatment
responses. All cases/calls remain matched. No extension authorized by this note.

Next: finish the bounded run; commit and push full next populations/RNG and frozen
selections BEFORE `robustness_study final`. Then final assessment, frozen exact
replay audit, supplemental completeness/provenance audit, saved-only analysis and
figures; update report/handoff/exclusions, hash completion packet, commit/push.

Commands use `.venv/bin/python -m maze_evolution.robustness_study <action>`.
Actions: prepare/calibrate/freeze/diagnostic/run/final/audit/analyze. Do not repeat
completed actions. Plot with `PYTHONPATH=output/plot-libs .venv/bin/python
 tools/plot_robustness_pressure.py`. Supplemental tools do not alter frozen source.
