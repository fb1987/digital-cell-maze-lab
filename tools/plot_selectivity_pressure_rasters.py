"""Render a saved retrospective paired example; no candidate evaluation."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/selectivity_pressure'
p=json.loads((OUT/'illustration.json').read_text());fig,axes=plt.subplots(2,3,figsize=(11,7),layout='constrained')
colors={'wall':'#28343d','open':'#e8edf0','route':'#009e73','extra':'#d55e00'}
from matplotlib.colors import to_rgb
for row,case in enumerate(p['cases']):
 w,h=case['width'],case['height'];route=set(case['path'])
 for col,(alias,title) in enumerate(((None,'Oracle: evaluation only'),('fresh/0/selective/primary','Fresh replicate 0\nCurrent = selective'),('carry/0/current/primary','Preserved carried specialist'))):
  if alias is None:lit=route
  else:
   bits=int.from_bytes(bytes.fromhex(case['rows'][alias]['mask']),'little');lit={k for k in range(w*h) if (bits>>k)&1}
  grid=np.zeros((h,w,3))
  for k,open_ in enumerate(case['cells']):
   color=colors['route'] if k in lit and k in route else colors['extra'] if k in lit else colors['open'] if open_ else colors['wall']
   grid[k//w,k%w]=to_rgb(color)
  ax=axes[row,col];ax.imshow(grid,interpolation='nearest')
  for name,k in [('S',case['start']),('G',case['goal'])]:ax.text(k%w,k//w,name,ha='center',va='center',color='white',weight='bold',fontsize=9)
  ax.set_xticks([]);ax.set_yticks([]);ax.set_title(title if row==0 else '',fontsize=11)
  ax.set_xlabel(f'Goal {row+1}: {len(route)} route cells, {len(lit-route)} extra cells')
fig.suptitle('A new prefix-two cycle: full route present, but output is still invalid\nSaved normal emissions; retrospectively chosen illustration, not a new test.',fontsize=13)
fig.legend(handles=[Patch(color=colors[k],label=label) for k,label in [('route','Illuminated route'),('extra','Unwanted output'),('open','Open, unlit'),('wall','Wall')]],loc='outside lower center',ncol=4,frameon=False)
fig.savefig(OUT/'routing_boundary.png',dpi=170);fig.savefig(OUT/'routing_boundary.pdf')
