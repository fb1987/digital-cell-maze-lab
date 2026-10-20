"""Seal V12Y only. Mutable longer-run preparation is explicitly separate."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.mating_opportunity_study import ROOT,OUT,check_freeze,prior_check,sha,write


def main():
    reg=check_freeze();assert prior_check()==6667
    assert not (OUT/'completion.json').exists()
    run=json.loads((OUT/'execution.json').read_text());audit=json.loads((OUT/'audit.json').read_text())
    assert run['complete'] and audit['passed']
    assert run['candidate_calls']==audit['candidate_calls']==run['new_mazes']==0
    paths={ROOT/name for group in ('sources','inputs') for name in reg[group]}
    paths.update(p for p in OUT.rglob('*') if p.is_file() and p.suffix!='.log')
    paths.update((ROOT/'tools').glob('*mating_opportunity*.py'))
    paths.add(ROOT/'results/mating_opportunity.md')
    write(OUT/'completion.json',dict(status='complete_and_audited',
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
        preregistration_revision=run['revision'],prior_hash_entries=6667,
        whole_layouts=255356,exclusion_hashset='results/linkage_restart/whole_layout_exclusions.json.gz',
        candidate_calls=0,new_mazes=0,new_evolution=False,source_repair_after_registration=False,
        static_screen_passed=False,long_efficacy_run_launched=False,
        mutable_followup_paths=['AGENTS.md','README.md','docs/MATING_OPPORTUNITY_PROGRESS.md',
            'docs/LONG_SEARCH_SETUP.md','results/long_search_setup/',
            'maze_evolution/family_reservoir.py','tests/test_family_reservoir.py','tools/prepare_long_search.py']))
    print(dict(sealed_entries=len(paths),future_prior_entries=6667+len(paths)))


if __name__=='__main__':
    main()
