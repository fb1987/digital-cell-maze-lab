"""Saved-data factorial plots; no new inference or model selection."""
from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/compatibility_map'
def read(path):
    with gzip.open(path,'rt') as f:return json.load(f)
def name(mask,store):return ('store/' if store else 'no_store/')+''.join(str(int(bool(mask&(1<<i)))) for i in range(4))
def main():
    a=read(OUT/'analysis.json.gz');panel=read(OUT/'panel.json.gz');metrics=read(OUT/'metrics.json.gz')
    order=list(range(8))+list(range(8,16));labels=[', '.join(str(i+9) for i in range(4) if m&(1<<i)) or 'None' for m in order]
    first=metrics[panel['aliases']['d07']+'|normal'];denoms=[sum(v['prefix']>0 for v in first['details'].values()),first['families']['corridor']['inputs'],sum(first['families'][f]['inputs'] for f in ('ordinary_perfect','ordinary_random'))]
    fig,axes=plt.subplots(1,3,figsize=(12,8))
    for ax,key,title,denom in zip(axes,('positive','corridors','ordinary'),('Positive-prefix pairs','Corridor outputs','Ordinary reachable outputs'),denoms):
        values=np.array([[a['totals'][name(mask,store)][key] for store in (False,True)] for mask in order]);ax.imshow(values,cmap='YlGnBu',vmin=0,vmax=max(1,values.max()),aspect='auto')
        for i,row in enumerate(values):
            for j,v in enumerate(row):ax.text(j,i,str(v),ha='center',va='center',color='white' if v>values.max()*.6 else '#18303c',fontsize=10)
        ax.set_xticks([0,1],['Self-COPY','Output STORE']);ax.set_yticks(range(16),labels if ax==axes[0] else [])
        ax.set_title(f'{title}\ncorrect / {denom:,}',fontsize=12);ax.axhline(7.5,color='#dc6f42',linewidth=2)
    axes[0].set_ylabel('Later edits present (9–12)')
    fig.suptitle('V12W: the same instruction in all 16 genetic backgrounds',fontsize=15)
    fig.text(.5,.015,'Constructed mechanistic probes, not new evolved discoveries. Orange line separates edit 12 absent/present.\nEight independent structured contexts; four fixed poses each. Ordinary controls use all eight poses.\nAll masks are native outputs under unchanged stopping and work limits.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.95));fig.savefig(OUT/'compatibility.png',dpi=180);fig.savefig(OUT/'compatibility.pdf');plt.close(fig)
    (OUT/'plot_manifest.json').write_text(json.dumps(dict(candidate_calls=0,source='Frozen complete factorial analysis; all32conditions',matplotlib=matplotlib.__version__),indent=2)+'\n')
if __name__=='__main__':main()
