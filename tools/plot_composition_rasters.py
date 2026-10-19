"""Post-hoc illustrations and distance counts from saved normal S outputs only."""
from pathlib import Path
from collections import Counter
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/composition_study'
def read(path):
    with gzip.open(path,'rt') as f:return json.load(f)
choices=read(OUT/'choices.json.gz');meta=read(OUT/'confirmation/metadata.json.gz')
cases={r['case_id']:r for r in read(OUT/'confirmation/mazes.json.gz')}
specs=[('fresh/2/mutation/primary','fork',1,'Fresh mutation descendant\nFork, prefix 1'),
       ('fresh/2/mutation/primary','fork',2,'Same fresh descendant\nFork, prefix 2'),
       ('carry/0/mutation/primary','cycle',1,'Carried mutation descendant\nAlternative cycle, prefix 1'),
       ('carry/0/mutation/primary','cycle',2,'Same carried descendant\nAlternative cycle, prefix 2')]
targets={}
for row,(alias,graph,prefix,label) in enumerate(specs):
    for side in (0,1):
        cid=next(c for c,m in meta.items() if m['index']==24 and m['pose']==0 and m['graph']==graph and m['prefix']==prefix and m['side']==side and m['family']=='paired')
        targets[choices['aliases'][alias],cid]=row,side
saved={};distances={}
with gzip.open(OUT/'confirmation/responses.jsonl.gz','rt') as f:
    for line in f:
        e=json.loads(line);dist=Counter()
        for r in e['rows']:
            q=meta[r['case']]
            if q['family'].startswith('ordinary_') and r['optimal']:dist[len(q['path'])-1]+=1
            if (e['key'],r['case']) in targets:saved[e['key'],r['case']]=r
        distances[e['key']]=dict(sorted(dist.items()))
(OUT/'ordinary_distance_counts.json').write_text(json.dumps(distances,indent=2)+'\n')
assert set(saved)==set(targets)
fig,axes=plt.subplots(4,2,figsize=(9,12))
colors=ListedColormap(['#172633','#f2f4f7','#29a178','#e89132','#dc7190'])
for key,(row,col) in targets.items():
    r=saved[key];m=cases[r['case']];q=meta[r['case']];ax=axes[row,col]
    cells=np.frombuffer(bytes.fromhex(m['cells_hex']),np.uint8).copy()
    emitted=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(cells)].astype(bool)
    expected=np.zeros(len(cells),bool);expected[q['path']]=True
    cells[emitted & expected]=2;cells[emitted & ~expected]=3;cells[~emitted & expected]=4
    ax.imshow(cells.reshape(m['h'],m['w']),cmap=colors,vmin=0,vmax=4,interpolation='nearest')
    for pos,symbol,color in ((m['start'],'S','#40a9e8'),(m['goal'],'G','#b685ed')):
        y,x=divmod(pos,m['w']);ax.scatter(x,y,s=90,c=color,edgecolors='white',linewidths=.7)
        ax.text(x+.65,y-.1,symbol,color=color,fontsize=10,fontweight='bold')
    ax.set_xticks([]);ax.set_yticks([])
    if col==0:ax.set_ylabel(specs[row][3],fontsize=11,labelpad=12)
    if row==0:ax.set_title('Goal A' if col==0 else 'Goal B',fontsize=12)
    ax.set_xlabel(('Correct shortest path' if r['optimal'] else 'Incorrect: '+r['failure'].replace('_',' '))+f" · {len(q['path'])-1} required edges",fontsize=9)
fig.suptitle('Normal outputs reveal acquired abilities and remaining boundaries',fontsize=14,y=.99)
fig.text(.5,.025,'Green: correct path pixels · Orange: extra output · Pink: missing path · White: unlit open cell\nPost-hoc illustration: first 4/6-arm stress context, pose 0, both goals; full board shown.\nThese are saved native emissions. No additional candidate evaluation or selection.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.08,1,.965))
fig.savefig(OUT/'normal_outputs.png',dpi=170)
fig.savefig(OUT/'normal_outputs.pdf')
(OUT/'normal_output_examples.json').write_text(json.dumps([dict(alias=specs[row][0],case=cid,model=pid,optimal=saved[pid,cid]['optimal']) for (pid,cid),(row,col) in targets.items()],indent=2)+'\n')
