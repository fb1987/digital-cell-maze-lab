"""Read-only M1 journal status and development assessment comparisons."""
import argparse,json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.modular_pilot import RUN,OUT
from maze_evolution.deep_campaign_store import unpacked
from maze_evolution.deep_confirmation_analysis import capabilities

p=argparse.ArgumentParser();p.add_argument('--assessment',type=int);p.add_argument('--output');args=p.parse_args()
c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
settings={k:unpacked(v) for k,v in c.execute('select key,value from settings')}
result=dict(latest_stage=settings['latest'],usage=settings['usage'],stages=[list(r) for r in c.execute('select n,kind,generation,complete from stages order by n desc limit 3')],assessment_rounds=[r[0] for r in c.execute("select generation from stages where kind='assessment' and complete=1 order by n")])
if args.assessment is not None:
 row=c.execute("select n,input,decision from stages where kind='assessment' and complete=1 and generation=?",(args.assessment,)).fetchone()
 assert row,'Assessment not complete';n,blob,dec=row;data=unpacked(blob);decisions=unpacked(dec)
 states=unpacked(c.execute('select value from states where stage=?',(n,)).fetchone()[0]);rows=[{} for _ in states]
 for blob, in c.execute('select result from tasks where stage=? order by n',(n,)):
  for e in unpacked(blob)['entries']:
   for k,i in e['aliases']:rows[k][i]=e['rows']
 summaries=[]
 for k,s in enumerate(states):
  summaries.append(dict(condition=s['name'],nominees=[dict(id=i['id'],mutation_depth=i['mutation_depth'],root=i['root'],metrics=capabilities(rows[k][i['id']],data['metadata'])['summary']) for i in s['nominees']],frozen=[dict(id=i['id'],metrics=capabilities(rows[k][i['id']],data['metadata'])['summary']) for i in s['frozen']]))
 result['development_assessment']=dict(round=args.assessment,conditions=summaries,independent_confirmation=False)
c.close()
text=json.dumps(result,indent=2)
if args.output:Path(args.output).write_text(text+'\n')
else:print(text)
