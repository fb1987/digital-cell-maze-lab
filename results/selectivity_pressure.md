# V13B: controlled selective-output pressure

Status: search in progress. This report will be completed after untouched final
confirmation and the independent replay audit. No final result is available yet.

## Registered comparison

Twenty-four conditions compare current versus selective partial fitness, random
resampling and unchanged founders, separately for continued and fresh random
origins, with three matched replicates and 96 organisms each. Continued states
fork the exact V12Z current-mutation populations and RNG at generation 128;
original states remain intact. Their 20 historical random-origin anchors remain
protected. Fresh pools protect at most three of their own common initial
validation selections. No known solver enters a lineage.

Only the partial fitness supplied to the common ranking and lexicase changes.
The selective score explicitly distinguishes one-, two- and four-cell excess
stubs that current fitness ties. An output containing the full route plus excess
cells scores above an incomplete route within this shaping score, but remains
invalid and below every exact shortest output. This is a deliberate path-retention
tradeoff; the evaluator never cleans the raster or supplies an oracle to inference.
Validation archives use the same real-success ordering and original partial
score in both arms. Capacity, local runtime, single-edit mutation, survivor count
and training schedule remain fixed across the contrast.

Main search is capped at 720 candidate seconds, 900 wall seconds and 128 matched
generations. It stops before a round that cannot safely fit. A failed efficacy
gate closes this pilot; it never authorizes an automatic longer run.

## Data and independence

Training uses 12 inputs per round, matching source-at-junction and upstream
prefix-one/two tasks with paired goals, corridors and disconnected controls.
Every 16 rounds covers all eight poses at both upstream distances. Validation
uses six independently seeded contexts and 340 queried inputs. Its four paired
poses are a timing tradeoff fixed before registration. All 1,440 generated
validation inputs, including unqueried poses, are excluded later.

Final confirmation uses 12 new structured contexts, eight poses, prefixes
0/1/2/4/8, forks, second junctions, genuine alternative cycles, and a separate
ordinary-maze sample. Each model receives 5,312 inputs: 800 two-goal pairs,
1,600 corridors, 384 ordinary reachable mazes and 1,728 disconnected inputs.
The contexts are seeded draws; their poses, prefixes and graph variants correlate.
These are new layouts in the existing grammar, not novel-topology transfer.
All selected genomes are committed and pushed before final generation.

## Preflight and provenance

Registration: `2f7a379`, pushed before scientific validation or training.
Seeds: 2026102007; fixture/schedule seeds 1454/1455. Local Apple M4; exact Python
and dependency versions are in `selectivity_pressure/preregistration.json`.

The original conservative timing estimate failed: 660 validation queries and
twice the slowest-pool rate projected 1,621.46 seconds for initial screening plus
16 generations. Its source and profile remain in `preflight_attempt0`. Before
registration, validation was reduced to 340 queries and the balanced-pool estimate
changed to 1.5 times the sum of the six measured rates. The revised projection
was 569.00 seconds, without new candidate calls or fitness-based model choices.
The final test retains all eight poses.

Synthetic checks and a separate known-solver output-store repair control pass.
The known control checks the existing instruction set and scoring, not whether
random-origin populations can discover suppression. The discarded three-round
rehearsal replays 82,944 responses and 1,620 mutations exactly. Calibration plus
rehearsal cost 99.28 candidate seconds under the separate 180-second cap; no
rehearsal population continues into search.
