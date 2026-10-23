"""Seal M27 exactly once after audit, reviewed report and guarded preservation."""
import json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.transfer_retention import ROOT,OUT,RUN,check,prior_check,readz,writej,sha,storage
from maze_evolution.referenced_campaign_store import load_layouts


def main():
    config=check();assert not (OUT/'completion.json').exists()
    status=json.loads((RUN/'workflow_status.json').read_text());assert status['state']=='audited_ready_for_report'
    review=json.loads((OUT/'report_review.json').read_text());assert review['status']=='PASS' and review['report_sha256']==sha(OUT/'report.md')
    reg=json.loads((OUT/'registration.json').read_text());launch=json.loads((OUT/'launch.json').read_text());commit=launch['registration_commit']
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
    import hashlib
    for file in ('registration.json','pool.json.gz'):
        assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/transfer_retention_m27/{file}'],cwd=ROOT)).hexdigest()==sha(OUT/file)
    assert sha(OUT/'pool.json.gz')==launch['pool_frozen_sha256']
    s=json.loads((OUT/'session.json').read_text());a=json.loads((OUT/'audit.json').read_text());summary=json.loads((OUT/'summary.json').read_text())
    assert s['status']=='complete' and s['reason'] is None and s['usage']['uncertain_attempts']==0
    assert s['wall_seconds']<config['session_wall_seconds'] and a['wall_seconds']<config['audit_wall_seconds']
    assert s['rss_peak_bytes']<config['memory_bytes'] and a['rss_peak_bytes']<config['memory_bytes']
    assert s['usage']['calls']<=config['call_cap'] and s['usage']['work']<=config['work_cap']
    assert a['all_native_replays']==a['independent_grades']==s['usage']['calls']==410650
    assert a['counted_work']==s['usage']['work'] and a['status']=='PASS' and a['all_controls_correct']
    assert a['conventional_calls']==6450 and a['source_prior_hashes']==prior_check()
    assert summary['primary']['identities']==28 and len(summary['conditions'])==30 and len(summary['offspring'])==39
    preservation=json.loads((OUT/'preservation.json').read_text());entry=preservation['evaluation']
    assert sha(ROOT/entry['journal']['path'])==entry['journal']['sha256']
    if entry['backup']['status']=='verified':assert sha(ROOT/entry['backup']['path'])==entry['backup']['sha256']
    assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==preservation['whole_layouts']==3978849
    for p,r in json.loads((OUT/'preparation_local_records.json').read_text()).items():
        assert sha(ROOT/p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes'],p
    assert json.loads((OUT/'control_reference_check.json').read_text())['status']=='PASS'
    assert not json.loads((OUT/'control_reference_check.json').read_text())['historical_aliases_with_intact_control_genotype']
    logs=OUT/'logs';assert not logs.exists();logs.mkdir()
    for p in [*RUN.glob('*.log'),*RUN.glob('*.jsonl')]:shutil.copy2(p,logs/p.name)
    shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
    paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/TRANSFER_RETENTION_M27_PROGRESS.md',ROOT/'tools/preserve_m27.py',ROOT/'tools/analyze_m27_saved.py',ROOT/'tools/inspect_m27_counterposes.py',Path(__file__).resolve()]
    files=dict(reg['files']);files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    local={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log','.jsonl') or p.name=='workflow_status.json')}
    assert storage()+1000000<config['storage_bytes'] and shutil.disk_usage(RUN).free>=config['disk_free_floor_bytes']
    writej(OUT/'completion.json',dict(status='complete_independently_evaluated_and_audited',registration_commit=commit,
       files=files,local_records=local,primary=summary['primary'],source_priors=prior_check(),
       scientific_usage=s['usage'],audit_native_calls=a['all_native_replays'],conventional_calls=a['conventional_calls'],
       whole_layouts=preservation['whole_layouts'],storage_bytes_before_seal=storage(),disk_free_bytes=shutil.disk_usage(RUN).free,
       no_evolution=True,no_reselection=True,old_histories_unchanged=True,next_phase_launched=False,
       mutable_handoff='AGENTS.md excluded intentionally; future audits require NEW output packets. Do not overwrite seals, failed artifacts or frozen science.'))
    for p,h in files.items():assert sha(ROOT/p)==h,p
    print('M27 sealed',len(files),'files and',len(local),'local records',flush=True)


if __name__=='__main__':main()
