"""Replay the frozen auditor without overwriting any sealed experiment artifact."""
from pathlib import Path
from datetime import datetime,timezone
import contextlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution import family_evolution_audit as frozen


def main():
    for study,tool in [('composition_study','archive_composition_births.py'),('family_evolution','archive_family_evolution_births.py')]:
        if not (ROOT/'results'/study/'reproduction.jsonl.gz').exists():
            subprocess.run([sys.executable,str(ROOT/'tools'/tool),'restore'],check=True)
    seal=json.loads((frozen.OUT/'completion.json').read_text())
    def verify_seal():
        for name,expected in seal['source_and_artifact_sha256'].items():assert frozen.sha(ROOT/name)==expected,name
    verify_seal()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest=ROOT/'output/family_evolution_replays'/stamp;dest.mkdir(parents=True)
    original=frozen.write_json
    def isolated_write(path,value):
        assert path==frozen.OUT/'audit.json','Unexpected write from frozen auditor'
        original(dest/'audit.json',value)
    print(f'Replaying frozen audit. Progress log: {dest / "console.txt"}',flush=True)
    frozen.write_json=isolated_write
    try:
        with (dest/'console.txt').open('w') as log,contextlib.redirect_stdout(log):
            frozen.audit()
            print('Fresh replay packet (the frozen auditor printed the sealed original above):')
            print((dest/'audit.json').read_text())
    finally:frozen.write_json=original
    verify_seal();packet=json.loads((dest/'audit.json').read_text());assert packet['passed']
    print(json.dumps(dict(passed=True,sealed_artifacts_unchanged=True,wall_seconds=packet['wall_seconds'],replay_packet=str(dest/'audit.json')),indent=2))

if __name__=='__main__':main()
