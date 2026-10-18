# Digital Cell Maze Lab

An experimental, **offline-first**, biologically inspired computing project. The aim is to discover whether a compact, evolvable genome can control the local reactions of a spatial substrate and solve previously unseen mazes more efficiently than conventional pathfinding. **No such speed improvement has yet been demonstrated here.**

The central distinction: **one organism solves one entire maze.** The many grid sites are the organism's internal computing medium, *not* independent intelligent agents. Dozens or thousands of organisms, each possessing a different genome, can be evaluated in a population and selectively reproduced/mutated.

## Current checkpoint — October 17, 2026

The context bundle is imported and the project is prepared for development on an
Apple M4 Mac with 16 GiB memory and Python 3.13.15. All **41 tests pass**, including
genome validation, synchronous execution, independent raster validation and
deterministic evolution replay. Maze generation is reproducible, the compiled
baseline runs, and the NumPy-only fallback was checked. See the local
[smoke output](results/local_setup_2026-10-17.txt) and
[environment/source metadata](results/local_setup_2026-10-17.json).

The first bounded genome runtime, evaluator and evolutionary pilot are complete.
Read [the full experiment and phenotype audit](results/first_evolution.md).
Three runs of 32 organisms over 25 generations compared random and wavefront-seeded
populations with their frozen initial champions. All champions were frozen before
generating the final test set.

| Initialization | Evolved shortest paths / reachable tests | Frozen control |
| --- | ---: | ---: |
| Random | 4/240 | 4/240 |
| Wavefront seed | 200/240 | 200/240 |

The random successes simply light every open pixel on unbranched snake corridors.
They do not demonstrate learned maze solving. Seeded organisms solve all 96
same-size unseen cases and all 48 disconnected cases. Forty larger/structural
cases exhaust the common read budget. Two runs delete a redundant persistence
instruction (29→28 genes, 2.22% less counted work), with unchanged accuracy.
The generic interpreter is about 150× slower than compiled BFS in the sampled
17×17 timings. These are pilot implementation comparisons, not a competitive win.

The next focus is **local versus fixed and evolvable multi-distance signalling**.
The [proposed experiment protocol](docs/MULTIDISTANCE_PLAN.md) defines controls,
wall semantics, compute budgets and holdout evaluation. Multi-distance signalling
has not been implemented yet.

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

## Run the evolutionary experiment

The interpreter uses Numba from `requirements-dev.txt`. It evaluates four local
uint16 channels with a closed 14-operation instruction set; genomes cannot execute
Python or call the evaluator. See [the genome](maze_evolution/genome.py),
[runtime](maze_evolution/runtime.py), [evaluator](maze_evolution/evaluator.py),
and [selection/experiment harness](maze_evolution/experiment.py).

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m maze_evolution.experiment --out results/repeat_evolution --seed 20261017 --replicates 3 --population 32 --generations 25 --samples 8 --benchmark-repeats 30
.venv/bin/python -m maze_evolution.inspect_results results/repeat_evolution
```

Choose a fresh output directory for each run. The saved pilot took about 25 seconds
after cached JIT warm-up. This includes evolution, final tests and timing; a first
compilation may take longer. Raw genomes/parents, all training fitnesses, exact
maze inputs, output masks, timings and environment metadata are in
[`results/first_evolution/`](results/first_evolution/).

## Files

| Path | Purpose |
|---|---|
| `cellular_maze_lab.py` | Runnable baseline: Python BFS, Numba BFS (optional), bit-packed wavefront, dead-end retraction; random/perfect/snake/comb maze generators |
| `tests/` | Core solver correctness tests, including cyclic and disconnected mazes |
| `maze_evolution/` | Typed genome, bounded interpreter, datasets, independent evaluator, evolution, baselines and audit |
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

**Existing**: standard/compiled BFS, compiled A*, exact bit-parallel wavefront,
leaf-pruning toy baseline, maze generators, bounded heritable programs, local
organism runtime, deterministic mutation/selection, frozen controls, independent
holdout validation, full-raster timing and recorded visual results.

**Not yet built**: multi-distance or 3D substrates, matched-budget random-search
control, broad optimized conventional baseline audit, or a competitive result.

## Experiment boundaries

- No paid APIs, cloud services, AWS deployment, foundation-model inference or unneeded dependencies.
- Do not use BFS or a precomputed solution *inside* the organism at inference time. Ground truth may be computed offline for scoring.
- Do not benchmark naive Python BFS alone and call a win; include compiled baselines and complete end-to-end wall-clock cost.
- Do not confuse millions of logically simultaneous grid updates with millions of CPU/GPU cores or zero-cost computation.
- Preserve reproducibility: fixed seeds, explicit environmental metadata, unseen tests and detailed result logs.
