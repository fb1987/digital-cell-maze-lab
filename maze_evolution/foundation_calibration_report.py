"""Report verified V12A results; no candidate execution or new selection."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .foundation_calibration import controls, write_json
from .growth import Genome


def run(out):
    out = Path(out)
    summary = json.loads((out / 'summary.json').read_text())
    verification = json.loads((out / 'verification.json').read_text())
    assert verification['all_checks_passed']
    assert hashlib.sha256((out / 'summary.json').read_bytes()).hexdigest() == verification['summary_sha256']
    input_hashes = {}
    def records(path):
        input_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        with gzip.open(path, 'rt') as f:
            for line in f:
                yield json.loads(line)
    partial = Counter()
    horizons = {str(h): Counter() for h in (8, 16, 32, 64)}
    for row in records(out / 'control_matrix.jsonl.gz'):
        if row['kind'] == 'ordinary' and row['key'].endswith('/local/pulse1'):
            name = row['key'].split('/')[0]
            partial[name] = sum(not r['valid'] and r['partial'] > 0 and r['old_partial'] == 0 for r in row['cases'])
        if row['kind'] == 'probe' and row['key'] == 'intact/local/pulse1' and not row['forced']:
            h = horizons[str(row['horizon'])]
            h['observations'] += 1
            h['raster_only_valid'] += row['raster_only_valid']
            h['new_partial_but_no_old_partial'] += (not row['raster_only_valid'] and row['partial'] > 0 and row['old_partial'] == 0)
    states = json.loads((out / 'frozen_selections.json').read_text())
    ancestry = {}
    for key in states:
        damage, rep = key.split('/r')
        base = controls()[damage].genome.digest
        intact = controls()['intact'].genome.digest
        digests = {}
        counts = Counter()
        for row in records(out / f'{damage}_{rep}.lineage.jsonl.gz'):
            digest = Genome.from_dict(row['genome']).digest
            counts['registered'] += 1
            counts['exact_intact_genotypes'] += digest == intact
            if row['parent']:
                counts['mutants_from_original_damaged_genotype'] += digests[row['parent']] == base
            digests[row['id']] = digest
        ancestry[key] = counts
    write_json(out / 'report_analysis.json', dict(scope='Post-hoc saved-record aggregation; no inference or reselection',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), input_sha256=input_hashes,
        normal_partial_credit=partial, intact_ordinary_horizon=horizons, ancestry=ancestry))
    rows = []
    for key, state in states.items():
        a, b = summary['confirmations'][key + '/champion'], summary['confirmations'][key + '/frozen']
        rows.append(f"| {key} | {state['next_generation']} | {state['champion_rank'][1]}/96 | {b['fitness'][1]}/96 | {a['fitness'][1]}/96 | {a['paired_optimal']}/48 |")
    horizon_rows = '\n'.join(f"| {h} | {v['raster_only_valid']}/{v['observations']} | {v['new_partial_but_no_old_partial']} |" for h, v in horizons.items())
    text = f'''# V12A: runtime works, reliable repair remains unestablished

The current runtime/goal-pulse convention passes the intact solver controls. **Only one of nine damaged-program runs passes fresh repair confirmation**, so the preregistered reliability gate is **false**. The long random-origin experiment is deferred while search stability is tested. These are known-solver repair controls, not random-origin discoveries.

The intact program solves all 136 reachable matrix inputs optimally and correctly reports all 8 disconnected targets, under both local/evolved topology and goal pulse off/on. The matrix comprises independent base layouts with correlated rotations/reflections; the four input/topology settings reuse the same inputs. All earlier source/raw results remain unchanged.

| Damage / replicate | Generations | Selected validation shortest | Frozen fresh shortest | Selected fresh shortest | Fresh complete shortest pairs |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Each replicate's fresh confirmation is six independent base layouts, each tested in eight symmetries under two goals. Thus 96 responses and 48 pairs are **not 96 independent layouts**. The three damage types share each replicate's confirmation corpus. The one successful output-register lineage reaches 96/96 shortest outputs and 48/48 complete pairs; its initial frozen control solves 0/96. The other conditions do not establish reliable repair. BFS solves all 288 confirmation responses across the three replicates.

The repair founders contain the exact stated defect and no intact program. Every child is traced to a damaged founder through recorded bounded edits. No solver genotype, repaired or otherwise, may enter any native/fresh random-origin population. Exact genotype identity is not required for functional repair; genotype counts in `report_analysis.json` are descriptive only.

The new ordinary-output score recognizes coherent growth back from the goal that the source-only partial score misses. Counts of invalid ordinary outputs receiving positive new credit while old partial credit is zero, for the local/pulse setting: `{dict(partial)}`. This demonstrates that useful partial traces can be visible to the new score, but the failed repair gate shows that this change alone is insufficient for reliable search.

For the intact program, bounded observations with ordinary stopping give:

| Observation cap | Raster-only legal paths | Incomplete traces with new credit and zero old credit |
|---|---:|---:|
{horizon_rows}

These are diagnostic snapshots, including truncated trajectories. Their raster legality is not a claim of ordinary emission at that cap. Selection uses only the actual normal response under the full bound; forced development never contributes fitness. Full state hashes and ordinary/forced observations at 8/16/32/64 are saved and replayed.

The first two west-gate searches never recreate the exact original intact genotype, although they produce some perfect four-input training batches. This does not exclude equivalent repairs elsewhere. It motivates testing smaller mutations and more orientation coverage within each training batch, rather than assuming extra runtime alone will solve retention.

Main calibration: **{summary['elapsed_seconds']/60:.2f} minutes**, peak process RSS **{summary['max_rss_bytes']/2**20:.1f} MiB**. Matrix: {summary['normal_responses']:,} ordinary responses/{summary['probe_responses']:,} probes; repair search/validation: {summary['repair_responses']:,} ordinary responses; fresh organism confirmation: {summary['holdout_responses']:,} responses. Logical repair work: {summary['repair_work']:,} dispatch-plus-read units. This is calibration cost, separate from a future 60–90-minute random-origin study. It is not an inference-speed comparison.

Independent audit: **{verification['fitness_records']:,} fitness records**, **{verification['mutations']:,} mutation traces**, all selected confirmation outputs, and **{verification['probe_replays']:,} full-state probe replays** pass. Audit time: {verification['elapsed_seconds']:.2f}s, charged separately. All 101 frozen source hashes and 13 prior-manifest hashes match. Original regression run: 128 passes; six focused checks after final additions cover the 129 then-current tests. Those test runs preceded the experiment; the independent audit follows it.

Seed 2026101812; preregistration/final control-score revision `81f74a4`. Every selected model was frozen before fresh confirmation construction. The study excludes 9,376 prior/fixture whole layouts and constructs 6,500 additional whole layouts across 813 base groups; future studies must exclude all **15,876**. Data were generated in advance of repair, including all symmetries, so constructed-layout counts exceed the layouts actually queried in training. Some orbits contain symmetric duplicates.

Next: [V12B repair protocol](../docs/FOUNDATION_REPAIR_V12B.md), comparing one-edit versus 1–6-edit mutation on identical orientation-balanced batches. This uses fresh layouts and preserves V12A's negative outcome. It changes the learning conditions without placing a known solver in a random lineage.

Protocol: [V12A](../docs/FOUNDATION_CALIBRATION_V12A.md). Raw data, checkpoints, source/input hashes and verification: [packet](foundation_calibration/summary.json).
'''
    out.with_suffix('.md').write_text(text)
    print(out.with_suffix('.md'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
