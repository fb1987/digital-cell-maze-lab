"""Summarize the independently verified V12B calibration without new inference."""
import argparse
import hashlib
import json
from pathlib import Path


def run(out):
    out = Path(out)
    s = json.loads((out / 'summary.json').read_text())
    v = json.loads((out / 'verification.json').read_text())
    assert v['all_checks_passed']
    assert hashlib.sha256((out / 'summary.json').read_bytes()).hexdigest() == v['summary_sha256']
    states = json.loads((out / 'frozen_selections.json').read_text())['states']
    rows = []
    for key, state in states.items():
        a, b = (s['confirmations'][key + '/' + role] for role in ('champion', 'frozen'))
        rows.append(f"| {key} | {state['next_generation']} | {state['champion_rank'][1]}/96 | "
                    f"{b['fitness'][1]}/96 | {a['fitness'][1]}/96 | {a['paired_optimal']}/48 |")
    out.with_suffix('.md').write_text(f'''# V12B: reliable bounded repair supports the longer search

The preregistered repair gate passes. The single-edit policy was selected on validation before fresh confirmation: six exact validation repairs versus four for the 1–6-edit policy. On fresh layouts it repairs all three west-return defects, two of three output-register defects, and one of three two-return defects. The intact solver and BFS pass every confirmation input. This establishes bounded repair capability in known-solver descendants, not random-origin discovery.

| Defect / policy / replicate | Generations | Validation shortest | Frozen fresh shortest | Selected fresh shortest | Complete fresh shortest pairs |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Each replicate has six independent base layouts × eight symmetries × two goals: 96 responses and 48 pairs. Policies/defects share that replicate's corpus. The 1–6-edit policy passes two west-return and two two-return replicates, but no output-register replicates. With only three replicates per defect, the experiment does not establish universal superiority of single edits. Both policies received four rotations per training batch, with reflection alternating. Differences from V12A also include those batches and new layouts, so its improvement cannot be attributed solely to mutation size.

The single policy passes the fixed requirement of at least two successful replicates in at least two defect types. Each passing replicate has ≥95% fresh shortest outputs, ≥95% complete shortest pairs, and ≥25 percentage-point gain over its initial frozen control. No threshold was changed after confirmation. Failed conditions remain in the table.

Main cost: {s['elapsed_seconds']/60:.2f} minutes, {s['max_rss_bytes']/2**20:.1f} MiB peak RSS. Search/validation: {s['repair_responses']:,} ordinary responses and {s['repair_work']:,} dispatch-plus-read work units. Fresh candidate/reference-organism confirmation: {s['holdout_responses']:,} responses. Independent audit: {v['elapsed_seconds']:.2f}s, {v['fitness_records']:,} fitness records, {v['mutations']:,} replayed mutation traces, {v['confirmation_replays']:,} selected normal replays, {v['reference_rasters']} BFS rasters, {v['source_hashes']} source and {v['input_hashes']} input hashes. All checks pass. Two focused tests verify single-edit traces, unchanged wide-arm parity, equal response counts and exact checkpoint continuation.

Seed {s['seed']}; preregistration commit `26fdd12`. This study adds {v['layouts']:,} whole layouts across {v['groups']} base groups. Future studies exclude all **{s['resulting_layouts']:,}** whole layouts through V12B, including unused constructed transforms. Full prepared populations, RNG state, founder identity and every mutation are retained.

Proceed with a separately preregistered 75-minute random-origin study using the selected single-edit policy, ordinary-output fitness and orientation coverage. Retain native populations and include fresh random cohorts, matched resampling and frozen controls. The repaired programs are excluded from every random-origin founder pool.

Protocol: [V12B](../docs/FOUNDATION_REPAIR_V12B.md). Raw packet: [summary](foundation_repair/summary.json), [verification](foundation_repair/verification.json).
''')
    print(out.with_suffix('.md'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
