# V12Z completed and audited

The mutation versus family-reserve comparison is complete. The fixed 75-minute
allowance closed after 128 matched generations in 69.57 minutes, with 6,512,640 search
responses. Registration 8c01929; selections/search records ef1dca6 before final.

Read [the report](../results/family_evolution.md) and
[the next proposal](../results/family_evolution/next_experiment.md). No gate passes.
Family reserve increases structural variation but gives no final routing benefit.
Fresh ordinary mutation and resampling each reach 160/1,120 pairs in all three replicates,
all prefix-zero forks; family 160/0/160, frozen 0/0/4. No fresh positive-prefix pairs. Carried
primary correctness stays at its frozen baseline. Mutation reaches elementary
validation success earlier; final resampling catches up. Saved masks expose
one-cell branch stubs on prefix-one forks; outputs remain invalid and unmodified.

Audit passes on first attempt: 2465.55s wall,
3,294,531 exact main/profile/final replays plus 82,944 rehearsal,
6,819,616 independent grades plus 82,944 rehearsal,
all ancestry/RNG/checkpoints and 21,696 conventional baseline replays.
43 focused/related tests plus four archive/replay integrity tests pass; not a full-suite run.
No frozen source repair or protocol deviation.

All 24 next populations, RNG, raw masks, nominees, ancestry and locus IDs preserved.
Restore the large log using tools/archive_family_evolution_births.py restore.
For future audits use tools/replay_family_evolution_audit.py, which writes a
separate packet under output/ and leaves sealed artifacts unchanged.

Exclude **272,464 whole layouts** through Z using
results/family_evolution/whole_layout_exclusions.json.gz plus later fixtures.
Completion adds 957 sealed entries; future prior total 7880.
Do not repeat or extend Z, silently resume its states, or tune on inspected finals.
The next mechanism/activation work is a proposal only; no sexual long run launched.
