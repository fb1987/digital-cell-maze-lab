"""One-time M6 completion seal after audited confirmation and guarded preservation."""
import sys,json,shutil,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.upstream_continuation import ROOT,OUT,RUN,check,writej,sha

def main():
    config=check();assert not (OUT/'completion.json').exists()
    assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
    reg=json.loads((OUT/'registration.json').read_text());prior=json.loads((ROOT/'results/holding_assay/completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    for commit,file in [('929150f','registration.json'),('e50da65','choices.json.gz')]:
        subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
        assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/upstream_continuation/{file}'],cwd=ROOT)).hexdigest()==sha(OUT/file)
    sessions={'search':json.loads((OUT/'session.json').read_text()),'final':json.loads((OUT/'final_session.json').read_text())}
    audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in sessions}
    for k,s in sessions.items():
        assert s['status']=='complete' and s['reason'] is None and audits[k]['status']=='PASS'
        assert s['wall_seconds']<=config['session_wall_seconds'] and s['usage']['uncertain_attempts']==0
    assert sessions['search']['usage']['calls']<=config['call_cap'] and sessions['search']['usage']['work']<=config['work_cap']
    assert sessions['final']['usage']['calls']<=1000000 and sessions['final']['usage']['work']<=10**14
    preservation=json.loads((OUT/'preservation.json').read_text());assert preservation['status']=='verified'
    for s in preservation['stages'].values():
        for k in ('journal','backup'):assert sha(ROOT/s[k]['path'])==s[k]['sha256']
    attempt=json.loads((OUT/'preservation_attempt_001/note.json').read_text())
    assert sha(ROOT/attempt['backup_preserved'])==attempt['backup_sha256'],'Existing first backup must never be overwritten'
    summary=json.loads((OUT/'summary.json').read_text());diagnostics=json.loads((OUT/'saved_diagnostics.json').read_text())
    for i,ss in summary['ordinary_length_strata'].items():
        assert sum(v['bases'] for v in ss.values())==256
        assert sum(v['correct_both_poses'] for v in ss.values())==summary['all_models'][i]['ordinary_bases_both_poses']
    assert sum(diagnostics['birth_counts'].values())==audits['search']['births_replayed']==280176
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in RUN.glob('*.log'):shutil.copy2(p,logs/p.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    total={k:sum(s['usage'][k] for s in sessions.values()) for k in sessions['search']['usage']}
    writej(OUT/'completion_details.json',dict(status='complete_audited',registration_commit='929150f',choice_commit='e50da65',
        scientific_usage=total,scientific_wall_seconds=sum(s['wall_seconds'] for s in sessions.values()),audits=audits,
        source_hashes_verified=len(reg['files']),prior_M5_hashes_verified=len(prior['files']),whole_layouts=preservation['whole_layouts'],
        acquisition_gate_passes={k:sum(bool(c[k]) for c in summary['conditions']) for k in ('upstream_acquisition','long_ordinary_acquisition','combined_transfer')},
        preservation_helper_correction='preservation_attempt_001/note.json; unregistered operational helper only, no scientific or audit change',
        no_reselection=True,next_experiment_launched=False,heartbeat_status='PAUSED'))
    files=dict(reg['files']);paths=[*OUT.rglob('*'),ROOT/'docs/UPSTREAM_CONTINUATION_PROGRESS.md',ROOT/'tools/analyze_m6_saved.py',ROOT/'tools/preserve_m6.py',Path(__file__).resolve()]
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
    local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log') or p.name=='workflow_status.json')}
    storage=sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
    assert storage+300000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_audited',files=files,local_records=local,preserved_tree_bytes_before_seal=storage,disk_free_bytes=free,
        mutable_handoff='AGENTS.md intentionally excluded',future_audit='Use separate output packets; never raw-rerun sealed actions or overwrite failed records.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M6 complete:',len(files),'sealed files;',storage,'preserved bytes before seal.')
if __name__=='__main__':main()
