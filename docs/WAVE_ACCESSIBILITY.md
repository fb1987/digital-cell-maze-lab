# M2: fixed-parent wave mutation accessibility

This new study is explicitly informed by completed M1. It does not extend M1 or
use its inspected cases for selection. Random-origin discovery remains central.
The question is whether generic nearby mutations can improve native output
selectivity while retaining acquired skills. This is a static neighborhood assay,
not an evolutionary-policy efficacy comparison or a general-solver benchmark.

## Frozen design

Two exact M1 modular anchors, chosen for previously documented mechanisms:
- accumulating wave: modular/0/familiar/mutation/g24/b39, random founder79;
- delayed wave: modular/1/broad/mutation/g84/b11, random immigrant g31/b6.
Full identities/genomes and source packets are preserved in anchors.json.
These are two deliberately chosen lineages, not random independent replicates.

For each anchor independently draw 4,096 one-opportunity and 4,096 two-opportunity
variants using unchanged M1's generic seven-opportunity mutation operator. Every
two-opportunity trial starts from its anchor and applies two successive random
mutations without evaluating/selecting the intermediate. Retain intermediate
genomes, events, initial/final RNG, duplicates and no-ops. No targeted edit,
solver injection, crossover or architecture change. A shared pool of 4,096 fresh
random M1 genomes supplies a reference. All 20,480 draw slots receive identical
screening queries, with exact genotype deduplication disclosed. One/two edits are
opportunities, not necessarily two retained functional changes. The two-step
factor is not a selected evolutionary trajectory or proof of a fitness valley.

Screening seed2026102102: all six existing structured SPECS, prefixes0/1/2/4/8,
paired poses0/4, corridor pose0, disconnected prefix0 pose0, plus12 ordinary bases
in perfect11/random9/disconnected9, two poses each. All unqueried variants/poses
are excluded. Screening is DEVELOPMENT data; ordinary endpoints/generator biases
and the existing small grammar are retained and disclosed. No difficulty filter.
Pool seed2026102101. Discarded software/profile fixture seed202610210101.

For each anchor × depth nominate two from the SAME draws plus unchanged anchor:
1. Original M1 equal-family aggregate rank (correct-minus-false, valid-minus-false,
   existing branch-penalized partial), unconstrained.
2. Retention/selectivity: require every anchor-correct query remain correct and
   no new false no-path case; then maximize complete pairs, ordinary bases correct
   in both poses, full-route-covered emitted fork/corridor query count, mean
   full-route precision, then original rank. Identity ascending breaks ties.
   Full-route precision is zero unless all oracle-route pixels are emitted;
   otherwise route-pixel count / total output-pixel count. It applies ONLY to
   unique-route fork/corridor tasks, never alternate-route cyclic/random cases.
   An empty or fragmentary mask cannot gain this precision reward. Diagnostic
   route coverage is fitness-side information, never supplied to the organism.
The anchor fallback ensures eligibility. This rule is deliberately stricter than
M1 retention and changes selection only, not the common candidate pool. Random
pool nominees: original rank plus retention/selectivity relative to each anchor
(with anchor fallback). Report any unchanged fallback transparently. At most11
nominee aliases; not11 independent discoveries. Report all sampled neighborhood
frequencies, genotype changes, retained outputs and new/lost capabilities.

## Confirmation and decision

Freeze and commit/push exact choices, entire pool/event/RNG records and screening
summary BEFORE generating confirmation seed2026102103. Use unchanged C1/M1
1,424-input confirmation builder:12 structured contexts,400 pairs,200 corridors,
40 structured disconnected,32 bases ×2poses in perfect11/15, random9/15,
disconnected9/15. Assess nominees, both anchors, two-opportunity immediate
intermediates, and separately labelled intact flat/modular controls. Baselines
BFS/A*/bitwave are external controls. No reselection from final data.

Acquisition requires a changed mutant with >=8 new complete pairs across>=2
contexts, >=90% retention of anchor paired/corridor AND ordinary-base successes,
and no increase in false no-path. Empty retention denominators are N/A.
Broad flag additionally >=4 new ordinary bases, including perfect and random.
Report gains/losses relative to exact anchor and immediate intermediate, and all
prefix/graph/domain strata. Partial coverage/precision gains alone never count
as correct path acquisition. A worthwhile follow-on evolutionary design requires
confirmed acquisition; broad claims require the broad flag. No automatic long
run follows, no negative result closes random-origin discovery. Search neighbors
are correlated; no population-policy causality or latency/speedup claim.

## Bounds, checks and preservation

Unchanged M1 runtime:8 persistent uint16 channels,<=256 instructions/ticks,
4096 reads and32768 dispatches/site, synchronous radius-one sensing; no cleanup.
10 local workers;90min/session;12GiB tree RSS;8GiB new phase storage including
nested backups;16GiB disk free floor. Screen<=12M charged calls,10^15 work;
confirmation separately<=100K calls,10^14 work. SQLite FULL/WAL single writer,
receipts/conservative reservations, checkpoint on a guard; never bypass guards.
All991,291 prior layouts plus discarded fixtures excluded. Prior sealed files
verified, preserved unchanged. Registration and source pushed before science.

Preflight: complete control correctness on discarded panel, random-only timing,
mutation/RNG reconstruction, genotype dedup/alias completeness, rank ordering
for correct/partial/empty/flooded masks and retention gates. No scientific anchor
performance is inspected before registration. Audit regenerates pool/events/RNG
and corpora, task specs and nomination decisions; independently grades every
physical response, native replay fixed hash1/64 screen and all confirmation
responses, all conventional baselines. Shared mutation/runtime code replay is
not a second independent VM. Audit additional, separately charged/reported.
Preserve full journals and verified SQLite backups within bounds; seal completion.
