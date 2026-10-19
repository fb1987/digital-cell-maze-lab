# V12G progress

2026-10-19: authorized minimal-fork proposal implemented and calibrated. Known
controls remain outside random-origin populations. All 12 new focused tests
pass. Old sources/results are unchanged. Read `docs/FORK_PRESSURE_V12G.md` for
fixed seeds, counts, budget and final-assessment rules.

Initial 30 states and their parent provenance are prepared. Next operation:
commit/push this preregistration, then run the one bounded 720-second pilot with
`.venv/bin/python -m maze_evolution.fork_study run`. Do not restart or extend its
budget. Check `results/fork_pressure/search_summary.json` and checkpoint before
any recovery. Freeze/push selections before running `fork_confirm`; then run
`fork_audit`, report evidence and preserve all states/RNG/raw masks.

Pilot complete:113 matched generations in706.51 seconds (11.78 minutes),
2,236,032 physically evaluated responses,269,773,599,386 work units,
927.14MiB peak RSS. Search stopped using its conservative wall reserve.
No budget extension. Initial validation41.54seconds is included. All next
populations/RNG and archives are preserved. The validation gate was computed
before fresh final generation in `validation_gate_before_final.json`.

The audit uses `tools/audit_fork_pressure.py`: it preserves the preregistered
checks while releasing verified historical program objects from RAM, and adds
founder/anchor and calibration checks. Original audit code stays unchanged.
No search or final-assessment rule changed. All analysis/plot code is prepared
before final generation. Next:push frozen selections, then confirmation/audit.
