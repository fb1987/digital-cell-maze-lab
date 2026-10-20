"""Seal V12Z only after independent audit and verified remote ancestry storage."""
from pathlib import Path
import sys,json,subprocess,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.family_evolution_study import *


def exclusions_packet():
    previous=through_fixtures()
    paths=[OUT/'validation',*sorted((OUT/'train').glob('g*')),OUT/'confirmation']
    for path in paths:add_layouts(previous,path)
    compressed_json(OUT/'whole_layout_exclusions.json.gz',dict(count=len(previous),hashes=sorted(previous)))
    return len(previous)


def main():
    reg=check_freeze();assert prior_check()==6923
    audit=json.loads((OUT/'audit.json').read_text());assert audit['passed']
    count=exclusions_packet();assert count==audit['whole_layouts']
    assert not (OUT/'completion.json').exists()
    for name in ('descriptive_summary.json.gz','comparison.png','comparison.pdf'):
        assert (OUT/name).exists()
    assert (ROOT/'results/family_evolution.md').exists()
    selection_revision=json.loads((OUT/'confirmation/generation.json').read_text())['revision']
    path=OUT/'reproduction_parts/manifest.json';packed=json.loads(path.read_text())
    assert subprocess.check_output(['git','show',f'{selection_revision}:{path.relative_to(ROOT)}'])==path.read_bytes()
    assert sha(OUT/'reproduction.jsonl.gz')==packed['sha256']
    full=hashlib.sha256();size=0
    for part in packed['parts']:
        path=OUT/'reproduction_parts'/part['file']
        data=subprocess.check_output(['git','show',f'{selection_revision}:{path.relative_to(ROOT)}'])
        assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256']==sha(path)
        full.update(data);size+=len(data)
    assert full.hexdigest()==packed['sha256'] and size==packed['bytes']
    paths={ROOT/name for group in ('sources','inputs') for name in reg[group]}
    paths.update(p for base in (OUT,FIXTURES) for p in base.rglob('*') if p.is_file())
    paths.update((ROOT/'tools').glob('*family_evolution*.py'))
    paths.update((ROOT/'tests').glob('test_family_evolution*.py'))
    paths.add(ROOT/'results/family_evolution.md')
    packet=dict(status='complete_and_audited',scientific_result_usable=True,audit_passed=True,
        preregistration_revision=subprocess.check_output(['git','rev-parse','8c01929'],text=True).strip(),
        selection_freeze_revision=selection_revision,
        source_and_artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
        whole_layouts_through_Z=count,ancestry_remote_byte_chunks_verified=True,
        primary_gate=read_compressed(OUT/'analysis.json.gz')['replicated'],
        next_experiment_launched=False,
        mutable_handoffs_excluded=['AGENTS.md','README.md','docs/FAMILY_EVOLUTION_PROGRESS.md','docs/LONG_SEARCH_SETUP.md','results/long_search_setup','tools/prepare_long_search.py'])
    write_json(OUT/'completion.json',packet)
    print(dict(hash_entries=len(packet['source_and_artifact_sha256']),prior_entries=6923,future_total=6923+len(packet['source_and_artifact_sha256']),whole_layouts=count))

if __name__=='__main__':main()
