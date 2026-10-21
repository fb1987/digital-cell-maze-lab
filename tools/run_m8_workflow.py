"""Durable M8 fixed panel -> published freeze -> fresh assay -> full native audit."""
import json,os,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_mechanism import ROOT,OUT,RUN,check,pushed,writej
from maze_evolution.deep_campaign_store import writer_lock
PYTHON=str(ROOT/'.venv/bin/python')
def main():
 RUN.mkdir(parents=True,exist_ok=True)
 with writer_lock(RUN/'workflow'):
  assert not (RUN/'workflow_status.json').exists(),'Never launch a duplicate or silently resume a failed workflow'
  check();pushed(OUT/'registration.json')
  status=dict(pid=os.getpid(),started_epoch=time.time(),state='running',phase='starting',steps=[])
  def save():writej(RUN/'workflow_status.json',status)
  def command(phase,action):
   status.update(phase=phase,state='running');save()
   with (RUN/f'{phase}.log').open('x') as f:
    p=subprocess.Popen([PYTHON,'-u','-m','maze_evolution.repair_mechanism',action],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    status['child_pid']=p.pid;save();code=p.wait()
   status['steps'].append(dict(phase=phase,returncode=code,ended_epoch=time.time()));status.pop('child_pid',None);save()
   if code:raise RuntimeError(f'{phase} exited {code}; preserve logs, no automatic repair')
  def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
  save()
  try:
   command('panel_001','panel');assert not git('diff','--cached','--name-only')
   git('add','--',str(OUT/'panel.json.gz'),str(OUT/'panel_counts.json'));git('commit','-m','Freeze M8 diagnostic panel before fresh cases');git('push');pushed(OUT/'panel.json.gz')
   writej(OUT/'panel_freeze.json',dict(commit=git('rev-parse','HEAD'),pushed=True,epoch=time.time(),fresh_cases_generated=False))
   command('assay_001','run');assert json.loads((OUT/'session.json').read_text())['status']=='complete'
   command('analysis_001','analyze');command('audit_001','audit');assert json.loads((OUT/'audit.json').read_text())['status']=='PASS'
   status.update(state='audited_ready_for_report',phase='report_backup_seal',ended_epoch=time.time());save()
  except BaseException:
   failure=traceback.format_exc();print(failure,flush=True);status.update(state='failed',failure=failure,ended_epoch=time.time());save();raise
if __name__=='__main__':main()
