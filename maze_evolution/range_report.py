"""Read-only interpretation of the range study; no model selection on tests."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics

from .experiment import write_json


def report(out):
    out=Path(out)
    config=json.loads((out/'config.json').read_text())
    env=json.loads((out/'environment.json').read_text())
    champions=json.loads((out/'champions.json').read_text())
    assert hashlib.sha256((out/'champions.json').read_bytes()).hexdigest()==env['champions_sha256']
    summary=json.loads((out/'summary.json').read_text())
    timings=json.loads((out/'timings.json').read_text())
    with gzip.open(out/'holdout.jsonl.gz','rt') as handle:
        rows=[json.loads(line) for line in handle]
    byarm={r['arm']:r for r in summary if r['group']=='all'}
    # A successful all-open response is a favourable special case, not evidence
    # of discovery; source-only output likewise does not count as a solver.
    with gzip.open(out/'mazes.json.gz','rt') as handle:
        cases={row['case_id']:row for row in json.load(handle)}
    phenotypes=defaultdict(Counter)
    for row in rows:
        n=row['w']*row['h']
        raw=bytes.fromhex(row['mask'])
        selected={p for p in range(n) if (raw[p//8]>>(p%8))&1}
        maze=cases[row['case_id']]
        opened={p for p,v in enumerate(bytes.fromhex(maze['cells_hex'])) if v}
        if selected==opened:
            phenotypes[row['arm']]['all_open']+=1
            if row['valid_path']:
                phenotypes[row['arm']]['all_open_successes']+=1
        if selected=={maze['start']}:
            phenotypes[row['arm']]['source_only']+=1
        if not selected:
            phenotypes[row['arm']]['empty']+=1
    audit=dict(phenotypes=dict(phenotypes), champions_unchanged=True,
               next_step='Continue random-origin discovery separately; do not infer impossibility from these bounded runs.')
    write_json(out/'phenotype_audit.json',audit)
    lines=['# Range and regulation study', '',
        'Random-origin discovery remains an active research track. This study tests a '
        'specific larger regulatory substrate and search policy; a failure here does not '
        'establish that emergence is impossible or that additional capacity/time cannot help.', '',
        f"Run {env['recorded_at']}; {env['cpu']}, Python {env['python']}; "
        f"elapsed {env['elapsed_seconds']:.1f}s. {config['replicates']} independent evolutionary seeds.", '',
        '## Controlled topology comparison', '',
        f"{config['control']['population']} organisms × {config['control']['generations']} generations, "
        'random and locally wavefront-seeded origins. All topologies share the V2 runtime, '
        'grammar, initial genotype lists, mazes and limits. Local primitives stay radius 1. '
        'Only REMOTE/REMOTE_MIN sample other ranges: local always 1; fixed cycles 1/2/4/8 '
        'by tick; evolved uses a heritable per-gene range. Gates control expression in every arm.', '',
        '| Arm | Shortest / reachable | Correct no-path | Budget failures | Nonlocal reads |',
        '| --- | ---: | ---: | ---: | ---: |']
    for arm,r in sorted(byarm.items()):
        if arm.startswith('control/') and not arm.endswith('/ablate'):
            lines.append(f"| {arm[8:]} | {r['optimal']}/{r['reachable']} | "
                         f"{r['no_path']}/{r['unreachable']} | {r['budget_failures']} | {r['nonlocal_reads']:,} |")
    lines+=['', '## Larger random-origin track', '',
        f"{config['rich']['population']} organisms × {config['rich']['generations']} generations "
        'per run, local and evolvable ranges, with eight uint16 state channels, 64 local '
        'registers and up to 128 genes (3,584 binary bytes). Random initial genomes have '
        '64–128 instructions; none are derived from the wavefront seed. The model, '
        'curriculum and search policy change together here: this is an exploratory bundle, '
        'not an isolated causal test of genome length.', '',
        '| Arm | Shortest / reachable | Shortest with distance ≥8 | Correct no-path | Nonlocal reads |',
        '| --- | ---: | ---: | ---: | ---: |']
    for arm,r in sorted(byarm.items()):
        if arm.startswith('rich/') and not arm.endswith('/ablate'):
            lines.append(f"| {arm[5:]} | {r['optimal']}/{r['reachable']} | {r['long_optimal']}/{r['long_cases']} | "
                         f"{r['no_path']}/{r['unreachable']} | {r['nonlocal_reads']:,} |")
    lines+=['', '## Range dependence and budget diagnostic', '',
        'Ablations zero nonlocal reads at frozen genotypes; they still charge the reads. '
        'They do not retrain or repair the output. Availability, actual range use and '
        'accuracy benefit are distinct claims.', '',
        '| Frozen evolved arm | Normal shortest | Nonlocal ablated shortest |',
        '| --- | ---: | ---: |']
    for arm,r in sorted(byarm.items()):
        if arm.endswith('/ablate'):
            original=byarm[arm[:-7]]
            lines.append(f"| {arm[:-7]} | {original['optimal']}/{original['reachable']} | {r['optimal']}/{r['reachable']} |")
    diag=byarm['diagnostic/local_seed_old_budget']
    new=byarm['control/local/seeded/frozen']
    lines+=['', f"The same frozen local seed under old limits solves {diag['optimal']}/{diag['reachable']}; "
        f"under V2 test limits, {new['optimal']}/{new['reachable']}. This isolates additional "
        'inference budget from a topology/evolution claim. It does not replicate the old '
        'runtime’s exact overhead or stopping rule.', '',
        '## What the saved phenotypes actually do', '']
    for arm,counts in sorted(phenotypes.items()):
        if arm.startswith('rich/') and not arm.endswith('/ablate'):
            lines.append(f'- {arm}: {dict(counts)}.')
    lines+=['', '| Evolution condition | Champion genes | New genotype from initial pool? |',
            '| --- | ---: | --- |']
    for key,saved in sorted(champions.items()):
        if saved['config']['method']=='evolution':
            from .regulatory import Genome
            genome=Genome.from_dict(saved['champion']['genome'])
            lines.append(f"| {key} | {len(genome.genes)} | {genome.digest not in saved['initial_digests']} |")
    lines+=['', '## Cost and timing', '',
        '| Arm | Median of correct 17x17 instance medians (µs) | Correct timed instances |',
        '| --- | ---: | ---: |']
    for arm in sorted(byarm):
        if arm.endswith('/ablate') or arm.startswith('diagnostic/'):
            continue
        values=[row['median_us'] for row in timings if row['arm']==arm and row['n']==17
                and row['correct']==row['repeats']]
        lines.append(f"| {arm} | {statistics.median(values):.2f} | {len(values)} |" if values
                     else f'| {arm} | n/a | 0 |')
    largest=max(r['largest_array_bytes'] for r in summary)
    lines+=['', f"Timing uses {config['benchmark_repeats']} warm repetitions on selected fresh "
        '17x17/33x33 perfect and random instances, randomized solver order and common raw-byte '
        'input/binary-raster output. Oracle, validation, JIT and one-time genome encoding are '
        'excluded. Every repetition is independently checked. Failed outputs do not count '
        'as fast solutions; no competitive performance claim follows from this pilot.', '',
        f'Largest accounted array payload: {largest:,} bytes. Whole-run maximum RSS '
        f"{env['max_rss_bytes']/2**20:.1f} MiB includes JIT, the evaluator, mazes and result buffers. "
        'Array bounds are not full allocator/process peaks per solver. Expression gates skip '
        'operand reads and primitive execution, but every gene dispatch is charged and '
        'every site still incurs scanning/register-reset work. These proxies are not energy.', '',
        '## Protocol and limits', '',
        f"Training limits: `{config['train_limits']}`. Test/validation limits: `{config['eval_limits']}`. "
        'Each limit is shared by topologies and search methods. Work on an interrupted tick '
        'is charged, but its partial next state is discarded. Range reads cannot wrap across '
        'rows; nonlocal sensing can cross intervening walls, while wall sites remain zero '
        'and final path legality always uses adjacent open grid cells.', '',
        'A source-local channel-7 request with both output endpoints lit proposes emission; '
        'alternatively, four unchanged full-state ticks settle a response. All four fixed '
        'range phases must be quiet. The evaluator independently rejects malformed or '
        'illegal settled outputs. This removes V1’s implicit halt as soon as both endpoints '
        'lit, which excluded strategies that first illuminate broadly and later prune.', '',
        'Fitness preserves V1’s legality/optimality/no-path/partial priorities and shaping. '
        'The cost tie-break now applies only to fully correct batches, so unfinished '
        'programs are not immediately selected for cheap shrinkage. Validation uses new '
        '9x9/17x17 cases. Test data never influences fitness or champion selection.', '',
        'The controlled cohort uses elitism and tournament mutation. The rich cohort uses '
        'behavioural niches (output density, partial progress, gene-length bin, expression '
        'fraction, lifetime and range use), up to one third diversity elites, 10% fresh '
        'random immigrants, and 90% epsilon-lexicase/10% uniform-parent mutation. Epsilon '
        'is 0.02 for partial scores only; complete-solution priority is exact. Mutation '
        'uses 1–6 bounded edits, including block duplication; there is no crossover or '
        'generated Python. Rich training progresses at fixed generation boundaries: '
        '0–39 use sizes 5/9; 40–79 use 9/17; 80+ use 17. A disconnected example appears '
        'every fourth batch. Population, program, state, tick and work ceilings remain hard.', '',
        'Resampling controls evaluate the same number of training genomes/cases per '
        'generation, without inheritance: fresh random programs, or independent '
        '1–6-edit seed perturbations. Frozen controls are the initial validation-selected '
        'champions. Validation attention, actual dispatched work and elapsed CPU cost '
        'can differ and are logged; these are training-sample-matched controls, not '
        'exactly matched CPU-time experiments.', '',
        f"All champions were frozen (SHA256 `{env['champions_sha256']}`) before "
        f"generating {env['fresh_tests']} final cases with {env['unique_tests']} distinct "
        'input/endpoint hashes. Every final case is disjoint from all training, validation '
        'and first-experiment input/endpoint hashes. Deterministic V1 snake/comb shapes '
        'are excluded from this fresh test. Source hashes, dependencies, complete lineage '
        'and fitness logs, output bitmasks and all timing samples are retained.', '',
        '## Continuation and next test', '',
        'Random discovery is not abandoned. JSON checkpoints contain the next population, '
        'exact RNG state, generation, frozen control and validation champion. The '
        '`regulatory_search.search(..., resume=checkpoint)` interface resumes to a higher '
        'absolute generation target; deterministic replay is tested. A continuation '
        'must use a fresh final test set, and its earlier test results must not become '
        'selection feedback. Checkpoints are data, not executable pickles.', '',
        'The rich cohort changes capacity, training schedule and diversity together. '
        'Any improvement motivates separating those factors in matched ablations. '
        'A small set of successes, especially at short source–goal distances or with '
        'all-open masks, does not demonstrate a transferable general solver. More '
        'time/complexity remains a hypothesis to test, not a guarantee.', '',
        '## Visual sample', '',
        'First fresh 17x17 perfect maze in replicate 0. Green = emitted pixels, blue = '
        'source, red = goal. This sample is not selected by correctness.', '',
        f'![Fresh responses]({out.name}/visuals/unseen_17.png)', '',
        '```bash',
        '.venv/bin/python -m maze_evolution.range_study --out results/repeat_ranges '
        f"--seed {config['seed']} --replicates {config['replicates']} "
        f"--control-population {config['control']['population']} --control-generations {config['control']['generations']} "
        f"--rich-population {config['rich']['population']} --rich-generations {config['rich']['generations']} "
        f"--samples {config['samples']} --benchmark-repeats {config['benchmark_repeats']}",
        '```', '']
    out.with_suffix('.md').write_text('\n'.join(lines))


if __name__=='__main__':
    import sys
    report(sys.argv[1])
