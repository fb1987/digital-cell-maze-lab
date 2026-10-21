"""Durable M14 search -> published choices -> audits -> untouched confirmation.

Stops on any error/guard. Does not extend budgets or automatically repair/resume.
Completion reporting, backups and sealing are performed by the follow-up monitor.
"""
import json,os,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.exploration_allocation import ROOT,OUT,RUN,check,pushed,writej
from maze_evolution.deep_campaign_store import writer_lock

PYTHON=str(ROOT/'.venv/bin/python')

def main():
    RUN.mkdir(parents=True,exist_ok=True)
    with writer_lock(RUN/'workflow'):
        assert not (RUN/'workflow_status.json').exists(),'Existing workflow: inspect, never start a duplicate.'
        check();pushed(OUT/'registration.json')
        status=dict(pid=os.getpid(),started_epoch=time.time(),state='running',phase='starting',steps=[])
        def save():writej(RUN/'workflow_status.json',status)
        def command(phase,args):
            status.update(phase=phase,state='running');save()
            log=RUN/f'{phase}.log'
            with log.open('x') as f:
                p=subprocess.Popen(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
                status['child_pid']=p.pid;save();code=p.wait()
            status['steps'].append(dict(phase=phase,returncode=code,ended_epoch=time.time(),log=str(log.relative_to(ROOT))))
            status.pop('child_pid',None);save()
            if code:raise RuntimeError(f'{phase} exited {code}; preserved {log}')
        def git(*args):
            return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
        save()
        try:
            command('search_001',[PYTHON,'-u','-m','maze_evolution.exploration_allocation','run'])
            assert json.loads((OUT/'session.json').read_text())['status']=='complete','Search checkpointed at a guard; no automatic extension.'
            status['phase']='publishing_frozen_choices';save()
            paths=[str(OUT/name) for name in ('choices.json.gz','ancestry.json.gz','final_states.json.gz','search_exclusions.json','search_exclusions.delta.json.gz','validation.json.gz','session.json')]
            assert not git('diff','--cached','--name-only'),'Unexpected staged files; preserve for inspection.'
            git('add','--',*paths);git('commit','-m','Freeze M14 nominees and ancestry before independent confirmation');git('push')
            pushed(OUT/'choices.json.gz')
            writej(OUT/'choices_freeze.json',dict(commit=git('rev-parse','HEAD'),pushed=True,epoch=time.time(),independent_confirmation_generated=False))
            command('search_audit_001',[PYTHON,'-u','-m','maze_evolution.exploration_allocation_analysis','audit_search'])
            assert json.loads((OUT/'search_audit.json').read_text())['status']=='PASS'
            command('confirmation_001',[PYTHON,'-u','-m','maze_evolution.exploration_allocation_analysis','final'])
            assert json.loads((OUT/'final_session.json').read_text())['status']=='complete','Final checkpointed at guard.'
            command('analysis_001',[PYTHON,'-u','-m','maze_evolution.exploration_allocation_analysis','analyze'])
            command('final_audit_001',[PYTHON,'-u','-m','maze_evolution.exploration_allocation_analysis','audit_final'])
            assert json.loads((OUT/'final_audit.json').read_text())['status']=='PASS'
            status.update(state='audited_ready_for_report',phase='report_backup_seal',ended_epoch=time.time());save()
            print('M14 AUDITS PASS: ready for reviewed report, guarded backups and completion seal.',flush=True)
        except BaseException:
            failure=traceback.format_exc();print(failure,flush=True)
            status.update(state='failed',failure=failure,ended_epoch=time.time());save()
            raise

if __name__=='__main__':main()
