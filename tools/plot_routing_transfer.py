"""V12H standalone figures from saved outputs only; no additional inference."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.routing_transfer_data import OUT,FAMILIES,load

VIS=OUT/'visuals'
LOCAL='local/ecb803bdd83a1f6717fe'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
    'axes.spines.right':False,'figure.facecolor':'#fafaf7','axes.facecolor':'#fafaf7','savefig.facecolor':'#fafaf7'})


def save(fig,name):
    fig.savefig(VIS/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(VIS/(name+'.svg'),bbox_inches='tight')
    p=VIS/(name+'.svg');p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n');plt.close(fig)


def run():
    VIS.mkdir(exist_ok=True)
    summary=json.loads((OUT/'confirmation/summary.json').read_text());packet=read_compressed(OUT/'models.json.gz')
    fixed=packet['mechanism']['carried'];resampled=packet['mechanism']['resampled']
    labels=['Matched\ncorridor','One\njunction','Two\njunctions','Competing\nroutes'];families=['corridor',*FAMILIES]
    fig,axes=plt.subplots(1,2,figsize=(12,5.2),gridspec_kw={'width_ratios':[1.8,1]})
    for i,(key,label,color) in enumerate([(fixed,'Previous G leader','#d47a35'),
        (LOCAL,'Preserved local ancestor','#3e83a2'),(resampled,'Random-resampling variant','#7c6a9e')]):
        counts=[sum(summary['models'][key]['strata'][f'{f}/band{b}']['optimal'] for b in range(2)) for f in families]
        x=np.arange(4)+(i-1)*.24;bars=axes[0].bar(x,np.array(counts)/768*100,width=.23,label=label,color=color)
        axes[0].bar_label(bars,labels=[str(n) for n in counts],padding=3,fontsize=8)
    axes[0].axhline(100,color='#758375',ls='--',lw=1,label='Intact VM and conventional solvers')
    axes[0].set_ylim(0,115);axes[0].set_ylabel('Shortest individual outputs (%)');axes[0].set_xticks(range(4),labels)
    axes[0].set_title('Same endpoints and shortest routes')
    handles,legend_labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,legend_labels,frameon=False,fontsize=8,ncol=2,loc='upper center',bbox_to_anchor=(.5,.95))
    counts=[sum(summary['models'][LOCAL]['strata'][f'{f}/band{b}']['complete_pairs'] for b in range(2)) for f in FAMILIES]
    bars=axes[1].bar(range(3),counts,color=['#3e83a2','#578eaa','#80a4b4'],width=.65)
    axes[1].bar_label(bars,labels=[f'{c}/384' for c in counts],padding=5)
    axes[1].set_xticks(range(3),['One\njunction','Two\njunctions','Competing\nroutes']);axes[1].set_ylim(0,24)
    axes[1].set_ylabel('Complete shortest pairs');axes[1].set_title('Random-origin pair success: one preserved ancestor',fontsize=10)
    for ax in axes:ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.suptitle('V12H · corridor performance does not imply reliable routing',fontsize=15,y=1.03)
    fig.text(.5,-.035,'48 independent contexts × 8 poses. Graph variants are matched, correlated controls.\nLeft labels are counts / 768; right successes are all short and none spans all eight poses of a context.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,0,1,.85]);save(fig,'transfer')
    cases,contexts,metadata=load(OUT/'confirmation')
    selected={r['model']:{row['case']:row for row in r['rows']} for r in lines(OUT/'confirmation/normal.jsonl.gz') if r['model'] in (fixed,LOCAL)}
    chosen=None
    for context in contexts:
        for pose in context['poses']:
            ids=pose['cases']['alternate_cycle']
            if all(selected[LOCAL][cid]['optimal'] for cid in ids):
                chosen=(context,pose);break
        if chosen:break
    if chosen is None:return
    context,pose=chosen
    fig,axes=plt.subplots(2,3,figsize=(11,7.6))
    titles=['Previous leader · pruned corridor','Previous leader · real cycle','Preserved ancestor · same cycle']
    entries=[]
    for side in range(2):
        ids=[pose['cases'][f'corridor_{side}'][0],pose['cases']['alternate_cycle'][side],pose['cases']['alternate_cycle'][side]]
        keys=[fixed,fixed,LOCAL]
        for col,(cid,key) in enumerate(zip(ids,keys)):
            row=selected[key][cid];m=cases[cid].maze
            mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:len(m.cells)]
            grid=np.array(list(m.cells),int);grid[mask>0]=2
            ax=axes[side,col];ax.imshow(grid.reshape(m.h,m.w),cmap=ListedColormap(['#283747','#edf0e8','#e6a052']),vmin=0,vmax=2,interpolation='none')
            ax.scatter([m.start%m.w],[m.start//m.w],s=40,c='#49a4d7',edgecolors='white',linewidths=.7)
            ax.scatter([m.goal%m.w],[m.goal//m.w],s=65,c='#eddd66',marker='*',edgecolors='#293646',linewidths=.5)
            ax.set_xticks([]);ax.set_yticks([])
            ax.set_title(titles[col]+f'\nGoal {side+1} · '+('shortest' if row['optimal'] else row['failure'].replace('_',' ')),fontsize=9)
            entries.append(dict(model=key,case=cid,optimal=row['optimal']))
    short=[len(x)-1 for x in pose['meta']['paths']];long=[len(x)-1 for x in pose['meta']['alternatives']]
    fig.suptitle('A preserved primitive chooses both shorter routes on this one layout',fontsize=14,y=1.01)
    fig.text(.5,.012,f'Blue: source · yellow star: current goal · orange: emitted output. Shortest routes {short}; alternatives {long} edges.\nPost-hoc illustration: first complete cycle pair of the preserved ancestor. One context, not broad generalization.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.98]);save(fig,'matched_cycle')
    (VIS/'example_selection.json').write_text(json.dumps(dict(base=context['id'],symmetry=pose['symmetry'],
        shortest_edges=short,alternative_edges=long,entries=entries,
        selection='First saved complete cycle pair of local/ecb803bdd83a1f6717fe in construction order; post-hoc illustration only; no new selection or inference'),indent=2)+'\n')


if __name__=='__main__':run()
