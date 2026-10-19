"""V12O post-registration plots and a saved-raster illustration; no inference."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.mutation_depth_data import OUT,TOPS,ARMS,load
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
V=OUT/'visuals';V.mkdir(exist_ok=True)
g=json.loads((OUT/'discovery_gates.json').read_text());a=read_compressed(OUT/'analysis.json.gz');diag=json.loads((OUT/'diagnosis.json').read_text())
colors=['#29866c','#4b7ca5','#bf8453'];labels=['Depth 1','Depth 4','Depth 16','One edit','Random draw'];y=np.arange(5)


def save(fig,name):
    for ext in ('png','pdf','svg'):
        path=V/f'{name}.{ext}';fig.savefig(path,dpi=150,bbox_inches='tight')
        if ext=='svg':path.write_text('\n'.join(l.rstrip() for l in path.read_text().splitlines())+'\n')
    plt.close(fig)

fig,axes=plt.subplots(2,2,figsize=(13,9))
for r,top in enumerate(TOPS):
    for rep,color in enumerate(colors):
        ss=g[f'{rep}/{top}']['supply']
        for c,field in enumerate(('changed_masks','useful_count')):
            values=[ss[arm][field] for arm in ARMS];ax=axes[r,c];offset=(rep-1)*.23
            ax.barh(y+offset,values,height=.22,color=color,label=f'Founder group {rep}')
            for yy,v in zip(y+offset,values):ax.text(v+.7,yy,str(v),va='center',fontsize=8)
    for c in range(2):
        ax=axes[r,c];ax.set_yticks(y,labels);ax.invert_yaxis();ax.spines[['top','right']].set_visible(False)
        ax.set_title(f"{('Local' if top=='local' else 'Nonlocal')} topology · "+('changed raster / 192' if c==0 else 'new useful branch response / 192'))
        maximum=max(g[f'{rep}/{top}']['supply'][arm][('changed_masks','useful_count')[c]] for rep in range(3) for arm in ARMS)
        ax.set_xlim(0,max(8,maximum*1.16+1))
axes[0,0].legend(loc='upper right',fontsize=9)
fig.suptitle('Cumulative mutation, output variation and new goal-dependent responses',fontsize=15)
fig.text(.5,.02,'Equal terminal pool sizes; two related walks per founder. “Useful” is a partial-response screen, not a completed maze pair.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.95));save(fig,'variation_and_supply')
fig,axes=plt.subplots(2,2,figsize=(13,9))
for r,top in enumerate(TOPS):
    for rep,color in enumerate(colors):
        aa=a['results'][f'{rep}/{top}']['arms']
        for c,field in enumerate(('nonadj_pairs','mean_score')):
            vals=[aa[arm]['metrics'][field] for arm in ARMS];ax=axes[r,c];offset=(rep-1)*.23;ax.barh(y+offset,vals,height=.22,color=color,label=f'Founder group {rep}')
            for yy,v in zip(y+offset,vals):ax.text(v+(.002 if c else .15),yy,f'{v:.3f}' if c else str(v),va='center',fontsize=8)
    for c in range(2):
        ax=axes[r,c];ax.set_yticks(y,labels);ax.invert_yaxis();ax.spines[['top','right']].set_visible(False)
        ax.set_title(f"{('Local' if top=='local' else 'Nonlocal')} topology · "+('non-adjacent complete pairs / 128' if c==0 else 'mean branch score'))
        mx=max(a['results'][f'{rep}/{top}']['arms'][arm]['metrics'][('nonadj_pairs','mean_score')[c]] for rep in range(3) for arm in ARMS)
        ax.set_xlim(0,max(.05 if c else 4,mx*1.2+(.01 if c else 1)))
axes[0,0].legend(loc='lower right',fontsize=9)
fig.suptitle('Independent final: frozen validation choices across equal-size sampling arms',fontsize=15)
fig.text(.5,.02,'All eight poses. Shared final contexts and related descendants are correlated; no fitness-guided evolution occurred.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.95));save(fig,'final_comparison')
# Pick a saved final example only for illustration, never for selection or a gate.
options=[]
for key,r in a['results'].items():
    for arm in ('depth4','depth16'):
        z=r['arms'][arm];parent={(d['base'],d['pose']):d for d in z['reference_metrics']['details']}
        for d in z['metrics']['details']:
            before=parent[d['base'],d['pose']];gain=d['score']-before['score']
            if gain>0:options.append((int(d['complete'] and not before['complete']),gain,int(d['kind']=='three_edge'),key,arm,d['base'],d['pose']))
if options:
    _,gain,_,key,arm,base,pose=max(options);z=a['results'][key]['arms'][arm];top=key.split('/')[1];aliases=read_compressed(OUT/'aliases.json.gz');ids=[z['reference'],z['selected']];models=[aliases[top][i] for i in ids];cases,contexts,meta=load(OUT/'confirmation')
    wanted=[cid for cid,m in meta.items() if m['base']==base and m['pose']==pose and m['family']=='paired'];wanted.sort(key=lambda cid:meta[cid]['side']);rows={}
    for rec in lines(OUT/'confirmation/responses.jsonl.gz'):
        if rec['model'] in models and rec['row']['case'] in wanted:rows[rec['model'],rec['row']['case']]=rec['row']
    fig,axes=plt.subplots(2,2,figsize=(8,8));palette=['#e3e6e4','#ffffff','#3a9e80','#d76c50','#e5b44d'];cert=[]
    for col,pid in enumerate(models):
        for side,cid in enumerate(wanted):
            row=rows[pid,cid];o=cases[cid];m=o.maze;ax=axes[side,col];mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:81].astype(bool);truth=np.zeros(81,bool);truth[o.path]=True
            grid=np.frombuffer(m.cells,np.uint8).copy();grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4;ax.imshow(grid.reshape(9,9),cmap=ListedColormap(palette),vmin=0,vmax=4,interpolation='nearest')
            for q,label in ((m.start,'S'),(m.goal,'G')):ax.text(q%9,q//9,label,ha='center',va='center',fontweight='bold',color='#253a60')
            ax.set_xticks([]);ax.set_yticks([]);ax.set_title(('Original founder' if col==0 else arm.replace('depth','Depth '))+f" · goal {side+1}\n"+('Shortest path' if row['optimal'] else 'Incorrect'),fontsize=11)
            cert.append(dict(item=ids[col],model=pid,row=row,metadata=meta[cid]))
    fig.suptitle(f'Saved final example · group {key} · same layout and goals',fontsize=13)
    fig.legend(handles=[Patch(color=palette[i],label=l) for i,l in [(2,'Correct output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.04))
    fig.text(.5,.016,'Retrospective illustration from the frozen panel; not an additional test or selection.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.1,1,.94));save(fig,'saved_mutation_example');(V/'raster_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')
print(V)
