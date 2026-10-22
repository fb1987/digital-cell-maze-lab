"""One-time M17 completion seal; requires reviewed report and verified preservation."""
import json,hashlib,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.spare_state_assay import ROOT,OUT,RUN,check,sha,writej,verify_prior


def main():
    config=check();assert not (OUT/'completion.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    assert (OUT/'report.md').exists() and (OUT/'interpretation.json').exists()
    prior=verify_prior();reg=json.loads((OUT/'registration.json').read_text())
    for receipt,file in [('launch.json','registration.json'),('pool_freeze.json','pool.json.gz'),('choices_freeze.json','choices.json.gz')]:
        p=json.loads((OUT/receipt).read_text());commit=p.get('commit',p.get('registration_commit'))
        subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],check=True,cwd=ROOT)
        assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/spare_state_assay/{file}'],cwd=ROOT)).hexdigest()==sha(OUT/file)
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in ('screen','final')}
    assert all(x['status']=='PASS' for x in audits.values())
    sessions={k:json.loads((OUT/f'{k}_session.json').read_text()) for k in ('screen','final')}
    for k,x in sessions.items():
        assert x['status']=='complete' and x['reason'] is None and x['usage']['uncertain_attempts']==0
        assert x['wall_seconds']<=config['session_wall_seconds' if k=='screen' else 'final_wall_seconds']
        assert x['rss_peak_bytes']<config['memory_bytes'] and audits[k]['wall_seconds']<=config['audit_wall_seconds']
        assert audits[k]['independent_grades']==x['usage']['calls']
    totals={k:sum(x['usage'][k] for x in sessions.values()) for k in sessions['screen']['usage']}
    assert totals['calls']<=config['call_cap'] and totals['work']<=config['work_cap']
    preservation=json.loads((OUT/'preservation.json').read_text())
    for s in preservation['stages'].values():
        assert sha(ROOT/s['journal']['path'])==s['journal']['sha256']
        if s['backup']['status']=='verified':assert sha(ROOT/s['backup']['path'])==s['backup']['sha256']
    assert preservation['status'] in ('verified','originals_verified_backups_partially_blocked')
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in RUN.glob('*.log'):shutil.copy2(p,logs/p.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    writej(OUT/'completion_details.json',dict(status='complete_audited',usage=totals,
       registration_hashes=len(reg['files']),prior_M16_hashes=len(prior['files']),prior_M16_local_records=len(prior['local_records']),
       no_reselection=True,next_experiment_launched=False,whole_layouts=preservation['whole_layouts']))
    files=dict(reg['files']);paths=[*OUT.rglob('*'),ROOT/'docs/SPARE_STATE_ASSAY_PROGRESS.md',ROOT/'tools/preserve_m17.py',ROOT/'tools/report_m17.py',ROOT/'tools/analyze_m17_saved.py',Path(__file__).resolve()]
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
    local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log') or p.name=='workflow_status.json')}
    size=sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
    assert size+500000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_audited',files=files,local_records=local,preserved_tree_bytes_before_seal=size,
       disk_free_bytes=free,mutable_handoff='AGENTS.md excluded',future_audit='New output packet only; never overwrite sealed actions or failed records.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M17 completion sealed:',len(files),'files;',size,'preserved bytes.')


if __name__=='__main__':main()
