# V12E controlled comparison

The user authorized the matched completed-pair-priority comparison after V12D.
Protocol: `docs/FOUNDATION_PAIR_V12E.md`. Implementation: separate
`maze_evolution/foundation_pair*.py`; output: `results/foundation_pair/`.
Do not modify completed V12A–D source/raw data or extend their budgets.

Preregistration and training code were committed/pushed in `c8fe1cf` before launch.
Search started October 18 at approximately 21:47 Toronto time (October 19 01:47
UTC), with the one fixed 4500-second budget. Execution log:
`output/foundation_pair.log`; atomic full-state checkpoint:
`results/foundation_pair/checkpoint.latest.json.gz`. Search is in progress;
no final confirmation layouts have been generated. The appearance of
`search_summary.json` marks completed search, not completed confirmation/audit.

Eight new preflight tests are covered. The first attempt passed six tests and
found a test-reader field error (integer count versus event list); the corrected
tradeoff test and new paired-resume test then both passed. Two additional audit/
time-course regressions pass, including rejection of a corrupted RNG hash.
No old source was changed. Full details: `results/foundation_pair_preflight.json`
and `results/foundation_pair/software_checks.json`.

The read-only audit through generation 905 (40 new generations) passes 69,480
fitness records, 559,872 independently graded rasters and exact reproduction of
60,480 new programs (36,000 mutations and 24,480 immigrants), including population
and RNG hashes. It took 38.47 seconds during search, added no candidate inference
or new layouts, and found that global ordering changes some retained genotypes
and parent choices. This is process verification, not unseen performance evidence.
Auxiliary code and the early proof were pushed in `c30f3a1`; reporting and figures
were added in `52cd492`. All final conclusions remain pending.

Eighteen conditions fork the generation-865 fresh-origin states: local/evolved
× Current evolution/Paired evolution/Current resampling × three replicates.
Current and Paired evolution inherit identical populations and RNG states.
Primary selections use the same paired-first validation archive in both arms;
common original-rank archives are retained as secondary selections. New training
and final layouts exclude 85,548 earlier layouts plus 80 construction fixtures.
Old validation remains explicit reused selection data. No known solvers enter
these lineages.

The fixed search budget is 4500 seconds across all conditions, finishing the
current matched round. The final gate requires new 3–8-edge paired transfer,
independent groups, all-pose success and adjacent/two-edge retention. Save full
population/RNG state and lineage every ten rounds. Freeze/push all final and
prespecified time-course selections before generating final layouts.

The running search command is:

```bash
caffeinate -i .venv/bin/python -u -m maze_evolution.foundation_pair --out results/foundation_pair
```

Use `--resume` only for an interrupted unfinished packet. Confirmation, audit,
time-course, report and visual artifacts must be completed before claiming the
comparison finished. See the new packet's software checks for preflight results.

After successful search completion, run these stages in order. Commit and push
the complete search packet and frozen selection files before the confirmation
command. Do not regenerate founders or overwrite completed output.

```bash
.venv/bin/python -m maze_evolution.foundation_pair_timecourse --out results/foundation_pair --freeze
# Commit/push the training packet and selection freeze before final-case generation.
.venv/bin/python -m maze_evolution.foundation_pair_confirm --out results/foundation_pair
.venv/bin/python -m maze_evolution.foundation_pair_audit --out results/foundation_pair
.venv/bin/python -m maze_evolution.foundation_pair_timecourse --out results/foundation_pair
.venv/bin/python -m maze_evolution.foundation_pair_interventions --out results/foundation_pair
.venv/bin/python -m maze_evolution.foundation_pair_report --out results/foundation_pair
PYTHONPATH=output/plot-libs .venv/bin/python tools/plot_foundation_pair.py --out results/foundation_pair
```

Write the interpretation in `results/foundation_pair/discussion.md`, regenerate
the derived report, inspect figures, update project checkpoint documentation and
sync all evidence with GitHub. Independent audit and report overhead are separate
from the fixed search time; no automatic search extension is authorized.
