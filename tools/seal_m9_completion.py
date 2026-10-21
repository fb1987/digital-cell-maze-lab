"""One-time M9 completion seal; no scientific regeneration or reselection."""
import sys,json,shutil,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.conditional_regulation import ROOT,OUT,RUN,check,writej,sha,readz

def main():
 config=check();assert not (OUT/'completion.json').exists()
 assert json.loads((RUN/'workflow_status.json').read_text())['state']=='audited_ready_for_report'
 reg=json.loads((OUT/'registration.json').read_text());prior=json.loads((ROOT/'results/repair_mechanism/completion.json').read_text())
 for p,h in prior['files'].items():assert sha(ROOT/p)==h,p
 assert len(prior['files'])==326 and len(reg['files'])==310
 freeze=json.loads((OUT/'choices_freeze.json').read_text())
 for commit,file in [('7d1199a','registration.json'),(freeze['commit'],'choices.json.gz')]:
  subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
  assert hashlib.sha256(subprocess.check_output(['git','show',f'{commit}:results/conditional_regulation/{file}'],cwd=ROOT)).hexdigest()==sha(OUT/file)
 sessions={k:json.loads((OUT/n).read_text()) for k,n in [('search','session.json'),('final','final_session.json')]}
 audits={k:json.loads((OUT/f'{k}_audit.json').read_text()) for k in sessions}
 for k,s in sessions.items():
  assert s['status']=='complete' and s['reason'] is None and audits[k]['status']=='PASS'
  assert s['wall_seconds']<=(config['session_wall_seconds'] if k=='search' else 900) and s['usage']['uncertain_attempts']==0
  assert audits[k]['wall_seconds']<=1800
 assert sessions['search']['usage']['calls']<=config['call_cap'] and sessions['search']['usage']['work']<=config['work_cap']
 assert sessions['final']['usage']['calls']<=1000000 and sessions['final']['usage']['work']<=10**14
 preservation=json.loads((OUT/'preservation.json').read_text());assert preservation['status']=='verified'
 for s in preservation['stages'].values():
  for k in ('journal','backup'):assert sha(ROOT/s[k]['path'])==s[k]['sha256']
 summary=json.loads((OUT/'summary.json').read_text());d=json.loads((OUT/'saved_diagnostics.json').read_text())
 for i,ss in summary['ordinary_length_strata'].items():
  assert sum(v['bases'] for v in ss.values())==256
  assert sum(v['correct_both_poses'] for v in ss.values())==summary['all_models'][i]['ordinary_bases_both_poses']
  assert d['model_details'][i]['length16plus_bases']==sum(v['bases'] for k,v in ss.items() if k.endswith('/long'))
 assert sum(d['birth_counts'].values())==audits['search']['births_replayed']==6*52*sessions['search']['generation']
 assert len(set(tuple(sorted(v.items())) for v in audits['search']['logical_query_counts'].values()))==1
 assert audits['final']['native_replays']==sessions['final']['usage']['calls']
 assert sessions['search']['generation']<=config['max_rounds']
 assert (OUT/'report.md').exists()
 logs=OUT/'logs';assert not logs.exists();logs.mkdir()
 for p in RUN.glob('*.log'):shutil.copy2(p,logs/p.name)
 shutil.copy2(RUN/'workflow_status.json',OUT/'completed_workflow_status.json')
 total={k:sum(s['usage'][k] for s in sessions.values()) for k in sessions['search']['usage']}
 writej(OUT/'completion_details.json',dict(status='complete_audited',registration_commit='7d1199a',choice_commit=freeze['commit'],scientific_usage=total,
  scientific_wall_seconds=sum(s['wall_seconds'] for s in sessions.values()),audits=audits,source_hashes_verified=len(reg['files']),prior_M8_hashes_verified=len(prior['files']),
  whole_layouts=preservation['whole_layouts'],policy_comparison=summary['policy_comparison'],
  acquisition_gate_passes={k:sum(bool(c[k]) for c in summary['conditions']) for k in ('upstream_acquisition','long_ordinary_acquisition','combined_transfer')},
  integration_gate_passes=sum(c['integration']['integration_pass'] for c in summary['conditions']),no_reselection=True,next_experiment_launched=False,heartbeat_created=False))
 files=dict(reg['files']);paths=[*OUT.rglob('*'),ROOT/'docs/CONDITIONAL_REGULATION_PROGRESS.md',ROOT/'tools/analyze_m9_saved.py',ROOT/'tools/report_m9.py',ROOT/'tools/preserve_m9.py',Path(__file__).resolve()]
 files.update({str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()})
 local={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in RUN.rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.log') or p.name=='workflow_status.json')}
 storage=sum(p.stat().st_size for b in (RUN,OUT) for p in b.rglob('*') if p.is_file());free=shutil.disk_usage(RUN).free
 assert storage+500000<config['storage_bytes'] and free>=config['disk_free_floor_bytes']
 writej(OUT/'completion.json',dict(status='complete_audited',files=files,local_records=local,preserved_tree_bytes_before_seal=storage,disk_free_bytes=free,
  mutable_handoff='AGENTS.md intentionally excluded',future_audit='Separate output packets; never overwrite sealed actions, original reports or failed records.'))
 for p,h in files.items():assert sha(ROOT/p)==h,p
 print('M9 complete:',len(files),'sealed files;',storage,'preserved bytes before seal.')
if __name__=='__main__':main()
