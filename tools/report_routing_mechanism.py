"""Write the V12T report and handoff from audited evidence, no inference."""
from pathlib import Path
import sys,json,re
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.routing_mechanism_data import OUT,FIXTURES,ROOT,read_compressed

def main():
    panel=read_compressed(OUT/'panel.json.gz');metrics=read_compressed(OUT/'metrics.json.gz');analysis=read_compressed(OUT/'analysis.json.gz')
    execution=json.loads((OUT/'confirmation/execution.json').read_text());audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    fit=json.loads((OUT/'predictor_fit.json').read_text());trace=json.loads((OUT/'trace_summary.json').read_text())['results']
    calibration=json.loads((FIXTURES/'native_cost.json').read_text());aliases=panel['aliases'];names=('fresh0','fresh2','carry0','carry1','spliced')
    table=[];mechanism=[];ordinary=[];predict=[];screens={}
    for name,pid in aliases.items():
        s=metrics[pid+'|normal'];families=s['families'];good=[d for d in s['details'].values() if d['complete'] and d['prefix']>0]
        ordinary.append(f"| {name} | {families['ordinary_perfect']['optimal']} | {families['ordinary_random']['optimal']} | {families['corridor']['optimal']} | {families['disconnected']['no_path']+families['ordinary_disconnected']['no_path']} |")
        groups=defaultdict(list)
        for k,d in s['details'].items():groups[k.rsplit('/pose',1)[0]].append(d)
        full=[v[0] for v in groups.values() if len(v)==8 and all(d['complete'] for d in v) and v[0]['prefix']>=4]
        screen=(len({d['template'] for d in full})>=2 and len({d['shape'] for d in full})>=2 and any(d['graph']!='fork' for d in full))
        screens[name]=dict(full_long_prefix_groups=len(full),structural_screen=screen)
        if name not in names:continue
        cmp=analysis['comparisons'][name]
        roots=','.join(cmp['roots']);rootpositive=set()
        for r in cmp['roots']:rootpositive.update(k for k,d in metrics[aliases[r]+'|normal']['details'].items() if d['complete'] and d['prefix']>0)
        table.append(f"| {name} | {roots}: {len(rootpositive)} | {s['positive']} | {sum(d['graph']=='two_junction' for d in good)} | {sum(d['graph']=='cycle' for d in good)} | {max(max(d['route_lengths']) for d in good)} |")
        me=analysis['interventions'][name];mechanism.append('| '+name+' | '+' | '.join(f"{me[k]['retained']}/{me[k]['normal_success']}" for k in ('pulse_off','flag_off','both_off','output_feedback_off','endpoint_off','halt_off'))+' |')
    for name,k in fit['prospective_fixed_k'].items():
        f=fit['models'][aliases[name]]['paired'];predict.append(f"| {name} | {k} | {f['matches'][k]}/{f['inputs']} ({100*f['matches'][k]/f['inputs']:.2f}%) |")
    assert not any(screens[name]['structural_screen'] for name in aliases if name!='intact')
    text=f'''# V12T: acquired routing mechanisms and structural transfer

Complete and independently audited. This fixed-panel study confirms that both
selected fresh descendants acquired goal-dependent branching abilities absent
from their exact random immigrant roots. It also finds a preserved specialist
that completes paired20-edge routes in particular orientations. These are real,
limited capabilities; no random-origin model passes the registered transfer
screen or handles the non-isolated disconnected cases.

The simple finite-pruning explanation from S is incomplete. Prospective matches
fall to54–61% of branched normal rasters. Different lineages use different goal
inputs and output feedback; all five depend on their native halt request for
the tested successes. This points to coordination of propagation, selective
output and emission timing, rather than a single universal pruning mechanism.

![Root comparisons and prospective predictor fit](routing_mechanism/comparison.png)

## What was frozen and tested

Registration/panel/source pushed in907f96d before final generation. No new
evolution, candidate editing, breeding, selection or final-based replacement.
The12identities are five S-informed descendants, their five distinct roots,
the preserved68-gene random resampling control and separate intact VM control.
All use the same local M runtime and existing256tick/work limits. All787saved
ancestral birth events are reconstructed, including both parents of splices.

Four independently seeded33x33structural contexts cover straight arms, both
arms bending, one bending, and outward hooks. Within each, arms stay fixed while
source prefix varies0/1/2/4/6/8straight or4/6/8bent, and graphs vary fork,
second junction at distance1/2, or true alternative cycle at distance2/3.
Both goals and all8rotations/reflections are tested. Four contexts are the
structural sampling units: thousands of poses/variants are not independent
replicates. Shape and tail length are confounded between contexts; source
distance and bend contrasts within a context retain downstream geometry.

Per model:2880branched inputs/1440pairs (1280positive-prefix pairs),576matched
corridors,512non-isolated structured disconnected inputs,384ordinary reachable
inputs and128ordinary partition-disconnected inputs. Ordinary inputs are48new
9x9bases (24Wilson,24random) plus16disconnected bases,all8poses. No direct S/T
score change can be attributed to evolution: genomes are fixed and test cases
and grammar differ. New clutter prevents exact-layout reuse but does not itself
establish structural novelty. New hook shapes provide a specific transfer test.

## Exact roots versus descendants

A complete pair means two different goals on the SAME layout both receive
correct normal shortest-path rasters. All root-positive counts below are zero
on this corpus; roots can still solve source-at-junction or ordinary tasks.

| Descendant | Exact root positive pairs /1280 | Descendant /1280 | Positive two-junction pairs | Positive cycle pairs | Longest paired route, edges |
|---|---|---:|---:|---:|---:|
{chr(10).join(table)}

Fresh0 grows from96to163genes over96mutations; fresh2 from119to160over75.
Fresh0's root already solves576/576corridors, so its acquired ability is branch
choice, not the origin of all routing. Fresh2's exact root solves no pairs or
corridors here. Fresh2 completes all four prefix1fork contexts in all8poses,
including13-edge hook routes. Fresh0 succeeds in two poses per context, with no
positive-prefix context correct in all8poses. Both fail positive extra junctions.
Increased program length accompanies these histories; this is not a causal
capacity test and does not establish that larger genomes are necessary.

The68-gene historically selected, unmutated random draw also completes32/1280
positive pairs, matching fresh2's paired count, though ordinary scores differ.
It is a capable selected random draw, not an average unselected genome. The
root comparison now establishes acquisition along these selected lineages;
it does not establish a replicated evolutionary-policy advantage over random
resampling or identify the causative edit.

Carried0 is12mutations from narrow-Branch. It gains289all-prefix pairs and loses3
versus its root, including168newpositive pairs. Carried1 is124mutations from
broad-Branch and gains203all-prefix pairs,116positive. Its68positive pairs at
prefix>=4include28extra-junction/cycle pairs. Five paired20/20-edge successes
occur in the ONE hook context: two straight-prefix fork poses, two second-
junction poses and one bent-prefix fork pose. Its two positive cycle pairs
are one orientation of the straight context at prefixes4and8 (shortest8/9
and12/13edges; alternatives20/21and24/25). No positive-prefix group works in
all8poses for this specialist. Preserve it despite its lower aggregate score.

Spliced0 has96positive pairs,including32two-junction pairs but no positive cycle
pairs. It gains204all-prefix pairs and loses2relative to its three-root success
union. Its ancestry includes249splices AND mutations; this comparison cannot
credit a particular splice or demonstrate functional-module composition.

The registered long-prefix transfer screen fails for every random-origin model:
none has even one prefix>=4group correct in all8poses. Ordinary and corridor
skill loss remains visible rather than being hidden by branch-score gains.
Context bootstrap intervals are conditional descriptions of four contexts and
these selected lineages. Some are degenerate because all four context deltas
are equal; that does not imply certainty about new geometries or discoveries.

## What the interventions establish

All six interventions were fixed in advance, applied to the five descendants
and intact control on1280inputs/model: four contexts, prefixes1/2/4straight and
4bent, all graphs/poses/goals. Roots receive normal tests only. The table counts
retained normal-successful PAIRS, not individual inputs; every denominator is
the model's genuine normal successes on this subset.

| Model | Pulse off | Static flag off | Both off | Output feedback off | Goal endpoint check off | Halt request off |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(mechanism)}

Fresh0 needs the initial pulse for these successes; fresh2 instead needs the
static goal flag and retains all32pairs with output feedback suppressed.
Carried0 needs static flags and output feedback. Carried1 and spliced0 retain
some successes with either goal input available, but none when both are removed.
Flag removal also produces four new carried1pairs; loss and gain are separate.
Feedback ablation zeroes channel2 reads only, preserving stores, final emission
and endpoint checks. Its effect is not simply deleting the output raster.

Disabling the goal-output endpoint check retains every tested normal success.
Disabling the source halt request loses all of them under the remaining normal
quiescence rules. Thus these outputs are tied to emission timing; they need not
be stable attractors to be legitimate algorithms. This does not mean endpoint
checking is useless generally, nor that every earlier hypothesis about pulse or
feedback dependence applies across lineages.

## Fixed-pruning hypothesis and bounded trajectories

The S-informed predictor uses an evaluator-only goal-distance ball of radius
equal to source-goal distance, then a fixed number of endpoint-protected leaf
deletion rounds. Its parameters were frozen before T; no fitting on T selects
a replacement algorithm. Exact raster matches include failures.

| Model | Pruning rounds fixed from S | Branched normal-raster matches |
|---|---:|---:|
{chr(10).join(predict)}

The lower prospective fit and fresh2's feedback independence refute treating
this observer as a complete causal account. It remains a partial descriptive
approximation. Oracle distances never enter candidate inference or reproduction.

All2304forced traces reach64ticks,147456frames, retaining native work caps.
The goal inputs are toggled only as preregistered; both-off paired states are
identical throughout. Of five random-origin descendants, only carried1 has
normal-failed tasks with later correct geometry: five individual tasks in the
fixed128-input trace subset. Other four have zero such cases. Carried1 has
three pairs with simultaneous shortest geometry at some forced tick; this is
diagnostic geometry, not successful native inference or a retuned stopping rule.
Correct frames are frequently transient and the two goals need not be correct
at the same global tick, even when both native outputs are valid. Longer time
alone is therefore not a supported general remedy. This horizon/subset cannot
rule out all longer-time phenomena. All exact states remain saved.

![Normal source-distance examples](routing_mechanism/normal_outputs.png)

## Ordinary transfer and retained skills

| Model | Wilson shortest /192 | Random shortest /192 | Corridors /576 | Correct non-isolated no-path /640 |
|---|---:|---:|---:|---:|
{chr(10).join(ordinary)}

All11random-origin models fail all640non-isolated disconnected cases; none
falsely reports no-path on a reachable input. Best ordinary score is the frozen
broad root60/384, while its descendant scores26. Carried0 scores40versus its
root38. These tradeoffs argue against replacing the preserved diversity with
the best branch specialist. S's74/384was a different selected model/corpus;
this study neither repeats that benchmark nor establishes a temporal decline.
BFS,A*,bitwave and intact VM each solve3840/3840reachable and640/640disconnected
inputs. No latency benchmark, multirange advantage or speedup is claimed.

## Feasibility, cost and audit

The first geometry fixture failed before any candidate call: a cycle attachment
at distance1made its alternate raster chorded, and a length assertion omitted
attachment distance. All4480rejected inputs remain preserved and excluded.
Correction precedes calibration/registration. The first draft profile projected
1990.23seconds, failing feasibility. Before registration, normal cost was
separated from diagnostic parity, interventions were limited to descendants and
intact, and a fixed timing-only8then4context rule selected4contexts:621.25versus
394.29seconds with2xsafety against a600second planning allowance. Hard cap720
remained unchanged. Original draft source, rejected data, failed profile and
all recalibration outputs are preserved. No score-dependent sizing and no
post-registration scientific-source repair occurred.

Main inference:{execution['budget']['calls']:,}calls,
{execution['budget']['seconds']:.2f}/720candidate seconds,
{execution['budget']['work']:,}charged work units;
{execution['wall_seconds']:.2f}s wall,
{execution['peak_rss_bytes']/2**20:.2f}MiB peak RSS. The separate cost pilot,
including refinement, uses{calibration['budget']['calls']:,}calls and
{calibration['budget']['seconds']:.2f}/180candidate seconds. Warmups are separately
recorded. Equal caps do not imply equal work; diagnostic setup is not a latency
comparison with native inference or conventional solvers.

Audit passes: {audit['counts']['candidate_replays']:,}exact candidate replays,
{audit['counts']['independently_graded_rasters']:,}independently graded response rasters,
{audit['counts']['baseline_replays']:,}baseline replays,
{audit['counts']['predictor_masks']:,}independently constructed predictor masks,
{audit['counts']['independent_adapter_parity']:,}legacy-adapter checks,
all787ancestral events, all4677prior completion hash entries,
{audit['source_hashes']}source/{audit['input_hashes']}input hashes. All trace states
are exactly replayed and frame summaries recomputed. New feedback/halting modes
have synthetic semantic tests and normal native parity, not a separately coded
full interpreter. Audit wall{audit['wall_seconds']:.2f}s,
{audit['peak_rss_bytes']/2**20:.2f}MiB peak RSS. Eleven new plus29related tests pass;
this is not a fresh full-suite run. All225592whole layouts through T must be
excluded next, including rejected/corrected fixtures and every final pose.

## Next research decision

Do not launch another unchanged long evolution run or inject the explanatory
predictor. First map the preserved12-edit carried0lineage on a NEW matched
corpus, with its exact root, every intermediate and final descendant fixed
before generation. Locate which inherited changes alter branch suppression and
native stopping, and preserve the longer-prefix specialist and fresh2 as separate
comparators. Any later edit-reversion study needs its own frozen design and new
data; these final inputs cannot select edits.

This is more informative than immediately increasing time or raw capacity:
goal-dependent branch selection has now been acquired demonstrably, propagation
already spans13–20edge routes in some contexts, yet selective output and correct
stopping do not transfer reliably as source/junction arrangement changes. A
subsequent controlled evolution can target the identified limitation while
retaining corridor, ordinary and rare long-prefix skills. Fresh random-origin
populations remain central; all original populations/RNG are preserved. Larger
semantic recombination modules remain a future representation hypothesis.
'''
    # Human-facing report typography; identifiers remain exact in panel.json.gz.
    for old,new in [('fresh0_root','fresh 0 root'),('fresh2_root','fresh 2 root'),('narrow_root','narrow root'),('broad_root','broad root'),('shared_root','shared root'),('fresh0','fresh 0'),('fresh2','fresh 2'),('carry0','carried 0'),('carry1','carried 1'),('random68','random 68')]:text=text.replace(old,new)
    text=text.replace('V12T','VTTOKEN').replace('907f96d','REGTOKEN').replace('33x33','33 × 33').replace('9x9','9 × 9').replace('prefix>=4','prefix ≥ 4')
    text=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',text)
    text=text.replace('VTTOKEN','V12T').replace('REGTOKEN','907f96d')
    text=re.sub(r',(?=[A-Za-z])',', ',text)
    (ROOT/'results/routing_mechanism.md').write_text(text)
    (OUT/'transfer_screen.json').write_text(json.dumps(dict(interpretation='Conservative reading of preregistered all-eight-pose long-prefix structural criterion; all random-origin models fail before false-no-path retention is relevant.',models=screens),indent=2)+'\n')
    (OUT/'next_experiment.md').write_text('''# Proposed next step after V12T

Proposal only; not launched or preregistered. T is closed and audited. Do not
extend it, resume S or tune/reselect against inspected T final cases.

Freeze the narrow-root -> carried0 12-edit lineage, all13exact historical
programs, with fresh2/exactroot and carried1/broadroot as preserved comparators.
Use a new excluded-layout corpus with more independent structural contexts,
matched source/junction distances and goal bends, plus retention controls.
Use native inference first and the now-tested separate pulse, static flag,
output feedback and halt-request interventions on a fixed diagnostic subset.
Compare consecutive genotypes on identical new cases, including lost abilities.
This maps candidate transitions; if several edits interact, a later frozen
reversion/combination experiment is needed for attribution. Do not synthesize
solver logic or transplant the oracle-based finite-pruning observer.

T establishes selected-lineage acquisition, not general solving or a universal
pruning mechanism. Five descendants use distinct input/feedback strategies;
simply waiting longer does not rescue most tested failures. Preserve the
orientation-sensitive20-edge specialist and the68-gene random control. Their
aggregate score must not erase their differing evidence. One result from four
contexts is not a replicated evolutionary-policy effect.

Only after locating a useful change should we choose a controlled evolution
pressure or representation adjustment, with fresh random origins, carry origins,
resampling, retained diverse anchors and equal evaluation budgets. More raw
capacity, longer runs and stronger semantic recombination remain hypotheses,
not automatic consequences of this assay. All225592whole layouts through T,
including rejected fixtures, are excluded from future independent data.
''')
    handoff='''# V12T mechanism and transfer handoff

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
'''
    (ROOT/'docs/ROUTING_MECHANISM_PROGRESS.md').write_text(handoff)

if __name__=='__main__':main()
