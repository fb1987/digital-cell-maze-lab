"""Post-hoc M19 life histories from saved receipts; no organism executions."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import resource
import shutil
import sqlite3
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from maze_evolution.deep_campaign_store import unpacked

SOURCE = ROOT / 'results/connected_evolution'
OUT = ROOT / 'results/connected_history_diagnosis'
DB = ROOT / 'runs/connected_evolution_m19/campaign.sqlite'
FIELDS = ('pairs', 'corridors', 'ordinary_bases', 'correct_no_path')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(2**20), b''):
            h.update(b)
    return h.hexdigest()


def write(path, obj):
    with open(path, 'x') as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write('\n')


def readz(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


def digest(genome):
    return hashlib.sha256(json.dumps(genome, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def features(rows, meta):
    """Use only queried saved rows, never the broader generated metadata ledger."""
    c = {k: set() for k in (*FIELDS, 'success', 'reachable_success', 'false', 'upstream', 'long8', 'long16')}
    pairs = defaultdict(list)
    ordinary = defaultdict(list)
    terminal = []
    steps = []
    work = 0
    for r in rows:
        cid = r['case']; m = meta[cid]
        terminal.append((r['status'], r['mask']))
        steps.append(r['steps'])
        work += r['reads'] + r['dispatches'] + r['exposure_checks']
        if r['optimal'] or r['no_path']: c['success'].add(cid)
        if r['optimal'] and r['reachable']: c['reachable_success'].add(cid)
        if r['no_path']: c['correct_no_path'].add(cid)
        if r['reachable'] and r['status'] == 'no_path': c['false'].add(cid)
        if m['family'] == 'corridor' and r['optimal']: c['corridors'].add(cid)
        if m['family'] == 'paired': pairs[(m['base'], m['pose'])].append(r)
        if m['family'].startswith('ordinary_'): ordinary[m['base']].append(r)
    for key, rs in pairs.items():
        if len(rs) == 2 and all(r['optimal'] for r in rs):
            c['pairs'].add(key); m = meta[rs[0]['case']]
            if m['graph'] != 'fork' and m['prefix'] >= 2: c['upstream'].add(key)
    for key, rs in ordinary.items():
        if len(rs) == 2 and all(r['optimal'] for r in rs):
            c['ordinary_bases'].add(key); edges = len(meta[rs[0]['case']]['path']) - 1
            if edges >= 8: c['long8'].add(key)
            if edges >= 16: c['long16'].add(key)
    c.update(terminal=tuple(terminal), steps=tuple(steps), work=work,
             queried=tuple(r['case'] for r in rows),
             disconnected_opportunities=sum(not r['reachable'] for r in rows))
    return c


def union_caps(caps):
    return {k: set().union(*(c[k] for c in caps)) for k in
            (*FIELDS, 'success', 'reachable_success', 'false', 'upstream', 'long8', 'long16')}


def compare_caps(child, parent, protected, entry, a0):
    result = dict(parent_available=parent is not None, entry_available=entry is not None,
                  correct_inputs=len(child['success']), false_no_path=len(child['false']),
                  correct_disconnections=len(child['correct_no_path']),
                  disconnected_opportunities=child['disconnected_opportunities'])
    for field in ('reachable_success', 'upstream', 'ordinary_bases', 'long8', 'long16'):
        result['novel_' + field] = len(child[field] - protected[field])
    for label, other in [('parent', parent), ('entry', entry)]:
        if other is None:
            result[label + '_all_correct_retained'] = None
            result[label + '_90pct_skill_retention'] = None
            continue
        assert child['queried'] == other['queried'], 'Cross-panel comparison forbidden'
        result[label + '_correct_denominator'] = len(other['success'])
        result[label + '_all_correct_retained'] = bool(other['success']) and other['success'] <= child['success']
        result[label + '_90pct_skill_retention'] = all(
            not other[k] or len(child[k] & other[k]) / len(other[k]) >= .9 for k in FIELDS)
        result[label + '_new_correct'] = len(child['success'] - other['success'])
        result[label + '_lost_correct'] = len(other['success'] - child['success'])
    result['same_terminal_as_parent'] = child['terminal'] == parent['terminal'] if parent else None
    result['same_steps_as_parent'] = child['steps'] == parent['steps'] if parent else None
    result['work_delta_from_parent'] = child['work'] - parent['work'] if parent else None
    result['work_ratio_to_parent'] = child['work'] / parent['work'] if parent and parent['work'] else None
    result['a0_disconnection_denominator'] = len(a0['correct_no_path'])
    result['a0_disconnection_90pct'] = bool(a0['correct_no_path']) and len(
        child['correct_no_path'] & a0['correct_no_path']) / len(a0['correct_no_path']) >= .9
    result['portfolio_gain_parent_kept'] = bool(result['novel_reachable_success'] and
        result['parent_all_correct_retained'] and not child['false'])
    result['portfolio_gain_parent_and_entry_kept'] = bool(result['portfolio_gain_parent_kept'] and
        result['entry_all_correct_retained'])
    result['upstream_retention_gate'] = bool(result['novel_upstream'] and
        result['parent_90pct_skill_retention'] and result['entry_90pct_skill_retention'] and
        result['a0_disconnection_90pct'] and not child['false'])
    return result


def guard(start):
    assert time.monotonic() - start < 1200, 'Analysis wall guard'
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 8 * 2**30, 'RSS guard'
    assert shutil.disk_usage(OUT).free >= 16 * 2**30, 'Disk floor'
    assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) < 512 * 2**20, 'Output storage guard'


def verify_source():
    seal = json.loads((SOURCE / 'completion.json').read_text())
    for name, h in seal['files'].items(): assert sha(ROOT / name) == h, name
    for name, r in seal['local_records'].items(): assert sha(ROOT / name) == r['sha256'], name
    return dict(completion_sha256=sha(SOURCE / 'completion.json'), journal_sha256=sha(DB),
                sealed_files=len(seal['files']), local_records=len(seal['local_records']))


def metrics_count(r):
    keys = ('novel_reachable_success', 'novel_upstream', 'novel_ordinary_bases', 'novel_long8', 'novel_long16',
            'portfolio_gain_parent_kept', 'portfolio_gain_parent_and_entry_kept', 'upstream_retention_gate')
    return {k: int(bool(r.get(k))) for k in keys}


def aggregate(records):
    groups = defaultdict(Counter)
    for r in records:
        if r['birth_kind'] == 'immigrant': continue
        for key in ('arm:' + r['arm'], 'population:' + r['population'],
                    'arm_cohort:' + r['arm'] + '/' + r['cohort'],
                    'arm_policy:' + r['arm'] + '/' + r['parent_policy']):
            c = groups[key]; c['births'] += 1
            c['direct_children'] += r['children']; c['ever_bred'] += bool(r['children'])
            c['ending_live_or_archive'] += r['ending_live_or_archive']
            if 'first_train' not in r:
                c['no_first_train_observation'] += 1; continue
            x = r['first_train']; c['first_train_observations'] += 1
            c['parent_available'] += x['parent_available']; c['entry_available'] += x['entry_available']
            c['same_terminal_as_parent'] += x['same_terminal_as_parent'] is True
            c['changed_terminal_as_parent'] += x['same_terminal_as_parent'] is False
            c['parent_all_correct_retained'] += x['parent_all_correct_retained'] is True
            c['survived_first_train'] += x['survived']; c['bred_at_first_train'] += bool(x['children_born'])
            c['correct_input_gainers_over_parent'] += bool(x.get('parent_new_correct', 0))
            c['false_no_path_present'] += bool(x['false_no_path'])
            for label, yes in metrics_count(x).items():
                c[label] += yes
                if yes:
                    c[label + '/survived'] += x['survived']
                    c[label + '/ever_bred'] += bool(r['children'])
                    c[label + '/ending'] += r['ending_live_or_archive']
            if x['same_terminal_as_parent']:
                c['same_terminal/extra_work'] += x['work_delta_from_parent'] > 0
    return {k: dict(v) for k, v in sorted(groups.items())}


def main():
    start = time.monotonic(); assert not (OUT / 'analysis.json').exists()
    plan = json.loads((OUT / 'plan.json').read_text()); assert plan['scope'] == 'posthoc_saved_M19_only'
    before = verify_source(); c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True); c.execute('BEGIN')
    initial = unpacked(c.execute('select value from states where stage=-1').fetchone()[0])
    inherited = readz(SOURCE / 'inherited_registry.json.gz')
    registry = {}
    for s in initial:
        for i in s['population']:
            registry[i['id']] = dict(id=i['id'], parent=i['parent'], entry=i['id'], digest=digest(i['genome']),
                phase_depth=0, copy_depth=0, since_copy=None, children=0, arm=s['arm'], population=s['name'])
    records = []; assessment_records = []; samples = []; physical_calls = 0; logical = Counter()
    first_exposed = Counter(); last_generation = None
    for n, kind, g, blob, decision_blob in c.execute('select n,kind,generation,input,decision from stages where complete=1 order by n'):
        guard(start); data = unpacked(blob); decisions = unpacked(decision_blob)
        state_rows = [dict() for _ in initial]
        for result_blob, in c.execute('select result from tasks where stage=? order by n', (n,)):
            receipt = unpacked(result_blob); physical_calls += receipt['calls']
            for e in receipt['entries']:
                f = features(e['rows'], data['metadata'])
                for k, identity in e['aliases']:
                    if identity.startswith('budget_padding/'): continue
                    state_rows[k][identity] = f
                    logical[initial[k]['name'] + '/' + kind] += len(e['rows'])
        for k, event in enumerate(decisions):
            name = event['name']; s = initial[k]; fs = state_rows[k]
            genotype_rows = {registry[i]['digest']: f for i, f in fs.items()}
            protected = union_caps([fs[i['id']] for i in s['protected']])
            a0 = fs['m14/reference/anchor/0']
            survivors = set(event.get('survivors', [])); explorers = set(event.get('explorer_ids', []))
            born_here = Counter(b['item']['parent'] for b in event['births'] if b['events'])
            for identity, f in fs.items():
                r = registry[identity]
                if r.get('birth_kind') != 'mutation': continue
                first = kind == 'train' and 'first_train' not in r
                if not first and kind != 'assessment': continue
                parent = fs.get(r['parent'])
                entry_id = r['entry']; entry = fs.get(entry_id)
                if entry is None: entry = genotype_rows.get(registry[entry_id]['digest'])
                stats = compare_caps(f, parent, protected, entry, a0)
                stats.update(stage=n, generation=g, survived=identity in survivors,
                    children_born=born_here[identity], selected_explorer=identity in explorers)
                if first:
                    assert g == r['birth_generation'], (identity, g)
                    r['first_train'] = stats; first_exposed[r['population']] += 1
                    if int(hashlib.sha256(identity.encode()).hexdigest(), 16) % 64 == 0:
                        samples.append(dict(id=identity, stage=n, population_index=k))
                else:
                    assessment_records.append(dict(id=identity, population=name, arm=s['arm'], cohort=r['cohort'],
                        phase_depth=r['phase_depth'], copy_depth=r['copy_depth'], **stats))
            if kind == 'assessment':
                for i in event['archive']:
                    if i in registry: registry[i]['archive_presentations'] = registry[i].get('archive_presentations', 0) + 1
            for b in event['births']:
                i = b['item']; parent = registry.get(i['parent']); edits = b['events']; is_copy = bool(edits and edits[0]['kind'].startswith('initialized_'))
                assert i['id'] not in registry
                r = dict(id=i['id'], parent=i['parent'], birth_generation=i['birth'], population=name,
                    arm=s['arm'], replicate=s['replicate'], parent_policy=b['parent_policy'],
                    birth_kind='mutation' if edits else 'immigrant', edit_kind=edits[0]['kind'] if edits else 'immigrant',
                    digest=digest(i['genome']), entry=parent['entry'] if parent else i['id'],
                    phase_depth=parent['phase_depth']+1 if parent else 0,
                    copy_depth=(parent['copy_depth'] if parent else 0)+is_copy,
                    since_copy=0 if is_copy else (parent['since_copy']+1 if parent and parent['since_copy'] is not None else None),
                    cohort='direct_copy' if is_copy else 'post_copy_mutation' if parent and parent['copy_depth'] else 'generic_without_copy',
                    children=0, ending_live_or_archive=False)
                if parent: parent['children'] += 1
                registry[r['id']] = r; records.append(r)
        if kind == 'train': last_generation = g + 1
        if n % 32 == 0: print(f'stage {n}: {len(records)} births, {sum(first_exposed.values())} first training exposures', flush=True)
    final = unpacked(c.execute('select value from states where stage=(select max(stage) from states)').fetchone()[0]); c.close()
    for s in final:
        for i in {i['id'] for group in ('population', 'archive') for i in s[group]}:
            registry[i]['ending_live_or_archive'] = True
    for r in records:
        r.setdefault('ending_live_or_archive', False); r['archive_presentations'] = r.get('archive_presentations', 0)
        r.pop('digest')
    mutation_records = [r for r in records if r['birth_kind'] == 'mutation']
    assert len(records) == 9*52*275 and len(mutation_records) == 111375
    assert sum(first_exposed.values()) == 9*45*274
    source_audit = json.loads((SOURCE/'search_audit.json').read_text())
    assert physical_calls == source_audit['charged_calls']
    for name, counts in source_audit['logical_query_counts'].items():
        for kind, count in counts.items(): assert logical[name+'/'+kind] == count
    for name, counts in source_audit['immediate_birth_survival'].items():
        observed = Counter()
        for r in mutation_records:
            if r['population'] != name or 'first_train' not in r: continue
            observed[r['edit_kind']+'/presentations'] += 1
            observed[r['edit_kind']+'/survive_next_train'] += r['first_train']['survived']
        assert dict(observed) == counts, name
    assessment_groups = defaultdict(Counter)
    for r in assessment_records:
        for key in ('arm:'+r['arm'], 'arm_cohort:'+r['arm']+'/'+r['cohort']):
            counter = assessment_groups[key]; counter['presentations'] += 1
            counter['parent_available'] += r['parent_available']; counter['entry_available'] += r['entry_available']
            for label, yes in metrics_count(r).items(): counter[label] += yes
    for name, data in [('birth_lifetimes.jsonl.gz', records), ('assessment_presentations.jsonl.gz', assessment_records)]:
        assert not (OUT/name).exists()
        with gzip.open(OUT/name, 'xt') as f:
            for r in data: f.write(json.dumps(r, sort_keys=True, separators=(',', ':'))+'\n')
    summary = dict(scope='Post-hoc DEVELOPMENT analysis of saved M19 receipts only; no cases/inference/reselection.',
        training=aggregate(records), assessments={k:dict(v) for k,v in assessment_groups.items()},
        source=before, physical_calls_read=physical_calls, births=len(records), mutant_births=len(mutation_records),
        first_training_observations=sum(first_exposed.values()), unobserved_last_round_mutants=405,
        assessment_presentations=len(assessment_records), audit_samples=samples,
        logical_counts=dict(logical), wall_seconds=time.monotonic()-start,
        rss_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        inference_calls=0, new_cases=0, cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
    assert verify_source() == before
    write(OUT/'analysis.json', summary); guard(start)
    print('Complete:',len(records),'births;',sum(first_exposed.values()),'first exposures;',len(assessment_records),'assessment presentations', flush=True)


if __name__ == '__main__':
    main()
