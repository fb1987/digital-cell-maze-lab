"""Finish the user-authorized archive after its upload, or fail without cleanup.
One archival workflow only; never launches a scientific experiment.
"""
import fcntl, hashlib, json, os, sqlite3, subprocess, sys, time, traceback
from pathlib import Path
from s3_research_archive import ROOT, sha_file, readj, write_new, S3

P=ROOT/'results/storage_archive/20261021'

def cmd(*a):
    print('RUN',*a,flush=True)
    subprocess.run(a,cwd=ROOT,check=True)

def publish(paths,message):
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT), 'Unexpected staged changes; stop before publishing'
    cmd('git','add','--',*paths)
    cmd('git','diff','--cached','--check')
    cmd('git','commit','-m',message)
    cmd('git','push')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)==subprocess.check_output(['git','rev-parse','@{u}'],cwd=ROOT)

def main():
    with (P/'finish.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (P/'finish_complete.json').exists()
        launch=readj(P/'upload_launch.json')
        while not (P/'upload_complete.json').exists():
            try:os.kill(launch['pid'],0)
            except ProcessLookupError:raise RuntimeError('Upload stopped before successful completion; inspect preserved log. No cleanup.')
            time.sleep(15)
        # Wait until uploader releases its lock; never overlap writers.
        with (P/'archive.lock').open('a') as active:
            fcntl.flock(active,fcntl.LOCK_EX)
        done=readj(P/'upload_complete.json');catalog=readj(P/'catalog.json')
        assert sha_file(P/'catalog.json')==done['catalog_sha256']
        f=min((f for f in catalog['manifest']['files'] if f['path'].endswith('.sqlite')),key=lambda f:f['bytes'])
        restored=P/'restore_test.sqlite'
        cmd(sys.executable,'tools/s3_research_archive.py','restore','--packet',str(P),'--file',f['path'],'--destination',str(restored))
        db=sqlite3.connect(restored.as_uri()+'?mode=ro&immutable=1',uri=True)
        checks=db.execute('PRAGMA quick_check').fetchall()
        tables=db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall();db.close()
        assert checks==[('ok',)] and tables
        write_new(P/'restore_test.json',{'status':'PASS','catalog_sha256':done['catalog_sha256'],
                  'file':f['path'],'bytes':f['bytes'],'original_sha256':f['sha256'],'restored_sha256':sha_file(restored),
                  'sqlite_quick_check':'ok','tables':[x[0] for x in tables],'epoch':time.time()})
        restored.unlink() # Disposable verified restore, never an original research record.
        verify={}
        for seal in ['results/exploration_allocation/prepared_manifest.json','results/mutation_scope/completion.json']:
            data=readj(ROOT/seal)
            for rel,h in data['files'].items():assert sha_file(ROOT/rel)==h,rel
            for rel,item in data.get('local_records',{}).items():
                h=item['sha256'] if isinstance(item,dict) else item
                assert sha_file(ROOT/rel)==h,rel
            verify[seal]={'files':len(data['files']),'local_records':len(data.get('local_records',{}))}
        write_new(P/'retained_dependency_verification.json',verify)
        # All version-pinned receipts and restore evidence published before removal.
        paths=['tools/s3_research_archive.py','tools/finish_s3_research_archive.py','tests/test_s3_research_archive.py',
               'results/storage_archive/20261021/catalog.json','results/storage_archive/20261021/chunks',
               'results/storage_archive/20261021/upload_complete.json','results/storage_archive/20261021/upload_launch.json',
               'results/storage_archive/20261021/finish_launch.json','results/storage_archive/20261021/restore_test.json',
               'results/storage_archive/20261021/retained_dependency_verification.json','results/storage_archive/20261021/restore_instructions.json']
        publish(paths,'Preserve verified S3 archive catalog and successful database restore before local eviction')
        cmd(sys.executable,'tools/s3_research_archive.py','evict','--packet',str(P))
        eviction=readj(P/'eviction_complete.json')
        # Add a new handoff without modifying any historical seals.
        agents=ROOT/'AGENTS.md';text=agents.read_text()
        block='''<!-- S3-ARCHIVE-STATUS-START -->
Current October21,2026: user explicitly authorized S3 archival and local space
recovery. Closed runs through M12 plus deep/C1 are archived in private versioned
bucket digital-cell-maze-lab-research-384268139212-use2 (us-east-2), using existing
personal-os AWS profile. Exact original bytes are preserved as SHA256 chunks with
version-pinned catalog in results/storage_archive/20261021/. EVERY unique chunk
was downloaded and hash verified; one full SQLite restore passed byte hash and
quick_check BEFORE local eviction. Catalog/receipts/restore evidence pushed first.
Only exact archived .sqlite files removed locally; small logs/locks/status files,
all results/source/Git/dependency manifests, and M13/M14 runs remain local.
Historical instructions saying journals are local describe PRE-MIGRATION state.
Never rerun old campaigns to recreate missing journals. Restore exact files via
 tools/s3_research_archive.py restore; see restore_instructions.json and catalog.
Archive does not expire automatically. Keep manifests, pinned object versions,
old seals, and referenced layout bases. Credentials never stored in project.
M14 remains PAUSED BY USER, prepared/not registered/not launched. S3 migration
is not authorization to start M14. After explicit resume verify all M14 preparation
hashes and new passing storage plan before registration/commit/push/science.
<!-- S3-ARCHIVE-STATUS-END -->

'''
        assert '<!-- S3-ARCHIVE-STATUS-START -->' not in text
        agents.write_text(text.replace('## Immediate first task\n\n','## Immediate first task\n\n'+block,1))
        final={'status':'complete','upload':done,'eviction':eviction,'restore_test':'PASS','retained_dependency_verification':verify,
               'scientific_experiment_started':False,'completed_epoch':time.time()}
        write_new(P/'finish_complete.json',final)
        # Store completion and recovery instructions in the bucket as well as Git.
        s3=S3(catalog['manifest']['bucket'])
        for name in ['restore_instructions.json','restore_test.json','eviction_complete.json','finish_complete.json']:
            p=P/name;s3.put('catalogs/20261021/evidence/'+name,p,sha_file(p))
        publish(['AGENTS.md','results/storage_archive/20261021/evicted',
                 'results/storage_archive/20261021/eviction_complete.json','results/storage_archive/20261021/finish_complete.json'],
                'Complete verified S3 migration and recover local research storage')
        write_new(P/'published_complete.json',{'status':'published_complete','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'epoch':time.time()})
        print('MIGRATION COMPLETE',json.dumps(final),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException:
        traceback.print_exc()
        failure=P/('finish_failure_'+str(time.time_ns())+'.json')
        write_new(failure,{'traceback':traceback.format_exc(),'epoch':time.time(),'automatic_resume':False})
        raise
