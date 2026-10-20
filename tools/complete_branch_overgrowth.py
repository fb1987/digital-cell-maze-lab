"""Seal audited V13A artifacts; mutable project navigation stays outside the seal."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.branch_overgrowth_study import OUT,FIXTURES,ROOT,check_freeze,prior_check,exclusions,add_layouts,compressed_json,write_json,sha

def main():
    assert not (OUT/'completion.json').exists();reg=check_freeze();assert prior_check()==7880
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    old=exclusions();add_layouts(old,FIXTURES);add_layouts(old,OUT/'confirmation');assert len(old)==audit['whole_layouts']==275168
    compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(count=len(old),hashes=sorted(old)))
    for name in ('comparison.png','comparison.pdf','trajectories.png','trajectories.pdf','descriptive_summary.json','next_experiment.md'):assert (OUT/name).exists()
    paths={ROOT/n for group in ('sources','inputs') for n in reg[group]}
    paths.update(p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file())
    paths.update((ROOT/'tools').glob('*branch_overgrowth*.py'));paths.update((ROOT/'tests').glob('test_branch_overgrowth*.py'));paths.add(ROOT/'results/branch_overgrowth.md')
    generation=json.loads((OUT/'confirmation/generation.json').read_text())
    packet=dict(status='complete_and_audited',scientific_result_usable=True,audit_passed=True,registration_revision=generation['revision'],
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},whole_layouts_through_V13A=len(old),next_experiment_launched=False,
        mutable_handoffs_excluded=['AGENTS.md','README.md','docs/BRANCH_OVERGROWTH_PROGRESS.md','docs/LONG_SEARCH_SETUP.md','results/long_search_setup'])
    write_json(OUT/'completion.json',packet)
    print(dict(sealed_entries=len(packet['source_and_artifact_sha256']),prior_entries=7880,future_total=7880+len(packet['source_and_artifact_sha256']),layouts=len(old)))
if __name__=='__main__':main()
