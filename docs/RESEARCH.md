# Research foundations and reference implementations

These are leads from the ChatGPT research discussion, not endorsements of any claimed speed advantage. Before importing third-party code, check the original paper, reproduction details and licenses.

## Closest work to this project

1. **Earle, Yildiz, Togelius, Hegde (2023), “Pathfinding Neural Cellular Automata.”** Hand-coded and learned cellular networks for shortest-path and diameter tasks; the paper also evolves adversarial maze data. This does not establish that it evolves organism genomes in our proposed sense. Paper: https://arxiv.org/abs/2301.06820 ; full text checked during setup: https://arxiv.org/html/2301.06820v1 . Code: https://github.com/smearle/pathfinding-nca . Important: compare dataset, update rounds, train/test sizes and how final paths are extracted, not just a headline accuracy figure. Its hand-coded extraction can emit multiple shortest alternatives rather than one route.
2. **Classical cellular automata shortest-path algorithms.** A 1996 paper “Computation of shortest path in cellular automata” discussed wave excitation and retained paths; search primary literature before making novelty claims.
3. **Nakagaki, Yamada, Tóth (2000), “Maze-solving by an amoeboid organism” (Nature).** *Physarum polycephalum* adjusted tubes to form efficient routes through a physical maze. Proof of a physical substrate solving a route problem, not proof that a CPU simulation outperforms BFS. https://doi.org/10.1038/35035159
4. **Mathematical Physarum solvers** model adaptive conductance and flow, including shortest-path convergence under assumptions. Distinguish convergence quality/time from discrete exact maze shortest path.
5. **Mordvintsev et al. (2020), “Growing Neural Cellular Automata.”** Shared local neural updates can produce coherent macroscopic growth and regeneration. https://distill.pub/2020/growing-ca/

## Adjacent context

- **Avida**, digital organisms competing for computational resources and evolving executable genomes: https://avida.devosoft.org/ . Relevant to population, mutation and genotype/phenotype; less directly relevant to maze-runtime performance.
- **AlphaEvolve**, LLM-generated candidate algorithms evaluated and selected using numerical fitness. Strong precedent for automated program search; not required here because the project must run offline and cheaply.
- **Darwin Gödel Machine**, coding agents changing their own implementation with external evaluation. Relevant to future autonomous improvement, but the current experiment intentionally avoids LLM-agent loops and arbitrary program mutation.
- **Physical reservoir computing / embodied computation**, physical dynamics as computation. Actual materials can offload dynamics onto natural interactions; emulating physical systems on a CPU does not grant free cycles.
- **Mixture-of-experts / sparse computation**, adaptively activating only portions of a program. Architectural inspiration, not a basis for claiming automatic speed superiority.

## Hard questions to investigate

1. Can an evolved CA solve loop-rich unseen mazes **correctly**, or does it learn only perfect/tree-specific pruning?
2. Can it learn a causal process substantially different from breadth-first excitation, or does it rediscover BFS-like propagation?
3. Do state channels, hidden memory or hierarchy help enough to offset their per-step cost?
4. Could local Boolean/gating genomes compile into packed integer/GPU bitwise operations more efficiently than floating-point NCAs?
5. Does the algorithm improve total compute cost as well as wall-clock time, or merely exchange more work for parallel latency?
6. Does changing the local rule *evolution process* materially improve holdout performance over the published 2023 learned NCA approach?
7. How does 2D success translate into 3D six-neighbour mazes, larger diameter and memory constraints?

## Important scientific limitations

The input data itself must be read; grid information must propagate, in strictly local interactions, at no more than one adjacency edge per synchronous update. A maze with geometric diameter D may require Omega(D) local cycles to determine distant connectivity. Comparing a CA on a GPU against a BFS in unoptimized Python would not isolate the algorithmic contribution. If the learned organism uses global operations, count them and compare against equally capable classical methods.
