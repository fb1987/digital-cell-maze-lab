"""Scientific figures from immutable V12F saved outputs; no model inference."""
import json
from pathlib import Path
import sys
import gzip

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.foundation_data import load_pairs
from maze_evolution.route_confirmation import OUT,lines
from maze_evolution.route_confirmation_analysis import unpack

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titleweight':'bold',
    'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'#fafbfc'})
vis=OUT/'visuals';vis.mkdir(exist_ok=True)
a=json.loads((OUT/'analysis.json').read_text())
fig=plt.figure(figsize=(13.6,6.2),facecolor='#fafbfc')
gs=fig.add_gridspec(1,2,left=.045,right=.98,top=.76,bottom=.22,width_ratios=[1.13,1],wspace=.27)
left=fig.add_subplot(gs[0]);left.axis('off')
names=[('Target','target'),('Immediate parent','parent'),('V12D checkpoint','checkpoint'),
       ('Paired replacement','replacement'),('Intact wavefront','intact'),('Compiled BFS','bfs')]
values=[]
for label,key in names:
    s=a['summaries'][key+'/normal']
    long=sum(v['optimal'] for k,v in a['strata'][key+'/normal'].items() if not k.endswith('/0'))
    values.append([label,f"{s['optimal']}/768",f"{s['complete_pairs']}/384",f'{long}/512'])
table=left.table(cellText=values,colLabels=['Frozen model','Shortest routes','Complete pairs','9–32 edges'],
    cellLoc='center',colLoc='center',loc='center',colWidths=[.34,.23,.23,.2])
table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,2)
for (r,c),cell in table.get_celld().items():
    cell.set_edgecolor('#fafbfc');cell.set_linewidth(3)
    cell.set_facecolor('#e9edf4' if r==0 else '#eef2f8' if r<5 else '#d9eee7')
    if r==0:cell.set_text_props(weight='bold',fontsize=9)
    if c==0 and r>0:cell.set_text_props(ha='left',weight='bold' if r==1 else 'normal')
left.set_title('Normally emitted, independently graded outputs',loc='left',pad=18,fontsize=12)
right=fig.add_subplot(gs[1])
labels=['Junction state\nchanges','Output changes\n(excluding goals)','Correct paired\nexit choices']
counts=[a['probes']['normal']['junction_response'],a['probes']['normal']['output_response_excluding_goals'],a['probes']['normal']['strict_any']]
y=np.arange(3)
right.barh(y,counts,color=['#587bb0','#587bb0','#c66e4e'],height=.54)
right.set_yticks(y,labels);right.invert_yaxis();right.set_xlim(0,435);right.set_xticks([0,128,256,384]);right.set_xlabel('Paired poses, out of 384')
right.spines[['left','right','top']].set_visible(False);right.tick_params(axis='y',length=0)
right.grid(axis='x',alpha=.16);right.set_axisbelow(True)
for j,value in enumerate(counts):right.text(value+7,j,f'{value}/384',va='center',weight='bold',fontsize=10)
right.set_title('Target: response to switching the goal',loc='left',pad=18,fontsize=12)
fig.text(.045,.94,'V12F  |  Target goal signals spread; branch choices remain incorrect',fontsize=19,weight='bold',color='#172b46')
fig.text(.045,.87,'48 independent reachable layouts · trees and cyclic grids · 4–32 edges · all 8 rotations/reflections',fontsize=11,color='#4d5c6b')
fig.text(.045,.125,'The target fails the preregistered transfer screen. BFS and the intact wavefront also solve all 64 disconnected inputs.',fontsize=11,weight='bold',color='#172b46')
fig.text(.045,.07,'Right: any recorded tick up to 96, subject to work caps; these diagnostic changes are not successful routes.\nPoses share base layouts. No evolution or genotype tuning occurred in this confirmation.',fontsize=9,color='#526071',linespacing=1.5)
fig.savefig(vis/'transfer_and_signal.png',dpi=180);fig.savefig(vis/'transfer_and_signal.svg');plt.close(fig)

cases,groups=load_pairs(OUT/'confirmation')
rows={(r['model'],r['variant'],r['case']):r for r in lines(OUT/'confirmation/normal.jsonl.gz')}
# Deliberately first manifest group/pose, not chosen for candidate performance.
group=groups[0];pair=group.pairs[0]
fig,axes=plt.subplots(2,3,figsize=(12,8.1),facecolor='#fafbfc')
for side,o in enumerate(pair.cases):
    m=o.maze
    for col,(model,variant,title) in enumerate((('bfs','normal','BFS shortest path'),('target','normal','Target: native stopping'),('target','source_only','Target: endpoint checks removed'))):
        ax=axes[side,col];r=rows[model,variant,m.case_id]
        canvas=np.where(np.frombuffer(m.cells,np.uint8).reshape(m.h,m.w),1,0)
        mask=unpack(r,len(m.cells)).reshape(m.h,m.w);canvas[mask>0]=2
        ax.imshow(canvas,cmap=ListedColormap(['#202c3c','#edf0f4','#df9b47']),vmin=0,vmax=2,interpolation='nearest')
        for p,marker,color,label in ((m.start,'o','#fff','S'),(m.goal,'*','#42dbb2','G')):
            ax.scatter(p%m.w,p//m.w,s=72 if marker=='o' else 140,marker=marker,color=color,edgecolors='#152439',linewidths=1)
        j=o._foundation_label['vertex'];ax.scatter(j%m.w,j//m.w,s=125,marker='s',facecolors='none',edgecolors='#cd4acb',linewidths=1.7)
        ax.set_xticks([]);ax.set_yticks([])
        status='shortest' if r['optimal'] else r['failure'].replace('_',' ')
        tick='' if model=='bfs' else f" · tick {r['steps']}"
        ax.set_title(f'{title}\n{status}{tick}',fontsize=10,pad=9)
        if col==0:ax.set_ylabel(f"Goal {'A' if side==0 else 'B'} · {len(o.path)-1} edges",fontsize=11,labelpad=14)
fig.suptitle('A goal response can still leave an invalid branched raster',x=.05,y=.98,ha='left',fontsize=17,weight='bold',color='#172b46')
fig.text(.05,.925,'First reachable base and first pose in the frozen manifest; illustration only, not an additional test.',fontsize=10,color='#526071')
fig.subplots_adjust(left=.06,right=.97,top=.85,bottom=.1,hspace=.35,wspace=.15)
fig.text(.05,.045,'Orange: emitted output   •   White circle: source   •   Green star: current goal   •   Purple square: shared decision junction',fontsize=10,color='#526071')
fig.savefig(vis/'paired_failure.png',dpi=180);fig.savefig(vis/'paired_failure.svg');plt.close(fig)
for svg in vis.glob('*.svg'):
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
print(vis)
