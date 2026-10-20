"""Read saved milestone observations and trace chosen ancestry; no inference."""
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign import DEFAULT_RUN, ROOT, check_setup
from maze_evolution.deep_campaign_amendment import check_amendment
from maze_evolution.deep_campaign_store import unpacked, hashed
from maze_evolution.deep_campaign_search import features
from maze_evolution.exposure_genome import Individual
from maze_evolution.foundation_study import read_compressed, compressed_json


def main():
    started = time.monotonic()
    check_setup()
    check_amendment()
    out = ROOT / 'results/deep_campaign_run/milestone'
    assert not (out / 'candidate_assessment.json').exists()
    assert not (out / 'ancestry.json.gz').exists()
    choices = read_compressed(out / 'choices.json.gz')
    db = sqlite3.connect(f'file:{DEFAULT_RUN / "campaign.sqlite"}?mode=ro', uri=True)
    db.execute('BEGIN')
    n, raw, ih, decision, chain = db.execute(
        'SELECT n,input,input_hash,decision,chain_hash FROM stages '
        'WHERE kind="assessment" AND generation=10000 AND complete=1').fetchone()
    assert hashed(raw) == ih and chain == choices['chain']
    data, decisions = unpacked(raw), unpacked(decision)
    rows = [{}, {}, {}]
    for raw, h in db.execute('SELECT result,result_hash FROM tasks WHERE stage=?', (n,)):
        assert hashed(raw) == h
        for entry in unpacked(raw)['entries']:
            for island, identity in entry['aliases']:
                rows[island][identity] = entry['rows']
    records = []
    for island, items in enumerate(choices['items']):
        success, strata = {}, None
        for identity, rr in rows[island].items():
            success[identity], strata = features(rr, data['metadata'])
            assert dict(Counter(strata[k] for k in success[identity])) == decisions[island]['capabilities'][identity]['by_stratum']
        references = [r['id'] for r in choices['frozen_references'][island]]
        union = set().union(*(success[r] for r in references))
        reference = min(references, key=lambda r:tuple(-x for x in decisions[island]['fitness'][r]))
        for rank, archived in enumerate(items):
            item = archived['item']
            identity = item['id']
            cap = decisions[island]['capabilities'][identity]
            good = [r for r in rows[island][identity] if r['optimal'] and
                    data['metadata'][r['case']]['family'] in ('ordinary_perfect', 'ordinary_random')]
            records.append(dict(island=island, role='primary' if rank == 0 else f'complement_{rank}',
                identity=identity, birth=item['birth'], parent=item['parent'],
                genome_digest=Individual.load(item).genome.digest,
                genes=len(item['genome']['genes']), capabilities=cap,
                paired=sum(v for k, v in cap['by_stratum'].items() if k.startswith('paired/')),
                aggregate_reference=reference,
                aggregate_reference_capabilities=decisions[island]['capabilities'][reference],
                gains_vs_aggregate_reference=len(success[identity]-success[reference]),
                losses_vs_aggregate_reference=len(success[reference]-success[identity]),
                novel_vs_reference_union=dict(Counter(strata[k] for k in success[identity]-union)),
                ordinary_successful_bases=len({data['metadata'][r['case']]['base'] for r in good}),
                longest_ordinary_edges=max((len(data['metadata'][r['case']]['path'])-1 for r in good), default=0)))
    packet = dict(generation=10000, chain=chain, development_data=True, new_inference_calls=0,
                  choices_unchanged=True, ordinary_dimensions={'perfect':[11, 11], 'random':[9, 9]},
                  candidates=records)
    (out / 'candidate_assessment.json').write_text(json.dumps(packet, indent=2, sort_keys=True)+'\n')
    initial = unpacked(db.execute('SELECT value FROM states WHERE stage=-1').fetchone()[0])
    roots = {r['id']:r for s in initial for r in s['population']+s['protected']}
    wanted = {r['identity'] for r in records if r['identity'].startswith('deep_v1/')}
    ancestry, counts = {}, Counter()
    for stage, g, raw in db.execute(
            'SELECT n,generation,decision FROM stages WHERE kind="train" AND complete=1 ORDER BY n DESC'):
        events = unpacked(raw)
        for island_event in events:
            for b in island_event['births']:
                counts['births'] += 1
                counts['mutations' if b['mutation'] is not None else 'immigrants'] += 1
                counts['original_births' if g < 8268 else 'a1_births'] += 1
                identity = b['item']['id']
                if identity not in wanted:
                    continue
                assert len(b['parents']) <= 1
                parent = b['parents'][0] if b['parents'] else None
                assert b['item']['parent'] == parent
                ancestry[identity] = dict(parent=parent, birth=b['item']['birth'], stage=stage,
                                          mutation=b['mutation'],
                                          genome_digest=Individual.load(b['item']).genome.digest)
                wanted.remove(identity)
                if parent and parent.startswith('deep_v1/') and parent not in ancestry:
                    wanted.add(parent)
        if g % 1000 == 0:
            print(json.dumps(dict(scanned_back_to=g, selected_ancestry_records=len(ancestry))), flush=True)
    assert not wanted, wanted
    assert counts['births'] == 1560000 and counts['mutations'] == 1350000 and counts['immigrants'] == 210000
    lineages = []
    for r in records:
        identity, trail = r['identity'], []
        while identity in ancestry:
            assert identity not in trail
            trail.append(identity)
            parent = ancestry[identity]['parent']
            if parent is None:
                break
            identity = parent
        if identity not in ancestry:
            assert identity in roots, identity
        lineages.append(dict(identity=r['identity'], root=identity,
                             root_kind='campaign_random_immigrant' if identity in ancestry else 'preserved_initial_individual',
                             campaign_births=len(trail),
                             campaign_mutation_births=sum(ancestry[i]['mutation'] is not None for i in trail),
                             ancestry_from_child_to_root=trail))
    db.close()
    compressed_json(out / 'ancestry.json.gz', dict(records=ancestry, lineages=lineages,
                                                 counts=dict(counts),
                                                 recorded_events_not_full_replay=True))
    (out / 'ancestry_summary.json').write_text(json.dumps(dict(
        lineages=[{k:v for k,v in r.items() if k != 'ancestry_from_child_to_root'} for r in lineages],
        counts=dict(counts), unique_selected_ancestry_events=len(ancestry),
        new_inference_calls=0, wall_seconds=time.monotonic()-started,
        full_selection_mutation_rng_audit='separate durable process'), indent=2)+'\n')


if __name__ == '__main__':
    main()
