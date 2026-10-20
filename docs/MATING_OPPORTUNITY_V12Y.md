# V12Y: preregistered fixed-parent crossover opportunity assay

Authorized follow-up to X-R1. This is a static design study on inspected training
histories, not new independent evidence of solver efficacy. Zero organism calls,
zero new mazes, no genomes edited or promoted, no old populations resumed.
Preserve all 6,667 prior completion entries and the 255,356-layout exclusion set.
Seed 2026102003. Freeze/push source, protocol and exact input hashes before execution.

## Complete historical opportunities and controls

Reconstruct all 18,432 scheduled mating births from the valid X-R1 32 generations:
carry/fresh × three replicates × linked/unlinked/sham × 1,024 births. Include
failed proposals. Preserve the actual recipient and recorded eight-draw donor
shortlist. Deduplicate repeated donor identities within each shortlist. Add eight
distinct, uniform, fitness-blind other population donors, excluding the recipient
and original shortlist, using a deterministic event-specific seed.

Four views: the actual historically proposed donor (or none), recorded shortlist,
eight additional donors, and their union. All rules receive the exact same pairs.
For each cap and view, virtual donor choice is a fixed hash-random ordering among
donors with any differing structural segment at that cap. No linkage eligibility
or fitness enters this virtual choice. The actual-donor view has at most one
member. Alternative views are structural design probes, not a replay of X's
complementarity-ranked donor policy.

Also probe all 36 saved arms, including mutation/resampling/frozen, at generations
0/8/16/24/32. For each snapshot choose 16 parents uniformly without replacement
and eight distinct uniform donors per parent, excluding the parent: 2,880 probes.
All snapshot samples are frozen by seed, not selected for performance. Record
population family composition at all 180 snapshots. A family is an initial
founder/random-immigrant ancestry root; known d07/d12 share the explicit known_U_d07
root. Recombinants have multiple roots with fractional membership. Separate
protected identities from mutable members. Effective family counts are inverse
concentration descriptions, not functional diversity or independent discoveries.
The final snapshot includes unevaluated newborns and is static only.

## Factorial comparison

Common structural pool: inherited gene identities, two shared boundary anchors,
consistent ordering of all shared loci, equal-length exchange, no duplicate child
identity, and at least one changed instruction row. No register renaming, inferred
homology from matching rows or equal-interface constraint. Same rules as X except
the explicit length factor. Compare common length pools 2/4/8/16 and 2/4/8/16/32.

Three biological/structural rules:
- Full transitive STORE value/gate closure from X.
- Immediate STORE gate-writer linkage: include the STORE and every possible
  reaching writer of its scratch gate, retaining conditional predecessors and
  stopping at an unconditional writer. No recursion into writers' reads and no
  STORE value dependency expansion. An unconditional STORE forms a singleton.
- Unlinked exchange.

Both parents contribute groups, including a STORE removed in one parent.
Every intersected group must fit wholly within the union of transferred loci.
No hardcoded historical circuit or functionally certified module is assumed.
For each protected rule include a sham that picks a random subset of the common
segments with exactly that rule's eligible cardinality, then selects uniformly.
Thus there are five rule/control policies. Full closure, gate linkage and unlinked
share the same parent pair, common length and ticket. The paired shams match
acceptance feasibility on that pair/length, not all evolving marginal outcomes.

Virtual length is uniform among the common available lengths; use shared shuffle
and ticket across the five policies. Save selected intervals and actual row-change
counts. Also calculate the exact probability of a >=2-row change under uniform
length/segment choice, including sham randomness. Count all scheduled opportunities
in denominators, including no donors. These are PRE-MUTATION potential transfers,
not the actual inherited-transfer endpoint of an evolutionary pilot.

Save complete segment pools once per unique genotype+inherited-identity pair,
all virtual proposals, all family snapshots, expected/realized counts and any
available multi-change opportunity. Report unique genotype pairs alongside
opportunity-weighted counts; repeated parents and poses are correlated.

## Frozen design decision

For the historical union view, average expected pre-mutation multi-change fractions
equally over the three prior sexual-arm populations within each origin/replicate.
A cap qualifies for a new activation pilot only if gate, gate-sham and unlinked
each reach 12% expectation in at least two of three replicates in BOTH origins.
Prefer 16 if both caps qualify. The 12% design screen supplies a small margin over
the later 10% actual post-mutation criterion; it is not a replacement of that gate.
If neither qualifies, design a shared related-lineage diversity mechanism before
another pilot. Do not declare recombination or random-origin evolution impossible.
Neither outcome authorizes a long efficacy run by itself.

Prepare a concrete longer-run configuration after this assay, reflecting its
findings. Long crossover efficacy runs require a separately preregistered fresh
activation pilot that passes the original retained-transfer/active-generation/
replicate criteria. Long mutation/diversity search is a separate research option,
not a way to call inactive crossover successful. The user's request for more
evolutionary time remains central; preserve fresh origins, protected capabilities,
equal evaluation budgets, checkpoints, isolated validation and untouched finals.

## Bounds and audit

Main wall cap 900s, 400,000 unique homology-aware pairs, 3 GiB RSS, 3 GiB outputs.
Audit wall allowance 1,800s reported separately. Stop and preserve partial artifacts
if a bound fails; no silent extension. All thresholds and samples fixed beforehand.
Independent audit uses backwards dependency scans and set-based interval checks,
not production forward maps/bit masks. Reconstruct every queried pair, every
selected virtual interval and aggregate, final populations/gene maps and family
snapshots. Verify all prior/source/input hashes. Static randomness and aggregation
are replayed; their exact expectations are also unit-tested. No VM warmups or
hidden organism evaluations occur. Do not claim independent selection-policy
implementation from replay alone.
