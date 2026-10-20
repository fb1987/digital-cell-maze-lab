"""Update mutable navigation after V13A sealing; never modify old sealed evidence."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/branch_overgrowth'
s=json.loads((OUT/'completion.json').read_text());assert s['audit_passed'];n=len(s['source_and_artifact_sha256']);total=7880+n
block=f'''Current checkpoint: **V13A is complete and independently audited**. Read
`results/branch_overgrowth.md` and `docs/BRANCH_OVERGROWTH_PROGRESS.md` first.
Do not repeat/extend A or Z, silently resume populations, or train/reselect on
inspected final data. No new evolutionary or sexual study is launched.

V13A registration 676e418 pushed before scientific generation. Seed2026102006,
fixture1444. Z-informed panel25 exact genomes:9 Z fresh primaries,12 exact
roots/parents, historical long/short specialists,random68,intact. All95 ancestral
birth events replayed. No editing/training/selection/breeding. Native local,
exposure7,256 genes/normal ticks; 96tick bounded forced traces retain work caps.
All7880 prior hash entries verify. Preserve all old populations/RNG/diversity.

12 contexts,8poses,2goals,prefix0/1/2/4/8, matched fixed-cell fork/second-junction/
real alternative cycles,straight/bent stems.5312 inputs/model:800pairs,1600corridors,
384ordinaryreachable,1728disconnected. New clutter/layouts in Z grammar, NOT novel
structural topology. Contexts independent seeded draws; poses/variants correlated.
Normal primary Z pairs:mutation[96,96,96],family[96,0,96],resample[96,96,96]/800;
all source-at-junction forks. All9 Z selections0upstream/second-junction/cyclepairs,
1600/1600corridors,0/384ordinary,0/1728no-path,0false reachable no-path claims.
Changed corpus prevents Z/A raw-count comparisons as ability gains/losses.

Exact ordinary-mutation roots0pairs each; descendants96each, no pair losses,
29/7/11 Z mutation births. Immediate parents already96each, same successful pairs.
Family root28/0/96→descendant96/0/96, immediateparents96/0/96. This demonstrates
selected-lineage acquisition, NOT a replicated policy/capacity advantage;
resampling matches. Root mutation1 falsely calls all3584reachable no-path.

Historical long specialist344/800pairs,208/640upstream,46/160prefix4,30/160prefix8,
8upstreamcyclepairs (4eachprefix4/8),12upstreamsecond-junctionpairs;ordinary14/384,
corridors1476/1600. Historical short/random68 each192pairs,96upstream prefix1,
ordinary8/384,corridors1600. Preserved skills, NOT A evolution. BFS/A*/bitwave/intact
solve3584reachable+1728disconnected. No latency/multirange/speedup comparison.

Interventions13targets atprefix0/1/4,480pairs+960corridors/model. Pulse-off retains
all96pairs for mutation0/2,resample0/1; flag-off losesall. Mutation1,family0/2,
resample2 show opposite. Both-off0pairs alltargets; endpoint-off retainsall.
Halt-off losesallZpairedsuccesses; historical long retains18/266,intact480/480.
No intervention creates a new pair; necessity claims restricted to normalsuccesses.

3120scientific forced traces×96=299520frames,60tasks/model/mode; modesnormal/pulse/
flag/both-off. Allboth-off paired statesidentical. In normal-rule Z traces540tasks,
428normalfailures NEVER shortest atanytick. All9 selectionsrepeatfullstates:
6fixedpoint,mutation1/resample1period4,family2period8. Eight selections illuminate
exact fullsourcecomponent at96 onall60tasks;family2 differs. Repeatedstate output
is persistent failure, not latent correct solving. No Z final96framecorrect.
Fullcomponentcounts retrospective saved-state diagnostic; underlying states
replayed. Historical long2/14failedtraceshave latercorrectframes,0failedpairs
laterjointcorrect; no new normal success. Forced frames never count as solutions.

Main94.55/720candidate sec,260720calls,45767464419work,105.65wall,239.56MiBRSS.
Calibration12.33/180candidate sec,27560calls. Mainbaseline15936calls separately.
FirstauditPASS143.49s,1215.28MiBRSS:288280exactcandidate replays,305308independent
response grades,17028baseline replays,15340legacyadapterchecks,449280traceframes
inclfixtures,243source/9inputhashes. Allframe summariesrecomputed; no separate
fullinterpreter forhalt-off. Nine new+eleven relatedtests pass;2replayisolation
checks separately; NOTfreshfullsuite. No scientificsource repair/deviation.

Exclude ALL **275168 whole layouts** throughA using
results/branch_overgrowth/whole_layout_exclusions.json.gz pluslaterfixtures.
Completion seals{n}entries;futureprior total{total}. Future re-audits use
tools/replay_branch_overgrowth_audit.py; writes separate packets under output/,
never raw audit over sealed audit.json. All source/rasters/trajectories preserved.

Next proposal ONLY: controlled selective-output acquisition pilot. Current
fitness ALREADY penalizes branches; demonstrate a distinct useful objective on
complete/partial/empty/flooded masks before one pressure change. Matched current
pressure, frozen/resampling controls, fresh random plus explicitly continued
origins, common protected skill diversity; no oracle cleanup. New normal upstream
paired gains, retention and2/3replicates gate75min. Sexual actual-transfer gate
still unmet. See results/branch_overgrowth/next_experiment.md.

'''
p=ROOT/'AGENTS.md';t=p.read_text();assert 'Current checkpoint: **V12Z' in t;t=t.replace('Current checkpoint: **V12Z','Historical V12Z checkpoint: **V12Z',1);t=t.replace('## Immediate first task\n\n','## Immediate first task\n\n'+block,1);p.write_text(t)
progress=f'''# V13A complete and audited

Read [the report](../results/branch_overgrowth.md) and
[the next proposal](../results/branch_overgrowth/next_experiment.md).

Waiting does not rescue the Z failures: 428 normally failed traced tasks have
zero shortest frames in 96 ticks. All nine Z selections repeat full states;
eight illuminate their entire source component by tick96. Removing the halt
request loses every Z paired success. These are bounded mechanism findings,
not a claim that random-origin general solving is impossible.

Positive acquisition evidence: ordinary-mutation roots each score0/800 pairs;
their descendants each96/800. Immediate parents already have those abilities.
Resampling also reaches96/800. All these are source-at-junction forks; no Z
selection solves an upstream pair. The historical specialist still solves208/640
upstream pairs, including true cycles, and stays protected.

Registration676e418 precedes new data;25genomes,95ancestral events,12contexts,
5312inputs/model. Main94.55candidate seconds,105.65wall; audit143.49seconds.
288280exact replays,305308independent raster grades and all trace states verify.
20focused tests plus2replay-output isolation tests pass, not a full suite.
No scientific-source repair or protocol deviation.

Exclude275168 whole layouts through A. Completion adds{n}sealed entries;
future prior total{total}. Re-audit using tools/replay_branch_overgrowth_audit.py,
which preserves sealed originals. Never resume closed studies or train/reselect
on inspected final data. All checkpoints and useful diversity remain intact.

Next: design a distinct output-selectivity pressure and test it against current
pressure, with matched ancestry/evaluation budgets and frozen/resampling controls.
The current objective already penalizes branches; verify the proposed difference
before registration. A small controlled pilot must qualify before long compute.
No next experiment or sexual comparison is launched.
'''
(ROOT/'docs/BRANCH_OVERGROWTH_PROGRESS.md').write_text(progress)
p=ROOT/'README.md';t=p.read_text();marker='## Current checkpoint — October 20, 2026\n\n';assert marker in t
intro='''The [V13A branch-overgrowth assay](results/branch_overgrowth.md) is complete and
independently audited. **Waiting does not rescue the new Z lineages:** 428 failed
traced tasks never show a correct path across96ticks, and removing the halt
request destroys their paired successes. Continued updates usually spread output
across the entire connected component.

There is real, limited acquisition: all three ordinary-mutation descendants
solve96/800goal pairs absent from their exact random roots. Resampling matches
this elementary skill; none of the nine Z selections solves an upstream pair.
The preserved specialist still solves208/640upstream pairs, including cycles.

![Recorded spreading after native stopping](results/branch_overgrowth/trajectories.png)

Main inference takes94.55candidate seconds; the full audit passes. All data and
old populations remain preserved. Exclude **275,168 whole layouts** in future
independent work. The [next proposal](results/branch_overgrowth/next_experiment.md)
is a controlled output-selectivity acquisition pilot, with existing pressure as
the control. No further experiment has launched; sexual work remains gated.

## Completed family-reserve comparison V12Z

'''
t=t.replace(marker,marker+intro,1);p.write_text(t)
p=ROOT/'docs/LONG_SEARCH_SETUP.md';t=p.read_text();t=t.replace('# Longer evolution run status\n\n','# Longer evolution run status\n\nV13A is now complete: [report](../results/branch_overgrowth.md). Waiting does not\nrescue the Z failures. The proposed next controlled pilot targets output\nselectivity; no further long or sexual run is launched. Exclude275168layouts\nthrough V13A using results/branch_overgrowth/whole_layout_exclusions.json.gz.\n\n',1);p.write_text(t)
p=ROOT/'results/long_search_setup/family_crossover_75m.json';v=json.loads(p.read_text());v['whole_layout_exclusion_file']='results/branch_overgrowth/whole_layout_exclusions.json.gz';v['known_excluded_layouts']=275168;v['evidence']['results/branch_overgrowth/completion.json']=hashlib.sha256((OUT/'completion.json').read_bytes()).hexdigest();p.write_text(json.dumps(v,indent=2)+'\n')
print(dict(handoff_updated=True,prior_total=total))
