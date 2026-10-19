"""Seal Q outputs and recheck immutable sources/prior studies; no inference."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.shared_prefix_study import *

def main():
    reg=check_freeze();assert prior_check()==2384
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed'] and json.loads((OUT/'schedule_audit.json').read_text())['passed']
    assert not (OUT/'completion.json').exists()
    paths={ROOT/p for group in ('sources','inputs') for p in reg[group]}
    paths.update(p for root in (OUT,FIXTURES) for p in root.rglob('*') if p.is_file())
    paths.update((ROOT/'tools').glob('*shared_prefix*.py'));paths.add(ROOT/'results/shared_prefix.md')
    packet=dict(status='complete_and_audited',preregistration_revision=subprocess.check_output(['git','rev-parse','4fafe1c'],text=True).strip(),schedule_amendment_revision=subprocess.check_output(['git','rev-parse','b1b9530'],text=True).strip(),selection_freeze_revision=subprocess.check_output(['git','rev-parse','2ba193d'],text=True).strip(),source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},candidate_calls=json.loads((OUT/'confirmation/execution.json').read_text())['budget']['calls'],audit_passed=True,whole_layouts_through_Q=187416,next_experiment_launched=False,mutable_handoffs_excluded=['AGENTS.md','README.md','docs/SHARED_PREFIX_PROGRESS.md'])
    write_json(OUT/'completion.json',packet);print(dict(hash_entries=len(packet['source_and_artifact_sha256']),prior_entries=2384,future_total=2384+len(packet['source_and_artifact_sha256'])))
if __name__=='__main__':main()
