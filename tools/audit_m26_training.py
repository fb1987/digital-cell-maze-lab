"""M26: bounded, read-only M25 training audit. Never runs organisms or selection."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import sqlite3
import sys
import time
import zlib
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.m26_saved_metrics import (Panel, FIELDS, append_reason, cohort_flags,
                                     compare, counts, genome_info, novelty, union_profiles)
OUT = ROOT / 'results/evolvability_audit_m26'
OLD = ROOT / 'results/skill_integration'
RUN = ROOT / 'runs/skill_integration_m25'
START = time.monotonic()
CPU = time.process_time()


def unpack(blob):
    return json.loads(zlib.decompress(blob))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def readz(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def guard():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        rss *= 1024
    assert rss < 4 * 1024**3, ('RSS guard', rss)
    assert time.monotonic() - START < 1800, '30 minute wall guard'
    assert shutil.disk_usage(OUT).free >= 16 * 1024**3, 'Disk free floor'
    assert sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()) < 512 * 1024**2, 'Packet storage guard'
    return rss


def verify_old():
    seal = json.loads((OLD / 'completion.json').read_text())
    for p, h in seal['files'].items():
        assert sha(ROOT / p) == h, p
    for p, r in seal['local_records'].items():
        assert (ROOT / p).stat().st_size == r['bytes'] and sha(ROOT / p) == r['sha256'], p
    for kind in ('search', 'final'):
        assert json.loads((OLD / f'{kind}_audit.json').read_text())['status'] == 'PASS'
    return dict(files=len(seal['files']), local_records=len(seal['local_records']),
                completion_sha256=sha(OLD / 'completion.json'),
                search_journal_sha256=sha(RUN / 'campaign.sqlite'))


def db():
    con = sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro', uri=True)
    con.execute('PRAGMA query_only=ON')
    con.execute('BEGIN')
    return con


def candidate(item, event=None, name=None, allocation=None):
    return dict(id=item['id'], parent=item['parent'], root=item['root'], birth=item['birth'],
                phase='M25' if event is not None else 'inherited',
                mutant=bool(event), noop=bool(event and event['before'] == event['after']),
                operator=None if not event else event['kind'],
                opportunity=None if not event else event['opportunity'],
                parent_policy=allocation, population=name, **genome_info(item['genome']),
                first=None, train_exposures=0, survived_first=None,
                children_after_first=0, changed_mutant_children_after_first=0,
                first_offspring_generation=None, last_train_generation=None,
                archive_assessments=0, ever_ordinary8=False, ever_ordinary16=False,
                ever_novel_complete8=False, ever_novel_single8=False,
                ever_novel_complete8_beyond_collective=False,
                novel_complete_bases=[], novel_single_inputs=[],
                max_correct_ordinary_edges=None)


def brief(c, refs, panel, rs, registry, identity, stage, generation):
    novelty_ = novelty(c, refs, panel)
    info = registry[identity]
    parent = rs.get(info['parent'])
    root = rs.get(info['root'])
    return dict(stage=stage, generation=generation, counts=counts(c),
                novel_complete8=len(novelty_['complete']), novel_single8=len(novelty_['single']),
                novel_complete8_beyond_collective=len(novelty_['beyond_collective']),
                parent=compare(c, parent), root=compare(c, root),
                correct_ordinary8_bases=sorted(c['ordinary8']),
                correct_single8_inputs=sorted(c['single8']),
                novel_complete8_bases=sorted(novelty_['complete']),
                novel_single8_inputs=sorted(novelty_['single']))


def summarize(records):
    result = {}
    for name in sorted({r['population'] for r in records.values() if r['phase'] == 'M25'}):
        groups = defaultdict(Counter)
        for r in records.values():
            if r['phase'] != 'M25' or r['population'] != name:
                continue
            group = groups['mutants' if r['mutant'] else 'immigrants']
            group['born'] += 1
            if r['first'] is None:
                group['training_censored'] += 1
                continue
            group['first_exposed'] += 1
            if r['mutant']:
                group['noop' if r['noop'] else 'changed'] += 1
            for flag, yes in cohort_flags(r).items():
                if not yes:
                    continue
                group[flag] += 1 if flag != 'first_exposed' else 0
                if r['survived_first']:
                    group[flag + '/survived_first'] += 1
                if r['children_after_first']:
                    group[flag + '/bred'] += 1
                if r['live_descendants']:
                    group[flag + '/final_live_descendants'] += 1
                if r['final_live']:
                    group[flag + '/final_live_identity'] += 1
                if r['final_archive']:
                    group[flag + '/final_archive_identity'] += 1
            group['survived_first'] += bool(r['survived_first'])
            group['bred'] += bool(r['children_after_first'])
            for f in ('ever_ordinary8', 'ever_ordinary16', 'ever_novel_complete8', 'ever_novel_single8',
                      'ever_novel_complete8_beyond_collective'):
                if r[f]:
                    group[f] += 1
                    if r['children_after_first']:
                        group[f + '/bred'] += 1
                    if r['live_descendants']:
                        group[f + '/final_live_descendants'] += 1
            group['ordinary8_first_visible_later'] += bool(r['ever_ordinary8'] and not r['first']['counts']['ordinary8'])
            group['novel_complete8_first_visible_later'] += bool(r['ever_novel_complete8'] and not r['first']['novel_complete8'])
            group['parent_unavailable'] += r['first']['parent'] is None
            group['root_unavailable'] += r['first']['root'] is None
            if r['first']['counts']['ordinary8']:
                group['ordinary8/append_total_ineligible'] += not r['append_total_eligible']
                group['ordinary8/parent_missing'] += r['first']['parent'] is None
                group['ordinary8/changed'] += r['mutant'] and not r['noop']
                group['ordinary8/offspring'] += r['children_after_first']
                group['ordinary8/changed_mutant_offspring'] += r['changed_mutant_children_after_first']
                group['ordinary8/final_genotype_match'] += r['final_genotype_match']
        result[name] = {k: dict(v) for k, v in groups.items()}
    return result


def main():
    assert not (OUT / 'summary.json').exists() and not (OUT / 'cohorts.jsonl.gz').exists()
    registration = json.loads((OUT / 'registration.json').read_text())
    for p, h in registration['files'].items():
        assert sha(ROOT / p) == h, p
    before = verify_old()
    guard()
    con = db()
    initial_blob, initial_hash = con.execute('SELECT value,hash FROM states WHERE stage=-1').fetchone()
    assert hashlib.sha256(initial_blob).hexdigest() == initial_hash
    initial = unpack(initial_blob)
    registry = {i: candidate(e['item']) for i, e in readz(OLD / 'inherited_registry.json.gz').items()}
    populations = []
    archives = []
    for state in initial:
        populations.append({i['id'] for i in state['population']})
        archives.append({i['id'] for i in state['archive']})
        for group in ('population', 'archive', 'protected', 'frozen', 'nominees'):
            for item in state[group]:
                assert item['id'] in registry and registry[item['id']]['digest'] == genome_info(item['genome'])['digest']
    final = readz(OLD / 'final_states.json.gz')
    names = [s['name'] for s in initial]
    stage_log = []
    append = defaultdict(Counter)
    population_stats = defaultdict(Counter)
    last_chain = initial_hash
    physical_calls = 0
    receipt_count = 0
    hits_count = 0
    all_hit_bases, all_hit_singles = set(), set()
    ordinary_details = {}
    nominal = Counter()
    hitpath = OUT / 'novel_hits.jsonl.gz'
    assert not hitpath.exists()
    with gzip.open(hitpath, 'xt', compresslevel=6) as hitfile:
        for n, kind, generation, inp, input_hash, dec, chain, state_hash, complete in con.execute(
                'SELECT n,kind,generation,input,input_hash,decision,chain_hash,state_hash,complete FROM stages ORDER BY n'):
            guard()
            assert complete == 1 and hashlib.sha256(inp).hexdigest() == input_hash
            decisions = unpack(dec)
            assert [d['name'] for d in decisions] == names
            results = []
            hashes = []
            for status, blob, rhash in con.execute('SELECT status,result,result_hash FROM tasks WHERE stage=? ORDER BY n', (n,)):
                assert status == 'done' and hashlib.sha256(blob).hexdigest() == rhash
                result = unpack(blob)
                physical_calls += result['calls']
                receipt_count += 1
                hashes.append(rhash)
                if kind == 'train':
                    results.extend(result['entries'])
            payload = json.dumps([last_chain, input_hash, hashes, state_hash, hashlib.sha256(dec).hexdigest()], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            assert hashlib.sha256(zlib.compress(payload, 1)).hexdigest() == chain
            last_chain = chain
            stored = con.execute('SELECT value,hash FROM states WHERE stage=?', (n,)).fetchone()
            if stored:
                assert hashlib.sha256(stored[0]).hexdigest() == stored[1] == state_hash
            if kind == 'assessment':
                for k, d in enumerate(decisions):
                    archives[k] = set(d['archive'])
                    for identity in archives[k]:
                        registry[identity]['archive_assessments'] += 1
                continue
            data = unpack(inp)
            panels = [Panel(data['metadata'], data['queries'][s['curriculum']], data['common_queries'],
                            data['persistent_queries'][s['curriculum']]) for s in initial]
            profiles = [{} for _ in names]
            for e in results:
                for k, identity in e['aliases']:
                    assert identity in populations[k] and identity not in profiles[k]
                    profiles[k][identity] = panels[k].profile(e['rows'])
            for k, (state, d, rs, panel) in enumerate(zip(initial, decisions, profiles, panels)):
                assert set(rs) == populations[k] and len(rs) == 96
                name = state['name']
                nominal[name] += len(rs) * len(panel.queries)
                refs = union_profiles([rs[i['id']] for i in state['protected']])
                survivors = set(d['survivors'])
                assert len(survivors) == 44 and survivors <= populations[k]
                stats = population_stats[name]
                stats['train_stages'] += 1
                for b, cs in panel.bases.items():
                    m = panel.meta[cs[0]]
                    detail = dict(base=b, family=m['family'], edges=panel.lengths[b], size=m['size'], source=panel.source[b])
                    assert b not in ordinary_details or ordinary_details[b] == detail
                    ordinary_details[b] = detail
                for b in panel.target:
                    stats['target_base_presentations/' + panel.source[b]] += 1
                    stats['protected_complete8_presentations/' + panel.source[b]] += b in refs['ordinary8']
                for identity, c in rs.items():
                    r = registry[identity]
                    stats['population_presentations'] += 1
                    stats['ordinary8_presentations'] += bool(c['ordinary8'])
                    stats['ordinary16_presentations'] += bool(c['ordinary16'])
                    stats['novel_complete8_presentations'] += bool(novelty(c, refs, panel)['complete'])
                    if r['phase'] != 'M25':
                        continue
                    assert r['population'] == name and r['birth'] <= generation
                    if r['first'] is None:
                        assert r['birth'] == generation, (identity, generation)
                        r['first'] = brief(c, refs, panel, rs, registry, identity, n, generation)
                        r['survived_first'] = identity in survivors
                    r['train_exposures'] += 1
                    r['last_train_generation'] = generation
                    r['ever_ordinary8'] |= bool(c['ordinary8'])
                    r['ever_ordinary16'] |= bool(c['ordinary16'])
                    max_edges = max((panel.lengths[b] for b in c['ordinary']), default=None)
                    if max_edges is not None:
                        r['max_correct_ordinary_edges'] = max(max_edges, r['max_correct_ordinary_edges'] or 0)
                    novel = novelty(c, refs, panel)
                    r['ever_novel_complete8'] |= bool(novel['complete'])
                    r['ever_novel_single8'] |= bool(novel['single'])
                    r['ever_novel_complete8_beyond_collective'] |= bool(novel['beyond_collective'])
                    if novel['complete'] or novel['single']:
                        r['novel_complete_bases'] = sorted(set(r['novel_complete_bases']) | novel['complete'])
                        r['novel_single_inputs'] = sorted(set(r['novel_single_inputs']) | novel['single'])
                        all_hit_bases |= novel['complete']
                        all_hit_singles |= novel['single']
                        hit = dict(id=identity, population=name, stage=n, generation=generation,
                                   first_training_exposure=r['birth'] == generation,
                                   survived=identity in survivors, counts=counts(c),
                                   novel_complete8=sorted(novel['complete']), novel_single8=sorted(novel['single']),
                                   novel_complete8_beyond_collective=sorted(novel['beyond_collective']),
                                   parent=compare(c, rs.get(r['parent'])), root=compare(c, rs.get(r['root'])))
                        hitfile.write(json.dumps(hit, sort_keys=True) + '\n')
                        hits_count += 1
                for b in d['births']:
                    item = b['item']
                    identity, parent = item['id'], item['parent']
                    assert identity not in registry and item['birth'] == generation + 1
                    assert len(b['events']) == (1 if parent else 0)
                    edit = b['events'][0] if parent else None
                    if parent:
                        assert parent in survivors
                        p = registry[parent]
                        if p['first'] is not None:
                            p['children_after_first'] += 1
                            p['changed_mutant_children_after_first'] += edit['before'] != edit['after']
                            if p['first_offspring_generation'] is None:
                                p['first_offspring_generation'] = generation + 1
                        if edit['opportunity'] == 0:
                            reason = append_reason(p['instructions'], edit['activation_index'])
                            assert (reason != 'admitted') == (edit['kind'] == 'bounded_noop')
                            append[name][reason] += 1
                            for label, yes in dict(parent_ordinary8=bool(rs[parent]['ordinary8']),
                                                   parent_ordinary16=bool(rs[parent]['ordinary16']),
                                                   parent_novel_complete8=bool(novelty(rs[parent], refs, panel)['complete']),
                                                   parent_novel_single8=bool(novelty(rs[parent], refs, panel)['single'])).items():
                                if yes:
                                    append[name][label + '/' + reason] += 1
                    registry[identity] = candidate(item, edit if parent else {}, name, b['parent_policy'])
                    registry[identity]['phase_depth'] = (registry[parent].get('phase_depth', 0) + 1) if parent else 0
                    if parent:
                        assert edit['after'] == registry[identity]['digest'] and edit['before'] == registry[parent]['digest']
                populations[k] = survivors | {b['item']['id'] for b in d['births']}
                assert len(populations[k]) == 96
            stage_log.append(dict(stage=n, generation=generation, newly_born=312,
                                  physical_entries=len(results), nominal_queries=6 * 96 * 120))
            if len(stage_log) % 64 == 0:
                print(json.dumps(dict(train_stages=len(stage_log), generation=generation, novel_hit_presentations=hits_count,
                                      wall_seconds=round(time.monotonic() - START, 2))), flush=True)
    con.close()
    for k, state in enumerate(final):
        assert populations[k] == {i['id'] for i in state['population']}
        assert archives[k] == {i['id'] for i in state['archive']}
    live = set().union(*populations)
    archived = set().union(*archives)
    genotypes = [{registry[i]['digest'] for i in populations[k] | archives[k]} for k in range(6)]
    live_desc = Counter({i: 1 for i in live})
    for r in reversed(list(registry.values())):
        if r['phase'] == 'M25' and r['parent']:
            live_desc[r['parent']] += live_desc[r['id']]
    for r in registry.values():
        if r['phase'] != 'M25':
            continue
        identity = r['id']
        k = names.index(r['population'])
        r.update(final_live=identity in live, final_archive=identity in archived,
                 live_descendants=live_desc[identity] - int(identity in live),
                 final_genotype_match=r['digest'] in genotypes[k])
    phases = {i:r for i,r in registry.items() if r['phase'] == 'M25'}
    assert len(phases) == 99528
    assert sum(r['mutant'] for r in phases.values()) == 86130
    assert sum(r['mutant'] and r['first'] is None for r in phases.values()) == 270
    assert sum(not r['mutant'] and r['first'] is None for r in phases.values()) == 42
    old_headroom = json.loads((OLD / 'append_headroom_diagnostics.json').read_text())
    for name, old in old_headroom['reason_counts'].items():
        assert {k:v for k,v in append[name].items() if '/' not in k} == old
    summary = dict(scope='Posthoc saved DEVELOPMENT records only; zero inference, new cases, evolution or reselection.',
                   by_population=summarize(phases), population_exposures={k:dict(v) for k,v in population_stats.items()},
                   append_opportunities={k:dict(v) for k,v in append.items()},
                   novel_hit_presentations=hits_count, novel_complete8_distinct_bases=len(all_hit_bases),
                   novel_single8_distinct_inputs=len(all_hit_singles), train_stages=len(stage_log),
                   nominal_training_queries=dict(nominal), search_physical_calls_verified=physical_calls,
                   receipt_hashes_verified=receipt_count, chain=last_chain,
                   input_integrity_before=before, guards=dict(wall_seconds=1800, rss_bytes=4*1024**3,
                                                            output_bytes=512*1024**2, disk_free_floor_bytes=16*1024**3))
    assert physical_calls == 24388480 and receipt_count == 22188 and len(stage_log) == 319
    assert last_chain == '76d4f19003b0466be33d6cd065ea9c6c9d0d0ef4e88cfd3cefb175a227357d94'
    with gzip.open(OUT / 'cohorts.jsonl.gz', 'xt', compresslevel=6) as f:
        for r in phases.values():
            f.write(json.dumps(r, sort_keys=True) + '\n')
    write(OUT / 'ordinary_units.json', ordinary_details)
    write(OUT / 'stages.json', stage_log)
    after = verify_old()
    assert before == after
    summary['input_integrity_after'] = after
    summary['analysis_cost'] = dict(wall_seconds=time.monotonic() - START, cpu_seconds=time.process_time() - CPU,
                                    peak_rss_bytes=guard(), inference_calls=0, generated_layouts=0)
    write(OUT / 'summary.json', summary)
    print(json.dumps(dict(status='COMPLETE', costs=summary['analysis_cost'], novel_hits=hits_count)), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        import traceback
        failure = OUT / ('failure_' + time.strftime('%Y%m%d_%H%M%S') + '.json')
        write(failure, dict(traceback=traceback.format_exc(), wall_seconds=time.monotonic() - START,
                            analysis_source_sha256=sha(Path(__file__))))
        raise
