import hashlib, importlib.util, json
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('archive',Path(__file__).parents[1]/'tools/s3_research_archive.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def test_paths_cannot_escape_or_follow_symlinks(tmp_path):
    (tmp_path/'runs').mkdir()
    for bad in ('/runs/x','runs/../x','results/x'):
        with pytest.raises(ValueError):a.safe_path(tmp_path,bad)
    (tmp_path/'runs/link').symlink_to(tmp_path)
    with pytest.raises(ValueError):a.safe_path(tmp_path,'runs/link/x')
    assert a.safe_path(tmp_path,'runs/closed/x')==tmp_path/'runs/closed/x'

def test_nonempty_wal_blocks_archive(tmp_path):
    d=tmp_path/'runs/closed';d.mkdir(parents=True)
    (d/'campaign.sqlite-wal').write_bytes(b'pending transactions')
    with pytest.raises(RuntimeError,match='Nonempty WAL'):
        with a.locks(tmp_path,['runs/closed']):pass

def test_writer_lock_blocks_archive(tmp_path):
    d=tmp_path/'runs/closed';d.mkdir(parents=True)
    with (d/'writer.lock').open('w') as lock:
        a.fcntl.flock(lock,a.fcntl.LOCK_EX|a.fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            with a.locks(tmp_path,['runs/closed']):pass

def test_receipts_never_overwrite(tmp_path):
    p=tmp_path/'receipt.json';a.write_new(p,{'a':1})
    with pytest.raises(FileExistsError):a.write_new(p,{'a':2})
    assert a.readj(p)=={'a':1}

def test_restore_pins_versions_checks_chunks_and_full_file(tmp_path,monkeypatch):
    data=[b'abc',b'def']; hashes=[a.digest(b) for b in data]
    f={'path':'runs/closed/x.sqlite','bytes':6,'sha256':a.digest(b'abcdef'),
       'chunks':[{'sha256':h,'bytes':3} for h in hashes],'mode':0o600,'signature':[0,0,6,1000000000]}
    c={'manifest':{'bucket':{},'files':[f]},'chunks':{h:{'key':h,'version_id':'pinned-'+h} for h in hashes}}
    a.write_new(tmp_path/'catalog.json',c)
    a.write_new(tmp_path/'upload_complete.json',{'catalog_sha256':a.sha_file(tmp_path/'catalog.json')})
    class Fake:
        def __init__(self,c):pass
        def validate(self):pass
        def get(self,key,version,path):
            assert version=='pinned-'+key;path.write_bytes(data[hashes.index(key)])
    monkeypatch.setattr(a,'S3',Fake);monkeypatch.setattr(a,'FLOOR',0)
    dest=tmp_path/'restored';a.restore(tmp_path,f['path'],dest);assert dest.read_bytes()==b'abcdef'
    with pytest.raises(AssertionError):a.restore(tmp_path,f['path'],dest)
    def corrupt(self,key,version,path):path.write_bytes(b'bad')
    monkeypatch.setattr(Fake,'get',corrupt)
    with pytest.raises(AssertionError):a.restore(tmp_path,f['path'],tmp_path/'bad-restore')
    assert not (tmp_path/'bad-restore').exists()

def test_s3_put_refuses_unverified_existing_object(tmp_path):
    p=tmp_path/'data';p.write_bytes(b'abc')
    class Fake(a.S3):
        def head(self,key):return {'ContentLength':3,'ChecksumSHA256':'wrong','ServerSideEncryption':'AES256','VersionId':'1'}
    with pytest.raises(AssertionError):Fake({}).put('key',p,a.digest(b'abc'))
