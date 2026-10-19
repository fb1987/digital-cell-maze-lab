"""V12M saved-data figures; no candidate calls or selection changes."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from maze_evolution.exposure_data import OUT

p=json.loads((OUT/'analysis.json').read_text());out=OUT/'visuals';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
 for ext in ('png','svg','pdf'):
  path=out/f'{name}.{ext}';fig.savefig(path,dpi=170,bbox_inches='tight')
  if ext=='svg':path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
 plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(13,7),gridspec_kw={'width_ratios':[1.3,1]})
names=['branch_broad','branch_narrow','k2_target','k2_parent','local_long','resampled','long_prefix','long_replacement']
y=np.arange(len(names));arms=['active','neutral','zero','local'];colors=['#268b70','#9aa8ac','#497da5','#bd8758'];labels=['Inherited exposure','Neutral / all-on','Fixed zero','Local']
for i,arm in enumerate(arms):
 vals=[p['final']['carry/'+n]['selected_'+arm]['stats']['pairs'] for n in names]
 axes[0].barh(y+(i-1.5)*.19,vals,height=.19,color=colors[i],label=labels[i])
axes[0].set_yticks(y,['Old broad Branch','Old narrow Branch','K2 descendant','K2 parent','Local exception','68-gene draw','Long-prefix nominee','Its replacement']);axes[0].invert_yaxis()
axes[0].set_title('Validation-selected carried models\nFinal complete pairs / 144');axes[0].set_xlabel('Complete two-goal shortest-path pairs')
for i in range(3):
 r=p['fresh'][f'fresh/{i}']['neutral']
 axes[1].bar(i-.2,r['uniform_partial'],width=.19,color='#c6cccc')
 axes[1].bar(i,r['parent_partial'],width=.19,color='#268b70')
 axes[1].bar(i+.2,r['final_two_edge_partial'],width=.19,color='#497da5')
 axes[1].text(i,.355,f"{r['shaping_parent_changes']}/64 parent\ndraws change",ha='center',va='bottom',fontsize=8)
axes[1].set_ylim(0,.55);axes[1].set_xticks(range(3),['Replicate 0','Replicate 1','Replicate 2']);axes[1].set_ylabel('Mean two-edge paired-input partial score')
axes[1].set_title('Fresh random founders · neutral control\nSelection activation and independent final score')
from matplotlib.patches import Patch
axes[1].legend(handles=[Patch(color=c,label=l) for c,l in [('#c6cccc','Uniform founders · calibration'),('#268b70','Selected parent draws · calibration'),('#497da5','Selected founder · final')]],loc='upper right',bbox_to_anchor=(1,.99),fontsize=8,frameon=False)
fig.legend(handles=[Patch(color=c,label=l) for c,l in zip(colors,labels)],loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.5,.065))
fig.suptitle('Inherited exposure calibration: useful suppression is a separate claim from solving',fontsize=14)
fig.text(.5,.02,'Fixed neighborhoods and simulated reproduction only. Final inputs are independent; partial scores are not correct paths.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.13,1,.92));save(fig,'exposure_and_fresh_gradient')
# Matched-program comparison avoids attributing different selected programs only to a mask.
fig,ax=plt.subplots(figsize=(8,4.8));names2=['branch_broad','branch_narrow','k2_target','local_long','resampled'];y=np.arange(len(names2))
for i,label in enumerate(['selected_active','active_as_neutral','active_as_zero','active_as_local']):
 vals=[p['final']['carry/'+n][label]['stats']['pairs'] for n in names2]
 ax.barh(y+(i-1.5)*.19,vals,height=.19,color=colors[i],label=labels[i])
ax.set_yticks(y,['Old broad Branch','Old narrow Branch','K2 descendant','Local exception','68-gene draw']);ax.invert_yaxis();ax.set_xlabel('Complete pairs / 144');ax.set_title('The SAME selected program under four exposure conditions')
ax.legend(loc='lower center',bbox_to_anchor=(.5,-.27),ncol=2,frameon=False,fontsize=9)
fig.tight_layout();save(fig,'matched_program_exposure')
from maze_evolution.exposure_data import load
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
from matplotlib.colors import ListedColormap
aliases=read_compressed(OUT/'confirmation/aliases.json.gz');entry=aliases['fresh/0']['selected_neutral'];key=entry['model']
cases,contexts,meta=load(OUT/'confirmation/fresh');ctx=next(c for c in contexts if c['kind']=='two_edge' and c['goal_shape']=='turning')
ids=set(ctx['poses'][0]['cases']['paired']+ctx['poses'][0]['cases']['corridor_0']+ctx['poses'][0]['cases']['corridor_1']);rows={}
for r in lines(OUT/'confirmation/responses.jsonl.gz'):
 if r['origin']=='fresh' and r['model']==key and r['row']['case'] in ids:rows[r['row']['case']]=r['row']
fig,axes=plt.subplots(2,2,figsize=(7.2,7.2));colors=['#e3e6e4','#ffffff','#3a9e80','#d76c50','#e5b44d'];cert=[]
for side in (0,1):
 for col,family in enumerate(('paired','corridor_'+str(side))):
  cid=ctx['poses'][0]['cases'][family][side if family=='paired' else 0];r=rows[cid];o=cases[cid];m=o.maze;n=m.w;ax=axes[side,col]
  mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:n*n].astype(bool)
  truth=np.zeros(n*n,bool);truth[o.path]=True;grid=np.frombuffer(m.cells,np.uint8).copy()
  grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
  ax.imshow(grid.reshape(n,n),cmap=ListedColormap(colors),vmin=0,vmax=4,interpolation='nearest')
  for q,label in ((m.start,'S'),(m.goal,'G')):ax.text(q%n,q//n,label,ha='center',va='center',fontweight='bold',color='#253a60')
  ax.set_xticks([]);ax.set_yticks([]);ax.set_title(('Two-goal layout' if col==0 else 'Matched pruned corridor')+f' · goal {side+1}\n'+('Correct two-edge route' if r['optimal'] else f"Incorrect · partial score {r['partial']:.2f}"),fontsize=10)
  cert.append(dict(model=key,item_id=entry['item']['id'],row=r,metadata=meta[cid]))
fig.suptitle('Saved fresh founder: output fills the reachable component',fontsize=13)
fig.legend(handles=[Patch(color=colors[i],label=l) for i,l in [(2,'Correct output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.035))
fig.text(.5,.015,'Same genome; retrospective saved-raster illustration. No extra candidate calls.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.09,1,.94));save(fig,'fresh_component_output')
(out/'fresh_raster_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')
