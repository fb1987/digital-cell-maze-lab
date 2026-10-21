"""Durable M11: calibration, published bank freeze, audit, untouched test, audit."""
import sys,json,os,time,subprocess,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.retention_bank import ROOT,OUT,RUN,check,pushed,writej
from maze_evolution.deep_campaign_store import writer_lock

def main():
 RUN.mkdir(exist_ok=True)
 with writer_lock(RUN/'workflow'):
  assert not (RUN/'workflow_status.json').exists();check();pushed(OUT/'registration.json')
  state=dict(pid=os.getpid(),state='running',phase='starting',started_epoch=time.time(),steps=[])
  def save():writej(RUN/'workflow_status.json',state)
  def command(name,action):
   state['phase']=name;save()
   with (RUN/(name+'.log')).open('x') as log:
    p=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-u','-m','maze_evolution.retention_bank',action],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT);state['child_pid']=p.pid;save();code=p.wait()
   state.pop('child_pid');state['steps'].append(dict(phase=name,code=code,ended_epoch=time.time()));save()
   assert code==0,(name,code)
  def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
  save()
  try:
   command('calibration_001','calibrate')
   assert not git('diff','--cached','--name-only')
   paths=[str(OUT/p) for p in ('calibration_freeze.json.gz','calibration_session.json','calibration_exclusions.json','calibration_exclusions_parts')]
   git('add','--',*paths);git('commit','-m','Freeze M11 reference-conditioned banks and predictions before independent testing');git('push');pushed(OUT/'calibration_freeze.json.gz')
   writej(OUT/'bank_freeze.json',dict(commit=git('rev-parse','HEAD'),pushed=True,epoch=time.time(),independent_cases_generated=False,no_model_selection=True))
   command('calibration_audit_001','audit_calibration');assert json.loads((OUT/'calibration_audit.json').read_text())['status']=='PASS'
   command('confirmation_001','final');command('analysis_001','analyze');command('final_audit_001','audit_final')
   assert json.loads((OUT/'final_audit.json').read_text())['status']=='PASS'
   state.update(state='audited_ready_for_report',phase='report_backup_seal',ended_epoch=time.time());save()
  except BaseException:
   state.update(state='failed',failure=traceback.format_exc(),ended_epoch=time.time());save();raise
if __name__=='__main__':main()
