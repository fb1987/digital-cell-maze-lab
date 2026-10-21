# M1: modular random-origin discovery pilot

**Complete, audited, and independently confirmed.** The new representation supports interpretable inherited wave mechanics and within-genome computational reuse. This pilot does not establish a general maze solver, a speed advantage, or a replicated broad-transfer advantage over random resampling.

## What was tested

24 populations of 96, run for 128 rounds: flat versus eight-block M1 genomes; familiar versus broader ordinary-maze training; mutation versus random resampling; three independent founder seeds per representation. Within each representation/replicate, the four arms started from the same exact random population. Separate frozen initial nominees provide a no-evolution reference. All old deep-search lineages remain preserved. No known solver or oracle was injected into any random lineage.

M1 changes both the representation and variation operator: private single-assignment expression blocks, one writer per persistent channel, explicit channel ports, and within-genome block copying. Both designs retain the same eight persistent channels and bounded local runtime. Therefore this is a representation/variation-package comparison, not an isolated test of private memory. The common selector also differs from the historical deep campaign; comparisons across studies cannot identify its causal effect.

Registration `f18edcd` was pushed before search. Choices, final populations and exact selected ancestry were frozen/pushed in `34fc111` before final generation. The fixed final panel has 1,424 inputs/model:400 complete paired routing opportunities,200 corridors,168 total disconnected inputs, and 256 ordinary reachable inputs spanning perfect11/perfect15/random9/random15. The structured grammar is familiar; layouts are fresh. Size15 was excluded from this pilot’s training and nomination. Poses and structural variants correlate; cases are not all independent samples.

## Untouched final outcomes

Each bracket lists replicates0,1,2. “Ordinary” counts bases correct in both queried poses, out of 128 reachable ordinary bases. P and O are the two nominees fixed on validation: aggregate primary and ordinary specialist. They are not reselected on final cases.

| Representation | Training | Method | P complete pairs /400 | P ordinary bases /128 | O ordinary bases /128 | P false no-path /1256 |
|---|---|---|---|---|---|---|
| flat | familiar | mutation | [32, 48, 48] | [0, 1, 0] | [2, 2, 1] | [0, 0, 0] |
| flat | familiar | resample | [48, 48, 48] | [0, 1, 1] | [2, 2, 2] | [0, 0, 0] |
| flat | broad | mutation | [0, 8, 0] | [0, 0, 0] | [2, 0, 1] | [0, 0, 0] |
| flat | broad | resample | [32, 48, 48] | [0, 1, 0] | [0, 2, 2] | [0, 0, 0] |
| modular | familiar | mutation | [48, 32, 48] | [1, 0, 0] | [2, 2, 0] | [0, 0, 0] |
| modular | familiar | resample | [48, 0, 0] | [1, 0, 0] | [2, 2, 2] | [0, 0, 0] |
| modular | broad | mutation | [20, 96, 48] | [1, 1, 1] | [2, 4, 2] | [0, 0, 0] |
| modular | broad | resample | [0, 48, 48] | [0, 1, 2] | [2, 2, 2] | [0, 0, 0] |

The strongest paired result is modular/broad replicate 1:96/400 complete pairs (48/48 source-at-fork and 48/48 one-cell-prefix forks), versus 48/400 for its matched resampling primary and 0/400 for its exact random-immigrant root. It solves0 longer-prefix fork pairs and 0 second-junction/cycle pairs, while keeping200/200 corridors. Its root has no paired or corridor successes, so root retention in those categories is **N/A**, not evidence of retention. The immediate parent has exactly the same successful pairs; the final mutation did not create this ability. The selected descendant has 38 mutation births in its ancestry.

Its ordinary result is2/256 reachable inputs: the two poses of a single random9 base with a one-edge path. Perfect11, perfect15 and random15 are all 0/64; correct no-path is0/168, with 0 false reachable no-path claims. This is a narrow structured-routing acquisition, not ordinary-maze competence. The separate intact flat/M1 controls and each conventional baseline solve all 1,424 inputs.

Family/size breakdowns, valid versus shortest outputs, correct disconnected decisions, corridor retention, exact root/parent comparisons and all 48 nominee aliases are in `summary.json`. A mutation-arm nominee may be an unmutated random immigrant; arm membership alone is never credited as evolutionary acquisition.

### Registered screens

- flat/familiar: replicate passes [False, False, False]; long-run screen **FAIL**.
- flat/broad: replicate passes [False, False, False]; long-run screen **FAIL**.
- modular/familiar: replicate passes [False, False, False]; long-run screen **FAIL**.
- modular/broad: replicate passes [False, False, False]; long-run screen **FAIL**.

7 of 48 nominee aliases pass mutated-root routing acquisition; 0 pass the additional broad-acquisition flag. Aliases can share genomes/roots and are not independent discoveries. The long-run screen additionally requires ordinary improvement over frozen references and the matched resampling nominee in at least2/3 replicates. No threshold was changed after observing results.

## What a discovered mechanic actually does

A preserved round 32 modular descendant, `modular/0/familiar/mutation/g24/b39`, comes from random founder 79 through 12 mutation births. Its116-instruction genome has only four primitive nodes in the static recurrent output/halt dependency cone. Those implement:

```text
C1(next) = positive neighbor signal from C6
C2(next) = C1 OR previous C2       # visible output
C6(next) = C1 OR previous C6       # persistent explored region
C7(next) = C1 OR previous C7       # halt signal
```

The runtime’s initial goal pulse enters C1. The organism grows an accumulating goal-origin wave, advancing one edge every two ticks. When it reaches the source at distance d, it stops at 2d+1 ticks and emits the entire goal-distance ball of radius d. This exact mask/timing prediction matches all 168 emitted reachable development outputs. The result is a interpretable local exploration mechanic, but its raster includes explored branches. It does not retain a parent chain or extract one route. Other instructions still execute and cost work; finite budgets and disconnected behavior remain separate.

The exact ancestry records an accumulator becoming block 7’s output atgeneration2, being copied to block 6 atgeneration8, then copied into output block 2 atgeneration23. Generic channel-role rebinding preserves each copied block’s self-memory. This is concrete within-genome computational reuse, not sexual recombination or proof that the copying operator causes a population-level advantage.

![Saved development rasters: explored region versus exact route](</Users/frankie/Documents/ChatGPT/digital cell/results/modular_pilot/development_wave.png>)

A later modular/broad lineage solves the one-cell-upstream validation forks as well. Its105-instruction genome has six primitive nodes in the output/halt cone. On all 164 emitted reachable development cases with d>=2, its output is exactly the goal-distance ball of radius d−1 plus the source, again stopping at 2d+1. Four distance 1 cases are explicitly outside that formula;32 disconnected cases are separate. This explains the prefix1 improvement as a delayed output wave, not arbitrary-length branch suppression or backtracing. These diagnoses use saved rasters only: zero extra inference or new maze generation.

## Compute, preservation and audit

- Search: 9,009,064 physical calls; 6187.35 summed candidate seconds; 6717.75 worker CPU seconds; 1255.38 elapsed seconds with 10 workers. Sampled peak process-tree RSS 2.547 GiB. 2,039,502,237,858 charged read/dispatch/exposure-check work.
- Equal nominal allocation: 405,312 slots/condition,9,727,488 total. Exact duplicate identities/models are physically reused; per-representation calls/work are in `cost_breakdown.json`. Mixed-model receipts do not permit defensible per-condition timing allocation. No latency comparison is claimed.
- Search history: 159,744 births replayed, including 69,120 mutation births and 90,624 random births. 37,432 committed receipts; zero uncertain attempts. Every population/archive/RNG and all batch generation replay exactly. All 9,009,064 search outputs independently regraded; 91,942 fixed sampled native replays. Audit elapsed 345.46s, additional to search.
- Final: 131,008 physical candidate calls; 90.20 summed candidate seconds; 97.01 worker CPU seconds; 14.41 elapsed seconds. 33,500,289,606 work. All outputs independently graded; final audit adds 6,908 native replays and 4,272 independently graded conventional baseline calls, taking 4.62s.
- Preflight/profile/rehearsal: 143,248 timed candidate calls, 66.83 summed candidate seconds. Two executions of the prototype tests add584 native calls, untimed separately. Seven focused tests and 10,000 mutation stress checks pass; not a fresh full suite. A deterministic stress-schedule alignment was corrected before registration, with discarded second-junction fixtures added; all layouts are excluded.
- Production selection and native implementations are shared by replay; raster grading is independent. Prototype random-program translation checks compare separate interpreter kernels, but are not a second full implementation audit of every scientific run. Main/audit costs are distinct. No post-registration scientific-source repair or protocol deviation occurred.
- Full local journals and safe SQLite backups are preserved; raw history is scientific data, not a cache. Source/choices/reports are committed to Git. All new layouts, including unqueried orientations, remain excluded from later studies.

## Decision and next research direction

The architectural change produced understandable, heritable exploration and modular reuse. The intact controls show that both representations can express a correct solver within these bounds on this panel; they do not show that evolution can readily find one. It did not yet produce the crucial separation between exploring the maze and emitting only the selected route. The inspected effective programs remain tiny even inside much longer genomes; additional gene capacity alone has not translated into a multi-stage solver. More evolutionary time remains a live hypothesis, not a conclusion established by this pilot.

Preserve these lineages and their complementary skills. The next useful bounded study is a mutation-accessibility comparison around the frozen wave and delayed-wave lineages: can generic mutations retain correct routing while reducing branch output on matched longer-prefix/cyclic cases, and do those improvements transfer to ordinary mazes? Include unchanged and matched random alternatives, freeze choices before fresh confirmation, and measure effective mechanism changes and losses. Do not install a backtrace, oracle cleanup or solver-specific module into a random-origin lineage. A subsequent 60–90min continuation should be a documented new phase justified by those results, not an automatic rerun or a declaration that more time cannot help. Sexual recombination remains optional until demonstrated compatible complementary modules justify its cost.

C1 confirmation and M1 together sharpen the research claim: random-origin systems can acquire useful mechanics. Accumulating those mechanics into reliable selective path output remains unproven.
