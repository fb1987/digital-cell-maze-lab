"""Seal audited V13B artifacts; mutable navigation remains outside the seal."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.selectivity_study import OUT,FIXTURES,ROOT,check_freeze,prior_check,through_fixtures,add_layouts,compressed_json,write_json,sha,read_compressed

def main():
    assert not (OUT/'completion.json').exists();reg=check_freeze();assert prior_check()==8164
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    old=through_fixtures()
    for path in [OUT/'validation',*sorted((OUT/'train').glob('g*')),OUT/'confirmation']:add_layouts(old,path)
    assert len(old)==audit['whole_layouts']
    compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(count=len(old),hashes=sorted(old)))
    for name in ('comparison.png','comparison.pdf','descriptive_summary.json.gz','next_experiment.md'):assert (OUT/name).exists()
    selection=json.loads((OUT/'confirmation/generation.json').read_text())['revision']
    for name in ('choices.json.gz','next_states.json.gz','reproduction.jsonl.gz'):
        p=OUT/name;assert subprocess.check_output(['git','show',f'{selection}:{p.relative_to(ROOT)}'])==p.read_bytes()
    paths={ROOT/n for group in ('sources','inputs') for n in reg[group]}
    paths.update(p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file())
    paths.update((ROOT/'tools').glob('*selectivity_pressure*.py'));paths.add(ROOT/'tests/test_selectivity_replay.py');paths.add(ROOT/'results/selectivity_pressure.md')
    packet=dict(status='complete_and_audited',scientific_result_usable=True,audit_passed=True,registration_revision=subprocess.check_output(['git','rev-parse','2f7a379'],text=True).strip(),selection_freeze_revision=selection,
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},whole_layouts_through_V13B=len(old),primary_gate=read_compressed(OUT/'analysis.json.gz')['replicated'],next_experiment_launched=False,
        mutable_handoffs_excluded=['AGENTS.md','README.md','docs/SELECTIVITY_PRESSURE_PROGRESS.md','docs/LONG_SEARCH_SETUP.md','results/long_search_setup'])
    write_json(OUT/'completion.json',packet)
    print(dict(sealed_entries=len(packet['source_and_artifact_sha256']),prior_entries=8164,future_total=8164+len(packet['source_and_artifact_sha256']),layouts=len(old)))
if __name__=='__main__':main()
