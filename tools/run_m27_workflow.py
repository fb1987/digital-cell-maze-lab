"""M27 durable fixed assay. A failed phase is preserved and never auto-resumed."""
import json,os,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.transfer_retention import ROOT,OUT,RUN,check,pushed,writej
from maze_evolution.deep_campaign_store import writer_lock


def main():
    with writer_lock(RUN/'workflow'):
        assert not (RUN/'workflow_status.json').exists();check();pushed(OUT/'registration.json');pushed(OUT/'pool.json.gz')
        status=dict(pid=os.getpid(),state='running',started_epoch=time.time(),steps=[])
        def save():writej(RUN/'workflow_status.json',status)
        save()
        try:
            for action in ('run','analyze','audit'):
                status['phase']=action;save();log=RUN/(action+'_001.log')
                with log.open('x') as f:
                    p=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-u','-m','maze_evolution.transfer_retention',action],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
                    status['child_pid']=p.pid;save();code=p.wait()
                status['steps'].append(dict(phase=action,code=code,ended_epoch=time.time(),log=str(log.relative_to(ROOT))))
                status.pop('child_pid',None);save()
                if code:raise RuntimeError(f'{action} failed; preserve logs/receipts, no automatic resume')
            status.update(state='audited_ready_for_report',phase='report_preserve_seal',ended_epoch=time.time());save()
        except BaseException:
            status.update(state='failed',failure=traceback.format_exc(),ended_epoch=time.time());save();raise


if __name__=='__main__':main()
