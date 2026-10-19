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
