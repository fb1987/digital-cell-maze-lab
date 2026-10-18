# V6: symmetric initial source and goal stimuli

Preregistered before training, 18 October 2026. V1–V5 source and results remain unchanged. Random-origin evolution continues; no functional solver is inserted.

## Question and intervention

Can an initial goal-state pulse help the existing regulatory genomes turn communication into goal-directed route formation? V5 showed occasional directional growth but poor goal information at the source. This is a hypothesis about stimulus accessibility, not evidence that extra signalling will produce a solver.

Both conditions retain the source flag (register 9), goal flag (10), open flag (8), and constant (11), with state channel 0 initially one at the source. **Flag** leaves all other initial states zero, exactly matching the V2–V5 input convention. **Pulse** additionally sets channel 1 to one at the goal before the first update. This is one additional initial assignment, not a propagation/path instruction. The typed primitive loop, halting, capacities, update/read budgets and output channel are otherwise identical. Source-removal probes remove only source channel 0 initialization and source flag; they retain the goal flag and, in Pulse, the goal pulse. Stimulus decoding/assignment and full raster emission are included in inference timing.

## Population and provenance

Twelve conditions: local/evolvable ranges × flag/pulse × three replicates. Each has 96 organisms, eight uint16 channels, at most 128 genes, radii 1/2/4/8, deterministic mutation and epsilon lexicase, phenotype niches and nine random immigrants per generation. No automatic cost/size penalty for unfinished organisms. Identical starting genotypes and RNG per paired input condition; subsequent RNG paths may diverge with phenotype selection.

For each topology and replicate, the prespecified base is the V5 **product** checkpoint's full next population and RNG. Preserve the validation-selected **task, goal and transmission archives from both V5 product and curriculum arms**, plus their fixed ancestral protected elites. Deduplicate by genome hash, in product/task, goal, transmission, protected order, then curriculum in the same order. Inject absent variants into the last nonprotected population slot and record the replaced identity. Protect these same variants during both V6 arms. Selection here uses archive fields, never V5 final-test performance. Preserve all prior populations and log both source checkpoint hashes. No V6 validation archive automatically re-enters reproduction.

## Fixed objective and budget

Both arms use the V5 **product** objective throughout: completed legal routes, shortest routes, correct no-path utility (minus false claims on reachable inputs), then normal partial output + source-dependent transmission + 2 sqrt(Q S). Q is source-dependent connected output progress penalized for branches; S is improvement toward this goal over the other-goal output on identical geometry. Last, cost breaks ties only for fully correct batches. The task archive uses normal route fitness without shaping; goal/source/quality/specificity archives are diagnostic. Fitness probes use the same input mode as inference, with a forced 16-tick horizon; incomplete probes get no shaping credit.

Training limits: 256 ticks, 4,096 reads and 32,768 dispatches per grid site. Validation/final limits: 1,024 ticks, 8,192 reads and 131,072 dispatches per site. Memory ceilings and genome/program bounds remain unchanged. Probe work is separately charged; oracle graph distances occur only in evaluation. Observe bounded state timecourses only after model freeze, as diagnostics without reward or reselection.

Screen for 48 generations in all twelve conditions (expected roughly 15–20 minutes including evaluation). Only extend to 128, then at most 192 generations if the **unchanged V4 gate**, with Pulse as candidate and Flag as control, passes on validation: either aggregate gain of at least two shortest routes versus both its own frozen control and evolved Flag on a topology, or in two of three replicates G ≥ .05, ≥ frozen + .04 and ≥ Flag + .03, Q ≥ .10, S ≥ .05, both-goal qualification ≥ .25, retention of ≥ half initial transmission, and positive G on perfect and cyclic families. Validation reachable distances are ≥8. Mere transmission gains cannot trigger extension. Search deadline 4,500 seconds checked at generation boundaries; do not start another condition beyond it. Report incomplete conditions if the deadline intervenes. Final evaluation and audits are additional measured costs.

## Environments, controls and final tests

Seed root 2026101804. Exclude every whole layout in V1–V5 manifests, across every split and replicate. Reuse V5 data rules: Wilson trees for 9×9 perfect mazes; larger perfect trees, cyclic random mazes, disconnected cases, and rectangular final cases. Rotating training: two goal pairs/generation; 9×9 through generation 23, then 17×17. Fixed validation: six pairs/replicate, divergent goals at distances ≥8, including mixed reachable/unreachable pairs.

Freeze all archives and record champions SHA256 **before generating final layouts**. Primary final set: 88 layouts per replicate, 264 total (9/17/33/65 square sizes plus rectangles and disconnected cases). Paired final set: eight layouts per replicate, 24 total/48 inputs, with two goals sharing the same geometry/source and distances ≥8 for reachable cases. All arms share these environments. Primary outputs: task-selected and goal-selected genomes plus **separately selected frozen task and goal controls for each input convention**; compiled BFS, A* and wavefront baselines. Frozen controls account for an immediate stimulus benefit without evolution.

Report valid paths separately from shortest paths, unreachable correctness, turns required (endpoints differ in both coordinates), mandatory detour (oracle distance > Manhattan), failures and real work/memory. Compare goal-dependent source/hidden/output/stop states on paired layouts over aligned bounded horizons; these are causal goal-switch assays, not proof of route solving. Cross-input evaluation of frozen selected genomes and nonlocal-read ablation may be reported after freeze as diagnostics; neither changes selection or the extension gate.

Benchmark complete normal responses using the production read-only byte/grid/program signature, matching JIT warm-up, 30 warm randomized-order repetitions and medians/ranges. Wrong outputs carry no solved-instance speed claim. Report train/search/final/audit costs separately, raw outputs and masks, seeds, versions, checkpoint RNG/populations, source hashes and diversity. Compress new logs losslessly after timing; record decoded and stored SHA256. Final tests are never reused to tune this run.

## Run and interpretation

```
.venv/bin/python -m pytest -q
.venv/bin/python -m maze_evolution.beacon_study --out results/goal_beacon
```

A positive result requires exact unseen route evidence. Increased communication or shaping reward alone is a precursor. A negative bounded result leaves the random-origin research direction open and must identify whether the immediate input effect, evolutionary gain, useful goal dependence or route construction failed.
