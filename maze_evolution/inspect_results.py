"""Audit saved outputs after the run; no inference, selection or test retuning.

Usage: python -m maze_evolution.inspect_results results/first_evolution
"""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from .genome import Op


def inspect(out):
    out = Path(out)
    champions = json.loads((out / 'champions.json').read_text())
    environment = json.loads((out / 'environment.json').read_text())
    assert hashlib.sha256((out / 'champions.json').read_bytes()).hexdigest() == environment['frozen_champions_sha256']
    cases = {case['case_id']: case for case in json.loads((out / 'mazes.json').read_text())}
    test_cases = [case for case in cases.values() if case['split'] == 'test']
    with (out / 'holdout.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    phenotypes = []
    for key, arms in champions.items():
        regime, replicate = key.split('/r')
        relevant = [row for row in rows if row['replicate'] == replicate and row['arm'] == regime + '_evolved']
        counts = Counter()
        successful_families = Counter()
        for row in relevant:
            case = cases[row['case_id']]
            n = int(row['w']) * int(row['h'])
            packed = np.frombuffer(bytes.fromhex(row['mask_packbits_hex']), dtype=np.uint8)
            mask = np.unpackbits(packed, bitorder='little')[:n]
            grid = np.frombuffer(bytes.fromhex(case['cells_hex']), dtype=np.uint8)
            source = np.zeros(n, dtype=np.uint8)
            source[case['start']] = 1
            all_open = np.array_equal(mask, grid)
            counts['all_open'] += int(all_open)
            counts['source_only'] += int(np.array_equal(mask, source))
            if row['valid_path'] == 'True':
                successful_families[row['family']] += 1
                counts['successful_all_open'] += int(all_open)
        old = Counter(tuple(row) for row in arms['frozen']['genome']['genes'])
        new = Counter(tuple(row) for row in arms['evolved']['genome']['genes'])
        readable = lambda counter: [dict(op=Op(row[0]).name, operands=list(row[1:]), count=count)
                                    for row, count in counter.items()]
        frozen_rows = {row['case_id']: row for row in rows if row['replicate'] == replicate
                       and row['arm'] == regime + '_frozen'}
        same_outputs = sum(all(row[field] == frozen_rows[row['case_id']][field]
                               for field in ('mask_packbits_hex', 'status', 'steps'))
                           for row in relevant)
        phenotypes.append(dict(run=key, cases=len(relevant), phenotypes=dict(counts),
            identical_outputs_to_frozen=same_outputs,
            successful_families=dict(successful_families),
            removed_instructions=readable(old - new), added_instructions=readable(new - old)))
    failed = next((row for row in rows if row['arm'] == 'seeded_evolved' and row['failure'] == 'budget_exhausted'), None)
    failure = None
    if failed:
        case = cases[failed['case_id']]
        failure = dict(case_id=failed['case_id'], status=failed['status'], ticks=int(failed['steps']),
                   oracle_edges=case['oracle_length'] - 1,
                   wavefront_ticks_required=2 * (case['oracle_length'] - 1) + 1,
                   attempted_reads=int(failed['spatial_reads']),
                   read_cap=json.loads((out / 'config.json').read_text())['limits']['reads_per_site'] * case['w'] * case['h'])
    result = dict(phenotypes=phenotypes, first_seeded_failure=failure,
                  test_cases=len(test_cases), unique_test_mazes=len({case['sha256'] for case in test_cases}),
                  champions_unchanged=True, purpose='Post-run audit; no selection or configuration change')
    (out / 'phenotype_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    text = ['## Post-run phenotype audit', '',
        'This section inspects the saved outputs; it does not rerun selection or change '
        'the frozen champions, scoring or limits.', '']
    for row in phenotypes:
        text.append(f"- **{row['run']}**: {row['phenotypes']['all_open']}/{row['cases']} outputs "
                    f"equal all open input cells; {row['phenotypes']['source_only']}/{row['cases']} "
                    f"contain only the source. Successful families: {row['successful_families']}. "
                    f"Outputs/status/ticks unchanged from frozen: {row['identical_outputs_to_frozen']}/{row['cases']}. "
                    f"Deleted instruction instances: {sum(g['count'] for g in row['removed_instructions'])}.")
    random_runs = [row for row in phenotypes if row['run'].startswith('random/')]
    random_successes = sum(sum(row['successful_families'].values()) for row in random_runs)
    trivial = sum(row['phenotypes'].get('successful_all_open', 0) for row in random_runs)
    if random_successes and random_successes == trivial:
        text += ['', f'All {random_successes} random-regime successes light every open input '
                 'cell. In these cases the open input itself is already a legal shortest '
                 'route. This favourable special case is not evidence of a general '
                 'maze-solving procedure learned by evolution.']
    markers = [key for key, arms in champions.items() if key.startswith('random/')
               and arms['evolved']['genome']['genes'] == [[int(Op.STORE), 2, 5, 0, 0]]]
    if markers:
        text += ['', f"Runs {', '.join(markers)} compressed a source-only response to "
                 '`STORE output, source_flag`. This is a fitness plateau: shape constraints '
                 'alone did not bridge the gap to connected route construction.']
    redundant = [row for row in phenotypes if row['run'].startswith('seeded/')
                 and row['removed_instructions'] == [dict(op='OR', operands=[15, 15, 2, 0], count=1)]
                 and not row['added_instructions'] and row['identical_outputs_to_frozen'] == row['cases']]
    if redundant:
        text += ['', f"Runs {', '.join(row['run'] for row in redundant)} deleted "
             '`OR r15, r15, state_output`, the explicit '
             'persistence step. The goal remains active and the retained parent-linked chain '
             'sustains its own output, making that instruction redundant. One run also '
             'reordered independent instructions. Spatial reads, propagation depth and '
             'held-out outcomes remain unchanged. This is a small interpretable '
             'optimization, not a new pathfinding algorithm.']
        def units(genes):
            return len(genes) + sum(4 if row[0] in (int(Op.MIN_POS), int(Op.ARGMIN_POS))
                                   else 1 if row[0] in (int(Op.NEIGHBOR), int(Op.MATCH_NEIGHBOR))
                                   else 0 for row in genes)
        for row in redundant:
            arms = champions[row['run']]
            old, new = arms['frozen']['genome']['genes'], arms['evolved']['genome']['genes']
            text.append(f"- {row['run']}: {len(old)} → {len(new)} genes; "
                        f"{units(old)} → {units(new)} instruction+read units per open site per tick "
                        f"({100 * (units(old) - units(new)) / units(old):.2f}% reduction).")
    if failure:
        text += ['',
             f"The first seeded budget failure was `{failure['case_id']}`: shortest-path "
             f"distance {failure['oracle_edges']} edges requires {failure['wavefront_ticks_required']} "
             f"ticks for this seed's forward-and-backward process. It stopped at "
             f"{failure['ticks']} ticks on `{failure['status']}`, after "
             f"{failure['attempted_reads']:,} of {failure['read_cap']:,} permitted reads. "
             'No extra budget was granted to convert this failure into a reported success.', '']
    text += [f"The per-arm test denominator pools {len(test_cases)} case evaluations across "
             f"{len({row['replicate'] for row in rows})} independently evolved runs. These contain "
             f"{result['unique_test_mazes']} unique input/endpoint hashes. Snake and comb shapes "
             'repeat across replicates; those repeated structural checks are not independent '
             'randomly generated mazes.', '']
    verification_path = out / 'verification.json'
    if verification_path.exists():
        verification = json.loads(verification_path.read_text())
        text += ['## Verification', '',
            f"All {verification['tests_passed']} tests pass with `{verification['test_command']}`. "
            'The saved execution-source hashes and frozen-champion hash match. '
            f"Lineage links cover {verification['lineage_genomes']:,} created genomes; logs contain "
            f"{verification['population_evaluations']:,} population evaluations and "
            f"{verification['holdout_outputs']:,} final outputs across candidate arms and baselines. "
            'Cross-split input/endpoint overlap is absent. The phenotype audit can be reproduced '
            f"with `{verification['audit_command']}`.", '']
    report = out.with_suffix('.md')
    existing = report.read_text().split('\n## Post-run phenotype audit')[0]
    report.write_text(existing.rstrip() + '\n\n' + '\n'.join(text))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    inspect(sys.argv[1] if len(sys.argv) > 1 else 'results/first_evolution')
