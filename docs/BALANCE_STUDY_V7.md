# V7: balanced two-goal evolutionary pressure

Preregistered before training on 18 October 2026. Keep V1–V6 code and raw results unchanged. No known solver enters a random-origin lineage.

## Hypothesis and isolated change

V6 produced goal-dependent communication on unseen layouts, but failed paired route correctness. A higher average goal score sometimes displaced variants responding to both goals. Test whether reward for the weaker response helps useful two-goal behavior emerge at unchanged capacity, input and normal inference.

Every candidate uses the existing V6 pulse runtime: source channel0=1, goal channel1=1, source/goal flags, eight uint16 channels, at most128 typed genes, output2, stop7 and identical halting. Local and evolvable-range topologies remain separate. No new instruction, solver or state channel is added. Source-removal probes retain both goal inputs. BFS/distance computations stay outside inference.

For an aligned regular pair of reachable targets, let G_A and G_B be the unchanged sqrt(Q*S) goal scores. **Mean** gives case i bonus2G_i, totaling2(G_A+G_B). **Balanced** gives case i bonusG_i+min(G_A,G_B), totaling(G_A+G_B)+2min(G_A,G_B). Both pair maxima are4. An absent weaker response halves the stronger side's old bonus while retaining a gradient. Swapping goal labels swaps case rewards without changing the total.

Mixed reachable/unreachable pairs keep the original2G_i bonus in both arms; an unreachable target cannot be required to grow a route. Unaligned pairs receive zero goal credit as before. Valid routes, shortest routes and no-path utility precede all shaping. Normal partial output and source-dependent transmission terms remain unchanged. Cost breaks ties only when all ordinary cases are correct; unfinished genomes receive no cost/length penalty. Epsilon lexicase uses the explicitly assigned case bonus above. Invalid routes never count as fast solutions.

## Common continuation and selection

Twelve conditions: local/evolved × mean/balanced pressure × three replicates.96 organisms each. Base next population and RNG are the prespecified V6 **Pulse** checkpoint. Preserve validation-selected task, mean-goal and transmission archives from **both Pulse and Flag V6 arms**, their protected ancestors, and both entries from the V6 supplemental balanced validation archive. Deduplicate by genotype in Pulse task/goal/transmission/protected/supplement order, then Flag in the same order. Absent variants replace the last nonprotected population slot. Log checkpoint/supplement hashes, injection identities and complete lineage. Both V7 arms start with identical genotypes and RNG and protect exactly those same variants. All V6 raw populations remain available. No final-test performance selects a parent.

Reproduction otherwise stays V6: best training organism, fixed protected variants, phenotype niche elites, nine new rich random immigrants, and1–6 edits with10% uniform parent choice or epsilon lexicase. Hard maximum population128, genes128, channels8; preserve full next-population/RNG checkpoints. New V7 validation archives do not automatically enter reproduction.

Validation uses the **Mean objective in both arms**. Common archives: task by ordinary route fitness (no probe reward); goal by meanG; balanced by mean per-regular-pair min(G_A,G_B), then both-goal qualification, mean eligibleQ, meanG, validity and optimality; transmission/Q/S diagnostic archives retain their named criteria. Both training arms nominate the overall, transmission, goal, balanced, Q and S leaders, plus the same niche rule, for validation. This common nomination/archive policy avoids changing it only for the treatment. Freeze task and balanced archives, and their matching frozen initial controls, for primary final comparison. Mean-goal/Q/S/source archives remain saved as validation diagnostics. Archive labels may repeat a genotype and are not independent discoveries.

## Budget and continuation gate

Training caps256 ticks,4096 reads and32768 dispatches per site; validation/final1024,8192,131072. Probe horizon16. Same memory ceilings and program types as V6. Charge ordinary inference and both source-present/removed probes. Expected48-generation screen is around15 minutes of search plus final evaluation. No cloud, remote models or paid compute.

At48 generations, apply the prior fixed gate to the **common balanced archive B=mean regular-pair min(G_A,G_B)**, with Balanced as candidate and Mean as control. Extend to128, then at most192 generations only if one topology gains at least two optimal validation routes versus both its own frozen and Mean task controls, or in at least two of three replicates B≥.05,≥frozen+.04,≥Mean+.03, Q≥.10, S≥.05, both-goal qualification≥.25, ≥half initial transmission retained, and positive balanced scores in perfect and random families. The same gate thresholds now target B rather than meanG; record that distinction. Signal gains alone cannot trigger extension. Search deadline4500 seconds at generation boundaries; retain/report partial checkpoints if reached. Final evaluation, diagnostics and audits are separately timed.

## Independent environments and completed outputs

Study seed2026101805. Construction tests use separate seed1074; they must not generate this study's final layouts before freeze. Exclude whole layouts from all V1–V6 manifests across all splits/replicates. Reuse V6 generators and limits: Wilson9×9 perfect trees, larger DFS perfect trees, cyclic random, disconnected and rectangular cases. Two rotating training pairs/generation, size9 through generation23 then17; one mixed pair every fourth generation. Fixed validation has six pairs/replicate, regular goals separated and reachable distances≥8.

Record frozen model SHA256 before constructing final environments. Primary:88 independent layouts/replicate,264 total, sizes9/17/33/65 plus rectangles and disconnected cases. Paired final:8 layouts/replicate,24 total/48 inputs,42 reachable targets at distance≥8 and6 unreachable. Shared inputs across arms. Compare task and balanced selections plus frozen initial task/balanced controls; compiled BFS,A*,bit-wave baselines. Report legality, optimality, unreachable correctness and false claims, turn-required and mandatory-detour subsets, per-family/size behavior, failure raster, work, state-copy payload and memory.

Normal inference includes decoding, updates, stimulus initialization and raster emission. Warm production read-only dtype/signature;30 randomized-order warm repetitions, medians and ranges. Genome construction/oracle fitness/probes are excluded from inference timing and reported separately. Preserve all output rasters, seeds, versions, source hashes, diversity and charged work. Recompress new logs losslessly after timing with decoded/stored hashes; do not rewrite old experiment data.

After freeze, diagnostics may observe goal-switch source states at8/16/32/64 ticks and ablate nonlocal reads in both normal inference and probes. These do not change selection, gates or final accuracy. Additional diagnostics must be labelled and costed. Exact completed paths remain the final measure. A bounded negative does not establish impossibility of random-origin discovery.

## Commands

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m maze_evolution.balance_study --out results/balanced_goal
```
