"""Durable approved export-only recovery, then the original M25 audits/final."""
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.m25_export_recovery_a1 import A1, STATUS, check_a1
from maze_evolution.skill_integration import ROOT, OUT, RUN, pushed, writej
from maze_evolution.deep_campaign_store import writer_lock

PYTHON = str(ROOT / '.venv/bin/python')


def main():
    with writer_lock(RUN / 'workflow'):
        assert not STATUS.exists(), 'Never automatically resume a failed recovery'
        check_a1()
        assert json.loads((RUN / 'workflow_status.json').read_text())['state'] == 'failed'
        status = dict(state='running', phase='starting', pid=os.getpid(),
                      started_epoch=time.time(), amendment='M25-A1', steps=[])
        def save():
            writej(STATUS, status)
        def command(phase, action):
            status.update(state='running', phase=phase)
            save()
            log = RUN / (phase + '.log')
            with log.open('x') as f:
                child = subprocess.Popen([PYTHON, '-u', 'tools/m25_export_recovery_a1.py', action],
                    cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
                status['child_pid'] = child.pid
                save()
                code = child.wait()
            status.pop('child_pid', None)
            status['steps'].append(dict(phase=phase, returncode=code,
                ended_epoch=time.time(), log=str(log.relative_to(ROOT))))
            save()
            if code:
                raise RuntimeError(f'{phase} exited {code}; preserved {log}')
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
        save()
        try:
            command('a1_export_001', 'export')
            assert json.loads((OUT / 'session.json').read_text())['status'] == 'complete'
            status['phase'] = 'publishing_frozen_choices'
            save()
            assert not git('diff', '--cached', '--name-only')
            paths = ['exclusions.json', 'exclusions.delta.json.gz', 'search_exclusions.json',
                     'search_exclusions.delta.json.gz', 'session.json', 'recovery_a1/export_receipt.json',
                     'choices.json.gz', 'ancestry.json.gz', 'final_states.json.gz', 'validation.json.gz']
            git('add', '--', *(str(OUT / n) for n in paths))
            git('commit', '-m', 'Complete approved M25 A1 exports and freeze choices before confirmation')
            git('push')
            pushed(OUT / 'choices.json.gz')
            assert not (OUT / 'choices_freeze.json').exists()
            writej(OUT / 'choices_freeze.json', dict(commit=git('rev-parse', 'HEAD'),
                pushed=True, epoch=time.time(), independent_confirmation_generated=False,
                amendment='M25-A1', exact_original_partial_choices_retained=True))
            command('a1_search_audit_001', 'audit_search')
            assert json.loads((OUT / 'search_audit.json').read_text())['status'] == 'PASS'
            command('a1_confirmation_001', 'final')
            assert json.loads((OUT / 'final_session.json').read_text())['status'] == 'complete'
            command('a1_analysis_001', 'analyze')
            command('a1_final_audit_001', 'audit_final')
            assert json.loads((OUT / 'final_audit.json').read_text())['status'] == 'PASS'
            status.update(state='audited_ready_for_report', phase='report_backup_seal', ended_epoch=time.time())
            save()
            print('M25 A1 audits PASS; ready for report/preservation/seal', flush=True)
        except BaseException:
            failure = traceback.format_exc()
            print(failure, flush=True)
            status.update(state='failed', failure=failure, ended_epoch=time.time())
            save()
            raise


if __name__ == '__main__':
    main()
