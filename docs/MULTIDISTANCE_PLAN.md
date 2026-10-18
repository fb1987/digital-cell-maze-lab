# Multi-distance signalling: proposed first experiment

Prepared October 17, 2026, America/Toronto. This is an implementation protocol;
the genome runtime and evolutionary experiments have **not** been built or run.
The current user request is orientation, repository sync and preparation. The
older handoff's full implementation mission remains the next development phase.

## The hypothesis to test

Can evolution discover useful combinations of short- and longer-range signals
that produce complete shortest-path rasters on unseen mazes at lower total cost?
One organism processes the entire maze. Its shared genome controls the reactions
inside that organism; selection and mutation operate between organisms.

Separate three outcomes: learning to solve, benefiting from longer-range reads,
and outperforming strong conventional implementations. Each needs its own
evidence. Fewer reaction ticks alone do not establish lower compute or latency.

The handoff discusses multiscale signalling as a possible extension; it does not
contain a detailed previously agreed multi-distance design. The choices below
are a starting proposal based on the user's current priority.

## Define the communication substrate before evolving rules

Start with four orthogonal movement directions, unit edge costs and one maze
per inference call. Walls are never traversable. All spatial reads in tick t
observe the frozen state from tick t-1; instruction order cannot secretly move
signals through several sites in one tick. Off-grid reads return zero, without
wrapping across rows or boundaries.

Use two to four bounded integer/Boolean state channels, one of which represents
the visible output. A typed instruction vocabulary should allow activation,
suppression, persistence, decay, local comparison and deterministic tie-breaking.
The same vocabulary, representation and execution backend apply to every arm.
No arbitrary Python, maze-specific genome contents or evaluator oracle inputs.
A wavefront-style seed must execute through this same runtime, including route
construction; it must not call the existing BFS or wave solver as a shortcut.

| Topology | Available spatial reads | What evolves |
| --- | --- | --- |
| Local | Axial neighbours at radius 1 | Reaction/regulatory rules |
| Fixed multi-distance | Axial offsets at radii 1, 2, 4, 8, using a published fixed schedule | Reaction rules; range schedule stays fixed |
| Evolved multi-distance | The same offsets at radii 1, 2, 4, 8 | Reaction rules, range choice and state-conditioned range activation |

Here radius means geometric grid offset, not shortest-path distance through the
maze. Initially, longer-range reads can carry **regulatory information across
walls**. They do not create movement edges or certify connectivity. Document
this as nonlocal sensing, give conventional solvers the same full input, and
require the final route to use legal adjacent open cells. In every arm, radius-1
reads follow open maze edges and wall-site state remains zero. Only radii greater
than 1 permit sensing across intervening walls in the first multi-distance test.

A wall-aware longer-range control can later restrict reads to unobstructed
straight corridors, with every corridor scan charged. A hierarchy/coarse grid
is a separate later topology: pooling open cells must not merge disconnected
corridors. Neither variant may consume an oracle route or distance map.

These topology choices are permissions supplied by us. Emergence means that
selection discovers when and how to use them; we would not claim that evolution
invented long-range wiring from a nearest-neighbour-only runtime.

## Cheap development sequence

1. Build a shared output validator and timing harness. Normalize every solver to
   the same binary raster and explicit outcome status. Include blocked endpoints,
   disconnected grids, start=goal, cycles, rectangles and alternative endpoints.
2. Build the bounded local genome runtime and demonstrate a functional seeded
   organism. Verify synchronous updates and that inference never calls an oracle.
3. Pilot local-only random initialization, seeded initialization and frozen
   generation-zero controls. Start with 32 organisms, 25 generations, four mazes
   per rotating batch, and 9x9/17x17 grids. Measure cost before increasing it.
4. Add the two multi-distance arms to the same runtime. Repeat both initialization
   regimes using paired maze batches, mutation budgets and evolutionary seeds.
5. After profiling, target five independent runs per condition, 50 generations
   and eight mazes per training batch. Include matched-budget random search so
   selection can be compared with simply sampling more genomes. Frozen initial
   genomes remain a separate learning baseline, not an equal-search-cost claim.

Initial hard limits: 32 genes, at most 1 KiB serialized genome, four state
channels, 512 synchronous ticks and 64 bytes per grid site plus 64 KiB for
substrate/scratch buffers. Track interpreter overhead and process memory
separately. Use a common cap of 2,048 spatial channel reads per site per
inference, charged even for masked reads if the backend actually evaluates
them. Also cap and record all site instruction evaluations. Finalize their
numerical cap after the local pilot, before comparing topologies. Any budget
change creates a separately labelled experiment.

Equal tick limits do not equalize work across radii. Compare accuracy against
both measured latency and common read/instruction budgets. Count double buffers,
scratch arrays, temporary masks, range scheduling, initialization, termination
checks and output emission. Full-grid vector operations still cost work at
every processed site; inactive logical expression is only a saving if execution
actually skips that work. Operation counts and bytes are proxies, not measured
energy consumption.

## Fitness, splits and evidence of emergence

Rank complete legal routes first, shortest length second, resource cost third.
Use explicitly documented partial connectivity signals for unsuccessful genomes;
they must not outrank successful routes. Do not optimize similarity to one BFS
raster: several different shortest paths may be equally correct.

Keep training batches, tuning/validation mazes and a final untouched test set in
separate seed namespaces. Save a manifest of maze hashes, families, dimensions,
endpoints, generation and RNG seeds; check for overlap before running. Select
genomes and budgets without final test feedback. Freeze configurations before
the final test, and record every evaluated candidate, not just the champion.

Training starts with perfect and cyclic random mazes plus explicit no-path
examples. Evaluate held-out instances, endpoint locations, rotations/reflections,
generator families and sizes 33/65, then 129 if the compute budget allows.
Include winding corridors, combs, open rooms and misleading nearby passages
separated by walls. Existing snake/comb generators are deterministic in shape;
changing their seed does not make them independent unseen samples.

Report valid-path rate, shortest-path rate across reachable cases, optimality
among valid outputs, no-path accuracy and timeout rate separately. An empty mask
on a reachable maze fails; a timeout is not proof of disconnection. Longer mazes
that exceed the tick budget remain reported failures. Persist the output raster
and a failure reason for representative and randomly selected cases.

For a successful multi-distance genome, disable each nonlocal radius at frozen
weights and reevaluate. Then retrain a local-only control with the same search
budget. Use these together to distinguish reliance on a channel from improvement
over a competent local alternative. Record range usage over time, gene lineage
and activation/read counts. A radius never read cannot explain an improvement.

## What counts as a convincing conventional comparison

The starter's compiled BFS is the first comparator, not a claim about the best
traditional solver available. Add compiled bidirectional BFS, A* with Manhattan
distance and a suitable optimized grid-search implementation before making a
competitive claim. Pin versions and audit the actual movement rules. The
[original Jump Point Search paper](https://ojs.aaai.org/index.php/AAAI/article/view/7994)
uses an eight-neighbour grid with diagonal costs; importing its published numbers
would not compare the same task as our four-neighbour unit-cost mazes.

For newly generated mazes, include per-maze preprocessing and full raster
emission in single-query latency. If exploring many queries on one static maze,
report that as a separate workload and charge preprocessing/memory consistently.
Use at least 30 warm repetitions per selected instance, randomize solver order,
report median/p95/range, and aggregate across independent mazes and evolutionary
runs. Keep correctness testing independent of measured solver time.

The [Moving AI grid benchmarks](https://www.movingai.com/benchmarks/grids.html)
provide external maze, room and random-map families for later stress testing.
Their [scenario format](https://www.movingai.com/benchmarks/formats.html) assumes
diagonal movement when reporting optimal lengths. For a four-neighbour adapter,
recompute oracle lengths and label the adapted task explicitly. Check dataset
licensing and retain attribution before vendoring any data.

[Pathfinding Neural Cellular Automata](https://arxiv.org/html/2301.06820v1)
is a relevant learned-rule reference, with hand-coded and learned models and
separate shortest-path/diameter tasks. Its hand-coded extraction can light all
shortest alternatives; our contract requires one route. Match output semantics,
training setup and timing before comparing numbers. No published headline
accuracy or older paper is being treated here as a current speed record.

The first useful milestone is reliable held-out solving. A performance claim
requires comparable correctness, full-output timing, memory/work accounting and
repeatable improvement on a declared workload. A broader contemporary baseline
audit remains necessary before claiming to beat the best traditional solvers.
