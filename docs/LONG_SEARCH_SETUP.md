V12Z implementation and preflight now pass; see `docs/FAMILY_EVOLUTION_PROGRESS.md`
and `docs/FAMILY_EVOLUTION_V12Z.md` for current status. The original preparation
description below records the plan. Sexual75minute comparison remains gated.

# Longer evolution setup after V12Y

Two local 75-minute comparison specifications are prepared. They are not
registered, scheduled, running, or launch-ready experiments. The family retention
operator is implemented and unit-tested; integration into an end-to-end runner,
fresh software fixtures, timing calibration and exact replay preflight remain.
Those steps must precede scientific validation/training. This explicit status
prevents a planning file from being mistaken for an executed experiment.

## First priority: mutation with preserved related variation

`results/long_search_setup/mutation_diversity_75m.json`

Carry/fresh × three replicates × ordinary mutation, family-reserve mutation,
resampling and frozen controls: 24 conditions of 96 genomes. All use the same
starting pools, native local runtime, 256-gene ceiling, fitness, mutation rate
and evaluation schedule. Fresh founders remain wholly random, with no historical
solver code. Carried conditions protect the same 20 exact random-origin anchors.

Every evolving arm retains 44 and produces 52 offspring per generation. Mutation
arms produce seven random immigrants and 45 one-edit children. The common44
retention count leaves room for a family reserve while keeping20anchors intact;
it changes the shared baseline from X's24/72, so causal comparisons are within
this new study, not against old scores. Resampling draws52 new random genomes.

The only contrast between the two mutation arms is survivor selection.
Both first retain protected anchors and four additional merit-selected members.
The family arm can reserve up to20slots for five ancestry families with up to
four additional genotype-distinct variants each. Family choice uses best current
training rank. Within a family, select farthest-first by inherited-locus distance;
fitness rank breaks ties. Fill remaining slots using common behavior diversity
and rank. This is a hypothesis that related variation needs time to diverge, not
a claim that genetic distance itself improves solving.

The selector is in `maze_evolution/family_reservoir.py`. Its tests check exact
capacity, protected identities, no input/genome mutation, actual genotype
distinctness, bounded family reservations and deterministic behavior.
Full integration must also replay parent selection, concrete mutations,
gene identities, lineage labels and every RNG/checkpoint state.

Primary success concerns new complete prefix>=4pairs and real alternative-cycle
routing on new contexts, with retained paired/corridor/ordinary skills and no
increase in false no-path claims. Validation and untouched final must both pass
the frozen gate in at least two of three replicates of an origin. Family diversity,
mutation depth and genome complexity are diagnostic metrics, not substitutes.

This asexual experiment does not need a sexual activation gate. It does need a
successful software/timing preflight. Minimum coverage is96matchedgenerations;
75minutes is a hard search wall allowance, not a promise of a particular number
of generations. Reserve time for completing a matched round and saving state.
Calibration, final confirmation and independent audit are separately accounted.

## Second priority: crossover after activation

`results/long_search_setup/family_crossover_75m.json`

Carry/fresh × three replicates × immediate-gate-linked, unlinked, matched
gate-sham, mutation, resampling and frozen: 36conditions of96. Use a common
related-variation policy and identical bounded donor/segment opportunities.
The proposed larger common pool includes32-instruction segments.

Do not launch this 75-minute comparison merely because immediate linkage is less
restrictive. First run a NEW short activation pilot with fresh seeds and layout
exclusions. Require at least10%of scheduled matings to retain two changed donor
instructions after mutation, in at least8generations and2/3replicates for all
three sexual policies in BOTHorigins. Y's pre-mutation static probabilities are
not that test. Preserve failed proposals and exact parent/donor ancestry.

## Preparation and review

Inspect the two machine-readable configurations and run:

```bash
.venv/bin/python tools/prepare_long_search.py check
.venv/bin/python -m pytest -q tests/test_family_reservoir.py
```

The checker reports outstanding readiness steps rather than launching compute.
Neither job auto-starts or auto-extends; no automation or remote service is used.
All later fixtures and both future runs must extend the255356-layout exclusion
set, including unqueried symmetries. Freeze exact corpus sizes, grammar, timing-only
sizing rule and source before generating scientific selection data.

The user has authorized preparing longer evolution work. No new permission is
needed for routine implementation or preflight; remaining gates are scientific
and technical checks, not a request to approve the same work again.
