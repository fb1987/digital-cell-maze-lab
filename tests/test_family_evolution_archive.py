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
