"""Seal completed M4 evidence without changing any prior scientific packet."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mechanism_retention import ROOT,OUT,RUN,check,writej,sha


def main():
    config=check();assert not (OUT/'completion.json').exists()
    prior=json.loads((ROOT/'results/wave_continuation/completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
    registration=json.loads((OUT/'registration.json').read_text())
    subprocess.run(['git','merge-base','--is-ancestor','c4608da','origin/main'],cwd=ROOT,check=True)
    for commit,path in [('305c068','results/mechanism_retention/registration.json'),('c4608da','results/mechanism_retention/panel.json.gz')]:
        data=subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
        assert hashlib.sha256(data).hexdigest()==sha(ROOT/path)
    session=json.loads((OUT/'session.json').read_text());assert session['status']=='complete' and session['reason'] is None
    audit=json.loads((OUT/'audit.json').read_text());assert audit['status']=='PASS'
    summary=json.loads((OUT/'summary.json').read_text());strata=json.loads((OUT/'ordinary_length_strata.json').read_text())
    for i,groups in strata.items():
        assert sum(v['bases'] for v in groups.values())==256
        assert sum(v['correct'] for v in groups.values())==summary['models'][i]['metrics']['ordinary_bases_both_poses']
    preservation=json.loads((OUT/'preservation.json').read_text())
    for key in ('journal','backup'):
        p=preservation[key];assert sha(ROOT/p['path'])==p['sha256']
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for n in ('evaluation.log','analysis.log','audit.log'):shutil.copy2(RUN/n,logs/n)
    writej(OUT/'completion_details.json',dict(status='complete_audited',registration_commit='305c068',panel_freeze_commit='c4608da',
        science=session,audit=audit,reference_eligibility=summary['reference_eligibility'],diagnostic_hits=summary['qualified_diagnostic_hits'],
        whole_layouts=preservation['whole_layouts'],new_layouts=preservation['new_layouts'],
        no_evolution=True,no_mating=True,no_adaptive_selection=True,next_experiment_launched=False,
        source_hashes_verified=len(registration['files']),prior_M3_completion_hashes_verified=len(prior['files']),
        report_helper_checks='All 546 ordinary-stratum denominators equal 256; numerators match registered audited summary.',
        next_proposal='Separately register a matched accessibility pilot of generic conditional state-holding writes; preserve old behavior and random-origin provenance.'))
    files=dict(registration['files'])
    paths=[*OUT.rglob('*'),ROOT/'docs/MECHANISM_RETENTION_PROGRESS.md',ROOT/'tools/analyze_m4_saved.py',ROOT/'tools/preserve_m4.py',Path(__file__).resolve()]
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
    local_paths=[RUN/'campaign.sqlite',RUN/'backups/completed.sqlite',*sorted((RUN/'reporting_initial').glob('*.json')),*sorted(RUN.glob('*.log'))]
    local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in local_paths}
    storage=sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())
    free=shutil.disk_usage(RUN).free
    assert storage+200000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_audited',files=files,local_records=local,
        preserved_tree_bytes_before_seal=storage,disk_free_bytes=free,
        mutable_handoff='AGENTS.md intentionally excluded from immutable hashes; scientific reports/protocol/progress sealed.',
        future_audit='Use a separate output path; never overwrite this packet or rerun raw registered actions over it.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M4 complete:',len(files),'sealed files;',len(local),'local records;',storage,'preserved bytes before seal.')


if __name__=='__main__':main()
