"""PROPOSED gated recovery; does not run until explicit approved A1 publication."""
import os,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.m32_export_recovery_a1 import m,A1,approved,failure_check

def main():
    approved();failure_check();path=m.RUN/'recovery_a1_workflow_status.json'
    with m.writer_lock(m.RUN/'workflow'):
        assert not path.exists();assert m.json.loads((m.RUN/'workflow_status.json').read_text())['state']=='failed'
        status=dict(pid=os.getpid(),state='running',started_epoch=time.time(),steps=[],original_failed_status_preserved=True)
        def save():m.writej(path,status)
        save()
        try:
            for action in ('export','freeze','audit_search','final','analyze','audit_final'):
                status['phase']=action;save();log=m.RUN/('recovery_a1_'+action+'_001.log')
                with log.open('x') as f:
                    if action=='freeze':
                        assert not (m.OUT/'choice_freeze.json').exists()
                        files=[str(m.OUT/n) for n in ('choices.json.gz','ancestry.json.gz','final_states.json.gz','search_session.json')]
                        subprocess.run(['git','add','--',*files],cwd=m.ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
                        subprocess.run(['git','commit','-m','Freeze recovered M32 exact nominees before independent confirmation'],cwd=m.ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
                        subprocess.run(['git','push'],cwd=m.ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
                        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=m.ROOT,text=True).strip();m.pushed(m.OUT/'choices.json.gz')
                        m.writej(m.OUT/'choice_freeze.json',dict(commit=commit,choices_sha256=m.sha(m.OUT/'choices.json.gz'),published_before_final=True,epoch=time.time(),export_only_A1=True));code=0
                    else:
                        cmd=[str(m.ROOT/'.venv/bin/python'),'-u',str(m.ROOT/'tools/m32_export_recovery_a1.py'),'export'] if action=='export' else [str(m.ROOT/'.venv/bin/python'),'-u','-m','maze_evolution.repair_evolution_m32',action]
                        p=subprocess.Popen(cmd,cwd=m.ROOT,stdout=f,stderr=subprocess.STDOUT);status['child_pid']=p.pid;save();code=p.wait()
                status['steps'].append(dict(phase=action,code=code,ended_epoch=time.time(),log=str(log.relative_to(m.ROOT))));status.pop('child_pid',None);save()
                if code:raise RuntimeError(f'A1 {action} failed; preserve outputs; no automatic resume')
            status.update(state='audited_ready_for_report',phase='report_preserve_seal',ended_epoch=time.time());save()
        except BaseException:
            status.update(state='failed',failure=traceback.format_exc(),ended_epoch=time.time());save();raise
if __name__=='__main__':main()
