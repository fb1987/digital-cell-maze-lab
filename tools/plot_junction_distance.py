"""V12J scientific figures, saved evidence only; no candidate inference."""
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.foundation_study import read_compressed
from maze_evolution.routing_transfer import lines
from maze_evolution.junction_distance_data import OUT,PREFIXES,load

LABELS={'branch_narrow':'Branch narrow · 254 genes','branch_broad':'Branch broad · 256',
 'branch_narrow_parent':'Narrow parent · 253','branch_broad_parent':'Broad parent · 256',
 'shared_ancestor':'Shared E ancestor','long_prefix':'Longer-prefix narrow','long_replacement':'Its broad replacement',
 'local_long':'Inherited local exception','local_cycle':'Local short-cycle model','fresh_evolved':'Fresh multirange',
 'fresh_local':'Fresh local broad','fresh_local_narrow':'Fresh local narrow','resampled':'Random draw · 68 genes','intact':'Known solver control'}
ORDER=['branch_narrow','branch_broad','branch_narrow_parent','branch_broad_parent','shared_ancestor','long_prefix',
 'long_replacement','local_long','local_cycle','fresh_evolved','fresh_local','fresh_local_narrow','resampled','intact']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'#fafaf7','axes.facecolor':'#fafaf7','savefig.facecolor':'#fafaf7'})

def save(fig,name):
 out=OUT/'visuals';out.mkdir(exist_ok=True)
 fig.savefig(out/f'{name}.png',dpi=175,bbox_inches='tight');fig.savefig(out/f'{name}.svg',bbox_inches='tight');plt.close(fig)
 p=out/f'{name}.svg';p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')

def run():
 a=json.loads((OUT/'analysis.json').read_text());models=read_compressed(OUT/'panel.json.gz')
 for name in ('branch_narrow_parent','branch_broad_parent'):LABELS[name]=('Narrow' if 'narrow' in name else 'Broad')+f" parent · {models[name]['genes']}"
 fig,axes=plt.subplots(2,3,figsize=(13,12),sharey=True)
 for i,shape in enumerate(('straight','bent')):
  for j,f in enumerate(('fork','two_2','cycle_2')):
   ax=axes[i,j];values=np.array([[a['models'][n]['table'][f'{shape}/{f}/{p}']['pairs']/96*100 for p in PREFIXES] for n in ORDER])
   im=ax.imshow(values,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto')
   ax.set_xticks(range(5),PREFIXES);ax.set_yticks(range(14),[LABELS[n] for n in ORDER]);ax.tick_params(length=0)
   ax.set_title(f"{shape.title()} prefix · "+{'fork':'one junction','two_2':'extra junction at +2','cycle_2':'real cycle at ±2'}[f],fontsize=11)
   ax.set_xlabel('Edges from source to first junction')
   for y in range(14):
    for x in range(5):ax.text(x,y,f'{values[y,x]:.0f}',ha='center',va='center',fontsize=8,color='white' if values[y,x]>60 else '#172837')
 fig.subplots_adjust(left=.23,right=.9,top=.9,bottom=.105,hspace=.25,wspace=.12)
 cb=fig.colorbar(im,cax=fig.add_axes([.92,.26,.015,.43]));cb.set_label('Complete shortest goal pairs (%)')
 fig.suptitle('V12J · decision distance on matched downstream graphs',fontsize=17,y=.96)
 fig.text(.5,.925,'Each cell: 12 independent contexts × 8 paired poses. Genomes fixed before fresh maze generation.',ha='center',fontsize=10)
 fig.text(.5,.025,'Variants and poses are correlated; the two shapes duplicate inputs at distances 1 and 2.\nEvery random model scores zero paired solutions at attachment distance 4. This restricted grammar is not a general maze benchmark.',ha='center',fontsize=9)
 save(fig,'distance_matrix')

 cases,_,meta=load(OUT/'confirmation')
 # Descriptive examples selected after evaluation; never new model/holdout selections.
 specs=[('local_long','normal',3,'straight',8,'fork','Local · straight prefix 8'),
        ('local_long','normal',3,'bent',8,'fork','Same local model · bent prefix 8'),
        ('branch_narrow','normal',0,'straight',1,'cycle_2','Branch · normal nonlocal input'),
        ('branch_narrow','nonlocal_off',0,'straight',1,'cycle_2','Same Branch model · nonlocal zero')]
 wanted={}
 for col,(name,mode,pose,shape,p,f,title) in enumerate(specs):
  for cid,m in meta.items():
   if m['index']==0 and m['shape']==shape and m['pose']==pose and m['prefix']==p and m['family']==f:
    wanted[name,mode,cid]=col
 outputs={}
 for file in ('normal','interventions'):
  for e in lines(OUT/f'{file}.jsonl.gz'):
   key=(e['model'],e['mode'],e['row']['case'])
   if key in wanted:outputs[key]=e['row']
 assert len(outputs)==8
 fig,axes=plt.subplots(2,4,figsize=(14,7.3));colors=['#e4e7e5','#ffffff','#3a9e80','#db7659','#e6b24e']
 certificates=[]
 for key,row in outputs.items():
  name,mode,cid=key;md=meta[cid];o=cases[cid];col=wanted[key];ax=axes[md['side'],col]
  mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:625].astype(bool)
  truth=np.zeros(625,bool);truth[o.path]=True;grid=np.frombuffer(o.maze.cells,np.uint8).copy()
  grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
  ax.imshow(grid.reshape(25,25),cmap=ListedColormap(colors),vmin=0,vmax=4,interpolation='nearest')
  for p,label,color in ((o.maze.start,'S','#273f7c'),(o.maze.goal,'G','#7d387d')):ax.text(p%25,p//25,label,ha='center',va='center',fontsize=9,color=color,fontweight='bold')
  ax.set_xlim(.5,23.5);ax.set_ylim(23.5,.5);ax.set_xticks([]);ax.set_yticks([])
  ax.set_title(specs[col][-1]+f" · goal {md['side']+1}\n"+('Shortest path' if row['optimal'] else row['failure'].replace('_',' '))+f" · tick {row['steps']}",fontsize=9)
  certificates.append(dict(case=cid,model=name,mode=mode,row=row,shortest_edges=len(o.path)-1,alternative_edges=len(md['alternative'])-1 if md['alternative'] else None))
 fig.suptitle('Two matched contrasts: shape sensitivity and nonlocal interference',fontsize=16,y=.98)
 fig.text(.5,.935,'Saved completed outputs · first context · examples chosen after evaluation; no additional candidate calls',ha='center',fontsize=10)
 fig.legend(handles=[Patch(color=colors[i],label=l) for i,l in [(2,'Correct illuminated path'),(3,'Extra illuminated cells'),(4,'Missing path cells')]],loc='lower center',ncol=3,frameon=False)
 fig.subplots_adjust(top=.86,bottom=.08,wspace=.13,hspace=.25);save(fig,'matched_rasters')
 (OUT/'visuals/raster_certificates.json').write_text(json.dumps(certificates,indent=2)+'\n')

if __name__=='__main__':run()
