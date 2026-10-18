# Instructions for Codex and other coding agents

## Mission

Build an experimental, low-cost **digital-cell maze solver** that can evolve compact local reaction rules. The core research claim to test is whether an evolvable, biological-style regulatory/local rule system can find **correct shortest paths on unseen mazes** with an advantageous combination of CPU/GPU compute, latency, and memory when compared with conventional implementations.

This is a scientific prototype, not a startup website, an AWS agent swarm, or a request for generic LLM-powered reasoning. Avoid remote API calls and expensive infrastructure.

## Critical user intent

- Each *organism* contains a spatial array (a "tissue" or reaction substrate), accepts one entire 2D maze as stimulus, and emits an output raster in which illuminated positions represent the path.
- The genome defines the shared or structured local update rules and expression/regulatory behaviour; local sites are not each fully autonomous LLM agents.
- A **population** of organisms with different genomes competes over many mazes. Organisms with stronger general performance are selected, mutated and reproduced over generations. Test both a fully random starting population and populations seeded with useful known rules.
- Explore sparse expression, negative feedback, concentration/decay, time, context accessibility, and perhaps multiple signalling scales *only if experiments justify their cost*. Do not force elaborate biological metaphors into the implementation.
- Eventually support much larger mazes and 3D grid mazes, but **do not start there**.
- User prioritizes **efficiency** over the spectacle of parallelism: the target is useful computational performance, not raw swarm size.
- **Random-origin discovery remains a central, ongoing research track.** The user
  explicitly does not want a small negative pilot to close this direction. Test
  whether greater heritable capacity, regulation, evolutionary time and pressure
  help. Preserve population/RNG checkpoints and useful diversity. Do not silently
  insert a known solver into a supposedly random-origin lineage. More complexity
  is a hypothesis, not a guarantee; record effective behaviour and real cost.

## Invariants

1. **Algorithm not answer**: no genome may store the correct route for a particular maze. Train and evaluate across separately seeded environments.
2. **Independent evaluation**: BFS may produce oracle paths for fitness/tests only. It must never operate inside candidate inference.
3. **Fair benchmarks**: compare completed valid path outputs; include input decoding, internal updates and final raster/path emission (or report separate timings transparently). Warm JITs with the same array mutability/dtype/signature as production. Benchmark multiple warm repetitions and report medians and ranges.
4. **Correctness precedes speed**: wrong or partial routes are not faster solutions. A legal path and shortest-path optimality are separate metrics. Disconnected grids must be handled explicitly.
5. **Budget bounded**: genome size, memory footprint, instruction count, update cycles and population size all have hard limits. No arbitrary generated code execution, no arbitrary system access, no recursive spawning.
6. **Reproducibility**: record RNG seeds, maze family, CPU/GPU, Python and dependency versions, training iteration, fitness and runtime; isolate holdout seeds.
7. **Avoid hidden advantages**: perfect mazes are trees where pruning finds the unique path; cyclic mazes invalidate the same method. Report both. Report data movement and total work alongside latency.
8. **Local first**: no cloud, LLM API, model downloads or paid providers without an explicit later user instruction.

## Immediate first task

Current checkpoint (October 18, 2026): the local pilot and V2 range/regulation
continuation are complete, with 63 passing tests. Read
`results/range_and_regulation.md`, `docs/RANGE_STUDY_V2.md` and the original
`results/first_evolution.md`. V2 used 96×120 rich random populations, eight
channels and up to 128 gated genes. Rich local/evolvable genomes solved 2/216
and 1/216 reachable tests, all adjacent endpoints; neither solved any of the
165 distance>=8 cases. Independent resampling solved 2/216, so no evolutionary
advantage is established. Seeded arms all solved 211/216 with no nonlocal
reads; increased inference budget explains the improvement over 189/216 at
the old cap on the same fresh tasks. No competitive speedup was found.

V1's source/results remain untouched. V2 is in separate `regulatory*`/`range*`
modules. Full next-population and RNG checkpoints permit deterministic
continuation. Do not retune against already inspected tests. Original mission
steps below are historical; do not repeat them as unfinished work.

The user wants random-origin emergence to remain central. Preserve these local
and multirange controls and investigate effective regulatory complexity and
evolutionary pressure, rather than infer impossibility from the bounded negative
runs. A sensible next controlled test holds expanded capacity fixed while
testing precursor/source-dependent signal-transmission objectives against the
current fitness. Exact route correctness must remain the primary final measure.
Keep prior raw results immutable; label continuations/diagnostics separately.

1. Inspect and run `cellular_maze_lab.py` and `tests/`.
2. Implement a **minimal bounded evolvable organism** with a small, typed genome and 2–4 internal per-site state channels. Define a compact grammar of deterministic local instructions. Consider a finite-state/Boolean rule table or small linear program; avoid implementing a giant neural network.
3. Add separate organism and evaluator modules, ideally isolating maze generation, reference solvers, execution, selection, and scoring. Preserve baseline behaviour.
4. Implement selection and mutation over a small population; evaluate candidates on rotating training mazes and fixed unseen holdouts.
5. Run a short **two-arm** experiment: purely random initial genomes versus genomes seeded with a functional wavefront-style rule. Use the same fitness and compute limits. Include a no-evolution ablation.
6. Produce `results/first_evolution.md` (accuracy, optimality, runtime, steps, memory, failure cases), machine-readable raw results, and simple visual samples of the best output.
7. Commit/leave runnable code, deterministic tests and instructions. Do not report success without an accurate holdout result.

## Sensible ordering

Phase 0: reproduce baseline -> Phase 1: simple genome runtime -> Phase 2: evolution and fitness -> Phase 3: stress-test larger and cyclic mazes -> Phase 4: multiscale or 3D only when justified.

Avoid spending the first iteration on a GUI, cloud orchestration, genetic text compression, or expensive GPU kernels. A good negative result is valuable. State what failed.

## What to report when done

Summarize: files changed; commands/tests run; accuracy on unseen mazes; baseline comparisons; representative failure; time/memory cost and scalability implications; and one well-justified next experiment.
