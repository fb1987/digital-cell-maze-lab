"""Verified, resumable S3 archive for closed research runs. Uses the installed AWS CLI.

Never runs scientific code. Plan records exact bytes; upload verifies every chunk
by downloading its pinned S3 version. Eviction is a separate, explicit command.
No credentials are read, printed, or stored by this tool.
"""
import argparse, base64, contextlib, fcntl, hashlib, json, os, shutil, stat
import subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CHUNK = 64 * 2**20
FLOOR = 16 * 2**30
RETAIN = {'mutation_scope_m13', 'exploration_allocation_m14'}

def digest(data): return hashlib.sha256(data).hexdigest()
def readj(p): return json.loads(Path(p).read_text())
def write_new(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())

def sha_file(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        while b := f.read(CHUNK): h.update(b)
    return h.hexdigest()

def safe_path(root, rel):
    r = PurePosixPath(rel)
    if r.is_absolute() or '..' in r.parts or not r.parts or r.parts[0] != 'runs':
        raise ValueError('Unsafe research path: ' + rel)
    p = root.joinpath(*r.parts)
    if p.resolve() != p.absolute(): raise ValueError('Symlinked research path: ' + rel)
    return p

def signature(p):
    s = p.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]

@contextlib.contextmanager
def locks(root, directories):
    with contextlib.ExitStack() as stack:
        for rel in directories:
            d = safe_path(root, rel)
            for p in sorted(d.rglob('writer.lock')):
                f = stack.enter_context(p.open('rb'))
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            for p in d.rglob('*-wal'):
                if p.stat().st_size: raise RuntimeError('Nonempty WAL: ' + str(p))
        yield

class S3:
    def __init__(self, config): self.c = config
    def cmd(self, *args):
        return ['aws', '--profile', self.c['profile'], '--region', self.c['region'],
                '--no-cli-pager', '--cli-connect-timeout', '30', '--cli-read-timeout', '120', *args]
    def call(self, *args):
        r = subprocess.run(self.cmd(*args), capture_output=True, text=True, check=True)
        return json.loads(r.stdout) if r.stdout.strip() else {}
    def object_args(self, key):
        return ['--bucket', self.c['bucket'], '--expected-bucket-owner', self.c['account'], '--key', key]
    def validate(self):
        assert self.call('sts','get-caller-identity')['Account'] == self.c['account']
        base = ['--bucket', self.c['bucket'], '--expected-bucket-owner', self.c['account']]
        assert self.call('s3api','get-bucket-versioning',*base)['Status'] == 'Enabled'
        assert all(self.call('s3api','get-public-access-block',*base)['PublicAccessBlockConfiguration'].values())
    def head(self, key):
        try: return self.call('s3api','head-object',*self.object_args(key),'--checksum-mode','ENABLED')
        except subprocess.CalledProcessError as e:
            if '(404)' in e.stderr or '(NoSuchKey)' in e.stderr: return None
            raise
    def put(self, key, path, h):
        head = self.head(key)
        b64 = base64.b64encode(bytes.fromhex(h)).decode()
        if head is None:
            self.call('s3api','put-object',*self.object_args(key),'--body',str(path),
                      '--if-none-match','*','--checksum-algorithm','SHA256','--checksum-sha256',b64,
                      '--server-side-encryption','AES256','--storage-class','STANDARD')
            head = self.head(key)
        assert head['ContentLength'] == path.stat().st_size
        assert head['ChecksumSHA256'] == b64
        assert head['ServerSideEncryption'] == 'AES256'
        assert head.get('VersionId') not in (None,'null')
        return head
    def get(self, key, version, path):
        return self.call('s3api','get-object',*self.object_args(key),'--version-id',version,
                         '--checksum-mode','ENABLED',str(path))

def plan(packet):
    assert not (packet/'manifest.json').exists()
    directories = ['runs/'+p.name for p in sorted((ROOT/'runs').iterdir()) if p.is_dir() and p.name not in RETAIN]
    files = []
    with locks(ROOT, directories):
        for rel in directories:
            for p in sorted((ROOT/rel).rglob('*')):
                if p.is_symlink(): raise RuntimeError('Unexpected symlink '+str(p))
                if not p.is_file(): continue
                before = signature(p); h = hashlib.sha256(); chunks = []
                with p.open('rb') as f:
                    while b := f.read(CHUNK):
                        h.update(b); chunks.append({'sha256':digest(b),'bytes':len(b)})
                assert signature(p) == before
                files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,
                              'sha256':h.hexdigest(),'chunks':chunks,'signature':before,
                              'mode':stat.S_IMODE(p.stat().st_mode)})
            print('INVENTORIED',rel,flush=True)
    # Confirm historical local-record seals where available, without rewriting them.
    bypath={f['path']:f for f in files}; matches=[]
    for seal in sorted((ROOT/'results').glob('*/completion.json')):
        d=readj(seal)
        for rel, h in d.get('local_records',{}).items():
            if isinstance(h,dict): h=h.get('sha256')
            if rel in bypath and isinstance(h,str):
                assert bypath[rel]['sha256']==h, (str(seal),rel)
                matches.append({'seal':str(seal.relative_to(ROOT)),'path':rel,'sha256':h})
    manifest={'format':'sha256-chunks-v1','created_epoch':time.time(),'chunk_bytes':CHUNK,
              'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'bucket':readj(packet/'bucket.json'),'directories':directories,'files':files,
              'retained_local_runs':sorted(RETAIN),'historical_seal_matches':matches,
              'bytes':sum(f['bytes'] for f in files),'scientific_work_performed':False}
    write_new(packet/'manifest.json',manifest)
    print('MANIFEST',len(files),'files',manifest['bytes'],'bytes',len(matches),'seal matches',flush=True)

def upload(packet):
    m=readj(packet/'manifest.json'); s3=S3(m['bucket']); s3.validate()
    receipts=packet/'chunks';receipts.mkdir(exist_ok=True)
    refs={}
    for f in m['files']:
        off=0
        for c in f['chunks']:
            refs.setdefault(c['sha256'],(f,off,c));off+=c['bytes']
    def work(item):
        h,(f,off,c)=item; rp=receipts/(h+'.json'); key='blobs/sha256/'+h
        if rp.exists():
            r=readj(rp); assert r['sha256']==h and r['bytes']==c['bytes'] and r['download_verified']
            head=s3.call('s3api','head-object',*s3.object_args(key),'--version-id',r['version_id'],'--checksum-mode','ENABLED')
            assert head['ContentLength']==c['bytes'] and head['ChecksumSHA256']==base64.b64encode(bytes.fromhex(h)).decode()
            return
        p=safe_path(ROOT,f['path']);assert signature(p)==f['signature']
        with p.open('rb') as src:
            src.seek(off);b=src.read(c['bytes'])
        assert digest(b)==h
        # Two workers, one temporary chunk each. Preserve the disk floor.
        if shutil.disk_usage(ROOT).free < FLOOR+2*CHUNK: raise RuntimeError('Disk floor reserve')
        with tempfile.TemporaryDirectory(prefix='s3-archive-',dir=packet) as td:
            temp=Path(td)/'chunk';temp.write_bytes(b);del b
            head=s3.put(key,temp,h);temp.unlink()
            s3.get(key,head['VersionId'],temp)
            assert temp.stat().st_size==c['bytes'] and sha_file(temp)==h
        write_new(rp,{'sha256':h,'bytes':c['bytes'],'key':key,'version_id':head['VersionId'],
                      'download_verified':True,'verified_epoch':time.time()})
        print('VERIFIED',h,c['bytes'],flush=True)
    with locks(ROOT,m['directories']):
        with ThreadPoolExecutor(max_workers=2) as ex: list(ex.map(work,refs.items()))
        for f in m['files']: assert signature(safe_path(ROOT,f['path']))==f['signature']
    # Version-pinned remote catalog contains every local path and chunk receipt.
    catalog={'manifest':m,'manifest_sha256':sha_file(packet/'manifest.json'),
             'chunks':{h:readj(receipts/(h+'.json')) for h in refs},'all_chunks_download_verified':True}
    cp=packet/'catalog.json'
    if cp.exists(): assert readj(cp)==catalog
    else: write_new(cp,catalog)
    h=sha_file(cp);key='catalogs/'+packet.name+'/'+h+'.json'
    head=s3.put(key,cp,h)
    with tempfile.TemporaryDirectory(dir=packet) as td:
        dest=Path(td)/'catalog';s3.get(key,head['VersionId'],dest);assert sha_file(dest)==h
    completion={'status':'uploaded_and_download_verified','catalog_sha256':h,'catalog_key':key,
                'catalog_version_id':head['VersionId'],'logical_bytes':m['bytes'],
                'unique_blob_bytes':sum(c['bytes'] for c in catalog['chunks'].values()),
                'files':len(m['files']),'chunks':len(refs),'completed_epoch':time.time()}
    write_new(packet/'upload_complete.json',completion);print(json.dumps(completion),flush=True)

def restore(packet, relative, destination):
    c=readj(packet/'catalog.json');done=readj(packet/'upload_complete.json')
    assert sha_file(packet/'catalog.json')==done['catalog_sha256']
    f=next(f for f in c['manifest']['files'] if f['path']==relative)
    destination=Path(destination).absolute();assert not destination.exists()
    destination.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(destination.parent).free<FLOOR+f['bytes']+CHUNK: raise RuntimeError('Restore disk floor')
    s3=S3(c['manifest']['bucket']);s3.validate()
    partial=destination.with_name(destination.name+'.s3-partial')
    with partial.open('xb') as out:
        for chunk in f['chunks']:
            r=c['chunks'][chunk['sha256']]
            with tempfile.TemporaryDirectory(dir=destination.parent) as td:
                p=Path(td)/'chunk';s3.get(r['key'],r['version_id'],p)
                assert p.stat().st_size==chunk['bytes'] and sha_file(p)==chunk['sha256']
                with p.open('rb') as src: shutil.copyfileobj(src,out)
        out.flush();os.fsync(out.fileno())
    assert partial.stat().st_size==f['bytes'] and sha_file(partial)==f['sha256']
    os.chmod(partial,f['mode']);os.utime(partial,ns=(f['signature'][3],f['signature'][3]))
    # No clobber if another process creates destination while downloading.
    os.link(partial,destination);partial.unlink()
    print('RESTORED',relative,str(destination),f['sha256'],flush=True)

def evict(packet):
    c=readj(packet/'catalog.json');done=readj(packet/'upload_complete.json');m=c['manifest']
    assert sha_file(packet/'catalog.json')==done['catalog_sha256']
    # Catalog and receipt must be published in Git before local removal.
    for p in (packet/'catalog.json',packet/'upload_complete.json'):
        subprocess.run(['git','ls-files','--error-unmatch',str(p.relative_to(ROOT))],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        assert not subprocess.check_output(['git','status','--porcelain','--',str(p)],cwd=ROOT)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)==subprocess.check_output(['git','rev-parse','@{u}'],cwd=ROOT)
    s3=S3(m['bucket']);s3.validate()
    for r in c['chunks'].values():
        head=s3.call('s3api','head-object',*s3.object_args(r['key']),'--version-id',r['version_id'],'--checksum-mode','ENABLED')
        assert head['ContentLength']==r['bytes'] and head['ChecksumSHA256']==base64.b64encode(bytes.fromhex(r['sha256'])).decode()
    evicted=packet/'evicted';evicted.mkdir(exist_ok=True)
    with locks(ROOT,m['directories']):
        # Preflight every still-local source before deleting any of them.
        for f in m['files']:
            p=safe_path(ROOT,f['path']);receipt=evicted/(digest(f['path'].encode())+'.json')
            if not p.exists():
                assert receipt.exists() and readj(receipt)['sha256']==f['sha256'];continue
            assert signature(p)==f['signature'] and sha_file(p)==f['sha256'],f['path']
        # Keep tiny logs, lock files and status files local; evict only exact SQLite files.
        for f in m['files']:
            if not f['path'].endswith('.sqlite'): continue
            p=safe_path(ROOT,f['path']);receipt=evicted/(digest(f['path'].encode())+'.json')
            if not p.exists(): continue
            assert signature(p)==f['signature']
            # Durable intent precedes unlink, so interrupted eviction is recoverable.
            if not receipt.exists(): write_new(receipt,{'path':f['path'],'sha256':f['sha256'],'bytes':f['bytes'],'state':'verified_eviction_intent','epoch':time.time()})
            p.unlink();print('EVICTED',f['path'],f['bytes'],flush=True)
    removed=[f for f in m['files'] if f['path'].endswith('.sqlite') and not (ROOT/f['path']).exists()]
    write_new(packet/'eviction_complete.json',{'files':len(removed),'bytes':sum(f['bytes'] for f in removed),
              'free_bytes':shutil.disk_usage(ROOT).free,'completed_epoch':time.time(),
              'retained':'Source/results/Git, M13/M14 runs, all small run logs/locks/status files remain local.'})

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','upload','restore','evict']);p.add_argument('--packet',required=True)
    p.add_argument('--file');p.add_argument('--destination');a=p.parse_args();packet=Path(a.packet).resolve()
    with (packet/'archive.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.action=='restore':restore(packet,a.file,a.destination)
        else:globals()[a.action](packet)
if __name__=='__main__':main()
