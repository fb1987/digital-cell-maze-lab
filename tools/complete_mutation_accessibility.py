"""Seal completed V12R artifacts, preserving prior checksums; no inference."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mutation_accessibility_study import *

def main():
    reg=check_freeze();assert prior_check()==2644
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    assert not (OUT/'completion.json').exists()
    amendment=json.loads((OUT/'budget_amendment.json').read_text())
    for name,h in amendment['hashes'].items():assert sha(ROOT/name)==h,name
    paths={ROOT/p for group in ('sources','inputs') for p in reg[group]}
    paths.update(ROOT/p for p in amendment['hashes'])
    paths.update(p for root in (OUT,FIXTURES) for p in root.rglob('*') if p.is_file())
    paths.update((ROOT/'tools').glob('*mutation_accessibility*.py'))
    paths.add(ROOT/'tools/diagnose_accessibility_exception.py')
    paths.add(ROOT/'results/mutation_accessibility.md')
    revision=lambda r:subprocess.check_output(['git','rev-parse',r],text=True).strip()
    packet=dict(status='complete_and_audited',preregistration_revision=revision('dea1f0f'),
        timing_amendment_revision=revision('abff7b9'),selection_freeze_revision=revision('74d6d17'),
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
        candidate_calls=json.loads((OUT/'confirmation/execution.json').read_text())['budget']['calls'],
        audit_passed=True,whole_layouts_through_R=191784,next_experiment_launched=False,
        mutable_handoffs_excluded=['AGENTS.md','README.md','docs/MUTATION_ACCESSIBILITY_PROGRESS.md'])
    write_json(OUT/'completion.json',packet)
    print(dict(hash_entries=len(packet['source_and_artifact_sha256']),prior_entries=2644,
        future_total=2644+len(packet['source_and_artifact_sha256'])))
if __name__=='__main__':main()
