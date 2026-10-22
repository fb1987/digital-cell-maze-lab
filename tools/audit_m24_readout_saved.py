"""Posthoc exact recurrence verification on already-saved M24 completed ticks."""
import sys,json,base64,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.branch_causality import *

def main():
    import numpy as np
    check();assert not (OUT/'readout_recurrence_audit.json').exists();started=time.time()
    variants=readz(OUT/'variants.json.gz');models={i['id']:i['model'] for i in variants['items']}
    focal=Genome.from_dict(models[FOCAL]['genome']);data=readz(OUT/'panel.json.gz')
    maze={m['case_id']:m for m in data['mazes']};records=[];values=0
    for rec in readz(OUT/'traces.json.gz')['records']:
        g=Genome.from_dict(next(models[i]['genome'] for i in rec['aliases'] if i in models))
        assert g.body.blocks[2]==focal.body.blocks[2]
        p=g.body.ports[2];assert p in ((0,1,3,8,5,4,7,6,2,9),(0,1,3,2,5,4,7,6,8,9))
        h=np.frombuffer(base64.b64decode(rec['history_base64']),np.uint16).reshape(rec['shape'])
        old=h[:-1].astype(np.uint32);actual=h[1:,2];m=maze[rec['case']]
        live=np.array([bool(v) for v in bytes.fromhex(m['cells_hex'])]);source=np.zeros(m['w']*m['h'],bool);source[m['start']]=True
        assert not old[:,8].any()
        increment=np.where(old[:,4]!=0,(old[:,0]!=0) != (old[:,6]!=0),0)
        subtotal=np.minimum(65535,increment+(old[:,2] if p[3]==2 else 0))
        expected=np.where(old[:,1]!=0,np.where(source,old[:,1],subtotal),0)
        assert np.array_equal(expected[:,live],actual[:,live]),rec['aliases']
        count=int(actual[:,live].size);values+=count
        records.append(dict(aliases=rec['aliases'],case=rec['case'],completed_ticks=len(h)-1,open_site_predictions=count,ports_saved=p[3]==8))
    writej(OUT/'readout_recurrence_audit.json',dict(status='PASS',scope='Posthoc saved-only exact C2 recurrence check, completed ticks/open sites',new_inference_calls=0,
        open_site_predictions=values,records=records,wall_seconds=time.time()-started,
        limitation='One selected lineage/interventions, reused mechanism data; no independent confirmation or full second VM.'))

if __name__=='__main__':main()
