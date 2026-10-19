"""Seal the complete V12S packet after independent audit; no inference."""
from pathlib import Path
import sys,json,subprocess,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.composition_study import OUT,FIXTURES,ROOT,check_freeze,prior_check,sha,write_json


def main():
    reg=check_freeze();assert prior_check()==2913
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    assert json.loads((OUT/'raster_hypothesis_verification.json').read_text())['passed']
    assert json.loads((OUT/'exclusion_sources.json').read_text())['through_S_count']==audit['whole_layouts']
    assert not (OUT/'completion.json').exists()
    assert (OUT/'descriptive_outcomes.json').exists() and (OUT/'comparison.png').exists()
    selection_revision=json.loads((OUT/'confirmation/generation.json').read_text())['revision']
    manifest_path=OUT/'reproduction_parts/manifest.json'
    assert subprocess.check_output(['git','show',f'{selection_revision}:{manifest_path.relative_to(ROOT)}'])==manifest_path.read_bytes()
    packed=json.loads(manifest_path.read_text())
    assert sha(OUT/'reproduction.jsonl.gz')==packed['sha256']
    remote_hash=hashlib.sha256();remote_bytes=0
    for part in packed['parts']:
        path=OUT/'reproduction_parts'/part['file']
        data=subprocess.check_output(['git','show',f'{selection_revision}:{path.relative_to(ROOT)}'])
        assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256']==sha(path)
        remote_hash.update(data);remote_bytes+=len(data)
    assert remote_hash.hexdigest()==packed['sha256'] and remote_bytes==packed['bytes']
    paths={ROOT/name for group in ('sources','inputs') for name in reg[group]}
    paths.update(p for base in (OUT,FIXTURES,ROOT/'results/research_reset') for p in base.rglob('*') if p.is_file())
    paths.update((ROOT/'tools').glob('*composition*.py'))
    paths.add(ROOT/'results/composition_study.md')
    rev=lambda name:subprocess.check_output(['git','rev-parse',name],text=True).strip()
    packet=dict(status='complete_and_audited',preregistration_revision=rev('f650b93'),
        profile_freeze_revision=rev('4750c0f'),
        selection_freeze_revision=selection_revision,
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
        candidate_calls=json.loads((OUT/'confirmation/execution.json').read_text())['budget']['calls'],
        ancestry_remote_byte_chunks_verified=True,
        audit_passed=True,whole_layouts_through_S=audit['whole_layouts'],next_experiment_launched=False,
        mutable_handoffs_excluded=['AGENTS.md','README.md','docs/COMPOSITION_PROGRESS.md'])
    write_json(OUT/'completion.json',packet)
    print(dict(hash_entries=len(packet['source_and_artifact_sha256']),prior_entries=2913,
               future_total=2913+len(packet['source_and_artifact_sha256'])))


if __name__=='__main__':main()
