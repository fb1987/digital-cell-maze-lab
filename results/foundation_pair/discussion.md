**The controlled comparison is informative but does not pass its replication gate.**
Paired-first selection passes the complete preregistered screen in one of three
local replicates and none of three evolved-range replicates; two were required.
There is a useful local short-route signal, alongside a different, sparse
longer-route precursor preserved by Current selection. Neither establishes a
general or competitive maze solver.

Local Paired primary selections complete **44/144 fresh 3–4-edge pairs**, versus
16/144 for Current, 9/144 for the starting V12D selections on these same cases,
and zero for resampling. These successes span eight independent base layouts;
three work in all eight paired poses. Eight successful poses have cycles in the
source component. Every completed 3–4-edge pair includes at least one route with
a turn. Exact-two pairs improve to 70/144 versus 46/144 Current and 20/144 at the
checkpoint, with all 144 adjacent pairs retained. The replicate detail matters:
Paired's challenge counts are 24,16,4 versus Current's 0,16,0. One replicate ties
Current, and the last has no all-pose challenge layout. The aggregate gain is
promising, but it does not satisfy the agreed consistency criterion. With
evolvable ranges, Paired completes 10/144 3–4-edge pairs versus Current's 12/144.
No primary selection completes a 5–8- or 9–16-edge pair.

**A preserved local lineage produces rare, much longer correct outputs.**
Current/local replicate 1 selects `foundation_study/local/fresh/evolution/1/i72095`,
born at generation 858, before this experiment. It is present in both starting
populations and becomes the common paired validation leader at generation 872 in
both arms. Current retains it; Paired later replaces it, with its final primary
replacement selected at generation 1240. On the new ordinary corpus, the old
genome emits shortest paths of **9, 24 and 25 edges**, with **2, 5 and 12 turns**,
all on trees. All three fail when the goal pulse is removed and survive nonlocal
zeroing. These are real completed rasters, independently replayed and graded.
They are not a new mutation discovered during V12E, and three successes do not
establish reliable long-route generalization. The observation also shows why
better short-pair validation scores cannot be assumed to preserve broader skills.
Current/evolved replicate 2 separately produces one eight-edge, two-turn tree
route from a V12E-born descendant; it too requires the pulse in this intervention
and survives nonlocal zeroing. Geometry is a descriptive reading of saved outputs,
not an additional holdout assay.

Mechanism remains mixed. Of local Paired's 44 successful 3–4-edge pairs, **28
remain complete without the goal pulse**. Static goal flags and endpoint-aware
stopping remain active, so this does not demonstrate independence from goal
information. Current/evolved's 12 successful 3–4-edge pairs fall to six when
nonlocal values are zeroed and to zero without the pulse. Thus some correct
paired outputs depend on nonlocal values in these contexts, while there is still
no net multirange advantage. Paired/evolved retains all ten of its 3–4-edge pairs
under nonlocal zeroing. Ablated reads retain their charges. These interventions
condition on success and do not measure a new generalization rate or identify
the complete algorithm.

The late local gain supports continuing the random-origin research. Its frozen
Paired selections at +0/+48/+128/+256/+500 generations produce 9/19/17/17/44
complete 3–8-edge pairs on this same corpus. The trajectory is non-monotonic,
and these are correlated measurements, not five independent replications. All
12 evolved primary lineages trace to random immigrants from V12C, never a known
solver; their roots were born at generations 1–81. All have 256 genes, but that
does not measure functional complexity. The selection intervention is real:
all six matched population trajectories diverge, and same-pool/same-RNG replay
finds 3,090 different parent genotypes among 450,000 actual parent draws under
the alternate ranking. That counterfactual is not another evolved replicate.

The practical limits remain large. Paired cohorts each solve 11/216 ordinary
reachable mazes and 0/179 ordinary cases at distance ≥8. Current solves 11/216
local and 13/216 evolved, including the four sparse longer successes above.
All primary cohorts solve 0/48 disconnected cases, with no false reachable
no-path claims. Compiled BFS, A* and bit-wavefront solve all reachable and
disconnected cases. Eligible random-origin elementary timings are a median
54.28× slower than compiled BFS; none of the longer random-origin successes
falls in the prespecified ordinary timing subset, so no timing claim is made
for those routes. The intact VM wavefront misses nine long ordinary tree routes
under its tick limit; that is distinct from the compiled reference results.

**Recommended next step, not launched:** independently confirm and explain the
preserved longer-route local genome before another large search. Freeze that
genome, its relevant saved predecessors and the Paired replacement; test new
goal-switched, orientation-balanced tree and cyclic layouts at longer distances,
with fixed-time trajectories and pulse/endpoint controls to distinguish useful
routing from special stopping or growth patterns. Keep all short-pair and
longer-route variants and the full population/RNG continuations. All 124,392
layouts used so far must be excluded. This is a focused mechanism and transfer
test, not a reason to abandon random-origin discovery or assume that capacity
alone will solve the remaining problem.
