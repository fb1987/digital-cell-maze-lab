# Digital Cell Maze Lab

An experimental, **offline-first**, biologically inspired computing project. The aim is to discover whether a compact, evolvable genome can control the local reactions of a spatial substrate and solve previously unseen mazes more efficiently than conventional pathfinding. **No such speed improvement has yet been demonstrated here.**

The central distinction: **one organism solves one entire maze.** The many grid sites are the organism's internal computing medium, *not* independent intelligent agents. Dozens or thousands of organisms, each possessing a different genome, can be evaluated in a population and selectively reproduced/mutated.

## Current checkpoint — October 18, 2026

The [source-dependent pressure continuation](results/source_pressure.md) is complete;
**76 tests pass**. It forks six saved random-origin populations, pairs current and
causal signalling objectives, and runs 96 organisms for 160 additional generations
per condition. The genome capacity and inference runtime remain fixed. Search
including probes took 60.45 minutes on the M4; fresh tests and timing brought the
main run to 64.22 minutes. No known solver entered the random-origin lineages.

A measurable precursor improved on 174 unseen reachable cases with endpoint
distance at least eight:

| Transmission archive | Frozen initial | Current objective | Causal pressure |
| --- | ---: | ---: | ---: |
| Local mean signal score | — | 0.3071 | 0.3071 |
| Evolvable ranges mean signal score | 0.2480 | 0.4185 | 0.5090 |

The score measures source-dependent hidden activation and subtracts leakage into
other components. Causal pressure leads in two of three held-out replicates.
Zeroing nonlocal reads reduces its score to 0.0809. Leakage is higher than under
the current objective, and a broadcast does not encode a legal path.

**No general shortest-path solver or speed advantage emerged.** Final multirange
task archives solve 2/216 reachable mazes under either objective, versus 4/216 for
their initial frozen task selections. Local task archives solve 2/216 under the
current objective and 0/216 under causal pressure. Every final task arm solves
0/174 cases at distance>=8. All observed organism successes are straight paths
of only 1–2 edges. Compiled BFS/A* solve all 216 reachable and all 48
disconnected cases. The report distinguishes diagnostic transmission archives
from task archives and reports complete outputs, latency and real work.

Random-origin discovery remains active. Populations, RNG states and ancestry are
preserved in [`results/source_pressure/`](results/source_pressure/). A justified
next experiment preserves these signalling lineages and tests goal-conditioned
path thinning, with completed shortest paths still first and another fresh final
set. More complexity remains a hypothesis; it is not inferred from gene count.

```bash
.venv/bin/python -m maze_evolution.signal_study --out results/repeat_source_pressure
.venv/bin/python -m maze_evolution.signal_diagnostics --out results/repeat_source_pressure
.venv/bin/python -m maze_evolution.signal_audit --out results/repeat_source_pressure
.venv/bin/python -m maze_evolution.signal_report --out results/repeat_source_pressure
```

See the [preregistered design](docs/SIGNAL_PRESSURE_V3.md). V1/V2 raw results and
runtime/search modules are unchanged.

## Range/regulation study V2 — October 18, 2026

The [range/regulation continuation](results/range_and_regulation.md) is complete:
**63 tests pass**. V2 adds eight state channels, up to 128 typed genes, conditional
expression, local/fixed/evolvable signalling radii, diversity-preserving search,
independent resampling controls and exact population/RNG checkpoints.

The study ran 656,640 training responses (724,176 including validation) in about
12 minutes on the M4. All models were frozen before 264 entirely fresh test cases.
The expanded random-origin cohort used 96 organisms × 120 generations × three
seeds for each topology, 14.4× V1's population-generation slots per run.

| Rich random-origin population | Evolved shortest / reachable | Independent sampling | Initial frozen |
| --- | ---: | ---: | ---: |
| Local | 2/216 | 2/216 | 0/216 |
| Evolvable ranges | 1/216 | 2/216 | 0/216 |

All random-cohort successes were adjacent endpoints. None solved the 165 cases
with distance at least eight. Large genomes and improved partial scores did not
yet produce a general algorithm. **Random-origin discovery remains an active
track**: checkpoints retain the populations for longer continuation rather than
restart them. Greater capacity, time and regulatory pressure remain hypotheses.

Seeded local/fixed/evolvable arms each solved 211/216, with five budget failures
and 48/48 correct no-path outputs. Their champions did not use nonlocal reads.
The same frozen local seed solves 189/216 at the old work cap, so its gain to
211 comes from inference budget, not evolved range use. No speed advantage over
compiled BFS was found. See the [preregistered protocol](docs/RANGE_STUDY_V2.md).

```bash
.venv/bin/python -m maze_evolution.range_study --out results/repeat_ranges
.venv/bin/python -m maze_evolution.range_audit results/repeat_ranges
```

Defaults reproduce the saved design. Full compressed lineage/fitness/output logs,
initial controls, timing samples and 48 continuation checkpoints are in
[`results/range_and_regulation/`](results/range_and_regulation/). The new runtime
permits a broad initial activation to develop/prune before stopping; V1's immediate
endpoint halt is preserved in V1 but removed in V2. V2 gates still pay dispatch
cost, and all ranges share hard work and memory caps.

## First local experiment — October 17, 2026

The context bundle is imported and the project is prepared for development on an
Apple M4 Mac with 16 GiB memory and Python 3.13.15. Its **41 tests passed**, including
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

This checkpoint motivated the local/fixed/evolvable multi-distance continuation
above. The [original range proposal](docs/MULTIDISTANCE_PLAN.md) remains available;
the actual V2 design and changed limits are recorded separately.

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

**Also implemented in V2**: multi-distance sensing, conditional gene expression,
larger random-origin genomes, diversity/lexicase search, training-sample-matched
independent search controls and exact checkpoint resumption.

**Not yet built**: a reliable random-origin solver, hierarchical or 3D substrates,
exact CPU-budget-matched search controls, a broad optimized conventional baseline
audit, or a competitive result.

## Experiment boundaries

- No paid APIs, cloud services, AWS deployment, foundation-model inference or unneeded dependencies.
- Do not use BFS or a precomputed solution *inside* the organism at inference time. Ground truth may be computed offline for scoring.
- Do not benchmark naive Python BFS alone and call a win; include compiled baselines and complete end-to-end wall-clock cost.
- Do not confuse millions of logically simultaneous grid updates with millions of CPU/GPU cores or zero-cost computation.
- Preserve reproducibility: fixed seeds, explicit environmental metadata, unseen tests and detailed result logs.
