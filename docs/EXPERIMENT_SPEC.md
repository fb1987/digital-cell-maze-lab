# Experiment plan, controls and acceptance criteria

## Experimental question

Can a **population of evolved compact rule programs** operate on spatial input using cheap local reactions, producing optimal or high-quality maze paths on *unseen* grids, with lower wall-clock latency or compute cost than strong conventional solvers?

The default scientific hypothesis is **no demonstrated advantage yet**. A negative result, convergence to classical BFS-like behaviour, or an accuracy/latency tradeoff are all useful outcomes.

## Phase 0: existing baseline

`cellular_maze_lab.py` currently contains:

- `bfs`: reference Python breadth-first search, exact shortest path.
- `compiled_bfs`: optional Numba JIT solver, exact shortest path, better CPU comparator.
- `wave_cell`: packed-bit excitation waves that return exact shortest path on connected, unweighted, orthogonal 2D grids.
- `retract_cell`: simultaneous leaf pruning that returns a **survivor mask**, exact on tree/perfect mazes, generally invalid on cyclic mazes.
- `create_maze`: random obstacles (guaranteed reachable by rejection sampling), perfect DFS mazes, snake and comb arrangements.
- Rendered examples and microbenchmarks.

Do not claim the wave or pruning methods are new or universally faster. Existing timings are implementation-specific and different algorithms produce different output forms. The new test harness must normalize output and measure end-to-end latency fairly.

## Phase 1: minimum evolvable organism

Design the **smallest useful genome vocabulary**, ideally no more than 8–16 primitive operations initially, with deterministic interpretation. Possibilities: channel read/write, N/E/S/W neighbour-or, neighbour-and, XOR, gate, hold, excitation, inhibition, decay. Keep a typed bounded interpreter or compiled array kernel. Support two to four per-site channels (one visible output, others hidden) and isolated start/goal/wall stimulus input.

Limit genome length (e.g. 16–64 genes), max update cycles (e.g. 128–512 depending on grid), memory and operation counts. Avoid direct use of BFS/distance maps/ground truth in organism evaluation. Keep mutation seeds stable.

## Phase 2: evolutionary population

Start with about 32–64 genomes, tiny mazes (9, 17, 33 width), and approximately 50–200 generations, then adjust to measured local speed. Defaults are suggestions, not requirements. Each organism processes several mazes; use a rotating generation-specific training batch and keep fixed holdout seeds entirely isolated from fitness-based selection.

Experimental arms:

A. **Random evolution** from newly generated bounded genomes. Does functional behaviour arise?

B. **Seeded evolution** from a known local rule (wave/retraction-like). Can the population improve it in accuracy/compute?

C. **Ablation** using initial genomes without evolution (or random search with matched compute budget). Does selection confer any benefit?

Track full genealogy or parent IDs and population diversity. Optional crossover only after mutation-only evolution works.

## Fitness design

Do not start with naive per-pixel accuracy: an organism that switches every output pixel off would look deceptively accurate because valid route pixels are sparse.

Use a **staged fitness**:

1. Does the output contain a legal continuous route connecting entry and exit through open cells? Penalize leaks into walls, disconnected islands, cycles and extraneous lit regions.
2. If valid, how much longer is its path than an independently computed shortest path? Exactness is a separate binary metric.
3. Among otherwise comparable solutions, what are total evaluation time, update cycles, memory, primitive operations and energy budget?
4. For invalid outputs, use a shaped signal such as components' legal reach toward endpoints, connectivity of legal on-cells, output sparsity and penalties for wall crossings. **Do not let shaped partial accuracy outrank successful complete solutions.**

All fitness design choices must be published with each run so we can audit reward hacking. Tie-breaking and penalty weights must be disclosed.

## Maze families and fairness

- Perfect/tree mazes: DFS recursive-backtracker family. Unique solution. Does not prove general competence.
- Cyclic mazes: random binary obstacles and/or braided/looped mazes; avoid only showing trees.
- Long winding corridors/snake: severe propagation-distance tests.
- Trivial open fields, unreachable/disconnected mazes, start=goal, alternate entrance/exit positions, oddly shaped rectangular grids: edge cases.
- Held-out sizes: train small and evaluate larger (e.g. 17->33->65->129), and different generators to detect memorization.
- Eventually 3D 6-neighbour cubical and rectangular lattices, with maze generation and BFS oracle adapted properly.

Specify if one entrance/exit is on the outer boundary or anywhere, and whether 4-neighbour or 8-neighbour movement is permitted. By default use **four orthogonal neighbours** in 2D, **six** in 3D, unit edge weights, and blocked wall cells.

## Timing and performance measurement

1. Validate every emitted path independently. Measure **success rate**, **optimality among successes** and **overall optimality rate**.
2. Time at least 30 warm repetitions per representative size / family where practical. Show median, p95, min and distribution, not a single lucky sample. Isolate startup/JIT and rendering. Use the same CPU affinity/device settings where possible.
3. Report end-to-end: stimulus loading/encoding, local reaction, path reconstruction/output mask, and cleanup. Also report each component to explain differences.
4. Compare against **Numba/C/C++-level BFS** and an appropriate A* implementation, not interpreted BFS only. A bit-parallel BFS/wavefront itself is a strong parallel baseline.
5. A shared test harness must check path legality, shortest-path length against BFS, output-mask consistency, and strict no-path cases.
6. Measure peak memory, operation count, number of CA rounds and energy proxies. GPUs, if ever used, must report transfer overhead, kernel launch latency and amortization.
7. Plot latency as a function of grid area, path distance and structural complexity; report solve-rate under compute budgets.
8. Make seed and dataset splits explicit; no parameter selection on final unseen test mazes.

## Candidate success criteria (early exploratory, not proof of novelty)

- All fixed baseline correctness tests pass.
- Evolved output exists, is not hard-coded and is reproducible from recorded genome/seed.
- First honest random and seeded population experiments complete on local CPU without API costs.
- Holdout accuracy and optimality reported even if zero.
- Runtime and memory recorded for each class of algorithm, with at least one meaningful failure case shown.
- Code can be scaled to larger mazes without changing the meaning of "organism".

## Suggested first results artifacts

`results/first_evolution.md`, `results/first_evolution.csv` (one row per run), `results/best_genomes.json` (portable genome representation), and `results/visuals/` (sample responses). Include an environment block: OS/CPU, Python, NumPy, Numba, test seeds and git revision if available.
