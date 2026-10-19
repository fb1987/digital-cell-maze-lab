"""Write the V12S report from completed, independently audited saved evidence."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.composition_study import OUT, ROOT, read_compressed


def main():
    audit = json.loads((OUT/'audit.json').read_text()); assert audit['passed']
    search = json.loads((OUT/'search_execution.json').read_text())
    final = json.loads((OUT/'confirmation/execution.json').read_text())
    analysis = read_compressed(OUT/'analysis.json.gz')
    desc = json.loads((OUT/'descriptive_outcomes.json').read_text())
    choices = read_compressed(OUT/'choices.json.gz')
    metrics = read_compressed(OUT/'confirmation/metrics.json.gz')
    meta = read_compressed(OUT/'confirmation/metadata.json.gz')
    states = read_compressed(OUT/'next_states.json.gz')
    counts = desc['reproduction']; keys = list(counts)
    total = lambda k: sum(v.get(k,0) for v in counts.values())
    positive = len({(m['base'],m['pose']) for m in meta.values() if m['family']=='paired' and m['prefix']>0})
    allpairs = len({(m['base'],m['pose']) for m in meta.values() if m['family']=='paired'})
    corridors = sum(m['family']=='corridor' for m in meta.values())
    no_path = sum(m['family'] in ('disconnected','ordinary_disconnected') for m in meta.values())
    reachable = len(meta)-no_path
    replicated = [o for o,passed in analysis['replicated'].items() if passed]
    finding = ('The preregistered replicated recombination screen passes for '+', '.join(replicated)+'.'
               if replicated else 'The preregistered replicated recombination screen does not pass for either origin group.')
    rows=[]
    for origin in ('carry','fresh'):
        for rep in range(3):
            result=analysis['results'][f'{origin}/{rep}']
            scores=[str(result['final'][a]['positive']) for a in ('frozen','mutation','recombination','resample')]
            rows.append('| '+origin+' | '+str(rep)+' | '+' | '.join(scores)+' | '+str(result['validation_gate'])+' / '+str(result['final_gate'])+' |')
    activation=[]
    for key in keys:
        if not key.endswith('/recombination'):continue
        c=counts[key]
        activation.append(f"| {key.rsplit('/',1)[0]} | {c['attempts']:,} | {c['splices']:,} | {c.get('positive_pair_donor_gain',0):,} | {c.get('partial_only_donor_gain',0):,} | {c.get('direct_spliced_children_retained_at_least_once',0):,} |")
    secondary=[]
    lineages=[]
    for origin in ('carry','fresh'):
        for rep in range(3):
            for arm in ('mutation','recombination','resample'):
                a=f'{origin}/{rep}/{arm}/primary'; pid=choices['aliases'][a];m=metrics[pid];families=desc['models'][pid]['by_family']
                ordinary=sum(families[k]['shortest'] for k in ('ordinary_perfect','ordinary_random'))
                np=sum(v['correct_no_path'] for v in families.values())
                secondary.append(f"| {origin}/{rep}/{arm} | {m['pairs']} | {m['stress_positive']} | {m['corridors']} | {ordinary}/384 | {np}/{no_path} |")
                if arm=='recombination':
                    i=choices['items'][a];lin=desc['selected_lineages'][a]
                    lineages.append(f"| {origin}/{rep} | `{i['id']}` | {len(i['genome']['genes'])} | {lin['study_birth_generation']} | {lin['distinct_splice_events']} | {len(lin['roots'])} |")
    control=metrics[choices['aliases']['anchor/intact']]
    cost_rows=[]
    for origin in ('carry','fresh'):
        for arm in ('mutation','recombination','resample'):
            cc=[desc['search_cost_by_condition'][f'{origin}/{r}/{arm}'] for r in range(3)]
            n=sum(c.get('train_calls',0)+c.get('validation_calls',0) for c in cc)
            seconds=sum(c.get('train_seconds',0)+c.get('validation_seconds',0) for c in cc)
            work=sum(c.get('train_work',0)+c.get('validation_work',0) for c in cc)
            cost_rows.append(f'| {origin}/{arm} | {n:,} | {seconds:.2f} | {work:,} |')
    registered_revision=json.loads((OUT/'validation/generation.json').read_text())['revision']
    final_revision=json.loads((OUT/'confirmation/generation.json').read_text())['revision']
    text=f'''# V12S compatible recombination and sustained evolution

Completed and independently audited on the local Apple M4 CPU. **{finding}**
The fixed 75-minute allowance produces {search['generations']} matched generations
in {search['wall_seconds']/60:.2f} minutes, including initial validation. Its
closed stopping condition is `{search['stop']}`. No budget extension occurs.

![All primary comparisons and mating activation](composition_study/comparison.png)

## Why this comparison

The reassessment restores the broader preserved capability set: earlier internal-
junction/cycle and longer-prefix specialists alongside recent goal-wave lineages.
Failure in the recent wave experiments does not erase those older abilities.
The common starting panel preserves 16 exact random-origin identities. Existing
runtime storage comprises eight persistent channels and 64 scratch registers;
coordinating propagation, selective output and stopping remains a plausible
bottleneck. Greater raw capacity alone has not been established as the remedy.

Sexual recombination is a justified experiment because it can transfer multiple
coordinated instructions. Register and channel meanings can differ across genomes,
however. The static audit finds only eight eligible directed pairings among 240
panel pairings, all within related lineages. Exact instruction anchors are
structural similarity, not certified historical homology or functional modules.
The [saved assessment](research_reset/assessment.md) contains the full synthesis
and research references; it involved no candidate inference.

## Fixed experimental contrast

Carry and fresh origins each have three independently seeded replicates and
mutation, recombination and random-resampling arms: 18 populations of 96 organisms.
Each carried population protects all 16 historical identities and adds 80 random
founders. Fresh populations contain only new random founders. All arms within a
replicate share their starting pool, selection, evaluation schedule and archives.
Known-solver genes never enter a lineage. Old populations and RNG states remain intact.

All arms retain 24 organisms per generation. Evolution produces nine random
immigrants and 63 single-edit children; resampling produces 72 random draws.
Recombination attempts mating for 32 of its 63 children. A bounded shortlist
contains four lexicase-selected and four uniform donors. Compatible donors rank
by improvements on the recipient's current tasks, prioritizing paired correctness,
shortest paths, legal paths and then partial credit. Different goals can therefore
favor different parents without using holdout performance.

A splice replaces a bounded instruction segment between matching anchors, with
matching register-write and persistent-store sets and no additional scratch
requirements. Every splice is followed by the same one-edit mutation used in the
mutation-only arm. This tests the combined mating-and-splicing policy, not their
separate causal effects. It does not test arbitrary cross-family transplantation.

Native local runtime, input flags, endpoint stopping, 256-gene capacity and work
limits are common. Training uses two new contexts and 12 inputs per organism per
generation. All forms and eight poses cycle every 96 generations. Every 32
generations, two current nominees per condition receive the same 3,456-input
validation set. The initial 576 founder memberships receive validation once;
their results are logically reused across the three matched arms.

The [protocol](../docs/COMPOSITION_V12S.md) was pushed in `f650b93` and the
feasibility profile in `{registered_revision[:7]}` before validation generation.
All populations, RNG states, choices and search data were frozen in
`{final_revision[:7]}` before final generation. No selection uses final results.

## Untouched confirmation

The final corpus contains 28 new structured contexts, all eight poses, two goals,
prefixes 0/1/2/4, and matched forks, second junctions and real alternative cycles.
It contains {allpairs:,} branched pairs, including {positive:,} positive-prefix
pairs, and {corridors:,} corridor inputs. A separate transfer test adds 48 ordinary
9 by 9 reachable bases and 16 partition-disconnected bases in all eight poses.
Total: {len(meta):,} inputs per model, {reachable:,} reachable and {no_path:,}
disconnected. Independent units are contexts/base layouts; poses and variants
are correlated. Route forms recur, so the structured set is a diagnostic test.

Complete positive-prefix pairs per primary selection, denominator {positive:,}:

| Origin | Replicate | Frozen initial | Mutation | Recombination | Resampling | Validation / final gate |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

The same primary must pass both stages: at least 16 new positive-prefix pairs and
16 more than every control, two complete eight-pose groups, eight extra-junction
positive pairs, four contexts, retained junction/corridor skills and no increased
false no-path claims. At least 96 matched generations and two passing replicates
within an origin group are required. Passing replicate lists are
`{analysis['passing']}`. Secondary archives cannot replace a failed primary.

Additional primary outcomes:

| Condition | All pairs | Extra-junction positive pairs | Corridors | Ordinary shortest | Correct no-path |
|---|---:|---:|---:|---:|---:|
{chr(10).join(secondary)}

BFS, A* and bit-wave each emit correct outputs for all {reachable:,} reachable
and {no_path:,} disconnected inputs. The intact VM control emits
{control['optimal']:,} shortest paths and {control['no_path']:,} correct no-path
answers. No latency benchmark is conducted; there is no speedup claim.

## Did the mating operator activate

| Origin and replicate | Attempts | Actual splices | Donor pair-score gain | Partial-only donor gain | Direct children retained |
|---|---:|---:|---:|---:|---:|
{chr(10).join(activation)}

There are {total('splices'):,} actual splices among {total('attempts'):,} attempts.
Of these, {total('multi_instruction_donor_segments'):,} transfer more than one
instruction and {total('length_changing_splices'):,} change program length.
Donor gains measure its current-batch score relative to the recipient, not the
offspring's inherited skill. The retained column counts distinct direct spliced
children retained at least once after evaluation. Each splice also receives a
mutation, so successful ancestry alone cannot identify which change caused a gain.

At their first training evaluation, {total('first_evaluation_with_both_parents'):,}
direct spliced children have both parents still present on the same batch;
{total('first_evaluation_changed_from_both'):,} of them emit a raster/status
sequence different from both. These are selected parent-retention comparisons,
not all spliced children and not a causal test of skill composition. Full
recipient/donor denominators and retention counts are saved in the descriptive packet.

Recombination primary ancestry within this new comparison:

| Origin and replicate | Selected identity | Genes | Study birth | Distinct ancestral splices | Study roots |
|---|---|---:|---:|---:|---:|
{chr(10).join(lineages)}

Both parental edges are preserved in `birth.parents`. Historical anchors are
roots of this comparison, not claimed original random founders. The descriptive
packet preserves root identities for every selected alias and final population
counts with splice ancestry. Last-generation births have not yet been evaluated:
{total('last_generation_unevaluated_births'):,} across all populations.

## Cost and verification

Main candidate inference, including final confirmation, uses
{final['budget']['seconds']:.2f}/5,400 candidate seconds,
{final['budget']['calls']:,} physical calls and {final['budget']['work']:,} work
units. Search peak RSS is {search['peak_rss_bytes']/2**20:.2f} MiB; confirmation
peak RSS is {final['peak_rss_bytes']/2**20:.2f} MiB. The separate profile uses 17,792
candidate calls. Search wall includes reproduction and checkpoints; equal
evaluation allowances do not imply identical computational work across arms.

Search cost after the shared founder screen, summed across three replicates:

| Origin and arm | Training plus later validation calls | Candidate seconds | Work units |
|---|---:|---:|---:|
{chr(10).join(cost_rows)}

The initial 1,990,656 physical calls are separate and shared across policies;
they are not charged three times in the physical total above.

The independent audit passes all {audit['prior_hashes']:,} prior completion
entries, {audit['source_hashes']} frozen source hashes and {audit['input_hashes']}
input hashes. It reconstructs every birth, mutation, splice, parent choice,
fitness calculation, archive decision, population and RNG state. It regenerates
every corpus and checks geometry/orbits and pre-final commit ordering.

It performs {audit['exact_candidate_replays']:,} exact candidate replays,
independently grades {audit['independently_graded_candidate_rasters']:,} candidate
rasters, and replays {audit['baseline_replays']:,} baseline outputs. All profile,
initial/later validation and final outputs receive exact replay and grading.
Training uses the preregistered deterministic 1/256 exact-replay sample, plus
independent grading of every claimed legal/no-path output. This is not a full
training-inference replay. Audit wall is {audit['wall_seconds']:.2f} seconds with
{audit['peak_rss_bytes']/2**20:.2f} MiB peak RSS.

Ten new focused tests pass; 293 tests are collected, not a fresh full-suite run.
Before registration and candidate calls, an exhausted ordinary-maze fixture
supplier was replaced with the existing Wilson generator. The rejected partial
construction and all its layouts are preserved. Frozen scientific sources remain
unchanged. Exclude all **{audit['whole_layouts']:,} whole layouts through V12S**
from future independent data, including fixtures and unqueried poses.

All raw rasters, two-parent birth events, validation selections, 32-generation
checkpoints, final populations and RNG states remain available under
`results/composition_study/`. No subsequent experiment is launched.
'''
    (ROOT/'results/composition_study.md').write_text(text)


if __name__=='__main__':
    main()
