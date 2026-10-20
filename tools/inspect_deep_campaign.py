"""Read-only, same-panel development summaries; performs zero candidate inference."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign import DEFAULT_RUN, ROOT, check_setup
from maze_evolution.deep_campaign_store import unpacked, hashed
from maze_evolution.deep_campaign_search import features
from maze_evolution.exposure_genome import Individual


def summarize(generation):
    check_setup()
    db = sqlite3.connect(f'file:{DEFAULT_RUN / "campaign.sqlite"}?mode=ro', uri=True)
    db.execute('BEGIN')
    stage = db.execute(
        'SELECT n,input,input_hash,decision,chain_hash,state_hash FROM stages '
        'WHERE kind="assessment" AND generation=? AND complete=1', (generation,)).fetchone()
    if not stage:
        raise ValueError('Requested assessment is not complete')
    n, blob, ih, decision, chain, sh = stage
    assert hashed(blob) == ih
    data, decisions = unpacked(blob), unpacked(decision)
    blob, saved_hash = db.execute('SELECT value,hash FROM states WHERE stage=?', (n,)).fetchone()
    assert hashed(blob) == saved_hash == sh
    states = unpacked(blob)
    rows = [{} for _ in states]
    physical_calls = 0
    for blob, rh in db.execute(
            'SELECT result,result_hash FROM tasks WHERE stage=? ORDER BY n', (n,)):
        assert hashed(blob) == rh
        receipt = unpacked(blob)
        physical_calls += receipt['calls']
        for entry in receipt['entries']:
            for island, identity in entry['aliases']:
                assert identity not in rows[island]
                rows[island][identity] = entry['rows']
    db.close()
    output = dict(generation=generation, stage=n, chain=chain, input_hash=ih,
                  physical_calls=physical_calls, development_data=True, new_inference_calls=0,
                  independent_confirmation=False, islands=[])
    for island, (state, decision, rr) in enumerate(zip(states, decisions, rows)):
        reference_ids = [r['id'] for r in state['frozen_references']]
        success = {}
        for identity, records in rr.items():
            f, strata = features(records, data['metadata'])
            success[identity] = f
            assert dict(Counter(strata[k] for k in f)) == decision['capabilities'][identity]['by_stratum']
        union = set().union(*(success[i] for i in reference_ids))
        registry = {r['id']:r for r in state['population']}
        registry.update({a['item']['id']:a['item'] for a in state['coverage_archive']})

        def aggregate_key(identity):
            item = Individual.load(registry[identity])
            return tuple(-x for x in decision['fitness'][identity]), item.genome.digest, identity

        def ordinary_count(identity):
            c = decision['capabilities'][identity]['by_stratum']
            return c.get('ordinary_perfect', 0) + c.get('ordinary_random', 0)

        best_ref = min(reference_ids, key=aggregate_key)
        best_ordinary_ref = min(reference_ids, key=lambda i:(-ordinary_count(i), aggregate_key(i)))

        def describe(identity):
            cap = decision['capabilities'][identity]
            good = [r for r in rr[identity] if r['optimal'] and
                    data['metadata'][r['case']]['family'] in ('ordinary_perfect', 'ordinary_random')]
            novel = success[identity] - union
            return dict(identity=identity, birth=registry[identity]['birth'],
                        parent=registry[identity]['parent'],
                        genome_digest=Individual.load(registry[identity]).genome.digest,
                        genes=len(registry[identity]['genome']['genes']),
                        fitness=decision['fitness'][identity], capabilities=cap,
                        ordinary_shortest=ordinary_count(identity),
                        ordinary_bases=len({data['metadata'][r['case']]['base'] for r in good}),
                        longest_ordinary_edges=max((len(data['metadata'][r['case']]['path'])-1
                                                    for r in good), default=0),
                        gains_vs_aggregate_reference=len(success[identity] - success[best_ref]),
                        losses_vs_aggregate_reference=len(success[best_ref] - success[identity]),
                        novel_vs_reference_union=dict(Counter(strata[k] for k in novel)),
                        novel_feature_keys=sorted(novel),
                        archived=identity in decision['identities'])

        # Some old archive members can be dropped by the assessment. Their raw
        # genomes still exist in the previous 100-round checkpoint.
        missing = set(rr) - set(registry)
        if missing:
            db2 = sqlite3.connect(f'file:{DEFAULT_RUN / "campaign.sqlite"}?mode=ro', uri=True)
            previous = unpacked(db2.execute('SELECT value FROM states WHERE stage=?', (n-1,)).fetchone()[0])
            db2.close()
            registry.update({a['item']['id']:a['item'] for a in previous[island]['coverage_archive']})
        assert set(rr) <= set(registry)
        primary = decision['identities'][0]
        best_ordinary = min(rr, key=lambda i:(-ordinary_count(i), aggregate_key(i)))
        new = sorted((i for i in rr if success[i] - union), key=aggregate_key)
        output['islands'].append(dict(
            island=island, frontier=state['frontier'], promotion_streak=state['promotion_streak'],
            assessed_identities=len(rr), opportunities=decision['strata'],
            primary=describe(primary), aggregate_reference=describe(best_ref),
            best_ordinary=describe(best_ordinary), ordinary_reference=describe(best_ordinary_ref),
            candidates_with_novel_success=len(new),
            novel_candidates=[describe(i) for i in new[:8]],
            total_novel_success_union=dict(Counter(
                strata[k] for k in set().union(*(success[i] for i in rr))-union))))
    return output


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('generation', type=int)
    p.add_argument('--save', action='store_true')
    a = p.parse_args()
    result = summarize(a.generation)
    if a.save:
        path = ROOT / f'results/deep_campaign_run/assessment_{a.generation:05d}.json'
        if path.exists():
            assert json.loads(path.read_text()) == result, 'Never overwrite a differing assessment summary'
        else:
            path.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, indent=2, sort_keys=True))
