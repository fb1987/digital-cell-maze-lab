# M7: matched breeding-allocation comparison

Authorized October 21, 2026 by “Please proceed” after the completed M6 report.
This new phase tests whether guaranteed reproductive opportunity helps preserved
specialists acquire additional routing abilities. M6 allocated 83.544% of mutation
births to A0 and 1.783% to standard0191. This motivates the intervention; it does
not establish that quotas will work. No old history or allowance is resumed.

## Paired starting material and single intervention

Three replicate pairs, each with one shared-selection and one quota population
of 96. Both members have identical ordered genomes, clone counts and protected
references. Pair members start with the same evolution RNG state; different pairs
have different RNG states. Streams diverge as selection consumes random draws;
subsequent mutations are not asserted to be identical counterfactual edits.
All six populations see identical mazes in each matched round.

Seven protected exact M1 genomes, in this order:

1. M5 a1/standard/0191, exact neutral-embedding M1 body.
2. M3 A0, m3/modular/0/mixed/g669/b31.
3. M5 a0/standard/0434, exact neutral-embedding M1 body.
4. M3 A1, m3/modular/2/single/g800/b15.
5. A0's M3 root, m2/a1/d2/00410.
6. A1's M3 root, m1/modular/1/broad/mutation/g84/b11.
7. M6 frozen upstream nominee, m6/modular/0/single/g900/b17.

The four focal lineages are 1, 2, 3 and 7. Add 89 clonal slots in that repeated
order: 23 copies of focal1, 22 each of focal2–4. Seven protected plus 89 clones
makes96. Clone creation is not mutation. All M7 mutation depths start at zero;
source records and inherited M1/M2/M3/M5/M6 ancestry are retained separately.
These are M6-informed preserved random-origin genomes, not independent origins.
Including the exact M6 nominee in both arms is a prospective choice; inspected
M6 confirmation cases are excluded, and no new old-panel screen is performed.

In BOTH arms retain44 survivors using the unchanged M6 mechanism: seven exact
protected copies, eight merit survivors, up to12 extra coverage survivors, up to18
genotypically distinct finite-panel neutral variants, then lexicase fill. Same
merit, epsilon-lexicase, archive16, mutation operator, runtime and nomination.
Protection guarantees that each focal lineage has an eligible parent, not that
its descendants survive. There are no lineage-specific survivor reservations.

Every round adds seven random immigrants and45 single-edit children:

- Shared: all45 parents selected by existing lexicase among all44 survivors.
- Quota: nine parents selected within each of the four focal root-descendant
  survivor groups, in fixed focal order (36 births), followed by nine unrestricted
  parent selections among all44 survivors. Unrestricted slots can also select a
  focal lineage, so nine is a minimum. Newly immigrated roots can reproduce in
  the unrestricted slots. No fallback or quota reassignment is allowed; each
  focal protected root always remains eligible.

Birth decisions record the reserved root or null. One unchanged generic mutation
opportunity per child, including logged no-op edits. No sexual recombination,
new holding operator, curriculum change, output cleanup or known-solver injection.
Unchanged M1 eight-channel local runtime: <=256instructions and256ticks,
4096reads/site and32768instructions/site. Engineering solvers remain external.

## Matched evaluation and inputs

Seeds: evolution/training2026102116, development2026102117,
confirmation2026102118; discarded fixtures202610210116 and202610210117.
Exclude all2,109,655 M6 cumulative whole layouts plus ALL new fixture layouts,
including rejected and unqueried variants. No fixture descendants become founders.

Copy the M6 external input construction into a new M7 namespace:48 train inputs
per round (18 structured,24 ordinary reachable,6 disconnected), same rotating
contexts, poses, graph types and prefixes. Ordinary training routes are >=8edges,
with perfect11 medium/long and random9 medium strata. Candidates see only maze
cells and endpoints. Length sampling is external, oracle-based construction;
max2000 draws per requested ordinary base, all attempted layouts excluded.

The fixed392-input development panel is assessed initially, every100 rounds and
on the final population. Each population receives exactly96×48 nominal training
queries per round and115×392 nominal assessment queries per assessment. The
assessment capacity is96live+16archive+3frozen. When identities overlap, fill
unused assessment slots with explicitly marked fixed A0 reference aliases.
Padding is never selectable, archived or nominated. Exact genotype/query pairs
are physically deduplicated across all six populations; report nominal allocations,
actual physical calls, candidate seconds and work separately. Equal evaluation
budgets do not imply equal CPU cost. All populations finish the same round count;
no arm-specific performance stopping or redistribution of unused budgets.

Same three fixed nomination roles per population: integrated (zero false no-path
and>=90% of nonempty protected A0 correct-disconnection set, then aggregate
merit), upstream exploratory (new nonfork prefix2+ pairs beyond protected union,
then fewer false no-path, more correct no-path, merit), and ordinary merit. All
ties by identity. Initial nominees remain frozen no-evolution references.
Final development nominees, exact roots/parents, all references, ancestry and
states are frozen and committed/pushed before any independent confirmation.
No role switching, reselection or extension based on final outcomes.

## Prospective endpoints and limitations

Fresh confirmation:1680 inputs,400 complete structured pairs,200 corridors,
256 ordinary reachable bases in two poses (512inputs),168 disconnected inputs.
Report perfect11/perfect15/random9/random15 separately with route-length strata
and pose-specific gains/losses. Familiar grammar and correlated poses/variants
limit transfer claims; three replicate pairs are a small policy pilot.

Keep the M6 individual acquisition criteria unchanged, now against exact M7 roots
and the SEVEN protected-reference union. Each gate requires at least one M7
mutation birth, zero false reachable no-path, >=90% retention of exact-root paired,
corridor, ordinary-both-pose and correct-no-path sets (empty root denominator=N/A),
AND>=90% of protected A0's NONEMPTY correct-no-path set.

- Upstream: >=8 new nonfork prefix2/4/8 complete pairs across>=2contexts, absent
  from BOTH exact root and protected union, plus the shared retention gate.
- Long ordinary: >=4 new both-pose bases of length>=8, both perfect/random,
  >=1length16+, absent from root and protected union, plus the same gate.
- Combined: both acquisition criteria.

Policy primary is fixed to the INTEGRATED role: count new nonfork prefix2+ complete
pairs beyond root/protected union, assigning zero if the retention/disconnection
gate fails. Compute quota-minus-shared within each replicate. Descriptive support
for quota requires a positive difference in at least two of three pairs AND a
positive sum. This is a registered descriptive pilot rule, not a significance
test. Report all differences, ties and individual acquisition flags. A positive
count below the individual acquisition threshold is not broad acquisition.
Other roles, raw specialist gains, lost skills, no-path changes, mutation-depth,
lineage birth shares and live/archive lineage persistence are secondary diagnostics.
Do not substitute a secondary endpoint when the primary fails. Equal budgets
permit a bounded policy comparison; few related founders and three pairs cannot
establish universal policy superiority. No general-solver or speed claim.

## Resources, preflight, audit and preservation

Ten workers for the combined six populations.70-minute soft search target,
90-minute cumulative hard search ceiling; max4096matched rounds,100M charged
physical calls and10^15work. Reserve6×96×48 next-round queries plus6×115×392
final assessment queries. Stop independent of capability; resource guards may
stop earlier.12GiB process-tree RSS;12GiB total M7 storage INCLUDING results,
nested backups/final journal;16GiB disk-free floor. Preserve all old scientific
records. SQLite FULL/WAL and transactional receipts; never launch duplicate
writers, reset history, change sealed files or bypass bounds.

Final separate allowance:<=1M calls,10^14work,90minutes, same combined storage/RSS
and free-space bounds. Setup, audits and final costs are additional and reported.
Search audits are allowed to finish after the search wall allowance; they do not
create new candidates or extend evolution. No cloud or external model usage.

Preflight controls on discarded392 and1680-input panels; four discarded matched
rounds after initial assessment,1248 births, complete transition/RNG replay.
Tests verify exact founders, paired allocations, protected roots, quota floors,
shared unconstrained selection, equal nominal queries, gates, primary endpoint,
zero-round stop/freeze, and the full audit/final pipeline on excluded fixtures.
Record all setup costs; failures stay preserved. Register source/config/founders/
protocol/tests/workflow/inspector/fixture hashes, verify all351 M6 completion hashes,
and push before scientific generation.

Durable workflow: search; freeze and push choices; full search audit; registered
fresh confirmation; analysis; ALL-native final audit. Search audit regenerates
all corpora/tasks/selection/mutation/RNG, independently regrades all candidate
responses, and replays hash-selected native samples (1/256train,1/32assessment),
then verifies frozen artifacts. Final audit replays all candidate outputs/grades,
conventional BFS/A*/bitwave controls and canonical metrics including policyprimary.
Shared production VM/reproduction, independent raster grader; no second VM claim.
Any guard/error/failed audit preserves traceback and receipts and stops workflow;
no automatic failed-workflow restart or silent repair.

After both audits PASS: report actual capabilities, paired results, allocation,
ancestry, ordinary length strata, controls and costs. Preserve originals; make
verified SQLite-API backups under writer locks only within12GiB combined storage
and16GiB free floor. Export all initial/search/final generated/rejected/unqueried
layouts; seal completion hashes; update AGENTS/progress; commit/push compact
evidence, never raw journals. A15-minute monitor stays quiet on routine progress,
alerts only meaningful capability change/completion/failure/user action, then
pauses after preservation/reporting or when action is required. M7 explicitly
authorizes this registered confirmation. No phase beyond M7 is authorized here.
