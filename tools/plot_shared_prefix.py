"""Saved normal Q rasters only; no new inference or winner selection."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from maze_evolution.shared_prefix_study import *

def main():
    cases,contexts,meta=load(OUT/'confirmation');choices=read_compressed(OUT/'choices.json.gz')
    labels=['Oracle shortest raster','Preserved depth9','Carried mixed, replicate0','Fresh mixed, replicate0']
    aliases=['anchor/route/d9','carry/0/mixed/primary','fresh/0/mixed/primary'];pids=[choices['aliases'][a] for a in aliases]
    target={p:next(c for c,m in meta.items() if m['index']==0 and m['pose']==0 and m['prefix']==p and m['side']==0 and m['family']=='paired') for p in (0,1,2)}
    saved={}
    for e in lines(OUT/'confirmation/responses.jsonl.gz'):
        if e['key'] in pids:
            for r in e['rows']:
                if r['case'] in target.values():saved[e['key'],r['case']]=r
    fig,axes=plt.subplots(3,4,figsize=(12,9));colors=ListedColormap(['#142333','#f0f3f4','#f4a340','#3ca878'])
    for p,cid in target.items():
        o=cases[cid];m=o.maze
        for col in range(4):
            ax=axes[p,col];data=np.frombuffer(m.cells,np.uint8).copy()
            if col==0:
                mask=np.zeros(len(data),bool);mask[o.path]=True;label='shortest path'
            else:
                r=saved[pids[col-1],cid];mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(data)].astype(bool)
                label='shortest' if r['optimal'] else r['failure'].replace('_',' ')
            data[mask]=3 if col==0 or saved[pids[col-1],cid]['optimal'] else 2
            ax.imshow(data.reshape(m.h,m.w),cmap=colors,vmin=0,vmax=3,interpolation='nearest')
            for pos,symbol,color in ((m.start,'S','#c93664'),(m.goal,'G','#3479d3')):
                y,x=divmod(pos,m.w);ax.scatter(x,y,s=65,c=color,edgecolors='white',linewidths=.6);ax.text(x+.6,y,symbol,color=color,fontsize=9,fontweight='bold')
            ax.set_xlim(3,15);ax.set_ylim(14,2);ax.set_xticks([]);ax.set_yticks([])
            if p==0:ax.set_title(labels[col],fontsize=11,pad=12)
            ax.set_xlabel(label,fontsize=10)
            if col==0:ax.set_ylabel(f'Shared prefix: {p} edge'+('' if p==1 else 's'),fontsize=11)
    fig.suptitle('Moving the source behind the junction\nNormal emitted outputs on the same unseen fork',fontsize=17,y=.98)
    fig.text(.5,.025,'Green = complete shortest raster · Orange = incorrect emitted raster · S = source · G = goal\nFixed illustration: first final context, pose0, goal0; mixed replicate0 chosen before final. View cropped to connected geometry.',ha='center',fontsize=9)
    fig.tight_layout(rect=(.02,.065,1,.93))
    for ext in ('png','svg','pdf'):fig.savefig(OUT/f'normal_outputs.{ext}',dpi=170)
    p=OUT/'normal_outputs.svg';p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
if __name__=='__main__':main()
