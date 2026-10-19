"""Refresh mutable repository handoffs after successful V12S verification."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.composition_data import OUT,ROOT


def main():
    a=json.loads((OUT/'audit.json').read_text());assert a['passed']
    s=json.loads((OUT/'search_execution.json').read_text())
    f=json.loads((OUT/'confirmation/execution.json').read_text())
    d=json.loads((OUT/'descriptive_outcomes.json').read_text())
    total=lambda k:sum(c.get(k,0) for c in d['reproduction'].values())
    handoff=f'''# Compatible recombination study handoff

V12S is complete and independently audited. Read `results/composition_study.md`
and `results/research_reset/assessment.md` first. The user-authorized three-step
reassessment is complete. Do not repeat/extend S, resume historical searches,
edit frozen scientific source, or train/reselect on inspected final cases.

## Protocol and execution

Registration `f650b93`, feasibility profile `4750c0f`, all selections/populations
and search data `b9f8a7f` pushed before final generation. Seed2026101914;
fixtures1334; schedule software1335. The exhausted old DFS fixture supplier was
corrected to Wilson before registration and candidate calls. Its partial data
remain preserved and are a subset of corrected fixtures. No post-registration
scientific-source repair or budget extension.

18 conditions: carry/fresh by mutation/recombination/resampling by three RNG
replicates, 96 organisms each. Carry protects16 historical random-origin identities;
fresh founders and immigrants are new random draws. No known solver in ancestry.
All use the unchanged common local runtime and256-gene bound. Recombination tries
32 compatible complementary splices per condition/generation, followed by the
same one-edit mutation. Two-parent ancestry is authoritative in `birth.parents`.
Legacy `parent` is recipient only; do not infer full ancestry from that field.

{s['generations']} matched generations in {s['wall_seconds']/60:.2f} minutes under
the75-minute wall allowance, stopping at `wall_reserve`. Search {s['budget']['calls']:,}
physical calls; main including final {f['budget']['calls']:,} calls,
{f['budget']['seconds']:.2f}/5400candidate seconds and {f['budget']['work']:,} work.
Profile17792calls separately. Last-generation {total('last_generation_unevaluated_births'):,}
offspring are saved but unevaluated. All18 populations/RNG and every32-generation
checkpoint remain intact. Equal evaluation counts do not mean identical work.

## Main evidence and limits

Final41physical models behind89aliases,7424inputs/model. Structured1152pairs,
864positive-prefix pairs,2304corridors,2304isolated-goal no-path inputs; ordinary
384reachable and128partition-disconnected inputs.28 structured contexts; all8poses
and paired goals, prefixes0/1/2/4, forks/twojunctions/realalternativecycles. The
structured route forms recur from validation: new clutter is not arbitrary
structural generalization. Poses and variants are correlated.

Carried positive pairs by replicate: mutation[512,390,512], recombination[448,512,224],
resampling/frozen[224,224,224]. Fresh: mutation[132,0,224], all other primaries0.
Only carry/recombination replicate1 passes both-stage gate; neither origin passes
required2/3. That passing selection i14092 has ZERO splice ancestry and is six
mutation steps from historical narrow-Branch i5140. Do not credit sex for it.

Actual splices{total('splices'):,}/{total('attempts'):,} attempts; only
{total('multi_instruction_donor_segments'):,} transfer multiple instructions.
{total('positive_pair_donor_gain'):,} have a donor paired-score advantage.
{total('direct_spliced_children_retained_at_least_once'):,} direct spliced children
are retained at least once. Carry/0 recombination i20652 has three historical
roots and249 distinct ancestral splice events,448positivepairs and368 beyond the
root-success union, but no positive extra-junction pairs; mutation control512.
Mutation and selection also occur along its graph; no causal module-composition claim.

Preserve carry/1/mutation i18358:390positivepairs,86atprefix4 (including6twojunction,
4cycle), paired routes up to10edges. Lower aggregate score does not erase this skill.
Fresh/0/mutation i13694 gives132positivepairs,noneall8poses,up to8edges; rooti288,
96mutation steps. Fresh/2/mutation i18042 gives224prefix1forkpairs,all28contexts
all8poses,up to7edges; rooti2958,75mutation steps. Both roots are new random
immigrants, not known algorithms. Exact roots were not in final panel; do not
attribute a particular functional transition without new comparison.

Highest ordinary result74/384, all40random-origin models0/128ordinary no-path.
Some match2304/2304isolated-goal controls only. BFS/A*/bitwave/intactVM all correct.
No latency benchmark, causal multirange advantage or general solver demonstrated.
Saved normal raster examples show residual branches as prefixes lengthen; mechanism
is a hypothesis, not a new ablation result. Preserve old capabilities and controls.

Post-hoc saved-mask observer, zero candidatecalls: goal-distance ball plus1round
leafpruning fits2016/2304branched rasters forfresh2mutation; plus2rounds fits2016
foractualsplicedcarry0; plus3rounds fits2048forcarry0mutation. Fitsincludeerrors,
notadditionalcorrectsolutions. Predictorusesoracle distances outsideinference;
do notinjectit intoagenome orclaiminternalcausalmechanism. Othervariantsfitlesswell.
See raster_hypothesis_fit.json and the report's disclosed post-hoc interpretation.

## Verification and restoration

Audit passes first attempt: {a['exact_candidate_replays']:,} exact candidate
replays, {a['independently_graded_candidate_rasters']:,} independently graded
candidate rasters, {a['baseline_replays']:,} baseline replays, all fitness arithmetic,
births/edits/splices/RNG/populations/archives and all2913priorhashentries.
All nontraining outputs replayed; training exact replay uses preregistered1/256
sample plus independent grading of every evaluator-positive valid/correct-no-path row. Do not
claim full training inference replay. Audit wall{a['wall_seconds']:.2f}s,
peak{a['peak_rss_bytes']/2**20:.2f}MiB. Ten new tests pass;293collected, notfullsuite.

The199165540byte reproduction log is in six lossless remote byte chunks under
`reproduction_parts/`. The local original remains intact but is gitignored.
After cloning, run `.venv/bin/python tools/archive_composition_births.py restore`
BEFORE frozen audit or prior-hash verification. Per-part and full-log hashes are
checked; completion also verifies the bytes were present in the selection commit.
Scientific source is unchanged. Plotting dependencies are separate and recorded.

Exclude ALL **{a['whole_layouts']:,} whole layouts through S**. The S data helper
`composition_data.exclusions()` returns only THROUGH R. Future code must also add
`composition_fixtures/mazes.json.gz`, `composition_study/schedule_fixtures/mazes.json.gz`,
`composition_study/validation/mazes.json.gz`, EVERY `composition_study/train/g*/mazes.json.gz`,
and `composition_study/confirmation/mazes.json.gz`. Include unqueried poses and all
ordinary inputs; rejected preflight is already contained in corrected fixtures.
A consolidated hashset is also saved in `whole_layout_exclusions.json.gz`, with
`exclusion_sources.json` recording the source manifests and audited total.

The next mechanism/transfer comparison is a proposal only in
`results/composition_study/next_experiment.md`. No further experiment launched.
'''
    (ROOT/'docs/COMPOSITION_PROGRESS.md').write_text(handoff)
    agents=ROOT/'AGENTS.md';text=agents.read_text()
    anchor='Current checkpoint: **V12S is complete' if 'Current checkpoint: **V12S is complete' in text else 'Active authorized goal: **three-step research reassessment'
    start=text.index(anchor)
    end=text.index('Historical checkpoint: **V12R',start)
    block=f'''Current checkpoint: **V12S is complete and independently audited**. Read
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

Audit firstattemptpasses{a['exact_candidate_replays']:,}exactreplays,
{a['independently_graded_candidate_rasters']:,}gradedrasters,allbirths/RNG/fitness
and2913priorhashes. Trainingexactreplayissampled1/256;do notclaimfullinferenceaudit.
10newtestspass,293collected,notfreshfullsuite. AllfrozenSscientificsourcesunchanged.
Afterfreshclone,restorebyte-identicalancestrylogBEFOREaudit/priorchecks with
`tools/archive_composition_births.py restore`;sixremotechunks preserve199165540bytes.
Excludeall{a['whole_layouts']:,}wholelayoutsthroughS; helperexclusions()onlythroughR,
soaddSfixtures,schedulefixtures,validation,EVERYtraingeneration,andconfirmation
manifests as specified in COMPOSITION_PROGRESS. Nextmechanism/transferproposal
is NOTlaunched. Noautomaticunchangedlongsearch orrecombinationextension.

'''
    agents.write_text(text[:start]+block+text[end:])
    readme=ROOT/'README.md';text=readme.read_text();marker='## Current checkpoint — October 19, 2026\n\n'
    start=text.index(marker)+len(marker)
    historical='## Completed mutation-accessibility study V12R\n\n'
    end=text.index(historical,start)+len(historical) if historical in text[start:] else start
    update=f'''The [V12S recombination comparison](results/composition_study.md) and three-step
research reassessment are complete and independently audited. **Sustained search
finds stronger random-origin routing, but compatible recombination does not show
a replicated advantage over mutation.**

294 matched generations run for 72.22 minutes across 18 conditions. Two fresh mutation
lineages complete 132 and 224 of 864 positive-prefix pairs on new contexts; matched
recombination/resampling primaries complete zero. Carried mutation yields 512/390/512,
recombination 448/512/224, versus 224 each for frozen/resampling controls. Only one
recombination replicate passes both gates—and its winner has no splice ancestry.
There are 45,248 actual splices, 97.3% transferring a single instruction. This does not
establish useful combination of functional modules.

![Matched comparisons and operator use](results/composition_study/comparison.png)

Preserve the rarer prefix-four/cycle specialist and the fresh descendants. The best
ordinary result is 74/384; all random-origin models fail 128 partition-disconnected
inputs. General solving, multirange advantage and speedup remain unestablished.
The [report](results/composition_study.md) distinguishes structural transfer,
ancestry, lost skills and proposed mechanism tests. No next experiment launched.

Audit passes {a['exact_candidate_replays']:,} exact candidate replays and all
birth/RNG/selection reconstruction. Training replay is sampled as preregistered;
validation/final replay is complete. All populations and raw data remain saved.
Exclude **{a['whole_layouts']:,} whole layouts** next. See the
[handoff](docs/COMPOSITION_PROGRESS.md), including lossless ancestry-log restoration
after a fresh clone, and the [unlaunched proposal](results/composition_study/next_experiment.md).

## Completed mutation-accessibility study V12R

'''
    readme.write_text(text[:start]+update+text[end:])


if __name__=='__main__':main()
