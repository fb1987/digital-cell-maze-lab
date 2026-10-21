# M14: bounded exploration allocation under matched broad mutation

The user's Proceed after M13 authorizes preparing this new comparison and running
it when registered resource requirements are met. No old history is resumed or
changed. Random-origin discovery remains central; no known solver, oracle inference,
backtrace, learned answer table or sexual recombination is introduced.

## Hypothesis and limits

M13's broad mutation produced more finite-panel terminal novelty, but little novel
behavior compatible with all fixed-parent skills; no frozen nominee gained a fresh
successful input beyond the protected union. M14 tests whether reserving survival
AND reproductive access for useful distinct performance patterns helps traverse
intermediate tradeoffs. This is a selection-allocation POLICY PACKAGE, not isolated
causality of either survival or breeding alone. M7 already showed that root-based
birth quotas alone did not produce targeted deeper routing; these niches instead
follow current performance, without a chosen root quota. The existing control
already includes coverage and genotype-neutral alternatives. There is no claim
that all imperfect intermediates were previously prohibited.

## Common design

Six96-organism populations: three paired retention/explore histories. Exact twelve
M10-informed preserved random-origin references plus42clonal slots each exact
M9 gated_partial and gated_specialist, identical ordered starting genomes and
initial RNG withinpair. Separate future streams acrosspairs, not independent
origins. No M13-confirmation nominee becomes a founder. Source panel provenance
preserves earlier references/history. Seed2026102180; confirmation2026102181;
discarded fixture202610210180. Model/runtime/operator remain unchanged M1, bounded
256instructions/ticks. Both arms use ONLY ordinary generic all-block M1 mutation,
one opportunity perchild; no-op edits charged. Seven random immigrants and45mutant
births perround,44survivors,16archive,12protected references.

Reuse exact three M11 BANK development panels exported through M13, with only case
identities namespaced perreplicate. Both arms withinpair see identical inputs.
Train:48common freshly generated rotating inputs plus48persistent ordinary bank
inputs (24parent-successful bases byconstruction, no16+bankquota). Assessment392
inputs perorganism and115nominalslots incl nonselectable A0 padding;train96x96
nominalqueries perpopulation. Physical genotype/query dedup is explicit. Equal
nominal allocation is not equal CPU. M11 bank construction12,742parentcalls is prior
additional cost. Banks are reference-conditioned development data, not independent
confirmation. All old/fixture/generated/rejected/unqueried layouts excluded from
fresh generation; only expressly frozen development banks reused.

## Control selection and experimental allocation

Control is exactly the M13 retention selector:12protected,8merit by integration
rank,up to12coverage additions,up to18distinct-genotype finite-panel-neutral
alternatives,lexicase fills44. All45mutant parents chosen by existing shared lexicase.
A compatibility test compares survivor order,neutral IDs and RNG with the prior
selector on identical saved fixture rows. Both arms retain the same archive and
nomination rules; no extra evaluations, model slots or enlarged archive.

Explore begins with the same12protected and8merit. It then chooses UP TO12explorer
survivors from the remaining candidates. Eligibility and cells use ONLY current
saved evaluation rows, not any new organism execution:

- Reject an explorer with any false reachable no-path on this panel.
- Build a per-input routing-quality vector, in the common query order. Unreachable
  inputs score0, so disconnected-case behavior alone cannot qualify.
- Reachable optimal path scores4; valid nonoptimal path scores3. Otherwise require
  status emitted, failure missing_endpoint and existing partial fitness>=0.25;
  score min(2,floor(4*partial)). All other inputs score0. Partial fitness is the
  existing oracle-based branch/stray-penalized TRAINING metric, never an inference
  primitive. This does not prove each partial mask is a route precursor.
- Require at least one positive component. Empty output, all-flood/branch-only,
  wall-crossing, budget failure, disconnected-output-only or no-path-only profiles
  do not qualify. A candidate may still fail many other cases. No full-parent
  retention requirement applies to explorers.
- Group by exact quality vector; exclude vectors already represented by protected
  or merit survivors. Arbitrary mask changes that leave this vector unchanged do
  not create a niche. Each distinct cell has one representative: highest existing
  balanced performance rank (without parent-retention precedence), then smallest
  genome digest and identity for deterministic ties.
- Sort cells by vector, shuffle using that population's RNG, take at most12.
  Cells receive equal sampling opportunity regardless of clone count. No reward
  for raw Hamming distance, random raster complexity or all-zero novelty.

After those explorers, fill remaining44survivor slots with the same coverage,
neutral and lexicase operations using the updated chosen set. Thus explorers
replace some existing survivor capacity; they do not add to it. If no eligible
cell exists, survival reduces exactly to the control algorithm/RNG consumption.
Keep explorer IDs,quality vectors,eligibility counts and reservations in decisions.

When explorers exist, the first12of45mutant births cycle across the selected
explorers in their recorded order, giving each at least one offspring. Remaining
33mutants use shared lexicase over allsurvivors. With fewer12explorers cycle repeats;
with none all45use shared lexicase. Seven immigrants unchanged. Report actual
explorer survival/persistence,cell counts,breeding allocations and mutation depths,
not merely nominal quotas. Populations remain96. Every birth and RNG draw replays.

Exploration is measured on a finite, partly changing panel; it is neither global
semantic novelty nor proven useful algorithmic progress. Dominated current
profiles can qualify because temporary losses are the hypothesis. Coverage and
partial-quality filters limit arbitrary novelty but do not establish evolvability.
Reference genomes remain protected while their descendants may trade skills.

## Endpoints and frozen nomination

Common three nominee roles: INTEGRATED, upstream-exploratory, ordinary. Fixed
primary score is INTEGRATED-role specialist-only complete paired successes ONLY
when full integration passes, elsezero. Gate unchanged: positive M14 mutation
depth,zero false reachable no-path,nonempty fixed-parent pair/corridor/ordinary
both-pose/correct-no-path sets,100%retention of allthose skills and ALLspecialist-only
pairs (at least8across2contexts). Exploration descriptive support requires positive
paired differences in2/3replicates AND positive sum. No final role switching or
statistical significance claim from three related histories.

Separate deeper/long gates unchanged from M13: at least8new nonforkprefix2+pairs
across2contexts beyond exactroot AND protectedunion; longordinary at least4new8+
both-pose bases including16+and bothperfect/random families. Require90%root
retention includingcorrectdisconnection,90%nonemptyA0 correct-disconnection
retention,zero false no-path,positive M14mutationdepth. Report useful specialist
gains and losses even if stronger gates fail; distinguish inherited root/parent/
reference skills from acquisitions. No general-solver/multiscale/speedclaim.

## Bounds, storage and reproducibility

Maximum64matched rounds,assessment0/16/32/48/64 and at any declared soft stop.
1200ssoft/1800scumulativehard search,6Mphysicalcalls,1e13work,10workers,8GiBRSS,
600MiBphase storage INCLUDINGbackups,16GiBdisk-free floor. Same rounds/budgets as
M13, not another reduction because capacity is tight. Final separate900s/1Mcalls/
1e14work; eachaudit1800s, allwithin phase storage/RSS/free-space constraints.
No automatic failed-workflow resume, second writer, guard bypass or bound extension.

Use the already-tested reference+delta journal, preserving immutable historical
manifest/part hashes and full logical union. Specs/receipts losslesszlib9, FULL/WAL
transactional receipts/reservations, original state/chain semantics. New journal
layouts table holds DELTAONLY; never use it alone as the historical exclusion set.
Backups depend on their explicit checksummed base files. No migration/compaction/
deletion of old records, no lowering the16GiBfloor. Admission requires600MiB
available abovefloor, plus a prospective estimate fitting600MiB. The first storage
plan is retained even when admission fails; recheck and save a new readiness plan
before registration/launch. Do not shrink search based on observed outcomes.

Before registration: verify all378M13 completion hashes; discarded rehearsal and
intact controls, exact1248fixture birth/RNG replay, allocation boundary/flood/empty/
false-no-path tests, common global operator/all8blocks, baseline selector/RNG
compatibility, exact bank/founder provenance, equal evaluation counts, primary
role/gates, full zero-round freeze/searchaudit/final/ALL-native audit on discarded
fixtures. Preserve failed attempts. All generated fixture layouts excluded.
Preparation outputs are software evidence, not scientific discoveries. The first
zero-round software test correctly hit the full600MiB admission reserve; its
log is preserved. That fixture-only zero-round test then used32MiB storage with
the SAME16GiBfreefloor and passed the full pipeline. The64-round scientific
600MiB reserve is unchanged.

Durable workflow: push source/config/founders/protocol registration BEFOREscience;
search; freeze exactchoices/ancestry/finalstates and COMMIT/PUSH BEFOREfresh1680input
confirmation; fullsearch audit; final; analysis; ALL-native finalaudit. Search audit
regenerates corpora/tasks, independently regrades ALLrows, replaysALLselection/
mutation/RNG/births/freeze, native hash samples1/32assessment and1/256train. Final
replaysALLcandidate outputs/grades/summary plusBFS/A*/bitwave, separate intact flat/
M1controls. SharedproductionVM/reproduction andindependentgrader,notsecondfullVM.

At completion report exact endpoints, root/parent/protected/frozen comparisons,
ordinary length strata, no-path outcomes, actual survival/breeding allocations,
ancestry, logical/physical cost, limits and any failures. Verified SQLite-API
backups underlocks only within bounds; preserveoriginals if backup cannot fit.
Export ALLinitial/search/final generated/rejected/unqueried layouts via verified
reference+delta manifest. Seal compact evidence/report andcommit/push,never raw
journals. No furtherphase beyondM14 authorized by this protocol.
