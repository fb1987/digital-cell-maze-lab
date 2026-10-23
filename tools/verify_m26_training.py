"""Independent saved-row/grouping and identity-lifecycle verification for M26.

Does not import the analysis, its metrics, the VM, selection or maze generators.
Rechecks every first exposure and every later novel hit against original receipts.
It relies on the original PASS native-output/grade audits; it is not a second VM.
"""
import gzip
import hashlib
import json
from pathlib import Path
import resource
import shutil
import sqlite3
import sys
import time
import zlib
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/evolvability_audit_m26'
RUN = ROOT / 'runs/skill_integration_m25'
OLD = ROOT / 'results/skill_integration'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304), b''):
            h.update(b)
    return h.hexdigest()


def un(blob):
    return json.loads(zlib.decompress(blob))


def readz(p):
    with gzip.open(p, 'rt') as f:
        return json.load(f)


def classify(rows, metadata):
    good = {r['case'] for r in rows if r['optimal']}
    groups = defaultdict(list)
    pairs = defaultdict(list)
    for row in rows:
        c = row['case']
        m = metadata[c]
        if m['family'] in ('ordinary_perfect', 'ordinary_random'):
            groups[m['base']].append(c)
        if m['family'] == 'paired':
            pairs[(m['base'],m['pose'])].append(c)
    ordinary, eight, sixteen, single = set(), set(), set(), set()
    for b, cs in groups.items():
        assert len(cs) == 2 and len({metadata[c]['pose'] for c in cs}) == 2
        length = len(metadata[cs[0]]['path']) - 1
        if length >= 8:
            single.update(set(cs) & good)
        if all(c in good for c in cs):
            ordinary.add(b)
            if length >= 8:
                eight.add(b)
            if length >= 16:
                sixteen.add(b)
    return dict(ordinary=ordinary, ordinary8=eight, ordinary16=sixteen, single8=single,
                pairs={k for k,cs in pairs.items() if len(cs) == 2 and all(c in good for c in cs)},
                corridors={c for c in good if metadata[c]['family'] == 'corridor'},
                no_path={r['case'] for r in rows if r['no_path']},
                false={r['case'] for r in rows if r['reachable'] and r['status']=='no_path'},
                success={r['case'] for r in rows if r['optimal'] or r['no_path']})


def comparison(c, p):
    if p is None:
        return None
    result = {}
    for key in ('pairs','corridors','ordinary','no_path','ordinary8'):
        result[key] = dict(before=len(p[key]),retained=len(c[key]&p[key]),
                           gained=len(c[key]-p[key]),lost=len(p[key]-c[key]))
    result['all_old_correct_inputs_retained'] = not (p['success']-c['success'])
    result['domain90_and_disconnection90_zero_false'] = (bool(p['no_path']) and not c['false'] and all(
        len(c[k]&p[k]) / len(p[k]) >= .9 for k in ('pairs','corridors','ordinary','no_path') if p[k]))
    return result


def main():
    started, cpu = time.monotonic(), time.process_time()
    target = OUT / 'verification.json'
    assert not target.exists()
    summary = json.loads((OUT / 'summary.json').read_text())
    journal_sha = sha(RUN / 'campaign.sqlite')
    assert journal_sha == summary['input_integrity_before']['search_journal_sha256']
    cohorts = {}
    with gzip.open(OUT / 'cohorts.jsonl.gz','rt') as f:
        for line in f:
            r = json.loads(line)
            assert r['id'] not in cohorts
            cohorts[r['id']] = r
    hits = {}
    with gzip.open(OUT / 'novel_hits.jsonl.gz','rt') as f:
        for line in f:
            h = json.loads(line)
            hits[h['stage'], h['id']] = h
    initial = readz(OLD / 'founders.json.gz')
    final = readz(OLD / 'final_states.json.gz')
    parents, births, exposures, children, changed_children, first_child = {}, {}, Counter(), Counter(), Counter(), {}
    seen, seen_hits = set(), set()
    ever8, ever16, evernew, evernewpose, evernewcollective = set(),set(),set(),set(),set()
    maxedges, all_bases, all_singles = {},defaultdict(set),defaultdict(set)
    instruction = {}
    for i,e in readz(OLD / 'inherited_registry.json.gz').items():
        blocks = e['item']['genome']['body']['blocks']
        instruction[i] = sum(len(b)+int(len(b)>0) for b in blocks)
    append = defaultdict(Counter)
    con = sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON')
    con.execute('BEGIN')
    stages = 0
    for n,g,inp,dec in con.execute("SELECT n,generation,input,decision FROM stages WHERE kind='train' AND complete=1 ORDER BY n"):
        assert time.monotonic()-started < 1800
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform=='darwin' else 1024)
        assert rss < 4*1024**3 and shutil.disk_usage(OUT).free >= 16*1024**3
        data, decisions = un(inp),un(dec)
        rows = [{} for _ in initial]
        for blob, in con.execute('SELECT result FROM tasks WHERE stage=? ORDER BY n',(n,)):
            for e in un(blob)['entries']:
                for k,identity in e['aliases']:
                    assert identity not in rows[k]
                    rows[k][identity] = e['rows']
        for k,d in enumerate(decisions):
            rs = rows[k]
            meta = data['metadata']
            caps = {i:classify(r,meta) for i,r in rs.items()}
            union = {field:set().union(*(caps[i['id']][field] for i in initial[k]['protected'])) for field in ('ordinary8','single8')}
            for identity,c in caps.items():
                if identity not in cohorts:
                    continue
                record = cohorts[identity]
                assert identity in births and record['birth'] == births[identity] and record['parent']==parents[identity]
                exposures[identity] += 1
                new_b = c['ordinary8']-union['ordinary8']
                new_c = c['single8']-union['single8']
                collective = {b for b in new_b if any(meta[cid].get('base')==b for cid in new_c)}
                if identity not in seen:
                    assert births[identity]==g
                    seen.add(identity)
                    first = record['first']
                    assert first['stage']==n and first['generation']==g
                    assert first['counts']=={key:len(value) for key,value in c.items()}
                    assert first['novel_complete8']==len(new_b)
                    assert first['novel_single8']==len(new_c)
                    assert first['novel_complete8_beyond_collective']==len(collective)
                    assert first['parent']==comparison(c,caps.get(record['parent']))
                    assert first['root']==comparison(c,caps.get(record['root']))
                    for key,expected in [('correct_ordinary8_bases',c['ordinary8']),('correct_single8_inputs',c['single8']),
                                         ('novel_complete8_bases',new_b),('novel_single8_inputs',new_c)]:
                        assert first[key]==sorted(expected)
                    assert record['survived_first']==(identity in d['survivors'])
                if c['ordinary8']:ever8.add(identity)
                if c['ordinary16']:ever16.add(identity)
                if new_b:evernew.add(identity)
                if new_c:evernewpose.add(identity)
                if collective:evernewcollective.add(identity)
                lengths=[len(meta[row['case']]['path'])-1 for row in rs[identity]
                         if row['optimal'] and meta[row['case']]['family'] in ('ordinary_perfect','ordinary_random')
                         and meta[row['case']]['base'] in c['ordinary']]
                if lengths:maxedges[identity]=max(maxedges.get(identity,0),max(lengths))
                all_bases[identity].update(new_b)
                all_singles[identity].update(new_c)
                if new_b or new_c:
                    key=(n,identity)
                    h=hits[key]
                    assert h['novel_complete8']==sorted(new_b) and h['novel_single8']==sorted(new_c)
                    assert h['novel_complete8_beyond_collective']==sorted(collective)
                    assert h['counts']=={f:len(v) for f,v in c.items()}
                    assert h['first_training_exposure']==(g==births[identity])
                    assert h['survived']==(identity in d['survivors'])
                    assert h['parent']==comparison(c,caps.get(record['parent']))
                    assert h['root']==comparison(c,caps.get(record['root']))
                    seen_hits.add(key)
            for b in d['births']:
                item=b['item'];identity=item['id'];parent=item['parent']
                assert identity not in births and item['birth']==g+1
                parents[identity]=parent;births[identity]=g+1
                blocks=item['genome']['body']['blocks']
                instruction[identity]=sum(len(block)+(1 if block else 0) for block in blocks)
                r=cohorts[identity]
                assert instruction[identity]==r['instructions']
                assert r['population']==d['name'] and r['parent_policy']==b['parent_policy']
                if parent:
                    event,=b['events']
                    assert r['mutant'] and r['noop']==(event['before']==event['after'])
                    if parent in seen:
                        children[parent]+=1
                        changed_children[parent]+=event['before']!=event['after']
                        first_child.setdefault(parent,g+1)
                    if event['opportunity']==0:
                        total=instruction[parent]+3>128
                        writer=event['activation_index']+3>31
                        reason='both_bounds' if total and writer else 'total128_only' if total else 'writer31_only' if writer else 'admitted'
                        append[d['name']][reason]+=1
                        assert (event['kind']=='bounded_noop')==(total or writer)
                else:assert not r['mutant']
        stages+=1
    con.close()
    live={i['id'] for s in final for i in s['population']}
    archive={i['id'] for s in final for i in s['archive']}
    descendants=Counter()
    for identity in live:
        current=parents.get(identity)
        while current in cohorts:
            descendants[current]+=1
            current=parents[current]
    for identity,r in cohorts.items():
        assert r['train_exposures']==exposures[identity]
        assert (r['first'] is None)==(identity not in seen)
        assert r['children_after_first']==children[identity]
        assert r['changed_mutant_children_after_first']==changed_children[identity]
        assert r['first_offspring_generation']==first_child.get(identity)
        if identity in first_child:assert first_child[identity]>r['first']['generation']
        assert r['final_live']==(identity in live) and r['final_archive']==(identity in archive)
        assert r['live_descendants']==descendants[identity]
        for key,s in [('ever_ordinary8',ever8),('ever_ordinary16',ever16),('ever_novel_complete8',evernew),
                      ('ever_novel_single8',evernewpose),('ever_novel_complete8_beyond_collective',evernewcollective)]:
            assert r[key]==(identity in s)
        assert r['max_correct_ordinary_edges']==maxedges.get(identity)
        assert r['novel_complete_bases']==sorted(all_bases[identity])
        assert r['novel_single_inputs']==sorted(all_singles[identity])
    assert len(seen)==99216 and len(cohorts)==99528 and stages==319
    assert seen_hits==set(hits)
    for name,counts_ in append.items():
        assert dict(counts_)=={k:v for k,v in summary['append_opportunities'][name].items() if '/' not in k}
    assert sha(RUN/'campaign.sqlite')==journal_sha
    result=dict(status='PASS',scope='Independent saved-row grouping/identity lifecycle verification; not new inference or a second VM.',
                first_training_exposures_verified=len(seen),births_verified=len(cohorts),training_stages=stages,
                novel_hit_presentations_verified=len(seen_hits),all_prospective_append_bounds_reconciled=True,
                survival_reproduction_final_descendants_verified=True,
                original_search_journal_sha256_unchanged=journal_sha,
                wall_seconds=time.monotonic()-started,cpu_seconds=time.process_time()-cpu,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
                inference_calls=0,generated_layouts=0)
    with target.open('x') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException:
        import traceback
        path=OUT/('verification_failure_'+time.strftime('%Y%m%d_%H%M%S')+'.json')
        with path.open('x') as f:json.dump(dict(traceback=traceback.format_exc()),f,indent=2)
        raise
