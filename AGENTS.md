# Instructions for Codex

## Mission
Develop a CPU-first, offline, evolutionary cellular computing system for maze solving. Explore whether an organism with a compact heritable genome that governs parallel local spatial reactions can generalize and outperform conventional compiled pathfinding under fair benchmarks.

## Distinction
One organism solves one entire input maze. Each organism contains a large array of reactive sites executing local rules. A *population* contains 64 or more organisms with different genomes; selection amplifies robust behaviour across previously unseen mazes.

## Constraints
- No paid APIs, LLM inference, AWS infrastructure, or external subscriptions.
- Do not execute genome mutations as arbitrary Python source; use a safe constrained DSL or instruction set.
- No BFS or precomputed paths inside evolved organism inference; conventional solvers are permitted as independent evaluation ground truth.
- Benchmarks must include compiled BFS, end-to-end input-to-output latency, correctness, shortest-path optimality, memory use, and iterations.
- Ensure reproducibility: fixed random seeds, rotating training mazes, held-out test sets, hardware details, warm-up for JIT compilation.
- Start with 2D before 3D; prioritize sound experiments over UI polish.
- Record negative findings. Never imply that logical parallelism means free computation.

## Development
1. Import the starter ZIP from the original ChatGPT thread into the repository (keep existing README and AGENTS instructions reconciled).
2. Verify and execute baseline tests and benchmarks.
3. Design an evolvable genome encoding simple local operations: activation, inhibition, neighbor sensing, decay, persistence, logical composition and short-term memory.
4. Implement spatial reaction substrate with 2-4 internal state channels and an explicit binary output path.
5. Implement mutation, selection, fitness and a population simulator; evaluate random initialization vs a wavefront-seeded population and a no-evolution control.
6. Benchmark at multiple 2D sizes and families (perfect/tree, cyclic, disconnected, corridor, held-out generators); then consider 3D.
7. Write `results/first_evolution.md` documenting outcome, limitations and honest comparisons.

## Fitness
Illegal or disconnected paths fail. Primary objective: correct continuous start-to-goal route, then optimality, then latency and resource cost. Provide graded intermediate learning signals without rewarding trivial empty or full-frame outputs. Score across diverse unseen mazes, not a single puzzle.

## Important conceptual question
Can evolution discover an algorithmically useful, transferable regulatory rule, perhaps with multiscale signalling, rather than memorizing training mazes?
