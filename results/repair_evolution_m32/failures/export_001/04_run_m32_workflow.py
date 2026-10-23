"""Single durable M32 workflow; no automatic failed-action resume."""
import json,os,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_evolution_m32 import ROOT,OUT,RUN,check,pushed,writej,sha
from maze_evolution.deep_campaign_store import writer_lock

def main():
    with writer_lock(RUN/'workflow'):
        assert not (RUN/'workflow_status.json').exists();check();pushed(OUT/'registration.json')
        status=dict(pid=os.getpid(),state='running',started_epoch=time.time(),steps=[])
        def save():writej(RUN/'workflow_status.json',status)
        save()
        try:
            for action in ('source','audit_source','search','freeze','audit_search','final','analyze','audit_final'):
                status['phase']=action;save();log=RUN/(action+'_001.log')
                with log.open('x') as f:
                    if action=='freeze':
                        paths=[str(OUT/n) for n in ('choices.json.gz','ancestry.json.gz','final_states.json.gz','search_session.json')]
                        subprocess.run(['git','add','--',*paths],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
                        subprocess.run(['git','commit','-m','Freeze M32 sequential descendants before independent confirmation'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
                        subprocess.run(['git','push'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
                        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();pushed(OUT/'choices.json.gz')
                        writej(OUT/'choice_freeze.json',dict(commit=commit,choices_sha256=sha(OUT/'choices.json.gz'),published_before_final=True,epoch=time.time()));code=0
                    else:
                        p=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-u','-m','maze_evolution.repair_evolution_m32',action],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
                        status['child_pid']=p.pid;save();code=p.wait()
                status['steps'].append(dict(phase=action,code=code,ended_epoch=time.time(),log=str(log.relative_to(ROOT))));status.pop('child_pid',None);save()
                if code:raise RuntimeError(f'{action} failed; preserve all receipts; no automatic resume')
            status.update(state='audited_ready_for_report',phase='report_preserve_seal',ended_epoch=time.time());save()
        except BaseException:
            status.update(state='failed',failure=traceback.format_exc(),ended_epoch=time.time());save();raise
if __name__=='__main__':main()
