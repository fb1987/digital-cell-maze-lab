"""Post-registration figures from saved V12N metrics; no inference or selection."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/branch_pressure_calibration';V=OUT/'visuals';V.mkdir(exist_ok=True)
a=json.loads((OUT/'analysis.json').read_text());g=json.loads((OUT/'calibration_gates.json').read_text());keys=list(a['results'])
labels=[f"Group {k[0]} · {k.split('/')[1]}" for k in keys];y=np.arange(len(keys));colors=('#9aa6ac','#218b73')
fig,axes=plt.subplots(1,3,figsize=(15,6),gridspec_kw={'width_ratios':[1.2,1.2,1.]})
for index,(pressure,color) in enumerate(zip(('current','choice'),colors)):
    scores=[a['results'][k]['metrics']['selected_'+pressure]['mean_score'] for k in keys]
    pairs=[a['results'][k]['metrics']['selected_'+pressure]['nonadj_pairs'] for k in keys]
    for ax,values in zip(axes[:2],(scores,pairs)):
        ax.barh(y+(index-.5)*.32,values,height=.3,color=color,label=pressure.title()+' pressure')
        for yi,v in zip(y+(index-.5)*.32,values):ax.text(v+.005 if ax is axes[0] else v+.1,yi,f'{v:.3f}' if ax is axes[0] else str(v),va='center',fontsize=9)
axes[0].set_xlim(0,max(.08,max(a['results'][k]['metrics']['selected_choice']['mean_score'] for k in keys)*1.3));axes[1].set_xlim(0,max(4,max(a['results'][k]['metrics']['selected_choice']['nonadj_pairs'] for k in keys)*1.3))
axes[2].barh(y,[g[k]['parent_changes'] for k in keys],color='#487fa5');axes[2].axvline(16,color='#b65d36',ls='--',label='16-draw threshold');axes[2].set_xlim(0,66)
axes[0].set_title('Independent final\nMean interior branch-choice score');axes[1].set_title('Independent final\nComplete non-adjacent pairs / 192');axes[2].set_title('Calibration\nChanged parent draws / 64')
for ax in axes:
    ax.invert_yaxis();ax.set_yticks(y);ax.set_yticklabels(labels if ax is axes[0] else []);ax.spines[['top','right']].set_visible(False)
axes[0].legend(loc='lower right',fontsize=9);axes[2].legend(loc='lower right',fontsize=9)
fig.suptitle('Branch-pressure calibration: selection changes must accompany normal route-choice progress',fontsize=15)
fig.text(.5,.025,'Fixed random-founder neighborhoods; no evolution. Groups share the case corpus; poses and graph controls are correlated.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.07,1,.91))
for ext in ('png','svg','pdf'):
    path=V/f'pressure_and_transfer.{ext}';fig.savefig(path,dpi=150,bbox_inches='tight')
    if ext=='svg':path.write_text('\n'.join(x.rstrip() for x in path.read_text().splitlines())+'\n')
print(V)
# A retrospective same-layout rotation exposes the calibration coverage limitation.
import sys
sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_study import read_compressed
from maze_evolution.branch_pressure_data import load
from maze_evolution.branch_pressure_fitness import pair_score
from maze_evolution.routing_transfer import lines
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
aliases=read_compressed(OUT/'confirmation/aliases.json.gz');entry=aliases['0/local']['selected_choice'];cases,contexts,meta=load(OUT/'confirmation')
ctx=next(c for c in contexts if c['kind']=='two_edge' and c['goal_shape']=='turning');wanted={cid for pose in (0,1) for cid in ctx['poses'][pose]['cases']['paired']};rows={}
for rec in lines(OUT/'confirmation/responses.jsonl.gz'):
    if rec['model']==entry['model'] and rec['row']['case'] in wanted:rows[rec['row']['case']]=rec['row']
fig,axes=plt.subplots(2,2,figsize=(8,8));palette=['#e3e6e4','#ffffff','#3a9e80','#d76c50','#e5b44d'];cert=[]
for col,pose in enumerate((0,1)):
    ids=ctx['poses'][pose]['cases']['paired'];score=pair_score([rows[cid] for cid in ids],meta)['score']
    for side,cid in enumerate(ids):
        r=rows[cid];o=cases[cid];m=o.maze;ax=axes[side,col];mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:81].astype(bool)
        truth=np.zeros(81,bool);truth[o.path]=True;grid=np.frombuffer(m.cells,np.uint8).copy();grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
        ax.imshow(grid.reshape(9,9),cmap=ListedColormap(palette),vmin=0,vmax=4,interpolation='nearest')
        for q,label in ((m.start,'S'),(m.goal,'G')):ax.text(q%9,q//9,label,ha='center',va='center',fontweight='bold',color='#253a60')
        ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f"Pose {pose} · goal {side+1} · {'shortest' if r['optimal'] else 'incorrect'}\nPaired branch score {score:.3f}",fontsize=11)
        cert.append(dict(model=entry['model'],item_id=entry['item']['id'],row=r,metadata=meta[cid],pair_score=score))
fig.suptitle('Preserved founder 81: rotation exposes partial response, not a complete pair',fontsize=13)
fig.legend(handles=[Patch(color=palette[i],label=l) for i,l in [(2,'Correct output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.04))
fig.text(.5,.016,'Both examples are final data. Selected mutation is genotype-identical to the founder. No extra inference.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.10,1,.94))
for ext in ('png','svg','pdf'):
    path=V/f'orientation_and_partial_choice.{ext}';fig.savefig(path,dpi=150,bbox_inches='tight')
    if ext=='svg':path.write_text('\n'.join(x.rstrip() for x in path.read_text().splitlines())+'\n')
(V/'raster_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')
