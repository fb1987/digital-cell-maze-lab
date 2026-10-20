"""Update mutable project navigation after the immutable Z packet is sealed."""
from pathlib import Path
import gzip,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/family_evolution'
def read(name):
 with gzip.open(OUT/name,'rt') as f:return json.load(f)
seal=json.loads((OUT/'completion.json').read_text());audit=json.loads((OUT/'audit.json').read_text());assert seal['audit_passed'] and audit['passed']
s=read('descriptive_summary.json.gz');count=seal['whole_layouts_through_Z'];future=6923+len(seal['source_and_artifact_sha256'])
block=f'''Current checkpoint: **V12Z is complete and independently audited**. Read
`results/family_evolution.md` and `docs/FAMILY_EVOLUTION_PROGRESS.md` first.
Do not rerun/extend its closed allowance, silently resume its states, or train
or reselect on its inspected final cases. The longer sexual comparison remains
unregistered and unlaunched; its actual-transfer gate is still required.

Z registration8c01929 pushed before scientific validation/training; all choices,
next populations and search records frozen/pushed ef1dca6 BEFORE final generation.
Seed2026102004; fixtures1434/1435; software23456789.24conditions of96:carry/fresh
×3replicates×currentmutation/familyreserve/resample/frozen. Carry20exact historical
random-origin anchors, fresh wholly random64–128gene founders. Native local
runtime/exposure7,256gene/256tick cap; no known-solver injection or crossover.
44survivors/52births common; mutation7immigrants+45singleedit children. Family
only changes retention:4additionalmerit, upto5families×4distinct variants,
farthest-first inherited-locus mismatch; common behavior/rank fill. Archives
stay external. Historical labels separate except documented d07/d12 homology.

128matchedgenerations finish in4174.06s(69.57min), wall_reserve stop. Candidate
3485.28s,6512640calls,2017046991212work,464.83MiBRSS.119808births:69120mutation
and50688newrandom.550144logicalresponses/condition; initial shared screening
physically reused. Of candidate time,779.09s initial,1911.72s training,794.47s
later validation. Only8laternominationevents/condition; useful unnominated
variants remain preserved. Final newborn populations have unevaluated offspring.

Final7232inputs/model:20structured contexts,8poses,2goals,prefix0/1/2/4/8,
matched forks/secondjunctions/realalternativecycles;1120pairs,2240corridors,
384ordinaryreachable,2368disconnected inputs. Contexts independent seeded
clutter draws within a small fixed grammar; variants/poses correlated and route
shapes recur.93aliases/40physicalmodels,289280candidatecalls,281.29candidate
seconds,293.15wall,21696separate conventional baseline calls.

ALL carried primaries share frozen successful-case membership:526/1120pairs,
326/896positiveprefix,66/224prefix4,36/224prefix8,8/128positivecycle,
2064/2240corridors,56/384ordinary.11/12keep exact historical carry1i18358;
currentmutation/0 selects256gene i1319 through3Zmutationbirths, no new correct
case membership. These are preserved abilities, not a Z improvement.

Fresh complete pairs across3replicates:current[160,160,160],family[160,0,160],
resample[160,160,160],frozen[0,0,4]. All160successes are20prefix0forkcontexts
inall8poses. Every fresh primary0positiveprefix and0secondjunction/cyclepairs.
Ordinary current[8,8,8],family[8,0,16],resample[16,8,16],frozen[0,0,2]/384;
all these ordinary successes1–2edges,atmost2bases. Mutation finds elementary
validation80pairs in2/3by32,3/3by64;resampling3/3onlyat128. Correlated selection
timecourse; final resampling matches. Current winners122/136/91genes,
29/7/11Zmutationbirths; resampling124/106/120genes,unmutatedrandomdraws.
No registered gate passes:0/3bothorigins,bothmutation policies. No general
solver, causal multirange benefit or speedup established; no latency benchmark.

Retrospective saved masks:all six fresh current/resample primaries contain the
oracle path PLUS exactly1extra cell onall320prefix1forkinputs/model. Prefix2/4/8
also contain the path withmultipleextras. These remain INVALID native outputs;
no pruning/repair or extra inference. No new forced traces or mechanism ablations.
See routing_boundary.png and raster_diagnostics.json. This narrows a visible
output-selectivity failure but does not prove stopping versus rule causation.

Final retained-relative mean inherited-locus distance higher inall6matched
comparisons:carry current4.7/6.9/4.4%→family9.8/14.5/18.4%;fresh22.2/22.7/24.4%
→27.1/31.9/42.3%. Structural variation, not functional modules or transfer proof.
Effective mutable-family count increases inonly3/6finalcomparisons. Preserve
all24states/RNG, full genomes, archived ancestry, locus IDs, raw masks and losses.

Evolved/resampled primaries0/2368correctno-path and0false reachable claims.
Frozenfreshrep2gets1752no-path but3542/4864false reachable claims; not competence.
BFS/A*/bitwave/intactVMsolve4864/4864reachable and2368/2368disconnected.

First audit PASSES: {audit['wall_seconds']:.2f}s wall,{audit['peak_rss_bytes']/2**20:.2f}MiBRSS.
{audit['exact_candidate_replays']}main/profile/final exact replays (ALLnontraining +fixed1/256
training), {audit['independently_graded_candidate_rasters']}independent raster grades; rehearsal separately
82944exactreplays/grades. All parent/selection/mutation/RNG/checkpoint/archive/
choice events reproduced; shared production selection functions, independent
grader.21696baseline replays;240source/21inputhashes,6923priorentries verify.
No frozen-source repair/deviation.43focused/related+4archive/replayintegritytests
pass, NOTfullsuite. Calibration+rehearsal63.83candidate seconds; audit additional.

The131653270byte ancestrylog is preserved in4verified32MiB-or-smaller remote
byte chunks. Restore with tools/archive_family_evolution_births.py restore.
After sealing, use tools/replay_family_evolution_audit.py; it verifies seals and
writes new audit packets under output/, preserving sealed originals. Do NOT
rerun the raw audit action over the sealed audit.json. Completion seals
{len(seal['source_and_artifact_sha256'])}entries;futureprior total{future}(6923+new;notunique files).
Exclude ALL **{count} whole layouts** throughZ via
results/family_evolution/whole_layout_exclusions.json.gz, pluslaterfixtures.

Next proposal ONLY: freeze Z-informed fresh models/roots/randomcontrols and
historical complements; new matched cases distinguish native stopping from
persistent branch overgrowth, normal successes before forced-trace interpretation.
Assess actual recombination opportunity separately. Sexual75min still requires
NEW10%actualretainedmultichange activation,8generations,2/3allsexualpolicies
BOTHorigins. See results/family_evolution/next_experiment.md. No new study launched.

'''
p=ROOT/'AGENTS.md';t=p.read_text();marker='## Immediate first task\n\n';assert marker in t
old='Current checkpoint: **V12Y';assert old in t;t=t.replace(old,'Historical V12Y checkpoint: **V12Y',1);t=t.replace(marker,marker+block,1);p.write_text(t)
progress=f'''# V12Z completed and audited

The mutation versus family-reserve comparison is complete. The fixed 75-minute
allowance closed after 128 matched generations in 69.57 minutes, with 6,512,640 search
responses. Registration 8c01929; selections/search records ef1dca6 before final.

Read [the report](../results/family_evolution.md) and
[the next proposal](../results/family_evolution/next_experiment.md). No gate passes.
Family reserve increases structural variation but gives no final routing benefit.
Fresh ordinary mutation and resampling each reach 160/1,120 pairs in all three replicates,
all prefix-zero forks; family 160/0/160, frozen 0/0/4. No fresh positive-prefix pairs. Carried
primary correctness stays at its frozen baseline. Mutation reaches elementary
validation success earlier; final resampling catches up. Saved masks expose
one-cell branch stubs on prefix-one forks; outputs remain invalid and unmodified.

Audit passes on first attempt: {audit['wall_seconds']:.2f}s wall,
{audit['exact_candidate_replays']:,} exact main/profile/final replays plus 82,944 rehearsal,
{audit['independently_graded_candidate_rasters']:,} independent grades plus 82,944 rehearsal,
all ancestry/RNG/checkpoints and 21,696 conventional baseline replays.
43 focused/related tests plus four archive/replay integrity tests pass; not a full-suite run.
No frozen source repair or protocol deviation.

All 24 next populations, RNG, raw masks, nominees, ancestry and locus IDs preserved.
Restore the large log using tools/archive_family_evolution_births.py restore.
For future audits use tools/replay_family_evolution_audit.py, which writes a
separate packet under output/ and leaves sealed artifacts unchanged.

Exclude **{count:,} whole layouts** through Z using
results/family_evolution/whole_layout_exclusions.json.gz plus later fixtures.
Completion adds {len(seal['source_and_artifact_sha256'])} sealed entries; future prior total {future}.
Do not repeat or extend Z, silently resume its states, or tune on inspected finals.
The next mechanism/activation work is a proposal only; no sexual long run launched.
'''
(ROOT/'docs/FAMILY_EVOLUTION_PROGRESS.md').write_text(progress)
p=ROOT/'README.md';t=p.read_text();head='## Current checkpoint — October 20, 2026\n\n';assert head in t
new=f'''The [V12Z family-reserve evolution comparison](results/family_evolution.md) is
complete and independently audited: **128 matched generations in 69.57 minutes**,
with 6.51 million search responses. The family reserve preserves more variation
within retained relatives but does not improve final primary solving.

Fresh ordinary mutation and random resampling each solve 160/1,120 complete pairs
in all three replicates; family reserve solves 160/0/160 and frozen references
0/0/4. These successes all start directly at a fork junction. None of the fresh
primaries completes a positive-prefix pair. Carried primary correctness stays
at its frozen baseline. Mutation reaches the elementary validation phenotype
earlier; resampling catches up on the final test. The registered stronger gate
fails in every cohort.

![Actual emitted fork outputs and their boundary](results/family_evolution/routing_boundary.png)

The one-cell-prefix failure is precise: in all six ordinary-mutation/resampling
primaries, the correct fork route is illuminated along with one extra cell.
These are invalid native outputs, with no cleanup applied. The saved populations
support a bounded mechanism/activation follow-up; another long sexual run still
requires its new actual-transfer gate. See [the handoff](docs/FAMILY_EVOLUTION_PROGRESS.md)
and [longer-run status](docs/LONG_SEARCH_SETUP.md). Exclude **{count:,} whole layouts**
from future independent data. All raw histories and RNG checkpoints are preserved.

## Completed opportunity assay V12Y

'''
t=t.replace(head,head+new,1)
oldstart=t.index('The [longer-run setup](docs/LONG_SEARCH_SETUP.md) prepares two 75-minute designs:');oldend=t.index('\n## Completed activation pilot',oldstart)
t=t[:oldstart]+'''The two longer-run designs prepared after Y are tracked in
[the setup document](docs/LONG_SEARCH_SETUP.md). The first is now complete as Z
above. The sexual comparison remains conditional and unlaunched.
'''+t[oldend:];p.write_text(t)
(ROOT/'docs/LONG_SEARCH_SETUP.md').write_text(f'''# Longer evolution run status

The first 75-minute design is complete as V12Z: 128 matched generations in 69.57 minutes,
followed by untouched confirmation and an independent audit. Read
[the report](../results/family_evolution.md) and
[the current handoff](FAMILY_EVOLUTION_PROGRESS.md). The registered gate fails;
no budget extension or additional evolution occurred.

The family reserve increases inherited-locus variation but gives no final
primary correctness gain. Fresh mutation finds elementary fork behavior earlier
on validation; final resampling matches it. No fresh positive-prefix pairs are
completed. Preserve all populations/RNG and the partial abilities that remain.

The second 75-minute sexual specification remains **unregistered, unlaunched and
not launch-ready**. It still needs a NEW actual-transfer activation pilot:
>=10% of scheduled matings retain two changed donor instructions after mutation,
>=8 generations, in 2/3 replicates for all sexual policies in BOTH origins. Neither Y's
static probabilities nor Z's larger within-family distances satisfy that gate.
Any Z-derived pool must be explicitly described as continued random-origin
ancestry, not newly drawn fresh founders.

Before further long compute, the [next proposal](../results/family_evolution/next_experiment.md)
tests branch overgrowth/stopping on new matched cases and considers actual
recombination opportunity separately. It is a proposal, not a launched job.

Use `.venv/bin/python tools/prepare_long_search.py check` to inspect status.
The command never launches a run and marks completed designs as nonlaunchable.
Future independent work must exclude all {count:,} whole layouts through Z via
results/family_evolution/whole_layout_exclusions.json.gz plus later fixtures.
No cloud resources or recurring automation are configured.
''')
p=ROOT/'results/long_search_setup/mutation_diversity_75m.json';plan=json.loads(p.read_text());plan['status']='complete_and_audited';plan['completion']='results/family_evolution/completion.json';plan['readiness']={k:True for k in plan['readiness']};p.write_text(json.dumps(plan,indent=2)+'\n')
p=ROOT/'results/long_search_setup/family_crossover_75m.json';plan=json.loads(p.read_text());plan['whole_layout_exclusion_file']='results/family_evolution/whole_layout_exclusions.json.gz';plan['known_excluded_layouts']=count;plan['evidence']['results/family_evolution/completion.json']=hashlib.sha256((OUT/'completion.json').read_bytes()).hexdigest();plan['readiness']['new_actual_transfer_activation_gate']=False;p.write_text(json.dumps(plan,indent=2)+'\n')
print(dict(updated_handoff=True,whole_layouts=count,future_prior_entries=future))
