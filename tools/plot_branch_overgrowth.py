"""Descriptive figures from saved V13A rasters/states; zero candidate calls."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import gzip,base64,zlib
from types import SimpleNamespace
OUT=Path(__file__).resolve().parents[1]/'results/branch_overgrowth'
def read_compressed(path):
    with gzip.open(path,'rt') as f:return json.load(f)
def lines(path):
    with gzip.open(path,'rt') as f:
        for line in f:yield json.loads(line)
def unpack_history(v):return np.frombuffer(zlib.decompress(base64.b64decode(v['data'])),dtype='<u2').reshape(v['shape'])

def main():
    p=read_compressed(OUT/'panel.json.gz');a=read_compressed(OUT/'analysis.json.gz')
    names=['mutation0','mutation1','mutation2','family0','family1','family2','resample0','resample1','resample2','historical_short','historical_long','random68','intact']
    fig,axes=plt.subplots(2,1,figsize=(13,8),layout='constrained')
    x=np.arange(len(names));zero=[];positive=[]
    for name in names:
        m=a['metrics'][p['aliases'][name]+'|normal'];zero.append(m['pairs']-m['positive']);positive.append(m['positive'])
    axes[0].bar(x-.18,zero,.36,label='Source at junction (160 pairs)',color='#238b8d');axes[0].bar(x+.18,positive,.36,label='Source upstream (640 pairs)',color='#c75d48')
    axes[0].set_ylabel('Complete shortest-path pairs');axes[0].set_xticks(x,names,rotation=25,ha='right');axes[0].legend();axes[0].set_title('Normal outputs on new layouts; source-distance opportunity counts differ')
    modes=['pulse_off','flag_off','both_off','endpoint_off','halt_off'];colors=['#3279ad','#cf8249','#803e8f','#479067','#b7354a']
    for j,(mode,color) in enumerate(zip(modes,colors)):
        v=[a['interventions'][n][mode]['complete'] for n in names]
        axes[1].bar(x+(j-2)*.15,v,.15,color=color,label=mode)
    axes[1].set_xticks(x,names,rotation=25,ha='right');axes[1].set_ylabel('Complete pairs /480 intervention opportunities');axes[1].legend(ncol=3);axes[1].set_title('Unforced interventions; gains and losses are separately tabulated in report')
    for ax in axes:ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.savefig(OUT/'comparison.png',dpi=160);fig.savefig(OUT/'comparison.pdf');plt.close(fig)
    meta=read_compressed(OUT/'confirmation/metadata.json.gz');cases={r['case_id']:SimpleNamespace(**r,cells=bytes.fromhex(r['cells_hex'])) for r in read_compressed(OUT/'confirmation/mazes.json.gz')};cid=next(c for c,m in meta.items() if m['family']=='paired' and m['index']==0 and m['prefix']==1 and m['pose']==0 and m['side']==0)
    chosen=['mutation0','resample0'];wanted={p['aliases'][n]:n for n in chosen};saved={};normal={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        if e['model'] not in wanted or e['row']['case']!=cid or e['mode']!='normal':continue
        name=wanted[e['model']]
        if e['scope']=='normal':normal[name]=e['row']
        if e['scope']=='trace':saved[name]=unpack_history(e['history'])
    fig,axes=plt.subplots(2,6,figsize=(15,5),layout='constrained');m=cases[cid]
    for row,name in enumerate(chosen):
        h=saved[name];ticks=[1,normal[name]['steps'],normal[name]['steps']+2,16,32,len(h)]
        for col,tick in enumerate(ticks):
            ax=axes[row,col];mask=h[tick-1,2]>0;im=np.full((len(m.cells),3),[.13,.18,.22]);im[np.frombuffer(m.cells,np.uint8)>0]=[.9,.93,.94];im[mask]=[.83,.38,.28]
            ax.imshow(im.reshape(m.h,m.w,3),interpolation='nearest');ax.set_xticks([]);ax.set_yticks([])
            for point,text in [(m.start,'S'),(m.goal,'G')]:ax.text(point%m.w,point//m.w,text,color='white',ha='center',va='center',fontsize=8,bbox=dict(boxstyle='circle,pad=.1',fc='#265c51' if text=='S' else '#6f3d78',ec='none'))
            ax.set_title(f'{"Native stop" if col==1 else "Forced"} · tick {tick}',fontsize=10)
            if col==0:ax.set_ylabel(name)
    fig.suptitle('Saved one-cell-prefix trajectories — illuminated cells in coral\nForced frames are diagnostic, not solver outputs',fontsize=13)
    fig.savefig(OUT/'trajectories.png',dpi=160);fig.savefig(OUT/'trajectories.pdf');plt.close(fig)
    (OUT/'illustration.json').write_text(json.dumps(dict(case=cid,models=chosen,selection='First context, prefix1, pose0, side0; fixed metadata illustration; no new inference'),indent=2)+'\n')

if __name__=='__main__':main()
