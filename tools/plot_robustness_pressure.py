"""V12K publication files from saved results only; no candidate inference."""
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

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'#fafaf7','axes.facecolor':'#fafaf7','savefig.facecolor':'#fafaf7'})

def save(fig,name):
    out=OUT/'visuals';out.mkdir(exist_ok=True)
    fig.savefig(out/f'{name}.png',dpi=175,bbox_inches='tight');fig.savefig(out/f'{name}.svg',bbox_inches='tight');plt.close(fig)
    p=out/f'{name}.svg';p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')


def run():
    a=json.loads((OUT/'analysis.json').read_text());s=json.loads((OUT/'search_summary.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(12,8),sharey=True)
    for i,origin in enumerate(('carry','fresh')):
        for j,topology in enumerate(('local','evolved')):
            ax=axes[i,j];rs=a['gates'][f'{origin}/{topology}']['replicates'];x=np.arange(3)
            for off,key,label,color in [(-.24,'frozen','Frozen initial','#9ca5a8'),(0,'pair','Pair pressure','#4c79a8'),(.24,'context','Context pressure','#d28d42')]:
                y=[r[key]['pairs'] for r in rs];bars=ax.bar(x+off,y,width=.23,color=color,label=label)
                ax.bar_label(bars,fontsize=9,padding=3)
            ax.set_xticks(x,['Replicate 0','Replicate 1','Replicate 2']);ax.set_title(f'{origin.title()} · '+('local' if topology=='local' else 'evolvable ranges'))
            ax.spines[['right','top']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
            if j==0:ax.set_ylabel('Complete goal pairs / 576')
    fig.suptitle(f'V12K · {s["rounds"]} matched generations, one selection-pressure change',fontsize=16,y=.98)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.025))
    fig.text(.5,.005,'24 independently seeded final contexts per model; graph variants and poses are correlated. Common context-first finalist archive.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.08,1,.94));save(fig,'primary_comparison')

    names=['branch_narrow','branch_broad','long_prefix','local_long','resampled','shared_ancestor']
    labels=['Branch narrow','Branch broad','Long-prefix variant','Local exception','68-gene random draw','Shared ancestor']
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,metric,denom in zip(axes,('pairs','corridor'),(576,384)):
        x=np.arange(len(names));normal=[a['rescue'][n]['normal'][metric] for n in names];zero=[a['rescue'][n]['zero'][metric] for n in names]
        for off,y,label,col in [(-.18,normal,'Normal','#4c79a8'),(.18,zero,'Nonlocal values zeroed','#d28d42')]:
            bars=ax.bar(x+off,y,width=.35,label=label,color=col);ax.bar_label(bars,padding=3,fontsize=8)
        ax.set_xticks(x,labels,rotation=35,ha='right');ax.set_ylabel(f'Correct {"paired routes" if metric=="pairs" else "corridors"} / {denom}')
        ax.spines[['right','top']].set_visible(False);ax.set_ylim(0,max(max(normal),max(zero))*1.2)
    axes[0].legend(frameon=False,fontsize=9);fig.suptitle('Fresh fixed-panel diagnostic · nonlocal interference and retention',fontsize=15)
    fig.text(.5,.005,'Same 24 contexts, fixed genomes, all read charges retained. Zeroing is external, not an evolved gate.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.94));save(fig,'nonlocal_diagnostic')

    # Explicitly retrospective illustration: first sorted rescued broad-Branch pair.
    cases,_,meta=load(OUT/'diagnostic');rescued=a['rescue']['branch_broad']['gained_pairs']
    if rescued:
        base,family,pose=sorted(rescued)[0];ids=[cid for cid,m in meta.items() if (m['base'],m['family'],m['pose'])==(base,family,pose)]
        records={}
        for r in lines(OUT/'diagnostic/responses.jsonl.gz'):
            if r['model']=='branch_broad' and r['row']['case'] in ids:records[(r['mode'],r['row']['case'])]=r['row']
        fig,axes=plt.subplots(2,2,figsize=(8,8));cert=[];colors=['#e3e6e4','#ffffff','#3a9e80','#d76c50','#e5b44d']
        for col,mode in enumerate(('normal','nonlocal_off')):
            for cid in ids:
                md=meta[cid];o=cases[cid];row=records[(mode,cid)];ax=axes[md['side'],col];n=o.maze.w
                mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:n*n].astype(bool)
                truth=np.zeros(n*n,bool);truth[o.path]=True;grid=np.frombuffer(o.maze.cells,np.uint8).copy()
                grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
                ax.imshow(grid.reshape(n,n),cmap=ListedColormap(colors),vmin=0,vmax=4,interpolation='nearest')
                for p,l in ((o.maze.start,'S'),(o.maze.goal,'G')):ax.text(p%n,p//n,l,ha='center',va='center',fontweight='bold',fontsize=10,color='#253a60')
                ax.set_xticks([]);ax.set_yticks([]);ax.set_title(('Normal' if mode=='normal' else 'Nonlocal values zeroed')+f' · goal {md["side"]+1}\n'+('Shortest path' if row['optimal'] else row['failure'].replace('_',' ')),fontsize=10)
                cert.append(dict(model='branch_broad',mode=mode,row=row,metadata=md))
        fig.suptitle('Same frozen genome and maze: a rescued goal-switch pair',fontsize=14)
        fig.legend(handles=[Patch(color=colors[i],label=l) for i,l in [(2,'Correct output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False)
        fig.text(.5,.045,'Example chosen after evaluation; no additional candidate calls.',ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.08,1,.94));save(fig,'rescued_pair')
        (OUT/'visuals/raster_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')

if __name__=='__main__':run()
