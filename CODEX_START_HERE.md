# Paste into Codex after opening this extracted folder

The bundle is imported; V1–V4 experiments are complete. There are84 passing tests.
Read `results/goal_conditioning.md`, `docs/GOAL_STUDY_V4.md` and `AGENTS.md` first.
V4 compared transmission/goal-output pressures in12 conditions,96 organisms x40
generations, protecting learned V3 signalling elites. Some goal-sensitive branched
output evolved, but no unseen advantage: multirange goal score0.0022 vs0.0071
control; local0.0033 vs0.0035. Task archives solve local1/216 (adjacent, matches
frozen), multirange0/216, all0/174 long routes and0/42 paired reachable targets.
The longer-run gate did not pass. Training took9.67 minutes; training plus
recovered final evaluation/timing15.32 minutes. Only final size9 perfect mazes
changed to Wilson spanning trees after the original sampler exhausted unused
corner-DFS layouts, before any final candidate evaluation. The deviation and
timing/memory scope are documented. All archives, populations/RNG and provenance
are saved; V1–V3 code/raw results are unchanged. Do not reuse inspected final tests
for tuning. Next test a factorized curriculum for connected causal growth and
goal modulation at fixed capacity, with complete shortest paths primary.

Previous V3 handoff context:

Read `results/source_pressure.md`, `docs/SIGNAL_PRESSURE_V3.md` and `AGENTS.md`.
There are 76 passing tests. The random-origin track has learned stronger
source-dependent multirange signalling, but no general shortest-path solver:
final task archives solve 0/174 unseen cases at distance>=8. The causal objective
improves mean hidden signal (0.5090 vs 0.4185 current; 0.2480 frozen), with higher
leakage; nonlocal ablation drops it to 0.0809. Full populations/RNG states and
ancestry are preserved. V1/V2 runtime/search/raw results remain unchanged.

That proposed goal-conditioned path experiment is now completed as V4 above.
Do not seed a known solver into a random lineage or infer impossibility from
these finite negative route results.
The original implementation prompt below is handoff history, not unfinished work.

Read `AGENTS.md`, `README.md`, `docs/THREAD_CONTEXT.md`, `docs/ARCHITECTURE.md`, `docs/EXPERIMENT_SPEC.md`, and `docs/RESEARCH.md`. The repository is a handoff from an extended research conversation. Preserve its central distinction: **one organism processes an entire maze using a spatial reaction substrate; a population evolves the genomes of these organisms.**

Start by running `python -m pytest -q` and `python cellular_maze_lab.py --sizes 33,65 --samples 3`, fixing any environment issues locally. Next, implement Phase 1: a compact, safe, heritable rule genome; a bounded 2D organism simulator (2–4 state channels); deterministic evolution with a rotating training set and unseen holdout mazes; and a fair benchmark against compiled BFS and the existing cellular baselines.

Conduct a small real evolutionary experiment with **(a)** random initialization, **(b)** wavefront-seeded initialization, and **(c)** a no-evolution control. Preserve meaningful intermediate fitness for initially non-solving organisms, but give the strongest fitness priority to complete legal paths, then shortest-path optimality and cost. Report failures and any compute/latency disadvantages. Save reproducible results, images and a concise findings report in `results/first_evolution.md`.

Constraints: CPU-first, offline, minimal dependencies, no LLM or paid external APIs, no self-executing mutated Python, no invented speedups or cherry-picked results. Do not spend the initial iteration on UI or infrastructure. Continue implementation and tests autonomously within the repository.
