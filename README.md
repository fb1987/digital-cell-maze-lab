# Digital Cell Maze Lab

An experimental, **offline-first**, biologically inspired computing project. The aim is to discover whether a compact, evolvable genome can control the local reactions of a spatial substrate and solve previously unseen mazes more efficiently than conventional pathfinding. **No such speed improvement has yet been demonstrated here.**

The central distinction: **one organism solves one entire maze.** The many grid sites are the organism's internal computing medium, *not* independent intelligent agents. Dozens or thousands of organisms, each possessing a different genome, can be evaluated in a population and selectively reproduced/mutated.

## Current checkpoint — October 17, 2026

The context bundle is imported and the project is prepared for development on an
Apple M4 Mac with 16 GiB memory and Python 3.13.15. All **22 tests pass**, including
new blocked-endpoint regressions. Maze generation is reproducible, the compiled
baseline runs, and the NumPy-only fallback was checked. See the local
[smoke output](results/local_setup_2026-10-17.txt) and
[environment/source metadata](results/local_setup_2026-10-17.json).

The next focus is **local versus fixed and evolvable multi-distance signalling**.
The [proposed experiment protocol](docs/MULTIDISTANCE_PLAN.md) defines controls,
wall semantics, compute budgets and holdout evaluation. Evolution has not been
implemented or run. Existing smoke timings compare different output forms and
do not establish a competitive speed result.

## Start here (for Codex)

1. Read [`AGENTS.md`](AGENTS.md) (repository coding-agent instructions).
2. Read [`docs/THREAD_CONTEXT.md`](docs/THREAD_CONTEXT.md), then [`docs/EXPERIMENT_SPEC.md`](docs/EXPERIMENT_SPEC.md).
3. Run the existing baseline and tests.
4. Give Codex the prompt in [`CODEX_START_HERE.md`](CODEX_START_HERE.md).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python cellular_maze_lab.py --sizes 33,65,129 --samples 6 --render --out-dir output
```

Only `numpy` is essential for the reference script. `numba` provides a compiled BFS baseline. `Pillow` renders image triptychs; `pytest` runs tests. The reference implementation is CPU-only and makes **no network or LLM calls**.

For the verified local environment, activate the existing `.venv`. To recreate
its exact package versions with `uv` on Python 3.13:

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements-lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python cellular_maze_lab.py --sizes 33,65 --samples 3 --seed 1729
```

`requirements-lock.txt` records the packages tested on macOS arm64; dependency
and wheel compatibility on other platforms still needs verification. `.venv`
and generated `output/` images stay out of Git.

## Files

| Path | Purpose |
|---|---|
| `cellular_maze_lab.py` | Runnable baseline: Python BFS, Numba BFS (optional), bit-packed wavefront, dead-end retraction; random/perfect/snake/comb maze generators |
| `tests/` | Core solver correctness tests, including cyclic and disconnected mazes |
| `AGENTS.md` | Repo-wide guardrails and next mission for coding agents |
| `CODEX_START_HERE.md` | Ready-to-paste Codex instruction |
| `docs/THREAD_CONTEXT.md` | Conversation handoff and user intentions |
| `docs/ARCHITECTURE.md` | Biological-to-computational mapping, organism vs cell and runtime model |
| `docs/EXPERIMENT_SPEC.md` | Initial evolution experiment, fitness, measures, baselines, phases, acceptance tests |
| `docs/RESEARCH.md` | Prior art and scientific cautions |
| `docs/MULTIDISTANCE_PLAN.md` | Proposed local/multi-distance experiment and validation sequence |
| `requirements-lock.txt` | Exact package versions used in the local setup check |
| `results/local_setup_2026-10-17.*` | This Mac's setup checks, metadata and smoke timings |
| `examples/` | Example 65×65 maze/result images from prior work |
| `results/baseline_smoke.txt` | A smoke run on this environment; **not** a scientific performance study |

## What exists vs what remains

**Existing**: standard BFS solver, exact bit-parallel wavefront solver, parallel leaf-pruning toy solver, maze generators, optional Numba timing baseline, visual results.

**Not yet built**: heritable genome, genome interpreter/compiler, organism population, selection/mutation, evolutionary training, holdout benchmarking, any 3D implementation, any competitive performance result.

## Experiment boundaries

- No paid APIs, cloud services, AWS deployment, foundation-model inference or unneeded dependencies.
- Do not use BFS or a precomputed solution *inside* the organism at inference time. Ground truth may be computed offline for scoring.
- Do not benchmark naive Python BFS alone and call a win; include compiled baselines and complete end-to-end wall-clock cost.
- Do not confuse millions of logically simultaneous grid updates with millions of CPU/GPU cores or zero-cost computation.
- Preserve reproducibility: fixed seeds, explicit environmental metadata, unseen tests and detailed result logs.
