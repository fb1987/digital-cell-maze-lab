# Completed calibration-first research plan

The October 18 user-authorized research goal is complete: calibration, ordinary
developmental scoring, a justified stable 75-minute search, fresh confirmation,
independent audit, analysis and figures. Read `results/foundation_study.md`.
The next continuation is a recommendation and has not been launched.

- V12A verifies intact controls but fails its repair gate: fresh successful
  replicates 0/3 west return, 1/3 output register, 0/3 two return gates.
  Main 310.802s; audit 48.759s. Packet: `results/foundation_calibration/`.
- V12B selects single edits on validation (six exact repairs versus four for
  1–6 edits) and passes fresh confirmation: 3/3, 2/3, 1/3 successful replicates,
  versus 2/3, 0/3, 2/3 for wider edits. Main 291.908s; audit 39.904s.
  Packet: `results/foundation_repair/`. These known-solver descendants remain
  strictly separate from every random-origin population.
- V12C completes 442 matched generations in 4509.093s across 24 conditions of
  96 organisms. Each receives 555,264 ordinary responses; total 13,326,336.
  Peak search RSS 436.0 MiB. All replicates finish at curriculum level 1.
  Preregistration `74b2588`; final and earlier selections committed/pushed in
  `16bfc3f` before any final layouts were generated.

Fresh local evolution passes the elementary screen in two of three replicates:
86/864 non-adjacent shortest outputs and 9/432 complete shortest pairs, spanning
five independent base groups. Resampling and initial frozen selections score
zero. No fresh-local group works in all eight poses. Other cohorts pass in 1/3
native local, 1/3 native multirange and 0/3 fresh multirange replicates.

The secondary time course gives fresh local 0/8/36/86 non-adjacent outputs and
0/0/2/9 pairs at generations 48/128/256/442. All time points reuse the same final
corpus; they are correlated measurements. Fresh-local primary lineages descend
from random immigrants introduced during the run, never known solvers.

Ordinary primary shortest counts are 6/216 native local, 6/216 native multirange,
7/216 fresh local and 3/216 fresh multirange, versus 2/216 for each resampling
cohort. Every cohort solves 0/181 ordinary distance≥8 and 0/48 disconnected
cases. BFS/A*/bit-wavefront solve 216/216 and 48/48. The intact wavefront control
solves 209/216 and 48/48; seven long tree paths hit the 1024-tick cap. Eligible
elementary candidate outputs have a median 48.95× runtime ratio to BFS. General
solving, a net multirange advantage and competitive efficiency remain open.

Main audit passes: 110 source hashes, 26 input hashes, 893,376 registered
programs, 397,800 mutations, 1,026,048 fitness records, 5,972,328 independently
graded search rasters, every final raster and 25,456 distinct final replays.
Audit 283.586s and 726.8 MiB peak RSS; fresh confirmation 48.728s. Time-course
freeze 26.781s; new time-course evaluation/replay 10.530s (10,368 new outputs,
each replayed). Post-hoc interventions 1.993s: 680 successful combinations;
pulse removal retains 277 shortest outputs, nonlocal zeroing 672, both 273.
All 2,720 intervention rasters are independently graded. Pulse removal leaves
static goal flags and endpoint-aware halting intact.

Full `pytest -q tests`: 136 passes. The subsequently added time-course unit
passes separately, covering 137 current tests. A prior unscoped pytest command
accidentally collected third-party plotting-package tests and failed collection;
it was replaced by the correctly scoped successful project run. Optional
Matplotlib 3.11.2 is isolated in ignored `output/plot-libs`; the experiment
runtime environment did not change. Saved figures were visually inspected.

All prior source/raw packets remain immutable. V12C next populations/RNG are in
`results/foundation_study/checkpoints/` and `checkpoint.latest.json.gz`; raw
records are in `segments/`. `discussion.md` supplies the report's editorial
interpretation. Primary selections remain distinct from secondary skill archives.
The extra fresh-local example is a labelled post-hoc illustration, not an assay.
Future studies must exclude all **52,424 whole layouts**, including unqueried
general symmetries and software fixtures.

The next proposed experiment is one separately preregistered, unchanged
75-minute continuation of all 24 prepared states, using today's frozen selections
as additional controls. Keep capacity, mutation, runtime, curriculum and
selection fixed. Require replicated paired-route gains plus orientation or
4–8-edge transfer and adjacent-skill retention before further escalation.
Do not inject known solvers, select on inspected final cases, silently increase
old budgets, or launch this recommendation as part of the completed goal.

Inspection/reproduction of derived reports:

```bash
.venv/bin/python -m maze_evolution.foundation_study_audit --out results/foundation_study
.venv/bin/python -m maze_evolution.foundation_study_report --out results/foundation_study
PYTHONPATH=output/plot-libs .venv/bin/python tools/plot_foundation_study.py --out results/foundation_study
```

Completed raw packets refuse rerun. Use a new output directory for reproduction;
a new independent study also needs a new protocol, seed and updated exclusions.
