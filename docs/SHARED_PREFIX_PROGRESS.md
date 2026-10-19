# V12Q handoff — complete, October19,2026

Read `results/shared_prefix.md` first. Do not repeat or extend Q, resume an
unchanged search, alter frozen source, or train/reselect on inspected final cases.
Next V12R mutation-accessibility diagnostic is a proposal only, not launched.

## Frozen sequence and budgets

- Protocol/source/pools/fixtures4fafe1c before panel inference.
- Fixture timing-only amendmentb1b9530 before any research evaluation: original
  factor2 chose16generations (onlyfour queried poses); factor1.5 chooses32,
 526.57s projection. Original profile retained, no fixture scores inspected/used,
 no source/runtime change. Hard720s and100s final reserve unchanged.
- All populations/RNG/search/choices2ba193d before fresh final generation.
- Seed2026101912;fixture1314. Local/all-on M runtime,goalinputs,limits,256gene
 ceiling and one-edit mutation unchanged. No known solver in any population.

18conditions:carry/fresh ×3replicates ×current/mixed evolution or mixed resampling,
96organisms each. Exact initial pool/searchRNG matched within origin/replicate.
Carried pools protect9exact O/P/random-founder/resample anchors; fresh pools
are288new random founders. Sourceposition100%zero versus50%zero/50%one is the only
changed factor between evolution arms; same rank,lexicase,elite/archive/immigration.
32matched generations complete,coverall8poses. 41472births=24192mutated+17280random;
40176births entered training,1296generation32offspring are SAVED BUT UNQUERIED.
Four checkpoints and all18nextpopulations/RNG/events/rawmasks retained.

Validation8clutter contexts,768inputs/model. Initial442368physicalcalls logically
reused across3arms as1327104calls. Eachcondition36864train+6144validationcalls.
Final20contexts/4032inputs:1344branched,1344corridors,1344isolated-goalNP; matched
prefix0/1/2,arms2/3/4/6,8poses,2goals,fork/two-junction/truealternativecycles.
78aliases/32physicalmodels,includingoneintactknowncontrol. No final reselection.
Contexts/clutter independent draws;poses/goals/variants correlated,routeformsreuse.

## Findings

Everyprimary0/64validationprefix1corepairs and0/128final. All31physicalrandom-origin
finalmodels (secondaryarchives/anchors included)0positive-prefixpairs and0two-
junction/cyclepairs. Gate0/3carry,0/3fresh;no extension. AllselectedfalseNP0.

Final coreprefix0paircounts /128 perreplicate:
- carry current,mixed,resampling,frozen:128each in everyreplicate.
- fresh current[0,96,0],mixed[96,64,128],resampling[0,0,16],frozen[0,0,0].
Freshaggregate96/288/16/0 outof384 is secondary junction-only evidence,not gatepass.
Allcarryprimaries1344corridors;freshmixed[1128,1344,1344]. Freshmixed0 loses
corridorsvs1344frozen. Freshresampling2 gives464corridors;corridorarchivespreserved.

Freshmixed0 i1151,114genes,12edits fromfreshfounder95:initialsamevalidation0→32/64
junctionpairs,final96/128 atarms3/4/6allposes,nonearm2. Freshcurrent1 i1146,96genes,
16edits fromfreshfounder22:validation0→48/64,final96/128sixposesateacharmlength.
Freshmixed1 i1694,93genes,samefounder22/13edits:smallvalidation0,butfinal64pairs at
arms4/6allposes. Do not infer firstcausaledit without an independent transitiontest.

Freshmixed2 i1480,121genes,13edits fromrandomimmigrant i507,born8:128junctionpairs,
1344corridors+1344NP. Root ALREADY solveditsfirstsampledtrainingjunctionpair;
13edits are not established as necessary. Carrymixed0 i1638,94genes,5edits from
newrandomimmigrant i1152,not thepreserved routinglineage. Carryresampling0 unmutated
95gene i63 matches its160totalpairs(allprefix0forks)/1344corridors/1344NP.

Posthoc independentdeque saved-raster comparison: all2688reachable masks of
freshmixed2,carrymixed0 and95gene resample exactly equal source-stoppedgoal-distance
balls. Outputphenotype replication,not internalalgorithm/causalmechanism evidence.
No Q mechanismablation or forcedtrace. NPcontrols haveisolatedgoals only.

4952births descend fromP route9/16,maximumchain18–32edits(includesunqueriedlast
births);maxborn167genes<256ceiling. 538/5472samebatchparent-childcomparisonschange
mask/status. Inmixedsubset18/2823prefix-scoreimprovements:15higheraggregatefitness,
3lower;only2improvementsincarriedarms. Correlatedco-presencesubset;partialcredit
is notsolving,andaggregatefitness isnotlexicaseprobability. No strongbasis to
blame selection alone or claim a bindingcapacitylimit. Random-origintrack staysopen.

## Verification and costs

Main1345536physical /2415744logicalaliascalls;251.23candidate seconds/720cap,
146149776961work;searchwall324.35s+final15.92s;951.48MiBpeakmainRSS. Fixtureprofile
27648calls,5.14candidate seconds separately. Unusedallowance notspentafterresults.
IntactVM/BFS/A*/bitwave all2688reachable+1344NPcorrect. No latencybenchmark/speedup.

Audit firstattempt PASS:1373184exactcandidate replays,1385280independentlygraded
rasters,12096baselines,all41472births/24192mutations/18states/78aliases;
190source/9input/2384priorcompletionhashes. Audit352.05s,1047.92MiBpeakseparately.
Scheduleaudit checks amendmentcommit,all8poses and logical/physicalcounts/times.
10new+22relatedtests pass;273collected within tests/,notfreshfullsuite. An initial
unscoped collection hitvendoredplottinglibrarymissingtestdeps;scopedcollectionpasses.
No frozen-sourcerepair. Posthoc diagnostics/tools are explicit saved-data analyses.

## Next independent exclusions

Exclude ALL187416wholelayouts:181928throughP +1424uniquepreflight/softwarefixtures
+320validation +2560training(allunqueriedposesincluded) +1184final.
`shared_prefix_data.exclusions()` returns THROUGH P ONLY. Append:
- results/shared_prefix/software_fixtures/mazes.json.gz
- results/shared_prefix_fixtures/mazes.json.gz
- results/shared_prefix/validation/mazes.json.gz
- results/shared_prefix/train/mazes.json.gz
- results/shared_prefix/confirmation/mazes.json.gz

Nextproposal `results/shared_prefix/next_experiment.md`: performance-blind mutation
accessibility nearseveralindependentlyrootedwavephenotypes,short/longwalks and
freshrandomcontrols,asymmetricnewgeometry,strictnormaloutputconfirmation. No known
solverinjection or automaticlongsearch. Preserveeveryoldpopulation/source/result.

Q completion packet seals260 source/artifact hashes. Next audit should verify
2644 prior completion entries (2384throughP +260Q), plus its own registration.
