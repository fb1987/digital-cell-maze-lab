"""V12C descriptive analysis and figures from frozen, independently verified outputs."""
import argparse
from array import array
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics

from .foundation_calibration import write_json
from .foundation_calibration_audit import lines
from .foundation_study import read_compressed
from .growth import Genome
from .range_audit import output_dataflow


def base_group(case):
    return case.rsplit('/d4-', 1)[0][:-2]


def metrics(rows, lookup):
    pairs = [rows[i:i + 2] for i in range(0, len(rows), 2)]
    by_group = defaultdict(list)
    by_family = defaultdict(Counter)
    for row in rows:
        family = by_family[lookup[row['case']]['family']]
        family['outputs'] += 1
        for field in ('reachable', 'valid', 'optimal', 'no_path'):
            family[field] += row[field]
    for pair in pairs:
        if all('pair_optimal' in row for row in pair):
            by_group[base_group(pair[0]['case'])].append(all(row['optimal'] for row in pair))
    return dict(outputs=len(rows), by_family={k: dict(v) for k, v in by_family.items()},
        reachable=sum(r['reachable'] for r in rows),
        valid=sum(r['valid'] for r in rows), optimal=sum(r['optimal'] for r in rows),
        no_path=sum(r['no_path'] for r in rows), pairs=sum(r.get('pair_optimal', False) for r in rows) // 2,
        groups_any_pair=sum(any(v) for v in by_group.values()),
        groups_all_pairs=sum(all(v) for v in by_group.values()), groups=len(by_group),
        long_outputs=sum(lookup[r['case']]['oracle_length'] >= 9 for r in rows),
        long_optimal=sum(r['optimal'] and lookup[r['case']]['oracle_length'] >= 9 for r in rows),
        nonadj_outputs=sum(lookup[r['case']]['oracle_length'] >= 3 for r in rows),
        nonadj_optimal=sum(r['optimal'] and lookup[r['case']]['oracle_length'] >= 3 for r in rows),
        successful_distances=dict(sorted(Counter(lookup[r['case']]['oracle_length'] - 1 for r in rows if r['optimal']).items())),
        failures=dict(Counter(r['failure'] for r in rows if not (r['optimal'] or r['no_path']))),
        range_reads=sum(sum(r.get('range_reads', [])[1:]) for r in rows),
        reads=sum(max(0, r['reads']) for r in rows), dispatches=sum(max(0, r['dispatches']) for r in rows),
        active=sum(max(0, r['active']) for r in rows),
        median_steps=statistics.median(r['steps'] for r in rows),
        maximum_array_bytes=max(r['array_bytes'] for r in rows))


def ancestry(out, summary, wanted):
    depths, roots, details = {}, {}, {}
    for segment in summary['segments']:
        for row in lines(out / segment['files'][0]):
            key, serial = row['id'].rsplit('/i', 1)
            serial = int(serial)
            depth = depths.setdefault(key, array('i'))
            root = roots.setdefault(key, array('i'))
            assert len(depth) == serial
            if row['parent']:
                parent = int(row['parent'].rsplit('/i', 1)[1])
                depth.append(depth[parent] + 1)
                root.append(root[parent])
            else:
                depth.append(0)
                root.append(serial)
            if row['id'] in wanted:
                details[row['id']] = dict(mutation_depth=depth[-1], current_study_root=f'{key}/i{root[-1]}',
                    initial_founder_root=root[-1] < 96, birth=row['birth'], genes=len(row['genome']['genes']))
    assert set(details) == wanted
    return details


def run(out):
    out = Path(out)
    summary = json.loads((out / 'search_summary.json').read_text())
    final = json.loads((out / 'confirmation/summary.json').read_text())
    proof = json.loads((out / 'verification.json').read_text())
    assert proof['all_checks_passed']
    assert hashlib.sha256((out / 'search_summary.json').read_bytes()).hexdigest() == proof['search_summary_sha256']
    assert hashlib.sha256((out / 'confirmation/summary.json').read_bytes()).hexdigest() == proof['confirmation_summary_sha256']
    selections = read_compressed(out / 'frozen_selections.json.gz')
    lookup = {}
    for name in ('mazes.json.gz', 'general_mazes.json.gz'):
        with gzip.open(out / 'confirmation' / name, 'rt') as f:
            lookup.update((m['case_id'], m) for m in json.load(f))
    records = list(lines(out / 'confirmation/outputs.jsonl.gz'))
    indexed = {(r['key'], r['role'], r['scope']): r for r in records}
    results, wanted = {}, set()
    for record in records:
        key = record['key'] + '/' + record['role'] + '/' + record['scope']
        result = metrics(record['cases'], lookup)
        if record['scope'] == 'micro':
            result['levels'] = {str(level): metrics([r for r in record['cases'] if f'/level{level}/' in r['case']], lookup)
                                for level in range(4)}
        results[key] = result
        if record['key'] in selections:
            wanted.add(record['id'])
    details = ancestry(out, summary, wanted)
    for state in selections.values():
        items = [state['champion'], state['frozen']]
        items += [v['item'] for field in ('skills', 'frozen_skills') for v in state[field].values()]
        for item in items:
            details[item['id']]['syntactic_dependencies'] = output_dataflow(Genome.from_dict(item['genome']))
    timing_packet = json.loads((out / 'confirmation/timings.json').read_text())
    bfs_times = {r['case']: r['median'] for r in timing_packet['records'] if r['model'] == 'compiled_bfs'}
    random_digests = {r['digest'] for r in records if r['key'] in selections}
    timing_groups = defaultdict(list)
    for row in timing_packet['records']:
        if isinstance(row['model'], str):
            continue
        kind = 'random-origin' if row['model'][0] in random_digests else 'known wavefront control'
        scope = 'ordinary' if row['case'].startswith('general/') else 'elementary'
        timing_groups[kind, scope].append(dict(model=row['model'][0], case=row['case'],
            ratio=row['median'] / bfs_times[row['case']], seconds=row['median']))
    timing_comparison = {kind + '/' + scope: dict(models=len({r['model'] for r in rs}),
        matched_inputs=len(rs), median_ratio_to_bfs=statistics.median(r['ratio'] for r in rs),
        minimum_ratio=min(r['ratio'] for r in rs), maximum_ratio=max(r['ratio'] for r in rs))
        for (kind, scope), rs in timing_groups.items()}
    screen, per_replicate = {}, []
    for origin in ('native', 'fresh'):
        for topology in ('local', 'evolved'):
            passing = 0
            for rep in range(3):
                key = f'foundation_study/{topology}/{origin}/evolution/{rep}'
                other = key.replace('/evolution/', '/resample/')
                e, r, f = (results[k] for k in (key + '/champion/micro', other + '/champion/micro', key + '/frozen/micro'))
                groups = sum(e['levels'][str(l)]['groups_any_pair'] for l in (1, 2, 3))
                success = e['nonadj_optimal'] > max(r['nonadj_optimal'], f['nonadj_optimal']) and groups >= 2
                passing += success
                per_replicate.append(dict(origin=origin, topology=topology, replicate=rep,
                    evolved_nonadj=e['nonadj_optimal'], resampled_nonadj=r['nonadj_optimal'], frozen_nonadj=f['nonadj_optimal'],
                    evolved_nonadj_pair_groups=groups, passes=success))
            screen[origin + '/' + topology] = dict(passing_replicates=passing, passes=passing >= 2)
    histories = {}
    for key, selection in selections.items():
        cfg = selection['config']
        name = '_'.join(str(cfg[k]) for k in ('origin', 'topology', 'method', 'replicate'))
        state = json.loads((out / 'checkpoints' / (name + '.json')).read_text())
        histories[key] = state['history']
    last_outputs, last_descriptors = defaultdict(set), defaultdict(set)
    last_counts = defaultdict(Counter)
    for row in lines(out / summary['segments'][-1]['files'][1]):
        if row['split'] != 'train' or row['generation'] != summary['rounds'] - 1:
            continue
        key, rs = row['condition'], row['cases']
        last_outputs[key].add(tuple((r['mask'], r['status']) for r in rs))
        last_descriptors[key].add(json.dumps(row['descriptor'], separators=(',', ':')))
        last_counts[key]['organisms'] += 1
        last_counts[key]['responses'] += len(rs)
        last_counts[key]['empty_rasters'] += sum(not r['mask'].strip('0') for r in rs)
        last_counts[key]['budget_failures'] += sum('budget' in r['status'] for r in rs)
        last_counts[key]['organisms_using_nonlocal'] += any(sum(r['range_reads'][1:]) for r in rs)
    assert all(v['organisms'] == 96 for v in last_counts.values()) and len(last_counts) == 24
    analysis = dict(scope='Descriptive analysis after model freeze and independent confirmation; no selection or tuning',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), results=results,
        elementary_screen=screen, per_replicate_screen=per_replicate, selected_ancestry=details,
        distinct_selected_genotypes=len({r['digest'] for r in records if r['key'] in selections}),
        maximum_evaluated_genes=max(h['max_genes'] for hs in histories.values() for h in hs),
        maximum_prepared_genes=max(proof['ancestry']['maximum_registered_genes'].values()),
        last_evaluated_population_unique={k: v[-1]['unique'] for k, v in histories.items()},
        last_training_batch_behavior={k: dict(**dict(v), distinct_output_status_fingerprints=len(last_outputs[k]),
            distinct_selection_descriptors=len(last_descriptors[k])) for k, v in last_counts.items()},
        timing_comparison=timing_comparison,
        primary_success_distances={k: r['successful_distances'] for k, r in results.items() if k.endswith('/champion/general')})
    timecourse_text = ''
    if (out / 'timecourse/summary.json').exists():
        timecourse = json.loads((out / 'timecourse/summary.json').read_text())
        analysis['secondary_timecourse'] = timecourse
        boundaries = sorted({r['generation'] for r in timecourse['results']})
        time_rows = []
        for origin in ('native', 'fresh'):
            for topology in ('local', 'evolved'):
                for method in ('evolution', 'resample'):
                    cells = []
                    for generation in boundaries:
                        rs = [r for r in timecourse['results'] if r['generation'] == generation
                              and r['condition'].startswith(f'foundation_study/{topology}/{origin}/{method}/')]
                        assert len(rs) == 3
                        correct = sum(r['levels'][str(l)]['optimal'] for r in rs for l in (1, 2, 3))
                        paired = sum(r['levels'][str(l)]['paired_optimal'] for r in rs for l in (1, 2, 3))
                        cells.append(f'{correct}/864; {paired}/432')
                    time_rows.append(f'| {origin}/{topology}/{method} | ' + ' | '.join(cells) + ' |')
        timecourse_text = ('\nSecondary transfer time course: added during training before any final layouts existed. '
            'Earlier validation selections were frozen and hashed before confirmation. Each cell is shortest non-adjacent '
            'outputs /864; complete shortest pairs /432 across three replicates. All time points reuse the same fresh cases, '
            'so they are correlated measurements, not independent replications.\n\n| Cohort | ' +
            ' | '.join(f'g{g}' for g in boundaries) + ' |\n|---|' + '---:|' * len(boundaries) + '\n' +
            '\n'.join(time_rows) + '\n')
    write_json(out / 'analysis.json', analysis)
    tables = []
    for origin in ('native', 'fresh'):
        for topology in ('local', 'evolved'):
            for label, method, role in (('evolution', 'evolution', 'champion'), ('resampling', 'resample', 'champion'), ('frozen', 'evolution', 'frozen')):
                cohort = [results[f'foundation_study/{topology}/{origin}/{method}/{rep}/{role}/micro'] for rep in range(3)]
                general = [results[f'foundation_study/{topology}/{origin}/{method}/{rep}/{role}/general'] for rep in range(3)]
                levels = [f"{sum(r['levels'][str(l)]['optimal'] for r in cohort)}/288; {sum(r['levels'][str(l)]['pairs'] for r in cohort)}/144" for l in range(4)]
                tables.append(f"| {origin}/{topology}/{label} | " + ' | '.join(levels) +
                    f" | {sum(r['valid'] for r in general)}/216; {sum(r['optimal'] for r in general)}/216 | {sum(r['no_path'] for r in general)}/48 |")
    replicate_rows = [f"| {r['origin']}/{r['topology']}/r{r['replicate']} | {r['evolved_nonadj']}/288 | {r['resampled_nonadj']}/288 | {r['frozen_nonadj']}/288 | {r['evolved_nonadj_pair_groups']}/18 | {r['passes']} |" for r in per_replicate]
    counts = [r for r in records if r['key'] in selections and r['role'] == 'champion' and r['scope'] == 'general']
    long_correct = sum(results[r['key'] + '/champion/general']['long_optimal'] for r in counts)
    timing_rows = [f"| {k} | {v['models']} | {v['matched_inputs']} | {v['median_ratio_to_bfs']:.2f}× | {v['minimum_ratio']:.2f}–{v['maximum_ratio']:.2f}× |" for k, v in timing_comparison.items()]
    reference_rows = []
    for role in ('compiled_bfs', 'compiled_astar', 'wave_bit', 'intact'):
        rs = [results[f'control/r{rep}/{role}/general'] for rep in range(3)]
        reference_rows.append(f"| {role} | {sum(r['valid'] for r in rs)}/216 | {sum(r['optimal'] for r in rs)}/216 | {sum(r['no_path'] for r in rs)}/48 |")
    text = f'''# V12C: stable random-origin search and fresh confirmation

The preregistered search completed **{summary['rounds']} matched generations in {summary['elapsed_seconds']/60:.2f} minutes** across 24 conditions. Termination: `{summary['reason']}`. All selected genomes were frozen before fresh layouts were generated. Elementary screening results: `{screen}`. These are bounded screening outcomes, not evidence of general or competitive maze solving.

Native V11 populations and separately labelled fresh random populations were compared under local and evolved-range topologies. Evolution/resampling shared founders, initial RNG, tasks and response counts. Resampling retained 12 elites and drew 84 independent programs; evolution retained 12, introduced 9 random immigrants and made 75 single-edit children. Frozen controls are initial validation selections. Known/repaired solver controls never entered these lineages.

Each elementary cell below is **shortest outputs /288; complete shortest pairs /144**, pooled across three replicates. Each replicate contributes six independent base layouts per level, each under eight symmetries and two goals. The pooled 288 responses are therefore not 288 independent layouts. The ordinary column is **legal /216; shortest /216**, using 72 independent reachable cases per replicate; the no-path column uses 16 disconnected cases per replicate. Primary global selections are used throughout this table.

| Cohort | D=1 | D=2–4 | D=4–8 | D=8–16 | Ordinary legal; shortest | Correct no-path |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(tables)}

| Separate reference | Ordinary legal | Ordinary shortest | Correct no-path |
|---|---:|---:|---:|
{chr(10).join(reference_rows)}

The per-replicate screen requires more shortest non-adjacent outputs than both matched resampling and frozen controls, plus at least one complete shortest pair in at least two independent base groups. At least two replicates in a cohort must pass. This is a descriptive screen with several cohort comparisons, not a hypothesis-test p-value. Pose correlations and shared task exposure are retained in the raw data.

| Cohort/replicate | Evolved non-adjacent | Resampled | Frozen | Evolved groups with a complete pair | Pass |
|---|---:|---:|---:|---:|---:|
{chr(10).join(replicate_rows)}

{timecourse_text}

Secondary per-level archives and their own frozen counterparts are in `analysis.json` and raw `confirmation/outputs.jsonl.gz`; they are never substituted for primary results. {analysis['distinct_selected_genotypes']} distinct selected genotypes underlie the many report aliases. The primary ordinary corpus contains {long_correct} successful distance≥8 outputs across all evolution/resampling condition selections; these aliases are not independent algorithm discoveries. Inspect their explicit case/distance distributions before attributing generality.

The common curriculum finishes at levels `{summary['levels']}`. Four current-task rotations were combined with earlier-skill practice and next-level previews, with an explicit disconnected task every eighth generation. Advancement required one candidate to retain earlier paired skills while solving≥90% of current validation pairs. A certificate from any of the eight conditions advanced that replicate's shared schedule, so weaker populations could encounter harder tasks before their own mastery. This design tests a stable search recipe; it does not isolate every change from older studies.

Training used ordinary stopping and bidirectional partial-path credit, never forced tick-16 probes. The runtime remains 8 channels and at most 256 genes. Evaluated genomes reached {analysis['maximum_evaluated_genes']} genes; registered/prepared genomes reached {analysis['maximum_prepared_genes']}. Gene count and proxy-score gains are not evidence of an effective algorithm. `analysis.json` gives selected mutation depths, whether the current-study root was an inherited founder or random immigrant, active/dispatch counts and nonlocal reads. Reading a nonlocal channel alone does not establish a causal multirange advantage.

Search cost: **{summary['responses']:,} ordinary responses**, **{summary['work']:,} dispatch-plus-read units**, **{summary['max_rss_bytes']/2**20:.1f} MiB peak process RSS**. Every condition receives the same number of responses; different programs consume different instructions/time within those slots. This is a 75-minute total study, not 75 minutes per lineage. The bounded total was distributed across 24 conditions. Full prepared populations/RNG and all raw traces are saved for continuation.

Fresh confirmation executes {final['distinct_inferences']:,} distinct program/topology/budget/case combinations, with {final['aliased_responses']:,} reported aliases, in {final['elapsed_seconds']:.2f}s. Elementary limits equal training: 256 ticks/4096 reads/32768 dispatches per site. Ordinary stress tests use 1024/8192/131072. Reference solvers emit complete rasters. Warm timing includes maze decoding, state initialization, updates and raster output; static program setup is separate. Thirty repeated timings, ranges, memory payload estimates and input-byte counts are in `confirmation/timings.json`. Failed routes receive no speed credit. No broad superiority claim follows from tiny-task timings.

| Eligible timing scope | Distinct genotypes | Model/input comparisons | Median runtime / BFS | Range of per-case median ratios |
|---|---:|---:|---:|---:|
{chr(10).join(timing_rows)}

Ratios above1 are slower. Only correctly completed shortest outputs enter these matched-case comparisons; omitted scopes have no eligible candidate. Random-origin timings can include secondary or initial selections and are not a claim about every population member. The reference's30 warm repetitions on each selected case provide the denominator. Input arrays and emitted rasters are included; payload memory estimates and peak process RSS are different quantities. The host is an Apple M4 with16GiB RAM, using one sequential search process and no GPU/cloud. Software checks and a read-only ancestry audit ran concurrently during portions of search; fresh timings follow their completion.

Independent audit: **{proof['fitness_records']:,} fitness records**, **{proof['ancestry']['mutations']:,} mutation traces**, **{proof['graded_search_rasters']:,} independently graded search rasters**, every final raster and {proof['distinct_final_replays']:,} distinct candidate replays. All pass, including source/input/selection hashes, founder identity, exact archives, layout exclusion and response/work bounds. Audit cost {proof['elapsed_seconds']:.2f}s, separately charged. Validation and every training record claiming a valid route or correct no-path are fully checked; the remaining training masks use the preregistered deterministic 1/512 record sample. All saved row-to-fitness arithmetic is checked.

Seed 2026101815; preregistration commit `74b2588`. Search excludes 17,748 previous whole layouts; final confirmation also excludes all search/validation layouts and eight software-only rectangle-transform fixtures created after launch. Those fixtures had no candidate inference and cannot overlap square training tasks. Final total exclusion count: **{final['resulting_layouts']:,} whole layouts**. All rotations/reflections are excluded, including constructed but unqueried ordinary poses.

Calibration preceding this run is retained separately: V12A fails its repair gate; V12B passes after testing single versus 1–6 edits on orientation-balanced batches. That evidence supports bounded searchability, not solver injection or random-origin success by itself.

![Validation progress](foundation_study/visuals/validation.png)

![Fresh paired-route accuracy](foundation_study/visuals/fresh_pairs.png)

![Illustrative fresh goal switch](foundation_study/visuals/paired_example.png)

![Ordinary fresh maze examples](foundation_study/visuals/ordinary_examples.png)

Protocol: [V12C](../docs/FOUNDATION_STUDY_V12C.md). [Search packet](foundation_study/search_summary.json), [fresh confirmation](foundation_study/confirmation/summary.json), [independent audit](foundation_study/verification.json), [analysis](foundation_study/analysis.json).
'''
    out.with_suffix('.md').write_text(text)
    # Plotting runs separately with isolated optional dependencies.
    write_json(out / 'plot_data.json', dict(histories=histories, results=results,
        selected_initial={k: v['frozen_rank'][1] for k, v in selections.items()}))
    print(out.with_suffix('.md'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
