# Paste into Codex after opening this extracted folder

The bundle has now been imported and the local setup verified. Read
`docs/MULTIDISTANCE_PLAN.md` for the current experiment proposal and
`results/local_setup_2026-10-17.json` for environment details. The steps below
describe the next implementation mission; no evolution result exists yet.

Read `AGENTS.md`, `README.md`, `docs/THREAD_CONTEXT.md`, `docs/ARCHITECTURE.md`, `docs/EXPERIMENT_SPEC.md`, and `docs/RESEARCH.md`. The repository is a handoff from an extended research conversation. Preserve its central distinction: **one organism processes an entire maze using a spatial reaction substrate; a population evolves the genomes of these organisms.**

Start by running `python -m pytest -q` and `python cellular_maze_lab.py --sizes 33,65 --samples 3`, fixing any environment issues locally. Next, implement Phase 1: a compact, safe, heritable rule genome; a bounded 2D organism simulator (2–4 state channels); deterministic evolution with a rotating training set and unseen holdout mazes; and a fair benchmark against compiled BFS and the existing cellular baselines.

Conduct a small real evolutionary experiment with **(a)** random initialization, **(b)** wavefront-seeded initialization, and **(c)** a no-evolution control. Preserve meaningful intermediate fitness for initially non-solving organisms, but give the strongest fitness priority to complete legal paths, then shortest-path optimality and cost. Report failures and any compute/latency disadvantages. Save reproducible results, images and a concise findings report in `results/first_evolution.md`.

Constraints: CPU-first, offline, minimal dependencies, no LLM or paid external APIs, no self-executing mutated Python, no invented speedups or cherry-picked results. Do not spend the initial iteration on UI or infrastructure. Continue implementation and tests autonomously within the repository.
