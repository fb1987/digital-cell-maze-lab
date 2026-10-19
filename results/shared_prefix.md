# V12Q — shared-prefix curriculum pilot

**Complete and independently audited.** The controlled curriculum change did not
produce a paired shortest-path solver across the first internal junction.
It did reproduce useful source-at-junction behavior in fresh random-origin
lineages. Those secondary gains include both mutation-associated gains and useful
unmutated random draws. They are not a general maze solver or a demonstrated
advantage from additional capacity, multirange signaling, or runtime speed.

## Main result

Every primary in both origin blocks gives **0/64 prefix 1 core pairs on validation
and 0/128 on untouched final**. All 31 physical random-origin final models,
including secondary archives and preserved anchors, fail every positive-prefix
pair and every two-junction/cycle pair. The separate intact solver succeeds.
The larger-run gate fails **0/3 carried and 0/3 fresh replicates**. No extension
or additional evolutionary experiment was launched.

Source-at-junction core pairs on the SAME final cases, out of 128 per selection:

| Origin / replicate | Current evolution | Mixed evolution | Resampling | Frozen |
|---|---:|---:|---:|---:|
| carry/0 | 128 | 128 | 128 | 128 |
| carry/1 | 128 | 128 | 128 | 128 |
| carry/2 | 128 | 128 | 128 | 128 |
| fresh/0 | 0 | 96 | 0 | 0 |
| fresh/1 | 96 | 64 | 0 | 0 |
| fresh/2 | 0 | 128 | 16 | 0 |

The fresh-origin aggregate is Current 96/384, Mixed 288/384, resampling 16/384,
frozen 0/384. This is a secondary descriptive result: the registered target was
positive-prefix solving, not junction-only success. Each arm sees the same final
contexts. Poses, goals and variants are correlated; 20 independent seeded clutter
contexts reuse a small number of route forms, not thousands of independent mazes.
This corpus is explicitly P-informed, not an ordinary-maze benchmark.

All carried primaries preserve 128/128 core junction pairs and 1344/1344 corridors.
Their 160/672 total final paired successes add 32 stress-fork prefix 0 pairs, but
none on extra-junction or cycle variants. Fresh mixed replicate 0 loses corridors:
1128/1344 (83.93%) versus 1344/1344 frozen. Fresh mixed replicates 1/2 retain all 1344.
The fresh resampling replicate 2 primary sacrifices corridor performance to 464/1344
while giving 16 core junction pairs; separate corridor archives remain saved.
No selected random-origin model makes a false no-path claim on final reachable
inputs. No-path successes concern isolated-goal clutter controls, not general
unreachability detection.

## What arose, and what is actually evolutionary evidence?

- Fresh/mixed 0 `fresh/0/mixed/i1151`, 114 genes, is 12 single edits from original
  founder 95. On the SAME validation cases that founder gave 0 junction pairs;
  the selected descendant gives 32/64 and then 96/128 on untouched core final.
  It works at arm lengths 3/4/6, all 8 poses, but not length 2. Its corridor loss
  prevents treating this as an unqualified improvement.
- Fresh/current 1 `fresh/1/current/i1146`, 96 genes, is 16 edits from original
  founder 22. Initial validation 0 becomes 48/64; final 96/128 includes six of
  eight poses at every arm length 2/3/4/6. Mixed 1 reaches 64/128 only on larger
  arms 4/6 despite 0 small-arm validation pairs. No isolated mutation-causality
  experiment was performed on either lineage.
- Fresh/mixed 2 `fresh/2/mixed/i1480`, 121 genes, gives 128/128 core junction pairs,
 1344/1344 corridors and 1344/1344 isolated-goal no-path responses. It is 13 edits
  from random immigrant `fresh/2/mixed/i507`. That immigrant ALREADY solved its
  first sampled training junction pair; necessity of the subsequent edits is
  unknown. This is a preserved random-origin lineage, not proof that 13 mutations
  created the primitive.
- Carried/mixed 0's new 94-gene winner descends 5 edits from another random immigrant,
  not from the preserved O routing lineage. The 95-gene **unmutated** carried
  resampling draw `carry/0/resample/i63` matches its final paired/corridor/no-path
  counts. Preserve this control; mutation was not required to sample that outcome.

A posthoc independent deque calculation on SAVED final rasters finds that all 2688
reachable masks of fresh/mixed 2, carried/mixed 0 and that 95-gene resample exactly
match the goal-distance ball stopped at the source distance. This is the same
output phenotype diagnosed in P, now seen in unrelated random-origin genomes.
It is emitted-output equivalence, not proof of internal BFS, identical internal
states, a shared mechanism or oracle access. No new candidate calls or mechanism
ablations were made for this diagnosis.

![Fixed normal-output comparison](shared_prefix/normal_outputs.png)

The illustration uses the first final context/pose/goal and mixed replicate 0,
not a post-final winner. Orange masks are wrong normal emissions, never successes
or retuned intermediate states. Moving the source upstream admits cells in the
unused arm. The final does not establish that these newly sampled genomes are
causally dependent on the same flags/pulse connections as P.

## Did the search actually explore?

There are 32 matched generations, 18 conditions of 96 organisms, 41,472 births:
**24,192 single-edit descendants and 17,280 random draws**, plus 288 fresh founders.
Generation 32's 1,296 newborns are preserved for future work and were not evaluated;
40,176 new births entered a subsequent training generation.
All initial pools/RNG, every birth/event, next population, protected anchors and
three common archives are retained. Carried and fresh origins are reported
separately; carried replicates share the P routing ancestry.

The six carried evolution arms produce 4,952 descendants of route depths 9/16.
Maximum depth along those lineages is 18–32 edits (mixed 22/24/18, current 27/32/29).
These are birth-chain depths and include the last unqueried offspring. Their
existence does not imply effective algorithmic complexity increased.
Across the whole pilot, the largest born genome is 167 genes, below the 256 ceiling;
this run therefore does not show a binding capacity limit or test a higher ceiling.

In 5,472 recorded same-batch child/parent comparisons, 538 change output mask or
status. These are a correlated co-presence subset, not a random sample of all
mutations. All measured training positive-prefix complete-pair counts remainzero.
A posthoc pressure check finds 18 prefix-score improvements in 2,823 mixed-arm
comparisons:15 improve overall aggregate rank, three worsen it. Onlytwo of these
improvements occur in the carried arms. Partial-score improvement is not a solved
route, and aggregate rank is not lexicase selection probability. The evidence
therefore does not support blaming the result simply on selection rejecting every
useful step. Nor does 32 generations settle the value of much longer evolution.

## Design, integrity and cost

Only training source-position mixture differs between the two evolving arms:
100% junction versus 50/50 junction/one-edge-prefix. Runtime, bounds, one-edit
mutation, fitness, elites, immigration and archive policies are identical.
Resampling uses the mixed stimuli and identical protection/validation allowances.
Training has two matched contexts per generation with common corridor/no-path
controls; all 8 poses are queried over 32 generations. Validation 8 contexts ×2 prefixes
×8 poses ×6 inputs =768/model. Final 20 contexts, prefixes 0/1/2 and true alternative
cycles gives 4032 inputs/model:1344 branched, 1344 corridor, 1344 disconnected.

Initial evaluation is physically shared across the three arms of each pool:
442,368 actual calls represent 1,327,104 logical calls. Every condition then gets
36,864 training and 6,144 validation calls.78 final aliases collapse to 32 models:
129,024 physical versus 314,496 alias evaluations. Main totals are
**1,345,536 physical /2,415,744 logical candidate evaluations**,
**251.23 s candidate inference** under the 720 s ceiling and
**146,149,776,961 charged work units**. Equal counts do not imply equal actual work.
Search wall 324.35 s + final wall 15.92 s;
peak main RSS 951.48 MiB.
Profile separately 27,648 calls/5.14 candidate seconds; immutable-byte JIT warmups
separately one candidate +three baseline calls per stage. The fixed 32-generation
schedule ended normally; unused allowance was not spent after inspecting results.

Compiled BFS, A* and bit-wavefront, plus the separate intact VM, each solve all
2688 reachable and 1344 disconnected final inputs. No latency benchmark was run;
no speedup is claimed. CPU AppleM 4,10 cores, 16 GiB; Python 3.13.15, NumPy 2.5.4,
Numba 0.68.0,llvmlite 0.50.0. No cloud, LLM or paid compute.

Registration/source/pools/fixtures: **4fafe1c**. Fixture timing initially chose
16 generations using 2× worst-pool mean, which would cover onlyfour queried poses.
A documented **timing-only amendment** changed the planning factor to 1.5 and chose
32 generations (526.57 s projected), retaining 600 s projection ceiling, 720 s hard cap
and 100 s final reserve. Original profile retained; amendment pushed **b1b9530**
BEFORE any research evaluation. No fixture scores were inspected/used for this
change, no frozen source was altered. All selections/ancestry/search/RNG pushed
**2ba193d** BEFORE final generation. This amendment is a preregistration deviation
made before scientific calls, not an unreported exception or post-result extension.

Audit passes first attempt: **1,373,184 exact candidate
replays**, **1,385,280 independently graded rasters**,
12,096 baseline replays, all 41,472 births/24,192 mutations,
18 next states and 78 aliases; 190 source/9 input/2,384 prior completion hash entries.
Audit wall 352.05 s, peak RSS 1047.92 MiB,
separate from research cost. Supplemental schedule audit verifies the amended
profile, pre-generation commit, all pose coverage, logical counts and summed times.
32 focused tests pass (10 new +22 related); 273 tests collected within `tests/`,
NOT a fresh full-suite run. An initial unscoped collection also traversed vendored
plotting-library tests and failed on their missing test dependencies; the scoped
collection succeeds. No research inference or frozen-source repair resulted.

## Interpretation and next step

Useful goal-conditioned wave behavior is accessible from several random-origin
lineages. Some same-validation improvements arise along mutated original-founder
lineages, so the random track remains scientifically productive at this elementary
level. But evolving branch isolation is a separate, still-unsolved step. The
registered target failed in every replicate, the strongest fresh wave already had
an initially useful immigrant ancestor, and unmutated resampling can achieve the
same phenotype. More capacity, regulation or time remain hypotheses.

Before another long search, run a bounded **mutation-accessibility diagnostic**
around several preserved, independently rooted wave genotypes, together with
fresh controls. Ask whether available edits create a reproducible signal toward
normal prefix routing, and distinguish output-changing edits from mere genome
size. Use entirely new layouts and retain an untouched final. Do not launch an
unchanged 60–90 minute continuation. The proposal is in
[the next-experiment note](shared_prefix/next_experiment.md); it has not run.

Exclude **all 187,416 whole layouts through Q** next:181,928 throughP +1,424 unique
preflight/software fixtures +320 validation +2,560 training +1,184 final. Include
all unqueried poses and test geometries. `shared_prefix_data.exclusions()` returns
THROUGH P ONLY; append Q software_fixtures, shared_prefix_fixtures, validation,
train and confirmation manifests. Final cases remain inspection data, never
new validation. All historical populations, source and completion hashes remain
unchanged.
