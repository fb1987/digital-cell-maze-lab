"""One-time M11 completion seal after reviewed report and verified preservation."""
import sys,json,subprocess,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.retention_bank import ROOT,OUT,RUN,check,sha,writej,load_layouts

def main():
 c=check();assert not (OUT/'completion.json').exists();assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
 reg=json.loads((OUT/'registration.json').read_text());old=json.loads((ROOT/'results/retention_pressure/completion.json').read_text());assert len(reg['files'])==312 and len(old['files'])==356
 for p,h in old['files'].items():assert sha(ROOT/p)==h,p
 freeze=json.loads((OUT/'bank_freeze.json').read_text())
 for commit,name in [('13d94e2','registration.json'),(freeze['commit'],'calibration_freeze.json.gz')]:
  subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],check=True,cwd=ROOT)
  assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/retention_bank/{name}'],cwd=ROOT)).hexdigest()==sha(OUT/name)
 sessions={k:json.loads((OUT/f'{k}_session.json').read_text()) for k in ('calibration','final')};audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in sessions}
 for k,s in sessions.items():
  assert s['status']=='complete' and s['wall_seconds']<c['session_wall_seconds'] and s['usage']['uncertain_attempts']==0
  assert audits[k]['status']=='PASS' and audits[k]['all_native_replays']==s['usage']['calls'] and audits[k]['wall_seconds']<1800
 p=json.loads((OUT/'preservation.json').read_text());assert p['status']=='verified'
 for k in ('journal','backup'):assert sha(ROOT/p[k]['path'])==p[k]['sha256']
 assert sum(s['usage']['calls'] for s in sessions.values())==p['usage']['calls']<=c['call_cap']
 assert sum(s['usage']['work'] for s in sessions.values())==p['usage']['work']<=c['work_cap']
 assert len(load_layouts(OUT/'whole_layout_exclusions.json'))==p['whole_layouts']
 assert (OUT/'report.md').exists() and (OUT/'diagnostics.json').exists()
 logs=OUT/'logs';assert not logs.exists();logs.mkdir()
 for f in RUN.glob('*.log'):shutil.copy2(f,logs/f.name)
 shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
 summary=json.loads((OUT/'summary.json').read_text())
 writej(OUT/'completion_details.json',dict(status='complete_audited',registration_commit='13d94e2',bank_freeze_commit=freeze['commit'],source_files=len(reg['files']),prior_M10_hashes=len(old['files']),
  scientific_usage=p['usage'],scientific_wall_seconds=sum(s['wall_seconds'] for s in sessions.values()),audit_wall_seconds=sum(a['wall_seconds'] for a in audits.values()),
  descriptive_bank_support=summary['descriptive_bank_support'],ready_for_new_protocol=summary['ready_for_new_protocol'],no_evolution=True,no_reselection=True,whole_layouts=p['whole_layouts'],next_phase_launched=False,heartbeat_created=False))
 files=dict(reg['files']);paths=[*OUT.rglob('*'),ROOT/'docs/RETENTION_BANK_PROGRESS.md',ROOT/'tools/preserve_m11.py',ROOT/'tools/report_m11.py',Path(__file__).resolve()]
 files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
 local={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log') or p.name=='workflow_status.json')}
 storage=sum(p.stat().st_size for b in (OUT,RUN) for p in b.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
 assert storage+1000000<c['storage_bytes'] and free>=c['disk_free_floor_bytes']
 writej(OUT/'completion.json',dict(status='complete_audited',files=files,local_records=local,storage_bytes_before_seal=storage,disk_free_bytes=free,mutable_handoff='AGENTS.md excluded',future_audits='New packets only; never overwrite seals or failed records.'))
 for p,h in files.items():assert sha(ROOT/p)==h,p
 print('M11 sealed',len(files),'files and',len(local),'local records')
if __name__=='__main__':main()
