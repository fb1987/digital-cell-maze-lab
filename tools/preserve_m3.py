"""Guarded M3 backup/exclusion preservation, then explicit completion sealing."""
import argparse,json,shutil,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.wave_continuation import ROOT,OUT,RUN,check,readz,writez,writej,sha
from maze_evolution.deep_campaign_store import writer_lock,unpacked

def preserve():
    config=check();assert not (OUT/'completion.json').exists()
    workflow=json.loads((RUN/'workflow_status.json').read_text());assert workflow['state']=='audited_ready_for_report'
    for name in ('search_audit.json','final_audit.json'):assert json.loads((OUT/name).read_text())['status']=='PASS'
    with writer_lock(RUN/'workflow'):
        for directory,name in ((RUN,'search_001'),(RUN/'final','final_001')):
            target=RUN/'backups'/f'{name}.sqlite';assert not target.exists()
            size=(directory/'campaign.sqlite').stat().st_size
            current=sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())
            assert current+size*1.2<config['storage_bytes'],'Backup would exceed phase storage bound'
            assert shutil.disk_usage(RUN).free-size*1.2>=config['disk_free_floor_bytes'],'Backup would violate free-space floor'
            target.parent.mkdir(exist_ok=True)
            with writer_lock(directory):
                a=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True);b=sqlite3.connect(target)
                assert a.execute('select count(*) from stages where complete=0').fetchone()[0]==0
                a.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok'
                for table in ('settings','layouts','stages','tasks','states'):
                    assert a.execute(f'select count(*) from {table}').fetchone()==b.execute(f'select count(*) from {table}').fetchone()
                assert a.execute('select key,value from settings order by key').fetchall()==b.execute('select key,value from settings order by key').fetchall()
                a.close();b.close()
            writej(OUT/f'backup_{name}.json',dict(path=str(target.relative_to(ROOT)),bytes=target.stat().st_size,sha256=sha(target),integrity_check='ok',counts_and_settings_equal=True,original_preserved=True))
            print('Verified backup',name,flush=True)
    seen=set(readz(OUT/'exclusions.json.gz')['hashes']);seen.update(readz(OUT/'search_exclusions.json.gz')['hashes']);seen.update(readz(OUT/'confirmation.json.gz')['new_layouts'])
    c=sqlite3.connect(f'file:{RUN}/final/campaign.sqlite?mode=ro',uri=True)
    assert seen=={r[0] for r in c.execute('select hash from layouts')};c.close()
    writez(OUT/'whole_layout_exclusions.json.gz',dict(count=len(seen),hashes=sorted(seen)))
    logs=OUT/'execution_logs';logs.mkdir(exist_ok=True)
    for p in RUN.glob('*.log'):
        target=logs/p.name;assert not target.exists();shutil.copyfile(p,target)
    shutil.copyfile(RUN/'workflow_status.json',OUT/'workflow_completion.json')
    print('Exclusion layouts',len(seen),flush=True)

def seal():
    check();assert not (OUT/'completion.json').exists()
    for name in ('report.md','completion_details.json','backup_search_001.json','backup_final_001.json','whole_layout_exclusions.json.gz'):
        assert (OUT/name).exists(),name
    prior=json.loads((ROOT/'results/wave_accessibility/completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==(h['sha256'] if isinstance(h,dict) else h),p
    files=dict(json.loads((OUT/'registration.json').read_text())['files'])
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[ROOT/'tools/preserve_m3.py',ROOT/'tools/summarize_m3_completion.py',ROOT/'tools/report_m3.py',ROOT/'docs/WAVE_CONTINUATION_PROGRESS.md']
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    for p,h in files.items():assert sha(ROOT/p)==h,p
    writej(OUT/'completion.json',dict(status='complete and audited',phase='M3',registration='302cab5',choices_freeze='d1f988a',
        files=files,exclusion_layouts=readz(OUT/'whole_layout_exclusions.json.gz')['count'],prior_completion_verified=True,
        source_unchanged=True,protocol_deviations=False,local_journals_preserved=True,sqlite_backups_verified=True,
        new_search_launched=False))
    print('Completion sealed',len(files),'hashes',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','seal']);a=p.parse_args();globals()[a.action]()
