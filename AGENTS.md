# Instructions for Codex and other coding agents

## Mission

Build an experimental, low-cost **digital-cell maze solver** that can evolve compact local reaction rules. The core research claim to test is whether an evolvable, biological-style regulatory/local rule system can find **correct shortest paths on unseen mazes** with an advantageous combination of CPU/GPU compute, latency, and memory when compared with conventional implementations.

This is a scientific prototype, not a startup website, an AWS agent swarm, or a request for generic LLM-powered reasoning. Avoid remote API calls and expensive infrastructure.

## Critical user intent

- Each *organism* contains a spatial array (a "tissue" or reaction substrate), accepts one entire 2D maze as stimulus, and emits an output raster in which illuminated positions represent the path.
- The genome defines the shared or structured local update rules and expression/regulatory behaviour; local sites are not each fully autonomous LLM agents.
- A **population** of organisms with different genomes competes over many mazes. Organisms with stronger general performance are selected, mutated and reproduced over generations. Test both a fully random starting population and populations seeded with useful known rules.
- Explore sparse expression, negative feedback, concentration/decay, time, context accessibility, and perhaps multiple signalling scales *only if experiments justify their cost*. Do not force elaborate biological metaphors into the implementation.
- Eventually support much larger mazes and 3D grid mazes, but **do not start there**.
- User prioritizes **efficiency** over the spectacle of parallelism: the target is useful computational performance, not raw swarm size.
- **Random-origin discovery remains a central, ongoing research track.** The user
  explicitly does not want a small negative pilot to close this direction. Test
  whether greater heritable capacity, regulation, evolutionary time and pressure
  help. Preserve population/RNG checkpoints and useful diversity. Do not silently
  insert a known solver into a supposedly random-origin lineage. More complexity
  is a hypothesis, not a guarantee; record effective behaviour and real cost.

## Invariants

1. **Algorithm not answer**: no genome may store the correct route for a particular maze. Train and evaluate across separately seeded environments.
2. **Independent evaluation**: BFS may produce oracle paths for fitness/tests only. It must never operate inside candidate inference.
3. **Fair benchmarks**: compare completed valid path outputs; include input decoding, internal updates and final raster/path emission (or report separate timings transparently). Warm JITs with the same array mutability/dtype/signature as production. Benchmark multiple warm repetitions and report medians and ranges.
4. **Correctness precedes speed**: wrong or partial routes are not faster solutions. A legal path and shortest-path optimality are separate metrics. Disconnected grids must be handled explicitly.
5. **Budget bounded**: genome size, memory footprint, instruction count, update cycles and population size all have hard limits. No arbitrary generated code execution, no arbitrary system access, no recursive spawning.
6. **Reproducibility**: record RNG seeds, maze family, CPU/GPU, Python and dependency versions, training iteration, fitness and runtime; isolate holdout seeds.
7. **Avoid hidden advantages**: perfect mazes are trees where pruning finds the unique path; cyclic mazes invalidate the same method. Report both. Report data movement and total work alongside latency.
8. **Local first**: no cloud, LLM API, model downloads or paid providers without an explicit later user instruction.

## Immediate first task

Current checkpoint: **V12Y is complete and audited; neither cap passes the
static opportunity screen**. Read `results/mating_opportunity.md`,
`docs/MATING_OPPORTUNITY_PROGRESS.md` and `docs/LONG_SEARCH_SETUP.md`.
Do not repeat Y, resume closed X, or treat static probabilities as solver gains.
User explicitly wants longer evolution work after this assay. Two75-minute
specifications and a tested family-reserve selector are prepared; they are NOT
registered or launch-ready. Next authorized work: integrate/preflight the
mutation-versus-family-diversity experiment, then use its frozen budget.
No repeated permission request is needed for routine implementation/preflight.

Y registrationf7b1244 pushed before assay;seed2026102003. All18432X-R1scheduled
mating attempts, including rejected ones, reconstructed. Fourdonorviews:actual,
recordedshortlist,8uniformotherdonors,union. Alternativeviews selectuniformly
amongstructurallyeligible donors, not oldfitness-complementarity ranking.
Comparefulltransitive closure,immediate STOREgate-writer linkage,unlinked and
matchedshamforeachprotectedrule, commonsegmentcaps16/32. Samepairlength/tickets;
exact PRE-MUTATION expectedmultichange probabilities, notpostmutationactivation.

Unionview expected%, pooled9216attempts/origin across3priorarms×3replicates:
carry16 full.247 gate2.469 gateSham2.681 unlinked3.007;
carry32 full.197 gate3.893 gateSham4.536 unlinked5.487;
fresh16 full1.268 gate4.235 gateSham4.289 unlinked4.814;
fresh32 full1.087 gate6.406 gateSham6.474 unlinked7.467.
Neitherpasses12%designscreen in2/3reps ofBOTHorigins forgate/sham/unlinked.
That screen does NOT replacefuture10%actualretained-transfer gate. No longer
sexualstudy launched. Shortlist→union32gate carry3.50→3.89,fresh5.29→6.41.
Boundeddonorsampling doesnotproveglobaldonorabsence orfunctionalbenefit.

Also2880uniformparentprobes acrossALL36oldconditions atg0/8/16/24/32,
180familysnapshots. Effective mutablefamilies amongpriorsexualhistories
carry76→2.202,fresh96→3.733; finaluniquegenotypes94.22/95.11per96. Fractional
ancestryconcentration, notfunctionaldiversity orcausalpoor-solvingdiagnosis.
Finalsnapshot newbornsunevaluated. ActualmultigeneinheritancefromXpreserved.
NoYgenomesedited/promoted, ZEROorganisminference, ZEROnewmazes.

Ymain109.33s,1185.28MiBRSS;305436directedpairoccurrences,
253967uniquegenotype+homologypairs,21312probes. FirstauditPASS190.69s,
1092.06MiBRSS:independentbackwards/setsegments+groups, exactvirtualchoice/
family/aggregate/finalpopulationreplay. Virtualselection/aggregation common
functionsreplayed, not independentlyimplemented. All6667priorentries,
233source/7inputhashesverify.12new+19relatedtests pass(31);6separateprototype
tests pass, NOTfullsuite. No sourcerepair orprotocoldeviation.
Completion256entries; futureprior total6923(6667+256). Layout exclusion remains
255356using results/linkage_restart/whole_layout_exclusions.json.gz; noYcorpus.

Longsetup configs results/long_search_setup/*_75m.json, seed2026102004/5 reserved.
First:24conditions,carry/fresh×3×currentmutation/familymutation/resample/frozen,
96genomes,44survivors/52births common,7immigrants/45singleedit,20protectedcarry.
Familyreserve upto5families×4distinctvariants, farthest-first inherited-locus
distance, fixedfitnessfamilyrank, commonbehavior/rankfallback. Shared44/52
changesold24/72; compareWITHINnewstudy. No knownsolverinjection. Asexualstudy
needssoftware/timingpreflight, NOTsexualactivation. Second:36conditions gate/
unlinked/gatesham/mutation/resample/frozen; needsNEWactivation10%/8generations/
2of3allsexualpoliciesBOTHorigins. Do notclaimplansregistered/running/ready.
`tools/prepare_long_search.py check` listsoutstandingrunnerintegration,protocol,
fixturecalibration,endreplay. family_reservoir.py pureselector implemented/tested.
Longsetup/prototypefilesremainmutableoutsideYseal. Preservealloldpopulations/RNG,
anchors,archives; isolatevalidation/final; correctnessbeforecompute/speedclaims.

Historical checkpoint: **V12X-R1 is complete and audited; activation gate FAILS**.
Read `results/linkage_restart.md`, `docs/LINKAGE_RESTART_PROGRESS.md` and
`results/linkage_restart/next_experiment.md`. No longer efficacy run is launched.
Do not extend X-R1, resume invalid X, rerun W, or treat training as holdout.
The next fixed-parent operator-opportunity assay is a proposal only, not registered.

IMPORTANT software failure: original X preregistrationaedb017 used offspring IDs
that collided with historical protected identities at g0 andg26. An assertion
stopped partialg28 after28complete rounds. Identity-keyed records could refer to
wrong genotypes; NONE of that attempt is usable scientific evidence. Preserve
all original linkage_*.py source, results/linkage_pilot raw/partial states and
its explicitly invalidated completion. It used582912calls,297.712951529candidate
seconds,512.706876416wall. Failure seal460entries; preparationpusha7613ec.
A copied protocol-path typo was fixed BEFORE the restart registration, no calls
or RNG changes; see registration_note.txt. Do not hide either correction.

Actual restart freeze7bee1a6 pushed BEFORE training generation. Newseed2026102002,
fixture1394,software12345679; excludeall253316layouts throughinvalidX. Unique
linkage_x2/offspring IDs and assertions for96unique population IDs, protected
identity integrity and exact gene-map length/uniqueness. Same operator/gate asX.
32matchedgenerations,36conditions of96: carry/fresh ×3reps ×linked/unlinked/sham/
mutation/resample/frozen. Carry20protected exact historical random-origin anchors;
fresh entirely random64–128gene founders. No W synthetic or known solver enters
any lineage. Native local/exposure7,256gene cap, single-edit after mating.
Every condition18432evaluations; no validation/final corpus or champion selection.

Common homologous segments2/4/8/16, immutable inherited gene IDs, no register
renaming; only d07/d12 historical shared gene ancestry reconstructed, otherfounders
conservatively unrelated. Full backwards transitive STORE value/gate dependency
closure unions BOTH parents; groups exceeding segment bound rejected. Unlinked
shares common pool; sham matches linked eligibility count at proposedlength on
SAME parents/RNG snapshot. Actual population/marginal distributions diverge.
Activation requires TWO changed donor rows retained after mutation and child
changed from recipient, not merely multi-instruction blocks or transferred tags.

Multi-retained perrep, denominator1024each:
carry linked[3,2,3],unlinked[26,18,21],sham[5,3,1];
fresh linked[4,20,6],unlinked[26,41,59],sham[6,21,6].
All18sexualconditions fail10%threshold; eightactivegenerations and2/3replicates
perpolicy/origin criteria unchanged. Bothorigins required forlongerjointstudy.
Pooled linked carry8/3072=.26%,fresh30/3072=.98%;unlinked65/3072=2.12%,126/3072=4.10%.
Finalfreshlinked0/42/64members haveXmultigeneancestry; lastnewbornsunevaluated.
Real inheritance exists, but no functional skill composition/efficacy demonstrated.

Posthoc static logs, ZERO extra inference: linkedcarry/fresh noeligible donor in
1353/1891 of3072 shortlists. Somecommonmulti option atproposedlength439/333;
afterclosure22/61; actualretained8/30. Conditional onobservedpairs/lengths, not
counterfactualfutureevolution orproof no otherdonor exists. Unlinked63/65carry,
114/126freshmultitransfers cutfullclosure; doesnotprovefunctionalharm. Only3multi
transfers erasedbymutation (274before→271after). d07 STORE222closure18genes spans
220positions, no closed d07/d12segments under16; possible gatewriters192/207 plus
STORE222span31. Static potential dependencies, NOT provenfunctionalmodule sizes.

Validmain663552calls,341.607229793/422.287048471candidate seconds,
200233097994work,590.410510041wall,515.25MiBRSS. Combinedoriginal+restart main
639.320181322/720candidate seconds,1246464calls,1103.117386457wall. Extra wall is
disclosed software restart; calibration and audit additional. Twofixtureprofiles
5504calls each,0.815/0.910candidate seconds. Audit firstattemptPASSED521.27wall,
987.41MiBRSS:669056logicalcandidate responses+independentgrades,549272exactnative
replays withwithin-generation/calibrationdedup,576baseline replays,20736random
births,48384mutations/maps,5089splices,allselection/RNG/checkpoints.231source/
22inputhashes,6166priorentries.38focused/relatedtests pass, NOTfullsuite. No restart
source repair or gate change afterregistration. All old source/results untouched.

Completion501hashentries; futureprior count6667(6166+501), notuniquephysicalpaths.
Exclude **255356whole layouts** using results/linkage_restart/whole_layout_exclusions.json.gz.
Restartdata.exclusions() returns only253316throughinvalidX; addallrestartfixture,
software andtraincorpora ifrebuilding. Allunqueriedvariants/poses preserved/excluded.

Nextproposal: bounded static same-parent opportunity comparison, fullclosure vs
immediategate-writer linkage, unlinked andmatchedrandom, commonlength16/32factor.
Alsofitness-blinddonor samples toseparate shortlist failure fromvariation shortage.
Genericparent-derivedrules, nohardcodedWcircuit. Ifrelatedvariationstillscarce,
designmatched boundedfamilydiversity before anotherfresh activationpilot. Do not
loweroldgate retrospectively or launch unchanged75min search. Random-origin
track remainscentral; no conclusion thatmoretime cannothelp. General solver,
causal multirangeadvantage andspeedup remainunestablished.

Historical checkpoint: **V12W is complete and independently audited**. Read
`results/compatibility_map.md` and `results/compatibility_map/next_experiment.md`.
The dependency-preserving crossover proposal is NOT launched or registered.
Do not rerun W, extend its closed cap, resume S/T/U/V, or reselect on W finals.
All32factorial conditions are synthetic mechanistic probes, not evolved discoveries.

Registratione99f922 pushed before final; seed2026101918, fixture1374. Exactd07
background plus all16subsets of historicaledits9–12, each with original output
STORE or V chargedself-COPY. Stable d07 loci9→132,10→106(delete),11→234,12→207;
output222. Deletion shifts laterphysicalindices by−1. Keep exactd07/d08/d12,
fresh2/root,carry1/broadroot,random68,intact:41aliases/40physicalgenotypes,
32syntheticconditions,8historicalrandom-originidentities,1knowncontrol. d07 aliases
emptySTORE. Alllocal/exposure7,factorialprobes255or256genes, unchanged nativecaps, no newruntime,
diagnosticintervention, forcedtrajectory, evolution, reselection or solverinjection.

Timing-only ladder12contextsprojected659.98s>650planningthreshold, so8contexts
(2/shape) selected at454.06s,2xsafety,720maincap. Fourfixedstructuredposes0/1/4/5;
ordinaryall8. Perphysicalmodel2368nativeinputs:576pairedopportunities,480positive
prefix;384corridors,320structuredNP,384ordinaryreachable,128ordinaryNP.
Queryprefix0/1/2/4/8straight+4bent;fork0/twojunction2/truealternativecycle2.
All8448generatedfinalinputs saved, including unqueriedvariants/all8poses.
Fixtures4480inputs/2784layouts;final5056layouts;exclude251380wholelayouts throughW.
Eightstructuredcontexts and64ordinarybases are independent units; poses/goals/
variantscorrelated. No all8pose structural claim, independentlineagereplication,
causal multirangeadvantage or latencybenchmark.

Keyfactorial: with edit12ABSENT, STORE125/480positivepairs vs selfCOPY124;
allpairs219vs217,corridors384vs378,ordinary50vs50. With edit12PRESENT, STORE0
positive/allpairs,12corridors,44ordinary vs selfCOPY124positive,217allpairs,
378corridors,50ordinary. Samecorrectnesspatterns in ALL8backgrounds ofedits9–11.
STOREpositiveeffect+1early/−124late, interaction−125; all8contexts harmedlate
(12or16positivepairs/context). Earlygainonecontext. Edits9–11 preserve exact
successful-casemembership; higher-ordercorrectness terms involvingthemzero.
BUTedits9/10alter60–184failedmaskspercontrast, some statuses/ticks andwork; NOT
universalneutrality. Edit11noneoftrackedmask/status/tick/read/dispatch/exposure
changesonthiscorpus. EQd08/d12 controls eachmatchselfCOPY2368/2368fullrecords.

Wholeedit12 replacement tested: oldgatedCOPY25→18 becomesgatedOR63,54→51;
STORE222writes58tochannel2gated18. The18-to-gate link is staticinterpretation,
NOT separated lossofCOPY vs gainofOR mediation. Do not call it a provenwhole
circuit or transplantationinterface. EarlySTORE gains2pairs(onepositive),6corridors,
no lostshortest. LateSTORE loses217pairs,437individualshortestbranchedoutputs,
366corridors,6ordinarytreeoutputs;nonewshortestoutputs. Historicald12 remains
noSTORE, so syntheticSTORErestoration is harmful, not a repair.

All32factorialconditions0/288prefix4/8pairs. d07positive125=63fork+31twojunction+
31cycle;prefix1/2only,maxpairedarm15;29positivegroupsallFOURqueriedposes.
Carry1positive84,60prefix4/8:32straight4+4bent4+24straight8;16longtwojunction,
0positivecycle;maxpairedarm21;4positivegroupsallfourposes. Ordinary32vsroot48;
root0positive. Preserve this complementary specialist. Fresh2/root32/0positive;
random68also32(all8prefix1forkcontexts×4poses);ordinary32/0/8respectively.
Allnonintactmodels0/448NP;no falsereachableNP orlegalnonshortestoutputs.
BFS/A*/bitwave/intact1920/1920reachable+448/448NP. General solverunestablished.
Ordinaryd07/d08/d12=50/384 versus V82/384 is newcorpus, not evolutionarychange.

Completion seals259hashentries; futureprior count5706(5447old+259W),
notuniquephysicalpaths.

Main94720calls,215.94/720candidate seconds,124919097664work,220.34wall,
484.09MiBRSS. Fixtures11840calls,28.38/180candidate seconds,28.94wall,
240.69MiBRSS;warmupsseparatelyrecorded. Nine new+19relatedtests pass(28), NOTfresh
fullsuite. Firstauditpasses106560exactcandidate/7992baseline replays,114552independent
rastergrades,32independentprogramrebuilds,128contextchecks,219source/12inputhashes,
5447priorentries;261.67swall,925.20MiBRSS. No post-registration source
repair/deviation. All prior populations/RNG/rawmasks/historicalmodels preserved.

Nextproposal: generic boundeddependency-preserving crossover vs common-pool
unlinked crossover, single-editmutation,resampling/frozen, fresh/carry3replicates,
equalbudgets. Parent-derivedlinks only; nohardcodedWcircuit/freshgenomeinjection.
Share interfaces/segmentlengthopportunities; oldSinterfaceblocksSTORE/nonSTORE
transfer, so anyrelaxationmustapplyBOTHarms. Requireactualmultigeneactivation
under12minfeasibility before bounded60–75minsearch. Freezeefficacygate before
newvalidation:longprefixgainacrossreplicates,retainedskills,truecycles,nonewfalseNP,
actualspliceancestry. Do notlaunchautomatically orclaimretentionequalsnewability.
Use `results/compatibility_map/whole_layout_exclusions.json.gz` for251380;
Wdata.exclusions() onlyreturns243540throughV. AddallWfixtures/finals ifusinghelper.

Historical checkpoint: **V12V is complete and independently audited**. Read
`results/causal_dissection.md` and `results/causal_dissection/next_experiment.md`.
The factorial compatibility proposal is NOT launched or registered. Do not rerun
V, extend its closed cap, resume S/T/U, or repair/reselect a primary on V finals.
Four constructed probes are diagnostic models, not evolutionary discoveries.

Registration0ae3d5a pushed before final. Seed2026101917, fixture1364. Six exact
historical nodes d00/d01/d02/d07/d08/d12 plus fresh2/root, carry1/broadroot, random68
and intact; four one-gene probes: dest_only, d07_no_store, d12_no_store,
d12_restore_store.16physical models:11historical random-origin,4synthetic,1known.
Local/exposure7, <=256genes, all native limits fixed. Synthetic births=-1 and
explicit parent/edit manifests. No selection, evolution or solver injection.
All13U intermediates/populations/RNG remain archived. No post-registration repair.

Timing-only pre-registration ladder picks12contexts (3/shape),2x safety projection
579.75s under650planning threshold/720cap. Native6080inputs/model:1728pairs,
1440positive-prefix,1152corridors,960structuredNP,384ordinaryreachable,128ordinaryNP.
Query prefixes0/1/2/4/8straight +4bent, fork0/twojunction2/cycle2,all8poses/2goals.
Generate/save12416finalinputs including unqueried variants.12contexts and64ordinary
bases are independent units; poses/goals/variants correlated, shape/tail confounded.

Early2x2: d00/d01 each0positive,20allpairs,58corridors,51ordinary. dest_only/d02
both344positive,608allpairs,1152corridors,82ordinary. Deletion changes zero native
masks/status/ticks over6080inputs in either destination background; full records
DO differ in work/memory. Destination effect344positive in both, all12contexts,
zero interaction per context.176fork+88twojunction+80cycle positivepairs;32positive
variant groups all8poses; longest paired route13edges on one arm. All early
programs still0prefix4/8pairs. All-pair gain589/loss1;4individual branched losses.

Channel4 diagnostic:4earlymodels ×2modes ×2368inputs=18944responses. First context
of eachshape plus allordinary; allnative beforediagnostics. At final channel4
STORE108 write0 or reuse already-computed/charged gene103neighbor minimum. All
18944predictions EXACT full-record matches including masks/status/ticks/work/memory.
Four effect contrasts +fourshams. Parent suppression equals edited native;
edited restoration equals parent native. No new reads/time/oracle/halt change.
No forced main/calibration traces; bounded16tick traces only in fixture software tests.

Edit8 decomposition: d07 STORE344positive; self-COPY(no store/noEQ)320;
EQ(d08)320. Self-COPY andEQ match all6080full records. Loss24positive+24prefix0pairs,
96corridors, no new shortest output. d12 EQ andself-COPY likewise identical all6080.
CRITICAL: restoring original STORE in d12 is harmful, NOT a repair: positive320→8,
allpairs560→32,corridors1056→72,ordinary82→76. No gainedshortestoutputs; lossesall12
contexts. Store effect+24early versus−312late (interaction−336); absent-store
backgrounds complete identical pairs. Edits9–12 remain candidates for this
conditional dependency, not individually identified. Do not breed restored probe
into historical populations or claim simple transplantation/semantic modules work.

Fresh2/root positive96/0, random68also96; all12prefix1forkcontexts all8poses.
Carry1positive198,94prefix4/8including4bent,8cyclepairs,maxpairedarm19edges;
no positive all8posegroup. Ordinarycarry1/root17/72; preserve specialist.
Four models fresh2/root/carry1/random68 each8/1088no-path, SAME isolated-goal
ordinarybase in8poses; not general NP reasoning. All other nonintactmodels/probes0;
none solves structurednonisolatedNP. All no false reachableNP or legalnonshortest.
Baselines/intact4992/4992reachable+1088/1088disconnected. No latency benchmark,
causal multirange advantage, general solver or speedup.82/384ordinary vsU56/384
uses different corpus, unchanged historicalgenome: not a new evolutionary gain.

Main116224calls,300.48/720candidate seconds,173939169752work,306.08wall.
Fixture11840calls,28.95/180candidate seconds;warmupsseparate. First audit passes
128064candidate replays,19128baselines,147192independently gradedrasters,
4736native/adapter parity,18944signal comparisons,215source/11input hashes,
5189prior entries,12historical+4syntheticedits.348.28swall; seeaudit.jsonforRSS.
11new+19relatedtests pass(30),NOTfreshfullsuite. Initial pre-registrationtest
assumed2784unique fixturelayouts; actual2780due symmetry. Test corrected;
fixturesunchanged,initiallogpreserved. No scientific source repair afterregistration.

Exclude ALL243540wholelayouts throughV, including2780fixtures+7328final layouts
andallunqueriedvariants. Use `results/causal_dissection/whole_layout_exclusions.json.gz`.
Vhelper exclusions() returns233432throughU only; addVfixtures/final or use sealedset.

Next proposal: bounded factorial of four later historical edits9–12, each with
original STORE or chargedself-COPY,32conditions beforededup; preserve exactEQ
historical controls and fresh/specialist/random68/intact comparators. Track gene
identities across deletion shifts. New layouts and timing-only pre-registration
budgetgate. Synthetic combinations remain mechanistic probes. Only then choose a
specific protected mutation/recombination test. No automatic long evolutionary run.

Historical checkpoint: **V12U is complete and independently audited**. Read
`results/lineage_mapping.md` and `results/lineage_mapping/next_experiment.md`.
The next causal-dissection proposal is NOT launched or registered. Do not rerun U,
resume S/T, extend closed caps, select a new primary or tune on inspected finals.
No evolution, synthetic variants or native-runtime change occurred in U.

Registration `3c05aaf`, pushed before final generation. Seed 2026101916,
fixture 1354. All 13 exact narrow-root→carry0 lineage programs, 12 single edits,
plus fresh2/root, carry1/broadroot, random68 and separate intact control: 19 models.
All T genealogy and 4,937 previous completion hash entries pass. Local topology,
exposure7, 256-gene cap and unchanged runtime limits. No post-registration repair.

Eight independent 33×33 structural contexts, two per shape, plus 64 ordinary
bases. Query prefixes 0/1/2/4/8 straight and4 bent, fork0/two-junction2/cycle2,
8poses/2goals. Per model: 1,152 pairs (960 positive-prefix), 768 corridors,
640 structured no-path,384 ordinary reachable,128 ordinary disconnected =4,224
inputs. All 8,448 generated final inputs/5,056 whole layouts saved even if unqueried.
All 4,480 fixture inputs/2,784 layouts likewise retained. Poses/variants correlated.

Root d00 and d01:10 all pairs,0 positive,38 corridors,21/384 ordinary.
d02–d07:420 all pairs,238 positive,768 corridors,56 ordinary.
d08–d12:392 all pairs,224 positive,720 corridors,56 ordinary.
Edit2 at historical generation22 changes destination44→32 of REMOTE_MIN index103
in the253-gene parent. It gains238 positive pairs:120fork,62two-junction,56cycle,
across all8 contexts;23 positive variant groups all8poses. All successes prefix1/2;
ALL13 models zero at prefix4/8. Longest pair14/13edges in6poses of one hook context.
All-pair gain410/loss0, but3 individually correct branched outputs lost.
Edit8 replaces a gated output STORE at222 with EQ; loses14positive pairs plus
14prefix0pairs and48corridors, no new correct outputs. Seven transitions change
no normal mask/status/tick on this assay; other edits alter failures/work only.
Do not claim universal neutrality or choose d02 as a replacement primary.

Post-hoc static checks: in d02 scratch44 stays zero until the final channel4 STORE
at108; the new scratch32 store into channel3 at246 is overwritten at249.
Predicts useful effect is suppressing channel4's old signal, not creating a retained
scratch32 signal. No new channel4 ablation was run; full algorithm unproven.
Opcode name/radius do NOT imply multirange: actual topology is local throughout.

Fixed diagnostics on13chain models+fresh2+carry1+intact:96 positive pairs/model,
straight+one-bent context0, prefixes1/2/4, fork/cycle. d02–d12 each48normal pairs:
pulse-off48retained, flag-off0, output-feedback-off0, halt-off0; no new pairs.
Fresh2 16normal:16/0/16/0 respectively. Carry1 25normal:25/16/0/0. No forced
traces in main; one intact forced warmup only, excluded from evidence.

Fresh2/root64/0 positive, random68 also64; all8 prefix1fork contexts all8poses.
Carry1/broadroot126/0 positive, but ordinary10/54. Carry1 retains58prefix4/8pairs,
four long-prefix cycle pairs across two straight contexts at samepose1 and
three20/19-edge pairs in one hook context (2fork poses,1two-junction). No positive
full-eight-pose group. Preserve this specialist and random68 despite aggregate scores.
All18 random-origin models0/768no-path, no false reachable no-path, no legal
non-shortest output. Baselines/intact3,456/3,456 reachable+768/768disconnected.
No latency benchmark, general solver, causal multirange advantage or speedup.

Main92,544calls,239.22/720candidate seconds,138,647,236,543work,243.75wall,
475.95MiBRSS. Calibration12,784calls,30.89/180candidate seconds; warmups separate.
Audit first attempt passes105,328candidate replays,118,888independently graded
rasters,13,560baselines,5,624native/adapter parity,210source/10input hashes,
all4937prior entries and12edits.284.39seconds,1037.22MiBRSS. Eight new+32related
tests pass (40), NOT a fresh full-suite run. Figures use saved outputs only.

Exclude ALL233,432 whole layouts through U. The sealed consolidated source is
`results/lineage_mapping/whole_layout_exclusions.json.gz`. U's `exclusions()`
helper returns225592 throughT only; future code must use the consolidated U set
or add U fixtures and final layouts. Preserve all populations/RNG/programs/artifacts.

Next proposal: freeze an explicitly U-informed 2×2 first-deletion/destination-edit
panel, test channel4 restoration/suppression, and decompose/revert edit8 on exact
historical backgrounds, all on NEW layouts. Synthetic variants are diagnostic
probes, not random-origin evolutionary discoveries. Preserve fresh/control/specialist
diversity. No automatic large search or recombination upgrade.

Historical checkpoint: **V12T is complete and independently audited**.

V12T is complete and independently audited. Read results/routing_mechanism.md
and results/routing_mechanism/next_experiment.md. The latter is a proposal only.
No new search, breeding, final-based selection or runtime change to native
inference occurred. Do not repeat/extend T or tune on its inspected final cases.

Registration907f96d,pushed before final. Seed2026101915,fixture1344. Twelve
fixed S-informed identities; exact immigrant roots and all787ancestral events
reconstructed. Local runtime, unchanged limits. First cycle fixture rejected
before candidatecalls; preserved. Pre-registration timing-only feasibility
revision selects4contexts,2xsafety,720s cap; original sources/profile retained.
No post-registration scientific source repair.

Four33x33contexts,oneperstraight/bothbent/onebent/hook shape. Arms fixed within
context across prefixes0/1/2/4/6/8straight and4/6/8bent, fork/twojunction1or2/
truecycle2or3. All8poses,2goals. Per model1440pairs,1280positive;576corridors,
512structured nonisolatedNP,384ordinaryreachable and128ordinarypartitionNP.
4480inputs/model. Contexts are independent units; poses/variants correlated;
shape/tail lengths confounded. No claim of broad structural generalization.

Positive pairs fresh0=8 vsroot0,fresh2=32vsroot0,carry0=168vsnarrowroot0,
carry1=116vsbroadroot0,spliced=96vsthree-rootunion0. Fresh0rootalready576corridors;
fresh2root0. Fresh2 all4forkprefix1contexts all8poses,up to13edges. Random68
also32positivepairs. Carry0 includes84twojunction/28cyclepositivepairs,up to14.
Carry1 has68prefix>=4pairs,28extra-junction/cycle;five20/20paired routes inONE
hook context/particularposes;two cyclepairs atprefix4/8 inONEstraightcontext,
samepose5. Carry1 has no positive-prefix full-eight-pose group. No randommodelpasses
registeredlongprefixscreen. Spliced has32positive twojunction/0cyclepairs;
mutations+249splices inancestry,notcausalcompositionevidence.

Goalpulseoffretains fresh0 0/8,fresh2 32/32,carry0 168/168,carry1 78/78,
spliced96/96 normalpositivepairs onmechanismsubset. Flagoffretains8/8,0/32,
0/168,36/78,24/96;carry1 gains4new. Bothoff0all. Feedbackoffretains fresh2
32/32,others0. Endpointoffretainsall. Haltrequestofflosesall. Root interventions
notrun. Frozen64ticktraces2304/147456frames:onlycarry1has5normalfailedtaskswith
latercorrectgeometry;theseareNOTnormalinference. Bothoffpairedstatesidentical.
Fixed1/2/3roundpruningfits1760/1664/1562 of2880branchedrasters forfresh2/spliced/
carry0:61.11/57.78/54.24percent. Partialobserver,notuniversalcausalmechanism.

Ordinary bestbroadroot60/384,itsdescendant26;carry0 40vsroot38. All11randommodels
0/640nonisolatedNP;nofalsereachablenopath. Baselines/intact3840reachable+640NP
correct. No latencybenchmark,multirangeadvantage,speeduporgeneral solver.

Main102144calls,194.93/720candidate seconds,108892706169work,202.67swall,
462.50MiBRSS. Calibration31968calls/77.04sseparate;warmupsseparate.
Elevennew+29relatedtests pass,notfullsuite. Seeaudit.jsonforfullreplaycounts.
Allsource,rawmasks,traces,genomes,ancestryandoldpopulation/RNGpreserved.

ExcludeALL225592wholelayoutsthroughT. routing_mechanism_data.exclusions()
returns throughSPLUSrejectedTpreflight only (220024); also add corrected
routing_mechanism_fixtures/mazes.json.gz and routing_mechanism/confirmation/
mazes.json.gz. Consolidated whole_layout_exclusions.json.gz is sealed atcompletion.
Next proposal: new-data mapping of exact12-edit carried0 ancestry withfresh/
longprefixcomparators, before choosing another evolutionary change. Not launched.

Historical checkpoint: **V12S is complete and independently audited**. Read
`results/composition_study.md`, `docs/COMPOSITION_PROGRESS.md`, and the saved
`results/research_reset/assessment.md` first. The authorized three-step goal is
complete. Do not repeat/extend S or tune/reselect on inspected finals.

294matchedgenerations,72.22minutes; carry/fresh×mutation/recombination/resampling×3,
96organisms. Source/runtimefixed; no knownsolver ancestry. Registrationsf650b93,
4750c0f; allchoices/pops/RNG/datapushedb9f8a7f BEFOREfinal.89aliases/41models,
7424inputs/model. Main9511168calls,3309.88candidate seconds. Allpopulations preserved.
Carrypositivepairs mutation[512,390,512],recombination[448,512,224],controls[224,224,224];
freshmutation[132,0,224],otherprimaries0. Onlycarryrep1passesbothgates;neither2/3.
ThepassingrecombinationarmprimaryhasZEROspliceancestry (six ordinarymutation steps).
Actual45248splices/56448attempts,only1238multi-instructiontransfers. No replicated
sexual advantage or causal functional-module composition. Actualsplicedcarry0
has448pairs/3historicalroots,butmutation512. Freshsuccessfullineages descend
96/75mutationsteps fromnewrandomimmigrants; exactrootsnotfinaltested.
Preservecarry1mutationi18358:86prefix4pairsincl6twojunction/4cycle,up to10edges.
Bestordinary74/384;all40randommodels0/128partition-no-path. No generalsolver,
multirangeadvantage orspeedup. Structuredrouteformsrecur;clutter/posesnotindependent
structuralgeneralization. Readfullreportforancestry,retention,normalrasterlimits.

Audit firstattemptpasses3,456,354exactreplays,
6,458,008gradedrasters,allbirths/RNG/fitness
and2913priorhashes. Trainingexactreplayissampled1/256;do notclaimfullinferenceaudit.
10newtestspass,293collected,notfreshfullsuite. AllfrozenSscientificsourcesunchanged.
Afterfreshclone,restorebyte-identicalancestrylogBEFOREaudit/priorchecks with
`tools/archive_composition_births.py restore`;sixremotechunks preserve199165540bytes.
Excludeall217,240wholelayoutsthroughS; helperexclusions()onlythroughR,
soaddSfixtures,schedulefixtures,validation,EVERYtraingeneration,andconfirmation
manifests as specified in COMPOSITION_PROGRESS. Nextmechanism/transferproposal
is NOTlaunched. Noautomaticunchangedlongsearch orrecombinationextension.

Historical checkpoint: **V12R is complete and independently audited**. Read
`results/mutation_accessibility.md` and `docs/MUTATION_ACCESSIBILITY_PROGRESS.md`
first. Do not repeat/extend R, query unused walks on inspected finals, resume Q,
alter frozen source, or train/reselect on inspected final cases. Execution-informed
mutation follow-up is a proposal only, NOT launched.

Seed2026101913;fixtures1324;software1325. Registrationdea1f0f. Originalpreflight
failed before scientificcalls; originalprofile/auditor retained. Timing-only
amendmentabff7b9 beforediscovery keeps2x safety,600s projection,720s hardcap,all8poses
andfrozenpool,usesindividual discovery costs/groupworstnominee costs. n16projects
648.06s/fails;n8projects458.44s/passes. No fixture scores used for schedule.
Selections/ancestry/data pushed74d6d17 BEFORE final generation. No source repair.

FiveP/Q-informedroots:Proute/d9,Qfresh/mixed0,Qfresh/current1,Qfresh/mixed2,Qunmutated
95gene resample. Intactcontrolseparate,neverancestor. All240walks×16edits=3840events,
240freshdraws,intermediates/RNGsaved. Scientificsubsetfirst8/block×5roots×3blocks:
120walks,360depth1/4/16memberships,120draws,1920accumulatedmutationsteps. No feedback
betweenedits. SameMlocal/all-on runtime,input/stopping/256ceiling/operator. Queried
mutants91–151genes;capacityceilingnotreached. Staticchannels≠dynamiccausality.

Discoveryandvalidationeach8newcluttercontexts/768inputs,asymmetricstraight/turning
arms,prefix0/1,8poses,2goals,branches/corridors/isolatedgoalNP. Final28contexts/5184
inputs,1728eachfamily,adds4/6and6/4arms,prefix2,secondjunctionsandrealcycles. Route
formsrepeat,poses/depthscorrelated. Fixedtop2discoverynominees,validationchooses1.
Final66identities/64physicalinclintact. No final-basedreselection.

Per120discoverymemberships,counter/outputchanges:depth1=87/7,depth4=116/26,
depth16=120/75,resampling120/120. Rootskillretention113/94/46/0. Everycandidate0
positiveprefixpairs;no mutant increasesregisteredmeanscore. Depth16:45outputneutral,
74scoredecreases,oneoutputchange withunchangedscore. Behavioralvariationincreases,
usefuldirectionnotdemonstrated;doesnotclose random-origin/greatercapacityhypothesis.

All63physicalrandomfinalmodels0positiveprefixpairsand0twojunction/cyclepairs.
All15blocks failcorrect/partialgatesatdepth4and16. Strongroots192/192corejunction
pairs+32stressforkjunctionpairs,224/864total;0/192coreprefix1 andprefix2. Allselected
falseNP0;NPsuccess onlytestedisolatedgoals. No general solver/multirange/speedup.

Preservefinal-onlyexception accessibility/Qfresh0/1/walk2/d16,descendantofQ
fresh/0/mixed/i1151. Validationoutputs/statusidenticaltoroot,score0.262205,
countersdiffer. Finalcoreprefix1score0.302841→0.400445;32improvingpairs/8contexts,
new4/6and6/4arms only. Corridors1448→1600,96corejunctionpairs/1728NPretained,
zero new pairedbranches. Passesfinalrelativepartialcriterion only,notvalidation
ortwo-stagegate. OtherQfresh0depth16 selectionsloseoldskills. Preserveallvariants.
Posthocindependentdeque saveddata:304changedrastersall source-stoppedgoal-distance
balls,80budgetexhausted→emitted,224emitted→emitted;152newcorrect,allcorridors.
Wholewave matches2936→3200/3456,notallcases. Zero newinference;no causaleditclaim.

Main797952physical/812160logicalcalls,133.24candidate seconds/720cap,
78071507543work,164.22swall,1141.39MiBRSS. Profile91776calls/12.35candidate seconds
separate. BFS/A*/bitwave/intact3456reachable+1728NPcorrect. No latencybenchmark.
AuditFIRSTPASS889728exactreplays/905280independentrasters/15552baselines,all240walks/
3840events/240draws/RNG,choices,194source/11input/amendmenthashesand2644priorentries;
206.79swall,1189.19MiBRSS. Use tools/audit_mutation_accessibility.py ifneeded;
original study audit intentionallyretains superseded costrule.20focusedtestspass,
283scopedcollected,NOTfreshfullsuite. Alloldsource/populations/RNGintact.

ExcludeALL191784wholelayouts:187416throughQ+464fixtures+1632softwarefixtures
+320discovery+320validation+1632final. Rhelperexclusions()returnsTHROUGH QONLY;
appendmutation_accessibility_fixtures/mazes.json.gz andmutation_accessibility/
{software_fixtures,discovery,validation,confirmation}/mazes.json.gz. No relabeling
finaldataasvalidation. Nextproposalonly:uniformversusexecution-informedmutation
withnativeobserverparity,sameeditvocabulary/roots/runtime/capacity,freshcontrols,
broadernewvalidationanduntouchedfinal. Do notautomaticallylaunchlongsearch.
See results/mutation_accessibility/next_experiment.md andcompletion.json.
Rcompletionseals269entries;nextprioraudit2913entries(2644throughQ+269R).

Historical checkpoint: **V12Q is complete and independently audited**. Read
`results/shared_prefix.md` and `docs/SHARED_PREFIX_PROGRESS.md` first. Do not repeat
or extend Q, alter frozen source, resume an unchanged search, or train/reselect on
inspected final cases. V12R mutation-accessibility proposal is NOT launched.

Q seed2026101912,fixtures1314. Registration4fafe1c; explicit timing-only amendment
b1b9530 before any research calls (factor2→1.5,16→32generations to cover8poses,
originalprofile retained, no fixture scores used,720s cap unchanged). No frozen
source repair. All choices/populations/RNG/search pushed2ba193d before fresh final.

32matched generations,18conditions×96:carry/fresh×3rep×current/mixed evolution or
mixedresampling. Exactinitialpools/searchRNG matched. Only evolutionarycontrast is
100%source-at-junction versus50/50prefix0/1 stimuli; same runtime/rank/one-edit
mutation/archive/elite/immigration. NineexactO/P/founder/randomresampleanchors are
protected ineachcarryarm; freshfounders288newrandom, never knownsolvers.
41472births=24192mutated+17280random;40176enteredtraining,1296generation32offspring
are SAVED BUT UNQUERIED. Preserveall18nextpopulations/RNG andeveryedit/archive.

Everyprimary0/64validationprefix1pairs and0/128finalcoreprefix1pairs. All31physical
random-origin finalmodels (secondaryarchives/anchorsincluded)0positive-prefixpairs
and0two-junction/cyclepairs. Gate0/3carry,0/3fresh; noextension. Final20seededclutter
contexts,4032inputs:1344branched/1344corridors/1344isolated-goalNP;prefix0/1/2,
8poses,2goals,arms2/3/4/6. Routeformsrepeat;poses/goals/variantscorrelated.78aliases,
32physicalmodelsincludingintactcontrol. No finalreselection or Qmechanismablation.

Finalcoreprefix0pairs /128:allcarryprimaries/frozen128each; freshCurrent[0,96,0],
Mixed[96,64,128],resampling[0,0,16],frozen[0,0,0]. Freshaggregate96/288/16/0 outof384
is SECONDARY junction-onlyevidence,not a targetgatepass. Carryall1344corridors;
freshmixed[1128,1344,1344],freshresample2=464;separatecorridorarchivespreserved.
Allselectedrandom-originfalseNP0; successfulNPcontrols areisolatedgoals only.

Freshmixed0 i1151,114genes,12edits fromfreshfounder95:initialsamevalidation0→32/64
junctionpairs,final96/128 (arms3/4/6all8poses),butcorridorloss. FreshCurrent1 i1146,
96genes,16edits fromfounder22:validation0→48/64,final96/128(sixposes/eacharmlength).
FreshMixed1 i1694,93genes,13edits samefounder22:validation0butfinal64pairs arms4/6.
FreshMixed2 i1480,121genes,13edits fromimmigrant i507:128corepairs+1344corridors+
1344NP. RootALREADYsolvedfirstsampledtrainingjunctionpair; do notclaim13editswere
necessary. CarryMixed0 i1638,94genes,5edits fromnewimmigrant i1152. Unmutated95gene
CarryResample0 i63 matches its160totalpairs(allprefix0forks)/1344corridors/1344NP.

Posthocindependentdequecheck:all2688reachablemasksofFreshMixed2,CarryMixed0 and
95geneResample matchsource-stoppedgoal-distanceballs. Emitted-outputequivalence,
notinternalBFS/causalmechanismidentity. No newcandidatecalls. 4952birthsdescendfrom
Oroute9/16,maxdepth18–32(includinglastunqueriedoffspring);maxborn167genes<256cap.
538/5472samebatchparent-childcomparisonschangemask/status. Mixedsubset18/2823
prefix-scoreimprovements:15improveaggregaterank,3worsen;only2carried. Correlated
co-presencesubset;partialcredit≠solving;aggregaterank≠lexicaseprobability. Neither
selectionalone nor a bindingcapacitylimit is established. Randomtrackremainsopen.

Main1345536physical/2415744logicalcalls,251.23candidate seconds/720cap,
146149776961work;340.27swall,951.48MiBRSS. Profile27648calls/5.14candidate seconds
separate. Audit firstattemptPASS:1373184exactreplays,1385280independentrasters,
12096baselines,all41472births/24192mutations/18states/78aliases,190source/9input/
2384priorhashentries;352.05swall,1047.92MiBRSS. Allbaselines/intact2688reachable+
1344NPcorrect;no latencybenchmark/speedup. 10new+22relatedtestspass,273collected,
NOTfreshfullsuite. Unscopedcollectionhitvendoredtestdeps;scopedcollectionpasses.

ExcludeALL187416wholelayouts:181928throughP+1424uniquepreflight/softwarefixtures
+320validation+2560training(allposes)+1184final. `shared_prefix_data.exclusions()`
returnsTHROUGH P ONLY; append shared_prefix/software_fixtures,shared_prefix_fixtures,
shared_prefix/validation,shared_prefix/train,shared_prefix/confirmation mazes.json.gz.
Nextproposalonly: bounded performance-blind mutation-accessibility assay around
severalpreservedwavegenotypes plusfreshcontrols,newasymmetricmatchedgeometry,
strictnormaloutputconfirmation;no knownsolverinjection/automaticlongsearch.
See `results/shared_prefix/next_experiment.md`. Preserveallprevioussource/results.
Q completion seals260hashentries; next prior audit total2644 (2384throughP+260Q).

Historical checkpoint: **V12P is complete and independently audited**. Read
`results/mutation_transition.md` and `docs/MUTATION_TRANSITION_PROGRESS.md` first.
Do not repeat P, extend its closed cap, alter frozen source, resume closed searches
or train/reselect on inspected final layouts. No mutation/evolution occurred in P.
The shared-prefix curriculum pilot is a proposal only, NOT launched/preregistered.

Protocol/source/panel/fixtures pushedaf823aa BEFORE any panel inference; passing
profile/native parity pushedfa9945b BEFORE final generation. Seed2026101911,
fixtures1304.62 fixed configurations:all17 O routing-walk states underboth
local/nonlocal topologies,reachability founders/checkpoints/descendants,M anchors,
unmutated resample,separateintact.48 actual mutation events reproduced; no edits.

**First useful transition is edit9:** local O `mutation_depth/r0/f71/walk0/d9`,
131genes, versus130-gene depth8. Founder through8 gives0/2080pairs,120/4160corridors;
depths9–16 give544/2080pairs,4160/4160corridors,5280/8320 reachable shortest
outputs,0/4160correctNP,0falseNP. Within0–8 andwithin9–16 all12480 masks/statuses/
ticks match;internal states unrecorded,counters differ. Step9 insertion atzero-based
index112 is `[3,36,49,44,0,0,64]`:R36=max(0,R49−R44). Causal in its actualdepth8
background; original-founder transplant,necessity ofearlieredits,minimality unknown.

Posthoc static certificate: R44 resets0 and has no writer; R49 at the insertion
copies R55 from priorchannel2 cardinal remote-min read. Finalchannel1 storeuses
R36. Thus complete-tickchannel1 receives minimumpositive neighboringchannel2
(radius1 local,radius8 nonlocal),or0. New output feedback,not a knownsolverinjection.
Depth9work624400792 versusdepth16work667128216 onwholecorpus;no latencybenchmark.

**Posthoc emitted-wave diagnosis:** ALL8320 reachable rasters/state equal the
open positions at goal distance≤shortest source-goal distance. ALL4160 disconnected
rasters equal the isolated goal component but are not correct no-path reports.
Independent deque traversal verifies24960savedrasters acrossdepths9/16,zero new
inference. This is output equivalence,not proof ofinternal BFS or oracleaccess.
Static/wave certificates are explicitly post-registration,saved-data diagnostics.

Core fullstem prefix0:256/256pairs; prefixes1/2/4 each0/256. Nostem prefix0:
256/256; sourcespurs at2/4 each0/256. Success atdegree2or3 atjunction; degree3
remotesource doesnotrescue. Arms2/3/4/6,straight/turning,bothstemlabels,all8poses.
Full layout/goals fixed acrosssourcepositions. Bendsdonotrescueprefix4. Fullprefix
contrasts−1 inall16coretemplates;conditionalbootstrapintervalsdegenerate,not
populationcertainty. Stressprefix0fork32/32,otherfork0/64,two-junction0/96,cycle0/96;
truealternatives12edgeslonger.32 additional individualoutputs arenotcompletepairs.
Raw544/2080 includesnostemduplicates:exactinputdedup416/1952.20seededtemplates,
repeatedrouteforms;poses/goals/control variants correlated. No generalmazespeedclaim.

Mechanism subset preselected:routefounder,depth4,depth15,depth16,intact ×2tops.
Localtarget544normal eligible successes: pulseoff544retained,flagoff0,both0,
endpointcheckoff544,nonlocalzero544;zero newlysuccessfulpairs. Staticflagnecessary
for these successes;initialpulse/extraendpointcheck unnecessary underretainedsystem.
Nonlocalzero inert locally. Ordinarynonlocaltarget0pairs/0corridors;nonlocalzero
rescues0pairs. Radiusredirection≠zeroing. No beneficialmultirange evidence,forced
traces or stoppingretune. Nonlocal normaldenominator0 precludesnecessityinference.

O reachabilitydescendantsr1/f53/walk0/d16 andr2/f69/walk1/d16 each4160corridors+
4160NP,0pairs,0falseNP underboth tops. r1founder/1/4:0corr/0NP. r2founder/1/4:
1040corr/4160NP but4768falseNP. NPgoalsisolated. Oresample0pairs/0corr inP's
no-adjacentcorpus;preserveitsoldskill. Intact/BFS/A*/bitwave8320reachable+4160NP.

Fixtures10templates/6240inputs/1232layouts;final20templates/12480inputs/2464layouts,
19×19,all8poses. Main904960calls=773760normal+131200probes,116.324837candidate
seconds/720cap,67248915826work,143.02wall,846.08MiBRSS. Profile72680calls/
12.73candidate seconds separately. Audit PASSES first attempt:175.99wall,1078MiBRSS,
977640exactcandidate replays,1015080independentrasters,37440baseline replays,
16120nativeparity,10800oldV6adapterparity,112summaries,48mutationevents,
186source/11input/2140priorcompletion hashes. No frozen-sourcerepair/deviation.
22focusedtests pass(11new+11O);263collected,NOTfullsuite. Initial preregistration
unit-test expectation8→12 corrected before freeze,unchangedgeometry,0candidatecalls.

Exclude ALL181928wholelayouts:178232throughO +1232fixtures +2464final.
`mutation_transition_data.exclusions()` returns THROUGH O ONLY; append BOTH
`results/mutation_transition_fixtures/mazes.json.gz` and
`results/mutation_transition/confirmation/mazes.json.gz`. Preserveallprior
populations/RNG/source/results. Never relabelfinalsasvalidation.

Next proposal only:bounded12-minute shared-prefix curriculum pilot,exactinitial
pool/RNG matchedacrosscurriculumarms,runtime/capacity/scoringfixed,protected
routing/corridordiversity,separatefresh-random track,resampling/frozencontrols,
3searchRNGreplicates. Conditionalcarried-lineageevolvability,not an O gatepass.
Commonbroader validation,freezechoicesbeforefreshfinal,strictgain/retention gate;
no automatic60–90-minute extension or human-codedtraceback. See
`results/mutation_transition/next_experiment.md`.

Historical checkpoint: **V12O is complete and independently audited**. Read
`results/mutation_depth.md` and `docs/MUTATION_DEPTH_PROGRESS.md` first. Do not
repeat O, extend its closed cap, alter frozen source, resume old runs or
train/reselect on final cases. The broad discovery gate fails; no evolution
pilot launched. The targeted lineage/transfer follow-up is now complete as V12P.

Protocol/source/pools/fixtures pushed in f08484c BEFORE any candidate inference;
all discovery/validation evidence and choices pushed in 21d5bfb BEFORE final
generation. Seed2026101910; fixtures1294. Three original M groups of96 founders;
two performance-blind16-edit walks/founder queried at1/4/16, plus two independent
one-edit children and two random draws. Each terminal arm192/group. Totals:
3168 evaluated identities,6246 physical local/nonlocal configs,576 walks,
9792 mutation events,576 random draws. Every intermediate genome and replayable
RNG state saved. No known solver injection, breeding or performance feedback
between edits. All-on M runtime/pulse/limits fixed; exposure bits inert.

**New positive lineage:** local `mutation_depth/r0/f71/walk0/d16`,137 genes,
descends from original random M `exposure/fresh/0/founder71`,128 genes. Untouched
final gives96/160 complete shortest pairs:32 adjacent +64 non-adjacent, plus
320/320 corridors and512/640 reachable shortest outputs. Non-adjacent successes:
32 two-edge-arm +32 three-edge-arm pairs, straight/turning forms,8 clutter
contexts of4 route-shape types, all8 poses. Founder and SAME WALK depths1/4 each
0pairs and32corridors; all960 early masks match founder, but counters differ.
Skill is present by16 and absent at4; first causal edit and necessity of16 edits
are unknown. Immediate parent15 is saved but NOT queried. Preserve all17 states.

Both shared-prefix fork classes fail. Each has ONE shared edge and total route
length2 or3. Source degree/branch/tail geometry also differ, so failure is not
an isolated causal prefix diagnosis. Target0/320correct no-path,0false claims.
No new mechanism ablations. General solving, useful multirange and speedup remain
unestablished. On DISCOVERY, same target local32nonadjpairs/160corridors versus
nonlocal0/0; selection evidence only. Final nonlocal choice is a different genome.

Only1 useful new response in discovery, group0/local/depth16:one founder/behavior.
Its final-transfer gate PASSES, discovery gate FAILS (requires4useful,2founders/
behaviors,2more than EACH depth1/single/resample control). Every combined gate
fails; no depth/topology qualifies2/3. Do not reinterpret this as evolutionary
readiness. Local changed masks at depths1/4/16 are[2,3,2]/[14,13,8]/[41,37,25]
per192 candidates; more changed outputs do not imply useful solving. Median
lengths96/97/105, deepest64–169; none reaches256-gene ceiling.

Other selected choices0nonadjpairs. Group2 unmutated resample gives32adjpairs
and64corridors inboth topologies; preserve it. Two separate depth16 descendants,
`mutation_depth/r1/f53/walk0/d16` and `mutation_depth/r2/f69/walk1/d16`, each give
320corridors+320correct no-path and0pairs underboth topologies. Group1 founder
0corridors/0NP; group2 founder80corridors/320NP but432falseNP onreachable.
All30 selected choices0falseNP. Disconnected goals are isolated clutter cells;
these are limited reachability gains, not general no-path recognition.

Scientific stages query all8poses. Discovery/validation10 contexts each,480
inputs/80pairs; final20 contexts,960 inputs/160pairs,320corridors,320no-path.
Small9×9 tree grammar, repeated route forms; no cycles/general maze test. Poses,
goals, variants, walks/depths correlated. IntactVM/BFS/A*/bitwave each solve
640reachable+320disconnected. No latency benchmark.

Main349.14candidate seconds/720cap,3100320calls,203251399805work; wall414.93s,
1249.61MiB peakRSS. Profile separate374760calls/42.45candidate seconds. Audit
PASSES first attempt:495.57s wall,1454.14MiB RSS,3475080 exactcandidate replays,
3477960 independently graded rasters,2880baseline replays,all9792events/576walks,
6397model summaries,5760nominee ranks,30choices,181source/12input/1883prior
completion hashes. No source repair or protocol deviation.22distinct focused
tests covered (11new+11N);252collected,NOT a fresh full suite.

Exclude ALL178232 whole layouts:177032throughN +240fixtures +240discovery
+240validation +480final. `mutation_depth_data.exclusions()` returns throughN
ONLY; add `mazes.json.gz` from `results/mutation_depth_fixtures/` and
`results/mutation_depth/{discovery,validation,confirmation}/`, including all poses.
All old populations/RNG and completion packets remain intact.

Next proposal only:freeze all17 saved target states, reachability lineages and
controls; use a new matched corpus to localize the first useful transition and
separate source prefix/degree/bends from downstream arm geometry. Normal successes
precede preselected pulse/flag/endpoint/nonlocal probes. At most12candidate
minutes after fixture profiling; no automatic60–90min evolution extension.
See `results/mutation_depth/next_experiment.md`.

Historical checkpoint: **V12N is complete and independently audited**. Read
`results/branch_pressure_calibration.md` and `docs/BRANCH_PRESSURE_CALIBRATION_PROGRESS.md`.
Do not rerun/extend N, resume old closed runs or train/reselect on its final cases.
All calibration/final readiness gates FAIL; NO evolution pilot launched. The
cumulative-mutation/full-orientation follow-up is now completed as V12O above.

Protocol/source/pools/fixtures pushed74fcc24 BEFORE anycandidatecall;12validation
choices/evidence pushed8bbf2cf BEFORE finalgeneration. Seed2026101909,fixtures1284.
Three original M96-founder groups +2independentone-edit children/founder:864ids,
576events,1662physical local/nonlocal configurations. Exposurebitsunchanged/inert;
all-onM runtime/goalpulse/limits,capacity256. SameevidenceandRNGforbothpressures.
Mvalidation-selected anchors protected equally. No breeding orknownsolverinjection.

Choiceproxy measures appropriate change on exclusiveINTERIORgoalarms excluding
bothgoalmarkers/sharedcells, timesweakerpathF1. Ordinaryemissiononly. Insertedafter
completepairs andbeforeindividual/corridor counts. Currentproxy0 reproducesM.
Cal/val10new9×9contexts each,evenposes0/2/4/6:240inputs,40pairs. Final30contexts,
all8poses:1440inputs,240pairs(48adjacent/192nonadjacent),480corr/480NP. Fivekindsof
adjacent/two-/three-edge arms/sharedprefixforks×2shapes,isolatedclutter. Treegrammar
only;routeformsrepeat,poses/controls correlated. All8poses saved/excluded.

Everycalcandidateproxy0,strict-both0,nonadjpairs0. All6cohorts0/64parentchanges,
sameelites/nominees;activationfails. Finalsamechoices underbothpressures:group0
local12adjacentpairs,0nonadj,.03125proxy,108corr;nonlocal12adjacent,0nonadj,
.0023148148proxy,12corr. Other4cohorts0pairs/0proxy,480corr. AllNP0,nofalseNP.
IntactVM/BFS/A*/bitwave solve960reachable+480disconnected. No speedclaim.

Group0selected `branch_pressure/r0/f81/edit1` is GENOTYPE IDENTICAL to Mfounder81,
96genes;ineffectiveedit,tie-breakalias,notnewdiscovery. All1440finalmasks matchparent.
Localpositivepartials:12pairs on3turning2-edge contexts atposes1/3/5/7(score.375).
Nonlocal:2poses(3/7)ofone3-edgecontext(score1/6). Strict-both0,nonadjcomplete0.
**Calibrationomittedquarter-turnposes**. Thiscoverageflawpreventsclaimingnopositive
responseanywhere;finalpartialsarenotnewselectionevidence orpressureadvantage.

543/576mutationschangegenotype (groups184/179/180of192),butmask-changingchildren
local/nonlocal=5/5,2/1,2/2. Counters/stepschange127/128,116/116,121/123:computation
changesmoreoften thanoutput;doNOTinferinactivegenes/hiddenstateequivalence.
Somecalgoalswitchawayfrommarkers(5/8,6/6,0/0candidates/288)hasnegativeinterior
contrast;allpositive0. Ndoesnottestcumulativeedits/longerevolution/largercapacity.

Main49.423candidate seconds,426960calls,28906147288work;cal+val47.843/480s,
final1.580/200s.1512MiBpeakRSS. Profile1440calls/.182s separate;timinggatepassed.
AuditfirstattemptPASSES71.303s/1742.88MiB:428400candidate replays,432720independent
rastergrades,4320baselines,576events/RNG,768parentdraws,3456ranks,12choices,
2880graphcases,177source/10inputhashes,1641priorcompletionentries. No sourcerepair/
protocoldeviation.21focusedtests(11new+10M),241collected,NOTfreshfullsuite.
Initialunscopedcollectionfailedonoptionalplot-librarytests;scopedcollectionpasses.

Exclude177032wholelayouts:175592throughM+240Nfixtures+240cal+240val+720final.
`branch_pressure_data.exclusions()`returnsTHROUGH M ONLY;addmazes.json.gzfromN
fixtures/calibration/validation/confirmation,includingunqueriedposes.
Nextproposal: boundedcumulativemutation/full8poseassay with equal-budget one-edit/
resamplingcontrols,allintermediates/RNGandanchorspreserved. Thenchoosebetween
shortdiversity-preservingevolution oraspecificexpression/emissionmechanismtest.
Noauto60–90min;normalnonadjpairedgains2/3evolutionreplicates+retentionstillrequired.

Historical checkpoint: **V12M is complete and independently audited**. Read
`results/exposure_calibration.md` and `docs/EXPOSURE_CALIBRATION_PROGRESS.md` first.
Do not repeat/extend M, resume older closed runs, or train/reselect on M final cases.
Its proposed branch-pressure calibration is completed as V12N above.

Inherited radii2/4/8 bits are implemented with exact all-on/all-off parity and
charged exposure checks. Static suppression, not dynamic regulation. Sixteen
carried fixed neighborhoods (8 mask states +8 sampled one-edit siblings each),
3×96 fresh random founders, active/neutral/zero/local controls; no evolution.
All pools/protocol pushed b85c25e before generation; 76 choices/evidence pushed
e5fdf70 before final. Seed2026101908, fixtures1274. Equal logical budgets and
physical dedup aliases preserved. No known-solver injection.

Carried readiness gate FAILS: broad SAME-program active32→48pairs/144 and
64→96corridors; narrow34→48pairs,64→96corridors. No losses, but broad gains only
on two straight-goal templates, failing required goal-form breadth. Both selected
active programs match ALL480 all-zero masks. Nonzero retained bits do not prove
useful nonlocal input. Broad/narrow parent draws change47/55 of64. K2 retains
24pairs/96corridors;68gene draw12/96. Local exception0pairs/44corridors; its paired
retention is vacuous. All selected prefix4/8pairs0. No carried scale-up.

Fresh numerical partial-gradient screen PASSES3/3, with46/47/27 of64 parent draws
changed. Preserve that preregistered result. But saved-output diagnosis shows all
three neutral selections fill the entire source component on384/384paired inputs,
with identical masks for both goals on192/192pairs. They score.30partial, solve
384corridors and ZERO pairs. Active/zero match this behavior. These are unmutated
random founders (89/123/84genes), not evolved discoveries. Local group0 founder81,
96genes, gives16adjacent pairs on4templates×4poses,128corridors,0two-edge pairs.
Preserve it. This diagnoses objective weakness; capacity/time hypotheses stay open.

All selected random models fail explicit no-path, no false reachable no-path claims;
all legal selected outputs shortest. IntactVM/BFS/A*/bitwave solve1152reachable+
480disconnected final cases. Main317.580candidate seconds,313464calls,
189375425715work; selection233.838/480s andfinal83.742/300s. PeakRSS1387.59MiB.
Original timing preflight failed450.301>432s; BEFORE registration/main generation,
carry calibration reduced4→2poses (no extra calls/score tuning); revised303.423passes.
Original failed record retained. No postregistration deviation/frozen-source repair.

Audit PASSES first attempt451.514s/1702.05MiB:390900candidate replays,
395796independent raster grades,4896baselines,3276adapter comparisons,128mutations,
288founders,9728parentdraws,152selectionrecords,76choices,8256graphcases;
173source/16input hashes and1390prior completion entries. Ten new+16related focused
tests covered;230collected, NOT a fresh full suite. All evidence/RNG preserved.

Exclude175592whole layouts:170840throughL+1008fixtures+1008cal+1008val+1728final.
`exposure_data.exclusions()` returns THROUGH L ONLY; also add `all_manifests()`
for `results/exposure_calibration_fixtures` and M calibration/validation/confirmation.
Next proposal: prospective goal-conditioned branch-exclusion pressure preflight,
then only if ordinary choice progress/selection activate, bounded matched12min
pilot with controls and preserved diversity. Exposure fixed between pressure arms.
Require2/3 normal nonadjacent paired gains+retention before60–90min. See next proposal.

Historical checkpoint: **V12L is complete and independently audited**. Read
`results/lineage_confirmation.md` and `docs/LINEAGE_CONFIRMATION_PROGRESS.md` first.
Do not repeat/extend L, resume G–K, or train/reselect on inspected L confirmation.
Its proposed heritable-exposure calibration is now completed as V12M above.

Protocol/source/22fixed K-informed models/fixtures pushed09422ee BEFORE main
case generation. Seed2026101907,fixtures1264. No evolution,genomeediting,reselection
orforcedtraces. Old14panel retained plus K1/K2target,parent,Gentry,frozencontrol;
identical Context genome aliases and full5/16edit ancestry preserved.

36independent25×25templates,3goalshapes(straight/symmetric/asymmetric)×6prefix/
sourceforms×2tailbands. Each has exact centered/offcenter graph+cluttertranslations,
8poses,2goals,fork/two-junction/realalternativecycle,corridors,disconnectedcontrols.
5760inputs/model:1728branchpairs,1152corridors,1152no-path. Translations/poses/graphs
are correlated. All22models have exacttranslatednormalmasks on2880comparisons;
this limited translation invariance is not arbitrary geometry generalization.

K2i1089,256genes,birth16,16edits fromentryGBranchr2i8103:192pairs vsentry0,frozen24;
all12short-prefixforktemplates work inall8poses/bothlocations,all3goalshapes,max11
edges;1152/1152corridors. Parenti1040 same5760masks/statuses/steps buttarget saves
4,404,576localreads;no last-editcorrectnessgain or hidden-stateequivalence claim.
K2zero prefix4/8,extra-junction/cyclepairs. K1i458,5edits fromentryi2826:12pairs
vsparent0,entry16;entrycomparison gains8,loses12,retains4;corridors52vs60. One
shortstraightgoaltemplate,two poses,bothlocations,all3graphs,max6edges;noallpose.
K1successfulpairs outside fixedmechanismsubset,so necessity is untested there.

Mechanisms:all22models,9fixedlong-tailtemplates (3goalshapes×prefix1straight,
2straight,8bent),1440inputs/432pairs pervariant;normalfirst thenpulseoff,flagoff,
endpointcheckoff,nonlocalzero,chargedreadsretained. K2normal96pairs/288corridors;
flagoff0/0,all1440maskschanged. Other3removals retainall1440masks/96pairs/288corridors,
thoughpulse/nonlocal changework. No beneficialmultirangedependence. Localexception's
12probepairs needpulse+endpointcheck,notflag. BroadBranch112→192nonlocalzeropairs,
204→288corridors,4netpositivetemplates/all3goalshapes,no pair/corridorloss;parent
repeats butrelated. Narrow128→192pairs,200→288corridors,only2straighttemplates,
failsscreen. Normalfarprobesuccesses0forboth:retentionvacuous. BothprimaryLgate
conditions pass (K2normal+oldbroadrescue);onlyseparatecalibrationrecommended.

Oldnarrow324pairs(164fork/80two/80cycle),broad288(128/80/80). Narrow+parent4prefix4
pairs,replacement4,local_long8(maxpaired12edges). ALLrandom0prefix8pairs.68gene
unmutateddraw96forkpairs/6templates(allprefix1),1152corridors;fresh_evolved16fork
pairs/1allpose-template;otherfreshcontrols0. Allrandom0/1152no-path,nofalsereachable
no-pathclaims,alllegalnormaloutputsshortest. BFS/A*/bitwave/intact4608/4608reachable
+1152/1152disconnected. No latencybenchmark/general-solver/multirangeclaim.

Main448.482candidate seconds/720cap,253440calls,267047037936work,457.149swall,
662.16MiBRSS. Actual25×25profile452.62s;calibrationseparate61.254s/34848calls.
AuditPASSEDfirstattempt532.999s/1044.23MiBRSS:288288candidate replays,303984rasters,
17280baselines,1584adapterparity,21mutations,11520regeneratedgraphcases,166source/
9input/19panel-source hashes,1187priorG/H/I/J/Kcompletionentries unchanged.8new+
17relatedtestspass;220collected,NOTfullsuite. No frozen-sourcerepair/deviation.

Exclude **170,840 whole layouts** next:163928throughK+3456Lfixtures+3456Lmain.
`lineage_confirmation_data.exclusions()` returns throughK ONLY: append BOTH
`lineage_confirmation_fixtures/mazes.json.gz` and
`lineage_confirmation/confirmation/mazes.json.gz` underresults toreach170840.
Tests reusedsavedfixtures;noadditionalunitgeometry. Keep alloldpopulation/RNG.

Nextproposalonly:`results/lineage_confirmation/next_experiment.md`:minimal3bit
heritableexposure(radii2/4/8),all-on/old andall-off/zero parity,neutralmetadataand
matchedmutationopportunities,fixedzero/localcontrols. Staticinheritedsuppression
isnotdynamicregulation orbeneficialmultirange. Calibrate performanceblind
neighborhoods/actualreproductiveselection onNEWcases beforeboundedpilot. Fresh
origin needsnewadjacent/twoedgepairedtasks andmeasurablepressure;2/3replicate
holdoutgates+exactskillretentionbefore60–90min. No additional experiment launched.

Historical checkpoint: **V12K is complete and independently audited**. Read
`results/robustness_pressure.md` and `docs/ROBUSTNESS_PRESSURE_PROGRESS.md` first.
Do not repeat/extend K, resume G–J, or train/reselect on inspected K final data.
The new-lineage confirmation/heritable-exposure follow-up is a proposal only.

Preregistration/foundations/panel pushed b1eee27 before main generation; all final
selections/populations/RNG pushed3ff220c BEFORE final generation. Seed2026101906,
fixtures1254. Thirty conditions: carry/fresh × local/evolved × Pair/Context ×3reps,
plus fresh resampling;96organisms,256genes,24elites,72births,9immigrants,single-edit,
unchanged V6 pulse runtime. New copies of G Branchgen113 states with same protected
anchors and same-condition I nominees (13–18); no old run resumed or known solver
injected. Fresh random founders; fourteen unchanged J-informed diagnostic controls.
Pair is paired-count-first, not G Current's valid-first breeding policy.

Two training contexts/batch, straight/turning goals, four poses each, two goals,
matched corridors:20calls/organism. Common validation:4contexts/rep,8poses,3graphs,
208inputs. Both policies have identical context/pair/corridor/far archives and
nomination counts. Context adds all-queried-pose completeness ahead of pair count.
23matched generations in688.973s wall/720cap,599.375candidate seconds,
1,639,296physical calls/1,998,720logical calls(66,624percondition),
354,415,967,905work,978.25MiBRSS. Initial screen119.447s included. No partial round
or extension. All checkpoints/RNG, masks, counters and mutations preserved.

Final24 independent21x21contexts, both goal shapes, prefixes1/2/4straight+ bent/
8straight+bent, short/long tails,8poses,2goals; matched fork/two-junction/realcycle,
corridors/disconnected.1920inputs/model=576branchpairs+384corridors+384nopath.
Variants/poses correlated; prefix strata also vary geometry.37physical models.
Primary pair counts byrep /576, Pair and Context IDENTICAL:
carry/local[64,0,8], frozen[64,0,8];carry/evolved[98,6,64], frozen[98,0,10];
freshlocal/evolved all[0,0,0], also frozen/resampling. All cohorts0/3expansiongate.
Tenof12 paired searches keep identical ordered genotypes/RNG throughout. Only
carry/localrep0(fromg8),rep2(fromg0)diverge; global maximal rank-genotype sets never
differ. Fresh candidates complete ZERO queried training pairs throughout, so new
pressure has no paired-skill gradient there. Do not interpret this as12distinct
negative treatment responses or closure of fresh random-origin discovery.

New useful descendant carry/evolved/Pairrep2i1089(256genes,birth/selection16),
identical Context alias:16mutations from G Branchrep2i8103. Entry has0/208correct
K validation outputs; descendant16validationpairs,64finalpairs. Eightforkcontexts
(prefix1/2,bothgoalshapes,bothtailbands)all8poses, routes up to11edges;384/384corridors
vs356frozen. Zeroextra-junction/cycle orprefix4/8pairs. Entry ancestor NOT on final:
10→64 compares frozenSELECTED initial, not directancestor. No new mechanism tests
on this descendant. Rep1i458(256genes,birth7,selection8,5steps fromGi2826)has6pairs:
two poses ofoneprefix2context across3graphs, noall8;corridors8→26.
Localrep0 pair-archive secondaries46pairs/0allpose/362corridors vsprimary64/8/384;
preserve, do not replace primary based on final. All random0/384nopath,no false
reachable no-path,alllegalshortest. BFS/A*/bitwave/intact1536reachable+384nopath.
No new latency benchmark, general solver or speedup.

Separate fixed diagnostic24contexts:53760calls,93.345candidate seconds/180cap,
normal/nonlocal-zero charged equally. Broad Branch88→128pairs,276→384corridors,
four positivecontexts,bothgoalshapes,six newlyallposegroups; passesrescuegate.
Itsparentdoeslikewise, not independentlineage replication. Narrow96→128,
256→384corridors, onlytwo straight-goalcontexts;failsscreen. Both0prefix4/8pairs
underbothconfigs, sofarretentionvacuous. Long-prefix/localcontrols retain8/3far
pairs. FinalnormaloldBranch98/90pairsincludes2far each;NOzeroingonfinal. No causal
multirange benefit or evolved gate. Actualdiagnostic93.345s vs47.390s projection
from13x13fixtures: profile actual board sizes next. Final71040calls67.274s/360cap.

Audit firstattempt PASS:1,774,976candidate replays,1,786,496rasters,67,752fitness,
34,776mutations,49,680births,all30states/RNG,11,520baselines;162source/11inputhashes,
889priorG/H/I/Jcompletionentries.908.199s wall,1941.23MiBRSS separately.
Supplemental12.285saudit regenerates15840maincases and checkscoverage/120aliases.
No frozen-source repair/deviation.29focusedpasses(8K+9J+12G),212collected,NOTfullsuite.

Exclude **163,928 whole layouts**:150776throughJ+384Kscientificfixtures+
3264additionalunitgeometry+1152diagnostic+7200search/validation+1152final.
`robustness_data.exclusions()` returns throughJ ONLY. Add
`robustness_pressure_fixtures/mazes.json.gz`, `geometry_test_mazes.json.gz` in that
same directory, and `robustness_pressure/{diagnostic,search,final}/mazes.json.gz`.
No relabeling finals as freshvalidation. Next proposal ONLY in
`results/robustness_pressure/next_experiment.md`: independently confirm new
lineage/parents/mechanisms, then calibrate bounded heritable nonlocal exposure
versus fixed/zero controls; fresh elementary paired-task gradient calibration.
Preserve random origins, diversity, actual-size profiling and measurable treatment
activation before another pilot. No unchanged60–90minrun.

Historical checkpoint: **V12J is complete and independently audited**. Read
`results/junction_distance.md` and `docs/JUNCTION_DISTANCE_PROGRESS.md` first.
Do not repeat J, extend its closed720s cap, resume G/H/I, train or reselect on
inspected J final cases. The robustness-pressure follow-up is completed as V12K above.

Protocol/panel/fixtures/source frozen and pushed in e4ca508 BEFORE main generation.
Seed2026101905; fixtures1244. Thirteen fixed random-origin genomes + separate
intact control; no evolution or editing. Strong narrow/broad Branch i5140/i7406,
parents i5076/i7327, shared E ancestor i108890, narrow longer-prefix i4596 and broad
i5708, inherited local i114696, local i5138, fresh evolved i2653, fresh local i8001
and founder i69, unmutated68-gene resampling i4469. All prior states/RNG preserved.

Twelve independent25x25contexts,8poses,2goals; first-junction prefixes1/2/4/6/8,
straight/bent, fixed downstream goals/arms/clutter. Source always an endpoint.
Fork, extra dead end at2/4along goal arm, true opposite-arm cycles at2/4,
2corridors and disconnected control. Cycle-distance contrasts ALSO alter
alternative length/open-cell count. Restricted orthogonal grammar. Prefix1/2
shape labels intentionally duplicate inputs. Per model13,440inputs:9,600branched
(4,800protocolpairs;3,840unique inputpairs),1,920corridors,1,920no-path.

Normal pairs /4800: shared ancestor288;resampling192;broad Currenti5708 164;
inherited local145;narrow Branch74;itsparent74;broad Branch50;itsparent50;
other five random models0;intact4800. Ancestor288=96fork+96two_2+96cycle_2,
allprefix1,halfposes. Narrow74=58fork+8two_2+8cycle_2; broad50=42+4+4.
All random models0two_4/cycle_4 pairs. No random transfer-gate passes.
Narrow/broad masks/status/steps match their immediate parents on all13,440normal
inputs. Narrow recorded counters also identical; broad child costs more dispatch,
active instructions and array bytes. No claim of identical hidden state.

Inherited locali114696 completes8prefix8forkpairs on6contexts, straight only,
paired17/17-edge routes possible, noneall8poses. Narrow/broad each6prefix8forkpairs
on2contexts, bent only, pairedroutes up to15edges. These are newly evaluated old
genomes, not J evolutionary gains. Local loses bentprefix4+; simple distance
ceiling falsified, but robust solving unestablished. Resampling all12prefix1fork
contexts/all8poses;zero atprefix2+. Only resampling passes descriptive distance-
failure screen; other near baselines too weak. No direct G/H/I/J causal scorechange.

Fixed mechanism subset:9targets,first2contexts,1,600branched inputs/mode/model.
Locali114696 normal27pairs: pulse-off0,flag-off27,endpoint-off0,nonlocal-off27.
Resampling32pairs: pulse-off32,flag-off0,endpoint-off32,nonlocal-off32.
Narrow/broad normal0on THESE2contexts;nonlocal-zero rescues128pairs each
(64unique), all8poses:prefix1fork/two_2/cycle_2 +prefix2fork;noneprefix4+or
attachment4. Reads stay charged. This is context-specific harmful nonlocal
interference, not beneficial multirange causality or general solving. Pulse/flag
probes on failing Branch normals cannot establish necessity for successes elsewhere.
Shared ancestor was outside mechanism subset; no post-hoc extra probes.

Trace subset1context,2poses,3prefixlevels,3graphs,2shapes,4signalmodes;2592traces
all64ticks. Fresh local has9normal-failing inputs with12later shortest frames,
including2paired configurations with simultaneous shortest frames; NOT normal
solutions. No stopping retune. Branch targets0shortestframes. Both signals off
makes paired full trajectories identical. Local source/junction responses12/36,
36/36 disappearpulse-off,remainflag-off. Resampling source/junction0 despite
normalpairs: internal response proxy is not a universal requirement for correctness.

All normal legal outputs shortest. All random models0/1920correct no-path;
no false reachable no-path. BFS/A*/bitwave/intact11520/11520reachable +1920/1920
no-path. No J latency benchmark, no speedup, no general solver.

Main624.699candidate seconds/720cap,277152calls,371500676156work;wall647.136s,
815.02MiBRSS. Calibration2318calls2.728candidate seconds separately. Rough388s
projection overweighted fast control; next profiling must weight per-model calls.
Audit first attempt PASS:658.499s wall,1115.88MiBRSS,279470response replays,
319790terminalrasterchecks including40320baselines,2664fulltraces includingfixtures,
170496frames;165888mainframes additionally graded;1296independent observer,
112native parity,435emission matches.157source/8registrationinput/8panelsource/
3maininput hashes;692oldG/H/Icompletion entries unchanged. No frozen-source repair
or protocol deviation.9new+19related tests pass;204collected,NOTfullsuite.

Exclude **150,776 whole layouts** through J:144120throughI+512Jfixtures+6144Jmain.
`junction_distance_data.exclusions()` returns144120throughI; future code must ALSO
add `junction_distance_fixtures/mazes.json.gz` and
`junction_distance/confirmation/mazes.json.gz`. Saved raw masks, trajectories,
ancestry, parent diffs and success certificates remain intact.

Next proposal only: `results/junction_distance/next_experiment.md`. Calibrate NEW
balanced shapes and useful near controls; preserve local pulse/flag-based/random
resampling/ancestor diversity. Compare ONE context-consistency selection change
against current policy with identical cases/calls/capacity/mutation; keep fresh
random-origin arms, resampling and frozen controls. Independently validate
nonlocal rescue before proposing a heritable gate. Do not combine new runtime
and new pressure into one uninterpretable test or launch unchanged60–90minsearch.

Historical checkpoint: **V12I is complete and audited**. Read
`results/validation_breadth.md` and this handoff first. Do not repeat I, extend
its closed cap, resume G/H, train or reselect on inspected I final cases.
The junction-distance follow-up is now completed as V12J above.

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

Historical checkpoint (October 19, 2026): **V12H is complete**. Read
`results/routing_transfer.md` and `docs/ROUTING_TRANSFER_PROGRESS.md` first.
Do not repeat H, extend its closed cap, resume G, or tune on inspected final
cases. H proposed the validation-breadth follow-up now completed as I above.

All 30 G primary + 30 frozen aliases (33 physical random-origin models), plus
2 separate known controls, were frozen/pushed in e5e30e8 BEFORE final generation.
No training or reselection. Seed 2026101903, fixtures 1224. There are 48 independent
contexts, 24 per 5–9/10–18-edge band, each with 8 poses, 2 goals and matched
fork/two-junction/real alternative-cycle graphs: 2,304 branched inputs/1,152 pairs,
768 corridors and 128 no-path controls. Variants/poses are correlated. Prefixes
4–8 versus G≤3, 25×25 boards and new geometry prevent a single-variable
interpretation of G-to-H failure.

G leader fork/carry/evolved/branch/evolution/0/i4549 gives 0/2,304 legal/shortest
branched outputs, 0/1,152 pairs, 690/768 corridors. All 1,152 short branched masks
have branch/cycle defects. G's 68-gene resampling winner gives zero branched
outputs, 768/768 corridors. Only one physical random-origin model completes
pairs: inherited V12E foundation_pair_paired/local/fresh/evolution/1/i109169,
256 genes, birth 1299, G carry/local Current/frozen replicate1. Fork 17/384,
two-junction 15/384, cycle 3/384 pairs; individual shortest 86/768, 69/768, 13/768.
Contexts 6/5/1, none in all eight poses; all paired routes have 5–6 edges. Cycle
pairs are three poses of ONE six/six-edge context with 18/18-edge alternatives.
Every model completes zero long-band pairs; every Branch cohort fails 0/3.
Do not claim a new G evolutionary gain. BFS/A*/bit-wavefront/intact VM solve
3,072/3,072 reachable and 128/128 disconnected inputs. No false normal reachable
no-path claims. General solving and multirange advantage remain unestablished.

Four preselected random-origin mechanism targets plus two controls receive six
interventions on all 2,304 branched inputs. G leader goal-switch source/junction/
output-away responses are 48/36/48 of 48 probed pairs; pulse removal retains them,
flag removal eliminates all three. Full flag-off states still differ at the goal
pulse; both-off forced trajectories are identical. Endpoint-check removal keeps
all 2,304 G-leader reactions identical; pulse removal keeps masks but changes work.
Nonlocal zeroing changes 334 masks and still gives zero correct routes. These
targets fail H normal pairs: the ablations do not establish necessity for G
successes. The successful inherited local H variant was outside the mechanism
subset and was not newly probed after H. All 1,536 forced traces reach 64 ticks,
98,304 frames; no strict-both or two-goal shortest geometry occurs. Fresh local
has 13 normal-input shortest frames after incorrect native emission, 36 pulse-off
and two both-off frames. These are not normal solutions; no stopping retune.

Inference 152.76s/600s cap, total 164.60s, 596.84 MiB RSS, 201,083 calls and
89,746,284,052 work units. The 71 successful timing cases are median 112.91× slower
than BFS (range 11.42–304.01); no speedup. Audit 166.61s, 612.88 MiB RSS verifies
149 source/41 input hashes, 194,944 normal/intervention replays, 1,536 full traces,
768 independent observer checks, 420 native parity checks, 9,600 final baselines,
and all calibration/timing/graph checks. The first audit failed only serializing
a NumPy count after all checks; original source remains. Active entry point
`tools/audit_routing_transfer.py` casts that count to a Python int. Full rerun
passes; failed log/partial packet and approximately 166.68s additional wall time
are preserved. Nine new protocol tests + eight existing tests pass; one audit
regression passes separately. 185 collected tests; NOT a fresh full-suite run.
All previous populations/RNG/source/results remain intact.

Exclude **all 138,712 whole layouts** through H (136,536 old + 192 fixtures + 1,984
final), including every pose and matched control. Do not relabel H final data as
validation. Next proposal: freeze the existing G validation-nominee pool, compare
new equal-budget narrow/broad validation, freeze choices, then use another
untouched final set. Preserve fresh/carry random origins, resampling, local/evolved
controls and useful diversity. Do not automatically launch another unchanged
60–90-minute evolution run.

Historical checkpoint V12G (October 19, 2026): V12G is complete. Read
`results/fork_pressure.md` and `docs/FORK_PRESSURE_PROGRESS.md` first. Do not
repeat or extend its closed 720-second pilot. All 30 next populations/RNG,
raw masks, concrete mutation events, anchors and primary/secondary archives
are preserved under `results/fork_pressure/`.

V12G compares carry/fresh × local/evolved × Current/Branch × 3 replicates,
plus fresh resampling controls, 96 organisms each. Carry uses V12E Current
populations/RNG at generation 1365, with 9–15 C/D/E validation-selected anchors
protected equally. Fresh founders are random, never known solvers. Capacity,
V6 pulse runtime, single-edit mutation and common archive/elite rules are fixed.
113 matched generations finish in 706.51 seconds (11.78 minutes), including
initial validation; 2,236,032 responses, 269,773,599,386 work, 927.14 MiB peak RSS.
Preregistration is 83f78c6. All selections were frozen/pushed in f1b6bf9 BEFORE
fresh final generation. Seed 2026101902, construction seed 1214.

Final corpus: 24 base forks × 8 poses × 2 goals = 384 inputs/192 pairs, 384
matched pruned corridor inputs and 128 disconnected inputs. Stage lengths
2–4/3–7/5–10 edges; stage 2 and 21×21 boards are untrained. Cycles are dangling
loops, NOT alternative source-to-goal paths. Eight shared isolated clutter
cells diversify layouts but need not be computationally neutral. Route shapes
can recur. Corridors on different layouts are NOT goal-switch pairs.

Primary complete-pair totals /576 across three replicates:
carry/local Current150 Branch128 frozen146;
carry/evolved Current146 Branch216 frozen124;
fresh/local Current2 Branch6 resampling2 frozen0;
fresh/evolved Current0 Branch8 resampling32 frozen0.
Carry/evolved Branch replicates [128,24,64] versus Current [28,72,46]. Best
`fork/carry/evolved/branch/evolution/0/i4549` (255 genes, birth/selection64)
descends through24 single-edit steps from protected V12E Paired ancestor
`foundation_pair_paired/evolved/fresh/evolution/0/i108890`, always random-origin.
It completes16 independent bases in all eight poses (12 trees,4 cyclic), including
four longer pairs with6/8,8/7,8/9,9/9-edge routes. Both goal-pulse removal and
nonlocal zeroing retain all128 pairs; flags/endpoint-aware halt remain. Every
eligible primary retains all its successful pairs under nonlocal zeroing. No
causal multirange advantage is established. Do not infer flag/halt necessity
without separate interventions.

Fresh Branch successes concentrate in replicate1: local133-gene descendant
of a random immigrant after3 mutation steps gives6 paired poses of3 bases,
no base in all8; evolved111-gene descendant after12 steps gives8 poses ofone
5/4-edge tree base. The resampling multirange winner is an unmutated68-gene
random draw,32 paired poses of4 tree bases, all8 poses each, including6/8edges.
Preserve this control; do not claim consistent evolutionary discovery advantage
or necessity of larger genomes. Choice archives are secondary, not replacements.

Only1/3 continued-local and1/3 continued-evolved validation replicates pass the
larger-run gate; fresh0/3. No cohort qualifies; no budget extension. A local
Branch validation gain12→24 becomes a fresh loss40→8, motivating broader
validation as a hypothesis. Four validation bases/replicate are selection data.
No general/ordinary maze benchmark was added. BFS/A*/bit-wavefront/intact VM
solve all768 reachable and128 disconnected inputs. Primary false no-path claims:
8 fresh/local resampling and8 fresh/evolved Current; other cohorts0. Median
successful fork timing is48.05× compiled BFS (corridors21.71×); no speedup.

Confirmation23.06s:45 physical models behind121 aliases,40,320 normal+2,760
ablation responses; timing adds48,177 candidate+48,177 BFS calls separately.
Audit224.21s verifies146 source/11 input hashes,328,392 fitness records,
all2,236,032 search rasters,170,856 mutations,244,080 reproduced births/RNG,
all30 next states and43,080 final candidate replays. A first audit was aborted
on tuple/list serialization equality in range_reads; diagnostic confirms values
identical, canonical comparison fixes it and the complete audit passes. Original
frozen auditor remains; active bounded-memory variant is tools/audit_fork_pressure.py.
12 new tests pass; previous163 are preserved, not a fresh full175-test run.

Exclude **all136,536 whole layouts** through V12G, including fixtures, unqueried
poses and final controls. No retuning against inspected finals. The unlaunched
proposal is a bounded fixed-variant mechanism/transfer test and a separate test
of wider validation, with more independent bases, two junctions, and genuine
alternative-route cycles. Do not start another unchanged60–90-minute search.

Historical checkpoint V12F (October 19, 2026): V12F is complete. Read
`results/route_confirmation.md` and `docs/ROUTE_CONFIRMATION_PROGRESS.md` first.
Do not rerun/extend it or resume V12E. No evolution occurred. Protocol, source,
fixtures and exact target/parent/checkpoint/replacement models were frozen and
pushed in9298bd0 BEFORE fresh final generation. Seed2026101901; preflight1204.
48 reachable bases ×8paired poses ×2goals =768inputs, plus64disconnected inputs.
Bands4–8/9–16/17–32; balanced trees/cycles, interior/rim sources and junction
bearing. Every paired task requires different shortest exits after a shared prefix.

Targeti72095 and parenti72029 both0/768legal/shortest,0/384pairs,0/64no-path.
D checkpointi66411 solves10/768and2/384pairs; E Paired replacementi103154 solves
5/768and0pairs. All these successes are4–8edges; allfour0/512at9–32edges.
The checkpoint's2pairs are two poses of ONE cyclic base. IntactVM/BFS solve
768/768reachable,384/384pairs,64/64no-path. Target screen fails in both families.

Target normal emits768reachable rasters:712branched/cyclic,56disconnected.
Goal switching changes source state360/384,junction384/384,output away from
goals376/384 at some recorded tick; strict-both choices0/384 at all recorded
and pre-stop ticks. Pulse-off removes measured goal response; static flag removal
leaves every measured normal output and complete target trajectory unchanged.
Source-only stopping emits all832responses at tick2, missing goals. All266,312
recorded frames across4variants have0legal path geometry. Caps remain active;
only384/768traces pervariant reach96ticks. Forced probes are not normal outputs.

Post-hoc saved geometry shows all THREE earlier target9/24/25-edge successes
have degree2 at source/goal and every internal route vertex: winding corridors
with NO internal branch junctions. This is reused explanatory evidence, not a
new holdout. V12F also changes generators; do not attribute the between-study
difference solely to branches. Random-origin discovery remains central, but
these successes do not establish general branch routing. Target and parent
normal outputs/status/ticks/work match on all832cases; hidden parent trajectories
were not recorded. Keep all genomes and useful diversity.

Inference123.65s,10,560responses,73,688,626,896workunits,589.25MiBpeak;600s cap
not extended. Wall137.13s;audit191.35s separately. Audit passes139source/36input
hashes,616fixture/final pair labels,8,320normal rasters/replays,4,160native-adapter
checks,3,072trajectory replays,1,536observer checks,266,312geometry frames.
10new tests covered plus previous153 and5existing focused passes; do not claim
fresh full163-test run. No eligible successful target timing case; no speedup.

All **125,008 whole layouts** through V12F must be excluded next, including
200new fixtures and416final poses. Preserve raw masks/trajectories and all old
population/RNG states. No retuning against inspected final data. Next proposal,
NOT launched/preregistered: calibrate minimal paired forks, then isolate one
branch-suppression curriculum/pressure change in matched random-origin arms,
with common protected corridor/short-route/choice diversity. A validation gate
must precede more60–90min compute. Include corridors and branches under the
SAME generator in future confirmation. See `results/route_confirmation/next_experiment.md`.

Historical checkpoint (October 18, 2026): V12E is complete. Read
`results/foundation_pair.md` and `docs/FOUNDATION_PAIR_PROGRESS.md` first.
Do not rerun or extend it. Eighteen conditions of 96 organisms fork generation
865 fresh-origin states into Current/Paired evolution plus Current resampling,
local/evolved ranges, three replicates. Search completes 500 matched generations
to 1365 in 75.14 minutes, 11,010,816 responses, 631.80 MiB peak RSS. Runtime,
256-gene capacity, single-edit mutation and shared curriculum remain fixed;
levels stay [1,1,1]. Both breeding policies use identical primary paired-first
and secondary original-rank validation archives. No known solver enters a lineage.

Local Paired primaries complete 44/144 fresh 3–4-edge pairs versus Current16/144,
D checkpoint9/144 and resampling0/144 on the SAME cases. Eight independent bases
work at least once, three in all eight paired poses; eight successful poses have
cyclic source components. Exact-two pairs70/144 vs46/144 Current and20/144 D;
all144 adjacent pairs retained. Strict screen passes only1/3 local and0/3 evolved
replicates (two required). Evolved Paired3–4 pairs10/144 vsCurrent12/144.
All primary arms complete0 pairs in5–8- and9–16-edge bands. Local Paired frozen
time-course3–8 pairs9/19/17/17/44 at+0/48/128/256/500 is correlated same-corpus
evidence, not five independent tests. All12 evolutionary primary lineages root
in V12C random immigrants at generations1–81.

Preserve the separate longer-route precursor: Current/local/r1 primary
`foundation_study/local/fresh/evolution/1/i72095`, born858, root
`foundation_study/local/fresh/evolution/1/i939` (random immigrant born11).
It was in BOTH initial populations and selected by both common paired archives
at872. Current retains it; Paired's final replacement was selected1240.
On new ordinary trees it solves9/24/25-edge shortest routes with2/5/12 turns.
Removing the goal pulse breaks all3; nonlocal zeroing retains all3. These are
rare correct outputs, not a new V12E-born discovery or a general solver. Another
Current/evolved/r2 descendant born1012 solves an8-edge,2-turn tree route, also
pulse-sensitive and nonlocal-ablation-insensitive. See saved geometry, rasters,
interventions and the explicitly retrospective longer-route illustration.

Do not overstate mechanisms: local Paired retains28/44 successful3–4 pairs
without the goal pulse; static goal flags and endpoint stopping remain.
Current/evolved retains6/12 such pairs when nonlocal values are zeroed and0/12
without the pulse. Paired/evolved retains10/10 under nonlocal zeroing. Ablated
reads retain charges. Some context-specific nonlocal dependence exists, but no
net multirange advantage. These are success-conditioned diagnostics.

Primary ordinary counts: local Current/Paired11/216 each; evolved Current13/216,
Paired11/216. Distance≥8: Current local3/179 andevolved1/179, bothPaired0/179.
Allprimary0/48 no-path, no false reachable no-path claims. Compiled BFS/A*/bitwave
solve216/216 and48/48; intactVMwavefront207/216 (nine long trees hit1024ticks).
Eligible random-origin elementary timings median54.28×BFS; no speedup. Longer
random-origin successes were outside the fixed ordinary timing subset.

Preregistration/training code`c8fe1cf`; all final/time-course models and search
data frozen/pushed`c3106fb` BEFORE final generation. Audit passes756,000 exact
new-program reproductions,450,000 mutations,868,464 fitness records,6,981,492
graded search rasters,43,392 final aliases,21,584 distinct candidate replays,
128source/46input hashes. All six matched population trajectories diverge;
alternate same-pool/RNG ranking changes3,090/450,000 parent genotypes, not a
second evolved trajectory. Ten new tests covered plus previous143 coverage;
do not claim a fresh full153-test run. Preserve all next populations/RNG, raw
outputs, ancestry, archives and prior study packets.

All **124,392 whole layouts** through V12E must be excluded from any new
independent study, including unqueried symmetries and fixtures. Old validation
is reused selection data. No retuning against inspected final cases. The next
recommendation, NOT launched, is a bounded independent confirmation and mechanism
study of the preserved longer-route local genome and saved controls before
another large search. See `results/foundation_pair/next_experiment.md`; it is a
proposal, not an already completed preregistration.

Historical V12D checkpoint (October 18, 2026): the authorized continuation is
complete. Read `results/foundation_continuation.md` and
`docs/FOUNDATION_CONTINUATION_PROGRESS.md` first. Do not repeat the completed
experiment or extend its budget. All 24 states continue intact from generation
442 to 865: 423 additional matched generations, 75.32 minutes, 12,427,776 new
responses, 472.05 MiB peak search RSS. Runtime, 256-gene capacity, fitness,
selection and curriculum rules are unchanged; levels remain [1,1,1].

Fresh-origin evolved-range primary selections pass the stronger preregistered
screen in 2/3 replicates: 103/864 non-adjacent shortest outputs and 28/432
complete pairs, versus 30/864 and 0/432 at the V12C checkpoint on the SAME new
cases, and zero for continued resampling. All 144 adjacent pairs are retained.
Three independent base groups work in all eight paired poses (two trees,
one cyclic). Scope is short: 24 completed pairs have two-edge routes to both
goals; four pair two- and four-edge routes. No primary selection completes a
pair in dedicated 4–8- or 8–16-edge levels. All selected fresh-evolved lineages
descend from random immigrants during V12C, never known solvers.

Prespecified selections at additional generations 0/48/128/256/423 give
fresh/evolved 0/0/8/22/28 complete pairs on this same new corpus (correlated
evidence, not five independent tests). Success-conditioned interventions on
its 103 non-adjacent outputs retain 34 shortest outputs and 0/28 pairs without
the goal pulse, versus all 103 and 28/28 when nonlocal values are zeroed.
Static goal flags/endpoint halting remain; ablated reads keep their cost.
Do not claim a causal multirange advantage from this winning cohort.

General solving remains unestablished: current primary ordinary counts
native/local 4/216, native/evolved 7/216, fresh/local 7/216, fresh/evolved 5/216;
all 0/176 distance≥8. A longer success in the native/evolved checkpoint is
lost by its continuation. Fresh/evolved reports 1/48 no-path, matching its
checkpoint; other current cohorts 0/48. BFS/A*/bit-wavefront solve 216/216 and
48/48; intact wavefront solves 210/216, with six long tree routes exceeding
1024 ticks. Eligible random-origin elementary outputs are median 63.25× slower
than compiled BFS. No competitive speedup is established.

All final and time-course selections were frozen/pushed in `1c22023` before
fresh final generation; preregistration is `7e30e60`. Independent audit passes
380,700 mutations, 979,680 fitness records, 6,274,032 graded search rasters,
all 63,840 final raster aliases and 33,912 distinct candidate replays. All
119 source and 36 input hashes pass. Six new regression tests pass in addition
to the 137 previously covered tests; do not claim a fresh full 143-test run.
Preserve all next populations/RNG, raw masks, histories and old study packets.

All **85,548 whole layouts** through V12D must be excluded in any new independent
study, including unqueried ordinary symmetries and software fixtures. V12C
validation was intentionally reused in V12D and is selection data, not holdout
evidence. No retuning against inspected final cases. That checkpoint proposed
complete-pair-first selection versus current ordering (now completed as V12E), forked
from the same fresh-origin populations/RNG with capacity/runtime/schedule and
local/evolved controls fixed. Four of 56 primary validation replacements lost
non-adjacent pairs while increasing individual route counts; this motivates a
test, not a claim that different selection will solve generalization.

Historical V12A–C checkpoint: the user-authorized calibration-first plan is
complete. See `results/foundation_study.md` and
`docs/FOUNDATION_GOAL_PROGRESS.md`. V12A fails its repair gate; V12B
passes after a validation-selected single-edit policy and balanced orientations.
Known/repaired solver controls remain separate from random-origin lineages.

V12C completes 442 matched generations in 75.15 minutes across 24 conditions
of 96 organisms: native/fresh × local/evolved × evolution/resampling × 3 reps,
plus initial frozen controls. Fresh local primary selections pass the elementary
screen in 2/3 replicates: 86/864 non-adjacent shortest outputs and 9/432 complete
pairs, versus zero for resampling/frozen. These pairs span five independent base
layouts; no fresh-local base works in all eight poses. Earlier selections frozen
before confirmation achieve 0/8/36/86 non-adjacent outputs at generations
48/128/256/442. This secondary time course is correlated evidence that more
stable search helped. Fresh-local primary lineages descend from random
immigrants, never known solvers.

General solving remains unestablished: best ordinary cohort 7/216, every cohort
0/181 distance≥8 and 0/48 no-path; BFS/A*/bit-wavefront 216/216 and 48/48.
No net multirange advantage or speedup: eligible tiny-task outputs have a median
48.95× runtime ratio to BFS. Search: 13.33M responses, 436.0 MiB peak RSS.
Audit passes 397,800 mutations, 1,026,048 fitness records, 5,972,328 search rasters
and all final outputs. 137 current tests are covered by 136 full-suite passes
plus the later time-course test. Preserve all next populations/RNG and raw data.

All 52,424 whole layouts through V12C were excluded from new V12D training and
final cases. The unchanged continuation is now complete as described above;
implementation is `maze_evolution/foundation_continuation*.py`, output is
`results/foundation_continuation/`. Do not alter immutable V12 source/budgets.

Historical checkpoint before V12: V1–V11,V8A,V10A are complete.
123 current tests are covered (122 full-suite passes, 4 focused passes after
the final study guard edit, plus 1 separately added exact 256-gene bound test).
Read `results/capacity_growth.md`, `docs/GROWTH_STUDY_V11.md`,
`docs/GROWTH_DIAGNOSTICS_V11.md` and the next-study proposal
`results/capacity_growth/next_experiment.md` first.
Earlier protocols/results below are historical; do not repeat completed work.

V3 pairs current/causal objectives from six saved V2 random-origin populations,
96 organisms x 160 additional generations. Capacity and V2 inference stay fixed.
It ran 60.45 minutes of search including source-removal probes, 64.22 minutes with
fresh holdouts/timing, plus separately recorded post-freeze diagnostics. Mean
source-dependent transmission on 174 unseen long-route cases improves from
0.2480 frozen to 0.4185 current / 0.5090 causal with evolvable ranges; local arms
both reach 0.3071. Causal wins two of three held-out replicates, with higher
component leakage. Zeroing nonlocal reads reduces its score to 0.0809.

This is a signalling precursor, not a solver. Final multirange task archives
solve 2/216 reachable cases under either objective (initial frozen task: 4/216).
Local task archives solve 2/216 current / 0/216 causal. All final task arms solve
0/174 distance>=8 cases; all successful outputs are straight 1–2-edge routes. Compiled BFS/A* solve 216/216 and 48/48 no-path. No
competitive speedup or evolutionary path-accuracy advantage is established.

V1/V2 source/results remain untouched. V3 uses separate `signal_*` modules and
`results/source_pressure/`; logs are losslessly repacked with decoded hashes in
`storage.json`. Full next-population/RNG checkpoints and lineage records permit
deterministic continuation. Do not retune against any inspected final tests.

V4 preserves six V3 causal populations/RNG states, adds the saved signalling
archive as a fixed elite in both arms, and compares transmission/goal-output
pressure at unchanged capacity for 40 further generations (96 organisms,
two topologies x three replicates). The validation extension gate did not pass.
Search took 9.67 minutes; training plus recovered final outputs/timing took15.32
minutes, excluding the sampling failure/repair-development gap. The corner-DFS
size9 perfect final generator ran out of unused layouts before any final output
evaluation. Only final size9 perfect cases changed to Wilson spanning trees;
frozen archives, training and fitness are unchanged. This deviation is explicit
in `final_generation_repair.json`; `goal_recovery --run` reproduces it.

Goal-sensitive branched output emerged weakly but did not generalize better:
multirange goal-archive score0.0022 vs0.0071 transmission control on independent
goal pairs; local0.0033 vs0.0035. No final pair meets both-direction criteria.
Task archives solve local1/216 (same frozen control), multirange0/216 under either
objective, all0/174 at distance>=8, and0/42 separate paired reachable targets.
The one local success is adjacent. BFS/A*/bit-wave solve all reachable/no-path
cases. Audited7128 primary +1296 paired +192 ablated normal rasters,1152 final
goal metrics,47998 fitness decompositions; source/layout/provenance checks pass.
V1–V3 code/raw results are untouched. V4 checkpoints, full next populations/RNG
states, source snapshots and losslessly repacked logs remain available.

V5 tests that factorized curriculum: six V4 goal-pressure next populations/RNG
states, product/curriculum arms, local/evolvable ranges, 96 organisms x48 further
generations. Both arms preserve fixed signalling and V4 goal elites. Generations
0–15 reward Q+S,16–31 blend to2*sqrt(Q*S),32+ share the product objective. Task
archives use common ordinary-route fitness without probe reward. All size9
perfect splits use Wilson trees; all V1–V4 layouts are excluded. No extension
criterion passed. Training13.02 minutes; main run16.05; peak RSS162.8MiB.

Curriculum task archives solve local1/216 and multirange1/216 primary reachable
cases, versus product2/216 local /1/216 multirange; all0/177 distance>=8 and
0/197 turn-required primary cases. Curriculum paired routes0/42; local product
1/42. The latter is a10-edge,3-turn shortest path through two internal junctions.
Existing-ancestor analysis finds its first success at generation38 after three
gene-row edits; its parent fails. It grows west/south, fails the other goal and
all90/180/270-degree rotations, and has identical state under both goals at
every tick1–21. The common endpoint-aware runtime halt explains the successful
stopping time. Preserve this directional filament as a precursor, without
claiming goal-guided routing. The analysis is post-hoc on an inspected final
case and is not another holdout test or a tuned genome.

V5 goal-proxy scores multirange0.0068 curriculum /0.0089 product; local both0.0106.
Curriculum task archives handle12/48 primary disconnected cases, no false claims
on216 primary reachable cases, versus frozen0/48; disconnected endpoints have
a corner/partition bias. BFS/A*/bit-wave solve all reachable/no-path tasks.
Exploratory validation time courses show local goal archives have no source
state response to switched goals through tick64; multirange responses remain
limited (3/12 curriculum,2/12 product). No competitive speedup is established.
V1–V4 source/raw results remain unchanged. V5 next populations/RNG states, all
validation archives and source/lineage/diagnostic records are preserved.

V6 completes that symmetric-stimulus test. Twelve conditions (local/evolved ×
flag/pulse ×3),96 organisms ×48 generations, fork the V5 product next population
and RNG, preserving validation-selected task/goal/transmission archives from
**both** V5 arms plus ancestral protected elites. Both use fixed V5 product
pressure. Pulse adds channel1=1 at the goal; source channel0 and public flags
are unchanged. Flag-mode normal/probe output/state/work and product-fitness
parity tests pass. Source-removal probes retain the goal pulse and goal flag.

On independent paired layouts, multirange goal archives improve G to0.0390
versus0.0135 frozen Pulse and0.0137 evolved Flag. Goal-switch source-state
responses at tick16:8/18 regular pairs Pulse,5/18 frozen Pulse,1/18 Flag.
Removing the pulse from those evolved Pulse genomes reduces G to0; zeroing
nonlocal reads also reduces G to0. These are goal-dependent output precursors,
not correct routes. Both-direction qualification remains0/18 final regular
pairs. Local goal scores both0.0052 and no source response through tick64.

Primary task archives: local2/216 each (same frozen),multirange0/216 each;
all0/178 distance>=8 and0/133 mandatory-detour cases. One inherited local
seven-edge path has one turn on a new maze; the other success is two straight
edges. Both occur before V6 training. All candidate arms solve0/42 paired
reachable targets, and all768 tick16 output rasters fail legality even with
assumed emission. Compiled BFS/A*/wavefront solve all216 primary and42 paired
reachable targets,48 primary and6 paired no-path cases. No speed advantage.
Local task no-path16/48 and multirange Flag12/48 match their frozen controls;
Pulse multirange0/48. No false primary reachable no-path claims in task arms.

The extension gate failed. Search13.11min;main16.31min;peak180.1MiB RSS onM4.
Audited5016 primary +912 paired +768 cross-input +192 ablated normal outputs,
58100 training fitness decompositions,254832 source arithmetic records,
49 training/validation valid claims,48 selected replays; all checks passed.
There are35907 new individuals and full population/RNG continuations under
`results/goal_beacon/checkpoints/beacon_{local|evolved}_{flag|pulse}_{0|1|2}.json`.
Prior V1–V5 source/raw results remain unchanged. New `beacon_*` modules are
separate; do not patch old runtimes or silently use the wrong input convention.
V6 config `pressure` names the input mode (`flag`/`pulse`); the objective is fixed
product pressure in both.

One recorded protocol deviation: the construction-only test used the study
seed before training, so freeze-before-generation was not literal. It evaluated
no candidate genomes or outputs; actual final inference began after all models
froze. See `protocol_notes.json`. Do not claim no prefreeze layouts were ever
constructed. Use a separate seed for future construction/preflight tests.

Random-origin emergence remains central. Preserve signalling, goal-sensitive,
and directional-growth variants from both V6 arms, by recorded validation
criteria. Also preserve `balanced_validation_archive.json`: a post-hoc archive
of existing validation-evaluated genotypes ranked by mean per-pair min(G_A,G_B),
then both-goal rate,Q,mean G. It did not alter primary archives or add final
assays; some identities overlap original selections. Its source/code hashes
and full genotypes are saved. Mean-G selection discarded some more balanced
variants (e.g. Pulse replicate1 has validation both=0.5 in the supplemental
archive but0 in the final mean-G archive). Do not present that as unseen accuracy.

V7 completes that balanced-pressure comparison. Twelve conditions,
local/evolved ×mean/balanced ×3,96 organisms ×48 additional generations. Both
use the unchanged V6 pulse runtime and8-channel/128-gene limits. Per regular
pair, Mean rewards2(G_A+G_B); Balanced rewards(G_A+G_B)+2min(G_A,G_B), assigning
case i the bonusG_i+min. Both maxima4. Mixed unreachable pairs retain2G_i in
both. Normal correctness/no-path priority, source reward and costs stay fixed.

Base next populations/RNG are V6 Pulse. Both V6 arms' validation task/goal/source
archives, protected ancestors and supplemental balanced variants are injected
by recorded criteria and protected equally. Validation uses Mean in both arms;
common balanced archives rank B=mean regular-pair minG,then both,Q,meanG,
validity/optimality. Both nominate balanced training leaders. Task archives use
normal fitness. Final selections are task/balanced plus their frozen controls;
mean-goal/source/Q/S archives remain saved. Absolute V6/V7 archive scores are
not a pressure-only comparison because the common archival policy changed.

On independent paired tests, multirange Balanced B0.0310 vsMean0.0048 vsfrozen
0.0215; individual G0.0509 /0.0386 /0.0352. Both-direction qualification2/18
versus0/18 Mean and1/18 frozen. Gain concentrates in replicate1;replicate0
retains B,replicate2 is slightly below frozen. Local Mean B0.0127 versusBalanced
0.0031, frozen0.0031. These are intermediate measures, not completed routes.
Removing the goal pulse reduces multirange Balanced B to0 (G remains0.0060);
zeroing nonlocal reads reduces B to0,source score0.4911→0.0831. Do not claim
all mean-G or source signals vanish. Mean's nonlocal-ablated B remains0.0038.

Primary task accuracy:local4/216 under both (same frozen);multirange Balanced
1/216 (same frozen),Mean2/216 (frozen1/216). All0/165 distance>=8 and0/42 paired
reachable targets. Candidate task successes are1–5 edges; an inherited local
five-edge route has two turns. Do not claim a new general route algorithm from
the extra short straight Mean success. BFS/A*/wavefront solve all216 primary,
42 paired reachable targets,48 primary and6 paired no-path cases. No speedup.

Diagnostic added during training before final inspection: on9 perfect-tree
pairs, locate the last shared oracle-prefix vertex and distinct next neighbor
for each goal. A correct local choice requires source-connected output at the
junction and desired neighbor, with the other branch off. Both-choice success
is0/9 in every selected archive. Multirange Balanced reaches the junction under
both goals and illuminates all three positions in6/9;source-to-junction distance
can exceed16 in another case. This reuses saved tick16 rasters, without new
inference, and is not another final accuracy measure. Source state changes at
tick16:Mean11/18,Balanced4/18,frozen4/18. Communication at source is distinct
from useful goal-dependent output. Full records:`junction_diagnostics.json`.

A matched-parent mutation diagnostic (also specified during training) observes
18628 newly born children whose parent is evaluated on the same rotating batch.
18423 change genotype;8585 of those (46.6%) match the saved normal/probe rasters,
status/steps and scalar fitness traits. Hidden trajectories may still differ.
1484 have higher,7196 lower training fitness (cost tie-break excluded). This is
a conditional subset, not an unbiased neutrality estimate. Preserve neutral
variation; gene length is not effective complexity. Task genomes126–128 genes,
conservative output/stop slices21–57; full-state quiescence may depend on others.

Gate failed;search13.18min,main16.18min,peak192.2MiB onM4. Audited5016 primary,
912 paired,768 pulse-removed and192 range-ablated normal outputs;58240 fitness
records,256512 source arithmetic records,99 valid training claims,48 replays,
12 archive maxima and all provenance/layout checks passed. There are34822 new
individuals and complete next populations/RNG in
`results/balanced_goal/checkpoints/balance_{local|evolved}_{mean|balanced}_{0|1|2}.json`.
Separate `balance_*` modules reuse unchanged V6 inference. Source hashes,
lossless decoded/stored log hashes and full prior populations are preserved.
Construction seed1074 differs from study2026101805; final layouts were generated
only after model freeze. V1–V6 code/raw results remain unchanged.

V7's proposed junction-pressure test is now complete as V8. At unchanged V6
pulse input/runtime, eight channels and128 genes, local/evolved ×Balanced/
Junction ×3 ran96 organisms for48 generations. Common decision-rich pairs
require a shared shortest prefix at source distance2..8 and goals≥4 beyond,
with disjoint sets of all valid shortest exits. Half of pair indices require
an initially misleading Manhattan bearing. Both arms share this sampling;
V8 versus V7 is not a pressure-only comparison. J=.25 causal connected prefix
+.75 branch choice; Junction uses J_i+minJ in place of Balanced G_i+minG.
All shortest-next-step ties are accepted; wrong exits must be suppressed for
strict qualification. Labels stay in fitness, never candidate inference.
Study seed2026101806, independent construction-test seed1084;6896 prior whole
layouts excluded. Models froze before264 ordinary and24 paired final layouts.

V8 primary task accuracy: multirange Junction3/216 versus Balanced0/216 and
frozen1/216; local Junction1/216 versus Balanced0/216 and frozen1/216. All task
arms0/174 at distance≥8,0/42 paired and0/144 mandatory detours. Multirange
Junction's3 successes span1–3 edges, two with one turn. BFS/A*/wave all216/216,
42/42 and all48/6 unreachable inputs. Correct no-path varies0..32/48, with
no false no-path claims on reachable primary cases. No competitive speedup.

Primary selected junction archives make0/18 strict-both choices on fresh
regular pairs. Their multirange J scores: treatment.2345, Balanced.1877,
frozen.2433, dominated by prefix credit. Goal switch changes junction state
at tick16 in6/18 treatment,9/18 Balanced and7/18 frozen, distinct from useful
exit choice. Only1/18 pairs has BOTH goals outside every local decision
site's16-edge influence cone; this cannot explain the overall failure.

A validation-only strict-choice archive, planned during training before final
inspection, finds two qualifying multirange variants. Both are preserved in
`results/junction_choice/strict_validation_archive.json` along with complete
ancestry replay at `choice_ancestry.json.gz`. They are NOT selected by final
performance or used to alter V8 breeding/gates/primary selections.
Balanced replicate2: birth4 id `junction/evolved/balanced/2/i284`, after three
ancestral mutation steps, makes proper paired choices on a cyclic17×17
validation case with goal distances17/8 and source-to-junction2. Junction
replicate1: birth7 id `junction/evolved/junction/1/i472`, from initial i3,
qualifies on a17×17 tree with goal distances23/10 and source-to-junction4.
Both lose the choice under either goal-pulse removal or nonlocal ablation;
neither completes either validation route. Gene rows may shift during
insertion/deletion; do not interpret83 changed rows in the first lineage as
83 independent mutations.

V8A separately preregistered a tiny confirmation AFTER V8 results/ancestry,
BEFORE its new layouts. Seed2026101807,12 new shared regular layouts/24 inputs,
all7490 V1–V8 layouts excluded. Five unique root/parent/variant genotypes from
the two validation-selected lineages all score0/12 strict-both and0/24 valid/
shortest outputs; BFS24/24. No training, tuning or reselection follows.
The Junction variant differs from its parent by swapping rows27/60 (neighbor
count and nonlocal minimum) and redirecting row66's destination63→43.
Counterfactual groups on the original validation pair: parent J=.0833;
swap alone.0833; register change alone.0833; combined child.8333 and strict
both true. This supports a context-specific cooperative interaction between
two change groups, NOT a general solver or necessary individual-gene proof.
Full raw data/provenance are in `results/junction_confirmation/`.

The mean-J archive can discard a useful choice on one pair in favor of broad
prefix growth across all pairs; the strict validation supplement rescued the
second primitive. Training recorded27 strict-both pair responses under
multirange Balanced and24 under Junction, zero local (repeated genomes/cases,
not independent discoveries). A matched-parent diagnostic finds9158/18610
changed-genotype children (49.2%) match its saved behavioral fingerprint;
work/active counters and hidden trajectories can differ. Preserve neutral
variation and these cooperating primitives. Task genomes114–128 genes,
conservative output/stop slices10–61; length is not effective complexity.

Gate failed. Search13.47min, main16.54min, peak main208.2MiB; diagnostics20.92s,
compression9.82s, audit18.04s, V8A4.07s plus.17s verification. Audited6908 main
final/diagnostic normal outputs,58686 fitness records,263612 junction masks,
29 valid training claims,48 selected replays,12 junction and12 balanced archive
maxima. V8A verifies124 candidate outputs/masks plus24 BFS outputs. Main
charged427687305596 dispatch-plus-read units.33334 new individuals; all source,
layout and lineage checks pass. Full next populations/RNG checkpoints are
`results/junction_choice/checkpoints/junction_{local|evolved}_{balanced|junction}_{0|1|2}.json`.
V1–V7 code/raw results remain immutable. V8A raw results also remain immutable.

V9 completes that strict-choice-first comparison. Local/evolved ×Prefix/Choice
×3,96 organisms ×48 generations, fork matching V8 Junction populations/RNG.
Preserve task/J/B/G/source, protected variants, strict-validation selections
and qualifying ancestors from both native V8 arms. No cross-replicate/topology
transfer. Protected counts13/15/15 local,23/19/25 evolved. Same V6 pulse VM,
8 channels,128 genes,unchanged V8 J shaping/caps. Global rank(V,O,N,0,S,W)
versus(V,O,N,K,S,W); K counts strict-both pairs. Normal correctness first.
Case lexicase inserts the pair bit before smooth shaping; zero control
preserves old RNG. Common validation is Prefix; choice archive ranks
(strict-both,J,B,G,valid,optimal). Both arms save all named archives.

All six matched pressure pairs have IDENTICAL ordered genotype populations at
every generation and identical final RNG states. The priority was implemented
and verified, not silently zeroed: each multirange pressure records19 strict-
both training responses across4 batches (rep0:g16/g22,rep1:g2,rep2:g14); local
none.10 positive unprotected-genotype opportunities across3 batches retain5
copies and produce40 mutated offspring under either pressure. All positive
parents (protected included) produce83 offspring per pressure. All four active
pools have the same global best sets;512 post-hoc matched-seed lexicase draws
also choose identical parent IDs/genotypes. Priority is redundant for observed
selection outcomes, NOT proven redundant for every possible population.
Choice primitives already reproduce; transfer is the observed bottleneck.
Full records:`reproductive_priority.json`,`priority_trajectories.json`,
`selection_counterfactual.json` (analysis seeds1139000..1139127,no inference).

Primary task accuracy local1/216,multirange0/216 under both, matching frozen.
All selected models0/18 strict-both final pairs and0/42 paired full routes.
Task distance≥8:local1/171,multirange0/171. Local success9 edges,1 turn, already
in frozen control. Task no-path16/48,no false primary reachable claims. BFS/
A*/wave216/216,42/42,all48/6 no-path. No speed advantage. Do not compare absolute
accuracy across versions as a pressure effect: common archive/seed changes.

Post-hoc inspected-final path assay (NOT another holdout): frozen and current
local task have identical genotype. Original9-edge goal emits tick19; midpoint
5-edge goal emits tick11. Forced probes show identical output concentrations
and source states under both goals at EVERY tick1–19; both halts satisfy the
common source-stop/endpoint conditions. Endpoint-aware halting chooses length
from the same measured growth trajectory here; do not call it goal-guided
routing. `inherited_path_diagnostic.json`,independent replay also passes.
Assay.080s,2 normals/38 probes,2540210 work; replay separately recorded.

Both pressures find the SAME evolved-rep2 validation-only lineage: initial i40
fails the fork; birth3 i218 succeeds; birth5 i324 retained. Different pressure
prefixes are aliases of the same genotype trajectory, not independent finds.
Its9×9 cyclic qualifying pair has source-to-junction4; it needs the goal pulse,
but nonlocal ablation retains J=1/strict-both on THIS case. Unlike the two V8
examples,long reads are not necessary here; this does not imply forcing every
range1 or general local solving. Fresh final paired tests remain0/18. Preserve
this new variant with both V8 primitives, directional growth and neutral drift.
A saved-raster entry diagnostic specified during training removes desired
exits and checks incoming source reachability/shortest-prefix length. All19
strict-both training responses per multirange pressure pass under both goals.
It does not change registered K/primary results. `entry_diagnostics.json`.

V9 seed2026101808,construction seed1094,7502 prior layouts excluded. Freeze
BEFORE264 ordinary/24 paired final layouts. SHA
74b6135000533707aa7fdc367152365e227047044ac92b043648d77e071c5cfb.
Gate failed;search13.90min,main17.09min,main peak200.4MiB. Diagnostics20.30s,
compression10.15s,audit19.51s,post-hoc parent replay2.13s.58998 fitness records,
59046 priority records,267356 junction masks,100 valid training claims,48
selected normal replays,12 each task/choice/J/B archive maxima all pass.
6908 main final/diagnostic normals audited,plus2 path normals/replay. Training
265608 normals+531216 probes,436915640448 dispatch-plus-read units.32258 new
IDs,full next populations/RNG in
`results/choice_priority/checkpoints/choice_{local|evolved}_{prefix|choice}_{0|1|2}.json`.
All70 frozen sources and lineage/layout/storage checks pass. Conditional
changed-genotype neutrality8784/18048 (48.7%) by saved behavioral fingerprint;
work/expression/hidden trajectories can differ. Gene length is not effective
complexity. Prior V1–V8/V8A source/raw data remain immutable.

The next justified test addresses transfer rather than increasing priority
again: a near-to-far GOAL-TO-FORK distance curriculum versus the current minimum-
distance distribution, same capacity/objective/common protected cohorts. Start
with attainable but genuinely source-dependent paired decisions, increase
cue distance on a preregistered schedule. Hold validation/final at the harder
distances; preserve all known variants and neutral diversity. Use new layouts;
report curriculum training AND independent transfer. Capacity, regulation and
longer evolution remain central live hypotheses. No known wavefront/solver
rules enter random-origin lineages. Larger precursor scores alone do not
justify hour-scale extension. Exclude ALL V1–V9/V8A layouts (including V9
manifest):8096 unique layouts. Do not retune against inspected tests; use new
separate version modules.

V10 completed the matched near-to-far cue comparison. New separate distance_*
modules preserve all V1–V9 source/raw data.12 conditions:local/evolved ×Fixed/
Curriculum ×3,96 organisms ×48 generations. Both fork native V9 Choice next
populations/RNG, preserve both V9 arms' task/choice/J/B/G/source/protected,
supplemental strict choices and qualifying ancestors. No cross-topology/replicate
transfer or known-solver insertion. Protected counts15/18/15 local,25/22/29
evolved. Same8 channels,128 genes,V6 pulse VM,Choice-first ranking in both arms,
including common hard validation. All initial DNA/protected cohorts/RNG match.

Fixed uses original hard goals. Curriculum shortens SAME layout/source/fork
branch goals to1/2 edges for generations0–15,2/3 for16–31,far at32 onward.
Mixed pairs unchanged. Short labels only in train_near splits; validation/final
retain original≥4 remaining/≥8 source distance. Near prefix/fork/exits verified
identical,all allowed exits subsets. Shortening also removes deceptive bearing
in both early phases; report that distribution effect. No automatic extension:
common hard-validation gate failed. Native variants and neutral drift remain.

Primary task archives/frozen controls ALL0/216 reachable,0/179 distance≥8,
0/42 paired. Every final selected model0/18 strict-both pairs. Secondary evolved
Curriculum choice archive1/216,adjacent endpoints only (2pixels,4ticks,
rep1 i415,birth6). No other selected success. Task no-path33/48 local,16/48
evolved;no false reachable claims. BFS/A*/wave216/216,42/42,all48/6 no-path.
No speed advantage. These are selection-specific scores,not absence of every
older protected capability; do not compare versions as a pressure-only effect.

Training valid normals local122 Curriculum vs49 Fixed;evolved52 vs4. No regular
training pair has BOTH ordinary outputs valid/shortest. Strict forced16-probe
training responses:local0;evolved Curriculum1,Fixed15 (repeated opportunities).
Phase leaders15/31/47 have0 final choices/routes; all boundary batches contain
one regular tree pair+one mixed disconnected pair,so snapshots miss cyclic
opportunities. Reused-training frozen/leader/final replays are NOT holdouts;
leader replays equal original full training records exactly.

NEW TRAINING-ONLY PRIMITIVE: evolved Curriculum rep2,i1472,birth30,first observed
generation30 on train_near2_goal/r2/p60/s15/perfect/17x17/a|b. Fork vertex90,
source-prefix[156,139,122,105,88,89,90],incoming89,exits91/73,allowedA73,B91,
goals2/3 beyond. Ancestryi94(birth0)→i1213(25)→i1402(29)→i1472(30).
Parent J=.25/strictfalse,child J=1/strictboth; neither ordinary route correct.
Child changes row25 REMOTE dst46→59 (radius2,ch6) androw117 operand3→36.
Counterfactual row25 alone suffices,row117 alone fails; NOT two-edit cooperation.
Goal-pulse removal or nonlocal-read removal each destroys choice,J=.2 on this
training case. Source-removal rasters independently verify causality/entry.
It is unprotected,retained once,produces18 mutants,and exact genotype is absent
from final population. Explicit full genotype/ancestry in
results/distance_curriculum/training_choice_diagnostic.json; preserve it,parent,
root with all earlier native variants in BOTH matching next-test cohorts.
This diagnostic is post-hoc training-selected after main final evaluation;
never evaluated this newly selected candidate on V10's inspected final set.
Original1.166s,12normals/24probes,14988575work; independent replay.128s plus
9447514work for edit reversions. Initial tuple/list assertion attempt extra
ancestry cost recorded separately; no training/raw result changed.

V10A froze child,parent,root BEFORE12 NEW layouts. Seed2026101810,independent
construction/replay preflight1105 (accuracy not inspected),excluded8690 prior
layouts.9/17 ×tree/random ×3;each same source/fork hasnear2/3 andfar≥4 paired
goals. All three genomes0/12 strictboth and0/24 normalroutes at EACH distance;
BFS48/48. ChildnearJ.25,far.2458333.12layouts are independent,not24pairs.
No training/reselection or primary V10 change. Main.877s,144normals/288probes,
143965340work;independent.359s verifies192normals/144Jrasters and replays all
144normals/288probes,equalwork. Model SHA
34329d632b2b551a68ae2b74cd89b409ed4199acc6d132007a95ae7b1d277474.
Preregister/freeze commit833dfe5. Raw:results/distance_confirmation/.
This bounded negative preserves random-origin,regulation,capacity/time hypotheses.

V10 seed2026101809,preflight1104,8096 prior layouts excluded. Freeze before
264 ordinary/24 paired final layouts. Model SHA
c6df4e29f961fcb0e62732c12a2fe34e245cb7710aae8409c35b7287c8ef8733;
prereg4aa60d6. Search829.323s(13.82min),main1017.161s(16.95min),peak203.5MiB.
Diagnostics30.114s(includes1440 phase normals);compression10.400s;audit20.360s.
All79 frozen sources,59004fitness,59232priorityrecords,268848Jrasters,
227validtrainclaims,48selectedreplays,12eachtask/choice/J/Bmaxima pass.
8328 main/diagnostic normals independently assessed,plus post-hoc training
assay/replays/reversions and V10A. Training265680normal+531360probes,
432900048953dispatch+attempted-read units;31417newIDs (not independent finds).
Neutrality8434/18094 changed-DNA matched-parent children (46.6%) by observable
fingerprint; hidden trajectories/work can vary. Full next population/RNG:
results/distance_curriculum/checkpoints/distance_{local|evolved}_{fixed|curriculum}_{0|1|2}.json.
All prior source/raw results stay immutable.8702 unique layouts throughV10A.

HISTORICAL PROPOSAL, COMPLETED AS V11: greater heritable program capacity with copy-and-diverge
structural growth,128vs256-gene ceilings,common block-duplication operator and
Fixed hard-pair objective. Keep eight channels/opcodes/range semantics unchanged;
prove≤128-gene old-program inference equivalence before training. Identical native
starting populations/RNG/protection,including i1472/parent/root in matching
evolved rep2 under BOTH capacities. No cross-topology/rep transfer,no known solver.
Common bounded instruction/read/tick caps; report additional dispatches and any
fewer completed ticks,actual growth/expression/dependency/behavior rather than
claiming effective complexity from ceiling/length. New separate modules/layouts,
exclude ALL8702 throughV10A. No hour extension from precursor scores alone.
Do not keep only optimizing easy-goal curricula at unchanged capacity.

V11 completed the capacity comparison using separate growth* modules. Twelve
conditions: local/evolved × cap128/cap256 × 3, 96 organisms × 48 generations.
Both fork native V10 Fixed populations/RNG and preserve the common native
Fixed/Curriculum archives, strict supplements and all four training-primitive
ancestry nodes in evolved replicate 2. No solver injection or cross-replicate
transfer. Eight channels, hard pair distribution, V9 Choice objective, opcodes,
mutation modes, immigrant lengths and instruction/read/tick limits stay fixed.
V2 already supported block duplication; only the length ceiling changes its
eligibility. Old inference/probe kernels remain unchanged.

V3 serialized genomes support 256 genes; use growth.Genome/Individual when
loading these checkpoints. Legacy parsers reject programs above 128. Preflight
parity verifies 1,052 native program/topology pairs, 7,712 normals, 10,016 probes
and 50 full fitness calls. Exact 256-gene bounds/memory/read accounting pass.

Growth is real: evaluated programs reach 228 genes, the prepared g48 next
population contains 240, and final evaluated expanded populations have 39–66
above128 members. All selected task genomes remain ≤128; one selected local
choice genome has 138. Do not infer every grown genome was tested on holdouts.
Both capacities have primary task accuracy local 0/216 and evolved 1/216,
matching frozen controls. Secondary local choice 4/216 versus frozen 3/216
under both caps. ALL selected successes are adjacent one-edge routes; all
selected models solve 0/180 long cases and 0/42 paired routes, 0/18 strict-both.
BFS/A*/wavefront solve all reachable and no-path cases. Gate false; no extension.
No competitive speedup or capacity-related accuracy advantage is established.

Post-hoc frozen-model region assay (growth_context) finds goal-dependent hidden
states at fork exits in evolved replicate 2: cap128 choice 4/18, cap256 3/18,
frozen 3/18; mostly absent at the vertex. This reuses final pairs and is not a
new accuracy test. Source × goal interaction can be positive with no goal
contrast under source-present inference; do not treat it as correct routing.
312 full-state/mask/counter probe replays and 288 native comparisons pass.

V11 seed 2026101811, preflight 1114, equivalence 1113. Excludes all 8,702 prior
layouts; total unique layouts through V11 is 9,296. Main 1020.317s (17.01min),
search 849.112s (14.15min), peak 213.2MiB. Diagnostics 30.233s, compression
10.26s, initial audit 23.362s and final audit 23.10s (temporal-label correction
only); hidden-context assay .671s and replay .690s, all separately charged.
91 frozen sources, 59,127 fitness records, 23,655 child mutation traces,
270,324 J rasters, 41 valid training claims, 48 selected normal replays,
1,440 phase outputs and archive maxima pass independent verification.
Training: 267,156 normal responses, 534,312 probes, 444,031,737,693 work units.
Genotype changes preserve recorded behavior in 8,396/17,176 coeval opportunities;
this fingerprint does not identify full hidden trajectories or effective complexity.
All earlier source/raw results stay immutable. Full native next populations/RNG:
results/capacity_growth/checkpoints/growth_{local|evolved}_{cap128|cap256}_{0|1|2}.json.

HISTORICAL NEXT-STUDY PROPOSAL, DEFERRED BY THE AUDIT BELOW: retain cap256 capacity and all native random-origin
populations/primitives; compare unchanged pressure against an added bounded
hidden goal-context discrimination term at fork exits. Preregister the exact
paired directional contrast/normalization and prove it on independent fixtures.
Keep correct complete routes and strict paired choice above shaping; raw
hidden-state differences or source × goal interactions alone are insufficient.
Do not insert a known solver or reset the grown populations. Match cohorts,
RNG, caps, sampling and operators; use fresh layouts excluding ALL 9,296.
48-generation screen, extension only for replicated hard-validation transfer.
The proposal is not an executed/preregistered V12. Random-origin discovery,
capacity/regulation and evolutionary time remain open hypotheses.

CURRENT HANDOFF — RESEARCH AUDIT, October 18, 2026:
The user requested a deep reassessment before more experiments. Read
results/research_audit_2026_10_18.md and its analysis/verification packets.
No new evolution, candidate inference or maze generation was run for the audit.
Earlier raw results/source remain unchanged. The hidden-context V12 proposal
above is deferred; it is not the automatically authorized next experiment.

Judgment: local representation works, evolved causal signalling and specific
fork computations exist, but general random-origin solving and competitive
speed remain unestablished. Continue research with searchability/timing
calibration before another shaping term. Keep known working/damaged program
controls strictly separate from all random-origin lineages. Preserve native
populations and useful variants; a fresh modern-convention random cohort, if
tested, must be separately labeled. Exact complete routes remain primary.

Retrospective facts: eleven main runs total208.43min, excluding separate
tests/audits/diagnostics; V3–V11 record2,834,862 normals/5,669,724 probes.
V11 protects18–36/96 organisms, leaving30.5–46.2 mutated children/generation
plus9 immigrants. This is not genetic collapse:95–96 unique genotypes remain.
All211 successful V2 frozen local seed outputs take2D+1 ticks;160 haveD>=8
and finish after16. Tick16 source-connected shaping disfavors that developmental
ordering, although completed solutions still win primary normal fitness.
This is not a universal solver lower bound or proof that timing explains failure.
Both goal positions lie outside the local tick16 fork-region cone on10/252
regular training pairs,1/12 validation,2/18 final; most pairs are within reach.
Independent distance code verifies all564 inputs;39 original input hashes match.

Recommendation, not an executed/preregistered experiment: calibrate current
controls/graded repair and achievable developmental objectives; then consider
one precommitted60–90min stable study of transferable elementary skills with
replication, frozen and evaluation-budget-matched resampling controls. Do not
require early exciting transfer to test a preregistered long-incubation claim,
but do not extend indefinitely. Set the detailed protocol before training.
Exclude all9296 prior whole layouts plus any new calibration layouts. No
claim of general progress from proxy scores, genome length, or isolated cases.

Original mission steps below are historical; do not repeat them as unfinished.

1. Inspect and run `cellular_maze_lab.py` and `tests/`.
2. Implement a **minimal bounded evolvable organism** with a small, typed genome and 2–4 internal per-site state channels. Define a compact grammar of deterministic local instructions. Consider a finite-state/Boolean rule table or small linear program; avoid implementing a giant neural network.
3. Add separate organism and evaluator modules, ideally isolating maze generation, reference solvers, execution, selection, and scoring. Preserve baseline behaviour.
4. Implement selection and mutation over a small population; evaluate candidates on rotating training mazes and fixed unseen holdouts.
5. Run a short **two-arm** experiment: purely random initial genomes versus genomes seeded with a functional wavefront-style rule. Use the same fitness and compute limits. Include a no-evolution ablation.
6. Produce `results/first_evolution.md` (accuracy, optimality, runtime, steps, memory, failure cases), machine-readable raw results, and simple visual samples of the best output.
7. Commit/leave runnable code, deterministic tests and instructions. Do not report success without an accurate holdout result.

## Sensible ordering

Phase 0: reproduce baseline -> Phase 1: simple genome runtime -> Phase 2: evolution and fitness -> Phase 3: stress-test larger and cyclic mazes -> Phase 4: multiscale or 3D only when justified.

Avoid spending the first iteration on a GUI, cloud orchestration, genetic text compression, or expensive GPU kernels. A good negative result is valuable. State what failed.

## What to report when done

Summarize: files changed; commands/tests run; accuracy on unseen mazes; baseline comparisons; representative failure; time/memory cost and scalability implications; and one well-justified next experiment.
