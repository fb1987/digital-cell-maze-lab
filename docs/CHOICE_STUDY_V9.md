# V9: strict paired-choice priority

Locally preregistered before training,18 October2026. V1–V8/V8A source and raw results stay immutable. Random-origin discovery remains central. No known solver enters these populations; this is bounded offline CPU work.

## Question and isolated change

V8 produced two validation-only source-dependent fork-choice variants. One requires cooperating instruction-order/register changes. Neither transferred in V8A. The mean-J archive could prefer broad prefix growth over correct choices on one pair. Test whether **Choice-first** selection preserves/extends actual paired choices better than the unchanged continuous **Prefix** objective. Keep complete path correctness primary.

Both arms call the unchanged V8 Junction evaluator, which uses the unchanged V6 pulse VM:8 uint16 channels, at most128 typed genes, output2, stop7, source channel0 and goal channel1 pulses plus source/goal flags. No new opcode, state channel, input, stopping rule or oracle access in inference. Both retain V8's smooth fitness/bonuses exactly: normal partial output + hidden source transmission + J_i+minJ on eligible regular pairs,2G_i on mixed pairs, with J=.25 source-dependent connected prefix +.75 shortest-exit choice. All cyclic shortest-next-step ties are accepted individually; wrong exits and branching are penalized. Fixed probe horizon16, including source-removed probes retaining goal input. Choice labels/oracles remain confined to evaluation.

Let K be the number of eligible regular pairs for which BOTH switched goals have strict source-dependent, source-connected correct exits with every wrong exit off. Existing normal priorities are V(valid paths),O(shortest paths),N(correct no-path minus false reachable claims). Let S be the unchanged continuous shaping total and W the old cost tie-break (zero unless all normal cases are correct). **Prefix** global rank is(V,O,N,0,S,W); **Choice-first** is(V,O,N,K,S,W). This promotes real paired choice ahead of arbitrary partial/source growth while normal correctness still dominates. Report K/rate separately from J and from complete route accuracy.

For epsilon lexicase, Prefix case values are(valid-or-no-path,optimal-or-no-path,0,old smooth case score). Choice-first replaces that zero with the strict-both flag for the case's pair, assigned identically to both members; mixed pairs receive0. Filter exactly on the first3 fields and within epsilon.02 on the final smooth field. Inserting a constant zero preserves Prefix's original V8 lexicase decisions and RNG consumption. Route correctness and optimality remain ahead of this new discrete priority in each case. Genome/descriptor, mutation and all inference work are otherwise unchanged.

## Shared lineages and archives

12 conditions: local/evolved range ×Prefix/Choice-first ×3 replicates,96 organisms each. Fork the matching V8 **Junction** next population and RNG. Preserve validation-selected task/junction/balanced/goal/transmission archives and protected ancestors from both matching V8 Junction then Balanced arms. Also preserve each matching arm's supplemental strict-validation selection and all saved ancestry nodes of a qualifying strict variant in that same topology/replicate. Do not transfer genomes across replicates or topologies. Thus both native multirange primitives survive in their own cohorts under BOTH V9 pressures; they are not independent discoveries in every replicate. Source choices depend on recorded validation fields/ancestry, never final performance.

Deduplicate in the stated order by genotype; absent variants replace the last nonprotected slot. Log all checkpoint/supplement/ancestry hashes, injection IDs and parents. Both arms start with identical96 genotypes and exact RNG and protect exactly the same variants. Prior full populations remain available. Reproduction stays best training organism, fixed protected variants, phenotype-niche elites,9 new rich random immigrants, remaining slots mutated1–6 edits using10% uniform parent choice otherwise epsilon lexicase. Invalid/unfinished phenotypes receive no size or cost penalty. New validation archives remain saved and do not automatically breed.

Common validation objective is Prefix in both arms. Save task by ordinary normal fitness; **choice** by(strict-both rate,mean regular-pair minJ,balanced G,mean G,valid,optimal); junction by old(mean minJ,strict-both,B,valid,optimal). Preserve balanced,goal,source,Q,S archives. Both arms nominate all8 named training leaders plus up to3 niche leaders every tenth generation. This common archive/nomination policy changes versus V8 but not between V9 pressures. Final primary selections are task/choice plus matching frozen initial controls; all other archives remain diagnostics. Repeated archive genotypes are not independent samples.

## Environments, budget and gate

Seed2026101808; construction-only full-capacity tests use independent seed1094. Exclude every whole layout in V1–V8 and V8A manifests (7502 prior layouts). Reuse V8 sampling without retuning: Wilson9 trees, larger DFS trees, random cyclic/disconnected/rectangular families. Regular pairs share a shortest prefix ending at distance2..8 from source, each goal at least4 edges farther, and disjoint sets of all shortest exits. Target separation≥greater source distance. Even pair indices require at least one target's allowed exits all initially increase Manhattan distance; odd indices need not. Bounded4000 layouts ×24 first/24 second targets. Save labels/manifests before outputs.

Two rotating training pairs/generation,9×9 through generation23 then17×17; perfect plus random except every fourth generation the second is mixed disconnected. Fixed validation6 pairs/replicate:9/17 ×perfect/random/disconnected. Ordinary training caps256 ticks,4096 reads/site,32768 dispatches/site; validation/final1024,8192,131072; unchanged memory hard ceilings. Charge normal inference, both source probes, wall time and memory. Population hard maximum128, genes128; no cloud/providers/models.

Run48 generations (roughly15–20 minutes including final outputs). Extend to128 then at most192 only if one topology has ≥2 additional optimal validation routes summed across replicates relative to the larger of own frozen and Prefix task controls per replicate, OR at least2/3 replicates' choice archives have strict-both rate≥.5,≥frozen+.25,≥Prefix+.25, J≥.4, and positive strict-both rates in BOTH tree and random families. Signal/prefix alone cannot trigger extension. Search deadline4500 seconds at generation boundaries; preserve/report partial checkpoints. Main final evaluation and post-freeze assays/audits are separately timed. No automatic90-minute scaling.

Freeze all selections and hash them BEFORE constructing final layouts. Primary:88 ordinary independent layouts/replicate,264 total,9/17/33/65 trees/random plus disconnected and rectangles. Separate paired set:8 layouts/replicate,24 total/48 inputs,42 reachable at distance≥8 and6 unreachable, including18 regular decision pairs. Common inputs across arms; compare frozen no-evolution selections and compiled BFS/A*/wavefront. Report valid/shortest outputs separately, no-path/false claims, turn/detour subsets, family/size, representative raster failures, memory/traffic/work. Wrong/partial routes confer no speed advantage. Warm matching production signatures;30 randomized-order repetitions, full decoding/initialization/updates/raster emission, medians/ranges. Fitness/probes excluded from inference timing and charged separately.

V8→V9 also changes common protected ancestors and archival policy, so cross-version absolute scores are not a pressure-only comparison. Neither protected validation behavior nor an isolated new short path establishes transfer. A bounded negative leaves capacity, regulation and time hypotheses open.

## Audits and fixed-genome diagnostics

Independently reassess saved normal routes, all valid training claims and source/J/G/B arithmetic. Check the inserted global/case priorities, strict-pair coupling, common validation objective, both task and strict-choice archive maxima, ancestry/protected sets, deterministic continuation, layout exclusions, work sums and source/model hashes. Preserve every raster, full next population/RNG, software/hardware versions and lossless compressed logs with stored/decoded hashes. Matched-parent behavior comparisons exclude the final cost field and include the new selection priority; conditional observed neutrality does not imply equal hidden trajectories or work counters.

Post-freeze diagnostics may remove the goal pulse, zero nonlocal reads, observe source/junction states at8/16/32/64 ticks, and replay qualifying validation ancestry. No reselection. Preserve all newly qualifying strict-choice variants; any supplemental validation archive must equal the preregistered choice rank. Report whether improvements concern prefix coverage, isolated exits, both goals, or complete correctly emitted paths. New data-driven diagnostics require explicit labels/costs and must not tune against final tests.

## Commands

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m maze_evolution.choice_study --out results/choice_priority
.venv/bin/python -m maze_evolution.choice_diagnostics --out results/choice_priority
.venv/bin/python -m maze_evolution.choice_audit --out results/choice_priority --repack
.venv/bin/python -m maze_evolution.choice_report --out results/choice_priority
```
