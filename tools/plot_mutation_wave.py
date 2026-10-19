"""Saved-output illustration and independent graph-distance check; zero inference."""
import sys,json
from pathlib import Path
from collections import deque
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from maze_evolution.foundation_study import read_compressed
from maze_evolution.mutation_transition_data import OUT,load
from maze_evolution.routing_transfer import lines
p=read_compressed(OUT/'panel.json.gz');cases,_,meta=load(OUT/'confirmation');key=p['aliases']['local/route/d16'];depth9=p['aliases']['local/route/d9'];cache={};checked=0;wanted={}
base=min(m['template'] for m in meta.values() if not m['stress'] and m['arm']==6 and m['shape']=='turning')
for rec in lines(OUT/'confirmation/responses.jsonl.gz'):
    if rec['mode']!='normal' or rec['model'] not in (key,depth9):continue
    row=rec['row'];o=cases[row['case']];m=o.maze;d=meta[row['case']];ck=(m.cells,m.goal)
    if ck not in cache:
        dist={m.goal:0};queue=deque([m.goal])
        while queue:
            q=queue.popleft();adj=[]
            if q%m.w:adj.append(q-1)
            if q%m.w<m.w-1:adj.append(q+1)
            if q>=m.w:adj.append(q-m.w)
            if q+m.w<len(m.cells):adj.append(q+m.w)
            for z in adj:
                if m.cells[z] and z not in dist:dist[z]=dist[q]+1;queue.append(z)
        cache[ck]=dist
    dist=cache[ck];radius=dist.get(m.start);expected={q for q,v in dist.items() if radius is None or v<=radius}
    bits=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:len(m.cells)];assert set(np.flatnonzero(bits))==expected;checked+=1
    if rec['model']==key and d['template']==base and d['pose']==0 and d['control']=='full' and d['bend']=='straight' and d['prefix'] in (0,1) and d['family']=='paired':wanted[d['prefix'],d['side']]=row
fig,axes=plt.subplots(2,2,figsize=(9,9));pal=['#e2e6e4','#ffffff','#329879','#d66e53','#e3b342'];cert=[]
for col,prefix in enumerate((0,1)):
    for side in (0,1):
        row=wanted[prefix,side];o=cases[row['case']];m=o.maze;mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:len(m.cells)].astype(bool);truth=np.zeros(len(m.cells),bool);truth[o.path]=True;grid=np.frombuffer(m.cells,np.uint8).copy();grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
        ax=axes[side,col];ax.imshow(grid.reshape(m.h,m.w),cmap=ListedColormap(pal),vmin=0,vmax=4,interpolation='nearest')
        for q,label in ((m.start,'S'),(m.goal,'G')):ax.text(q%m.w,q//m.w,label,ha='center',va='center',fontsize=9,fontweight='bold')
        ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f"Source prefix {prefix} · goal {side+1}\n"+('Correct shortest path' if row['optimal'] else 'Extra branch illuminated'))
        cert.append(dict(model=key,row=row,metadata=meta[row['case']]))
fig.suptitle('Same maze, source moved one edge: correct route becomes a branching wave',fontsize=13)
fig.legend(handles=[Patch(color=pal[i],label=t) for i,t in [(2,'Correct route output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.04));fig.text(.5,.015,'Retrospective saved-raster illustration. Exact goal-distance-ball equivalence holds across all recorded target inputs.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.1,1,.94));v=OUT/'visuals'
for ext in ('png','svg','pdf'):
 f=v/f'goal_wave_boundary.{ext}';fig.savefig(f,dpi=150,bbox_inches='tight')
 if ext=='svg':f.write_text('\n'.join(s.rstrip() for s in f.read_text().splitlines())+'\n')
plt.close(fig);(v/'wave_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')
(OUT/'independent_wave_check.json').write_text(json.dumps(dict(passed=True,saved_rasters_checked=checked,new_candidate_calls=0,post_registration=True,method='Independent deque traversal from goal; shortest source distance thresholds every open vertex.'),indent=2)+'\n')
print('independent wave checks',checked)
