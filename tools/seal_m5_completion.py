"""Seal audited M5 records; never rewrites a previous completion packet."""
import sys,json,shutil,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.holding_assay import ROOT,OUT,RUN,PRIOR,check,writej,sha


def main():
    config=check();assert not (OUT/'completion.json').exists()
    registration=json.loads((OUT/'registration.json').read_text());prior=json.loads((PRIOR/'completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    for commit,path in [('2bf9cc4','results/holding_assay/registration.json'),('63e367b','results/holding_assay/pool.json.gz'),('591870c','results/holding_assay/choices.json.gz')]:
        subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
        assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)).hexdigest()==sha(ROOT/path)
    sessions={n:json.loads((OUT/f'{n}_session.json').read_text()) for n in ('screen','final')}
    audits={n:json.loads((OUT/f'{n}_audit.json').read_text()) for n in ('screen','final')}
    for n in sessions:
        assert sessions[n]['status']=='complete' and sessions[n]['reason'] is None and audits[n]['status']=='PASS'
    total={k:sum(s['usage'][k] for s in sessions.values()) for k in sessions['screen']['usage']}
    wall=sum(s['wall_seconds'] for s in sessions.values())
    assert total['calls']<=config['call_cap'] and total['work']<=config['work_cap'] and wall<=config['session_wall_seconds']
    preservation=json.loads((OUT/'preservation.json').read_text())
    for s in preservation['stages'].values():
        for key in ('journal','backup'):assert sha(ROOT/s[key]['path'])==s[key]['sha256']
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in RUN.glob('*.log'):shutil.copy2(p,logs/p.name)
    summary=json.loads((OUT/'summary.json').read_text());strata=json.loads((OUT/'ordinary_length_strata.json').read_text())
    for i,ss in strata.items():
        assert sum(v['bases'] for v in ss.values())==256
        assert sum(v['correct'] for v in ss.values())==summary['all_metrics'][i]['ordinary_bases_both_poses']
    writej(OUT/'completion_details.json',dict(status='complete_audited',registration_commit='2bf9cc4',pool_commit='63e367b',choice_commit='591870c',
        scientific_usage=total,scientific_wall_seconds=wall,audits=audits,passing_nominee_aliases=summary['passing'],
        source_hashes_verified=len(registration['files']),prior_M4_hashes_verified=len(prior['files']),whole_layouts=preservation['whole_layouts'],
        no_continued_evolution=True,no_reselection=True,next_experiment_launched=False))
    files=dict(registration['files']);paths=[*OUT.rglob('*'),ROOT/'docs/HOLDING_ASSAY_PROGRESS.md',ROOT/'tools/analyze_m5_saved.py',ROOT/'tools/preserve_m5.py',Path(__file__).resolve()]
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
    local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix=='.sqlite' or p.suffix=='.log')}
    storage=sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
    assert storage+200000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_audited',files=files,local_records=local,preserved_tree_bytes_before_seal=storage,disk_free_bytes=free,
        mutable_handoff='AGENTS.md intentionally excluded',future_audit='Separate output packet required; do not overwrite registered/sealed reports or raw-rerun actions.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M5 complete:',len(files),'sealed files;',storage,'preserved bytes before seal.')

if __name__=='__main__':main()
