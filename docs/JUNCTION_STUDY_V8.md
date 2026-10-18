# V8: source-dependent junction choices

Preregistered before training on 18 October 2026. V1–V7 source/raw data stay immutable. No known solver enters a random-origin lineage. This is a bounded local CPU experiment.

## Hypothesis and isolated change

V7's balanced goal reward produced some goal-specific output, but its selected organisms left both exits illuminated at reached forks. At fixed capacity and pulse input, compare **Balanced** with explicit **Junction** pressure. Both arms use identical, newly sampled decision-rich environments. Thus the pressure comparison is controlled within V8; V8 versus V7 also changes sampling and is not a pressure-only comparison.

The unchanged V6 VM receives binary maze, source and goal flags, initial source channel0 and goal channel1 pulses. Eight uint16 channels, at most128 typed genes, output2, stop7, shared local/evolvable-range rule, identical update/halting and work caps. No oracle, shortest-step label, decision coordinate or new instruction enters inference. BFS remains in evaluation and generation only.

A regular pair has the same layout/source and different reachable targets. Choose the deepest vertex on target A's oracle path at source distance2..8 whose prefix is shortest toward **both** goals, with at least4 remaining edges to each. For each target, its allowed exits are **all** open neighbors one oracle distance closer to that goal. Exclude the incoming prefix neighbor. Require nonempty, disjoint allowed sets. This credits cyclic shortest-step ties rather than a particular BFS successor. Other exits are wrong for that target. No genome sees these labels.

At the fixed16-tick probe horizon, compute each target's source-connected output component and source-removed output raster. Prefix R is the fraction of oracle-prefix sites at source distance≥2 that are in the normal source component and off after source removal. Choice C is zero unless the junction is source-connected and at least one allowed exit is lit. Otherwise C = (fraction of lit allowed exits off after source removal) × (1 − fraction of wrong exits lit) / (number of lit allowed exits). Thus one source-dependent desired exit with all wrong exits off scores1; multiple allowed exits are legal shortest next steps individually but branching output is penalized. Source removal retains goal pulse/flag. J=.25R+.75C, bounded[0,1]. Unaligned probes receive J=0. Strict choice requires connected junction, exactly one allowed exit, no wrong exits, source dependence of that exit and aligned probes. Report strict choices under **both** goals separately from continuous J.

Balanced retains V7 case bonus G_i+min(G_A,G_B), G=sqrt(Q*S). Junction replaces this bonus on regular decision pairs with J_i+min(J_A,J_B). Both maxima are2/case,4/pair. Mixed reachable/unreachable pairs retain Balanced's2G_i in both arms. Normal partial output and hidden source-transmission terms remain unchanged. Valid emitted paths, optimality and no-path utility precede shaping; wrong/partial routes never count as fast solutions. Cost is a tie-break only when all normal cases are correct. Both arms use the same descriptor, mutation, epsilon lexicase and nomination policy.

## Common continuation and protected diversity

12 conditions: local/evolved range × Balanced/Junction ×3 replicates;96 organisms. Fork the V7 **Balanced** next population and exact RNG, preserve V7 task/balanced/goal/transmission archives and protected ancestors from **both Balanced then Mean** arms. Deduplicate in that order by genotype. Inject missing variants into the last nonprotected slot. Log hashes, identities, injections and external parents; both V8 arms have the same initial96 genotypes and protected variants. These parents are chosen by validation fields, never inspected final performance. Keep complete source populations and new next-population/RNG checkpoints.

Reproduction: best training organism, fixed protected variants, phenotype-niche elites, nine rich random immigrants, remaining slots mutated1–6 edits,10% uniform parent choice otherwise epsilon lexicase. No length/cost penalty on unfinished candidates. Common validation objective is **Balanced** in both arms. Task archive ranks ordinary normal fitness; junction ranks mean regular-pair minJ, then strict-both fraction, balanced G score, valid and optimal counts. Preserve balanced, mean-goal, Q, S and transmission archives. Nominate all seven named training leaders plus up to3 niche leaders every tenth generation in both arms. New validation archives do not automatically breed.

Primary final selections: task and junction archive, plus matching frozen initial controls. All archives remain saved; repeated archive genotypes are not independent discoveries.

## Independent sampling and budget

Study seed2026101806; full-capacity construction test uses independent seed1084. Exclude entire layouts from **all V1–V7 manifests**, across all new splits and replicates. Wilson9×9 trees, larger DFS trees, cyclic random, disconnected and rectangular families. Regular pairs additionally satisfy the decision conditions above; source-to-goal distances8..16 for9×9 training,8..32 for larger training/validation,8..64 for final pairs. Target separation remains at least the greater source distance. For even pair indices, at least one goal must require **every allowed exit to increase Manhattan distance at the decision**, a deceptive detour; odd indices have no detour requirement. This deterministic assignment is common to both arms. Sampling is bounded4000 layouts per requested pair,24 first and24 second targets/layout. Do not register rejected candidates. Save complete manifests and labels.

Two rotating training pairs/generation: size9 through generation23, then17; perfect plus cyclic, except every fourth generation the second is mixed disconnected. Fixed validation6 pairs/replicate:9/17 ×perfect/random/disconnected. Training caps256 ticks,4096 spatial reads and32768 dispatches/site; validation/final1024,8192,131072;16-tick probes. Charge normal inference and both source probes, actual wall time and memory. Hard population ceiling128 and unchanged runtime hard limits.

Run a48-generation screen (expected15–20 minutes including evaluation). Extend to128 then192 only if, for one topology, treatment task archives gain at least2 optimal validation routes summed across replicates versus the larger of its own frozen and Balanced task control in each replicate, **or** at least2/3 replicates have junction archive J≥.4, strict-both≥.5 and≥frozen+.25 and≥Balanced+.25, with positive J in both tree and cyclic families. Prefix/transmission alone cannot open the gate. Search ceiling4500 seconds at generation boundaries; preserve partial checkpoints. Final evaluation/audits have separate timing. No automatic extrapolation to90 minutes.

Freeze and hash all selections **before** generating final layouts. Primary remains88 independent layouts/replicate,264 total:9/17/33/65 trees and cyclic, disconnected and rectangles. These are ordinary sampling, not forced-decision pairs. Paired final8 layouts/replicate,24 total48 inputs: six regular decision pairs and two mixed per replicate,42 reachable targets≥8 and6 unreachable. Report complete-path accuracy, optimality, turn-required/detour subsets and no-path handling. Compare frozen no-evolution controls and compiled BFS, A*, bit-wave baselines. Warm matching production signatures and time30 randomized repetitions of complete decode/update/emission, report medians/ranges and correctness. Probes/fitness are separate from inference latency.

## Audits and follow-up diagnostics

Recompute branch sets/labels, detour assignment, source-connected masks, J/G/B rewards and strict-both counts independently from stored rasters. Validate every final emitted route/no-path claim, all valid training claims, a replay per selected model and all source/checkpoint hashes, split exclusions, protected ancestry and work totals. Audit matched-parent mutations on identical training batches; identical observed raster/scalar behavior is conditional neutrality, not proof of identical hidden trajectories. Keep neutral diversity and effective complexity distinct from gene count.

Post-freeze diagnostics may remove the goal pulse and ablate nonlocal reads on the same final pairs, and observe source states at8/16/32/64 ticks, without reselection. Label and charge them separately. Save every normal/probe raster, full logs/RNG, seeds, software/hardware versions and freeze hashes. Lossless new-log recompression records stored and decoded hashes. Static figures show representative ordinary failure and switched-goal choices. A negative run does not establish impossibility of random-origin discovery.

## Commands

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m maze_evolution.junction_study --out results/junction_choice
.venv/bin/python -m maze_evolution.junction_diagnostics --out results/junction_choice
.venv/bin/python -m maze_evolution.junction_audit --out results/junction_choice
.venv/bin/python -m maze_evolution.junction_report --out results/junction_choice
```
