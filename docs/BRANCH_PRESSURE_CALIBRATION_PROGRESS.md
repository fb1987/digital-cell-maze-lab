# V12N branch pressure calibration handoff

V12N is COMPLETE and audited. Read `results/branch_pressure_calibration.md` first.
Do not repeat/extend N, resume old runs, or train/reselect on N inspected finals.
All six calibration/final cohorts fail; NO evolution pilot was launched. The
cumulative-mutation/full-orientation follow-up is a proposal only.

## Frozen design

Protocol/source/pools/fixtures pushed74fcc24 BEFORE any candidate inference;
all12 validation choices and evidence pushed8bbf2cf BEFORE final generation.
Seed2026101909; fixtures1284. No frozen-source repair, scope revision or protocol
deviation. Sources and input hashes in `preregistration.json`.

Three original M groups×96 founders, plus two independently sampled single V3
edits per original founder (not chained):864 identities,576 sampled mutations,
1,662 physical local/nonlocal configurations. No known solver injection. All-on
M runtime, unchanged limits/goal pulse; stored exposure bits unchanged and inert.
Ceiling256genes; all ineffective edits retained. Exact same evidence/pools/RNG
for current/choice pressures. M neutral/local validation anchors are protected
identically, with no cross-group insertion or final-based selection.

New evaluator: on ordinary emitted goal pairs, exclusive interior arms exclude
shared path cells and BOTH goals. d0 = selected fraction of arm0 under goal0 minus
under goal1; d1 the analogous arm1 contrast. Proxy=max(0,(d0+d1)/2)×weaker path F1.
F1 includes all output pixels. Empty interior arms / non-emission score zero.
Floods, fixed-arm outputs, marker-only changes score zero. One-sided progress may
score but gate separately requires strict-both d0>0 and d1>0. Oracle stays evaluator-
only. Choice inserts proxy after complete-pair count and BEFORE individual/corridor
counts, in rank and lexicase. Current proxy field is zero and reproduces M selector.
Same top-quarter elite rule plus anchors,64 simulated parent draws,top2nominees.
No bred generation. New validation picks1 per group/topology/pressure.

9×9 elementary tree grammar: adjacent,two-edge arms,two-edge shared-prefix fork,
three-edge arms,three-edge shared-prefix fork ×straight/turning;6isolated clutter,
paired goals,2pruned corridors,2open-disconnected goals. Route grammar repeats;
independent clutter contexts are NOT independent topological forms. All8poses
saved/excluded. Fixture/calibration/validation10contexts each,480savedinputs.
Fixtureprofilepose0;cal/valqueryposes0,2,4,6 only:240inputs/40pairs/80corr/80NP.
Final30contexts,all8poses:1440inputs/240pairs/480corr/480NP;48adjacent+192nonadjacent
pairs,144proxy-eligible pairs. Same cases across founder groups; poses/controls
correlated. Exclude177032layouts through N (see below).

## Results

All6calibration cohorts: zero proxy for every candidate,zero strict-both andzero
nonadjacent completepairs; current/choice0/64parentchanges,same elites/nominees.
All activation gates fail. Timing gate passes61.56s projectedcal+val,55.52sfinal.
No posthoc relaxation; no pilot despite available compute.

Independent final current/choice select same model each cohort. Group0local:
12/48adjacentpairs,0/192nonadjacent,meanproxy.03125,12positivepairs,0strict-both,
108/480corridors. Group0nonlocal:12adjacent,0nonadjacent,meanproxy.0023148148,
2positivepairs,0strict-both,12corridors. Other4cohorts0pairs/0proxy,480corridors.
Allrandom selections0/480no-path, no false reachable no-path;alllegal shortest.
IntactVM/BFS/A*/bitwave solve960reachable+480disconnected. No latency benchmark.

Group0selection `branch_pressure/r0/f81/edit1` is EXACTLY GENOTYPE IDENTICAL to
M's96gene founder81: ineffective operand edit (field6 already64), digest/identity
selection tie. Both topology outputs match original founder on all1440finalmasks.
No new discovery or evolutionary improvement. Group1changed child also matches
its parent's finalmasks; group2nonlocal selectedchild is another ineffective edit.
Group2local selectedchild parent wasn't final-panelled; do not add a posthoc test.

All group0local positive partials are turningtwo-edge contexts c9/c10/c11 at
poses1,3,5,7, eachscore.375. Nonlocal positives are turningthree-edge contextc23,
poses3/7, each1/6. Alloutside even-pose calibration. **This is a coverage limitation**:
calibration omitted quarter-turn orientations. NdoesNOT show no positive response
anywhere in the pool. These one-sided final responses still fail pair/gate and
cannot become selection evidence. Allprior skills/variants preserved.

Saved-output diagnosis (post-registration,noinference): geneticallychangedchildren
per192opportunities =184/179/180 bygroup (543/576uniqueevents). Underlocal/nonlocal,
childrenwithchangedmask onany240calinputs: group0=5/5,group1=2/1,group2=2/2.
Counters/steps change127/128,116/116,121/123 respectively; not simply inactivegenes.
Matching masks/counters do not establish hidden-state equality. Goal-switch away
frommarkers occurs in5/8,6/6,0/0 candidates respectively outof288 percohort;all
nonzero normal interior directionalcontrasts negative,nonepositive oncalposes.
Negativeclipping also makes this proxy flat over those responses. Do not silently
change its formula after observing this; prospective tests needed.

## Costs and verification

Calibration398880physicalcalls,validation2160;eachselectorsees414720logicalcal,
combinednominationvalidation5760logicalcalls. Final18physicalmodels×1440=25920.
Main426960calls,49.4231839901candidate seconds,28906147288chargedwork:
cal+val47.842754677s/480cap,28025939410work,59.026821292srecordedwall,1512MiBRSS;
final1.580429313s/200cap,880207878work,2.201719417srecordedwall,819.09MiBRSS.
Initialcorpusgeneration/warmup excluded fromtheseexecutionwallrecords; no e2e
benchmarkclaim. Profile1440calls,.182163499candidate seconds separately;warmup
1candidate+3baselinecalls perstage. Final4320baselinecalls separately.

Audit PASSES firstattempt:71.303323916s,1742.88MiBRSS;428400exactcandidate replays,
432720independent raster grades,4320baselinereplays,576mutation/RNG replays,
288preservedfounders,768parentdraws,3456independentranks,12choices,2880graphcases,
177source/10input hashes and1641priorcompletionentries. Frozenauditunmodified.
21focused tests pass (11new+10M).241repositorytestscollected,NOT freshfullsuite.
Initialunscopedcollection traversedoptionalplot-libs dependencytests andfailed
ontheirtestassets/dependency;repository-scopedcollection passes,bothlogsretained.

Allrawmasks/counters,sources,events/RNG,pools,aliases/selections,oldcheckpoints and
finaldata preserved. See `completion.json` for immutable artifact hashes. Hardware
AppleM4/10cores/16GiB,Python3.13.15,numpy2.5.4,numba0.68.0,llvmlite0.50.0,pytest9.1.1.
No cloud,modelcalls orpaid infrastructure. Figures use saved output only.

## Exclusions and next proposal

Exclude ALL177032wholelayouts =175592throughM+240Nfixtures+240cal+240val+720final.
`branch_pressure_data.exclusions()` returns THROUGH M ONLY. Add `mazes.json.gz`
from `results/branch_pressure_calibration_fixtures`, and N calibration/validation/
confirmation. Includeall8poses evenunqueried. No reuseoffinalsforselection.

Nextproposal only: all8poses,newcases,performanceblindcumulative mutation walks
(e.g. depths0/1/4/16 tobepreregistered) versus equal-budget independentone-edit and
randomresampling controls;preserve everyintermediategenome/RNG andoldanchors.
Question is cumulativebehavioralreachability,not largerarraysbydefault. Count
signedgoalresponse,counter/maskchanges,normalpairedcompletion andskillloss separately.
Profileandboundroughly12minutes. If usefulnewresponse diversity emerges, propose
matcheddiversity-preserving evolution; ifcomputationstillchangeswithoutnormaloutput,
proposeaspecificemission/expressionmechanismtest. Larger60–90min correctnessrun
stillneedsnormalheld-out nonadjacentpaired gainsin2/3evolutionaryreplicates+retention.
Random-originresearch remainsopen;Ndoesnottestlongerevolution/neutraldrift/capacity.
