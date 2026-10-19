"""Post-hoc illustration of the longest complete pair from a frozen primary; saved rasters only."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.fork_data import load
from maze_evolution.fork_study import lines
OUT=ROOT/'results/fork_pressure';VIS=OUT/'visuals'
cases,_=load(OUT/'confirmation');s=json.loads((OUT/'confirmation/summary.json').read_text())
a='fork/carry/evolved/branch/evolution/0/archives/pair';b='fork/carry/evolved/current/evolution/0/archives/pair'
rows={r['model']:r['rows'] for r in lines(OUT/'confirmation/outputs.jsonl.gz')};selected=rows[s['aliases'][a]]
possible=[selected[i:i+2] for i in range(0,len(selected),2) if selected[i]['fork'] and selected[i]['pair_optimal']]
pair=max(possible,key=lambda p:(min(len(cases[r['case']].path) for r in p),max(len(cases[r['case']].path) for r in p)))
current={r['case']:r for r in rows[s['aliases'][b]]}
plt.rcParams.update({'font.family':'DejaVu Sans','figure.facecolor':'#fafaf7','savefig.facecolor':'#fafaf7'})
fig,axes=plt.subplots(2,3,figsize=(12,10))
for side,row in enumerate(pair):
 o=cases[row['case']];m=o.maze
 for column,(title,r,color) in enumerate([('Branch',row,'#e17c32'),('Current',current[row['case']],'#4477aa'),('Shortest-path oracle',None,'#62b389')]):
  mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:len(m.cells)] if r else np.isin(np.arange(len(m.cells)),o.path)
  grid=np.array(list(m.cells),int);grid[np.flatnonzero(mask)]=2;ax=axes[side,column]
  ax.imshow(grid.reshape(m.h,m.w),cmap=ListedColormap(['#263445','#ebede8',color]),vmin=0,vmax=2,interpolation='none')
  ax.scatter([m.start%m.w],[m.start//m.w],s=32,c='#42adfb',edgecolors='white');ax.scatter([m.goal%m.w],[m.goal//m.w],s=55,c='#f4df49',marker='*',edgecolors='#263445')
  ax.set_xticks([]);ax.set_yticks([]);ax.set_title(title+f' · goal {side+1}',fontsize=11)
  if r:ax.set_xlabel(('Shortest route' if r['optimal'] else r['failure'].replace('_',' '))+f" · tick {r['steps']}",fontsize=9)
lengths=[len(cases[r['case']].path)-1 for r in pair]
fig.suptitle(f'Goal-switched branch suppression: {lengths[0]}- and {lengths[1]}-edge routes\nCarry multirange replicate 0 · fixed primary selections',fontsize=14)
fig.text(.5,.025,'Post-hoc illustration chosen from saved successes, not a new test. Blue: source · star: goal.\nAll successes of this Branch genome survive goal-pulse removal and nonlocal-read zeroing; flags and halting remain.',ha='center',fontsize=9)
fig.subplots_adjust(left=.025,right=.975,bottom=.13,top=.88,hspace=.42,wspace=.13);fig.savefig(VIS/'longer_pair.png',dpi=180,bbox_inches='tight');plt.close(fig)
(VIS/'longer_pair_selection.json').write_text(json.dumps(dict(branch_alias=a,current_alias=b,cases=[r['case'] for r in pair],lengths=lengths,selection='Post-hoc longest minimum path length, then maximum; first tie. Saved evidence only.'),indent=2)+'\n')
