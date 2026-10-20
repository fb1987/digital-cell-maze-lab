"""Byte-preserving archival regression; no maze or candidate calls."""
import importlib.util,json,hashlib
from pathlib import Path
import pytest


def tool(tmp_path):
    spec=importlib.util.spec_from_file_location('zarchive',Path(__file__).resolve().parents[1]/'tools/archive_family_evolution_births.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.ROOT=tmp_path;mod.OUT=tmp_path/'study';mod.SOURCE=mod.OUT/'reproduction.jsonl.gz';mod.PARTS=mod.OUT/'parts';mod.PARTS.mkdir(parents=True)
    chunks=[b'first\x00part\n',b'second\xffpart\n'];entries=[]
    for k,data in enumerate(chunks):
        p=mod.PARTS/f'part{k:04}.bin';p.write_bytes(data);entries.append(dict(file=p.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    raw=b''.join(chunks);packet=dict(target=str(mod.SOURCE.relative_to(tmp_path)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),parts=entries)
    (mod.PARTS/'manifest.json').write_text(json.dumps(packet));return mod,raw


def test_two_part_restore_and_existing_mismatch(tmp_path):
    mod,raw=tool(tmp_path);mod.restore();assert mod.SOURCE.read_bytes()==raw;mod.restore()
    mod.SOURCE.write_bytes(b'valuable different data')
    with pytest.raises(AssertionError):mod.restore()
    assert mod.SOURCE.read_bytes()==b'valuable different data'


def test_corruption_rejected_before_restore(tmp_path):
    mod,_=tool(tmp_path);(mod.PARTS/'part0001.bin').write_bytes(b'bad')
    with pytest.raises(AssertionError):mod.restore()
    assert not mod.SOURCE.exists()


@pytest.mark.parametrize('unexpected_write',[False,True])
def test_replay_output_isolation(tmp_path,unexpected_write):
    from types import SimpleNamespace
    spec=importlib.util.spec_from_file_location('zreplay',Path(__file__).resolve().parents[1]/'tools/replay_family_evolution_audit.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.ROOT=tmp_path
    for name in ('composition_study','family_evolution'):
        p=tmp_path/'results'/name;p.mkdir(parents=True);(p/'reproduction.jsonl.gz').write_bytes(b'kept')
    out=tmp_path/'results/family_evolution';original=b'{"passed":true,"wall_seconds":99}\n';(out/'audit.json').write_bytes(original)
    seal=dict(source_and_artifact_sha256={'results/family_evolution/audit.json':hashlib.sha256(original).hexdigest()})
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
        mod.main();new=next((tmp_path/'output/family_evolution_replays').glob('*/audit.json'))
        assert json.loads(new.read_text())['wall_seconds']==1.25
    assert (out/'audit.json').read_bytes()==original
