# Compatible recombination study progress

V12S search is complete under the user-authorized three-step goal. Steps 1 and 2 are
complete in `results/research_reset/assessment.md`; step 3 is in progress.

Preregistration and frozen scientific source were committed and pushed in
`f650b93`. The feasibility profile passed and was pushed in `4750c0f` before
validation generation. No frozen scientific source has changed.

The search command is `.venv/bin/python -u -m maze_evolution.composition_study run`.
It completed 294 matched generations in 4,333.10 seconds under the fixed
4,500-second search-wall allowance, including initial validation, and stopped
at its registered reserve. There were 9,206,784 physical candidate calls and
3,113.70 candidate seconds. Do not restart, extend, or retune it.
Progress is in `results/composition_study/search.log`.
Raw histories, all 18 population/RNG states and every 32-generation checkpoint
are saved. Final data have not yet been generated.

The completed birth log has been losslessly packaged with
`tools/archive_composition_births.py pack` into six byte chunks; the original is
preserved locally. Commit/push all scientific artifacts and selections before `confirm`. The remote
byte chunks restore the exact original via the same tool's `restore` action.
Then run `confirm`, `analyze`, and the frozen independent `audit`. Do not mark the
goal complete before audit, report, saved checkpoints and remote synchronization.

Additional descriptive tools in `tools/*composition*.py` perform no candidate
inference. They are separate from the frozen scientific comparison. Their final
outputs must distinguish direct mating, splice ancestry, inherited ability,
validation improvement and untouched transfer. Only both-stage replicated gates
can support the primary comparison; other results remain secondary.

The source-first report generator is a draft pending final results. Complete its
interpretation after seeing confirmation and ancestry, render/check the figure,
then seal with `tools/complete_composition.py`. Update this handoff, AGENTS and
README, preserving all historical packets. No next experiment is authorized by
an automatic gate; finish the bounded study and report the evidence.
