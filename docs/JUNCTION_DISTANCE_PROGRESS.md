# V12J completed handoff

**Complete and audited; do not repeat or extend.** Read
[the report](../results/junction_distance.md) and
[the frozen protocol](JUNCTION_DISTANCE_V12J.md). The preregistration/panel/source/
fixtures were pushed in **e4ca508** before the main corpus was generated.
No genome edits, evolution, reselection, prior population/RNG changes, frozen
source repairs or post-registration protocol deviations occurred.

## What the study establishes

Thirteen fixed random-origin models plus one known control;12new contexts,
25×25boards,8poses,2goals,source prefixes1/2/4/6/8,straight/bent,fork/two-junction/
real alternate-cycle/corridor/no-path variants. Downstream geometry is fixed
within the source-distance contrast. Cycle attachment changes also alter the
alternative path and cell count. Prefix1/2 shape labels duplicate inputs.
Per model13,440inputs,4,800protocolpairs/3,840unique inputpairs.

Normal paired counts: shared ancestor288,resampling192,broad Current164,
inherited local145,narrow Branch74,parent74,broad Branch50,parent50;five other
random models0;intact4800. None passes the full transfer screen. Every random
model0/1920no-path, no false reachable no-path claims. Baselines/intact solve
all11,520reachable and1,920disconnected. No latency benchmark or speedup.

Inherited local completes eight prefix8forkpairs across six contexts, straight
only, reaching17/17edges. Narrow/broad each six prefix8forkpairs across two
contexts, bent only, reaching15edges. No all-eight-pose long-prefix context.
No random attachment4 paired successes. Immediate parents produce identical
normal masks/status/steps; broad child incurs extra work. These are old genomes
newly tested, not J-born evolutionary improvements.

Fixed2context mechanism subset: local27pairs lose all under pulse-off or
endpoint-off, retain27flag-off/nonlocal-off. Resampling32pairs retain pulse-off,
endpoint-off,nonlocal-off;loseallflag-off. Branch normal0on these two contexts;
nonlocal-zero rescues128pairs each (64unique), all short prefixes; read costs
remain. No claim of useful multirange benefit or general rescue. Shared ancestor
was not in the fixed mechanism subset and received no extra probes.

One-context forced trajectories: fresh local nine failed normals later contain
12shortestframes, with two simultaneously shortest paired configurations; not
normal solutions. No stopping retune. All2,592main traces reach64ticks. Source/
junction-response proxies are not universally required: resampling has paired
successes without those responses. See trace comparisons and saved diagnostics.

## Cost and verification

Main277,152calls,624.699candidate seconds /720cap,371,500,676,156work;
647.136s wall,815.02MiBpeakRSS. Calibration2,318calls/2.728candidate seconds.
Rough388s calibration estimate overweighted fast known-control samples; future
profiling should weight each model by its planned call count.

Audit PASSES first attempt:658.499s wall,1115.88MiBpeakRSS,279,470exact response
replays including calibration,319,790terminal raster checks including40,320
baseline replays,2,664fulltraces including fixtures/170,496frames. All165,888main
frames are additionally graded;1,296independent observer checks,112native parity,
435native emission matches.157source/8registration-input/8panel-source/3main-input
hashes pass, plus692oldG/H/Icompletion entries. No source or prior result repair.

Nine new and19related tests pass (28total);204collected, NOT a fresh full suite.
Post-analysis independent exact-path bitmap counts agree with graph-based trace
grading. Both figures rendered and visually inspected; plots use saved evidence
only. All rasters, trajectories, pair certificates, ancestry, parent diffs and
raw counters remain under results/junction_distance/. Logs are preserved.

## Resume safely

The run, audit and calibration are closed. Do not execute their CLI commands
again or reinterpret inspected final cases as fresh validation. Exclude all
**150,776whole layouts**:144,120throughI+512Jfixtures+6,144Jmain.
`junction_distance_data.exclusions()` returns throughI only; also load both
J fixture and confirmation maze manifests in the next study.

The [next proposal](../results/junction_distance/next_experiment.md) is not
registered or launched: calibrate new balanced shapes/near-skill controls,
replicate nonlocal rescue on independent contexts, then compare one context-
consistency selection change against current policy with equal cases/calls,
capacity/mutation/runtime fixed, fresh random-origin arms, resampling and
frozen/ancestor/diversity controls. Do not combine new regulatory runtime and
new pressure in one causal comparison. A stronger replicated validation gate
must precede a60–90minute extension; no unchanged long run is authorized here.
