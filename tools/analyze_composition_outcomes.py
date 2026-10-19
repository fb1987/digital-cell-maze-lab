"""Descriptive analysis of sealed V12S data; performs no candidate inference."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collections import Counter
from maze_evolution.composition_study import OUT, read_compressed, lines, write_json


def main():
    choices = read_compressed(OUT / 'choices.json.gz')
    states = read_compressed(OUT / 'next_states.json.gz')
    pools = read_compressed(OUT / 'pools.json.gz')
    metadata = read_compressed(OUT / 'confirmation/metadata.json.gz')
    summaries = read_compressed(OUT / 'confirmation/metrics.json.gz')
    founders = {i['id']: i for p in pools.values() for i in p['items']}
    edges, sexual, birth_generation, counts = {}, set(), {}, {}
    direct_retained = set(); retained_births = set(); birth_kind = {}
    # The authoritative two-parent graph is reconstructed from the birth log.
    # Historical founders are roots of THIS comparison, not claimed origin roots.
    for event in lines(OUT / 'reproduction.jsonl.gz'):
        key = event['key']; c = counts.setdefault(key, Counter())
        direct_retained.update(set(event['elite']) & sexual)
        retained_births.update(i for i in event['elite'] if i in edges)
        for b in event['births']:
            identity = b['item']['id']
            assert identity not in edges
            edges[identity] = b['parents']
            birth_generation[identity] = event['generation'] + 1
            birth_kind[identity] = 'splice' if b['crossover'] is not None else ('mutation' if b['mutation'] is not None else 'random')
            c['births'] += 1
            c['mutations'] += b['mutation'] is not None
            c['attempts'] += b['mating'] is not None
            if b['crossover'] is not None:
                sexual.add(identity); c['splices'] += 1
                nr=len(b['crossover']['recipient_rows']); nd=len(b['crossover']['donor_rows'])
                c[f'donor_segment_{nd}_rows']+=1
                c['multi_instruction_donor_segments']+=nd>1
                c['length_changing_splices']+=nr!=nd
                gains = b['mating']['gains']
                c['positive_pair_donor_gain'] += gains[0] > 0
                c['positive_shortest_donor_gain'] += gains[1] > 0
                c['any_positive_donor_gain'] += any(v > 0 for v in gains)
                c['partial_only_donor_gain'] += not any(v > 0 for v in gains[:3]) and gains[3] > 0
    for identity in direct_retained:
        counts[identity.rsplit('/i', 1)[0]]['direct_spliced_children_retained_at_least_once'] += 1
    for identity in retained_births:
        counts[identity.rsplit('/i', 1)[0]][birth_kind[identity]+'_children_retained_at_least_once'] += 1

    def ancestry(identity):
        pending = [identity]; seen = set(); roots = set(); cross = set()
        while pending:
            node = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in sexual:
                cross.add(node)
            parents = edges.get(node, [])
            if parents:
                pending.extend(parents)
            else:
                roots.add(node)
        return dict(nodes=len(seen), distinct_splice_events=len(cross),
                    roots=sorted(roots), direct_spliced_child=identity in sexual,
                    study_birth_generation=birth_generation.get(identity, 0),
                    initial_founder_roots=sum(r in founders for r in roots),
                    immigrant_roots=sum(r not in founders for r in roots))

    lineage = {a: ancestry(i['id']) for a, i in choices['items'].items() if not a.startswith('anchor/')}
    tested_id={raw['id']:choices['aliases'][a] for a,raw in choices['items'].items()}
    for alias,lin in lineage.items():
        roots=lin['roots'];available=[r for r in roots if r in tested_id]
        union=set()
        for r in available:
            union.update(map(tuple,summaries[tested_id[r]]['positive_keys']))
        child=set(map(tuple,summaries[choices['aliases'][alias]]['positive_keys']))
        lin['root_comparison']=dict(final_tested_roots=available,
            all_roots_tested=len(available)==len(roots),
            positive_pairs_beyond_tested_root_union=len(child-union),
            tested_root_positive_union=len(union))
    for key, state in states.items():
        c = counts[key]
        c['next_population_with_splice_ancestry'] = sum(bool(ancestry(i['id'])['distinct_splice_events']) for i in state['population'])
        c['last_generation_unevaluated_births'] = sum(birth_generation.get(i['id']) == state['generation'] for i in state['population'])

    metrics = {}
    for event in lines(OUT / 'confirmation/responses.jsonl.gz'):
        pid = event['key']; by = {}
        for r in event['rows']:
            m = metadata[r['case']]; family = m['family']
            group = by.setdefault(family, Counter())
            group['inputs'] += 1
            group['reachable'] += r['reachable']
            group['shortest'] += r['optimal']
            group['legal'] += r['valid']
            group['correct_no_path'] += r['no_path']
            group['false_no_path'] += r['reachable'] and r['status'] == 'no_path'
        metrics[pid] = dict(by_family=by, positive=summaries[pid]['positive'],
                            positive_full_groups=summaries[pid]['positive_full_groups'],
                            stress_positive=summaries[pid]['stress_positive'])
    assert set(metrics) == set(choices['models'])
    cost = {}
    for e in lines(OUT / 'initial.jsonl.gz'):
        # Each founder evaluation was physically run once, then shared by three arms.
        for arm in ('mutation', 'recombination', 'resample'):
            c = cost.setdefault(e['key']+'/'+arm, Counter())
            c['logical_initial_calls'] += len(e['rows'])
            c['shared_initial_seconds'] += e['seconds']
            c['shared_initial_work'] += e['work']
    behavior_checked=set()
    for path in sorted((OUT / 'train').glob('g*/responses.jsonl.gz')):
        training={}
        for e in lines(path):
            c = cost[e['key']]
            c[e['stage']+'_calls'] += len(e['rows'])
            c[e['stage']+'_seconds'] += e['seconds']
            c[e['stage']+'_work'] += e['work']
            if e['stage']=='train':
                training.setdefault(e['key'],{})[e['id']]=[(r['case'],r['mask'],r['status']) for r in e['rows']]
        for key, population in training.items():
            c=counts[key]
            for identity, behavior in population.items():
                if identity not in sexual or identity in behavior_checked:continue
                behavior_checked.add(identity);c['direct_spliced_children_evaluated']+=1
                recipient,donor=edges[identity]
                available=[p for p in (recipient,donor) if p in population]
                c['first_evaluation_with_any_parent']+=bool(available)
                c['first_evaluation_with_both_parents']+=len(available)==2
                if recipient in population:
                    c['first_evaluation_recipient_comparable']+=1
                    c['first_evaluation_changed_from_recipient']+=behavior!=population[recipient]
                if donor in population:
                    c['first_evaluation_donor_comparable']+=1
                    c['first_evaluation_changed_from_donor']+=behavior!=population[donor]
                if len(available)==2:
                    c['first_evaluation_changed_from_both']+=all(behavior!=population[p] for p in available)
    write_json(OUT / 'descriptive_outcomes.json', dict(
        candidate_calls=0,
        interpretation='Post-hoc saved-data description. A splice ancestor or a better donor does not prove functional composition; every splice is followed by a mutation.',
        behavior_comparison='Each direct spliced child is counted at its first training evaluation. Parent comparison is possible only when the parent was retained on that same batch; this is a selected descriptive subset, not a causal crossover experiment.',
        reproduction=counts, selected_lineages=lineage, models=metrics,
        search_cost_by_condition=cost,
        selection_aliases=choices['aliases']))


if __name__ == '__main__':
    main()
