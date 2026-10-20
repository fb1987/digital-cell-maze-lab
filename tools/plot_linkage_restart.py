"""Plot the registered activation outcomes, no inference or selection."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/linkage_restart'
def main():
    a=json.loads((OUT/'analysis.json').read_text());fig,axes=plt.subplots(1,2,figsize=(11,5))
    arms=('linked','unlinked','sham');colors=('#268c7f','#6e89b1','#be9258');xs=np.arange(3);width=.33
    for ax,origin in zip(axes,('carry','fresh')):
        for j,arm in enumerate(arms):
            records=[a['by_condition'][f'{origin}/{r}/{arm}'] for r in range(3)]
            accepted=[100*s['accepted']/s['scheduled'] for s in records];multi=[100*s['multi_retained']/s['scheduled'] for s in records]
            ax.bar(j-width/2,np.mean(accepted),width,color=colors[j],alpha=.3)
            ax.bar(j+width/2,np.mean(multi),width,color=colors[j])
            for r in range(3):
                offset=(r-1)*.065;ax.plot(j-width/2+offset,accepted[r],'o',color='#30434b',markersize=4)
                ax.plot(j+width/2+offset,multi[r],'o',color='#30434b',markersize=4)
            ax.annotate(f'{np.mean(multi):.2f}%',(j+width/2,np.mean(multi)),xytext=(0,6),textcoords='offset points',ha='center',fontsize=9)
        ax.axhline(10,color='#b44545',linestyle='--',linewidth=1,label='10% activation threshold')
        ax.set_xticks(xs,['Dependency\npreserved','Unlinked','Matched random\nboundary'])
        ax.set_title('Carried random-origin lineages' if origin=='carry' else 'Fresh random populations')
        ax.set_ylabel('% of all scheduled mating births');ax.grid(axis='y',alpha=.15)
        ax.set_ylim(0,max(16,ax.get_ylim()[1]*1.13));ax.legend(fontsize=8,loc='upper right')
    fig.suptitle('V12X-R1: does crossover actually transfer multiple instructions?',fontsize=14)
    fig.text(.5,.015,'Pale bars: any accepted crossover · Solid bars: ≥2 donor instruction changes retained after mutation\nDots: three search replicates; bars: their mean. Activation also requires transfer in ≥8 generations.\nFeasibility pilot only. Genetic transfer is not evidence of combining solving abilities.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.14,1,.94));fig.savefig(OUT/'activation.png',dpi=180);fig.savefig(OUT/'activation.pdf');plt.close(fig)
    (OUT/'plot_manifest.json').write_text(json.dumps(dict(candidate_calls=0,matplotlib=matplotlib.__version__,source='All preregistered sexual conditions; no selection'),indent=2)+'\n')
if __name__=='__main__':main()
