# V12Z: sustained mutation with a family reserve

Question: does reserving related but distinct variants improve transferable maze
solving under a fixed 75-minute local search allowance? This is a new asexual
experiment motivated by Y's ancestry-concentration observations. Y did not prove
that concentration caused poor solving. No sexual activation claim is made.

Seed2026102004; fixtures1434/1435; software23456789. Exclude255356 previous whole
layouts using the sealed X-R1 hash set, then every Z fixture, software layout,
validation and training layout including unqueried poses. Generate final only
after all selections and next states are committed and pushed. Native local
runtime, exposure7, existing bounded256gene/256tick execution. BFS is an oracle
and separate baseline only; never inside candidate inference.

## Conditions and ancestry

Carry/fresh ×3replicates × current_mutation/family_mutation/resample/frozen =24
conditions,96organisms each. Six founder pools are shared exactly across arms.
Carry protects20 historical random-origin genomes; fresh96 are independently
random64–128gene founders. No known solver enters any population. The intact VM
is separately labelled, used for fixture checks and final baseline only.

All nonfrozen arms retain44 and create52. Mutation arms:7random immigrants and
45one-edit children. Parent selection is current-batch paired-first lexicase with
10%uniform mixture. Resampling retains44 using current policy and draws52random
children. Frozen keeps all96founders and is evaluated on every common batch.
All arms receive exactly the same logical input counts. Initial screening is
physically evaluated once per shared pool and reused across its four arms;
subsequent training and nomination calls are physically separate and equal.

Only survivor policy differs between mutation arms. Protect anchors, take four
additional merit survivors, then family arm reserves up to20additional variants
from five families ranked by their best available current training member.
Fourrounds select at most one genotype-distinct member/family/round, maximizing
minimum inherited-locus distance to retained family members; original rank
breaks ties. Common behavior-diversity and rank fallback fill44. No genome-size
or family-count fitness reward. The common44/52 differs X's24/72: causal contrast
is WITHIN Z. Family membership uses recorded asexual ancestry, not instruction
similarity. Historical founders receive separate starting labels except the
explicit d07/d12 pair, whose documented deletion preserves homologous loci.
This is an operational grouping, not reconstruction of every historical shared
ancestor. New immigrants found new families. Mutation inherits family and locus
IDs; insertions/duplications get new child-local locus IDs. Unique family_z IDs
must never collide with current or protected identities.

Three common external validation archives (primary, choice, corridor) preserve
raw genomes, lineage metadata, nomination generation and metrics. Archives are
NEVER reinserted; protected anchors are the only fixed historical reinsertion
constraint. All populations/RNG, birth records and masks are preserved.

## Geometry and selection

19×19 structured boards have a shared stem extending8edges, straight or bent,
and asymmetric goal arms. Training uses two contexts per generation, oneprefix0
and oneprefix1/2/4;12queriedinputs in onepose, including paired goals, matched
pruned corridors and disconnected controls. The96generation pose schedule and
arm lengths2/2,2/3,3/4,4/2,4/6,6/4 are fixed. Every fourth generation uses a true
alternative-route cycle or a second junction in the hard context. All unqueried
poses/variants are saved and excluded later. Isolated clutter is replaced by
four disconnected two-cell regions; disconnected goal sites thus have neighbors.

Validation:10independent structured contexts (eight core:four arm-length pairs
×straight/bent;two straight stress contexts), all8poses, prefixes0/1/2/4/8.
Stress contexts each have fork/two-junction/real alternative-cycle variants.
There are560paired opportunities,1120corridors,1120structured disconnected
inputs. Add48ordinary reachable9×9bases (24Wilson trees,24random) and16partition
disconnected bases, all8poses, for3872inputs total. Reject isolated endpoints
in ordinary disconnected construction. Final doubles structured contexts to20,
with another independent64ordinary bases:7232inputs,1120paired opportunities.
Prefixes/graphs/poses within a context are correlated; contexts, not rasters,
are independent units. Ordinary partition geometry has a disclosed bias.

Initial validation evaluates every founder. Every32generations exactly two
current-batch behavior-diverse nominees/condition receive full common validation.
Primary rank: completeprefix>=4pairs, positive-prefix truecyclepairs, allpositive
pairs, allpairs, corridors, ordinaryshortest, no-pathminusfalseclaims, partial.
Digest then identity breaks ties. Choice and corridor archives are secondary.
Frozen primary is its initial all-founder selection. The same primary metrics
and precommitted choices are used on final, never reselected there.

Family gate: against currentmutation,resampling,frozen, eachreplicate must gain
>=16prefix4pairs above eachcontrol and >=16newprefix4pairs relative to frozen,
across>=2new independent contexts; >=8newpositive-prefixtruecyclepairs; retain
>=95%of the actual frozen successful paired/corridor/ordinary cases, and no
increase in false reachable no-path claims. Bothvalidation andfreshfinal must
pass, with>=96generations, in>=2/3replicates of an origin. Currentmutation is also
compared with resampling/frozen under the same gate. Prefix8 is separately
reported extrapolation. Descriptive secondary gains never replace the gate.

## Budgets, preflight and audit

Hard search wall4500seconds, candidate4500seconds, max4096generations; reserve
max(30s,1.5×largest observedround,8×calibrated meanround) before starting another
matched round. Wall includes initial screening, loop and checkpoint/final-choice
serialization; preparation, JIT warming, final and audit separately reported.
A feasibility estimate uses2×worst founder mean inference cost plus2×measured
24condition reproduction time; initial+96meanrounds must be<4200s. No scores
choose the duration, corpus size or a premature success stop.

Max4GiBRSS,3GiBstudy artifacts,40Mcandidate calls,4e13chargedwork. Final has a
separate600candidate-secondcap. Calibration plus discarded three-generation
preflight has180candidate seconds, including its exact inference replays.
Software checks: legal/optimal geometry, genuine alternatives, nonisolated
no-path, native signatures, protected identities, exact52births, ancestry,
mutation replay, unchanged frozen RNG and deterministic full replay. No pilot
birth is seeded into search. Freeze/push source, protocol, pools, fixtures,
calibration and rehearsal before scientific data generation.

Audit regenerates all corpora, checks all prior6923hash entries and registration,
replays every parent/selection/mutation/RNG/checkpoint/archive/choice event,
independently grades every stored raster, exactly replays all nontraining
inferences plus deterministic1/256training rows (SHA256[key,g,id,case] modulo256),
and all conventional baselines. Selection/reproduction replay shares production
functions; independent raster grading is a separate implementation. No claim of
exhaustive training inference replay. No latency/speedup claim without separate
warm complete-output timing. No automatic budget extension or sexual long run.
