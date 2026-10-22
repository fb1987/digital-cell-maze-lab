"""Audit every reported incremental event and fixed samples using saved sets."""
from collections import defaultdict
import gzip,hashlib,json,sqlite3,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.analyze_m19_history import SOURCE,OUT,DB,digest,guard,write,verify_source
from tools.audit_m19_history import lines,independently_compare
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.breeding_allocation_metrics import capabilities_plus


def main():
    start=time.monotonic();assert not (OUT/'incremental_audit.json').exists();before=verify_source()
    life={r['id']:r for r in lines('birth_lifetimes.jsonl.gz')}
    assessments=lines('assessment_presentations.jsonl.gz');events=lines('incremental_events.jsonl.gz')
    exported={(r['id'],r['stage']):r for r in events};assert len(exported)==len(events)
    expected={}
    for r in life.values():
        if 'first_train' in r:expected[(r['id'],r['first_train']['stage'])]=r['first_train']
    for r in assessments:expected[(r['id'],r['stage'])]=r
    targets=defaultdict(set)
    for i,n in expected:
        if (i,n) in exported or int(hashlib.sha256((i+'/'+str(n)).encode()).hexdigest(),16)%64==0:targets[n].add(i)
    c=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);c.execute('BEGIN')
    states=unpacked(c.execute('select value from states where stage=-1').fetchone()[0]);indices={s['name']:k for k,s in enumerate(states)}
    digests={i['id']:digest(i['genome']) for s in states for i in s['population']};verified=set();sample_count=0
    for n,ib,eb in c.execute('select n,input,decision from stages where complete=1 order by n'):
        guard(start)
        if n in targets:
            meta=unpacked(ib)['metadata'];rows=[{} for _ in states]
            for rb, in c.execute('select result from tasks where stage=? order by n',(n,)):
                for e in unpacked(rb)['entries']:
                    for k,i in e['aliases']:
                        if not i.startswith('budget_padding/'):rows[k][i]=e['rows']
            cached={}
            for i in targets[n]:
                r=life[i];k=indices[r['population']];rr=rows[k]
                if k not in cached:
                    refs=[rr[x['id']] for x in states[k]['protected']]
                    caps={j:capabilities_plus(rs,meta) for j,rs in rr.items()}
                    covered=set().union(*(caps[x['id']]['success'] for x in states[k]['protected']))
                    ordinary=set().union(*(caps[x['id']]['ordinary_bases'] for x in states[k]['protected']))
                    cached[k]=(refs,caps,covered,ordinary,{digests[j]:rs for j,rs in rr.items()})
                refs,caps,covered,ordinary,by_digest=cached[k];p=rr.get(r['parent'])
                entry=rr.get(r['entry'])
                if entry is None:entry=by_digest.get(digests[r['entry']])
                stats=expected[(i,n)]
                independently_compare(rr[i],p,refs,entry,rr['m14/reference/anchor/0'],meta,stats)
                added={x['case'] for x in rr[i] if x['optimal'] and x['reachable']}-covered-(caps[r['parent']]['success'] if p is not None else set())
                queried={x['case'] for x in rr[i]};om={m['base']:m for cid,m in meta.items() if cid in queried and m['family'] in ('ordinary_perfect','ordinary_random')}
                new_long={b for b in caps[i]['ordinary_bases']-ordinary-(caps[r['parent']]['ordinary_bases'] if p is not None else set()) if len(om[b]['path'])-1>=8}
                should_exist=p is not None and bool(added or new_long)
                assert should_exist==((i,n) in exported)
                if should_exist:
                    x=exported[(i,n)];assert set(x['added_cases'])==added and set(x['added_long_bases'])==new_long
                    assert x['flags']['addition_parent_kept']==bool(added and stats['parent_all_correct_retained'] and not stats['false_no_path'])
                    assert x['flags']['addition_parent_and_entry_kept']==bool(x['flags']['addition_parent_kept'] and stats['entry_all_correct_retained'])
                    verified.add((i,n))
                sample_count+=1
        for e in unpacked(eb):
            for b in e['births']:digests[b['item']['id']]=digest(b['item']['genome'])
    c.close();assert verified==set(exported);assert verify_source()==before
    write(OUT/'incremental_audit.json',dict(status='PASS',all_positive_events_checked=len(verified),
        positive_plus_fixed_sample_saved_comparisons=sample_count,source_hashes_unchanged=before,
        selection='All reported positives plus SHA256(identity/stage) modulo64==0 of all training/assessment observations',
        inference_calls=0,new_cases=0,wall_seconds=time.monotonic()-start,
        limitation='Independent existing capability sets on saved responses; no new native evaluation or confirmation.'))
    print('Incremental audit PASS:',len(verified),'positive events;',sample_count,'saved comparisons',flush=True)


if __name__=='__main__':main()
