"""Retrospective saved-raster illustration of the new K descendant and its limit."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from maze_evolution.robustness_data import OUT,load
from maze_evolution.routing_transfer import lines
from plot_robustness_pressure import save

alias='robustness/carry/evolved/pair/evolution/2/archives/context'
physical=json.loads((OUT/'final/aliases.json').read_text())[alias]
cases,contexts,meta=load(OUT/'final')
c=next(c for c in contexts if c['goal_shape']=='turning' and c['prefix']==2 and c['long'])
ids=[cid for f in ('fork','cycle') for cid in c['poses'][0]['cases'][f]];records={}
for r in lines(OUT/'final/responses.jsonl.gz'):
    if r['model']==physical and r['row']['case'] in ids:records[r['row']['case']]=r['row']
fig,axes=plt.subplots(2,2,figsize=(8,8));colors=['#e3e6e4','#ffffff','#3a9e80','#d76c50','#e5b44d'];cert=[]
for cid,row in records.items():
    md=meta[cid];o=cases[cid];col=int(md['family']=='cycle');ax=axes[md['side'],col];n=o.maze.w
    mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:n*n].astype(bool)
    truth=np.zeros(n*n,bool);truth[o.path]=True;grid=np.frombuffer(o.maze.cells,np.uint8).copy()
    grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
    ax.imshow(grid.reshape(n,n),cmap=ListedColormap(colors),vmin=0,vmax=4,interpolation='nearest')
    for p,l in ((o.maze.start,'S'),(o.maze.goal,'G')):ax.text(p%n,p//n,l,ha='center',va='center',fontweight='bold',color='#253a60')
    ax.set_xticks([]);ax.set_yticks([])
    ax.set_title(('Fork' if col==0 else 'Matched real cycle')+f' · goal {md["side"]+1}\n'+('Shortest path' if row['optimal'] else row['failure'].replace('_',' '))+f' · {len(o.path)-1} edges',fontsize=10)
    cert.append(dict(model=physical,row=row,metadata=md))
fig.suptitle('New random-origin descendant: robust short-prefix forks, limited transfer',fontsize=13)
fig.legend(handles=[Patch(color=colors[i],label=l) for i,l in [(2,'Correct output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False)
fig.text(.5,.045,'Same frozen genome and context; example chosen after evaluation. No extra candidate calls.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.08,1,.94));save(fig,'new_descendant_limit')
(OUT/'visuals/new_descendant_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')
