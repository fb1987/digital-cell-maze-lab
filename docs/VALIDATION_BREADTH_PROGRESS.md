# V12I completed handoff — October 19, 2026

Current checkpoint: **V12I is complete and audited**. Read
`results/validation_breadth.md` and this handoff first. Do not repeat I, extend
its closed cap, resume G/H, train or reselect on inspected I final cases.
The junction-distance follow-up is a proposal only, not launched.

The performance-blind fixed pool contains all G initial validation-screened
individuals plus every later validation nominee within each original condition:
30 pools, 3,632 identity memberships, 3,612 genotype memberships, 1,878 physical
models. No genome editing, breeding or known-solver injection. Preserved all
original populations/RNG, protected anchors, aliases and nomination generations.
Protocol/pool pushed in 5a00489; every choice and validation record pushed in
e53bfa1 BEFORE final generation. Seed2026101904; fixtures1234.

Narrow4contexts×4poses versus broad16×1 per draw, both128 inputs/genotype:
48 branched pairs +32 corridors. Three validation draws shared across historical
replicates. Exact stratum/family/side/pose counts match. Each arm240,384 physical
calls /462,336 logical calls. Actual time192.97s narrow,197.99s broad; equal
allowances do not imply identical work. Both use the same pair-first rank and
digest tie-break. Twelve of30 choices differ;28 unique narrow,29 broad,40 total.

Final:64 independent contexts (16 per stratum),25×25,8 poses,2 goals and matched
fork/two-junction/real alternative-cycle graphs. Source prefixes1–3/4–8 cross
goal tails3–4/5–9.3,072 branched inputs/1,536 pairs,1,024 corridors,128 no-path
inputs/model. Variants/poses correlated; contexts are the independent units.
Cycles join opposite goal arms; the I grammar differs from H. No direct G/H/I
score change can be attributed solely to a prefix, genome or selector change.

Complete pairs across3 replicates (denominator4,608 per selector):
carry/local Current258→328, Branch104→212;
carry/evolved Current432→492, Branch610→606;
fresh/local Current0→0, Branch0→12, resampling0→0;
fresh/evolved Current0→0, Branch56→56, resampling0→80.
Carry/local Branch replicates narrow[88,2,14], broad[184,12,16]: all raw counts
improve, but onlyrep1 passes full gate. Carry/evolved Currentrep0 also passes;
all cohorts fail the required2/3. Context-conditional bootstrap interval for
local Branch gain approximately75–143 pairs, but excludes lineage/draw
uncertainty. Corridor and rare longer-prefix skills can be lost by replacement.

Highest-scoring frozen I selection on final is NARROW
fork/carry/evolved/branch/evolution/0/i5140,254genes,birth72:
416/1,536 pairs =256fork +80two-junction +80cycle. All32 short-prefix contexts
work as forks in all8poses. The10 contexts with sourceprefix1 work in all8poses
under all3graphs. Paired route lengths reach11 onforks and10 oncycles (example
10/10 shortest vs16/16 alternatives). BROAD i7406,256genes,birth103,gives412
pairs (four fewer cycle poses), corridor1024 vs1008. G ancestry29/52 steps from
protected random-origin E foundation_pair_paired/evolved/fresh/evolution/0/i108890.
These are preserved G nominees newly evaluated in I, not I evolutionary gains
or replacements of earlier primary evidence. No new mechanism ablations.

Broad local Currentrep1 i5138,256genes,birth72, completes72pairs: three5/5-edge
contexts, all8poses and all3graphs, including24cyclepairs. Local correctness
therefore exists too; no causal multirange advantage. Fresh evolved Branchi2653,
110genes,birth37, selected by both, gives56forkpairs:7 short contexts all8poses.
Fresh local Broadi8001,128genes,birth112,gives12forkpairs on4contexts, noneall8;
that replicate loses corridor1024→158. Broad evolved resampling picks the saved
unmutated68-gene i4469:80forkpairs,10contexts all8poses,1024corridors,0extra-junction
pairs. Preserve this control; no consistent evolution/capacity advantage.

21/40 random-origin models complete a pair. None completes a5–8-edge prefix
pair (24 independent contexts,576 paired opportunities/model). All fail combined
long-prefix/long-tail. Only two physical models complete four-edge-prefix pairs:
narrow evolved/6251d8a39c24aa6e3034 gives16forkpairs on two7/7-edge contexts(all8);
broad local/dea7d3831d8e42746fda, inherited E Currenti114696 born1365,gives onepose
of one7/7 context across all3graphs, including13/13 alternative cycle,3pairs total.
The narrow longer-prefix variant is lost by its broad replacement. Distance is
an association across geometries, not an isolated causal diagnosis.

All selected random-origin models0/128no-path; no false reachable no-path claims.
One narrow fresh/local Current output is legal but non-shortest. BFS/A*/bit-wave/
intact VM solve4096/4096reachable and128/128disconnected. No I latency benchmark;
general solving, causal multirange benefit and speedup remain unestablished.

Main inference532.99s/720s cap,658,176calls,312,103,773,228work; wall560.36s,
680.83MiBpeakRSS. Calibration separately8152calls,6.10candidate seconds.
Audit PASSES first attempt:582.15s wall,782.20MiBRSS,666,328exactcandidate replays,
679,000 independently graded rasters,12,672baseline replays,all60 choices;
153source/16input/115pool-source hashes and481 priorG/H completion entries.
No frozen-source repair or post-registration protocol deviation. All output
masks, scores, raw counters, ancestry, selection aliases and generation manifests
are preserved. Ten new+21 related tests pass;195collected,NOT a fresh full suite.

Exclude ALL144,120 whole layouts through I:138,712throughH +192rejected preflight
+192corrected fixtures +2400validation(all poses) +2624final. The rejected fixture
construction had chorded longer rasters and received ZERO candidate calls;
correction occurred before calibration/registration. The helper
validation_breadth_data.exclusions() returns throughH plus rejected preflight;
future code must ALSO add validation_breadth_fixtures/mazes.json.gz,
validation_breadth/validation/mazes.json.gz and
validation_breadth/confirmation/mazes.json.gz to reach144,120.

Next proposal only: freeze an explicitly I-informed panel (both selectors,
longer-prefix exceptions, fresh controls,68-gene resampling), then use an entirely
new matched corpus to vary first/second junction distances and prefix bends with
downstream geometry held fixed. Separate pulse/flag/endpoint/nonlocal mechanisms;
normal successes precede forced-trace interpretation. Preserve diversity before
any future controlled evolution. See results/validation_breadth/next_experiment.md.
