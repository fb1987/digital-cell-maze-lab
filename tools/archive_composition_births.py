"""Lossless byte packaging of the large V12S ancestry log for GitHub storage.

Use `pack` only after search completion. Use `restore` after a fresh clone before
the frozen audit. The scientific log remains byte-identical; no data is removed.
"""
from pathlib import Path
import argparse, hashlib, json, os

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/composition_study'
SOURCE = OUT / 'reproduction.jsonl.gz'
PARTS = OUT / 'reproduction_parts'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(2**20): h.update(b)
    return h.hexdigest()


def pack():
    assert json.loads((OUT/'search_execution.json').read_text())['complete']
    assert not PARTS.exists()
    PARTS.mkdir()
    entries=[]
    with SOURCE.open('rb') as f:
        for index in range(1000):
            b=f.read(32*2**20)
            if not b:break
            p=PARTS/f'part{index:04d}.bin';p.write_bytes(b)
            entries.append(dict(file=p.name,bytes=len(b),sha256=sha(p)))
        else:raise AssertionError('Unexpected archive size')
    packet=dict(format='ordered raw byte concatenation, not recompression',
                target=str(SOURCE.relative_to(ROOT)),bytes=SOURCE.stat().st_size,
                sha256=sha(SOURCE),parts=entries)
    (PARTS/'manifest.json').write_text(json.dumps(packet,indent=2)+'\n')
    verify(packet)
    print(dict(bytes=packet['bytes'],parts=len(entries),sha256=packet['sha256']))


def verify(packet):
    full=hashlib.sha256();size=0
    for e in packet['parts']:
        p=PARTS/e['file'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
        with p.open('rb') as f:
            while b:=f.read(2**20):full.update(b);size+=len(b)
    assert size==packet['bytes'] and full.hexdigest()==packet['sha256']


def restore():
    packet=json.loads((PARTS/'manifest.json').read_text());verify(packet)
    assert packet['target']==str(SOURCE.relative_to(ROOT))
    if SOURCE.exists():
        assert SOURCE.stat().st_size==packet['bytes'] and sha(SOURCE)==packet['sha256']
        print('Existing log matches all remote byte chunks.');return
    temporary=SOURCE.with_suffix('.restoring')
    assert not temporary.exists()
    with temporary.open('wb') as out:
        for e in packet['parts']:
            with (PARTS/e['file']).open('rb') as src:
                while b:=src.read(2**20):out.write(b)
    assert sha(temporary)==packet['sha256']
    os.replace(temporary,SOURCE)
    print('Restored byte-identical scientific log.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('pack','restore'))
    globals()[p.parse_args().action]()
