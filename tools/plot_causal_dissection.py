"""V12V saved-data plots only; no inference or model selection."""
from pathlib import Path
import json,gzip
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/causal_dissection'
def read(path):
    with gzip.open(path,'rt') as f:return json.load(f)
def lines(path):
    with gzip.open(path,'rt') as f:
        for line in f:yield json.loads(line)

def main():
    p=read(OUT/'panel.json.gz');m=read(OUT/'metrics.json.gz');a=read(OUT/'analysis.json.gz');aliases=p['aliases']
    score=lambda n,mode='normal':m[aliases[n]+'|'+mode]['positive']
    denominator=sum(d['prefix']>0 for d in m[aliases['d00']+'|normal']['details'].values())
    fig,axes=plt.subplots(1,3,figsize=(15,5));x=np.arange(2);w=.34
    axes[0].bar(x-w/2,[score('d00'),score('dest_only')],w,label='Deletion absent',color='#91a5b7');axes[0].bar(x+w/2,[score('d01'),score('d02')],w,label='Deletion present',color='#208f7e');axes[0].set_xticks(x,['Original destination','Changed destination']);axes[0].set_title('Does the first deletion matter?');axes[0].legend(fontsize=8)
    early=['d07','d07_no_store','d08'];late=['d12_restore_store','d12_no_store','d12'];x=np.arange(3)
    axes[1].bar(x-w/2,[score(n) for n in early],w,label='Earlier background',color='#208f7e');axes[1].bar(x+w/2,[score(n) for n in late],w,label='Later background',color='#ab81b3');axes[1].set_xticks(x,['Gated store','Neither\n(self-copy)','Comparison only']);axes[1].set_title('Which part of mutation 8 causes the loss?');axes[1].legend(fontsize=8)
    names=['d01','d02'];x=np.arange(2);w=.24
    for delta,mode,label,color in [(-w,'normal','Native','#91a5b7'),(0,'channel4_zero','Signal suppressed','#208f7e'),(w,'channel4_restore','Signal restored','#db9269')]:
        vals=[]
        for n in names:
            if mode=='normal':vals.append(a['interventions'][n]['channel4_zero']['normal_success'])
            else:vals.append(m[aliases[n]+'|'+mode]['pairs'])
        axes[2].bar(x+delta,vals,w,label=label,color=color)
    axes[2].set_xticks(x,['Before mutation 2','After mutation 2']);axes[2].set_title('Channel 4 intervention on the fixed subset');axes[2].legend(fontsize=8)
    for ax in axes[:2]:ax.set_ylabel(f'Complete positive-prefix pairs / {denominator:,}')
    axes[2].set_ylabel('Complete pairs / 576 in diagnostic subset')
    for ax in axes:
        ax.grid(axis='y',alpha=.2)
        for bar in ax.patches:
            if bar.get_height():ax.annotate(str(int(bar.get_height())),(bar.get_x()+bar.get_width()/2,bar.get_height()),ha='center',va='bottom',fontsize=8,xytext=(0,3),textcoords='offset points')
        ax.margins(y=.17)
    fig.suptitle('V12V: controlled genetic and signal tests',fontsize=16)
    fig.text(.5,.015,'U-informed fixed panel; constructed variants are mechanistic probes, not new evolved discoveries.\nIndependent units are contexts; poses/goals/variants are correlated. Native stopping and work limits are unchanged.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.94));fig.savefig(OUT/'causal_tests.png',dpi=170);fig.savefig(OUT/'causal_tests.pdf');plt.close(fig)
    # Post-hoc illustration of a predicted native gain and restoration, selected
    # from cases already in the fixed intervention subset; no additional calls.
    md=read(OUT/'confirmation/metadata.json.gz');normal=m[aliases['d02']+'|normal']['details'];parent=m[aliases['d01']+'|normal']['details'];inter=m[aliases['d02']+'|channel4_restore']['details']
    good=[k for k in sorted(inter) if normal[k]['complete'] and not parent[k]['complete'] and normal[k]['prefix']>0]
    if not good:
        (OUT/'illustration_manifest.json').write_text(json.dumps(dict(candidate_calls=0,post_hoc=True,examples=[],reason='No qualifying gain in the fixed subset'),indent=2)+'\n');return
    pair=next((k for k in good if normal[k]['graph']=='cycle'),good[0]);ids=[cid for cid,v in md.items() if v['base']+'/pose'+str(v['pose'])==pair];assert len(ids)==2
    specs=[('d01','normal','Parent, native'),('d02','normal','Mutation 2, native'),('d02','channel4_restore','Mutation 2, signal restored')]
    wanted={(aliases[n],mode,cid) for n,mode,_ in specs for cid in ids};saved={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        key=e['model'],e['mode'],e['row']['case']
        if key in wanted:saved[key]=e['row']
    raw={r['case_id']:r for r in read(OUT/'confirmation/mazes.json.gz') if r['case_id'] in ids};fig,axes=plt.subplots(3,2,figsize=(9,11));colors=ListedColormap(['#172633','#f2f4f7','#29a178','#e89132','#dc7190']);examples=[]
    for i,(name,mode,label) in enumerate(specs):
        for j,cid in enumerate(ids):
            r=saved[aliases[name],mode,cid];o=raw[cid];cells=np.frombuffer(bytes.fromhex(o['cells_hex']),np.uint8).copy();n=len(cells)
            emitted=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:n].astype(bool);expected=np.zeros(n,bool);expected[md[cid]['path']]=True
            cells[emitted&expected]=2;cells[emitted&~expected]=3;cells[~emitted&expected]=4
            ax=axes[i,j];ax.imshow(cells.reshape(o['h'],o['w']),cmap=colors,vmin=0,vmax=4,interpolation='nearest')
            for pos,symbol,color in ((o['start'],'S','#40a9e8'),(o['goal'],'G','#b685ed')):
                y,xx=divmod(pos,o['w']);ax.scatter(xx,y,s=35,c=color,edgecolors='white',linewidths=.6);ax.text(xx+.7,y-.3,symbol,color=color,fontsize=9,fontweight='bold')
            ax.set_xticks([]);ax.set_yticks([])
            if j==0:ax.set_ylabel(label,fontsize=10)
            if i==0:ax.set_title('Goal A' if j==0 else 'Goal B')
            ax.set_xlabel(('Correct shortest' if r['optimal'] else r['failure'].replace('_',' '))+f" · tick {r['steps']}",fontsize=9)
            examples.append(dict(alias=name,mode=mode,case=cid,optimal=r['optimal'],steps=r['steps'],normal_stopping=True))
    fig.suptitle('Saved outputs: gaining and reversing the ability',fontsize=15)
    fig.text(.5,.015,'Green: correct path pixels · Orange: extra output · Pink: missing path\nPost-hoc illustration from the fixed diagnostic subset. Third row is an intervention, not native solving.\nNo forced continuation or new candidate call.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.08,1,.96));fig.savefig(OUT/'signal_outputs.png',dpi=170);fig.savefig(OUT/'signal_outputs.pdf');plt.close(fig)
    (OUT/'illustration_manifest.json').write_text(json.dumps(dict(candidate_calls=0,post_hoc=True,selection_rule='First gained positive cycle in fixed diagnostic subset, otherwise first gained positive pair',examples=examples,matplotlib=matplotlib.__version__),indent=2)+'\n')

if __name__=='__main__':main()
