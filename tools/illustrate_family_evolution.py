"""Post-hoc view of already frozen final rasters; zero new candidate calls."""
from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/family_evolution'
def read(p):
 with gzip.open(p,'rt') as f:return json.load(f)
choices=read(OUT/'choices.json.gz');meta=read(OUT/'confirmation/metadata.json.gz')
mazes={r['case_id']:r for r in read(OUT/'confirmation/mazes.json.gz')}
aliases=['fresh/0/current_mutation/primary','fresh/0/resample/primary'];pids=[choices['aliases'][a] for a in aliases]
example=next(q for q in meta.values() if q['family']=='paired' and q['graph']=='fork' and q['prefix']==0 and q['pose']==0 and q['arm']==[4,6])
ids={(q['prefix'],q['side']):c for c,q in meta.items() if q['template']==example['template'] and q['family']=='paired' and q['graph']=='fork' and q['prefix'] in (0,1) and q['pose']==0}
assert len(ids)==4
records={}
with gzip.open(OUT/'confirmation/responses.jsonl.gz','rt') as f:
 for line in f:
  e=json.loads(line)
  if e['key'] in pids:records[e['key']]={r['case']:r for r in e['rows'] if r['case'] in ids.values()}
fig,axes=plt.subplots(2,4,figsize=(13,7.4),layout='constrained')
packet=dict(post_hoc_illustration=True,new_inference_calls=0,context=example['template'],models={},cases={c:mazes[c] for c in ids.values()})
for row,(alias,pid) in enumerate(zip(aliases,pids)):
 rr=records[pid];assert all(rr[ids[0,s]]['optimal'] for s in (0,1));assert not all(rr[ids[1,s]]['optimal'] for s in (0,1))
 packet['models'][alias]=dict(item=choices['items'][alias],rows=rr)
 for col,(prefix,side) in enumerate(((0,0),(0,1),(1,0),(1,1))):
  cid=ids[prefix,side];m=mazes[cid];r=rr[cid];w,h=m['w'],m['h']
  cells=np.frombuffer(bytes.fromhex(m['cells_hex']),np.uint8).reshape(h,w)
  mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:w*h].reshape(h,w)
  rgb=np.zeros((h,w,3));rgb[:]=[.14,.19,.23];rgb[cells>0]=[.91,.93,.94]
  rgb[mask>0]=[.07,.49,.50] if r['optimal'] else [.82,.37,.30]
  ax=axes[row,col];ax.imshow(rgb,interpolation='nearest');ax.set_xticks([]);ax.set_yticks([])
  for name,letter,color in (('start','S','#216036'),('goal','G','#682d80')):
   y,x=divmod(m[name],w);ax.scatter([x],[y],s=105,c=color,edgecolors='white',linewidths=.8);ax.text(x,y,letter,ha='center',va='center',color='white',fontsize=7,fontweight='bold')
  outcome='Shortest path' if r['optimal'] else r['failure'].replace('_',' ')
  ax.set_title(f'Prefix {prefix}, goal {"AB"[side]}\n{outcome}',fontsize=10)
  if col==0:ax.set_ylabel('Mutated descendant' if row==0 else 'Unmutated random draw',fontsize=11)
for side in (0,1):
 a,b=[mazes[ids[p,side]] for p in (0,1)];assert a['cells_hex']==b['cells_hex'] and a['goal']==b['goal']
fig.suptitle('Same unseen fork: move the source one cell upstream\nActual emitted rasters — teal is correct, coral is unsuccessful. S = source, G = goal.',fontsize=14)
fig.savefig(OUT/'routing_boundary.png',dpi=170);fig.savefig(OUT/'routing_boundary.pdf')
(OUT/'routing_boundary.json').write_text(json.dumps(packet,indent=2)+'\n')
