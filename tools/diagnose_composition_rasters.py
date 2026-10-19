"""Post-hoc saved-mask comparison with goal-distance balls and bounded leaf pruning.

This is an oracle-based OBSERVER, never candidate inference or fitness. No genome
is run or altered. Fits are explanatory associations, not mechanism ablations.
"""
from pathlib import Path
import sys,json
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.composition_data import OUT,load,read_compressed
from maze_evolution.routing_transfer import lines


def main():
    choices=read_compressed(OUT/'choices.json.gz');cases,_,meta=load(OUT/'confirmation')
    aliases=['carry/0/mutation/primary','carry/1/mutation/primary',
             'carry/0/recombination/primary','carry/1/recombination/primary',
             'fresh/0/mutation/primary','fresh/2/mutation/primary']
    pids={choices['aliases'][a] for a in aliases};predicted={}
    for cid,o in cases.items():
        if not o.path:continue
        m=o.maze;ds=np.asarray(o.to_goal)
        mask=((ds>=0)&(ds<=ds[m.start])).reshape(m.h,m.w)
        fixed=np.zeros(mask.size,bool);fixed[[m.start,m.goal]]=True;fixed=fixed.reshape(mask.shape)
        values=[]
        for rounds in range(7):
            values.append(np.packbits(mask.ravel(),bitorder='little').tobytes().hex())
            degree=np.zeros(mask.shape,np.uint8)
            degree[:-1]+=mask[1:];degree[1:]+=mask[:-1]
            degree[:,:-1]+=mask[:,1:];degree[:,1:]+=mask[:,:-1]
            mask=mask & ((degree>1)|fixed)
        predicted[cid]=values
    result={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        if e['key'] not in pids:continue
        groups={}
        for r in e['rows']:
            if not r['reachable']:continue
            q=meta[r['case']]
            labels=['all_reachable','ordinary' if q['family'].startswith('ordinary_') else 'structured',q['family']]
            if q['family']=='paired':labels.append(f"paired/{q['graph']}/prefix{q['prefix']}")
            for label in set(labels):
                g=groups.setdefault(label,dict(inputs=0,mask_matches=[0]*7,emitted_mask_matches=[0]*7))
                g['inputs']+=1
                for k,value in enumerate(predicted[r['case']]):
                    g['mask_matches'][k]+=r['mask']==value
                    g['emitted_mask_matches'][k]+=r['mask']==value and r['status']=='emitted'
        result[e['key']]=groups
    packet=dict(candidate_calls=0,post_hoc=True,
        interpretation='Oracle-based observer fit on inspected saved outputs. A fit does not prove the internal mechanism, stopping logic or causal necessity; no predictor enters inference, evolution or model selection.',
        predictor='Goal-distance ball with radius equal to source-to-goal shortest distance, then 0 through 6 synchronous rounds deleting degree<=1 output sites except source and goal.',
        aliases={a:choices['aliases'][a] for a in aliases},results=result)
    (OUT/'raster_hypothesis_fit.json').write_text(json.dumps(packet,indent=2)+'\n')
    for a,p in packet['aliases'].items():print(a,result[p]['all_reachable'],result[p]['structured'])


if __name__=='__main__':main()
