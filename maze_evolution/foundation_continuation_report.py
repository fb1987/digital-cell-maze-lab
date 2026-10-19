"""V12D descriptive report from frozen selections and independently verified outputs."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics

from .foundation_calibration import write_json
from .foundation_calibration_audit import lines
from .foundation_continuation_data import PARENT
from .foundation_continuation_screen import level_metrics, replicate_screen
from .foundation_study import read_compressed
from .foundation_study_report import metrics, ancestry
from .growth import Genome
from .range_audit import output_dataflow


def primary_interventions(out, records):
    """Aggregate successful-case interventions by primary alias, retaining paired scope."""
    counts, outcomes = defaultdict(Counter), {}
    for record in lines(out / 'interventions/outputs.jsonl.gz'):
        for alias in record['aliases']:
            if alias['role'] != 'champion' or alias['scope'] != 'micro' or '/evolution/' not in alias['condition']:
                continue
            key = alias['condition']
            counts[key]['original_successes'] += 1
            for name, row in record['variants'].items():
                counts[key][name] += row['optimal']
                outcomes[key, name, record['case']] = row['optimal']
    for record in records:
        if record['role'] != 'champion' or record['scope'] != 'micro' or '/evolution/' not in record['key']:
            continue
        for i in range(0, len(record['cases']), 2):
            a, b = record['cases'][i:i + 2]
            if not a['pair_optimal'] or '/level0/' in a['case']:
                continue
            for name in ('replay', 'no_goal_pulse', 'zero_nonlocal', 'both'):
                counts[record['key']][name + '_pairs'] += int(outcomes[record['key'], name, a['case']] and outcomes[record['key'], name, b['case']])
    return {key: dict(value) for key, value in counts.items()}


def run(out):
    out = Path(out)
    summary = json.loads((out / 'search_summary.json').read_text())
    final = json.loads((out / 'confirmation/summary.json').read_text())
    proof = json.loads((out / 'verification.json').read_text())
    assert proof['all_checks_passed']
    for name, expected in (('search_summary.json', proof['search_summary_sha256']),
                           ('confirmation/summary.json', proof['confirmation_summary_sha256'])):
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == expected
    current = read_compressed(out / 'frozen_selections.json.gz')
    checkpoint = read_compressed(out / 'checkpoint_selections.json.gz')
    lookup = {}
    for name in ('mazes.json.gz', 'general_mazes.json.gz'):
        with gzip.open(out / 'confirmation' / name, 'rt') as f:
            lookup.update((m['case_id'], m) for m in json.load(f))
    records = list(lines(out / 'confirmation/outputs.jsonl.gz'))
    indexed = {(r['key'], r['role'], r['scope']): r for r in records}
    results, wanted = {}, set()
    for record in records:
        name = '/'.join((record['key'], record['role'], record['scope']))
        result = metrics(record['cases'], lookup)
        if record['scope'] == 'micro':
            result['levels'] = {str(level): metrics([r for r in record['cases'] if f'/level{level}/' in r['case']], lookup) for level in range(4)}
        results[name] = result
        if record['key'] in current:
            wanted.add(record['id'])
    parent_summary = json.loads((PARENT / 'search_summary.json').read_text())
    paths = [dict(files=[str((base / segment['files'][0]).resolve())])
        for base, packet in ((PARENT, parent_summary), (out, summary)) for segment in packet['segments']]
    details = ancestry(out, dict(segments=paths), wanted)
    for selections in (checkpoint, current):
        for state in selections.values():
            for item in [state['champion'], state['frozen'], *[v['item'] for source in ('skills', 'frozen_skills') for v in state[source].values()]]:
                details[item['id']]['syntactic_dependencies'] = output_dataflow(Genome.from_dict(item['genome']))
                details[item['id']]['born_in_continuation'] = item['birth'] > summary['start_generation']
    screen, replicate_results = {}, []
    for origin in ('native', 'fresh'):
        for topology in ('local', 'evolved'):
            passing = 0
            for rep in range(3):
                key = f'foundation_study/{topology}/{origin}/evolution/{rep}'
                other = key.replace('/evolution/', '/resample/')
                levels = {label: level_metrics(indexed[k, role, 'micro']['cases']) for label, k, role in
                    (('current', key, 'champion'), ('checkpoint', key, 'checkpoint'), ('resample', other, 'champion'))}
                decision = replicate_screen(levels['current'], levels['checkpoint'], levels['resample'])
                passing += decision['passes']
                replicate_results.append(dict(origin=origin, topology=topology, replicate=rep, levels=levels, **decision))
            screen[origin + '/' + topology] = dict(passing_replicates=passing, passes=passing >= 2)
    histories = {}
    for key, state in current.items():
        cfg = state['config']
        name = '_'.join(str(cfg[k]) for k in ('origin', 'topology', 'method', 'replicate'))
        histories[key] = json.loads((out / 'checkpoints' / (name + '.json')).read_text())['history']
    last_counts, last_outputs, last_descriptors = defaultdict(Counter), defaultdict(set), defaultdict(set)
    for record in lines(out / summary['segments'][-1]['files'][1]):
        if record['split'] != 'train' or record['generation'] != summary['rounds'] - 1:
            continue
        key, rows = record['condition'], record['cases']
        last_counts[key]['organisms'] += 1
        last_counts[key]['responses'] += len(rows)
        last_counts[key]['budget_failures'] += sum('budget' in r['status'] for r in rows)
        last_counts[key]['empty_rasters'] += sum(not r['mask'].strip('0') for r in rows)
        last_counts[key]['organisms_using_nonlocal'] += any(sum(r['range_reads'][1:]) for r in rows)
        last_outputs[key].add(tuple((r['mask'], r['status']) for r in rows))
        last_descriptors[key].add(json.dumps(record['descriptor'], separators=(',', ':')))
    assert len(last_counts) == 24 and all(v['organisms'] == 96 for v in last_counts.values())
    timing = json.loads((out / 'confirmation/timings.json').read_text())
    bfs = {r['case']: r['median'] for r in timing['records'] if r['model'] == 'compiled_bfs'}
    random_digests = {r['digest'] for r in records if r['key'] in current}
    timing_groups = defaultdict(list)
    for row in timing['records']:
        if isinstance(row['model'], str):
            continue
        kind = 'random-origin' if row['model'][0] in random_digests else 'known wavefront'
        scope = 'ordinary' if row['case'].startswith('general/') else 'elementary'
        timing_groups[kind + '/' + scope].append(dict(model=row['model'][0], case=row['case'],
            ratio=row['median']/bfs[row['case']], median_seconds=row['median'], array_bytes=row['array_bytes']))
    timing_comparison = {key: dict(genotypes=len({v['model'] for v in values}), matched_inputs=len(values),
        median_ratio=statistics.median(v['ratio'] for v in values), minimum_ratio=min(v['ratio'] for v in values),
        maximum_ratio=max(v['ratio'] for v in values)) for key, values in timing_groups.items()}
    analysis = dict(scope='Descriptive V12D analysis after independent audit; no selection or tuning',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), results=results,
        stronger_screen=screen, per_replicate_screen=replicate_results, selected_ancestry=details,
        timing_comparison=timing_comparison, timing_matches=dict(timing_groups),
        last_training_batch_behavior={key: dict(**dict(v), distinct_output_status_fingerprints=len(last_outputs[key]),
            distinct_selection_descriptors=len(last_descriptors[key])) for key, v in last_counts.items()},
        distinct_selected_genotypes=len(random_digests),
        maximum_evaluated_genes=max(h['max_genes'] for hs in histories.values() for h in hs[summary['start_generation']:]),
        maximum_prepared_genes=max(proof['ancestry']['maximum_registered_genes'].values()))
    timecourse = json.loads((out / 'timecourse/summary.json').read_text())
    analysis['secondary_timecourse'] = timecourse
    analysis['validation_selection_changes'] = json.loads((out / 'primary_selection_changes.json').read_text())
    if (out / 'interventions/summary.json').exists():
        analysis['posthoc_interventions'] = json.loads((out / 'interventions/summary.json').read_text())
        analysis['primary_interventions'] = primary_interventions(out, records)
    discussion = (out / 'discussion.md').read_text() if (out / 'discussion.md').exists() else ''
    analysis['discussion_sha256'] = hashlib.sha256(discussion.encode()).hexdigest()
    write_json(out / 'analysis.json', analysis)
    table = []
    for origin in ('native', 'fresh'):
        for topology in ('local', 'evolved'):
            for label, method, role in (('current evolution', 'evolution', 'champion'),
                ('V12C checkpoint', 'evolution', 'checkpoint'), ('continued resampling', 'resample', 'champion'),
                ('original frozen', 'evolution', 'frozen')):
                keys = [f'foundation_study/{topology}/{origin}/{method}/{rep}/{role}' for rep in range(3)]
                micro = [results[k + '/micro'] for k in keys]
                general = [results[k + '/general'] for k in keys]
                cells = [f"{sum(m['levels'][str(l)]['optimal'] for m in micro)}/288; {sum(m['levels'][str(l)]['pairs'] for m in micro)}/144" for l in range(4)]
                ordinary = f"{sum(m['valid'] for m in general)}/216; {sum(m['optimal'] for m in general)}/216"
                long = f"{sum(m['long_optimal'] for m in general)}/{sum(m['long_outputs'] for m in general)}"
                table.append(f'| {origin}/{topology}/{label} | ' + ' | '.join(cells) + f" | {ordinary} | {long} | {sum(m['no_path'] for m in general)}/48 |")
    replicate_table = []
    for r in replicate_results:
        count = r['nonadjacent_pairs']
        replicate_table.append(f"| {r['origin']}/{r['topology']}/r{r['replicate']} | {count['current']}/{count['checkpoint']}/{count['resample']} | {r['adjacent_pairs']}/48 | {r['all_pose_improvement']} | {r['distance_transfer']} | {r['passes']} |")
    times = sorted({r['additional_generation'] for r in timecourse['results']})
    time_table = []
    for origin in ('native', 'fresh'):
        for topology in ('local', 'evolved'):
            for method in ('evolution', 'resample'):
                cells = []
                for g in times:
                    rows = [r for r in timecourse['results'] if r['additional_generation'] == g and r['condition'].startswith(f'foundation_study/{topology}/{origin}/{method}/')]
                    assert len(rows) == 3
                    optimal = sum(r['levels'][str(l)]['optimal'] for r in rows for l in (1, 2, 3))
                    paired = sum(r['levels'][str(l)]['paired_optimal'] for r in rows for l in (1, 2, 3))
                    cells.append(f'{optimal}/864; {paired}/432')
                time_table.append(f'| {origin}/{topology}/{method} | ' + ' | '.join(cells) + ' |')
    reference_table = []
    for role in ('compiled_bfs', 'compiled_astar', 'wave_bit', 'intact'):
        rows = [results[f'control/r{rep}/{role}/general'] for rep in range(3)]
        reference_table.append(f"| {role} | {sum(r['valid'] for r in rows)}/216 | {sum(r['optimal'] for r in rows)}/216 | {sum(r['no_path'] for r in rows)}/48 |")
    timing_table = [f"| {key} | {v['genotypes']} | {v['matched_inputs']} | {v['median_ratio']:.2f}× | {v['minimum_ratio']:.2f}–{v['maximum_ratio']:.2f}× |" for key, v in timing_comparison.items()]
    passes = ', '.join(k for k, v in screen.items() if v['passes']) or 'none'
    text = f'''# V12D: unchanged evolution, paired transfer and retention

The continuation completed **{summary['additional_rounds']} additional matched generations**, from 442 to {summary['rounds']}, in **{summary['elapsed_seconds']/60:.2f} minutes**. Termination: `{summary['reason']}`. Cohorts passing the stronger preregistered screen: **{passes}**. All 24 populations/RNG continued intact; all final selections froze before new confirmation layouts were generated.

{discussion}

## Primary confirmation

Every elementary cell is **shortest individual outputs /288; complete shortest pairs /144**, across three replicates. Each replicate contributes six independent layouts per level, each in eight correlated poses and with two goals. Both outputs must be shortest-correct to count a pair. V12C checkpoint controls are evaluated on these same new cases; comparing this table with V12C's old test totals would confound changed cases with learning. Original frozen controls date from the beginning of V12C. “Fresh” identifies the originally random V12C cohorts and their descendants; no population was restarted for V12D. Continued resampling preserves 12 elites/niches and draws 84 new independent programs per generation; evolution preserves 12, draws 9 random immigrants and mutates 75 descendants.

| Origin/topology/selection | D=1 | D=2–4 | D=4–8 | D=8–16 | Ordinary legal; shortest | Ordinary shortest D≥8 | Correct no-path |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table)}

| Separate reference | Ordinary legal | Ordinary shortest | Correct no-path |
|---|---:|---:|---:|
{chr(10).join(reference_table)}

## Stronger criterion

A passing replicate needs more non-adjacent complete shortest pairs than **both** its V12C checkpoint and matched continued-resampling champion, plus at least 44/48 adjacent pairs. It also needs either a gain over both controls in level 1 base groups solved in all eight paired poses, or a gain in level 2 pairs across at least two independent level 2 layouts. A cohort needs two of three passing replicates. Different specialists cannot collectively satisfy retention. This is an exploratory screen across four cohorts, with no statistical-significance claim.

| Cohort/replicate | Non-adjacent pairs: current/checkpoint/resample (each /144) | Adjacent pairs | All-pose gain | 4–8-edge transfer gain | Pass |
|---|---:|---:|---:|---:|---:|
{chr(10).join(replicate_table)}

Full per-level, family, orientation-group, failure and per-replicate counts are in `analysis.json`. Secondary per-level archives and their checkpoint/initial counterparts remain labelled separately in raw confirmation. They never replace primary selections in the screen.

## Prespecified time course

Each cell is **non-adjacent shortest outputs /864; complete shortest pairs /432** across three replicates. These additional-generation boundaries were declared before search and selected solely from validation histories before any fresh final layouts. All time points share this same final corpus, so the measurements are correlated. The zero point is the V12C checkpoint champion.

| Cohort | {' | '.join('+'+str(g) for g in times)} |
|---|{'---:|' * len(times)}
{chr(10).join(time_table)}

## Search, ancestry and cost

The curriculum finishes at levels `{summary['levels']}`. The original 144 validation inputs per replicate were deliberately retained for comparable archive ranks and skill certificates. Validation is reused selection data, not unseen evidence. New training uses seed 2026101816 and excludes all 52,424 older layouts, including old final cases, transformations and software fixtures. Candidate RNGs retain their ancestral states/seed; only the environment stream changes. Absolute generation phases preserve family/reflection balance, mixed-task cadence, validation slots and rotating execution order.

Capacity/runtime/fitness/selection remain unchanged: 8 channels, up to 256 genes, 256 ticks, 4096 reads and 32768 instruction dispatches per site. No known or repaired solver enters a random-origin lineage. The audit replays all new edits from the separately verified V12C parent states. `selected_ancestry` records mutation depths and roots across the continuous V12C+V12D lineage; a random immigrant is explicitly distinguished from an initial inherited founder. Syntactic dependencies, gene length and active/read counters characterize programs but do not prove functional complexity. A post-hoc reading of the existing validation records tracks every primary replacement in `primary_selection_changes.json`, including any tradeoff between individual correctness, adjacent retention and non-adjacent complete pairs. This adds no inference or selection rule.

Incremental search cost: **{summary['responses']:,} responses**, **{summary['work']:,} dispatch-plus-read units**, **{summary['max_rss_bytes']/2**20:.1f} MiB peak RSS**. Each condition receives {next(iter(summary['conditions'].values()))['responses']:,} new responses. Cumulative V12C+V12D responses: {summary['cumulative_responses']:,}; cumulative work: {summary['cumulative_work']:,}. This is 75 minutes across all 24 conditions, not 75 minutes for each lineage. Warmup is separate. Small software checks and an early read-only integrity check ran during search; all such work finishes before timing. The host is Apple M4 / 16 GiB, one sequential search process, no GPU/cloud.

Fresh confirmation executes {final['distinct_inferences']:,} distinct candidate/topology/budget/case combinations in {final['elapsed_seconds']:.2f}s; reported aliases total {final['aliased_responses']:,}. Elementary inference uses the training limits; ordinary generalization uses 1024 ticks / 8192 reads / 131072 dispatches per site. The 264 ordinary inputs include 216 reachable and 48 disconnected cases. Full rectangular/square orbits are saved and excluded, while only declared ordinary primary orientations are queried. Final exclusion total: **{final['resulting_layouts']:,} whole layouts**.

## Completed-output timing

Thirty randomized warm repetitions include bytes decoding, state initialization, updates and raster emission. Static model construction is reported separately. Candidate models enter a matched comparison only on shortest-correct outputs. References are timed on fixed 17×17 / 33×33 tree/cyclic cases and each selected elementary success. Ratios greater than 1 mean slower than compiled BFS. Genotypes may be primary, secondary or control selections; tiny-task timing does not establish general-solver efficiency.

| Eligible scope | Genotypes | Model/input comparisons | Median runtime / BFS | Range of per-case median ratios |
|---|---:|---:|---:|---:|
{chr(10).join(timing_table)}

`confirmation/timings.json` records all medians/ranges, warmups, input bytes and array payload estimates. These payload estimates differ from process RSS. Invalid or partial routes receive no speed credit.

## Verification and artifacts

Independent audit passes **{proof['ancestry']['mutations']:,} new mutations**, **{proof['fitness_records']:,} fitness records**, **{proof['graded_search_rasters']:,} graded search rasters**, all {proof['final_rasters']:,} final raster aliases and {proof['distinct_final_replays']:,} distinct candidate replays. It checks every validation raster and every training record claiming legal output or correct no-path, plus a 1/512 sample of remaining records. Every saved fitness calculation is checked. Parent/source/input/selection hashes, ancestry, frozen controls, archive transitions, shared schedules, curriculum and response/work bounds pass. Audit cost {proof['elapsed_seconds']:.2f} s / {proof['max_rss_bytes']/2**20:.1f} MiB, separately recorded. Time-course new inferences and intervention outputs have separate independent grades/replays.

Post-hoc input/range interventions, if present, condition on already successful non-adjacent outputs. Removing goal pulse leaves the static goal flag and endpoint-aware halt intact; zeroing nonlocal values retains their work charge. Interpret them as local dependence tests, not fresh accuracy or a clean multirange treatment effect. No tuning follows confirmation.

![Paired-route transfer](foundation_continuation/visuals/fresh_pairs.png)

![Prespecified transfer time course](foundation_continuation/visuals/timecourse.png)

![A fresh paired-goal example](foundation_continuation/visuals/paired_example.png)

![Ordinary unseen maze examples](foundation_continuation/visuals/ordinary_examples.png)

[Protocol](../docs/FOUNDATION_CONTINUATION_V12D.md) · [search packet](foundation_continuation/search_summary.json) · [confirmation](foundation_continuation/confirmation/summary.json) · [audit](foundation_continuation/verification.json) · [analysis](foundation_continuation/analysis.json). Full next populations/RNG remain in `foundation_continuation/checkpoints/` and `checkpoint.latest.json.gz`. Raw lineage/evaluation segments are immutable; a subsequent experiment needs a new protocol/output and updated exclusions.
'''
    out.with_suffix('.md').write_text(text)
    write_json(out / 'plot_data.json', dict(histories=histories, results=results, screen=replicate_results,
        start_generation=summary['start_generation'], timecourse=timecourse['results']))
    print(out.with_suffix('.md'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
