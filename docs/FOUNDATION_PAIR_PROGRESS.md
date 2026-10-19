# V12E controlled comparison

The user authorized the matched completed-pair-priority comparison after V12D.
Protocol: `docs/FOUNDATION_PAIR_V12E.md`. Implementation: separate
`maze_evolution/foundation_pair*.py`; output: `results/foundation_pair/`.
Do not modify completed V12A–D source/raw data or extend their budgets.

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

Run after preflight and preregistration commit/push:

```bash
caffeinate -i .venv/bin/python -u -m maze_evolution.foundation_pair --out results/foundation_pair
```

Use `--resume` only for an interrupted unfinished packet. Confirmation, audit,
time-course, report and visual artifacts must be completed before claiming the
comparison finished. See the new packet's software checks for preflight results.
