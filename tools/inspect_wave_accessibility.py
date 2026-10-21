"""Read-only M2 journal status, including pending charged work."""
import argparse,json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.wave_accessibility import RUN
p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');a=p.parse_args()
d=RUN/'final' if a.final else RUN
c=sqlite3.connect(f'file:{d}/campaign.sqlite?mode=ro',uri=True)
settings={k:unpacked(v) for k,v in c.execute('select key,value from settings')}
print(json.dumps(dict(latest=settings.get('latest'),usage=settings.get('usage'),tasks=dict(c.execute('select status,count(*) from tasks group by status')),bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())),indent=2));c.close()
