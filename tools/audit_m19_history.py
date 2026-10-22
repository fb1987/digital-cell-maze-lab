"""Check saved-history exports against source events and independent set metrics."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import sqlite3
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.analyze_m19_history import ROOT, SOURCE, OUT, DB, sha, write, readz, digest, guard, verify_source, aggregate
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.breeding_allocation_metrics import capabilities_plus, upstream_pairs


def lines(name):
    with gzip.open(OUT/name,'rt') as f:
        return [json.loads(line) for line in f]


def independently_compare(rows, parent, protected_rows, entry, a0_rows, meta, exported):
    cap=capabilities_plus(rows,meta)
    p=capabilities_plus(parent,meta) if parent is not None else None
    e=capabilities_plus(entry,meta) if entry is not None else None
    refs=[capabilities_plus(rs,meta) for rs in protected_rows]
    a0=capabilities_plus(a0_rows,meta)
    assert exported['correct_inputs']==len(cap['success'])
    assert exported['false_no_path']==len(cap['false'])
    assert exported['correct_disconnections']==len(cap['correct_no_path'])
    success_union=set().union(*(c['success'] for c in refs))
    assert exported['novel_reachable_success']==len({r['case'] for r in rows if r['optimal'] and r['reachable']}-success_union)
    assert exported['novel_upstream']==len(upstream_pairs(cap,meta)-set().union(*(upstream_pairs(c,meta) for c in refs)))
    ordinary_union=set().union(*(c['ordinary_bases'] for c in refs))
    assert exported['novel_ordinary_bases']==len(cap['ordinary_bases']-ordinary_union)
    queried={r['case'] for r in rows}
    om={m['base']:m for cid,m in meta.items() if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random')}
    for threshold in (8,16):
        assert exported['novel_long'+str(threshold)]==sum(len(om[b]['path'])-1>=threshold for b in cap['ordinary_bases']-ordinary_union)
    for label, other in [('parent',p),('entry',e)]:
        assert exported[label+'_available']==(other is not None)
        if other is None:
            assert exported[label+'_all_correct_retained'] is None
        else:
            assert exported[label+'_correct_denominator']==len(other['success'])
            assert exported[label+'_new_correct']==len(cap['success']-other['success'])
            assert exported[label+'_lost_correct']==len(other['success']-cap['success'])
            assert exported[label+'_all_correct_retained']==(bool(other['success']) and other['success']<=cap['success'])
            assert exported[label+'_90pct_skill_retention']==all(not other[k] or len(cap[k]&other[k])/len(other[k])>=.9 for k in ('pairs','corridors','ordinary_bases','correct_no_path'))
    if parent is not None:
        assert [r['case'] for r in rows]==[r['case'] for r in parent]
        assert exported['same_terminal_as_parent']==all((a['mask'],a['status'])==(b['mask'],b['status']) for a,b in zip(rows,parent))
        assert exported['same_steps_as_parent']==all(a['steps']==b['steps'] for a,b in zip(rows,parent))
        work=lambda rs:sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rs)
        assert exported['work_delta_from_parent']==work(rows)-work(parent)
    assert exported['a0_disconnection_denominator']==len(a0['correct_no_path'])
    assert exported['a0_disconnection_90pct']==(bool(a0['correct_no_path']) and len(cap['correct_no_path']&a0['correct_no_path'])/len(a0['correct_no_path'])>=.9)


def main():
    started=time.monotonic();assert not (OUT/'audit.json').exists()
    source=verify_source();summary=json.loads((OUT/'analysis.json').read_text());assert source==summary['source']
    records=lines('birth_lifetimes.jsonl.gz');life={r['id']:r for r in records};assess=lines('assessment_presentations.jsonl.gz')
    assert len(life)==len(records)==128700
    assert aggregate(records)==summary['training']
    samples=defaultdict(list)
    for r in summary['audit_samples']: samples[r['stage']].append((r['population_index'],r['id'],life[r['id']]['first_train']))
    names={name:int(name.split('/')[1])*3+{'generic':0,'disconnected':1,'connected':2}[name.split('/')[2]] for name in {r['population'] for r in records}}
    for r in assess:
        if int(hashlib.sha256((r['id']+'/'+str(r['stage'])).encode()).hexdigest(),16)%64==0:
            samples[r['stage']].append((names[r['population']],r['id'],r))
    c=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);c.execute('BEGIN')
    states=unpacked(c.execute('select value from states where stage=-1').fetchone()[0])
    digests={i['id']:digest(i['genome']) for s in states for i in s['population']}
    counts=Counter();children=Counter();exposed=set();survival=defaultdict(Counter);replays=0;all_births=set();pending=defaultdict(list)
    for n,kind,g,ib,eb in c.execute('select n,kind,generation,input,decision from stages where complete=1 order by n'):
        guard(started);events=unpacked(eb)
        if n in samples:
            data=unpacked(ib);panel=[{} for _ in states]
            for rb, in c.execute('select result from tasks where stage=? order by n',(n,)):
                for e in unpacked(rb)['entries']:
                    for k,i in e['aliases']:
                        if not i.startswith('budget_padding/'):panel[k][i]=e['rows']
            for k,i,expected in samples[n]:
                fs=panel[k];r=life[i];by_digest={digests[j]:rs for j,rs in fs.items()}
                entry=fs.get(r['entry'])
                if entry is None:entry=by_digest.get(digests[r['entry']])
                independently_compare(fs[i],fs.get(r['parent']),[fs[x['id']] for x in states[k]['protected']],entry,fs['m14/reference/anchor/0'],data['metadata'],expected)
                replays+=1
        for event in events:
            survivors=set(event.get('survivors',[]))
            if kind=='train':
                # Every previous-round mutant must get exactly one first exposure.
                for r in pending.get(event['name'],[]):
                    assert r['id'] not in exposed;exposed.add(r['id'])
                    x=r['first_train'];assert x['stage']==n and x['generation']==g
                    assert x['survived']==(r['id'] in survivors)
                    expected_children=sum(b['item']['parent']==r['id'] for b in event['births'])
                    assert x['children_born']==expected_children
                    survival[event['name']][r['edit_kind']+'/presentations']+=1
                    survival[event['name']][r['edit_kind']+'/survive_next_train']+=x['survived']
                pending[event['name']]=[]
            for b in event['births']:
                i=b['item'];r=life[i['id']];assert i['id'] not in all_births;all_births.add(i['id'])
                assert r['parent']==i['parent'] and r['birth_generation']==i['birth'] and r['parent_policy']==b['parent_policy']
                digests[i['id']]=digest(i['genome'])
                kind_of_birth='mutation' if b['events'] else 'immigrant';counts[kind_of_birth]+=1
                assert r['birth_kind']==kind_of_birth
                if i['parent']:children[i['parent']]+=1
                if b['events']:pending[event['name']].append(r)
    c.close()
    assert len(exposed)==110970 and len(all_births)==128700
    for r in records:assert r['children']==children[r['id']]
    audit=json.loads((SOURCE/'search_audit.json').read_text())
    assert {k:dict(v) for k,v in survival.items()}==audit['immediate_birth_survival']
    assert verify_source()==source
    write(OUT/'audit.json',dict(status='PASS',birth_events_checked=len(all_births),first_training_survival_and_breeding_checked=len(exposed),
        aggregate_recomputed_from_export=True,source_audit_survival_counts_match=True,independent_saved_set_comparisons=replays,
        train_sample='SHA256(identity) modulo64 ==0',assessment_sample='SHA256(identity/stage) modulo64 ==0',
        source_hashes_unchanged=source,inference_calls=0,new_cases=0,wall_seconds=time.monotonic()-started,
        limitation='Saved-receipt analysis audit, not another native VM or independent confirmation. Aggregate routine shared; sampled capability comparisons use a separate existing set implementation.'))
    print('Audit PASS:',len(exposed),'first exposures;',replays,'independent saved comparisons',flush=True)


if __name__=='__main__':
    main()
