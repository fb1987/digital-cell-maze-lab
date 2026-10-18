# Active research goal: calibration and a longer random-origin study

The user explicitly authorized completion of the October 18 audit's next steps as a goal. Goal remains active. Work locally; no cloud, LLM calls or solver injection into random-origin populations.

1. **V12A complete and verified.** Read `results/foundation_calibration.md` and `docs/FOUNDATION_CALIBRATION_V12A.md`. Current runtime, pulse convention and intact wavefront control pass all 136 reachable and 8 disconnected matrix inputs under both topology/pulse settings. Timing observations confirm that ordinary goal-connected partial traces can receive useful credit. But repair reliability fails: successful fresh confirmations are 0/3 west-return defects, 1/3 output-register defects, 0/3 two-return defects. The single repaired control solves all 96 fresh responses/48 pairs (six independent base layouts × eight symmetries). This is known-solver repair, not random-origin emergence.
2. **V12B complete and verified; gate passes.** Read `results/foundation_repair.md`. The single-edit policy was selected from validation before fresh confirmation: six exact repairs versus four wide-policy repairs. Fresh successful replicates: single 3/3 west return, 2/3 output register, 1/3 two-return; wide 2/3, 0/3, 2/3. All intact/BFS controls pass. Main291.908s, RSS245.6MiB; audit39.904s checks47,240 fitness records,39,984 mutation traces,3,744 normal replays,288 BFS rasters,105 sources/17 inputs. These remain known-solver descendants only. Single edits are the preregistered chosen policy, not established as universally superior.
3. **Longer study being prepared.** Profile and preregister one stable 75-minute random-origin experiment:96 organisms, native V11 cap256 and separately labelled fresh random cohorts, local/evolved topology, three replicates, evolution versus evaluation-budget-matched resampling, plus frozen initial selections. A competence-based progression from elementary paired goals to longer forks must retain earlier skills. Use orientation coverage and ordinary-output scoring. Set exact generation/compute caps and confirmation corpus after profiling, before training. No early-excitement extension gate; keep the precommitted time budget. New modules `foundation_study*` are not frozen until that preregistration/run; V12A/B modules and raw packets are immutable.

The V11 native founders are the six files in `results/capacity_growth/checkpoints/growth_{local|evolved}_cap256_{0|1|2}.json`, each with 96 prepared organisms plus RNG/protection records. Preserve all of these and useful variants on disk. Native and fresh founders must be identical between evolution/resampling comparisons; preserve or explicitly record their RNG forks. The known/repaired programs in `foundation_calibration` or `foundation_repair` must never be included in those founders.

V12A main elapsed 310.802s (5.18min), peak RSS267.7MiB. Independent audit48.759s:67,208 fitness records,57,848 mutation traces,1,728 selected normal replays,27,648 full-state probe replays,101 sources/13 old input hashes. All pass. Existing full suite128 passed in421.65s; six later focused checks cover129 then-current tests. Two new V12B-focused tests also pass. V12A raw/source files are immutable; additions use separate modules.

Exclude **17,700** whole layouts through V12B:9,296 historical,80 fixture,6,500 V12A and1,824 V12B. All transformations of a final layout must be unseen as well. Holdout counts must distinguish independent base groups from correlated transforms and duplicated selected genotypes.

Commands:

```bash
.venv/bin/python -m maze_evolution.foundation_calibration_audit --out results/foundation_calibration
.venv/bin/python -m maze_evolution.foundation_repair --out results/foundation_repair
.venv/bin/python -m maze_evolution.foundation_repair_audit --out results/foundation_repair
```

Preserve negative results. Keep the goal active until the authorized calibration, justified longer study (or the diagnosed prerequisite work), independent evaluation, reporting, and repository synchronization are complete. No runtime/fitness code from a finished packet may be edited in place; introduce separately versioned modules if a change is needed.
