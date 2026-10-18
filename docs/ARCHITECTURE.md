# Architecture: organism, substrate, genome, evolution

## The point of departure

This began as a speculative architecture in which persistent agent capabilities are regulated like biological gene expression. The current experiment intentionally **abandons costly swarms of inference agents** to seek speed and low energy cost through parallel, local, reactionary computation. Maze solving is the deliberately measurable benchmark.

The organism is not the grid tile. The organism contains the grid, just as one biological cell contains many interacting molecular sites. It receives a maze in one stimulus, updates its internal spatial state under genome-defined rules, and presents the resulting lit pixels as its solution. Multiple organisms form the **evolutionary population**, not the set of pixels.

## Two time scales

- **Lifetime computation**: given one maze, repeatedly apply shared local rules across all spatial sites; signals propagate, strengthen, inhibit, decay or retract; read the final output pattern as a proposed route. Initial mutations do not need to be clever. Update cost must be measured.
- **Intergenerational learning**: vary the genome across organisms; evaluate many mazes; select offspring based on legal path correctness, shortest-path optimality and measured cost; track holdout generalization.

## Genome vs model weights

A compact genome may contain primitive operations, gates, update parameters and a small regulatory program. It is closer to a *program specifying development and response* than to pretrained foundation-model weights. Artificial-life evolution can optimize a genome without any foundation model at inference. Avoid conflating genome length, code entropy or biological codons with magic computational compression.

A simple starting genome might include `n_in`, `n_out`, primitive op IDs, channel addresses, masks and thresholds, allowing conditional activation. Local rules may examine only neighbouring spatial sites and the local substrate, with explicit declarations for any nonlocal links or coarser grids. A signed concentration channel could permit reaction-diffusion, while Boolean gates permit bit-packed simulation.

## Organism execution interface (proposed)

```python
organism = Organism(genome=genome, shape=(height, width), max_steps=512)
output = organism.react(maze_mask=maze, start=start, goal=goal)
# output.path_mask is a 2D binary raster; metadata includes steps, operations, energy, validity
```

This is an **illustrative API**, not already implemented.

Internally, the organism should have a limited number of channels, bounded update steps and deterministic or seeded stochastic transitions. The update kernel may be single-instruction SIMD operations over packed bits or NumPy arrays. Benchmark the *full* time to initialize, react and emit a path mask, and optionally separately report kernel-only time.

## Biological inspiration, but preserve physical realism

| Biological mechanism | Engineering analogue |
|---|---|
| Genome | Heritable program defining local reactions and regulators |
| Transcription and expression | Active rule selection / masked state updates |
| Signal proteins | Per-site excitation, inhibition and memory channels |
| Degradation | Timed decay / clearing obsolete states |
| Feedback | State-conditioned reinforcement and suppression |
| Metabolism | Hard instruction, memory and wall-clock budgets |
| Phenotype | Output path mask and measurable behaviour |
| Reproduction / mutation | Variation and selection between evaluated genomes |

A CPU/GPU simulation does **not** get molecular physics for free. Physical self-organization may be a useful analogy, but digital emulation must still execute operations and move data. If using multiscale links or globally aggregated signals, count and document them.

## Fundamental information-propagation limit

With synchronous nearest-neighbour updates only, information can propagate at most one grid edge per update cycle. An endpoint separated by graph distance D cannot influence the other endpoint in fewer than D cycles. Massive spatial parallelism can reduce wall-time per wave under suitable hardware, but cannot evade causal propagation latency. A future experiment may allow cheap coarse-grained/global regulators; compare honestly against other multilevel algorithms.

## Candidate pathways

1. **Hand-coded wavefront**: exact, BFS-like shortest path, SIMD/bitwise updates. Existing `wave_cell` implements a 2D variant.
2. **Dead-end retraction**: simultanous parallel deletion of unprotected degree <=1 nodes; exact on perfect/tree mazes, not on arbitrary cyclic mazes. Existing `retract_cell`.
3. **Evolved local state machine**: multiple signal channels, shared rule genome, trained against held-out mazes.
4. **Adaptive-flow / Physarum-style solver**: flow and path reinforcement; may converge to efficient network, not automatically exact shortest path.
5. **Hierarchical / multiscale solver**: learn local and sparse nonlocal/cross-scale signalling; prioritize only after a strong local baseline.
6. **3D substrate**: six orthogonal neighbours per voxel; input generator, reference BFS, output voxel path, visualization and benchmark. Defer until 2D generalization works.

## Architecture anti-goals

No AWS or cloud services for prototype; no LLM in feedback/update loop; no shell or arbitrary Python execution from mutated genomes; no per-pixel subprocesses; no dedicated queues per gene; no GPUs merely to appear parallel.
