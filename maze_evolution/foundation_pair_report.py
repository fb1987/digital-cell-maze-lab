"""V12E descriptive comparison from frozen models, fresh results and exact audit."""
import argparse
from array import array
from collections import Counter, defaultdict, deque
import gzip
import hashlib
import json
from pathlib import Path
import statistics

from .foundation_calibration import ROOT, write_json
from .foundation_calibration_audit import lines
from .foundation_pair import state_key
from .foundation_pair_screen import level_metrics, replicate_screen
from .foundation_study import read_compressed
from .foundation_study_report import metrics
from .growth import Genome
from .range_audit import output_dataflow


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def condition(topology, policy, method, rep):
    return f'foundation_pair_{policy}/{topology}/fresh/{method}/{rep}'


def source_component(m):
    cells = bytes.fromhex(m['cells_hex'])
    width, height = m['w'], m['h']
    reached, queue = {m['start']}, deque([m['start']])
    edges = 0
    while queue:
        p = queue.popleft()
        y, x = divmod(p, width)
        for yy, xx in ((y,x-1),(y,x+1),(y-1,x),(y+1,x)):
            q = yy * width + xx
            if 0 <= yy < height and 0 <= xx < width and cells[q]:
                edges += p < q
                if q not in reached:
                    reached.add(q)
                    queue.append(q)
    return dict(vertices=len(reached), edges=edges, independent_cycles=edges-len(reached)+1)


def route_geometry(row, m):
    packed = bytes.fromhex(row['mask'])
    occupied = {p for p in range(m['w'] * m['h']) if (packed[p // 8] >> (p % 8)) & 1}
    p, previous, directions = m['start'], None, []
    visited = {p}
    while p != m['goal']:
        y, x = divmod(p, m['w'])
        following = [yy * m['w'] + xx for yy, xx in ((y,x-1),(y,x+1),(y-1,x),(y+1,x))
            if 0 <= yy < m['h'] and 0 <= xx < m['w']
            and yy * m['w'] + xx in occupied and yy * m['w'] + xx != previous]
        assert len(following) == 1
        q = following[0]
        assert q not in visited
        visited.add(q)
        directions.append(q-p)
        previous, p = p, q
    assert visited == occupied and len(directions) == m['oracle_length'] - 1
    return dict(distance=len(directions), turns=sum(a != b for a, b in zip(directions, directions[1:])))


def completed_pair_geometry(records, lookup):
    """Describe already audited primary successes; no new inference or selection."""
    result = []
    for record in records:
        if record['role'] != 'champion' or record['scope'] != 'micro' or not record['key'].startswith('foundation_pair_'):
            continue
        rows = record['cases']
        for a, b in zip(rows[::2], rows[1::2]):
            if not a['pair_optimal'] or '/level0/' in a['case']:
                continue
            turns, distances_ = [], []
            for row in (a, b):
                m = lookup[row['case']]
                geometry = route_geometry(row,m)
                distances_.append(geometry['distance'])
                turns.append(geometry['turns'])
            m = lookup[a['case']]
            result.append(dict(condition=record['key'], cases=[a['case'],b['case']],
                base_group=a['case'].rsplit('/d4-',1)[0][:-2], family=m['family'],
                distances=distances_, turns=turns, **source_component(m)))
    return result


def longer_ordinary_geometry(out, records, lookup):
    interventions = {}
    if (out/'interventions/outputs.jsonl.gz').exists():
        for record in lines(out/'interventions/outputs.jsonl.gz'):
            for alias in record['aliases']:
                if alias['scope']=='general' and alias['role']=='champion':
                    interventions[alias['condition'],record['case']] = record['variants']
    observations = []
    for record in records:
        if record['role']!='champion' or record['scope']!='general' or not record['key'].startswith('foundation_pair_'):
            continue
        for row in record['cases']:
            m = lookup[row['case']]
            if not row['optimal'] or m['oracle_length']<9:
                continue
            variants = interventions.get((record['key'],row['case']),{})
            if variants:
                assert variants['replay']['mask']==row['mask']
            observations.append(dict(condition=record['key'],id=record['id'],case=row['case'],
                family=m['family'],steps=row['steps'],**route_geometry(row,m),**source_component(m),
                intervention_shortest={name:r['optimal'] for name,r in variants.items()}))
    return observations


def selected_ancestry(out, summary, wanted):
    """Continuous C/D/E ancestry; forks retain parents in their old namespaces."""
    depths, roots, offsets, root_names, root_births, details = {}, {}, {}, [], [], {}
    packets = [(ROOT / 'results/foundation_study'), (ROOT / 'results/foundation_continuation'), out]
    for packet in packets:
        source = summary if packet == out else json.loads((packet / 'search_summary.json').read_text())
        for segment in source['segments']:
            for row in lines(packet / segment['files'][0]):
                key, serial = row['id'].rsplit('/i', 1)
                serial = int(serial)
                offset = offsets.setdefault(key, serial)
                depth, root = depths.setdefault(key, array('i')), roots.setdefault(key, array('i'))
                assert len(depth) == serial - offset
                if row['parent']:
                    parent_key, parent_serial = row['parent'].rsplit('/i', 1)
                    index = int(parent_serial) - offsets[parent_key]
                    depth.append(depths[parent_key][index] + 1)
                    root.append(roots[parent_key][index])
                else:
                    depth.append(0)
                    root.append(len(root_names))
                    root_names.append(row['id'])
                    root_births.append(row['birth'])
                if row['id'] in wanted:
                    details[row['id']] = dict(mutation_depth=depth[-1], root=root_names[root[-1]],
                        root_birth=root_births[root[-1]], initial_founder_root=root_births[root[-1]] == 0,
                        birth=row['birth'], genes=len(row['genome']['genes']))
                    assert '/fresh/' in details[row['id']]['root']
    assert set(details) == wanted
    return details


def intervention_counts(out, records):
    counts, outcomes = defaultdict(Counter), {}
    for record in lines(out / 'interventions/outputs.jsonl.gz'):
        for alias in record['aliases']:
            if alias['role'] != 'champion' or alias['scope'] != 'micro':
                continue
            key = alias['condition']
            band = next(l for l in range(5) if f'/level{l}/' in record['case'])
            counts[key]['original_successes'] += 1
            for name, row in record['variants'].items():
                counts[key][name] += row['optimal']
                counts[key][f'band{band}_{name}'] += row['optimal']
                outcomes[key, name, record['case']] = row['optimal']
    for record in records:
        if record['role'] != 'champion' or record['scope'] != 'micro' or not record['key'].startswith('foundation_pair_'):
            continue
        for i in range(0, len(record['cases']), 2):
            a, b = record['cases'][i:i + 2]
            if not a['pair_optimal'] or '/level0/' in a['case']:
                continue
            band = next(l for l in range(1,5) if f'/level{l}/' in a['case'])
            for name in ('replay','no_goal_pulse','zero_nonlocal','both'):
                value = int(outcomes[record['key'],name,a['case']] and outcomes[record['key'],name,b['case']])
                counts[record['key']][name + '_pairs'] += value
                counts[record['key']][f'band{band}_{name}_pairs'] += value
    return {key: dict(value) for key,value in counts.items()}


def run(out):
    out = Path(out)
    summary = json.loads((out/'search_summary.json').read_text())
    final = json.loads((out/'confirmation/summary.json').read_text())
    proof = json.loads((out/'verification.json').read_text())
    assert proof['all_checks_passed']
    assert sha(out/'search_summary.json') == proof['search_summary_sha256']
    assert sha(out/'confirmation/summary.json') == proof['confirmation_summary_sha256']
    frozen = read_compressed(out/'frozen_selections.json.gz')
    checkpoint = read_compressed(out/'checkpoint.latest.json.gz')
    initial = {state_key(s): s for s in read_compressed(out/'initial_states.json.gz')}
    histories = {state_key(s): s['history'] for s in checkpoint['states']}
    records = list(lines(out/'confirmation/outputs.jsonl.gz'))
    indexed = {(r['key'],r['role'],r['scope']):r for r in records}
    lookup = {}
    for name in ('mazes.json.gz','general_mazes.json.gz'):
        with gzip.open(out/'confirmation'/name,'rt') as f:
            lookup.update((m['case_id'],m) for m in json.load(f))
    elementary_components = {case: dict(family=m['family'], **source_component(m))
        for case,m in lookup.items() if case.endswith('/a/d4-0')}
    component_totals = defaultdict(Counter)
    for value in elementary_components.values():
        component_totals[value['family']]['base_layouts'] += 1
        component_totals[value['family']]['cyclic_source_components'] += value['independent_cycles'] > 0
    results = {}
    for record in records:
        key = '/'.join((record['key'],record['role'],record['scope']))
        value = metrics(record['cases'],lookup)
        value['false_reachable_no_path'] = sum(r['reachable'] and r['status']=='no_path' for r in record['cases'])
        if record['scope'] == 'micro':
            value['bands'] = level_metrics(record['cases'])
            value['levels'] = {str(l):metrics([r for r in record['cases'] if f'/level{l}/' in r['case']],lookup)
                               for l in range(5)}
        results[key] = value
    screens, per_rep = {}, []
    for topology in ('local','evolved'):
        for rep in range(3):
            paired,current,resample = (condition(topology,p,m,rep) for p,m in
                                       (('paired','evolution'),('current','evolution'),('current','resample')))
            models = [results[f'{k}/{role}/micro']['bands'] for k,role in
                      ((paired,'champion'),(current,'champion'),(paired,'checkpoint'),(resample,'champion'))]
            decision = replicate_screen(*models)
            per_rep.append(dict(topology=topology,replicate=rep,**decision,
                challenge_pairs={name:sum(m[str(l)]['pairs'] for l in (2,3))
                    for name,m in zip(('paired','current','checkpoint','resample'),models)},
                adjacent_pairs=models[0]['0']['pairs'],two_edge_pairs=models[0]['1']['pairs']))
        passes=sum(r['passes'] for r in per_rep if r['topology']==topology)
        screens[topology]=dict(passing_replicates=passes,passes=passes>=2)
    divergence = []
    for topology in ('local','evolved'):
        for rep in range(3):
            current,paired = [condition(topology,p,'evolution',rep) for p in ('current','paired')]
            dna = [g for g in range(summary['start_generation'],summary['rounds'])
                   if histories[current][g]['population_sha256'] != histories[paired][g]['population_sha256']]
            rng = [g for g in range(summary['start_generation'],summary['rounds'])
                   if histories[current][g]['rng_sha256'] != histories[paired][g]['rng_sha256']]
            divergence.append(dict(topology=topology,replicate=rep,
                first_different_completed_generation=(dna[0]+1 if dna else None),
                different_population_rounds=len(dna),different_rng_rounds=len(rng)))
    timings=json.loads((out/'confirmation/timings.json').read_text())
    bfs={r['case']:r['median'] for r in timings['records'] if r['model']=='compiled_bfs'}
    candidate_digests={r['digest'] for r in records if r['key'] in frozen}
    matched=defaultdict(list)
    for row in timings['records']:
        if isinstance(row['model'],str): continue
        kind='random-origin' if row['model'][0] in candidate_digests else 'known wavefront'
        scope='ordinary' if row['case'].startswith('general/') else 'elementary'
        matched[kind+'/'+scope].append(dict(model=row['model'][0],case=row['case'],seconds=row['median'],ratio=row['median']/bfs[row['case']]))
    timing_comparison={k:dict(models=len({r['model'] for r in rows}),comparisons=len(rows),
        median_ratio=statistics.median(r['ratio'] for r in rows),minimum_ratio=min(r['ratio'] for r in rows),
        maximum_ratio=max(r['ratio'] for r in rows)) for k,rows in matched.items()}
    wanted={r['id'] for r in records if r['key'] in frozen}
    ancestry=selected_ancestry(out,summary,wanted)
    for state in frozen.values():
        for item in [state['frozen'],*[v['item'] for v in state['common_archives'].values()]]:
            if item['id'] in ancestry:
                ancestry[item['id']]['syntactic_dependencies']=output_dataflow(Genome.from_dict(item['genome']))
    timecourse=json.loads((out/'timecourse/summary.json').read_text())
    reproduction=json.loads((out/'reproduction.json').read_text())
    changes=json.loads((out/'primary_selection_changes.json').read_text())
    analysis=dict(scope='Descriptive analysis after frozen model selection, fresh confirmation and independent audit; no reselection or tuning.',
        source_sha256=sha(__file__),results=results,transfer_screen=screens,per_replicate_screen=per_rep,
        matched_population_divergence=divergence,reproduction=reproduction,validation_archive_changes=changes,
        elementary_source_components=elementary_components,
        elementary_component_totals={k:dict(v) for k,v in component_totals.items()},
        completed_primary_pair_geometry=completed_pair_geometry(records,lookup),
        longer_primary_ordinary_geometry=longer_ordinary_geometry(out,records,lookup),
        selected_ancestry=ancestry,timing_comparison=timing_comparison,timing_matches=dict(matched),
        secondary_timecourse=timecourse,maximum_new_evaluated_genes=max(h['max_genes'] for hs in histories.values()
            for h in hs[summary['start_generation']:]),
        maximum_final_prepared_genes=max(len(i['genome']['genes']) for s in checkpoint['states'] for i in s['population']))
    if (out/'interventions/summary.json').exists():
        analysis['interventions']=json.loads((out/'interventions/summary.json').read_text())
        analysis['primary_interventions']=intervention_counts(out,records)
    discussion=(out/'discussion.md').read_text() if (out/'discussion.md').exists() else ''
    analysis['discussion_sha256']=hashlib.sha256(discussion.encode()).hexdigest()
    write_json(out/'analysis.json',analysis)
    plot_histories={key:[dict(generation=summary['start_generation']-1,
        common_archives={name:dict(rank=entry['rank'],id=entry['item']['id']) for name,entry in initial[key]['common_archives'].items()}),
        *histories[key][summary['start_generation']:]] for key in frozen}
    write_json(out/'plot_data.json',dict(start_generation=summary['start_generation'],rounds=summary['rounds'],
        configs={k:v['config'] for k,v in frozen.items()},histories=plot_histories,results=results,
        timecourse=timecourse['results'],screen=per_rep))

    def summed(topology,policy,method,role,scope):
        return [results[f'{condition(topology,policy,method,r)}/{role}/{scope}'] for r in range(3)]
    table=[]
    for topology in ('local','evolved'):
        for label,policy,method,role in [('Current','current','evolution','champion'),('Paired','paired','evolution','champion'),
            ('Resampling','current','resample','champion'),('V12D checkpoint','paired','evolution','checkpoint'),
            ('Original frozen','paired','evolution','frozen')]:
            micro=summed(topology,policy,method,role,'micro'); general=summed(topology,policy,method,role,'general')
            pairs=[sum(v['bands'][str(l)]['pairs'] for v in micro) for l in range(5)]
            table.append(f"| {topology}/{label} | "+' | '.join(f'{v}/144' for v in pairs)+
                f" | {sum(v['valid'] for v in general)}/216; {sum(v['optimal'] for v in general)}/216 | {sum(v['long_optimal'] for v in general)}/{sum(v['long_outputs'] for v in general)} | {sum(v['no_path'] for v in general)}/48; {sum(v['false_reachable_no_path'] for v in general)}/216 false |")
    secondary=[]
    for topology in ('local','evolved'):
        for policy in ('current','paired'):
            micro=summed(topology,policy,'evolution','original_rank','micro'); general=summed(topology,policy,'evolution','original_rank','general')
            secondary.append(f"| {topology}/{policy} | {sum(v['levels']['2']['pairs']+v['levels']['3']['pairs'] for v in micro)}/288 | {sum(v['nonadj_optimal'] for v in micro)}/1152 | {sum(v['optimal'] for v in general)}/216 |")
    gates=[]
    for r in per_rep:
        c=r['challenge_pairs']
        gates.append(f"| {r['topology']}/r{r['replicate']} | {c['paired']}/{c['current']}/{c['checkpoint']}/{c['resample']} | {r['adjacent_pairs']}/48 | {r['two_edge_pairs']} ≥ {r['two_edge_threshold']} | {r['two_independent_challenge_groups']} | {r['all_pose_challenge_group']} | {r['passes']} |")
    times=sorted({r['additional_generation'] for r in timecourse['results']})
    time_rows=[]
    for topology in ('local','evolved'):
        for policy,method in [('current','evolution'),('paired','evolution'),('current','resample')]:
            values=[]
            for additional in times:
                records_=[r for r in timecourse['results'] if r['condition'] in {condition(topology,policy,method,rep) for rep in range(3)} and r['additional_generation']==additional]
                challenge=sum(r['levels'][str(l)]['paired_optimal'] for r in records_ for l in (2,3))
                two=sum(r['levels']['1']['paired_optimal'] for r in records_)
                values.append(f'{challenge}/288; {two}/144')
            time_rows.append(f"| {topology}/{policy}/{method} | "+' | '.join(values)+' |')
    reference=[]
    for name in ('compiled_bfs','compiled_astar','wave_bit','intact'):
        rows=[results[f'control/r{r}/{name}/general'] for r in range(3)]
        reference.append(f"| {name} | {sum(v['valid'] for v in rows)}/216 | {sum(v['optimal'] for v in rows)}/216 | {sum(v['no_path'] for v in rows)}/48 |")
    timing_rows=[f"| {key} | {v['models']} | {v['comparisons']} | {v['median_ratio']:.2f}× | {v['minimum_ratio']:.2f}–{v['maximum_ratio']:.2f}× |" for key,v in timing_comparison.items()]
    passes=', '.join(k for k,v in screens.items() if v['passes']) or 'none'
    component_text='; '.join(f"{family}: {v['cyclic_source_components']}/{v['base_layouts']} base layouts have a cycle in the source component"
                             for family,v in component_totals.items())
    report=f'''# V12E: completed-pair priority versus current selection

The matched comparison completes **{summary['additional_rounds']} additional generations** ({summary['start_generation']}→{summary['rounds']}) in **{summary['elapsed_seconds']/60:.2f} minutes** across 18 conditions of 96 organisms. Termination: `{summary['reason']}`. Cohorts passing the preregistered transfer screen: **{passes}**. All models and time-course selections froze before fresh confirmation layouts.

{discussion}

## Primary comparison under the same archival rule

Current and Paired evolution start from identical saved populations/RNG within each topology/replicate. The final primary model in EVERY arm uses the same validation rank: complete shortest pairs first, then individual validity/optimality/no-path and unchanged shaping/cost. This separates the breeding-policy comparison from different final archival rules. Old validation is reused selection data; all figures below use separately generated final cases unless labelled validation.

Each elementary cell is **complete shortest pairs /144**, across three replicates (six base layouts × eight correlated poses per band/replicate). Both goals lie within the stated distance band. Individual counts, failures, families, independent groups and every replicate are retained in `analysis.json` and raw outputs. The poses are not independent layouts. These bands differ from V12D; use the checkpoint on THESE cases for comparison. Source-component cycle counts are independently characterized: {component_text}. A random-grid family label alone is not taken as proof of a cycle in the source component.

| Topology/selection | D=1 | D=2 | D=3–4 | D=5–8 | D=9–16 | Ordinary legal; shortest | Ordinary D≥8 | Correct no-path; false claims |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

The secondary selections below use the common ORIGINAL rank in both arms; they do not replace primary models or alter the screen.

| Topology/breeding policy | D=3–8 pairs | Non-adjacent shortest outputs | Ordinary shortest |
|---|---:|---:|---:|
'''+ '\n'.join(secondary)+'''

| Separate reference | Ordinary legal | Ordinary shortest | Correct no-path |
|---|---:|---:|---:|
'''+ '\n'.join(reference)+'''

## Fixed transfer and retention criterion

A passing Paired primary must beat Current, the V12D checkpoint and resampling on complete 3–8-edge pairs; span at least two independent challenge layouts, including one with all eight paired poses correct; retain ≥44/48 adjacent pairs and ≥ceil(90% of its checkpoint's exact-two pairs). All requirements apply to the same genome. Two of three replicates must pass per topology. Zero two-edge baselines produce a zero threshold and are shown explicitly. This is an exploratory screen, not a significance claim.

| Replicate | D=3–8 pairs: Paired/Current/checkpoint/resample (each /96) | Adjacent | Two-edge retention | ≥2 challenge layouts | All-pose challenge layout | Pass |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(gates)+'''

## Prespecified same-corpus time course

Cells are **3–8-edge complete pairs /288; exact-two pairs /144**. Selections were fixed from validation histories before final-case generation; all time points reuse this corpus and are correlated.

| Cohort | '''+' | '.join('+'+str(t) for t in times)+''' |
|---|'''+ '|'.join('---:' for _ in times)+'''|
'''+ '\n'.join(time_rows)+f'''

## Search process and audit

Global rank changes `(V,O,N,P,S,W)`→`(P,V,O,N,S,W)` in the treatment; P counts BOTH shortest-correct emitted routes. The per-case pair field reordering is logically redundant on a fixed ordered pool because pair success implies individual correctness. Global ranking, elite/niche retention and nominee ordering can differ. `reproduction.json` reports actual exact replay and same-pool/same-RNG alternative parent choices; those counterfactuals are not another evolved trajectory. `matched_population_divergence` records differences between the actual two arms at every generation.

Every new child, its mutation events or random origin, parent draw, retained population and RNG hash replay from the verified starting states. The audit passes **{proof['reproduction']['registered']:,} new programs**, **{proof['reproduction']['mutations']:,} mutations**, **{proof['fitness_records']:,} fitness records**, **{proof['graded_search_rasters']:,} independently graded search rasters**, all **{proof['final_rasters']:,} final raster aliases** and **{proof['distinct_final_replays']:,} distinct candidate replays**. Every validation raster, training success and a fixed 1/512 sample of other training records is graded; every saved fitness calculation is checked. Layout isolation, transformed labels, archive maxima, shared schedules, full continuation state, source/input hashes and work/response bounds pass. Auxiliary tests and the early integrity check are documented in `software_checks.json`.

The runtime/grammar and 8-channel/256-gene limits remain unchanged; mutation is still one requested edit. Search uses 256 ticks /4096 reads /32768 dispatches per site. Each evolution condition retains 12 elites/niches, adds 9 random immigrants and 75 descendants; resampling retains 12 and adds 84 independent programs. The common 12-input batch, four validation nominations every eighth absolute generation, and competence-driven curriculum are unchanged. Final levels: `{summary['levels']}`. Shared curriculum transitions, if any, are reported in the raw summary. No known solver enters a random-origin lineage. Continuous C/D/E ancestry and syntactic dependency slices are saved; gene count and syntactic reachability are not proof of effective complexity.

New environment seed {summary['seed']}, continuous candidate RNG, {summary['excluded_layouts']:,} earlier/fixture layouts excluded from new training. The 432 original validation responses remain explicit reused selection data. Final exclusion total: **{final['resulting_layouts']:,} whole layouts**, including unqueried ordinary transformations. No retuning against inspected final inputs.

## Cost and completed-output timing

Incremental search: **{summary['responses']:,} responses**, **{summary['work']:,} dispatch-plus-read units**, **{summary['max_rss_bytes']/2**20:.2f} MiB peak RSS**. Parent histories are duplicated across forks and are not counted as additional compute. This is 75 minutes across all 18 conditions, not per population. Initial JIT warmup, software checks, audit, analysis, figures and Git operations are separate; small checks and the early audit ran during search and consume wall time available to all arms equally.

Confirmation: {final['elapsed_seconds']:.2f} s, {final['distinct_inferences']:,} distinct candidate/model/case responses. Ordinary tests use 1024 ticks /8192 reads /131072 dispatches per site; elementary limits match training. Audit: {proof['elapsed_seconds']:.2f} s, {proof['max_rss_bytes']/2**20:.1f} MiB peak. Host/dependency versions and exact counters are in the search packet. Local CPU only.

Thirty randomized warm repetitions include maze bytes decoding, state initialization, updates and emitted raster. Static model setup is separate. Only shortest-correct candidates receive matched timing comparisons; an invalid or partial output is not a faster solution. Ratios >1 mean slower than compiled BFS. Tiny-task timings do not establish general-solver efficiency.

| Eligible scope | Genotypes | Comparisons | Median runtime / BFS | Range of per-case ratios |
|---|---:|---:|---:|---:|
'''+ '\n'.join(timing_rows)+'''

Success-conditioned pulse/nonlocal interventions, if present, reuse successful final inputs. Static goal flags and endpoint halting remain during pulse removal; zeroed nonlocal values retain their work charges. These are local dependence diagnostics, not new generalization estimates or a clean topology treatment effect.

![Fresh paired transfer and retention](foundation_pair/visuals/fresh_pairs.png)

![Prespecified time course](foundation_pair/visuals/timecourse.png)

![Local paired example](foundation_pair/visuals/paired_local.png)

![Evolved-range paired example](foundation_pair/visuals/paired_evolved.png)

![Ordinary unseen maze examples](foundation_pair/visuals/ordinary_examples.png)

![Preserved longer-route precursor and pulse intervention](foundation_pair/visuals/longer_current_example.png)

[Protocol](../docs/FOUNDATION_PAIR_V12E.md) · [search](foundation_pair/search_summary.json) · [confirmation](foundation_pair/confirmation/summary.json) · [audit](foundation_pair/verification.json) · [reproduction](foundation_pair/reproduction.json) · [analysis](foundation_pair/analysis.json). Full next populations/RNG and all raw lineage/evaluation data remain saved. A subsequent study needs a new protocol and all updated layout exclusions.
'''
    (out.parent/(out.name+'.md')).write_text(report)
    print(out.parent/(out.name+'.md'))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
