"""Verify M2, create guarded SQLite backups, and seal the completed record."""
import json,shutil,sqlite3,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.wave_accessibility import OUT,RUN,ROOT,check,readz,writej,sha
from maze_evolution.deep_campaign_store import writer_lock

def main():
    config=check();assert not (OUT/'completion.json').exists()
    for name in ('screen_audit.json','final_audit.json'):assert json.loads((OUT/name).read_text())['passed']
    prior=json.loads((ROOT/'results/modular_pilot/completion.json').read_text())
    for p,h in prior['files'].items():assert sha(ROOT/p)==(h['sha256'] if isinstance(h,dict) else h),p
    for directory,name in ((RUN,'screen_001'),(RUN/'final','final_001')):
        target=RUN/'backups'/f'{name}.sqlite';assert not target.exists()
        size=(directory/'campaign.sqlite').stat().st_size
        current=sum(p.stat().st_size for base in (RUN,OUT) for p in base.rglob('*') if p.is_file())
        assert current+size*1.2<config['storage_bytes']
        assert shutil.disk_usage(RUN).free-size*1.2>=config['disk_free_floor_bytes']
        target.parent.mkdir(exist_ok=True)
        with writer_lock(directory):
            a=sqlite3.connect(f'file:{directory}/campaign.sqlite?mode=ro',uri=True);b=sqlite3.connect(target)
            a.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok'
            assert a.execute('select count(*) from tasks').fetchone()==b.execute('select count(*) from tasks').fetchone()
            a.close();b.close()
        writej(OUT/f'backup_{name}.json',dict(path=str(target.relative_to(ROOT)),bytes=target.stat().st_size,sha256=sha(target),integrity_check='ok',original_preserved=True))
    files=dict(json.loads((OUT/'registration.json').read_text())['files'])
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[ROOT/'docs/WAVE_ACCESSIBILITY.md',ROOT/'docs/WAVE_ACCESSIBILITY_AUDIT_NOTE.md',*ROOT.glob('tools/*m2*.py'),ROOT/'tools/inspect_wave_accessibility.py',ROOT/'tools/report_wave_accessibility.py',ROOT/'tools/diagnose_wave_accessibility.py']
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    for p,h in files.items():assert sha(ROOT/p)==h,p
    writej(OUT/'completion.json',dict(status='complete and audited',phase='M2',files=files,
        exclusion_layouts=readz(OUT/'whole_layout_exclusions.json.gz')['count'],prior_completion_verified=True,
        original_scientific_source_unchanged=True,audit_repair='df6ddaf; JSON tuple/list normalization only',
        registration='9608c28',choices_freeze='80d35f7',long_campaign_launched=False,
        local_journals_preserved=True,sqlite_backups_verified=True))
    print('Sealed',len(files),'hashes',flush=True)

if __name__=='__main__':main()
