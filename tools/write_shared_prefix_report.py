"""Assemble the completed Q report from audited packets; no new inference."""
import sys,json,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.shared_prefix_study import *

def main():
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed'];assert json.loads((OUT/'schedule_audit.json').read_text())['passed']
    search=json.loads((OUT/'search_execution.json').read_text());final=json.loads((OUT/'confirmation/execution.json').read_text());analysis=read_compressed(OUT/'analysis.json.gz');b=final['budget']
    table=[]
    for origin in ('carry','fresh'):
        for rep in range(3):
            r=analysis['results'][f'{origin}/{rep}']['final'];table.append(f"| {origin}/{rep} | "+' | '.join(str(r[a]['zero']) for a in (*ARMS,'frozen'))+' |')
    text=f'''# V12Q — shared-prefix curriculum pilot

**Complete and independently audited.** The controlled curriculum change did not
produce a paired shortest-path solver across the first internal junction.
It did reproduce useful source-at-junction behavior in fresh random-origin
lineages. Those secondary gains include both mutation-associated gains and useful
unmutated random draws. They are not a general maze solver or a demonstrated
advantage from additional capacity, multirange signaling, or runtime speed.

## Main result

Every primary in both origin blocks gives **0/64 prefix1 core pairs on validation
and 0/128 on untouched final**. All31 physical random-origin final models,
including secondary archives and preserved anchors, fail every positive-prefix
pair and every two-junction/cycle pair. The separate intact solver succeeds.
The larger-run gate fails **0/3 carried and0/3 fresh replicates**. No extension
or additional evolutionary experiment was launched.

Source-at-junction core pairs on the SAME final cases, out of128 per selection:

| Origin / replicate | Current evolution | Mixed evolution | Resampling | Frozen |
|---|---:|---:|---:|---:|
{chr(10).join(table)}

The fresh-origin aggregate is Current96/384, Mixed288/384, resampling16/384,
frozen0/384. This is a secondary descriptive result: the registered target was
positive-prefix solving, not junction-only success. Each arm sees the same final
contexts. Poses, goals and variants are correlated;20 independent seeded clutter
contexts reuse a small number of route forms, not thousands of independent mazes.
This corpus is explicitly P-informed, not an ordinary-maze benchmark.

All carried primaries preserve128/128 core junction pairs and1344/1344 corridors.
Their160/672 total final paired successes add32 stress-fork prefix0 pairs, but
none on extra-junction or cycle variants. Fresh mixed replicate0 loses corridors:
1128/1344 (83.93%) versus1344/1344 frozen. Fresh mixed replicates1/2 retain all1344.
The fresh resampling replicate2 primary sacrifices corridor performance to464/1344
while giving16 core junction pairs; separate corridor archives remain saved.
No selected random-origin model makes a false no-path claim on final reachable
inputs. No-path successes concern isolated-goal clutter controls, not general
unreachability detection.

## What arose, and what is actually evolutionary evidence?

- Fresh/mixed0 `fresh/0/mixed/i1151`,114genes, is12 single edits from original
  founder95. On the SAME validation cases that founder gave0 junction pairs;
  the selected descendant gives32/64 and then96/128 on untouched core final.
  It works at arm lengths3/4/6, all8poses, but not length2. Its corridor loss
  prevents treating this as an unqualified improvement.
- Fresh/current1 `fresh/1/current/i1146`,96genes, is16 edits from original
  founder22. Initial validation0 becomes48/64; final96/128 includes six of
  eight poses at every arm length2/3/4/6. Mixed1 reaches64/128 only on larger
  arms4/6 despite0 small-arm validation pairs. No isolated mutation-causality
  experiment was performed on either lineage.
- Fresh/mixed2 `fresh/2/mixed/i1480`,121genes, gives128/128 core junction pairs,
 1344/1344 corridors and1344/1344 isolated-goal no-path responses. It is13 edits
  from random immigrant `fresh/2/mixed/i507`. That immigrant ALREADY solved its
  first sampled training junction pair; necessity of the subsequent edits is
  unknown. This is a preserved random-origin lineage, not proof that13 mutations
  created the primitive.
- Carried/mixed0's new94-gene winner descends5 edits from another random immigrant,
  not from the preserved O routing lineage. The95-gene **unmutated** carried
  resampling draw `carry/0/resample/i63` matches its final paired/corridor/no-path
  counts. Preserve this control; mutation was not required to sample that outcome.

A posthoc independent deque calculation on SAVED final rasters finds that all2688
reachable masks of fresh/mixed2, carried/mixed0 and that95-gene resample exactly
match the goal-distance ball stopped at the source distance. This is the same
output phenotype diagnosed in P, now seen in unrelated random-origin genomes.
It is emitted-output equivalence, not proof of internal BFS, identical internal
states, a shared mechanism or oracle access. No new candidate calls or mechanism
ablations were made for this diagnosis.

![Fixed normal-output comparison](shared_prefix/normal_outputs.png)

The illustration uses the first final context/pose/goal and mixed replicate0,
not a post-final winner. Orange masks are wrong normal emissions, never successes
or retuned intermediate states. Moving the source upstream admits cells in the
unused arm. The final does not establish that these newly sampled genomes are
causally dependent on the same flags/pulse connections as P.

## Did the search actually explore?

There are32 matched generations,18 conditions of96 organisms,41,472 births:
**24,192 single-edit descendants and17,280 random draws**, plus288 fresh founders.
Generation32's1,296 newborns are preserved for future work and were not evaluated;
40,176 new births entered a subsequent training generation.
All initial pools/RNG, every birth/event, next population, protected anchors and
three common archives are retained. Carried and fresh origins are reported
separately; carried replicates share the P routing ancestry.

The six carried evolution arms produce4,952 descendants of route depths9/16.
Maximum depth along those lineages is18–32 edits (mixed22/24/18, current27/32/29).
These are birth-chain depths and include the last unqueried offspring. Their
existence does not imply effective algorithmic complexity increased.
Across the whole pilot, the largest born genome is167genes, below the256 ceiling;
this run therefore does not show a binding capacity limit or test a higher ceiling.

In5,472 recorded same-batch child/parent comparisons,538 change output mask or
status. These are a correlated co-presence subset, not a random sample of all
mutations. All measured training positive-prefix complete-pair counts remainzero.
A posthoc pressure check finds18 prefix-score improvements in2,823 mixed-arm
comparisons:15 improve overall aggregate rank,three worsen it. Onlytwo of these
improvements occur in the carried arms. Partial-score improvement is not a solved
route, and aggregate rank is not lexicase selection probability. The evidence
therefore does not support blaming the result simply on selection rejecting every
useful step. Nor does32 generations settle the value of much longer evolution.

## Design, integrity and cost

Only training source-position mixture differs between the two evolving arms:
100% junction versus50/50 junction/one-edge-prefix. Runtime, bounds, one-edit
mutation, fitness, elites, immigration and archive policies are identical.
Resampling uses the mixed stimuli and identical protection/validation allowances.
Training has two matched contexts per generation with common corridor/no-path
controls; all8poses are queried over32generations. Validation8contexts ×2prefixes
×8poses ×6inputs =768/model. Final20contexts, prefixes0/1/2 and true alternative
cycles gives4032inputs/model:1344branched,1344corridor,1344disconnected.

Initial evaluation is physically shared across the three arms of each pool:
442,368 actual calls represent1,327,104 logical calls. Every condition then gets
36,864 training and6,144 validation calls.78 final aliases collapse to32 models:
129,024 physical versus314,496 alias evaluations. Main totals are
**{b['calls']:,} physical /2,415,744 logical candidate evaluations**,
**{b['seconds']:.2f}s candidate inference** under the720s ceiling and
**{b['work']:,} charged work units**. Equal counts do not imply equal actual work.
Search wall{search['wall_seconds']:.2f}s + final wall{final['wall_seconds']:.2f}s;
peak main RSS{max(search['peak_rss_bytes'],final['peak_rss_bytes'])/2**20:.2f}MiB.
Profile separately27,648calls/5.14candidate seconds; immutable-byte JIT warmups
separately one candidate +three baseline calls per stage. The fixed32-generation
schedule ended normally; unused allowance was not spent after inspecting results.

Compiled BFS, A* and bit-wavefront, plus the separate intact VM, each solve all
2688 reachable and1344 disconnected final inputs. No latency benchmark was run;
no speedup is claimed. CPU AppleM4,10cores,16GiB; Python3.13.15, NumPy2.5.4,
Numba0.68.0,llvmlite0.50.0. No cloud, LLM or paid compute.

Registration/source/pools/fixtures: **4fafe1c**. Fixture timing initially chose
16 generations using2× worst-pool mean, which would cover onlyfour queried poses.
A documented **timing-only amendment** changed the planning factor to1.5 and chose
32 generations (526.57s projected), retaining600s projection ceiling,720s hard cap
and100s final reserve. Original profile retained; amendment pushed **b1b9530**
BEFORE any research evaluation. No fixture scores were inspected/used for this
change, no frozen source was altered. All selections/ancestry/search/RNG pushed
**2ba193d** BEFORE final generation. This amendment is a preregistration deviation
made before scientific calls, not an unreported exception or post-result extension.

Audit passes first attempt: **{audit['candidate_replays']:,} exact candidate
replays**, **{audit['independent_rasters']:,} independently graded rasters**,
{audit['baseline_replays']:,} baseline replays, all41,472 births/24,192 mutations,
18 next states and78 aliases;190source/9input/2,384prior completion hash entries.
Audit wall{audit['wall_seconds']:.2f}s, peak RSS{audit['peak_rss_bytes']/2**20:.2f}MiB,
separate from research cost. Supplemental schedule audit verifies the amended
profile, pre-generation commit, all pose coverage, logical counts and summed times.
32 focused tests pass (10new +22related);273 tests collected within `tests/`,
NOT a fresh full-suite run. An initial unscoped collection also traversed vendored
plotting-library tests and failed on their missing test dependencies; the scoped
collection succeeds. No research inference or frozen-source repair resulted.

## Interpretation and next step

Useful goal-conditioned wave behavior is accessible from several random-origin
lineages. Some same-validation improvements arise along mutated original-founder
lineages, so the random track remains scientifically productive at this elementary
level. But evolving branch isolation is a separate, still-unsolved step. The
registered target failed in every replicate, the strongest fresh wave already had
an initially useful immigrant ancestor, and unmutated resampling can achieve the
same phenotype. More capacity, regulation or time remain hypotheses.

Before another long search, run a bounded **mutation-accessibility diagnostic**
around several preserved, independently rooted wave genotypes, together with
fresh controls. Ask whether available edits create a reproducible signal toward
normal prefix routing, and distinguish output-changing edits from mere genome
size. Use entirely new layouts and retain an untouched final. Do not launch an
unchanged60–90minute continuation. The proposal is in
[the next-experiment note](shared_prefix/next_experiment.md); it has not run.

Exclude **all187,416 whole layouts through Q** next:181,928throughP +1,424unique
preflight/software fixtures +320validation +2,560training +1,184final. Include
all unqueried poses and test geometries. `shared_prefix_data.exclusions()` returns
THROUGH P ONLY; append Q software_fixtures, shared_prefix_fixtures, validation,
train and confirmation manifests. Final cases remain inspection data, never
new validation. All historical populations, source and completion hashes remain
unchanged.
'''
    protected=[]
    def protect(match):
        protected.append(match.group());return chr(0xE000+len(protected)-1)
    text=re.sub(r'`[^`]+`|\]\([^)]*\)|\bV[0-9]+[A-Z]?\b|\b[0-9a-f]{7,40}\b',protect,text)
    text=re.sub(r'(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])',' ',text)
    text=re.sub(r'(?<=[A-Za-z\uE000-\uF8FF]),(?=\S)|;(?=\S)',lambda m:m.group()+' ',text)
    for index,value in enumerate(protected):text=text.replace(chr(0xE000+index),value)
    (ROOT/'results/shared_prefix.md').write_text(text)
if __name__=='__main__':main()
