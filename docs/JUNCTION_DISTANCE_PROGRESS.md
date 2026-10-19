# V12J progress

User authorized the proposed bounded junction-distance diagnosis after V12I.
Panel, protocol, implementation and fixtures are frozen; main cases have not yet
been generated. No evolution or prior-result edits. Calibration passed with
2,318 calls / 2.73 measured candidate seconds; rough main estimate388.01s.
Main budget720candidate seconds /280,000calls; planned277,152calls.
Nine new +19 related tests pass (28total); not a fresh full-suite run.

Read docs/JUNCTION_DISTANCE_V12J.md. Run only after registration commit is pushed:
`.venv/bin/python -m maze_evolution.junction_distance run`
Then `audit` and `analyze`. Do not restart a partially generated main study or
extend its cap. Save incomplete outputs and investigate any audit failure
without overwriting frozen sources. All models, targets and context subsets
are fixed; no result-adaptive changes. All144,120old layouts plus512Jfixture
layouts are excluded before the main draw.
