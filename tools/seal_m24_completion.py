"""One-time M24 completion seal; originals and all old seals untouched."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.branch_causality import ROOT,OUT,RUN,check,writej,sha,prior_check,load_layouts

def main():
    config=check();assert not (OUT/'completion.json').exists();prior=prior_check()
    wf=json.loads((RUN/'workflow_status.json').read_text());assert wf['state']=='audited_ready_for_report' and all(s['code']==0 for s in wf['steps'])
    launch=json.loads((OUT/'launch.json').read_text());commit=launch['registration_commit']
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
    assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/branch_causality/registration.json'],cwd=ROOT)).hexdigest()==sha(OUT/'registration.json')
    review=json.loads((OUT/'report_review.json').read_text());assert review['status']=='PASS' and review['report_sha256']==sha(OUT/'report.md')
    audit=json.loads((OUT/'audit.json').read_text());ta=json.loads((OUT/'trace_audit.json').read_text());oa=json.loads((OUT/'observation_audit.json').read_text());session=json.loads((OUT/'session.json').read_text());trace=json.loads((OUT/'trace_session.json').read_text())
    assert audit['status']==ta['status']==oa['status']=='PASS'
    recurrence=json.loads((OUT/'readout_recurrence_audit.json').read_text())
    assert recurrence['status']=='PASS' and recurrence['new_inference_calls']==0
    assert oa['new_inference_calls']==0 and oa['wall_seconds']<config['trace_wall_seconds']
    assert session['status']=='complete' and session['reason'] is None and session['usage']['uncertain_attempts']==0
    assert session['usage']['calls']==audit['native_replays']==audit['independent_grades']==67200
    assert session['usage']['calls']<=config['call_cap'] and session['usage']['work']<=config['work_cap']
    assert session['wall_seconds']<config['session_wall_seconds'] and session['rss_peak_bytes']<config['memory_bytes']
    assert audit['wall_seconds']<config['audit_wall_seconds']
    for r in (ta,trace):
        assert r['calls']==240 and r['calls']<=config['trace_call_cap'] and r['counted_work']<=config['trace_work_cap']
        assert r['wall_seconds']<config['trace_wall_seconds'] and r['rss_peak_bytes']<config['memory_bytes']
    p=json.loads((OUT/'preservation.json').read_text())
    for field in ('journal','backup'):
        e=p['evaluation'][field]
        if field=='journal' or e['status']=='verified':assert sha(ROOT/e['path'])==e['sha256']
    assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==p['whole_layouts']==3742313 and p['new_layouts']==0
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for file in RUN.glob('*.log'):shutil.copy2(file,logs/file.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    reg=json.loads((OUT/'registration.json').read_text());files=dict(reg['files'])
    paths=[*OUT.rglob('*'),ROOT/'docs/BRANCH_CAUSALITY_PROGRESS.md',ROOT/'tools/interpret_m24_saved.py',ROOT/'tools/audit_m24_readout_saved.py',ROOT/'tools/review_m24.py',ROOT/'tools/preserve_m24.py',ROOT/'tools/report_m24.py',Path(__file__).resolve()]
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
    local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log') or p.name=='workflow_status.json')}
    size=sum(p.stat().st_size for b in (OUT,RUN) for p in b.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
    assert size+500000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_audited',phase='M24',files=files,local_records=local,prior=prior,
        registration_hashes=len(reg['files']),storage_bytes_before_seal=size,disk_free_bytes=free,new_layouts=0,
        independent_confirmation=False,next_experiment_launched=False,mutable_handoff='AGENTS.md excluded',future_audits='New packets only, never overwrite failed or sealed records'))
    for path,h in files.items():assert sha(ROOT/path)==h,path
    print('M24 completion sealed',len(files),'files;',len(local),'local records;',size,'bytes')

if __name__=='__main__':main()
