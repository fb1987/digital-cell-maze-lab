"""Byte-preserving archival regression; no maze or candidate calls."""
import importlib.util,json,hashlib
from pathlib import Path
import pytest


@pytest.mark.parametrize('unexpected_write',[False,True])
def test_replay_output_isolation(tmp_path,unexpected_write):
    from types import SimpleNamespace
    spec=importlib.util.spec_from_file_location('zreplay',Path(__file__).resolve().parents[1]/'tools/replay_branch_overgrowth_audit.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.ROOT=tmp_path
    for name in ('composition_study','family_evolution'):
        p=tmp_path/'results'/name;p.mkdir(parents=True);(p/'reproduction.jsonl.gz').write_bytes(b'kept')
    out=tmp_path/'results/branch_overgrowth';out.mkdir();original=b'{"passed":true,"wall_seconds":99}\n';(out/'audit.json').write_bytes(original)
    seal=dict(source_and_artifact_sha256={'results/branch_overgrowth/audit.json':hashlib.sha256(original).hexdigest()})
    (out/'completion.json').write_text(json.dumps(seal))
    fake=SimpleNamespace(OUT=out,sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(),write_json=lambda p,v:p.write_text(json.dumps(v)))
    def audit():
        fake.write_json(out/('unexpected.json' if unexpected_write else 'audit.json'),dict(passed=True,wall_seconds=1.25))
        print((out/'audit.json').read_text())
    fake.audit=audit;mod.frozen=fake
    if unexpected_write:
        with pytest.raises(AssertionError,match='Unexpected write'):mod.main()
        assert not (out/'unexpected.json').exists()
    else:
        mod.main();new=next((tmp_path/'output/branch_overgrowth_replays').glob('*/audit.json'))
        assert json.loads(new.read_text())['wall_seconds']==1.25
    assert (out/'audit.json').read_bytes()==original
