# M19 history diagnosis: discoveries survive, skills do not yet accumulate

**The saved histories do not support the idea that selection simply discards useful discoveries.** Of177 mutant births that added an optimal reachable training response beyond both their immediate parent and all13protected references,166survived their first training selection and161later reproduced. Every one of the51connected-arm additions survived;49reproduced. The central problem in these records is that new abilities usually replace earlier abilities. None of the177additions retained all correct responses of its M19 phase-entry ancestor on the same panel.

This is post-hoc DEVELOPMENT analysis of closed M19 data. It adds no fresh cases, candidate executions, generations or confirmations, and does not change M19’s frozen negative confirmation. The observations are related births on small, rotating panels; they are not independent discoveries or evidence of general solving.

## Scope and accounting

All128,700M19 births were traced:111,375mutants and17,325immigrants. There are110,970first-training mutant observations:36,990perarm. The final405mutants have no next training observation and are right-censored. Exact immediate-parent responses are available for every first-training mutant. Entry-ancestor comparisons are missing for309observations:62generic,136disconnected,111connected. A byte-identical genome alias can supply an exact entry comparison on the same panel; unavailable entries remain missing.

We separately examined13,213mutant assessment presentations, including repeated identities. Parents were available for10,829; entries for13,186. Assessments are the reused, reference-conditioned M11 development panels, not confirmation. The final1,680confirmation cases are not reused to nominate anything. All420sealed M19 files and13local records, including both original journals and backups, retain their hashes.

## Copying preserves an existing process; later changes rarely add a robust ability

| First-training observation | Connected copy | Disconnected copy |
|---|---:|---:|
| Copy children evaluated with their parent |7,077|7,383|
| Same terminal mask/status on the whole panel |6,641 (93.8%)|6,940 (94.0%)|
| Same terminal output, but more counted work |6,631|6,934|
| Any newly correct case over the parent |0|0|
| Survived first training selection |1,664|1,725|

Finite-panel output equality is not internal or semantic equivalence. Copying can change work, halting or unqueried behaviour. These figures show that the operator generally copies existing behaviour and charges extra work, which is consistent with the intended initial preservation step. They do not show that the copied process becomes a useful independent computation. All observed direct copies had zero correct-case additions over their parent; they also added zero complete ordinary bases or target upstream pairs beyond their parent and the protected union.

Later mutations after a connected copy do change outputs:3,411/10,704first exposures differ from the immediate parent. Among those10,704births,23add an optimal reachable case beyond both parent and portfolio; all23survive and reproduce. None keeps all entry responses, and none adds a complete target upstream pair. This establishes access to changed behaviour and occasional training successes, not cumulative algorithm construction or a causal benefit of copying. The populations and parents already differ across arms.

## True additions versus inherited coverage

Coverage beyond the protected references is not automatically an ability acquired by the latest mutation. The base export’s legacy-named `portfolio_gain_*` flags describe coverage present plus retention. They do not subtract the parent. The refinement explicitly subtracts BOTH parent and protected coverage before calling anything an addition. Of1,141first-training births with a reachable success outside protected coverage,964merely inherit such coverage from their parent. The remaining177are actual additions on that panel.

| Arm | Mutants first observed | True additions | Survive first selection | Later reproduce | Keep all immediate-parent correct responses | Keep all entry responses |
|---|---:|---:|---:|---:|---:|---:|
|generic|36,990|73|65|62|0|0|
|disconnected|36,990|53|50|50|3|0|
|connected|36,990|51|51|49|1|0|

All four additions that retained every immediate-parent correct response and made zero false no-path claims survived and reproduced. They nevertheless lost14,30,34or40correct entry responses. Their immediate parent had already lost ancestral skills. A locally improving step can therefore sit inside a lineage that has deteriorated relative to its starting algorithm. Comparing only adjacent generations would hide that.

Among all177true additions, only10retain90%of every nonempty immediate-parent skill class; only1retains90%of every entry skill class.103retain the nonempty A0disconnection reference at90%;169make zero false no-path claims. No addition meets the combined parent90%/entry90%/disconnection90%/zero-false gate. These are distinct diagnostics: failure is not explained solely by disconnection, nor solely by the100%retention threshold.

### Selection policy strata

Each arm has9,828first-exposure mutants from reserved exploration breeding and27,162from shared lexicase. True additions split21/52generic,14/39disconnected and13/38connected between reserved/shared breeding. Both routes can produce additions. Reserved exploration, copying and generic operators were not independently randomized within these related cohorts, so these counts are not causal efficacy estimates.

## One concrete17-edge example

`m19/connected/0/disconnected/g36/b48` is a single generic operand edit in block6, not an initialized-copy descendant. On an11×11perfect training maze, it emits the correct17-edge shortest route in both tested poses; its exact quota_child parent fails. The parent and child each run35ticks. The child survives and has10direct offspring, but loses9other correct parent/entry responses while adding12correct responses overall on that96-input panel. It handles the12queried disconnected inputs and makes no false no-path claims there. This is a real new training success with a substantial tradeoff. It was not retained in the final live/archive pool and was never independently confirmed as a nominee.

The following grids decode the SAVED raster bytes: `#`wall, `.`unlit open site, `*`illuminated site; `S`source and `G`goal overlay their raster sites. The parent output is disconnected; the child output is a valid shortest path. No solver was executed to draw these grids.

```text
Parent                  Mutated child
###########             ###########
#***#*#...#             #***#.#...#
#.#.#*###.#             #*#*#.###.#
#.#.**#.#.#             #*#***#.#.#
#.###.#.#.#             #*###*#.#.#
#.**#.*G..#             #***#**G..#
###S#####.#             ###S#####.#
#.......#.#             #.......#.#
#.###.###.#             #.###.###.#
#...#.#...#             #...#.#...#
###########             ###########
```

This one longer success is encouraging evidence that variation can reach additional route behaviours. It is a perfect tree from training, selected here post hoc as the longest ordinary addition. It does not demonstrate cyclic routing, a scalable algorithm, copy-induced improvement or transfer to unseen confirmation mazes. The exact stimulus, edit and saved records are in long_training_example.json.

## What the broader assessments show

Across all13,213mutant assessment presentations, including archive candidates, there are **zero new complete nonfork prefix2+pairs and zero new ordinary bases solved in both poses beyond the protected portfolio**, even before retention gates. This broadens the original result beyond just the27nominee roles. It still excludes organisms eliminated before an assessment and is not fresh confirmation.

When a parent is available, only three assessment presentations add reachable correct cases beyond both parent and portfolio: two generic and one connected descendant. The additions are isolated alternatives/poses of fork tasks. They do not form a complete new upstream pair, and each loses many entry responses. For example, the connected g127/b21descendant retains all current-parent correct responses on assessment128but has lost122entry responses. It adds one portfolio-new single alternative, produces offspring, and later disappears.

Thus the record does not support a hidden collection of robust new solvers discarded only by final nomination. Nor does it show that selection immediately eliminates most actual training innovations:94%survive their first selection. The missing step is stable accumulation and transfer. Assessment availability and early eliminations prevent ruling out every missed opportunity.

## Recommendation

I would prioritize an experiment about **adding a computation without dismantling the existing one**, rather than another unchanged long search or an immediate increase in novelty rewards. More aggressive retention alone would reject essentially all observed additions; more novelty alone could amplify the same tradeoffs. The current data do not isolate a single architectural or selection cause.

The next proposal is a bounded, matched copy-specialization assay: compare current generic variation with edits restricted to the copied writer and its existing regulatory attachment, keeping the rest of the same evolved scaffold intact. Select eligible edges prospectively, preserve random-origin provenance, use the same runtime and budgets, and measure new correct responses together with source/entry-skill retention on identical panels. This tests whether useful additive changes are accessible before paying for another sustained campaign. It is different from assuming that duplication itself creates an extra solver. No known solver or path-specific answer should be inserted.

If additive variants appear in that assay, a subsequent selection experiment could test bounded lineage-specific replay of discovered skills, separate from the existing fixed parent-conditioned banks. If additive variants remain absent, that would strengthen the case for revising how independent local processes and regulation can coexist. Both are hypotheses requiring new authorization and a concrete protocol; no further experiment has been launched. Random-origin discovery remains the research objective.

## Verification, costs and limitations

The base saved-data audit PASS checks all128,700birth events, all110,970first-training survival/breeding observations, reconciles original M19 nominal and per-operator survival counts, and checks1,937fixed sampled capability comparisons using a separate existing set implementation. The incremental audit PASS checks ALL180positive training/assessment events plus fixed samples:2,094saved comparisons. These checks reuse previously audited grades; they are not a second VM or confirmation.

Successful base analysis took85.58s (85.45CPU seconds), with688.7MiBpeakRSS. Its audit took72.81s; incremental refinement75.79s; incremental audit94.57s. Recorded successful passes total328.75wall seconds. Zero candidate executions or new cases occurred. An initial full read pass failed nominal padding reconciliation before export; its precise wall/CPU cost was not retained. Its script/plan/traceback remain under failed_attempt_001, and amendment_a1.json documents the bookkeeping fix. Eight focused synthetic checks passed across the two test files; no maze generation. The inherited-coverage distinction is explicitly documented in refinement_a2.json. Two local plotting-dependency probes found matplotlib unavailable; the example uses saved-byte text grids instead, without installing packages.

The analyses used a single local CPU worker per pass within20-minute per-pass/8GiBmemory/512MiBoutput/16GiBfree-floor bounds. Repeated births, repeated panels, related origins, conditioning on survival and differing ancestry prevent significance or causal copying claims. Missing parents, missing entry models, empty skill classes and right-censoring remain explicit. No fresh confirmation, general-solver or speed claim is made.

All M19 originals, backups, failed records, layout ledgers and completion seals remain unchanged. This supplemental packet is separate, with its own completion hashes. The old monitoring automation stays paused. No evolution, recombination, solver injection or cloud compute is running.
