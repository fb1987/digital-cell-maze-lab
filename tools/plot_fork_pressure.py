"""Publication-style V12G figures from frozen evidence; no model selection."""
import json,gzip,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution.fork_data import load
from maze_evolution.fork_study import lines
OUT=ROOT/'results/fork_pressure';VIS=OUT/'visuals'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fafaf7','axes.facecolor':'#fafaf7','savefig.facecolor':'#fafaf7'})


def save(fig,name):
    fig.savefig(VIS/(name+'.png'),dpi=170,bbox_inches='tight');fig.savefig(VIS/(name+'.svg'),bbox_inches='tight')
    p=VIS/(name+'.svg');p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n');plt.close(fig)


def run():
    VIS.mkdir(exist_ok=True);a=json.loads((OUT/'analysis.json').read_text());s=json.loads((OUT/'confirmation/summary.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(12,4.5));x=np.arange(4);groups=[('carry','local'),('carry','evolved'),('fresh','local'),('fresh','evolved')]
    for offset,(label,color) in enumerate([('frozen','#8c949f'),('current/evolution','#4477aa'),('branch/evolution','#e17c32')]):
        vals=[a['primary']['/'.join([o,t,label])] for o,t in groups]
        for ax,field,denom in ((axes[0],'complete_pairs',576),(axes[1],'corridor_optimal',1152)):
            ys=[r[field] for r in vals];bars=ax.bar(x+(offset-1)*.24,ys,width=.23,color=color,label=label.split('/')[0].capitalize())
            ax.bar_label(bars,padding=3,fontsize=8)
            ax.set_ylabel(f'Successes / {denom} across three replicates')
    for ax in axes:ax.set_xticks(x,['Carry\nlocal','Carry\nmultirange','Fresh\nlocal','Fresh\nmultirange']);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.margins(y=.2)
    axes[0].set_title('Complete goal-switched fork pairs');axes[1].set_title('Shortest matched corridor outputs');axes[0].legend(frameon=False,fontsize=9)
    fig.suptitle('V12G · fresh tests after the fixed 12-minute pilot',fontsize=15,y=1.02)
    fig.text(.5,-.035,'24 independent fork bases × 8 poses; poses and repeated genotype selections are correlated. Resampling is tabulated in the report.',ha='center',fontsize=9)
    fig.tight_layout();save(fig,'confirmation')
    with gzip.open(OUT/'checkpoint.latest.json.gz','rt') as f:states=json.load(f)['states']
    fig,axes=plt.subplots(2,2,figsize=(10,6),sharex=True,sharey=True)
    for ax,(origin,topology) in zip(axes.flat,groups):
        for policy,color in [('current','#4477aa'),('branch','#e17c32')]:
            subset=[v for v in states if v['config']['origin']==origin and v['config']['topology']==topology and v['config']['policy']==policy and v['config']['method']=='evolution']
            ys=[]
            for v in subset:
                y=[v['frozen']['pair']['rank'][0]]+[h['archives']['pair']['rank'][0] for h in v['history']];ys.append(y)
                ax.step(range(len(y)),y,where='post',color=color,alpha=.22,lw=1)
            ax.step(range(len(y)),np.mean(ys,axis=0),where='post',color=color,lw=2,label=policy.capitalize())
        ax.set_title(origin.capitalize()+' · '+('local' if topology=='local' else 'multirange'));ax.grid(alpha=.15)
    axes[0,0].legend(frameon=False);fig.supxlabel('Additional matched generations');fig.supylabel('Completed validation fork pairs / 32');fig.suptitle('Correlated validation history · thin lines are individual replicates',fontsize=13);fig.tight_layout();save(fig,'validation_history')
    # Illustration: deterministic first primary branch model with a complete pair;
    # if none, first carry/local/branch model and first final base. Displayed only,
    # never used to choose a primary genome or infer independent accuracy.
    records={r['model']:r['rows'] for r in lines(OUT/'confirmation/outputs.jsonl.gz')};cases,_=load(OUT/'confirmation')
    candidates=[(k,v) for k,v in s['aliases'].items() if '/branch/evolution/' in k and k.endswith('/archives/pair')]
    chosen=None
    for alias,key in sorted(candidates):
        rows=records[key]
        for i in range(0,len(rows),2):
            if rows[i]['fork'] and rows[i]['pair_optimal']:chosen=(alias,key,rows[i:i+2]);break
        if chosen:break
    if chosen is None:
        alias,key=sorted(candidates)[0];chosen=(alias,key,records[key][:2])
    alias,key,rows=chosen;fig,axes=plt.subplots(2,2,figsize=(8,8))
    for side,row in enumerate(rows):
        o=cases[row['case']];m=o.maze;mask=np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:len(m.cells)]
        for col,selection in enumerate((mask,np.isin(np.arange(len(m.cells)),o.path))):
            grid=np.array(list(m.cells),int);grid[np.flatnonzero(selection)]=2
            ax=axes[side,col];ax.imshow(grid.reshape(m.h,m.w),cmap=ListedColormap(['#263445','#ebede8','#e17c32' if col==0 else '#62b389']),vmin=0,vmax=2,interpolation='none')
            ax.scatter([m.start%m.w],[m.start//m.w],s=55,c='#4f9ee8',edgecolors='white');ax.scatter([m.goal%m.w],[m.goal//m.w],s=65,c='#e4d74c',marker='*',edgecolors='#263445')
            ax.set_xticks([]);ax.set_yticks([]);ax.set_title(('Candidate' if col==0 else 'Shortest-path oracle')+f' · goal {side+1}')
    fig.suptitle('Illustrative frozen Branch selection\n'+alias.replace('/archives/pair',''),fontsize=11)
    fig.text(.5,.025,'Blue circle: source · yellow star: goal · isolated cells are shared neutral clutter',ha='center',fontsize=9);fig.tight_layout(rect=[0,.04,1,.94]);save(fig,'example_pair')
    (VIS/'example_selection.json').write_text(json.dumps(dict(alias=alias,model=key,cases=[r['case'] for r in rows],selection='First complete primary Branch pair in sorted alias/case order, otherwise first pair; illustrative only'),indent=2)+'\n')

if __name__=='__main__':run()
