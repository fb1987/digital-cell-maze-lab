"""Plot saved V12R summaries only. No inference, selection, or new mazes."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from maze_evolution.mutation_accessibility_study import OUT

def main():
    d=json.loads((OUT/'saved_data_summary.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(12,5.3))
    arms=['depth1','depth4','depth16','resample'];x=np.arange(4);width=.24
    for offset,key,label,color in [(-1,'counters_changed','Internal counters changed','#6c90aa'),
            (0,'changed','Output raster/status changed','#d99a4b'),
            (1,'retained','At least 95% of root skills retained','#4c9d84')]:
        vals=[d['supply'][a][key] for a in arms]
        bars=axes[0].bar(x+offset*width,vals,width,label=label,color=color)
        axes[0].bar_label(bars,padding=3,fontsize=9)
    axes[0].set_xticks(x,['1 edit','4 edits','16 edits','Fresh random'])
    axes[0].set_ylabel('Candidate memberships out of 120 per arm')
    axes[0].set_ylim(0,175);axes[0].set_title('More edits change behavior more often')
    axes[0].legend(loc='upper left',fontsize=8,frameon=False)
    labels=list(d['roots']);x=np.arange(len(labels))
    root=[d['roots'][s]['final']['mean_score'] for s in labels]
    axes[1].scatter(x-.3,root,color='#243b53',marker='D',s=70,label='Unmutated root',zorder=5)
    for arm,off,color,label in [('depth1',-.1,'#6c90aa','1 edit'),('depth4',.1,'#d99a4b','4 edits'),('depth16',.3,'#4c9d84','16 edits')]:
        for rep in range(3):
            vals=[d['selections'][f'{s}/{rep}'][arm]['final']['mean_score'] for s in labels]
            axes[1].scatter(x+off+(rep-1)*.035,vals,color=color,s=35,label=label if rep==0 else None)
    axes[1].set_xticks(x,['P depth 9','Q fresh 0','Q current 1','Q fresh 2','Q random 95'],rotation=18,ha='right')
    axes[1].set_ylabel('Final one-edge-prefix partial score (not success)')
    axes[1].set_ylim(-.02,.54);axes[1].set_title('Selected mutants versus preserved roots')
    axes[1].legend(loc='upper left',fontsize=8,ncol=2,frameon=False)
    for ax in axes:
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',alpha=.14);ax.set_axisbelow(True)
    fig.suptitle('V12R: mutation supply around five random-origin lineages',fontsize=16)
    fig.text(.5,.035,'Discovery: 8 walks × 3 RNG blocks × 5 roots; depths are nested and correlated.\nFinal: fixed validation-selected models on new layouts. Partial scores are not legal paths.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.11,1,.93))
    for ext in ('png','svg','pdf'):fig.savefig(OUT/f'mutation_supply.{ext}',dpi=170)
    f=OUT/'mutation_supply.svg';f.write_text('\n'.join(s.rstrip() for s in f.read_text().splitlines())+'\n')
if __name__=='__main__':main()
