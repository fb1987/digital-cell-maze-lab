"""Separate inherited portfolio-new coverage from additions made by an edit."""
from collections import Counter, defaultdict
import gzip
import json
import sqlite3
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.analyze_m19_history import SOURCE,OUT,DB,readz,write,features,union_caps,guard,verify_source
from maze_evolution.deep_campaign_store import unpacked


def additions(child,parent,protected,entry):
    if parent is None:return None
    result={k:child[k]-parent[k]-protected[k] for k in ('reachable_success','upstream','ordinary_bases','long8','long16')}
    result['inherited_coverage']=(child['reachable_success']-protected['reachable_success'])&parent['reachable_success']
    result['new_reachable_over_parent']=child['reachable_success']-parent['reachable_success']
    result['phase_new']=result['reachable_success']-entry['reachable_success'] if entry is not None else None
    return result


def main():
    start=time.monotonic();assert not (OUT/'incremental.json').exists()
    assert json.loads((OUT/'audit.json').read_text())['status']=='PASS'
    before=verify_source();life={}
    with gzip.open(OUT/'birth_lifetimes.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line);life[r['id']]=r
    targets=defaultdict(list)
    for r in life.values():
        if 'first_train' in r:targets[r['first_train']['stage']].append((r,r['first_train'],'first_train'))
    with gzip.open(OUT/'assessment_presentations.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line);targets[r['stage']].append((life[r['id']],r,'assessment'))
    c=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);c.execute('BEGIN')
    states=unpacked(c.execute('select value from states where stage=-1').fetchone()[0]);index={s['name']:k for k,s in enumerate(states)}
    from tools.analyze_m19_history import digest
    digests={i['id']:digest(i['genome']) for s in states for i in s['population']}
    counts=defaultdict(Counter);details=[];events=[];checked=0;direct_copy_new_parent=0
    for n,kind,ib,eb in c.execute('select n,kind,input,decision from stages where complete=1 order by n'):
        guard(start)
        if n in targets:
            data=unpacked(ib);fs=[{} for _ in states]
            for rb, in c.execute('select result from tasks where stage=? order by n',(n,)):
                for e in unpacked(rb)['entries']:
                    f=features(e['rows'],data['metadata'])
                    for k,i in e['aliases']:
                        if not i.startswith('budget_padding/'):fs[k][i]=f
            cache={}
            for r,s,observation in targets[n]:
                k=index[r['population']]
                if k not in cache:
                    cache[k]=(union_caps([fs[k][p['id']] for p in states[k]['protected']]),{digests[i]:v for i,v in fs[k].items()})
                protected,by_digest=cache[k];child=fs[k][r['id']];parent=fs[k].get(r['parent']);entry=fs[k].get(r['entry'])
                if entry is None:entry=by_digest.get(digests[r['entry']])
                a=additions(child,parent,protected,entry);checked+=1
                keys=[observation+'/arm:'+r['arm'],observation+'/cohort:'+r['arm']+'/'+r['cohort'],
                      observation+'/policy:'+r['arm']+'/'+r['parent_policy'],observation+'/population:'+r['population']]
                flags={}
                if a is not None:
                    flags={key:bool(a[key]) for key in ('reachable_success','upstream','ordinary_bases','long8','long16','inherited_coverage','new_reachable_over_parent')}
                    flags['phase_new']=bool(a['phase_new'])
                    flags['addition_parent_kept']=bool(a['reachable_success'] and s['parent_all_correct_retained'] and not s['false_no_path'])
                    flags['addition_parent_and_entry_kept']=bool(flags['addition_parent_kept'] and s['entry_all_correct_retained'])
                    flags['addition_parent90_entry90_a0_kept']=bool(a['reachable_success'] and s['parent_90pct_skill_retention'] and
                        s['entry_90pct_skill_retention'] and s['a0_disconnection_90pct'] and not s['false_no_path'])
                    if observation=='first_train' and r['cohort']=='direct_copy':direct_copy_new_parent+=bool(a['new_reachable_over_parent'])
                    assert not flags['addition_parent_and_entry_kept'] or s['portfolio_gain_parent_and_entry_kept']
                for key in keys:
                    v=counts[key];v['observations']+=1;v['parent_available']+=parent is not None;v['entry_available']+=entry is not None
                    for flag,yes in flags.items():
                        v[flag]+=yes
                        if yes:
                            v[flag+'/survived_first_train']+=bool(observation=='first_train' and s['survived'])
                            v[flag+'/ever_bred']+=bool(r['children'])
                            v[flag+'/ending']+=r['ending_live_or_archive']
                if a is not None and (a['reachable_success'] or a['long8']):
                    d=dict(id=r['id'],observation=observation,stage=n,generation=s['generation'],population=r['population'],
                        arm=r['arm'],cohort=r['cohort'],parent_policy=r['parent_policy'],phase_depth=r['phase_depth'],copy_depth=r['copy_depth'],
                        parent=r['parent'],entry=r['entry'],first_train_survived=life[r['id']].get('first_train',{}).get('survived'),
                        direct_children=r['children'],ending=r['ending_live_or_archive'],flags=flags,
                        parent_new_correct=s.get('parent_new_correct'),parent_lost_correct=s.get('parent_lost_correct'),
                        entry_new_correct=s.get('entry_new_correct'),entry_lost_correct=s.get('entry_lost_correct'),false_no_path=s['false_no_path'],
                        a0_disconnection_90pct=s['a0_disconnection_90pct'],correct_disconnections=s['correct_disconnections'],
                        added_cases=sorted(a['reachable_success']),added_long_bases=sorted(a['long8']))
                    events.append(d)
                    for cid in sorted(a['reachable_success']):
                        m=data['metadata'][cid]
                        details.append(dict(id=r['id'],observation=observation,stage=n,case=cid,family=m['family'],base=m.get('base'),
                            size=m.get('size'),edges=len(m['path'])-1,pose=m.get('pose'),graph=m.get('graph'),prefix=m.get('prefix'),
                            both_pose_ordinary=m.get('base') in child['ordinary_bases'],new_complete_upstream=bool(a['upstream'])))
        for e in unpacked(eb):
            for b in e['births']:digests[b['item']['id']]=digest(b['item']['genome'])
    c.close();assert checked==110970+13213
    assert direct_copy_new_parent==0
    for name,rows in [('incremental_events.jsonl.gz',events),('incremental_case_details.jsonl.gz',details)]:
        with gzip.open(OUT/name,'xt') as f:
            for r in rows:f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
    assert verify_source()==before
    write(OUT/'incremental.json',dict(status='complete_saved_only',scope='Post-hoc refinement: subtract immediate parent as well as protected portfolio to distinguish additions from inherited coverage.',
        comparisons=checked,direct_copy_new_reachable_over_parent=direct_copy_new_parent,
        counts={k:dict(v) for k,v in sorted(counts.items())},positive_events=len(events),positive_case_details=len(details),
        inference_calls=0,new_cases=0,source=before,wall_seconds=time.monotonic()-start))
    print('Incremental comparison complete:',checked,'observations;',len(events),'positive events',flush=True)


if __name__=='__main__':main()
