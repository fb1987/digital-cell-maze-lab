"""V12I publication-style figures from saved rasters; no additional inference."""
import json
from pathlib import Path
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.validation_breadth_data import OUT,FAMILIES,load

VIS=OUT/'visuals'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
    'axes.spines.top':False,'axes.spines.right':False,
    'figure.facecolor':'#fafaf7','axes.facecolor':'#fafaf7','savefig.facecolor':'#fafaf7'})


def save(fig,name):
    fig.savefig(VIS/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(VIS/(name+'.svg'),bbox_inches='tight')
    path=VIS/(name+'.svg'); path.write_text('\n'.join(s.rstrip() for s in path.read_text().splitlines())+'\n')
    plt.close(fig)


def run():
    VIS.mkdir(exist_ok=True)
    result=json.loads((OUT/'analysis.json').read_text()); cohorts=result['cohorts']
    keys=sorted(cohorts,key=lambda k:(k.split('/')[0]=='fresh',k.split('/')[1]=='evolved',k.split('/')[3]=='resample',k.split('/')[2]=='branch'))
    labels=[]
    for key in keys:
        origin,topology,policy,method=key.split('/')
        labels.append(f'{"Carried" if origin=="carry" else "Fresh"} · {"local" if topology=="local" else "multirange"} · {"resampling" if method=="resample" else policy.title()}')
    fig,axes=plt.subplots(1,2,figsize=(12,6.5),gridspec_kw={'width_ratios':[1.8,1]},sharey=True)
    y=np.arange(len(keys)); colors=dict(narrow='#cd8145',broad='#2d859d')
    max_value=max(cohorts[k]['totals'][arm]['pairs'] for k in keys for arm in colors)
    for i,(arm,color) in enumerate(colors.items()):
        values=[cohorts[k]['totals'][arm]['pairs'] for k in keys]
        bars=axes[0].barh(y+(i-.5)*.32,values,height=.29,color=color,label=arm.title())
        axes[0].bar_label(bars,labels=[str(v) for v in values],padding=3,fontsize=9)
    axes[0].set_xlim(0,max(10,max_value*1.18)); axes[0].set_yticks(y,labels)
    axes[0].invert_yaxis(); axes[0].set_xlabel('Complete shortest pairs / 4,608 across three selected replicates')
    axes[0].legend(frameon=False,ncol=2,loc='lower right'); axes[0].set_title('Frozen pool · equal 128-input validation allowance')
    axes[1].axvline(0,color='#84908f',lw=1)
    for r,(color,marker) in enumerate([('#315c78','o'),('#748c4b','s'),('#9a6c9d','^')]):
        delta=[cohorts[k]['pair_counts_by_replicate']['broad'][r]-cohorts[k]['pair_counts_by_replicate']['narrow'][r] for k in keys]
        axes[1].scatter(delta,y+(r-1)*.13,s=36,c=color,marker=marker,label=f'Replicate {r+1}',zorder=3)
    axes[1].set_xlabel('Broad − narrow complete pairs / 1,536'); axes[1].set_title('Replicate consistency')
    axes[1].legend(frameon=False,fontsize=8,loc='lower right')
    for ax in axes:
        ax.grid(axis='x',alpha=.18); ax.set_axisbelow(True)
    fig.suptitle('V12I · does broader validation select better existing genomes?',fontsize=15,y=1.02)
    fig.text(.5,-.035,'Untouched final: 64 independent contexts × 8 poses × 3 matched graph variants. Poses and variants are correlated.\nNarrow: 4 contexts × 4 poses. Broad: 16 contexts × 1 pose. No genomes evolved during this experiment.',ha='center',fontsize=9)
    fig.tight_layout(); save(fig,'comparison')

    chosen=read_compressed(OUT/'selections.json.gz')
    cases,contexts,metadata=load(OUT/'confirmation')
    # A descriptive illustration is chosen only AFTER fixed-model evaluation.
    # It must not be mistaken for a new model choice or another holdout result.
    order=sorted(result['comparisons'],key=lambda k:(-(result['comparisons'][k]['broad']['pairs']-result['comparisons'][k]['narrow']['pairs']),k))
    key=next((k for k in order if result['comparisons'][k]['broad']['pairs']>result['comparisons'][k]['narrow']['pairs']),None)
    if key is None:
        return
    models={arm:chosen[key][arm]['model'] for arm in colors}
    outputs={p['model']:{r['case']:r for r in p['rows']} for p in lines(OUT/'confirmation/outputs.jsonl.gz') if p['model'] in models.values()}
    options=[]
    for c in contexts:
        for pose in c['poses']:
            for family in FAMILIES:
                ids=pose['cases'][family]
                if all(outputs[models['broad']][cid]['optimal'] for cid in ids) and not all(outputs[models['narrow']][cid]['optimal'] for cid in ids):
                    options.append((family!='alternate_cycle',-sum(len(p) for p in pose['meta']['paths']),c['id'],pose['symmetry'],family,pose))
    if not options:
        return
    _,_,base,symmetry,family,pose=min(options,key=lambda x:x[:5])
    fig,axes=plt.subplots(2,3,figsize=(10.7,7.1)); entries=[]
    for side in range(2):
        cid=pose['cases'][family][side]; o=cases[cid]; m=o.maze
        for col,arm in enumerate(('oracle','narrow','broad')):
            row=None if arm=='oracle' else outputs[models[arm]][cid]
            mask=np.zeros(len(m.cells),np.uint8)
            if row is None: mask[o.path]=1
            else: mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:len(m.cells)]
            grid=np.array(list(m.cells),int); grid[mask>0]=2
            ax=axes[side,col]; ax.imshow(grid.reshape(m.h,m.w),cmap=ListedColormap(['#283747','#edf0e8','#e6a052']),vmin=0,vmax=2,interpolation='none')
            ax.scatter([m.start%m.w],[m.start//m.w],s=40,c='#49a4d7',edgecolors='white',linewidths=.7)
            ax.scatter([m.goal%m.w],[m.goal//m.w],s=65,c='#eddd66',marker='*',edgecolors='#293646',linewidths=.5)
            status='shortest reference' if row is None else ('shortest' if row['optimal'] else row['failure'].replace('_',' ') or 'non-shortest')
            ax.set_title(f'{"Reference" if arm=="oracle" else arm.title()+" selection"} · goal {side+1}\n{status}',fontsize=10)
            ax.set_xticks([]); ax.set_yticks([])
            if row is not None: entries.append(dict(arm=arm,model=models[arm],case=cid,optimal=row['optimal']))
    fig.suptitle('Saved emissions on one unseen two-goal context',fontsize=14,y=1.01)
    lengths=[len(p)-1 for p in pose['meta']['paths']]
    fig.text(.5,.012,f'{key.removeprefix("fork/")} · {family.replace("_"," ")} · shortest routes {lengths} edges\nBlue: source · star: current goal · orange: emitted raster. Post-hoc illustration; no new inference or model selection.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.98]); save(fig,'paired_example')
    (VIS/'example_selection.json').write_text(json.dumps(dict(condition=key,base=base,symmetry=symmetry,family=family,
        shortest_edges=lengths,alternative_edges=[len(p)-1 for p in pose['meta']['alternatives']],entries=entries,
        selection='Largest positive condition gain; prefer cycle, then longest total routes, then construction identity. Post-hoc saved-raster illustration only.'),indent=2)+'\n')


if __name__=='__main__': run()
