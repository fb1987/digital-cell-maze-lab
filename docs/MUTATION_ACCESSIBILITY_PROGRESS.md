# V12R handoff — complete, October 19, 2026

Read `results/mutation_accessibility.md` first. R is complete and audited. Do not
repeat or extend it, change its frozen scientific source, score unused walks on
inspected finals, resume Q, or train/reselect on any inspected final case.
The execution-informed mutation follow-up is a proposal only, not launched.

## Freeze sequence and design

Seed 2026101913; fixtures 1324; software fixtures 1325. Original registration
dea1f0f. Original fixture cost rule fails before research calls: twice the slowest
group mean applied to every planned input. Preserve profile_original.json and
original auditor. Explicit timing-only amendment abff7b9 pushed before discovery:
2× sum of individual discovery costs plus group-wise worst nominee validation/
final costs, same 600s projection threshold, 720s hard cap, all8poses and pool.
16walks projects648.06s/fails; 8walks458.44s/passes. No scores used for scheduling.
No frozen-source repair after data. Choices/selectiondata pushed74d6d17 BEFORE final.

Five P/Q-informed roots: P route/d9; Q fresh/mixed0 i1151; fresh/current1 i1146;
fresh/mixed2 i1480; carry/resample0 unmutated95gene i63. IntactVM separate, never an
ancestor. Native M local/all-on runtime, inputs, stopping,256gene limit and existing
one-edit mutation unchanged. No evolutionary feedback between walk steps.

Save240walks×16edits=3840mutation events/intermediategenotypes,240freshdraws and all
RNG. Scientific subset: first8walks/draws per5roots×3blocks=120walks, queried at
depth1/4/16 (360memberships),120freshdraws;1920walkmutation steps. All remaining
genomes preserved, fixture-profiled checkpoint scores not research selection.
Mutant sizes91–151,below ceiling. Three depth1 identities identical to root
genotype; all depth4/16 differ. Static opcode/channel summaries are not dynamics.

Discovery and validation each8contexts/768inputs; all8poses,2goals,prefix0/1,
straight/turning asymmetric arms,branches/corridors/isolated-goalNP. Common top2
discovery nominees, separatevalidation chooses1 perroot/block/arm. Final28contexts/
5184inputs (1728 eachfamily),prefix0/1/2,adds4/6and6/4arms,forks/twojunctions/real
alternativecycles. Contexts have newclutter; routeforms repeat andposes/depths are
correlated. Models frozenbeforefinal, no final-basedselection.

## Outcomes

Discovery per120 memberships:
- depth1:87counterchanges,7outputchanges,113retainroot skills,0scoreincreases.
- depth4:116counterchanges,26outputchanges,94retain,0scoreincreases.
- depth16:120counterchanges,75outputchanges,46retain,0scoreincreases.
- random:120counter/outputchanges,0retain,0scoreincreases.
Everycandidate0positiveprefixpairs. Forty-five depth16 outputsequences unchanged;
74scoredecreases,oneoutputchange without scorechange. Internalchanges≠usefulprogress.

Final63physicalrandommodels all0positiveprefixpairs and0twojunction/cyclepairs.
All15blocks fail correct/partial gate atdepth4and16; no extension. Strongroots
192/192corejunctionpairs +32stressforkjunctionpairs,224/864total,all1728corridors.
Qfresh0root96corepairs/1448corridors;Qcurrent1root144/1728. All selectedfalseNP0;
NPsuccess appliesonly isolatedgoal controls. No general solver/multirange/speedup.

One final-only partial gain: accessibility/Qfresh0/1/walk2/d16. Validation masks/
status exactlymatchroot,score0.262205,internalcountersdiffer. Finalcoreprefix1
score0.302841→0.400445,32improvingpairs across8cluttercontexts,new4/6and6/4arms only;
corridors1448→1600,corejunction96andNP1728retained. Zero new paired branches. It
passesfinal rootrelativepartialcriterion but failsvalidation andtwo-stagegate.
Other twoQfresh0 depth16selections lose oldskills; allotherdepth16 selectedmetrics
matchroots. Preserveexception,root,allwalkstates andearlierpopulationdiversity.

Posthoc independentdeque saved-output diagnostic (zero inference):304changed
rasters all equal source-stopped goal-distance balls;80budgetexhausted→emitted,
224emitted→emitted;152become correct,allcorridors,152remainwrong. Whole reachable
wave matches2936→3200/3456,notallcases. Outputequivalence only,notcausaledit or
hiddenalgorithm claim. No forcedtrace/ablation/stopping retune.

## Verification, costs and exclusions

Main797952physical/812160logicalcalls;133.24candidate seconds/720cap;
78071507543work,164.22swall,1141.39MiBpeakRSS. Discovery483physical/486identities,
validation124/126,final64/66 (includesintact). Profile91776calls,12.35candidate
seconds,15.48swall separate. Threecandidate/ninebaselineJITwarmupcalls separate.
BFS/A*/bitwave/intactall3456reachable+1728NPcorrect. No latencybenchmark.

Audit FIRSTATTEMPTPASS:889728exactcandidate replays,905280independentrasters,
15552baseline replays,240walks/3840mutations/240randomdrawsandRNG,allchoices,
geometry/exclusions/budgets,194source/11input/amendmenthashes,2644priorentries.
206.79swall,1189.19MiBpeakRSS separately. Active entrypoint:
`.venv/bin/python tools/audit_mutation_accessibility.py` uses frozen amended
auditor; original `study audit` invokes original superseded timing verification.
Do not rerun a completed audit without a new reason.

9newcore+1timingamendment+10relatedQ tests pass;283scopedtests collected,
NOTfreshfullsuite. Plot/report andsaveddata diagnosis make no candidatecalls.

ExcludeALL191784wholelayouts:187416throughQ +464fixtures +1632softwarefixtures
+320discovery +320validation +1632final. Helper `mutation_accessibility_data.exclusions()`
returnsTHROUGH Q ONLY. Append manifests at:
- results/mutation_accessibility_fixtures/mazes.json.gz
- results/mutation_accessibility/software_fixtures/mazes.json.gz
- results/mutation_accessibility/discovery/mazes.json.gz
- results/mutation_accessibility/validation/mazes.json.gz
- results/mutation_accessibility/confirmation/mazes.json.gz

Nextproposalonly: execution-informed versusuniform mutationtargeting,observation/
nativeparity first,sameeditvocabulary/runtime/roots/capacity,uniformtargetfloor,
freshcontrols,broadernewvalidation anduntouchedfinal. Observeroverheadcounted,
nooracle/knownsolverinjection,retentionandreplicationgatebeforeanylongsearch.
Capacityceilingnotbindingdoesnotdisprovegreaterheritablecapacity/regulation.
See results/mutation_accessibility/next_experiment.md. Preserveallpriorhashes.

R completion seals 269 source/artifact hash entries. The next audit must verify
2,913 prior entries (2,644 through Q + 269 R), plus its own registration.
