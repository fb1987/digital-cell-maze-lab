"""Fixed C1 comparisons and sampled audit; no nomination or adaptive cases."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import sqlite3
import time
from .deep_confirmation import OUT,RUN,PRIOR,ROOT,check,writej,panel
from .foundation_study import read_compressed as readz,compressed_json as writez
from .deep_campaign_store import Journal,unpacked,hashed
from .deep_campaign_data import cases_from_manifest
from .foundation_study_verify_core import Checker
from .exposure_selection import organism,record
from .foundation_pair_confirm import normal_row
from .routing_transfer import canonical,sha
from .baselines import baseline
from .reboot_data import confirmation


def load():
    c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
    stage=c.execute('select n,input,input_hash,chain_hash from stages where complete=1').fetchone()
    assert stage and stage[0]==0 and hashed(stage[1])==stage[2]
    data=unpacked(stage[1]);models=[];rows={};receipts=[]
    for spec,result,h in c.execute('select spec,result,result_hash from tasks where stage=0 order by n'):
        assert hashed(result)==h
        receipt=unpacked(result);spec=unpacked(spec);assert len(spec)==len(receipt['entries'])==1
        entry=receipt['entries'][0];assert entry['aliases']==spec[0]['aliases']
        for identity in entry['aliases']:rows[identity]=entry['rows']
        models.append((spec[0],entry['rows']));receipts.append(receipt)
    usage=unpacked(c.execute('select value from settings where key="usage"').fetchone()[0]);c.close()
    return data,rows,models,usage,stage[3]


def capabilities(rows,meta):
    groups=defaultdict(list);corr=set();ordinary=defaultdict(list);by=defaultdict(Counter);false=set();success=set()
    for r in rows:
        cid=r['case'];m=meta[cid];family=m['family'];stratum=family+('/'+str(m['size']) if 'size' in m else '')
        by[stratum]['inputs']+=1;by[stratum]['optimal']+=int(r['optimal']);by[stratum]['valid']+=int(r['valid']);by[stratum]['correct_no_path']+=int(r['no_path'])
        bad=r['reachable'] and r['status']=='no_path';by[stratum]['false_no_path']+=int(bad)
        if bad:false.add(cid)
        if r['optimal'] or r['no_path']:success.add(cid)
        if family=='paired':groups[(m['base'],m['pose'])].append(r)
        if family=='corridor' and r['optimal']:corr.add(cid)
        if family.startswith('ordinary_'):ordinary[m['base']].append(r)
    good={k for k,v in groups.items() if len(v)==2 and all(r['optimal'] for r in v)}
    pair_by=defaultdict(Counter)
    for k,v in groups.items():
        m=meta[v[0]['case']];stratum=m['graph']+'/'+str(m['prefix']);pair_by[stratum]['opportunities']+=1;pair_by[stratum]['correct']+=int(k in good)
    both={b for b,v in ordinary.items() if len(v)==2 and all(r['optimal'] for r in v)}
    return dict(pairs=good,corridors=corr,ordinary_bases=both,false=false,success=success,
        summary=dict(inputs=len(rows),by_domain={k:dict(v) for k,v in by.items()},paired=len(good),pair_opportunities=len(groups),by_pair_stratum={k:dict(v) for k,v in pair_by.items()},
                     ordinary_bases_both_poses=len(both),false_no_path=len(false),work=sum(r['reads']+r['dispatches']+r['exposure_checks'] for r in rows)))


def compare(a,b,meta):
    new=a['pairs']-b['pairs'];lost=b['pairs']-a['pairs']
    pair_meta={(m['base'],m['pose']):m for m in meta.values() if m['family']=='paired'}
    ordinary_meta={m['base']:m for m in meta.values() if m['family'].startswith('ordinary_')}
    contexts={pair_meta[k]['template'] for k in new}
    retention={k:len(a[k]&b[k])/len(b[k]) if b[k] else None for k in ('pairs','corridors')}
    newbases=a['ordinary_bases']-b['ordinary_bases']
    families={ordinary_meta[b]['family'] for b in newbases}
    checks=dict(new_pairs=len(new)>=8,contexts=len(contexts)>=2,
        retention=all(v is None or v>=.9 for v in retention.values()),false_no_path=len(a['false'])<=len(b['false']))
    acquisition=all(checks.values())
    return dict(new_pairs=len(new),lost_pairs=len(lost),new_pair_contexts=len(contexts),retention=retention,
        new_ordinary_bases=len(newbases),lost_ordinary_bases=len(b['ordinary_bases']-a['ordinary_bases']),
        new_ordinary_by_domain=dict(Counter(ordinary_meta[b]['family']+'/'+str(ordinary_meta[b]['size']) for b in newbases)),
        acquisition_gate=acquisition,gate_checks=checks,
        broad_transfer_flag=acquisition and len(newbases)>=4 and {'ordinary_perfect','ordinary_random'}<=families,
        new_pair_keys=sorted(new),lost_pair_keys=sorted(lost),new_ordinary_base_keys=sorted(newbases))


def analyze():
    check();data,rows,models,usage,chain=load();p=readz(OUT/'panel.json.gz');meta=data['metadata']
    caps={i:capabilities(r,meta) for i,r in rows.items()}
    founders=set(p['initial_identities']);union={k:set().union(*(caps[i][k] for i in founders)) for k in ('pairs','corridors','ordinary_bases','false','success')}
    summaries=[]
    for c in p['comparisons']:
        child=c['child'];root=c['root'];a=caps[child]
        root_comparison=compare(a,caps[root],meta)
        root_comparison['eligible_for_evolved_acquisition']=c['mutations']>0
        if not c['mutations']:root_comparison['acquisition_gate']=root_comparison['broad_transfer_flag']=False
        summaries.append(dict(**c,metrics=a['summary'],versus_root=root_comparison,
            versus_parent=compare(a,caps[c['parent']],meta) if c['parent'] else None,
            novel_vs_all_founders=dict(pairs=len(a['pairs']-union['pairs']),ordinary_bases_both_poses=len(a['ordinary_bases']-union['ordinary_bases']),
                correct_inputs=len(a['success']-union['success']))))
    result=dict(status='confirmation_evaluated',independent_confirmation=True,no_selection=True,chain=chain,usage=usage,
        queried_inputs=len(data['queries']['all']),contexts=len(data['contexts']),physical_models=len(models),identities=len(rows),
        initial_slots=len(p['initial_identities']),unique_initial_identities=len(founders),nominees=summaries,
        all_model_metrics={i:c['summary'] for i,c in caps.items()},
        limitations=['Selected descendants share ancestry; not independent evolutionary replicates.',
        'Structured cases reuse the existing grammar; poses/variants correlate.',
        'Perfect15/random15 measure size transfer, not an unrestricted general solver.',
        'Random endpoint/component and partition-disconnected generation biases remain.',
        'No latency claim; controls share the candidate domain but conventional methods use their own algorithms.'])
    writej(OUT/'summary.json',result)
    cases=cases_from_manifest([r for r in data['mazes'] if r['case_id'] in data['queries']['all']]);checker=Checker(cases)
    baseline_rows={};started=time.perf_counter()
    for name in ('compiled_bfs','compiled_astar','wave_bit'):
        rr=[]
        for cid in data['queries']['all']:
            o=cases[cid];m=o.maze;r=canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o));checker.row(r);assert r['optimal'] or r['no_path'];rr.append(r)
        baseline_rows[name]=rr
    writez(OUT/'baselines.json.gz',baseline_rows)
    writej(OUT/'baseline_usage.json',dict(calls=sum(map(len,baseline_rows.values())),wall_seconds=time.perf_counter()-started,all_correct=True))
    writez(OUT/'responses.json.gz',dict(models=[dict(aliases=s['aliases'],rows=r) for s,r in models]))
    writez(OUT/'new_layout_exclusions.json.gz',dict(count=len(data['new_layouts']),hashes=data['new_layouts'],
        previous='results/deep_confirmation/exclusions.json.gz',previous_sha256=sha(OUT/'exclusions.json.gz')))
    print(json.dumps(dict(inputs=result['queried_inputs'],models=len(models),nominees=[dict(id=n['child'],paired=n['metrics']['paired'],acquisition=n['versus_root']['acquisition_gate'],broad=n['versus_root']['broad_transfer_flag']) for n in summaries]),indent=2))


def audit():
    started=time.monotonic();check();data,rows,models,usage,chain=load();p=readz(OUT/'panel.json.gz')
    assert panel()==p
    previous=set(readz(OUT/'exclusions.json.gz')['hashes'])
    recreated=confirmation(json.loads((OUT/'config.json').read_text())['seed'],previous)
    expected=readz(OUT/'confirmation.json.gz');assert recreated==expected
    assert data==dict(expected,queries={'all':expected['queries']})
    cases=cases_from_manifest([r for r in data['mazes'] if r['case_id'] in data['queries']['all']]);checker=Checker(cases)
    exact=grades=0
    for spec,rr in models:
        org=organism(spec['model']);model_id=hashed(__import__('maze_evolution.deep_campaign_store',fromlist=['packed']).packed(spec['model']))
        assert [r['case'] for r in rr]==spec['queries']
        for r in rr:
            checker.row(r);grades+=1
            if int(hashlib.sha256((model_id+'/'+r['case']).encode()).hexdigest()[:8],16)%32==0:
                o=cases[r['case']];m=o.maze
                assert record(org.react(m.cells,m.w,m.h,m.start,m.goal),o)==r
                exact+=1
    base=readz(OUT/'baselines.json.gz');bc=0
    for name,rr in base.items():
        for r in rr:
            o=cases[r['case']];m=o.maze;assert canonical(normal_row(baseline(name,m.cells,m.w,m.h,m.start,m.goal),o))==r;checker.row(r);bc+=1
    c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
    # Journal.verify_chain is read-only, instantiated without its writer constructor.
    j=Journal.__new__(Journal);j.db=c;j.directory=RUN
    assert j.verify_chain()==chain;c.close()
    before=(OUT/'summary.json').read_bytes();analyze();assert (OUT/'summary.json').read_bytes()==before
    result=dict(passed=True,source_hashes=True,panel_ancestry=True,corpus_recreated=True,chain=chain,
        independently_graded=grades,native_sample_replays=exact,baseline_replays=bc,summary_recomputed=True,
        second_vm=False,wall_seconds=time.monotonic()-started,usage=usage)
    assert not (OUT/'audit.json').exists();writej(OUT/'audit.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['analyze','audit']);args=a.parse_args();globals()[args.action]()
