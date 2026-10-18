# Paste into Codex after opening this extracted folder

The bundle is imported; V1, V2 and V3 source-pressure experiments are complete.
Read `results/source_pressure.md`, `docs/SIGNAL_PRESSURE_V3.md` and `AGENTS.md`.
There are 76 passing tests. The random-origin track has learned stronger
source-dependent multirange signalling, but no general shortest-path solver:
final task archives solve 0/174 unseen cases at distance>=8. The causal objective
improves mean hidden signal (0.5090 vs 0.4185 current; 0.2480 frozen), with higher
leakage; nonlocal ablation drops it to 0.0809. Full populations/RNG states and
ancestry are preserved. V1/V2 runtime/search/raw results remain unchanged.

The next proposed experiment preserves these signalling lineages and tests
**goal-conditioned path thinning**, keeping completed shortest paths primary,
capacity fixed and final tests fresh. Do not seed a known solver into a random
lineage or infer impossibility from these finite negative route results.
The original implementation prompt below is handoff history, not unfinished work.

Read `AGENTS.md`, `README.md`, `docs/THREAD_CONTEXT.md`, `docs/ARCHITECTURE.md`, `docs/EXPERIMENT_SPEC.md`, and `docs/RESEARCH.md`. The repository is a handoff from an extended research conversation. Preserve its central distinction: **one organism processes an entire maze using a spatial reaction substrate; a population evolves the genomes of these organisms.**

Start by running `python -m pytest -q` and `python cellular_maze_lab.py --sizes 33,65 --samples 3`, fixing any environment issues locally. Next, implement Phase 1: a compact, safe, heritable rule genome; a bounded 2D organism simulator (2–4 state channels); deterministic evolution with a rotating training set and unseen holdout mazes; and a fair benchmark against compiled BFS and the existing cellular baselines.

Conduct a small real evolutionary experiment with **(a)** random initialization, **(b)** wavefront-seeded initialization, and **(c)** a no-evolution control. Preserve meaningful intermediate fitness for initially non-solving organisms, but give the strongest fitness priority to complete legal paths, then shortest-path optimality and cost. Report failures and any compute/latency disadvantages. Save reproducible results, images and a concise findings report in `results/first_evolution.md`.

Constraints: CPU-first, offline, minimal dependencies, no LLM or paid external APIs, no self-executing mutated Python, no invented speedups or cherry-picked results. Do not spend the initial iteration on UI or infrastructure. Continue implementation and tests autonomously within the repository.
