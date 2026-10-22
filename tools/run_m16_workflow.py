"""Durable M16 protocol, stopping on errors without repair or automatic resume."""
import json,os,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.restoration_assay import ROOT,OUT,RUN,check,pushed,writej
from maze_evolution.deep_campaign_store import writer_lock

PYTHON=str(ROOT/'.venv/bin/python')


def main():
    RUN.mkdir(parents=True,exist_ok=True)
    with writer_lock(RUN/'workflow'):
        assert not (RUN/'workflow_status.json').exists()
        check();pushed(OUT/'registration.json')
        status=dict(pid=os.getpid(),state='running',started_epoch=time.time(),steps=[])
        def save():writej(RUN/'workflow_status.json',status)
        def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
        def command(action):
            status.update(phase=action,state='running');save();log=RUN/(action+'_001.log')
            with log.open('x') as f:
                p=subprocess.Popen([PYTHON,'-u','-m','maze_evolution.restoration_assay',action],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
                status['child_pid']=p.pid;save();code=p.wait()
            status['steps'].append(dict(phase=action,code=code,ended_epoch=time.time(),log=str(log.relative_to(ROOT))))
            status.pop('child_pid',None);save()
            if code:raise RuntimeError(f'{action} exited {code}; preserve {log}, no automatic restart')
        def publish(names,message,receipt):
            assert not git('diff','--cached','--name-only')
            git('add','--',*[str(OUT/name) for name in names]);git('commit','-m',message);git('push')
            pushed(OUT/names[0]);writej(OUT/receipt,dict(commit=git('rev-parse','HEAD'),pushed=True,epoch=time.time()))
        save()
        try:
            command('pool');publish(['pool.json.gz','pool_counts.json'],'Freeze M16 mutation pool before fresh screening','pool_freeze.json')
            command('screen');command('freeze')
            publish(['choices.json.gz','screen_exclusions.json','screen_exclusions.delta.json.gz','screen_session.json'],
                    'Freeze M16 restoration nominees before independent confirmation','choices_freeze.json')
            command('screen_audit');command('traces');command('trace_audit')
            command('final');command('analyze');command('final_audit')
            for name in ('screen','trace','final'):assert json.loads((OUT/f'{name}_audit.json').read_text())['status']=='PASS'
            status.update(state='audited_ready_for_report',phase='report_preserve_seal',ended_epoch=time.time());save()
            print('M16 all audits PASS; ready for report and preservation.',flush=True)
        except BaseException:
            status.update(state='failed',failure=traceback.format_exc(),ended_epoch=time.time());save();print(status['failure'],flush=True);raise


if __name__=='__main__':main()
