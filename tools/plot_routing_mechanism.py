"""Post-hoc presentation of saved V12T outputs; zero candidate calls."""
from pathlib import Path
import sys,json,gzip
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/routing_mechanism'
def read_compressed(path):
    with gzip.open(path,'rt') as f:return json.load(f)
def lines(path):
    with gzip.open(path,'rt') as f:
        for line in f:yield json.loads(line)
def load(path):
    meta=read_compressed(path/'metadata.json.gz');cases={}
    for r in read_compressed(path/'mazes.json.gz'):
        m=SimpleNamespace(cells=bytes.fromhex(r['cells_hex']),w=r['w'],h=r['h'],start=r['start'],goal=r['goal'])
        cases[r['case_id']]=SimpleNamespace(maze=m,path=meta[r['case_id']]['path'])
    return cases,None,meta

def main():
    panel=read_compressed(OUT/'panel.json.gz');metrics=read_compressed(OUT/'metrics.json.gz');a=read_compressed(OUT/'analysis.json.gz')
    fit=json.loads((OUT/'predictor_fit.json').read_text());aliases=panel['aliases'];names=['fresh0','fresh2','carry0','carry1','spliced']
    fig,axes=plt.subplots(1,2,figsize=(12,4.8));x=np.arange(5);width=.36
    roots=[];desc=[]
    for name in names:
        m=metrics[aliases[name]+'|normal'];cmp=a['comparisons'][name];rootset=set()
        for r in cmp['roots']:rootset.update(k for k,d in metrics[aliases[r]+'|normal']['details'].items() if d['complete'] and d['prefix']>0)
        roots.append(len(rootset));desc.append(m['positive'])
    axes[0].bar(x-width/2,roots,width,color='#9ca8b5',label='Exact root(s), success union')
    axes[0].bar(x+width/2,desc,width,color='#268979',label='Preserved S descendant')
    axes[0].set_xticks(x,['Fresh 0','Fresh 2','Carried 0','Carried 1','Spliced 0']);axes[0].set_ylabel('Complete positive-prefix pairs / 1,280')
    axes[0].set_title('Root and descendant on identical new inputs');axes[0].legend(fontsize=8)
    for i,v in enumerate(desc):axes[0].text(i+width/2,v+7,str(v),ha='center',fontsize=9)
    for name,k in [('fresh2',1),('spliced',2),('carry0',3)]:
        pid=aliases[name];v=fit['models'][pid]['paired'];axes[1].bar(f'{name}\n{k} pruning round'+('s' if k!=1 else ''),100*v['matches'][k]/v['inputs'],color='#547eab')
    axes[1].set_ylim(0,105);axes[1].set_ylabel('Exact normal-raster matches (%)');axes[1].set_title('Prospective finite-pruning prediction\nIncludes incorrect outputs')
    fig.suptitle('V12T: acquired abilities and their limits',fontsize=15)
    fig.text(.5,.015,'Four sampled structural contexts; all eight poses and matched variants are correlated.\nAll genomes frozen before final generation. No new evolution or final-based selection.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.08,1,.95));fig.savefig(OUT/'comparison.png',dpi=170);fig.savefig(OUT/'comparison.pdf');plt.close(fig)
    cases,_,meta=load(OUT/'confirmation');specs=[('fresh2','fork',0,1,'Fresh descendant, prefix 1'),('fresh2','fork',0,2,'Same genome, prefix 2'),('carry0','cycle',2,1,'Carried descendant, cycle / prefix 1'),('carry0','cycle',2,4,'Same genome, cycle / prefix 4')]
    wanted={}
    for row,(name,graph,second,prefix,label) in enumerate(specs):
        for side in (0,1):
            cid=next(cid for cid,m in meta.items() if m['family']=='paired' and m['shape']=='straight' and m['pose']==0 and m['source_shape']=='straight' and (m['graph'],m['second'],m['prefix'],m['side'])==(graph,second,prefix,side))
            wanted[aliases[name],cid]=(row,side)
    saved={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        key=e['model'],e['row']['case']
        if e['scope']=='normal' and key in wanted:saved[key]=e['row']
    assert set(saved)==set(wanted)
    fig,axes=plt.subplots(4,2,figsize=(9,12));colors=ListedColormap(['#172633','#f2f4f7','#29a178','#e89132','#dc7190'])
    examples=[]
    for (pid,cid),(row,col) in wanted.items():
        r=saved[pid,cid];o=cases[cid];m=o.maze;ax=axes[row,col]
        cells=np.frombuffer(m.cells,np.uint8).copy();emitted=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(cells)].astype(bool)
        expected=np.zeros(len(cells),bool);expected[o.path]=True
        cells[emitted&expected]=2;cells[emitted&~expected]=3;cells[~emitted&expected]=4
        ax.imshow(cells.reshape(m.h,m.w),cmap=colors,vmin=0,vmax=4,interpolation='nearest')
        for pos,symbol,color in ((m.start,'S','#40a9e8'),(m.goal,'G','#b685ed')):
            y,x=divmod(pos,m.w);ax.scatter(x,y,s=45,c=color,edgecolors='white',linewidths=.6);ax.text(x+.7,y-.3,symbol,color=color,fontsize=9,fontweight='bold')
        ax.set_xticks([]);ax.set_yticks([])
        if col==0:ax.set_ylabel(specs[row][4],fontsize=10)
        if row==0:ax.set_title('Goal A' if col==0 else 'Goal B')
        ax.set_xlabel(('Correct shortest' if r['optimal'] else r['failure'].replace('_',' '))+f' · {len(o.path)-1} required edges',fontsize=9)
        examples.append(dict(alias=specs[row][0],case=cid,optimal=r['optimal'],normal_emission=True))
    fig.suptitle('Normal emissions on matched source-distance tests',fontsize=14)
    fig.text(.5,.018,'Green: correct path pixels · Orange: extra output · Pink: missing path · White: unlit open cell\nSaved normal outputs, first straight context / pose 0. Illustrative subset; no new inference.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.065,1,.965));fig.savefig(OUT/'normal_outputs.png',dpi=170);fig.savefig(OUT/'normal_outputs.pdf')
    (OUT/'illustration_manifest.json').write_text(json.dumps(dict(candidate_calls=0,post_hoc=True,examples=examples,matplotlib=matplotlib.__version__),indent=2)+'\n')

if __name__=='__main__':main()
