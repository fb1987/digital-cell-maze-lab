# V12D: unchanged 75-minute continuation and a stronger transfer screen

Preregister before launching the continuation. V12C completed442 matched generations in75.15minutes. Fresh-local evolution passed its elementary screen in2/3replicates, but solved only9/432 complete non-adjacent pairs, no base group under all eight poses, and0/181 ordinary cases of distance≥8. This is a reason to test additional time under stable conditions, not evidence of a general solver or a speed advantage.

## Exact continuation

Restore all24 V12C final prepared populations of96 organisms from `results/foundation_study/checkpoint.latest.json.gz`. Preserve every population member/order, individual identity/serial, RNG, champion, per-level archive, original frozen selection, validation history, competence certificate and cumulative counter. Start at absolute generation442; carry curriculum levels[1,1,1] and stage-entry generations[20,20,20]. Do not initialize/re-evaluate founders, reseed candidate RNG, inject archived champions or insert a known solver. Keep their original config/study identifiers so mutation ancestry stays continuous. Store the new segment separately under `results/foundation_continuation`.

Use the unchanged `SkillSearch`, `MutationSearch`, bounded runtime, grammar, fitness, curriculum and `batch`/`advance` implementations from V12C. Eight channels,256 genes,256 ticks,4096 reads/site,32768 dispatches/site;96 organisms; evolution retains12 elites/niches,9 random immigrants and75 one-edit descendants; resampling retains12 and redraws84. Four validation nominees every eighth absolute generation. Each round has12 inputs per organism:four current poses, one recall pair, one preview/mixed pair. Absolute generation preserves family/reflection/validation/mixed-task phases and rotating condition execution order. All eight conditions within each replicate receive identical tasks.

**Retain V12C's432 validation inputs** (144 per replicate) byte-for-byte, with original goal-pair labels. These are reused selection data, never called unseen. Current champions and skill archives therefore retain comparable ranks. New maze-stream seed2026101816 changes only environment generation, not candidate RNG. Exclude all52,424 whole layouts constructed through V12C, including its final cases and all software fixtures, from every new training and final layout. Reject complete transformation orbits, independent of endpoints. Borrowed validation is the explicit exception: install only its27 existing groups into the data cache before generating new groups. Resume reconstructs new groups in their original order.

Freeze V12C's primary/secondary selections separately as checkpoint controls before search. Keep the original initial frozen controls inside each search state untouched. Resampling populations also continue with their full state; they get exactly the same incremental response slots as evolution. No control enters reproduction. No old confirmation result is used for selection.

## Bounds and records

One fixed4,500-second local search budget, including parent verification, restoration, data construction, ordinary evaluation, selection and checkpoint I/O; initial JIT warmup is separate. Finish the current matched24-condition round on expiry. Hard limit4096 **additional** generations;4GiB output and8GiB process RSS checked at10-round checkpoints. No extension or early termination based on performance. If a resource cap intervenes, report it. Save atomic complete-population/RNG checkpoints and closed lineage/evaluation segments every10 rounds, all raw rasters and counters, metadata and source/input hashes. Resume overhead consumes the remaining budget. Preserve incomplete segments as uncounted orphan files. Report incremental and cumulative responses/work separately.

Before launch, test exact24-state restoration, resumed versus uninterrupted next-step behavior on already excluded V12A fixtures, borrowed validation identity and screen boundary conditions. No candidate inference on newly generated final layouts occurs before selections are frozen. Completed earlier source/raw files remain immutable. New confirmation/audit/report code can be prepared during search; it cannot alter frozen training code and is hashed before its own outputs.

## Confirmation and decision rule

After training freeze primary global champions, secondary per-level selections, original frozen selections and checkpoint controls. Also freeze the primary validation-selected genomes at additional generations0,48,128,256 and final (omit a boundary beyond termination). These time points are declared now, before training. Additional generation0 is the V12C champion. Evaluate all on the same fresh elementary corpus; this time course is secondary and correlated, not independent replication.

Fresh elementary cases:three independent base layouts per family(tree/cyclic), per level(1,2–4,4–8,8–16edges), per replicate, with eight dihedral poses and two disjoint-goal routes:384 responses/replicate,48 complete pairs/level. All primary and control selections see all levels; each secondary skill sees only its level. Final seed is the new environment seed, in a separately named confirmation stream. Report individual legal/shortest outputs, complete shortest pairs, independent base groups with any/all successful poses, family, distance, work and failures.

A replicate passes the **stronger continuation screen** only if all conditions hold:

1. Its final evolved primary selection has strictly more complete shortest pairs across levels1–3 than both its V12C checkpoint selection and the matched continued-resampling primary selection.
2. The same final selection retains at least44/48 adjacent complete pairs (the integer threshold for≥90%).
3. Either its number of level1 base groups solved in **all eight paired poses** exceeds both controls (thus at least one group), **or** its level2 complete-pair count exceeds both controls and includes successful pairs in at least two independent level2 base layouts.

A cohort(origin×topology) passes if≥2/3replicates pass. These are descriptive exploratory screens across four cohorts, not p-value claims. Do not pool different specialists to pass retention. All results, including failed components and secondary skills, are reported. A failed screen may coexist with incremental learning, but does not justify claiming robust solving or automatically extending the same run.

Fresh ordinary generalization matches V12C's design:per replicate8 tree/8 cyclic cases at9,17,33,65;4 disconnected at each size;4 rectangular at9,17:88 cases/replicate,72reachable and16disconnected. Generate and exclude every orbit; query only the declared primary orientation. Distinct stress budget1024ticks/8192reads/131072dispatches per site. Keep BFS/A*/bit-wavefront and intact wavefront references separate from evolution. Compare completed rasters. Benchmark30 randomized warm repetitions, bytes decoding through emitted raster, exact production signatures; static setup separate. References on the first17/33tree/cyclic case per replicate; candidates only where shortest-correct. Also benchmark each model's first non-adjacent elementary success, if any. No speedup credit for invalid output.

## Independent audit and interpretation

Verify parent proof/source/input hashes and parent-state identities, then independently audit every new mutation from the preserved parent population or its descendants; random immigrants remain explicitly labelled. Check all new fitness arithmetic, response/work accounting, shared batches, archive changes and curriculum certificates. Independently grade every validation/final raster and every training record claiming a complete legal route or correct no-path, plus a deterministic1/512sample of other training records. Replay every distinct final candidate/case result and reference raster. Verify checkpoint/population/RNG integrity, original frozen controls, layout isolation and transformed labels. Audit overhead is separate from the75-minute search.

Optional frozen-model interventions repeat V12C's removal of goal pulse, nonlocal values, or both on successful non-adjacent cases. Static goal flags and endpoint-aware halting remain. These are success-conditioned diagnostics, not new accuracy or a clean topology effect. Report all outcomes without retuning. Save runnable code, full states, raw results, a concise research report and representative successful/failing raster figures. Recommend one next experiment justified by the evidence.

```bash
.venv/bin/python -m pytest -q tests/test_foundation_continuation.py
caffeinate -i .venv/bin/python -u -m maze_evolution.foundation_continuation --out results/foundation_continuation
# Resume only an interrupted, unfinished continuation:
.venv/bin/python -u -m maze_evolution.foundation_continuation --out results/foundation_continuation --resume
```
