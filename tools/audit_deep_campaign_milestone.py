"""Durable, resource-bounded wrapper around the sealed A1 audit command."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign_a1 import DEFAULT_RUN, ROOT, check_setup, resource_reason
from maze_evolution import deep_campaign_a1 as runner
from maze_evolution.deep_campaign_amendment import check_amendment
from maze_evolution.deep_campaign_store import writer_lock
from maze_evolution.routing_transfer import sha


def main():
    out = ROOT / 'results/deep_campaign_run/milestone'
    config = check_setup()
    check_amendment()
    freeze = json.loads((out / 'freeze.json').read_text())
    assert sha(out / 'choices.json.gz') == freeze['choices_sha256']
    started = time.monotonic()
    reason = resource_reason(DEFAULT_RUN, config, started)
    if reason:
        raise RuntimeError(f'Audit resource guard: {reason}')
    with writer_lock(out):
        partial = out / 'audit.partial.json'
        if any((out / name).exists() for name in ('audit.json', 'audit_execution.json', 'audit.partial.json')):
            raise RuntimeError('Preserve the existing audit attempt; do not overwrite')
        command = [str(ROOT / '.venv/bin/python'), '-u', '-m',
                   'maze_evolution.deep_campaign_a1', 'audit']
        with partial.open('x') as stdout, (out / 'audit.stderr.log').open('x') as stderr:
            child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                     stdout=stdout, stderr=stderr)
            start = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                         wrapper_pid=os.getpid(), audit_pid=child.pid, command=command,
                         script_sha256=sha(Path(__file__)), chain=freeze['chain'],
                         confirmation_not_generated=True)
            (out / 'audit_start.json').write_text(json.dumps(start, indent=2)+'\n')
            print(json.dumps(start), flush=True)
            while child.poll() is None:
                reason = resource_reason(DEFAULT_RUN, config, started)
                if reason:
                    child.terminate()
                    try:
                        child.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                    break
                time.sleep(2)
        success = child.returncode == 0 and reason is None
        error = None
        if success:
            try:
                audit = json.loads(partial.read_text())
                assert audit['generation'] == 10000
                assert audit['replay']['chain'] == freeze['chain']
                assert audit['replay']['transitions'] == 10021
                assert audit['replay']['births_replayed'] == 1560000
                assert audit['usage'] == freeze['usage']
                partial.rename(out / 'audit.json')
            except Exception as exc:
                success, error = False, repr(exc)
        cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
        result = dict(success=success, returncode=child.returncode, resource_stop=reason,
                      result_validation_error=error, ended_utc=datetime.now(timezone.utc).isoformat(),
                      wall_seconds=time.monotonic()-started,
                      child_cpu_seconds=cpu.ru_utime+cpu.ru_stime,
                      sampled_peak_tree_rss_bytes=runner._peak_rss,
                      inference_replayed=False, confirmation_not_generated=True)
        (out / 'audit_execution.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result), flush=True)
        if not success:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
