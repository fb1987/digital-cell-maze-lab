"""Seal reviewed M28 once. Frozen science and prior seals remain immutable."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.integration_accessibility import ROOT,OUT,RUN,check,prior_check,readz,writej,sha,storage,final_summary,load
from maze_evolution.referenced_campaign_store import load_layouts


def published_files(commit,files):
    requests=''.join(f'{commit}:{p}\n' for p in files).encode()
    data=subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,input=requests);position=0
    for p,h in files.items():
        end=data.index(b'\n',position);header=data[position:end].decode().split();assert len(header)==3 and header[1]=='blob',p
        n=int(header[2]);content=data[end+1:end+1+n];assert hashlib.sha256(content).hexdigest()==h,p
        position=end+n+2
    assert position==len(data)


def main():
    config=check();assert not (OUT/'completion.json').exists();prior=prior_check()
    status=json.loads((RUN/'workflow_status.json').read_text());assert status['state']=='audited_ready_for_report'
    assert [s['phase'] for s in status['steps']]==['development','select','freeze','audit_development','final','analyze','audit_final']
    assert all(s['code']==0 for s in status['steps'])
    review=json.loads((OUT/'report_review.json').read_text());assert review['status']=='PASS' and review['report_sha256']==sha(OUT/'report.md')
    launch=json.loads((OUT/'launch.json').read_text());reg=json.loads((OUT/'registration.json').read_text());freeze=json.loads((OUT/'choice_freeze.json').read_text())
    for commit in (launch['registration_commit'],freeze['commit']):subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
    published_files(launch['registration_commit'],dict(reg['files'],**{str((OUT/'registration.json').relative_to(ROOT)):sha(OUT/'registration.json')}))
    published_files(freeze['commit'],{str((OUT/'choices.json.gz').relative_to(ROOT)):sha(OUT/'choices.json.gz')})
    assert freeze['choices_sha256']==sha(OUT/'choices.json.gz') and freeze['published_before_fresh_generation']
    assert launch['pool_sha256']==sha(OUT/'pool.json.gz')
    for name in ('development','final'):
        s=json.loads((OUT/(name+'_session.json')).read_text());a=json.loads((OUT/(name+'_audit.json')).read_text())
        assert s['status']=='complete' and s['reason'] is None and s['usage']['uncertain_attempts']==0
        assert s['wall_seconds']<(config['session_wall_seconds'] if name=='development' else config['final_wall_seconds'])
        assert a['status']=='PASS' and a['wall_seconds']<config['audit_wall_seconds']
        assert max(s['rss_peak_bytes'],a['rss_peak_bytes'])<config['memory_bytes']
        assert s['usage']['calls']<=config['call_cap'] and s['usage']['work']<=config['work_cap']
        assert a['all_native_replays']==a['independent_grades']==s['usage']['calls'] and a['counted_work']==s['usage']['work']
        assert a['all_controls_correct'] and a['source_prior_hashes']==prior
    data,rows,models,usage,chain=load('final');summary=json.loads((OUT/'summary.json').read_text())
    assert final_summary(readz(OUT/'pool.json.gz'),data,rows,usage,chain)==summary
    preservation=json.loads((OUT/'preservation.json').read_text())
    for rec in preservation['journals'].values():
        assert sha(ROOT/rec['journal']['path'])==rec['journal']['sha256']
        if rec['backup']['status']=='verified':assert sha(ROOT/rec['backup']['path'])==rec['backup']['sha256']
    assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==preservation['whole_layouts']
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes']
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in [*RUN.glob('*.log'),*RUN.glob('*.jsonl')]:shutil.copy2(p,logs/p.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/INTEGRATION_ACCESSIBILITY_M28_PROGRESS.md',ROOT/'tools/preserve_m28.py',ROOT/'tools/analyze_m28_saved.py',ROOT/'tools/inspect_m28_structured.py',ROOT/'tools/inspect_m28_operator_events.py',ROOT/'tools/report_m28.py',Path(__file__).resolve()]
    files=dict(reg['files']);files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    local={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log','.jsonl') or p.name=='workflow_status.json')}
    assert storage()+1000000<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_independent_confirmation_and_all_native_audits',files=files,local_records=local,
        registration_commit=launch['registration_commit'],choice_freeze_commit=freeze['commit'],primary=summary['primary'],source_priors=prior,
        whole_layouts=preservation['whole_layouts'],storage_bytes_before_seal=storage(),disk_free_bytes=shutil.disk_usage(RUN).free,
        no_evolution=True,no_final_reselection=True,old_histories_unchanged=True,next_phase_launched=False,
        mutable_handoff='AGENTS.md intentionally excluded. Future audits require NEW output packets; never overwrite old seals, frozen science or failed artifacts.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M28 sealed',len(files),'files',len(local),'local records',flush=True)


if __name__=='__main__':main()
