# M2: wave mutation accessibility and retention

This is a fixed-parent assay around two deliberately selected M1 random-origin lineages. It tests local accessibility under the unchanged generic mutation operator; it is not a continuing evolution run or a replicated policy-efficacy experiment. Both old genomes remain preserved.

The two-opportunity variant m2/a0/d2/02786 confirms48 new paired successes with no losses:96/400 versus48/400 for its exact anchor, and200/200 corridors retained. It solves9/128 ordinary bases in both poses and passes the registered broad-transfer flag. However, eight of those ordinary routes have only one edge and one has three edges. It still solves zero prefix2/4/8, second-junction and cycle pairs. The formal flag passes, but a general-solver claim is unsupported.

## Untouched confirmation

All frozen nominees and reference models were assessed on 1,424 new inputs, including 400 complete two-goal pairs, 200 corridors, 256 ordinary reachable queries (128 bases in both poses), and 168 disconnected queries. Sizes15 were absent from M2 screening. Structured tasks reuse the existing grammar; variants and poses are correlated.

| Nomination | Identity | Pairs /400 | Ordinary bases /128 | New / lost pairs vs anchor | Acquisition | Broad |
|---|---|---:|---:|---:|---|---|
| a0/d1/original | m2/a0/d1/00312 | 48 | 0 | 0 / 0 | False | False |
| a0/d1/selective | m2/a0/d1/00312 | 48 | 0 | 0 / 0 | False | False |
| a0/d2/original | m2/a0/d2/02786 | 96 | 9 | 48 / 0 | True | True |
| a0/d2/selective | m2/a0/d2/02786 | 96 | 9 | 48 / 0 | True | True |
| a1/d1/original | m2/a1/d1/02894 | 0 | 0 | 0 / 96 | False | False |
| a1/d1/selective | m2/a1/d1/00565 | 96 | 9 | 0 / 0 | False | False |
| a1/d2/original | m2/a1/d2/00071 | 0 | 0 | 0 / 96 | False | False |
| a1/d2/selective | m2/a1/d2/00410 | 96 | 9 | 0 / 0 | False | False |
| random/original | m2/random/00540 | 40 | 0 | N/A | N/A | N/A |
| random/retained_a0 | m1/modular/0/familiar/mutation/g24/b39 | 48 | 0 | 0 / 0 | False | False |
| random/retained_a1 | m1/modular/1/broad/mutation/g84/b11 | 96 | 1 | 0 / 0 | False | False |

Unchanged anchor fallbacks and random draws are never credited as acquired mutant abilities. Acquisition requires eight new complete pairs across two contexts, 90% retention of anchor paired, corridor and ordinary-base successes, and no increase in false no-path. Broad additionally requires four new ordinary bases including both perfect and random families. Partial coverage alone is not a solution.

## Anchor and candidate detail

### m1/modular/0/familiar/mutation/g24/b39

Complete pairs: 48; ordinary bases in both poses: 0; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 112 | 112 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=0/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m1/modular/1/broad/mutation/g84/b11

Complete pairs: 96; ordinary bases in both poses: 1; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 2 | 2 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 224 | 224 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=48/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a0/d1/00312

Complete pairs: 48; ordinary bases in both poses: 0; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 112 | 112 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=0/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a0/d2/02786

Complete pairs: 96; ordinary bases in both poses: 9; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 10 | 10 | 0 | 0 |
| ordinary_random/15 | 64 | 2 | 2 | 0 | 0 |
| ordinary_random/9 | 64 | 6 | 6 | 0 | 0 |
| paired | 800 | 224 | 224 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=48/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a0/d2/02786/intermediate

Complete pairs: 48; ordinary bases in both poses: 0; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 112 | 112 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=0/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a1/d1/00565

Complete pairs: 96; ordinary bases in both poses: 9; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 10 | 10 | 0 | 0 |
| ordinary_random/15 | 64 | 2 | 2 | 0 | 0 |
| ordinary_random/9 | 64 | 6 | 6 | 0 | 0 |
| paired | 800 | 224 | 224 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=48/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a1/d1/02894

Complete pairs: 0; ordinary bases in both poses: 0; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 0 | 0 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 40 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 8 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 64 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 0 | 0 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=0/48, fork/1=0/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a1/d2/00071

Complete pairs: 0; ordinary bases in both poses: 0; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 0 | 0 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 40 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 8 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 64 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 0 | 0 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=0/48, fork/1=0/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a1/d2/00071/intermediate

Complete pairs: 0; ordinary bases in both poses: 0; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 0 | 0 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 40 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 30 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 64 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 0 | 0 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=0/48, fork/1=0/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a1/d2/00410

Complete pairs: 96; ordinary bases in both poses: 9; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 10 | 10 | 0 | 0 |
| ordinary_random/15 | 64 | 2 | 2 | 0 | 0 |
| ordinary_random/9 | 64 | 6 | 6 | 0 | 0 |
| paired | 800 | 224 | 224 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=48/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/a1/d2/00410/intermediate

Complete pairs: 96; ordinary bases in both poses: 1; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 2 | 2 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 224 | 224 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=48/48, fork/1=48/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

### m2/random/00540

Complete pairs: 40; ordinary bases in both poses: 0; false reachable no-path: 0.

| Domain | Inputs | Shortest | Legal | Correct no-path | False no-path |
|---|---:|---:|---:|---:|---:|
| corridor | 200 | 200 | 200 | 0 | 0 |
| disconnected | 40 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_disconnected/9 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/11 | 64 | 0 | 0 | 0 | 0 |
| ordinary_perfect/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/15 | 64 | 0 | 0 | 0 | 0 |
| ordinary_random/9 | 64 | 0 | 0 | 0 | 0 |
| paired | 800 | 104 | 104 | 0 | 0 |

Pair strata: cycle/0=0/16, cycle/1=0/16, cycle/2=0/16, cycle/4=0/16, cycle/8=0/16, fork/0=40/48, fork/1=0/48, fork/2=0/48, fork/4=0/48, fork/8=0/48, two_junction/0=0/16, two_junction/1=0/16, two_junction/2=0/16, two_junction/4=0/16, two_junction/8=0/16.

## Development neighborhood frequencies

Each anchor received 4,096 independent one-opportunity and 4,096 independent two-opportunity draws. Two-opportunity intermediates were not evaluated or selected during screening. A separate shared pool contained 4,096 wholly random genomes. Duplicate/no-op draws remain in the records; physical exact genotype evaluations were reused. Original M1 aggregate ranking and retention/selectivity ranking saw the same fixed pool. The latter changes both retention and ordering, so their effects are not isolated.

| Anchor / depth | Draws | Changed genotype | Distinct genotypes | Retains every correct query | Gains any pairs | Acquisition gate | Broad flag |
|---|---:|---:|---:|---:|---:|---:|---:|
| a0/d1 | 4096 | 3962 | 2211 | 3638 | 0 | 0 | 0 |
| a0/d2 | 4096 | 4087 | 4014 | 3274 | 1 | 1 | 0 |
| a1/d1 | 4096 | 3976 | 2074 | 3208 | 0 | 0 | 0 |
| a1/d2 | 4096 | 4090 | 4001 | 2573 | 0 | 0 | 0 |

These are DEVELOPMENT frequencies over highly correlated neighbors, not independent discovery probabilities. One or two mutation opportunities do not guarantee that one or two functional changes survive. All intermediate genomes, operator events and complete initial/final RNG states are saved. Ancestors are the M1 accumulating-wave g24/b39 and delayed-wave g84/b11 genomes, selected before M2 screening.

## Compute, audit and limits

| Phase | Physical calls | Summed candidate seconds | Wall seconds | Work units |
|---|---:|---:|---:|---:|
| Screen | 6,318,256 | 3573.75 | 465.23 | 1,133,358,230,878 |
| Confirmation | 19,936 | 12.13 | 9.88 | 7,527,540,042 |

Screen nominal slots: 20,484 models × 392 queries. Physical models: 16,118 screening; 14 confirmation. Observed process-tree RSS peaks: 3.510GiB screen, 1.169GiB confirmation. Up to ten local workers. Candidate time is summed across workers, not elapsed time. Conventional baselines are correctness controls; no latency/speedup claim.

Screen audit PASS: all 20,480 pool draws, 24,576 mutation events, RNG, corpus, task specs and nominations reproduced; 6,318,256 independent grades and 98,539 fixed native samples, 113.44s additional wall. Final audit PASS: all 19,936 physical candidate responses and 4,272 conventional baseline calls replayed; 24.61s additional wall. Production mutation and VM code are shared in replay; the raster grader is independent, not a second complete VM.

The first final-audit attempt stopped after all19,936 native replays because intermediate-comparison pair keys were Python tuples versus JSON lists. All scientific values and memberships agreed. A separately committed JSON-only adapter (df6ddaf) reran the unchanged audit; frozen scientific source/results were not edited. The failed attempt adds19,936 native replays and grades; its standalone wall time was not instrumented. See docs/WAVE_ACCESSIBILITY_AUDIT_NOTE.md and the preserved failure packet.

BFS, A*, bit-wave and separately labelled intact flat/modular controls solve the full confirmation panel. No known solver enters any candidate ancestry; inference receives only maze cells and endpoints. The oracle precision diagnostic applies only to unique-route fork/corridor tasks and never repairs emitted rasters.

Finite generic neighborhoods cannot establish that larger architectures, neutral drift, regulation or sustained evolution will fail. Conversely, narrow structured improvements do not establish general solving. The exact nominated candidate capability is the confirmation claim; why a selection policy works remains untested.

## Mechanism and next research decision

The successful117-instruction genome changed only output block2: an input-port swap followed by copying an existing XOR node to the output position. It now combines the persistent goal wave with a pre-existing source-flag computation. Six primitive nodes lie in its conservative recurrent output/halt dependency cone. Its emitted raster is exactly a goal-distance ball of radius d-1 plus the source, at2d+1 ticks: all348 reachable development and1,256 reachable confirmation outputs match. This activates previously unused computation, but reaches the same narrow delayed-wave repertoire already present in the other M1 lineage. The immediate intermediate has no new paired successes; no second-edit-only counterfactual was run, so two-mutation necessity is not established.

Post-hoc terminal-output identity:61–87% of sampled variants match their anchor on every screening raster/status. Across4,096 draws per neighborhood there are only40,107,44 and89 distinct terminal behaviors. This is evidence of many behaviorally neutral sampled changes, not proof of neutrality on all mazes or all internal states.

Both rankings select the same acquiring variant; the new rule cannot be credited with discovering it. For the delayed-wave anchor, aggregate ranking chooses variants that lose all paired/corridor successes, while retention ranking preserves96 pairs and200 corridors and gains eight ordinary bases. That supports protecting demonstrated skills in this fixed pool, not a causal evolutionary-policy advantage.

Recommend a separately registered60–90min evolutionary continuation from the preserved random-origin wave lineages, with protected skill archives, neutral behavioral diversity and mixed one/two-opportunity variation. Compare against unchanged variation on equal evaluation allocations. Selection should distinguish longer-route and multiple-junction correctness, not let numerous one-edge examples satisfy a breadth screen. Permit neutral intermediates; no solver primitive or oracle cleanup. Keep the current M2 outcome and its passed flag unchanged. No continuation is launched by this report.
