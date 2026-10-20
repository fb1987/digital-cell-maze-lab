"""Write final V13A report from sealed-design outputs after audit."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.branch_overgrowth_data import *
p=read_compressed(OUT/'panel.json.gz');a=read_compressed(OUT/'analysis.json.gz');audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
e=json.loads((OUT/'confirmation/execution.json').read_text());profile=json.loads((FIXTURES/'execution.json').read_text());reg=json.loads((OUT/'preregistration.json').read_text())
rows=[]
for n in ['mutation0','mutation1','mutation2','family0','family1','family2']:
 c=a['comparisons'][n];m=a['metrics'][p['aliases'][n]+'|normal'];rows.append(f"| {n} | {c['root']['pairs']} | {c['parent']['pairs']} | {m['pairs']} | {p['chains'][n]['mutation_births']} |")
inter=[]
for n in ['mutation0','mutation1','mutation2','family0','family2','resample0','resample1','resample2','historical_long','historical_short','random68','intact']:
 v=a['interventions'][n];inter.append('| '+n+' | '+str(v['pulse_off']['normal_success'])+' | '+' | '.join(str(v[k]['retained']) for k in ('pulse_off','flag_off','endpoint_off','halt_off'))+' |')
text=f'''# V13A: extra branch cells are not rescued by waiting

**The new Z lineages have a persistent output-spreading problem, not a hidden
correct solution that appears if we simply wait longer.** In the fixed trace
subset, all 428 normally failed Z tasks have zero shortest-path frames anywhere
in 96 ticks. Removing the native halt request loses every existing paired Z
success and creates no new pairs. This conclusion is specific to these selected
genomes and contexts; the preserved long-prefix specialist behaves differently.

There is positive evolutionary evidence too: all three ordinary-mutation
lineages acquire 96 complete goal pairs absent from their exact random roots.
The immediate parents already have those abilities. Random resampling also
finds the same elementary skill, so this is evidence of acquisition along
selected histories, not a replicated final-performance advantage of evolution.

## Normal inference and exact ancestry

The panel freezes 25 genomes before new scientific cases: nine Z primaries,
twelve exact root/parent controls, two historical specialists, the historical
68-gene random draw, and a separate intact VM. All 95 relevant ancestral birth
events replay exactly; no genome edits, training, selection or breeding occur.

Each model receives 5,312 new inputs: 800 branched two-goal pairs, 1,600 corridors,
1,600 structured disconnected inputs, 384 ordinary reachable inputs and 128
ordinary disconnected inputs. Twelve seeded structural contexts cover matched
prefixes 0/1/2/4/8, straight/bent stems, forks, second junctions and real
alternative cycles, with eight poses. Moving the source keeps cells and goals
fixed within each graph. The grammar is inherited from Z, with new clutter;
this is a mechanism test on new layouts, not novel-topology generalization.
The twelve contexts are independent seeded draws; their poses/variants correlate.

| Selected lineage | Exact root pairs /800 | Immediate parent /800 | Descendant /800 | Z mutation births |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

All six ordinary-mutation/resampling primaries solve **96/800 pairs**, exactly
the twelve source-at-junction forks in all eight poses. Family selections solve
96/0/96. None of the nine Z selections completes an upstream pair or a second-
junction/cycle pair. All nine retain 1,600/1,600 corridors, but solve 0/384 ordinary
reachable inputs and 0/1,728 disconnected inputs, with no false reachable no-path
claims. The ordinary benchmark and structured mix differ from Z: the changed raw
counts do not measure a loss of ability between studies. Genomes were unchanged.

The roots distinguish acquisition from inheritance. Ordinary-mutation roots
score 0/800 paired; descendant gains are 96/96/96, with no lost pairs. Family0
gains 68 pairs over its root's 28; family1 gains none; family2 inherits its 96-pair
skill. Every immediate parent's successful-pair set matches its descendant here.
Two ordinary-mutation roots already solve every corridor; the other solves none
and falsely declares all 3,584 reachable cases unreachable. Root no-path scores
therefore cannot be presented without their false claims. Neither more genes
nor the final edit is established as the cause of acquired routing.

Preserved historical abilities remain stronger:

| Frozen comparator | Pairs /800 | Upstream pairs /640 | Prefix4 pairs /160 | Prefix8 pairs /160 | Ordinary shortest /384 |
|---|---:|---:|---:|---:|---:|
| Long-prefix specialist | 344 | 208 | 46 | 30 | 14 |
| Short-prefix specialist | 192 | 96 | 0 | 0 | 8 |
| 68-gene unmutated random draw | 192 | 96 | 0 | 0 | 8 |
| Intact VM | 800 | 640 | 160 | 160 | 384 |

The long-prefix specialist includes eight upstream cycle pairs, four each at
prefix4 and prefix8, and twelve upstream second-junction pairs. These are
preserved capabilities, not new evolutionary gains. Its corridors are 1,476/1,600.
BFS, A*, bit-wavefront and intact VM solve all 3,584 reachable and 1,728 disconnected
inputs. No timing comparison, speedup or multirange advantage is claimed.

![Normal and intervention outcomes](branch_overgrowth/comparison.png)

## Distinct goal mechanisms, shared dependence on timely emission

Interventions cover 480 pairs/model plus their matched corridor tasks at
prefixes 0/1/4. Counts below are retained genuine NORMAL successes; every entry's
denominator is the second column. Both-off retains zero pairs for every target.
No intervention produces a new pair for any target on this subset. Family1 has
zero normal pairs, so it supplies no success-conditioned necessity claim.

| Target | Normal successful pairs | Pulse removed | Flag removed | Endpoint check removed | Halt request removed |
|---|---:|---:|---:|---:|---:|
{chr(10).join(inter)}

Mutation0/2 and resample0/1 require the static flag for these successes and retain
them without the initial pulse. Mutation1, family0/2 and resample2 instead require
the pulse and retain the pairs without the flag. Thus similar output behavior
can arise through distinct goal inputs. Removing the endpoint check preserves
all pairs, whereas removing the source halt request destroys all Z paired
successes. These are separate causal interventions; the endpoint result does
not show that every stopping mechanism is dispensable.

The historical long specialist retains 18/266 pairs without its halt request,
while intact retains 480/480. The common adapter can therefore preserve stable
successes; blanket intervention failure is not built into the experiment.

## The trajectories resolve the waiting hypothesis

All 3,120 scientific traces reach 96 ticks, yielding 299,520 saved full-state frames.
There are 60 tasks/model/mode in three fixed contexts and two poses, under normal,
pulse-off, flag-off and both-off rules. The traces keep work caps but bypass
emission and quiescence stopping. They never count as normal solutions.

For the nine Z selections under unchanged rules:

- 540 traces contain 428 normally failed tasks; none has shortest geometry at
  ANY recorded tick, before or after native stopping.
- Every trace repeats a full substrate state. Six selections settle to fixed
  states; mutation1 and resample1 have period 4, family2 period 8. These local,
  deterministic dynamics explain persistence within the observed execution.
- Eight of nine selections illuminate exactly the entire source-connected
  component at tick 96 on all 60 traced tasks each. Family2 has different repeated
  states; it also produces no late correct output.
- Already successful outputs are transient: no Z selection has a shortest
  raster at tick 96. Two goals may be correct at different native stopping ticks;
  the absence of simultaneous forced correctness does not invalidate native pairs.

![Recorded output spreading](branch_overgrowth/trajectories.png)

The illustration uses mutation0 and resample0 on the first one-cell-prefix fork.
Their native rasters have the complete route plus one extra cell. Continuing
updates expands the unwanted branch and stem, rather than retracting the stub.
The images use saved states only; no corrective decoder or oracle pruning is used.
The full-component counts are labelled retrospective diagnostics in
`descriptive_summary.json`; the registered audit replays the underlying states.

The preserved long specialist is an exception worth retaining: two of its 14
normally failed traced tasks do have later shortest frames. No failed pair gains
simultaneous later correctness for both goals, and unforced halt removal creates
no new pair. This limited exception does not support a universal waiting fix.
Both-off paired full trajectories are identical throughout, as required.

## Cost, audit and limits

Registration **676e418** was pushed before scientific generation. Seed 2026102006,
fixture 1444. Calibration used 27,560 candidate/parity calls and
{profile['budget']['seconds']:.2f}/180 candidate seconds. Its timing-only ladder
selected 12 contexts with a 187.86-second projection including 2× safety.

Main inference used **260,720 calls, {e['budget']['seconds']:.2f}/720 candidate
seconds**, {e['budget']['work']:,} charged work units, {e['wall_seconds']:.2f} wall
seconds and {e['peak_rss_bytes']/2**20:.2f} MiB peakRSS. Normal, interventions and
traces charge 45.79, 44.92 and 3.84 candidate seconds respectively. Baseline calls
are separate. Warmups are separately logged using production signatures.
Execution is local Apple M4, Python {reg['python']}, NumPy {reg['dependencies']['numpy']},
Numba {reg['dependencies']['numba']}; no remote compute or model is used.

The independent audit passes first attempt in {audit['wall_seconds']:.2f} seconds,
{audit['peak_rss_bytes']/2**20:.2f} MiB peakRSS. It verifies 7,880 prior hash entries,
243 source/9 input hashes, all 95 ancestral events, both regenerated corpora and every
scheduled response:288,280 exact candidate replays,305,308 independent response
raster grades,17,028 baseline replays,15,340 legacy adapter checks and449,280 full
trace frames including fixtures. Frame summaries are recomputed with the separate
grader. There is no independent second full interpreter for halt-off.
Nine new plus eleven existing focused tests pass; two replay-output isolation
tests pass separately. This is not a fresh full-suite run.
No scientific-source repair or protocol deviation was needed. A plotting helper
was adjusted to use saved JSON rather than import Numba into its plotting-only
environment; this made no candidate calls or changes to scientific code/results.

The study does not test new evolutionary pressure or recombination. It diagnoses
these selected histories under a limited grammar and fixed 96-tick horizon;
normal failure here is not proof that random-origin general solving is impossible.
For later re-audits, run `tools/replay_branch_overgrowth_audit.py`; it verifies
the seal and writes a separate packet under `output/`, preserving the originals.

Exclude all **{audit['whole_layouts']:,} whole layouts** through V13A from future
independent work, including fixtures/unqueried poses. Preserve all Z populations,
RNG, ancestry and every earlier specialist unchanged.

## Recommended next experiment

Return to a controlled acquisition test aimed at **selective output**, rather
than another unchanged run or further time extensions. Compare current selection
against one explicit change rewarding reduced off-route output while retaining
complete routes on paired one-/two-cell-prefix tasks. The current fitness already
penalizes branches: first verify that the proposed change creates a distinct,
useful ranking on complete, partial, empty and flooded outputs. Do not assume
that adding another penalty alone will help.

Use a small calibration/pilot with matched initial populations, fresh random
founders and clearly labelled continued random-origin controls, equal evaluation
budgets and common protected corridor/goal-choice specialists. Retain frozen and
resampling references. Exact normal two-goal shortest paths on new validation
contexts, gains beyond controls and retention of old skills must gate a longer
run in at least two of three replicates. Oracle routes may inform fitness only;
never clean a candidate's emitted raster. Freeze all choices before another
untouched test. No new study has been launched.

Sexual recombination remains available as a separate hypothesis, with its
actual retained-multigene-transfer gate still unmet. These mechanism findings
and Z's larger genetic distances do not satisfy that gate.
'''
(ROOT/'results/branch_overgrowth.md').write_text(text)
