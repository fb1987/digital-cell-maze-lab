# Persistent random-origin discovery campaign

Prepared October 20, 2026. **Not launched.** Scientific milestone: 10,000 replacement
rounds in each of three continued populations. Software rehearsals are discarded.
Configuration and implementation are frozen in
`results/deep_campaign_setup/registration.json` after preparation checks.

## Scientific judgment

A deeper discovery campaign is justified. We have acquired short routing abilities
in particular random-origin lineages, retained complementary specialists, and a
very small number of longer-prefix successes. We do not have evidence that the
present representation and selection process will converge on general solving.
Neither the negative short pilots nor these successes settle that question.

B's strongest primary was an unchanged historical anchor: 416/800 goal-switch
pairs and 44/384 ordinary reachable inputs. A retained secondary anchor completed
46 prefix-four and 30 prefix-eight pairs. These are reasons to preserve multiple
lineages, not new B gains. Most ordinary mazes still fail; every selected primary
failed all disconnected cases. We have no established multirange advantage or
competitive speedup. Output selectivity and transfer across geometry remain major
barriers. Increasing time cannot substitute for correcting an unsuitable search
space, but the current evidence does not establish that the space is unsuitable.

The new user instruction deliberately changes the research strategy: sustained
discovery replaces repeated short controlled comparisons. This is a NEW phase
forking B's saved states, not an extension of B's closed budget or a retrospective
change to its passing gate. We will be able to establish a discovered genome's
capability and ancestry. Without concurrent matched search controls we will have
weaker evidence about which campaign policy caused improvement.

The literature supports the strategy, with important differences:

* [Lenski et al., 2003](https://cse.msu.edu/~ofria/pubs/2003LenskiEtAl.pdf)
  used 3,600 digital organisms and 100,000 updates, equivalent to 15,873
  **ancestral replication-time generations**. They began with a handwritten
  self-replicator and rewarded simpler functions. Their ancestral-time measure
  is not our replacement-round count or a count of genotype-changing births.
  It is evidence for sustained search and intermediate rewards, not a 10,000-round
  success threshold for this project.
* [POET](https://arxiv.org/abs/1901.01753) combines environment generation,
  solution optimization and transfer. It supports progressively challenging
  environments as a research direction; it does not demonstrate that merely
  running a fixed maze curriculum longer will succeed.
* [MAP-Elites](https://arxiv.org/abs/1504.04909) preserves good solutions in
  distinct behavioral niches. Our archive is a simpler normalized successful-case
  coverage archive inspired by quality-diversity, **not canonical MAP-Elites**.
  Its usefulness here remains experimental.

## Frozen phase-one design

| Component | Decision |
|---|---|
| Founders | Exact B `carry/0/current`, `carry/1/current`, `carry/2/current` populations at B round 30 |
| Preserved state | All 96 identities/genomes per island, RNG state, locus identities, family labels and 20 protected anchors |
| Live population | Three islands of 96, 288 total; no inter-island migration |
| Reproduction | 44 survivors, 52 births per island per round: seven random immigrants and 45 single-edit mutants |
| Parent selection | Existing lexicase pressure; 10% uniform parent sampling permits neutral exploration |
| Runtime | Existing local V6 pulse/exposure runtime, exposure 7, at most 256 genes and 256 normal ticks |
| Work limits per inference | 4,096 reads and 32,768 dispatches per substrate site; exposure checks also charged |
| Diversity | 20 protected historical anchors; distinct-output survivor preference; at most 32 archived genomes per island |
| Assessment | Every live genome, prior archive and frozen protected references on a common new panel at round 0 and every 500 |
| Archive selection | Four aggregate elites, then marginal successful-case coverage normalized within each stratum |
| Reintroduction | Up to four archived nonlive genomes occupy survivor slots after an assessment; total remains 96 |
| Recombination | Off in this phase; preserved locus identities support a later, separately documented test |
| Milestone | 10,000 rounds; preserve history and freeze candidates before generating confirmation |

All three populations are random-origin descendants, not fresh random founders.
They share historical anchors and ancestry; three RNG streams are not three
independent origins. Initial population contents and RNGs are exact copies.
Campaign identity namespaces and the round counter are new; the origin records
retain their B source generation and digest.

At the milestone the campaign will have produced 1,560,000 births if uninterrupted
by a resource ceiling: 210,000 random immigrants and 1,350,000 mutated offspring.
That is not 10,000 mutation steps in each surviving lineage. Concrete parent,
mutation and locus records permit actual lineage depths to be reconstructed.

The local topology follows the current evidence and avoids paying for unsupported
nonlocal reads. A later phase can fork preserved states to test nonlocal signalling,
capacity changes or recombination. None enters this phase silently.

## Challenges, selection and evidence boundaries

Each training round supplies two matched structured contexts, each with both goal
choices, pruned corridor controls and disconnected controls: 12 queried inputs per
island. Every fourth round adds six ordinary 9×9 inputs: two perfect, two random
reachable and two disconnected bases with nonisolated endpoints. All eight poses
are generated and excluded from future independent corpora even if only one is
queried.

One context practices the previous prefix level; the other targets the island's
frontier. Prefix levels are 1, 2, 4 and 8, with prefix zero used as initial easy
practice. Every seventh round probes the next level. Every fifth round includes
an extra junction or a genuine alternative-route cycle. Schedule periods and
pose rotations are separated to avoid permanently coupling harder tasks to one
orientation. Straight and turning forks are included. Geometry is the existing
19×19 structured grammar, not a claim of unrestricted topology.

The 500-round assessment has six independent structured contexts, five prefix
levels, all three graph families where the geometry supports them, and 64 ordinary
bases. It queries 648 inputs per candidate from 2,912 generated inputs. Whole
layouts and every generated pose are excluded later. Variants and poses are
correlated; the independent experimental units are contexts/base mazes.

All genomes are assessed, rather than only two validation nominees. Old archive
members and references are rescored on that SAME new panel before selection.
Correct paired routing is one feature, so a one-goal success is not counted as
a complete pair. Corridor, ordinary and disconnected successes have their own
strata; numerous corridor inputs cannot dominate the archive by sheer count.
Genetic distance alone is not a fitness reward.

An island advances only when one candidate completes at least 80% of frontier
pairs in **each** graph family on two consecutive assessments. A union of
specialists cannot trigger promotion. Failure to advance does not stop evolution.
Older skills continue to receive training and protected representation.

Every intermediate assessment is development/selection data. None is an untouched
final test. The three islands share common contexts; they may query different
prefixes after their frontiers diverge. This is intentionally not an equal-budget
causal comparison between policies.

All 279,824 layouts through B and every setup/rehearsal layout are excluded.
The final exact setup total is recorded in `exclusions.json.gz` and the readiness
report. Reused historical final cases are never candidate training inputs.
The generator's restricted geometry and construction biases remain limitations;
changing clutter alone is not novel-topology transfer.

## Resources and execution

The user dedicated the laptop to research. The chosen setting uses all ten CPU
workers on the Apple M4 (four performance and six efficiency cores, 16 GiB RAM).
Each worker executes serial native kernels. No cloud, model API, model download
or GPU conversion is involved.

* Session wall allowance: 12 hours, then checkpoint and resume the same history.
* Process-tree RSS guard: 12 GiB; storage guard: 20 GiB; retain at least 16 GiB free
  disk. These are sampled stop-dispatch thresholds, not operating-system quotas.
  Already submitted bounded tasks finish before the session closes.
* Campaign charged caps: 100 million physical calls and 10^15 work units.
  Every submission reserves its entire bounded call/work allowance before launch.
  Completed receipts replace the work reservation with measured work.
* Normal candidate limits, genome capacity, live population and archive bounds
  remain fixed. Increasing generations does not increase an organism's capacity.

The 5.2-hour estimate in the proposed description used Z's mixed training average,
including cheaper fresh/resampling/frozen conditions. B's three carried mutation
populations imply approximately 9.8 serial candidate-inference hours for 10,000
rounds at B's 12-input batch size, before assessments and other overhead.

Actual setup benchmarking found identical rasters and reproduction at one, four
and ten workers. Warm medians for the same 4,284-call training fixture were
3.40 s, 0.94 s and 0.56 s respectively. Ten workers were fastest, with a measured
sixfold speedup for that inference pipeline, not an assumed tenfold speedup.
Summed candidate wall time under contention is not CPU time; both are recorded.

The broad rehearsal assessed 154,224 physical candidate responses in 27.96 s,
including grading, archive decisions and journal commit, but using prebuilt inputs.
A separate 16-round rehearsal including new input construction, reproduction and
journaling took 19.88 s in its generation loops, median 1.20 s per round.
Preparation, verification and archive packaging brought that rehearsal to 31.43 s.
Process memory observed during broad assessment was approximately 2.1 GiB.

The short rehearsal extrapolates to approximately 3.5 hours of training loop time
plus assessments. **Plan for 4–8 hours initially**, with the 12-hour resumable
session as a ceiling, not a promised completion time. Costs can increase as
organisms change and the exclusion set grows. Reforecast from actual execution at
each 500-round checkpoint. Storage appears compatible with the 20 GiB guard;
growth is measured, never assumed to remain linear.

After preparation has been committed/pushed, launch locally from the repository:

```sh
/usr/bin/caffeinate -i -s .venv/bin/python -m maze_evolution.deep_campaign run
```

Use the same command to resume. It will not restart founders. For a limited first
session, `--through-round 100` stops after round 100 without changing the frozen
10,000-round campaign milestone. Status can be read while the writer is active:

```sh
.venv/bin/python -m maze_evolution.deep_campaign status
```

The journal lives at `runs/deep_campaign_v1/campaign.sqlite`, excluded from Git.
It is a scientific record, not a disposable cache. FULL/WAL transactions and a
single-writer lock protect against interrupted writes. Inputs are committed before
inference; completed evaluation batches survive resume. Population, RNG, ancestry
events and a receipt hash chain commit atomically. Every hundredth population/RNG
state, every assessment and the latest state are kept; intermediate full states
can be reconstructed from retained birth/selection events and rasters.

SIGINT/SIGTERM stop dispatching and drain bounded in-flight tasks. After a hard
crash, an unreceipted task may need reevaluation. Its previous worst-case resource
reservation remains charged, and a retry increments the uncertain-attempt count.
Exact CPU consumption of a killed task is unknown; it is not silently reported
as zero. Completed tasks are not rerun. A broken receipt/hash or changed frozen
source/configuration fails closed.

This provides crash recovery on the local disk, not protection from disk loss.
At session boundaries, use SQLite's backup API for a portable copy before moving
or archiving the journal; do not copy a live database while omitting its WAL.
Do not prune raw observations or ancestry to fit storage: stop at the guard and
make a documented storage/phase decision.

## Auditing, milestone interpretation and subsequent confirmation

Every saved candidate raster is independently graded at evaluation time. Every
birth records its exact mutation; mutation replay is checked on creation.
The command below verifies the sealed journal and replays every selection,
mutation, population and RNG transition:

```sh
.venv/bin/python -m maze_evolution.deep_campaign audit
```

It does **not** rerun all candidate inference. We explicitly reduce the repeated
full-inference auditing burden during discovery. The same native kernel is used
for candidate inference, with a separate raster grader; there is no independent
second VM implementation.

At round 10,000 the runner performs the scheduled broad assessment, writes
`milestone_choices.json.gz`, then stops. The packet selects one aggregate primary
and up to three complementary coverage selections per island and preserves frozen
references. It must be committed/pushed before an independent confirmation corpus
is generated. Confirmation is a subsequent bounded protocol, not an automatic
unchecked continuation in this runner.

The confirmation protocol should measure:

1. Acquired capability: paired shortest-output gains against initial references
   on the same untouched cases, with exact ancestry replay and context-level
   uncertainty. Specialist successes count as specialist discoveries.
2. Broad progress: ordinary trees, random reachable cyclic grids and disconnected
   cases separately, on 9×9 plus new 17×17 and 25×25 domains; include new structured
   geometries, not only new clutter. Freeze exact domain counts and seeds before
   generation. A primary and its complement are separate organisms, not an oracle
   ensemble that chooses a successful answer after inspection.
3. General-solver evidence: near-complete correctness across those declared domains,
   explicit legal-path versus shortest-path metrics, reliable disconnection
   handling and algorithmic inspection. A finite holdout cannot prove unrestricted
   maze solving.

Any speed claim requires completed correct outputs, warm repeated end-to-end
timings and comparison with compiled BFS, A* and bit-wavefront, with input/output
and total work included. Incorrect spreading is not a faster solver.
No performance advantage is claimed merely for surviving 10,000 rounds.

At each development assessment inspect retention, new successful-case patterns,
ordinary transfer, mutation acceptance, diversity and actual cost. Plateauing
does not trigger an unrecorded fitness change. If the population repeatedly
produces the same failures, preserve this phase and propose a new phase that
changes a specific bottleneck. Sexual recombination is an option if we can first
identify transferable complementary rule modules; whole-genome mating could
otherwise destroy coadapted regulation. Ten thousand rounds is an initial
milestone within a preservable history, not a guarantee or an expiry date.
