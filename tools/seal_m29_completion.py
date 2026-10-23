"""Seal M29 once after review, audit and guarded original-trace preservation."""
import json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.state_interference import ROOT,OUT,RUN,check,prior_check,readz,read_records,summarize,writej,sha,storage
from maze_evolution.referenced_campaign_store import load_layouts
from tools.seal_m28_completion import published_files


def main():
    config=check();assert not (OUT/'completion.json').exists();prior=prior_check()
    status=json.loads((RUN/'workflow_status.json').read_text());assert status['state']=='audited_ready_for_report'
    assert [x['phase'] for x in status['steps']]==['run','analyze','audit'] and all(x['code']==0 for x in status['steps'])
    reg=json.loads((OUT/'registration.json').read_text());launch=json.loads((OUT/'launch.json').read_text());commit=launch['registration_commit']
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
    published_files(commit,dict(reg['files'],**{str((OUT/'registration.json').relative_to(ROOT)):sha(OUT/'registration.json')}))
    assert sha(OUT/'sources.json.gz')==launch['sources_sha256'] and sha(OUT/'jobs.json.gz')==launch['jobs_sha256']
    review=json.loads((OUT/'report_review.json').read_text());assert review['status']=='PASS' and review['report_sha256']==sha(OUT/'report.md')
    session=json.loads((OUT/'session.json').read_text());audit=json.loads((OUT/'audit.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
    assert session['status']=='PASS' and session['uncertain_attempts']==0 and audit['status']=='PASS'
    assert session['wall_seconds']<config['session_wall_seconds'] and audit['wall_seconds']<config['audit_wall_seconds']
    for x in (session,audit):
        assert x['totals']['executions']<=config['execution_cap'] and x['totals']['counted_work']<=config['work_cap'] and x['rss_peak_bytes']<config['memory_bytes']
    assert session['totals']['executions']==audit['totals']['executions'] and session['totals']['counted_work']==audit['totals']['counted_work']
    records=read_records();assert len(records)==audit['all_jobs_replayed']==len(readz(OUT/'jobs.json.gz'))
    assert summarize(readz(OUT/'sources.json.gz'),records)==summary and audit['source_priors']==prior
    pres=json.loads((OUT/'preservation.json').read_text());rec=pres['journal']
    assert sha(ROOT/rec['source']['path'])==rec['source']['sha256']
    if rec['backup']['status']=='verified':assert sha(ROOT/rec['backup']['path'])==rec['backup']['sha256']
    assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==pres['whole_layouts'] and pres['new_layouts']==0
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes']
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in [*RUN.glob('*.log'),*RUN.glob('*.jsonl')]:shutil.copy2(p,logs/p.name)
    for p in (RUN/'evaluation').glob('*.jsonl'):shutil.copy2(p,logs/('science_'+p.name))
    for p in (RUN/'fixture').glob('*.jsonl'):shutil.copy2(p,logs/('fixture_'+p.name))
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/STATE_INTERFERENCE_M29_PROGRESS.md',ROOT/'tools/interpret_m29_saved.py',ROOT/'tools/inspect_m29_saved_targets.py',ROOT/'tools/preserve_m29.py',ROOT/'tools/report_m29.py',Path(__file__).resolve()]
    files=dict(reg['files']);files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    local={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log','.jsonl') or p.name=='workflow_status.json')}
    assert storage()+1000000<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_development_mechanism_assay_and_all_job_audit',files=files,local_records=local,
        registration_commit=commit,source_priors=prior,science_executions=session['totals']['executions'],science_work=session['totals']['counted_work'],
        audited_jobs=audit['all_jobs_replayed'],whole_layouts=pres['whole_layouts'],new_layouts=0,development_only=True,
        no_evolution=True,no_combined_solver_claim=True,old_science_unchanged=True,next_phase_launched=False,
        storage_bytes_before_seal=storage(),disk_free_bytes=shutil.disk_usage(RUN).free,
        mutable_handoff='AGENTS.md intentionally excluded; future audits need NEW packets. Never overwrite old seals, failed artifacts or registered science.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M29 sealed',len(files),'files and',len(local),'local records',flush=True)


if __name__=='__main__':main()
