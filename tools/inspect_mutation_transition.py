"""Posthoc static data-flow certificate and input-alias counts; no inference."""
import json,sys
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_study import read_compressed
from maze_evolution.mutation_transition_data import OUT,load
p=read_compressed(OUT/'panel.json.gz');a=read_compressed(OUT/'analysis.json.gz');cert={}
for depth in (9,16):
    genes=p['items'][f'route/d{depth}']['genome']['genes']
    writes=lambda register,stop:[(i,g) for i,g in enumerate(genes[:stop]) if g[0]!=13 and g[1]==register]
    stores=[(i,g) for i,g in enumerate(genes) if g[0]==13 and g[1]==1]
    store=stores[-1];assert store[1]==[13,1,36,0,0,0,64]
    subtract=writes(36,store[0])[-1];assert subtract==(112,[3,36,49,44,0,0,64]);assert writes(44,subtract[0])==[]
    copy=writes(49,subtract[0])[-1];assert copy==(63,[0,49,55,0,0,0,64])
    read=writes(55,copy[0])[-1];assert read==(54,[15,55,2,0,0,3,64])
    cert[str(depth)]=dict(read=read,copy=copy,subtract=subtract,final_channel1_store=store,register44_writers=[],
        derived_semantics='After a complete tick, channel1 receives the minimum positive prior channel2 value at the four cardinal neighbors at radius1 locally or radius8 nonlocally; zero if none. Gates unconditional; R44 resets to zero at every site.')
cases,_,meta=load(OUT/'confirmation');by=defaultdict(list)
for cid,m in meta.items():
    if m['family']=='paired':by[m['config']+f'/pose{m["pose"]}'].append(cid)
unique={};details=a['normal']['local/route/d16']['details']
for pair,ids in by.items():
    ids.sort(key=lambda cid:meta[cid]['side']);x,y=[cases[c].maze for c in ids];key=(x.cells,x.start,x.goal,y.goal)
    if key in unique:assert unique[key]==details[pair]['complete']
    unique[key]=details[pair]['complete']
result=dict(post_registration=True,new_candidate_calls=0,static_dataflow=cert,
    raw_paired_opportunities=len(by),distinct_paired_inputs=len(unique),raw_successes=sum(d['complete'] for d in details.values()),distinct_successes=sum(unique.values()),
    signature_equivalence=dict(depth0_to8=len({a['normal'][f'local/route/d{i}']['response_signature'] for i in range(9)})==1,depth9_to16=len({a['normal'][f'local/route/d{i}']['response_signature'] for i in range(9,17)})==1,fields=['case','mask','status','steps'],excludes=['internal states','work counters']),
    work={str(i):a['normal'][f'local/route/d{i}']['work'] for i in (0,8,9,16)})
(OUT/'static_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
