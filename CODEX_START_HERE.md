# Paste into Codex after opening this extracted folder

The bundle is imported; the first local experiment and V2 range/regulation study
are complete. Read `results/range_and_regulation.md`, its integrity/phenotype
audit, `docs/RANGE_STUDY_V2.md` and `AGENTS.md`. There are 63 passing tests.
Random-origin discovery remains a central user priority; 96×120 populations with
128 gated genes have not yet produced a general solver. Their actual populations
and RNG states are checkpointed for continuation. V1 results/source remain intact.
Use new final test sets for new experiments; do not treat the finite negatives
as a verdict. The original implementation mission below is handoff history.

Read `AGENTS.md`, `README.md`, `docs/THREAD_CONTEXT.md`, `docs/ARCHITECTURE.md`, `docs/EXPERIMENT_SPEC.md`, and `docs/RESEARCH.md`. The repository is a handoff from an extended research conversation. Preserve its central distinction: **one organism processes an entire maze using a spatial reaction substrate; a population evolves the genomes of these organisms.**

Start by running `python -m pytest -q` and `python cellular_maze_lab.py --sizes 33,65 --samples 3`, fixing any environment issues locally. Next, implement Phase 1: a compact, safe, heritable rule genome; a bounded 2D organism simulator (2–4 state channels); deterministic evolution with a rotating training set and unseen holdout mazes; and a fair benchmark against compiled BFS and the existing cellular baselines.

Conduct a small real evolutionary experiment with **(a)** random initialization, **(b)** wavefront-seeded initialization, and **(c)** a no-evolution control. Preserve meaningful intermediate fitness for initially non-solving organisms, but give the strongest fitness priority to complete legal paths, then shortest-path optimality and cost. Report failures and any compute/latency disadvantages. Save reproducible results, images and a concise findings report in `results/first_evolution.md`.

Constraints: CPU-first, offline, minimal dependencies, no LLM or paid external APIs, no self-executing mutated Python, no invented speedups or cherry-picked results. Do not spend the initial iteration on UI or infrastructure. Continue implementation and tests autonomously within the repository.
