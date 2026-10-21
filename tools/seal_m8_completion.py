"""Seal M8 only after audited fixed assay and verified guarded backup."""
import sys,json,shutil,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_mechanism import ROOT,OUT,RUN,check,writej,sha

def main():
 config=check();assert not (OUT/'completion.json').exists()
 assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
 reg=json.loads((OUT/'registration.json').read_text());prior=json.loads((ROOT/'results/breeding_allocation/completion.json').read_text())
 for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
 freeze=json.loads((OUT/'panel_freeze.json').read_text());launch=json.loads((OUT/'launch.json').read_text())
 for commit,file in [(launch['registration_commit'],'registration.json'),(freeze['commit'],'panel.json.gz')]:
  subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
  assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/repair_mechanism/{file}'],cwd=ROOT)).hexdigest()==sha(OUT/file)
 session=json.loads((OUT/'session.json').read_text());audit=json.loads((OUT/'audit.json').read_text());summary=json.loads((OUT/'summary.json').read_text());pres=json.loads((OUT/'preservation.json').read_text())
 assert session['status']=='complete' and session['reason'] is None and audit['status']=='PASS' and pres['status']=='verified'
 assert session['usage']['uncertain_attempts']==0 and session['usage']['calls']<=config['call_cap'] and session['usage']['work']<=config['work_cap']
 assert session['wall_seconds']<=config['session_wall_seconds'] and audit['wall_seconds']<=1800
 assert audit['native_replays']==audit['independent_grades']==session['usage']['calls']
 for i,r in summary['models'].items():
  assert sum(v['bases'] for v in r['ordinary_length_strata'].values())==256
  assert sum(v['correct_both_poses'] for v in r['ordinary_length_strata'].values())==r['metrics']['ordinary_bases_both_poses']
 for name in ('journal','backup'):assert sha(ROOT/pres[name]['path'])==pres[name]['sha256']
 logs=OUT/'logs';assert not logs.exists();logs.mkdir()
 for p in RUN.glob('*.log'):shutil.copy2(p,logs/p.name)
 shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
 writej(OUT/'completion_details.json',dict(status='complete_audited',registration_commit=launch['registration_commit'],panel_commit=freeze['commit'],science=session,audit=audit,
  primary_repair_replication=summary['primary_repair_replication'],diagnostic_upstream_hits=summary['diagnostic_upstream_hits'],
  source_hashes_verified=len(reg['files']),prior_M7_completion_hashes_verified=len(prior['files']),whole_layouts=pres['whole_layouts'],
  no_evolution=True,no_mating=True,no_adaptive_selection=True,next_experiment_launched=False,heartbeat_created=False))
 files=dict(reg['files']);paths=[*OUT.rglob('*'),ROOT/'docs/REPAIR_MECHANISM_PROGRESS.md',ROOT/'tools/analyze_m8_saved.py',ROOT/'tools/report_m8.py',ROOT/'tools/preserve_m8.py',Path(__file__).resolve()]
 files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
 local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log') or p.name=='workflow_status.json')}
 storage=sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
 assert storage+500000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
 writej(OUT/'completion.json',dict(status='complete_audited',files=files,local_records=local,preserved_tree_bytes_before_seal=storage,disk_free_bytes=free,
  mutable_handoff='AGENTS.md intentionally excluded',future_audit='New output packets only; never raw-rerun sealed actions or overwrite original records.'))
 for p,h in files.items():assert sha(ROOT/p)==h,p
 print('M8 complete:',len(files),'sealed files;',storage,'preserved bytes before seal.')
if __name__=='__main__':main()
