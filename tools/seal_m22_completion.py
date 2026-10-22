"""One-time M22 completion sealing after reviewed actual outcomes and backups."""
import json,hashlib,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.guarded_extension import ROOT,OUT,RUN,check,verify_prior,readz,writej,sha,load_layouts

def main():
    config=check();assert not (OUT/'completion.json').exists();prior=verify_prior()
    wf=json.loads((RUN/'workflow_status.json').read_text());assert wf['state']=='audited_ready_for_report' and all(s['code']==0 for s in wf['steps'])
    review=json.loads((OUT/'report_review.json').read_text());assert review['status']=='PASS' and review['report_sha256']==sha(OUT/'report.md')
    for receipt,file in [('launch.json','registration.json'),('pool_freeze.json','pool.json.gz'),('choices_freeze.json','choices.json.gz')]:
        rec=json.loads((OUT/receipt).read_text());commit=rec.get('commit',rec.get('registration_commit'))
        subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
        assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/guarded_extension/{file}'],cwd=ROOT)).hexdigest()==sha(OUT/file)
    sessions={k:json.loads((OUT/f'{k}_session.json').read_text()) for k in ('screen','final','trace')}
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in sessions};assert all(x['status']=='PASS' for x in audits.values())
    for phase in ('screen','final'):
        s=sessions[phase];a=audits[phase];u=s['usage'];assert s['status']=='complete' and s['reason'] is None and not u['uncertain_attempts']
        assert s['wall_seconds']<config['session_wall_seconds' if phase=='screen' else 'final_wall_seconds']
        assert s['rss_peak_bytes']<config['memory_bytes'] and a['wall_seconds']<config['audit_wall_seconds']
        assert u['calls']==a['independent_grades'] and u['calls']<=(config['call_cap'] if phase=='screen' else 1000000)
        assert u['work']<=(config['work_cap'] if phase=='screen' else 10**14)
    assert audits['final']['native_replays']==sessions['final']['usage']['calls']
    for r in (sessions['trace'],audits['trace']):
        assert r['calls']<=config['trace_call_cap'] and r['counted_work']<=config['trace_work_cap']
        assert r['wall_seconds']<config['trace_wall_seconds'] and r['rss_peak_bytes']<config['memory_bytes']
    assert sessions['trace']['calls']==audits['trace']['calls']
    d=json.loads((OUT/'saved_diagnostics.json').read_text());assert d['status']=='PASS'
    assert json.loads((OUT/'branch_usage.json').read_text())['status']=='PASS'
    for a,c in d['allocation'].items():assert c['proposals']==768 and c['opportunities']==3072
    p=json.loads((OUT/'preservation.json').read_text())
    for stage in p['stages'].values():
        assert sha(ROOT/stage['journal']['path'])==stage['journal']['sha256']
        e=stage['backup']
        if e['status']=='verified':assert sha(ROOT/e['path'])==e['sha256']
    assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==p['whole_layouts']
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for f in RUN.glob('*.log'):shutil.copy2(f,logs/f.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    reg=json.loads((OUT/'registration.json').read_text());files=dict(reg['files'])
    helpers=[ROOT/f'tools/{name}_m22{suffix}.py' for name,suffix in [('analyze','_saved'),('observe','_saved'),('sensitivity','_saved'),('preserve',''),('report','')]]
    paths=[*OUT.rglob('*'),ROOT/'docs/GUARDED_EXTENSION_PROGRESS.md',*helpers,Path(__file__).resolve()]
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
    local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log') or p.name=='workflow_status.json')}
    size=sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
    assert size+500000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_audited',phase='M22',files=files,local_records=local,prior=prior,
        registration_hashes=len(reg['files']),storage_bytes_before_seal=size,disk_free_bytes=free,
        independent_confirmation=True,next_experiment_launched=False,mutable_handoff='AGENTS.md excluded',
        future_audits='New output packets only; never overwrite failed or sealed records'))
    for path,h in files.items():assert sha(ROOT/path)==h,path
    print('M22 sealed',len(files),'files;',len(local),'local records;',size,'bytes')

if __name__=='__main__':main()
