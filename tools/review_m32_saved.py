"""Additive report evidence from closed M32 records; no candidate execution."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_evolution_m32 import *


def main():
    check()
    target = OUT/'interpretation_evidence.json'
    assert not target.exists()
    d, rows, _, _, _ = load_finite('final')
    caps = caps_rows(rows, d)
    s = readz(OUT/'sources.json.gz')
    choices = readz(OUT/'choices.json.gz')['choices']
    models = {i['id']: i['model'] for i in s['items']}
    meta = {cid: d['metadata'][cid] for cid in d['queries']['all']}
    ordinary = {m['base']: m for m in meta.values()
                if m['family'] in ('ordinary_perfect', 'ordinary_random')}
    evidence = []
    for c in choices:
        i = c['item']; identity = i['id']; cap = caps[identity]
        _, correct = controlled(cap, d)
        _, entry_correct = controlled(caps[i['entry']], d)
        complete = [ordinary[b] for b in cap['ordinary_bases']]
        no_path_failures = Counter(r['status'] for r in rows[identity]
                                   if not r['reachable'] and not r['no_path'])
        evidence.append(dict(population=c['population'], role=c['role'], id=identity,
            controlled_correct=len(correct), controlled_entry_retained=len(correct & entry_correct),
            controlled_entry_gained=len(correct-entry_correct), controlled_entry_lost=len(entry_correct-correct),
            controlled_correct_by_edges=dict(Counter(len(meta[x]['path'])-1 for x in correct)),
            complete_ordinary_by_family=dict(Counter(m['family'] for m in complete)),
            complete_ordinary8=sum(len(m['path'])-1 >= 8 for m in complete),
            complete_ordinary16=sum(len(m['path'])-1 >= 16 for m in complete),
            maximum_complete_ordinary_edges=max((len(m['path'])-1 for m in complete), default=None),
            disconnected_failure_statuses=dict(no_path_failures),
            historical_exact_genotype_matches=[x for x in s['historical_references']
                if models[x] == i['model']]))
    budgets = {}
    for name in ('source', 'search', 'final'):
        j = readonly(name)
        groups = defaultdict(Counter)
        generations = defaultdict(list)
        for n, blob in j.db.execute('SELECT n,input FROM stages WHERE complete=1 ORDER BY n'):
            data = unpacked(blob); kind = data.get('kind', name)
            group = groups[kind]; group['stages'] += 1
            if 'generation' in data: generations[kind].append(data['generation'])
            for _, spec, status in j.tasks(n):
                assert status == 'done'
                for e in spec:
                    group['physical_calls'] += len(e['queries'])
                    group['logical_alias_queries'] += len(e['queries'])*len(e['aliases'])
        assert sum(x['physical_calls'] for x in groups.values()) == j.get('usage')['calls']
        budgets[name] = dict(groups={k:dict(v) for k,v in groups.items()}, generations=dict(generations))
        j.close()
    saved = json.loads((OUT/'saved_diagnostics.json').read_text())
    allocation = saved['allocation']
    birth_totals = {key:sum(a[key] for a in allocation.values())
                    for key in ('mutants', 'immigrants', 'changed', 'noops')}
    writej(target, dict(status='PASS', no_new_inference=True,
        no_new_cases_or_genomes=True, same_panel_role_evidence=evidence,
        budgets=budgets, birth_totals=birth_totals,
        nominal_live_training_queries_per_population=62*96*96,
        nominal_live_training_queries_all_populations=62*96*96*6,
        nominal_live_assessment_queries_per_population=5*96*811,
        nominal_live_assessment_queries_all_populations=5*96*811*6,
        budget_note='Live-slot counts before physical deduplication. Logical task totals additionally include archives, frozen references, entry and assessment parent aliases, with globally shared aliases counted once. Physical CPU cannot be uniquely allocated among arms sharing evaluated genotypes.',
        postprocessor_failure='saved_analysis_failure_001 retained; queried-only counterpart filtering corrected the unregistered helper before its first successful saved output. Science and raw summary unchanged.'))
    print('Additive saved-record review PASS', flush=True)


if __name__ == '__main__':
    main()
