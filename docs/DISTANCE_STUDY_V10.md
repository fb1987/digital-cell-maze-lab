# V10: near-to-far goal-distance curriculum

Locally preregistered before training,18 October2026. V1–V9/V8A sources and raw results remain immutable. This is offline random-origin continuation, without known solver rules entering a lineage.

## Question and isolated change

V9 strict-choice priority changed no observed selection trajectories. Some source-dependent paired choices reproduce but do not transfer. Test whether initially attainable goal cues help these populations extend choice over distance. Both arms keep the same V6 pulse VM,8 uint16 channels,128 typed genes,16-tick diagnostic horizon, V8 smooth J shaping and V9 **Choice-first** global/case ranking. Normal valid routes, shortest routes and no-path utility precede strict-both count K, then smooth shaping, then cost only if every normal output is correct. Candidate inference never accesses the oracle, decision label or training schedule.

The **Fixed** arm uses unchanged V8/V9 regular paired-goal sampling: source-to-goal≥8, a common shortest prefix ending2..8 edges from source, both goals≥4 edges beyond the fork, disjoint sets of all shortest exits, target separation≥greater source distance. Even pair indices require a misleading Manhattan bearing for at least one goal. Wilson9 trees and ordinary larger DFS/random mazes remain unchanged.

The **Curriculum** arm uses the EXACT SAME layout, source and fork as Fixed in every generation. For generations0–15, move the two goals along their respective original shortest suffixes to remaining distances(1,2), alternating goal order by(generation+replicate) parity. For generations16–31, use(2,3) likewise. At32 onward, use the original far goals: both arms now receive identical inputs. Choose each suffix's next step as the smallest-index open neighbor whose original goal distance decreases by1. No inference algorithm is inserted; this constructs training environments outside the VM.

Near labels permit remaining distance≥1 instead of4. All source-prefix, all-shortest-exit and causal scoring rules are unchanged. Near allowed exit sets must be subsets of the original disjoint sets; fork vertex, prefix, incoming edge, distance and exit set must be identical. A source-independent goal light receives no strict-choice credit. Near source-to-goal distance may be3 or more; target separation and deceptive bearing naturally change when endpoints move. Record actual distances/detours rather than claiming those remain matched. Mixed disconnected pairs remain identical in both arms. Only training splits may use these short labels; fixed validation and final paired tests retain all original hard constraints. The near variants intentionally share training layouts with their far anchors; no validation or final layout is shared with training or past experiments.

## Lineages, selection and budget

12 conditions: local/evolved range ×Fixed/Curriculum ×3 replicates,96 organisms each. Fork matching V9 Choice next population/RNG. In order, preserve task/choice/J/B/G/source and protected variants from native Choice then Prefix checkpoints, then native strict supplements and qualifying ancestry. No cross-topology/replicate transfer. Deduplicate genotype, replace last nonprotected slots if absent, log inputs/hashes/IDs. Both arms start with identical ordered genotypes/RNG/protected cohorts; all prior fork primitives and useful neutral variation remain available. Random immigrants remain rich random genomes. Reproduction/mutation/niche rules are unchanged; new validation archives do not automatically breed.

Both arms use Choice-first even on common hard validation. Preserve task,choice,J,B,G,source,Q,S archives, with identical V9 ranking and nomination policies. Final primary selections remain task/choice plus matching frozen initial no-evolution controls. Repeated archive copies are not independent samples. Additionally save each current globally ranked training leader at generations15,31,47, with genome/fitness/cases, in checkpoints and the pre-final frozen champions file. Post-freeze secondary assays evaluate these fixed leaders on the same paired final set and hard validation; they never replace primary models or feed breeding.

Seed2026101809. Independent full-capacity construction preflight seed1104; no production-seed preflight or final-test inspection. Exclude all8096 prior whole layouts through V9/V8A. Two rotating pairs/generation,9×9 through23 then17×17, tree+random except every fourth generation second pair mixed disconnected. Fixed validation6 pairs/replicate:9/17 ×tree/random/disconnected. Training caps256ticks,4096reads/site,32768dispatches/site; validation/final1024,8192,131072. Existing hard memory ceilings, maximum128 organisms and128 genes remain. Count normal and forced source probes separately; charge attempted reads even when gated/ablated.

Screen48 generations. Extend to128 and at most192 only if a topology gains≥2 optimal hard-validation task routes summed across replicates versus max(own frozen,Fixed) per replicate; OR≥2/3 replicates have hard-validation choice strict-both≥.5,≥own frozen+.25,≥Fixed+.25,J≥.4, and positive strict-both in both tree/random families. Only fixed hard validation can trigger the gate. Larger near-training scores alone cannot. Search ceiling4500seconds, with complete next-population/RNG checkpoints at boundaries. No automatic90-minute scaling.

## Freeze, final evaluation and diagnostics

Freeze/hash champions BEFORE constructing264 ordinary final layouts and24 paired layouts/48 inputs. Ordinary set:88 independent layouts/replicate,9/17/33/65 tree/random plus disconnected and rectangular. Paired set:6 regular and2 mixed layouts/replicate,42 reachable inputs at distance≥8,6 unreachable,18 regular decision pairs. Common inputs across all models and compiled BFS/A*/wavefront. Completed legal raster and shortest optimality are separate primary metrics. Report no-path utility/false claims, family/size/distance/turn/detour subsets, representative failures, memory/traffic/work. Wrong or partial outputs confer no speed advantage.

Warm identical production mutability/dtype/signature;30 randomized-order full decode→initialization→updates→raster repetitions, report median/range. Fitness/probes are excluded from inference timing and charged separately. No significance claim from three replicates.

Independent saved-raster audit: routes, all valid training claims, G/B/J arithmetic, strict coupling/global/case fitness, archive maxima, layout sharing/exclusion, exact anchor/near transformations and per-phase distances, complete ancestry/protected sets, deterministic resume and model/source hashes. Record changed-DNA behavior neutrality with its limited observable fingerprint, actual reproduction of strict positives, and source entry to a fork after desired exits are removed. Save training phase rates separately: different cue distances make those rates incomparable as transfer evidence. Compare frozen and final choice models on reused phase-boundary training pairs as an explicitly training-only diagnostic if needed. Preserve all newly qualifying validation variants and ancestry. Pulse-removal, nonlocal-read ablation and8/16/32/64-tick state probes remain fixed-model post-freeze assays. Record costs and no reselection.

## Commands

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m maze_evolution.distance_study --out results/distance_curriculum
.venv/bin/python -m maze_evolution.distance_diagnostics --out results/distance_curriculum
.venv/bin/python -m maze_evolution.distance_audit --out results/distance_curriculum --repack
.venv/bin/python -m maze_evolution.distance_report --out results/distance_curriculum
```
