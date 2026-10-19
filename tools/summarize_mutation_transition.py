"""Post-registration compact diagnosis from saved P records; no inference."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_study import read_compressed
from maze_evolution.mutation_transition_data import OUT
p=read_compressed(OUT/'panel.json.gz');a=read_compressed(OUT/'analysis.json.gz');result={}
for top in ('local','evolved'):
    events=[]
    for tr in a['transitions'][top]:
        if tr['gained'] or tr['lost']:
            ev=next(e for e in p['events'] if (e['rep'],e['index'],e['walk'],e['depth'])==(0,71,0,tr['depth']))
            events.append(dict(depth=tr['depth'],gained=tr['gained'],lost=tr['lost'],event=ev['event'],parent=ev['item']['parent'],child=ev['item']['id'],genes=len(ev['item']['genome']['genes'])))
    target=a['normal'][top+'/route/d16'];result[top]=dict(transitions=events,target={k:v for k,v in target.items() if k not in ('details','strata')},
        strata=target['strata'],mechanisms=a['mechanisms'][p['aliases'][top+'/route/d16']])
result['controls']={alias:{k:m[k] for k in ('pairs','corridors','no_path','false_no_path')} for alias,m in a['normal'].items() if '/route/' not in alias}
result['post_registration']=True;result['new_inference_calls']=0
(OUT/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({top:{k:v for k,v in result[top].items() if k!='strata'} for top in ('local','evolved')},indent=2))
