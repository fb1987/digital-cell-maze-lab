"""Post-hoc saved-data visualization only; zero candidate inference."""
from pathlib import Path
import sys,json,gzip
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/lineage_mapping'
def read(path):
    with gzip.open(path,'rt') as f:return json.load(f)
def lines(path):
    with gzip.open(path,'rt') as f:
        for line in f:yield json.loads(line)

def main():
    p=read(OUT/'panel.json.gz');m=read(OUT/'metrics.json.gz');a=read(OUT/'analysis.json.gz');chain=p['chain'];x=np.arange(13)
    ss=[m[p['aliases'][name]+'|normal'] for name in chain]
    fig,axes=plt.subplots(2,2,figsize=(13,9));ax=axes[0,0]
    ax.plot(x,[s['positive'] for s in ss],'o-',color='#138779',label='Positive-prefix complete pairs / 960')
    ax.plot(x,[s['pairs'] for s in ss],'o--',color='#557eae',label='All complete pairs / 1,152')
    ax.set_title('Native paired solving along the exact lineage');ax.legend(fontsize=8);ax.set_ylabel('Complete shortest pairs')
    ax=axes[0,1]
    for family,label,color in [('ordinary_perfect','Ordinary trees / 192','#138779'),('ordinary_random','Ordinary cyclic / 192','#8b61a5')]:
        ax.plot(x,[s['families'][family]['optimal'] for s in ss],'o-',label=label,color=color)
    ax.set_title('Retention on ordinary mazes');ax.set_ylabel('Correct shortest outputs');ax.legend(fontsize=8)
    ax=axes[1,0];gains=[];losses=[]
    for before,after in zip(chain,chain[1:]):
        v=a['comparisons'][before+'->'+after]['positive_by_context'];gains.append(sum(s['gained'] for s in v.values()));losses.append(-sum(s['lost'] for s in v.values()))
    ax.bar(x[1:],gains,color='#138779',label='Gained positive-prefix pairs');ax.bar(x[1:],losses,color='#dc7b63',label='Lost positive-prefix pairs');ax.axhline(0,color='gray',linewidth=.6)
    ax.set_title('Each edit compared with its exact parent');ax.set_ylabel('Paired outcomes gained / lost');ax.legend(fontsize=8)
    for ax in (axes[0,0],axes[0,1],axes[1,0]):
        ax.set_xticks(x);ax.set_xlabel('Historical edit count (0 = root)');ax.grid(axis='y',alpha=.2)
    modes=['pulse_off','flag_off','output_feedback_off','halt_off'];values=np.full((4,13),np.nan)
    labels=[]
    for j,name in enumerate(chain):
        for i,mode in enumerate(modes):
            d=a['interventions'][name][mode]
            if d['normal_success']:values[i,j]=d['retained']/d['normal_success']
        labels.append(str(a['interventions'][name][modes[0]]['normal_success']))
    ax=axes[1,1];cmap=plt.get_cmap('YlGnBu').copy();cmap.set_bad('#dddddd');ax.imshow(values,vmin=0,vmax=1,cmap=cmap,aspect='auto')
    ax.set_xticks(x,[f'{i}\n({labels[i]})' for i in x],fontsize=8);ax.set_yticks(range(4),['Pulse off','Static flag off','Output reads off','Halt request off'])
    for i in range(4):
        for j in range(13):
            ax.text(j,i,'—' if np.isnan(values[i,j]) else f'{values[i,j]:.0%}',ha='center',va='center',fontsize=7,color='white' if values[i,j]>.65 else 'black')
    ax.set_title('Normal successful diagnostic pairs retained');ax.set_xlabel('Edit count (normal successes among 96 subset pairs)')
    fig.suptitle('V12U: where the 12 historical edits changed behavior',fontsize=16)
    fig.text(.5,.016,'Eight new sampled structural contexts; poses/variants correlated. Fixed, T-informed lineage.\nObserved edit effects depend on the preceding genotype. No new evolution or replacement selection.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.065,1,.96));fig.savefig(OUT/'lineage_map.png',dpi=170);fig.savefig(OUT/'lineage_map.pdf');plt.close(fig)
    # Explicitly post-hoc: strongest positive-pair-gain transition, first gained
    # positive-prefix cycle (else paired task), followed by same-case descendants.
    transitions=[a['comparisons'][b+'->'+c] for b,c in zip(chain,chain[1:])]
    top=max(transitions,key=lambda v:sum(d['gained'] for d in v['positive_by_context'].values()))
    detail=m[p['aliases'][top['after']]+'|normal']['details']
    gained=[k for k in top['gained'] if detail[k]['prefix']>0];assert gained
    pair=next((k for k in gained if detail[k]['graph']=='cycle'),gained[0]);md=read(OUT/'confirmation/metadata.json.gz')
    ids=[cid for cid,v in md.items() if v['base']+'/pose'+str(v['pose'])==pair]
    assert len(ids)==2
    models=[top['before'],top['after'],'d12'];wanted={(p['aliases'][n],cid) for n in models for cid in ids};saved={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        key=e['model'],e['row']['case']
        if e['scope']=='normal' and key in wanted:saved[key]=e['row']
    raw={r['case_id']:r for r in read(OUT/'confirmation/mazes.json.gz') if r['case_id'] in ids}
    fig,axes=plt.subplots(3,2,figsize=(9,11));colors=ListedColormap(['#172633','#f2f4f7','#29a178','#e89132','#dc7190']);examples=[]
    for i,name in enumerate(models):
        for j,cid in enumerate(ids):
            r=saved[p['aliases'][name],cid];o=raw[cid];cells=np.frombuffer(bytes.fromhex(o['cells_hex']),np.uint8).copy();n=len(cells)
            emitted=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:n].astype(bool);expected=np.zeros(n,bool);expected[md[cid]['path']]=True
            cells[emitted&expected]=2;cells[emitted&~expected]=3;cells[~emitted&expected]=4
            ax=axes[i,j];ax.imshow(cells.reshape(o['h'],o['w']),cmap=colors,vmin=0,vmax=4,interpolation='nearest')
            for pos,symbol,color in ((o['start'],'S','#40a9e8'),(o['goal'],'G','#b685ed')):
                y,xx=divmod(pos,o['w']);ax.scatter(xx,y,s=35,c=color,edgecolors='white',linewidths=.6);ax.text(xx+.7,y-.3,symbol,color=color,fontsize=9,fontweight='bold')
            ax.set_xticks([]);ax.set_yticks([])
            if j==0:ax.set_ylabel(f'{name}: edit {int(name[1:])}',fontsize=11)
            if i==0:ax.set_title('Goal A' if j==0 else 'Goal B')
            ax.set_xlabel(('Correct shortest' if r['optimal'] else r['failure'].replace('_',' '))+f" · tick {r['steps']}",fontsize=10)
            examples.append(dict(alias=name,case=cid,optimal=r['optimal'],steps=r['steps'],normal_emission=True))
    fig.suptitle('One newly acquired cycle pair: saved native outputs',fontsize=15)
    fig.text(.5,.016,'Green: correct path pixels · Orange: extra output · Pink: missing path\nPost-hoc illustration of the largest gain transition; not an independent test.\nBoth goals use the same maze and source. Zero new candidate calls.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.075,1,.96));fig.savefig(OUT/'normal_outputs.png',dpi=170);fig.savefig(OUT/'normal_outputs.pdf');plt.close(fig)
    (OUT/'illustration_manifest.json').write_text(json.dumps(dict(candidate_calls=0,post_hoc=True,selection_rule='Largest positive-pair gain adjacent transition; first gained positive cycle else first positive pair',examples=examples,matplotlib=matplotlib.__version__),indent=2)+'\n')

if __name__=='__main__':main()
