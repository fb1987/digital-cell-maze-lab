"""Saved V12L counts and retrospective raster illustration; no inference."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from maze_evolution.lineage_confirmation_data import OUT,load
from maze_evolution.routing_transfer import lines

out=OUT/'visuals';out.mkdir(exist_ok=True)
a=json.loads((OUT/'analysis.json').read_text());s=a['scores'];c=a['interventions']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,5.2),gridspec_kw={'width_ratios':[1,1.25]})
names=['k2_entry','k2_frozen','k2_parent','k2_target','k1_entry','k1_frozen','k1_parent','k1_target']
labels=['K2 entry ancestor','K2 frozen selection','K2 immediate parent','K2 descendant','K1 entry ancestor','K1 frozen selection','K1 immediate parent','K1 descendant']
y=np.arange(len(names));vals=[s[f'{n}/normal']['pairs'] for n in names]
axes[0].barh(y,vals,color=['#9aa8ac','#9aa8ac','#b4cfc6','#268b70']*2)
axes[0].set_yticks(y,labels);axes[0].invert_yaxis();axes[0].set_title('Normal complete pairs · full corpus / 1,728')
for i,v in enumerate(vals):axes[0].text(v+2,i,str(v),va='center',fontsize=9)
axes[0].set_xlim(0,max(vals+[1])*1.2);axes[0].set_xlabel('Complete two-goal shortest-path pairs')
names2=['k2_target','k2_parent','branch_broad','branch_narrow','local_long','resampled'];y=np.arange(len(names2));width=.15
modes=['normal','pulse_off','flag_off','endpoint_off','nonlocal_off'];colors=['#268b70','#d2a349','#b96b62','#8a78aa','#487fa6']
for i,mode in enumerate(modes):
 vals=[c[f'{n}/pulse_off']['normal']['pairs'] if mode=='normal' else c[f'{n}/{mode}']['intervened']['pairs'] for n in names2]
 axes[1].barh(y+(i-2)*width,vals,height=width,color=colors[i],label=['Normal','Pulse off','Goal flag off','Endpoint halt off','Nonlocal zero'][i])
axes[1].set_yticks(y,['K2 descendant','K2 parent','Old broad Branch','Old narrow Branch','Local long-prefix','Unmutated 68-gene'])
axes[1].invert_yaxis();axes[1].set_title('Mechanisms · identical fixed subset / 432 pairs');axes[1].set_xlabel('Complete two-goal shortest-path pairs')
fig.legend(loc='lower center',ncol=5,frameon=False,bbox_to_anchor=(.5,.04))
fig.suptitle('Fixed random-origin lineages: independent geometry and mechanism checks',fontsize=14)
fig.text(.5,.015,'36 independent templates; poses, locations and graph variants are correlated. No evolution or latency comparison in V12L.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.12,1,.93))
for ext in ('png','svg','pdf'):fig.savefig(out/f'lineage_and_mechanisms.{ext}',dpi=180,bbox_inches='tight')
plt.close(fig)
cases,contexts,meta=load(OUT/'confirmation')
ctx=next(c for c in contexts if c['goal_shape']=='asymmetric' and c['prefix']==2 and c['long'] and c['position']==1)
ids={cid for f in ('fork','cycle') for cid in ctx['poses'][0]['cases'][f]};rows={}
for rec in lines(OUT/'confirmation/responses.jsonl.gz'):
 if rec['mode']=='normal' and rec['model'] in ('k2_entry','k2_target') and rec['row']['case'] in ids:rows[(rec['model'],rec['row']['case'])]=rec['row']
fig,axes=plt.subplots(2,3,figsize=(10,7));colors=['#e3e6e4','#ffffff','#3a9e80','#d76c50','#e5b44d'];cert=[]
for col,(name,family,title) in enumerate([('k2_entry','fork','Actual entry ancestor'),('k2_target','fork','New descendant: fork'),('k2_target','cycle','New descendant: matched cycle')]):
 for side in (0,1):
  cid=ctx['poses'][0]['cases'][family][side];r=rows[(name,cid)];o=cases[cid];n=o.maze.w;ax=axes[side,col]
  mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:n*n].astype(bool)
  truth=np.zeros(n*n,bool);truth[o.path]=True;grid=np.frombuffer(o.maze.cells,np.uint8).copy()
  grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
  ax.imshow(grid.reshape(n,n),cmap=ListedColormap(colors),vmin=0,vmax=4,interpolation='nearest')
  for p,l in ((o.maze.start,'S'),(o.maze.goal,'G')):ax.text(p%n,p//n,l,ha='center',va='center',fontweight='bold',color='#253a60',fontsize=8)
  ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f'{title} · goal {side+1}\n'+('Shortest path' if r['optimal'] else r['failure'].replace('_',' '))+f' · {len(o.path)-1} edges',fontsize=10)
  cert.append(dict(model=name,row=r,metadata=meta[cid]))
fig.suptitle('Off-centre junction with asymmetric goal bends',fontsize=14)
fig.legend(handles=[Patch(color=colors[i],label=l) for i,l in [(2,'Correct output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.03))
fig.text(.5,.015,'Saved normal outputs; example selected after evaluation. No extra candidate calls or model selection.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.08,1,.94))
for ext in ('png','svg','pdf'):fig.savefig(out/f'new_lineage_rasters.{ext}',dpi=180,bbox_inches='tight')
(out/'raster_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')
