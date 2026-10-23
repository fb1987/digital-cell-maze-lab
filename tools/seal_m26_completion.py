"""Seal the new M26 saved-analysis packet once, leaving all older records intact."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/evolvability_audit_m26'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()


def main():
    assert not (OUT/'completion.json').exists()
    reg=json.loads((OUT/'registration.json').read_text())
    for p,h in reg['files'].items():assert sha(ROOT/p)==h,p
    launch=json.loads((OUT/'launch.json').read_text())
    commit=launch['registration_commit']
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
    assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/evolvability_audit_m26/registration.json'],cwd=ROOT)).hexdigest()==sha(OUT/'registration.json')
    old=json.loads((ROOT/'results/skill_integration/completion.json').read_text())
    assert sha(ROOT/'results/skill_integration/completion.json')==reg['M25_completion_sha256']
    for p,h in old['files'].items():assert sha(ROOT/p)==h,p
    for p,r in old['local_records'].items():
        assert (ROOT/p).stat().st_size==r['bytes'] and sha(ROOT/p)==r['sha256'],p
    s=json.loads((OUT/'summary.json').read_text());v=json.loads((OUT/'verification.json').read_text())
    w=json.loads((OUT/'witness_review.json').read_text());r=json.loads((OUT/'report_review.json').read_text())
    inter=json.loads((OUT/'interpretation.json').read_text())
    assert v['status']==w['status']==r['status']=='PASS'
    assert r['report_sha256']==sha(OUT/'report.md')
    assert s['input_integrity_before']==s['input_integrity_after']
    assert s['input_integrity_before']['completion_sha256']==reg['M25_completion_sha256']
    assert v['first_training_exposures_verified']==99216 and v['births_verified']==99528
    assert v['novel_hit_presentations_verified']==s['novel_hit_presentations']==337
    assert w['all_saved_novel_child_rasters_validated']==60
    assert w['groups']['changed_mutants_only']['identities']==28
    assert w['groups']['changed_mutants_only']['direct_offspring_after_hit']==35
    assert inter['complete8']['episodes_retaining_no_solver']==0
    assert r['rare_variant_final_exact_genotype_matches']==0
    assert s['search_physical_calls_verified']==24388480
    costs=[s['analysis_cost'],v,inter['costs'],w['costs']]
    assert all(c['inference_calls']==c['generated_layouts']==0 and c['wall_seconds']<1800 and c['peak_rss_bytes']<4*1024**3 for c in costs)
    free=shutil.disk_usage(OUT).free
    size=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    assert free>=16*1024**3 and size+1000000<512*1024**2
    paths=[p for p in OUT.rglob('*') if p.is_file()]
    paths += [ROOT/'docs/EVOLVABILITY_AUDIT_M26.md',ROOT/'docs/EVOLVABILITY_AUDIT_M26_PROGRESS.md',
       ROOT/'tools/m26_saved_metrics.py',ROOT/'tools/audit_m26_training.py',ROOT/'tools/verify_m26_training.py',
       ROOT/'tools/interpret_m26_saved.py',ROOT/'tools/review_m26_witnesses.py',Path(__file__).resolve(),
       ROOT/'tests/test_m26_saved_metrics.py']
    assert not any(p.suffix=='.sqlite' for p in paths)
    value=dict(status='complete_saved_only_audited',registration_commit=commit,
       created_unix=time.time(),files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},
       old_M25_files_verified=len(old['files']),old_M25_local_records_verified=len(old['local_records']),
       original_search_journal_sha256=s['input_integrity_after']['search_journal_sha256'],
       packet_bytes_before_seal=size,disk_free_bytes=free,
       total_recorded_scan_wall_seconds=sum(c['wall_seconds'] for c in costs),
       total_recorded_scan_cpu_seconds=sum(c['cpu_seconds'] for c in costs),
       peak_recorded_rss_bytes=max(c['peak_rss_bytes'] for c in costs),
       inference_calls=0,generated_layouts=0,new_evolution=False,next_phase_launched=False,
       scope='Posthoc saved training development data; native correctness relies on preserved original PASS audits plus 60 independent raster geometry checks.',
       mutable_handoff='AGENTS.md intentionally excluded. New audits require new packets; never overwrite this seal or older records.')
    with (OUT/'completion.json').open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({k:v for k,v in value.items() if k!='files'},indent=2))


if __name__=='__main__':main()
