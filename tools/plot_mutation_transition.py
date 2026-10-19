"""Post-registration V12P figures from frozen saved outputs; no candidate calls."""
import sys,json
from pathlib import Path
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
V=OUT/'visuals';V.mkdir(exist_ok=True);a=read_compressed(OUT/'analysis.json.gz');p=read_compressed(OUT/'panel.json.gz')


def save(fig,name):
    for ext in ('png','svg','pdf'):
        path=V/f'{name}.{ext}';fig.savefig(path,dpi=145,bbox_inches='tight')
        if ext=='svg':path.write_text('\n'.join(s.rstrip() for s in path.read_text().splitlines())+'\n')
    plt.close(fig)

fig,axes=plt.subplots(1,3,figsize=(14,4.7))
for top,col in [('local','#278c70'),('evolved','#bc7950')]:
    ms=[a['normal'][f'{top}/route/d{i}'] for i in range(17)]
    for ax,field,title in zip(axes,('pairs','corridors','no_path'),('Complete shortest pairs / 2,080','Correct corridors / 4,160','Correct disconnected inputs / 4,160')):
        ax.plot(range(17),[m[field] for m in ms],'-o',color=col,label='Local' if top=='local' else 'Nonlocal',markersize=4);ax.set_title(title);ax.set_xlabel('Cumulative saved edit');ax.set_xticks(range(0,17,2));ax.spines[['top','right']].set_visible(False);ax.set_ylim(0,max(1,max(m[field] for m in ms))*1.1)

for ax,field in zip(axes,('pairs','corridors','no_path')):
    maximum=max(a['normal'][f'{top}/route/d{i}'][field] for top in ('local','evolved') for i in range(17));ax.set_ylim(0,max(1,maximum)*1.1)
axes[0].legend();fig.suptitle('New corpus: every saved state of the random-origin routing lineage',fontsize=14)
fig.text(.5,.01,'Same frozen inputs for every state. No new mutation, training or selection; poses and control variants are correlated.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.94));save(fig,'lineage_transition')

rows=[('full',0),('full',1),('full',2),('full',4),('no_stem',0),('spur',2),('spur',4)];labels=['Full stem · prefix 0 · degree 3','Full stem · prefix 1 · degree 2','Full stem · prefix 2 · degree 2','Full stem · prefix 4 · degree 2','No stem · prefix 0 · degree 2','Source spur · prefix 2 · degree 3','Source spur · prefix 4 · degree 3']
fig,axes=plt.subplots(1,2,figsize=(12,6))
for ax,shape in zip(axes,('straight','turning')):
    matrix=[];counts=[]
    for control,prefix in rows:
        vv=[];cc=[]
        for arm in (2,3,4,6):
            ds=[d for d in a['normal']['local/route/d16']['details'].values() if d['stratum'].split('/')[0]=='core' and d['stratum'].split('/')[1]==str(arm) and d['stratum'].split('/')[2]==shape and d['stratum'].split('/')[4:6]==[control,str(prefix)]]
            n=sum(d['complete'] for d in ds);vv.append(n/len(ds));cc.append(f'{n}/{len(ds)}')
        matrix.append(vv);counts.append(cc)
    ax.imshow(matrix,vmin=0,vmax=1,cmap='YlGn',aspect='auto');ax.set_xticks(range(4),[2,3,4,6]);ax.set_yticks(range(7),labels if shape=='straight' else []);ax.set_title(f'{shape.title()} goal arms');ax.set_xlabel('Junction-to-goal length (edges)')
    for r in range(7):
        for c in range(4):ax.text(c,r,counts[r][c],ha='center',va='center',fontsize=10,color='white' if matrix[r][c]>.6 else 'black')
fig.suptitle('Depth-16 local target: geometry and degree controls',fontsize=14)
fig.text(.5,.01,'Counts include both stem labels; no-stem duplicates are correlated. Full-stem source moves leave the layout fixed.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.94));save(fig,'matched_transfer')

fig,axes=plt.subplots(1,2,figsize=(12,5))
modes=('pulse_off','flag_off','both_off','endpoint_off','nonlocal_off');mode_labels=['Goal pulse off','Goal flag off','Both off','Endpoint check off','Nonlocal values zero']
for ax,top in zip(axes,('local','evolved')):
    key=p['aliases'][top+'/route/d16'];probe=a['mechanisms'][key];vals=[probe[m]['retained'] for m in modes];normal=probe[modes[0]]['eligible_normal_pairs'];bars=ax.barh(range(5),vals,color='#278c70');ax.set_yticks(range(5),mode_labels);ax.invert_yaxis();ax.set_xlim(0,max(1,normal)*1.22)
    for i,m in enumerate(modes):ax.text(vals[i]+max(1,normal)*.02,i,f"{vals[i]}/{normal}  (+{probe[m]['new']} new)",va='center',fontsize=9)
    ax.set_title(('Local' if top=='local' else 'Nonlocal')+f' target · {normal} normal eligible pairs');ax.set_xlabel('Normal successful pairs retained');ax.spines[['top','right']].set_visible(False)
fig.suptitle('Preselected interventions on ordinary emitted outputs',fontsize=14)
fig.text(.5,.01,'A zero normal denominator cannot establish necessity. New intervention successes are shown separately.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.94));save(fig,'mechanisms')

# Retrospective illustration: first gain at a consecutive saved step, no new calls.
choices=[]
for top,series in a['transitions'].items():
    for tr in series:
        if tr['gained_keys']:
            for k in tr['gained_keys']:choices.append((tr['depth'],top,k))
if choices:
    depth,top,pair=min(choices);config,pose=pair.rsplit('/pose',1);pose=int(pose)
    cases,contexts,meta=load(OUT/'confirmation');wanted=sorted([cid for cid,m in meta.items() if m['config']==config and m['pose']==pose and m['family']=='paired'],key=lambda c:meta[c]['side'])
    ids=[p['aliases'][f'{top}/route/d{d}'] for d in (depth-1,depth)];saved={}
    for rec in lines(OUT/'confirmation/responses.jsonl.gz'):
        if rec['mode']=='normal' and rec['model'] in ids and rec['row']['case'] in wanted:saved[rec['model'],rec['row']['case']]=rec['row']
    fig,axes=plt.subplots(2,2,figsize=(8,8));pal=['#e2e6e4','#ffffff','#329879','#d66e53','#e3b342'];cert=[]
    for col,key in enumerate(ids):
        for side,cid in enumerate(wanted):
            o=cases[cid];m=o.maze;r=saved[key,cid];mask=np.unpackbits(np.frombuffer(bytes.fromhex(r['mask']),np.uint8),bitorder='little')[:m.w*m.h].astype(bool);truth=np.zeros(m.w*m.h,bool);truth[o.path]=True;grid=np.frombuffer(m.cells,np.uint8).copy();grid[truth&mask]=2;grid[mask&~truth]=3;grid[truth&~mask]=4
            ax=axes[side,col];ax.imshow(grid.reshape(m.h,m.w),cmap=ListedColormap(pal),vmin=0,vmax=4,interpolation='nearest')
            for q,t in ((m.start,'S'),(m.goal,'G')):ax.text(q%m.w,q//m.w,t,ha='center',va='center',fontsize=8,fontweight='bold')
            ax.set_title(f"Depth {depth-1+col} · goal {side+1}\n"+('Shortest path' if r['optimal'] else 'Incorrect'));ax.set_xticks([]);ax.set_yticks([]);cert.append(dict(model=key,row=r,metadata=meta[cid]))
    fig.suptitle(f'First observed paired gain · {top} topology',fontsize=14);fig.legend(handles=[Patch(color=pal[i],label=t) for i,t in [(2,'Correct output'),(3,'Extra output'),(4,'Missing route')]],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.04));fig.text(.5,.015,'Retrospective illustration of saved normal outputs; no new test or selection.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.1,1,.94));save(fig,'first_transition_example');(V/'raster_certificates.json').write_text(json.dumps(cert,indent=2)+'\n')
print(V)
