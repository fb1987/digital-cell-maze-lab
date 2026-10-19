"""Standalone V12E figures from saved, audited outputs; no candidate inference."""
import argparse
from collections import deque
import gzip
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np


def compressed(path):
    with gzip.open(path,'rt') as f: return json.load(f)


def key(topology,policy,method,rep):
    return f'foundation_pair_{policy}/{topology}/fresh/{method}/{rep}'


def run(out):
    out=Path(out)
    visual=out/'visuals'
    visual.mkdir(exist_ok=True)
    data=json.loads((out/'plot_data.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'savefig.facecolor':'white'})
    arms=[('current','evolution','Current','#5176a3'),('paired','evolution','Paired first','#087e8b'),
          ('current','resample','Resampling','#bd5c37')]
    fig,axes=plt.subplots(1,2,figsize=(12,4.7),sharey=True)
    for ax,topology in zip(axes,('local','evolved')):
        for policy,method,label,color in arms:
            series=[]
            for rep in range(3):
                hs=data['histories'][key(topology,policy,method,rep)]
                xs=[h['generation']+1-data['start_generation'] for h in hs]
                ys=[h['common_archives']['paired']['rank'][0] for h in hs]
                ax.plot(xs,ys,color=color,alpha=.22,linewidth=.8)
                series.append(ys)
            ax.plot(xs,np.mean(series,axis=0),color=color,linewidth=2,label=label)
        ax.set_title(f'{topology.capitalize()} signalling')
        ax.set_xlabel('Additional matched generations')
        ax.set_ylabel('Complete validation pairs / 64 reachable pairs')
        ax.grid(axis='y',alpha=.15)
    axes[0].legend(frameon=False)
    fig.suptitle('Common archive: validation progress, not unseen-test accuracy',fontsize=14)
    fig.text(.5,.02,'Bold: mean of three replicates. Thin: individual replicates. Both breeding policies use the same final archive rule.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.93))
    fig.savefig(visual/'validation.png',dpi=160)
    fig.savefig(visual/'validation.svg')
    plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(12,4.7),sharey=True)
    bars=[*[(p,m,'champion',label,c) for p,m,label,c in arms],
          ('paired','evolution','checkpoint','V12D checkpoint','#a9b3bd')]
    for ax,topology in zip(axes,('local','evolved')):
        for offset,(policy,method,role,label,color) in enumerate(bars):
            values=np.asarray([[data['results'][key(topology,policy,method,r)+'/'+role+'/micro']['bands'][str(l)]['pairs']/48
                                for l in range(5)] for r in range(3)])
            xs=np.arange(5)+(offset-1.5)*.2
            ax.bar(xs,values.mean(axis=0),.18,color=color,label=label)
            for rep in range(3): ax.scatter(xs+(rep-1)*.035,values[rep],s=10,color='#172d3a',zorder=3)
        ax.set_title(topology.capitalize()+' signalling')
        ax.set_xticks(range(5),('1','2','3–4','5–8','9–16'))
        ax.set_xlabel('Both source–goal distances (edges)')
        ax.set_ylabel('Fraction of complete shortest pairs')
        ax.set_ylim(-.015,1.05)
        ax.grid(axis='y',alpha=.15)
    axes[0].legend(frameon=False,fontsize=9)
    fig.suptitle('Unseen paired routes: retention and longer transfer',fontsize=14)
    fig.text(.5,.02,'Bars: mean of three replicates; dots: each replicate. Each band/replicate has six base layouts × eight correlated poses.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.93))
    fig.savefig(visual/'fresh_pairs.png',dpi=160)
    fig.savefig(visual/'fresh_pairs.svg')
    plt.close(fig)

    times=sorted({r['additional_generation'] for r in data['timecourse']})
    indexed_time={(r['condition'],r['additional_generation']):r for r in data['timecourse']}
    fig,axes=plt.subplots(2,2,figsize=(12,7),sharex=True)
    for col,topology in enumerate(('local','evolved')):
        for row,(levels,denom,title) in enumerate([((2,3),96,'3–8-edge transfer'),((1,),48,'Two-edge retention')]):
            ax=axes[row,col]
            maximum=0.
            for policy,method,label,color in arms:
                values=np.asarray([[sum(indexed_time[key(topology,policy,method,r),t]['levels'][str(l)]['paired_optimal'] for l in levels)/denom
                                    for t in times] for r in range(3)])
                maximum=max(maximum,float(values.max()))
                for values_ in values: ax.plot(times,values_,color=color,alpha=.20,linewidth=.8)
                ax.plot(times,values.mean(axis=0),marker='o',markersize=4,color=color,label=label,linewidth=2)
            ax.set_title(f'{topology.capitalize()} · {title}')
            ax.set_xlabel('Additional matched generations')
            ax.set_ylabel('Fraction of complete shortest pairs')
            ax.set_ylim(-.01,max(.08,min(1.04,maximum*1.12+.01)))
            ax.set_xticks(times)
            ax.grid(axis='y',alpha=.15)
    axes[0,0].legend(frameon=False)
    fig.suptitle('Prespecified models on the same unseen corpus',fontsize=14)
    fig.text(.5,.01,'Bold: mean of three replicates; thin: individual replicates. Models froze before case generation. Time points and poses are correlated.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.94))
    fig.savefig(visual/'timecourse.png',dpi=160)
    fig.savefig(visual/'timecourse.svg')
    plt.close(fig)

    frozen=compressed(out/'frozen_selections.json.gz')
    lookup={m['case_id']:m for name in ('mazes.json.gz','general_mazes.json.gz') for m in compressed(out/'confirmation'/name)}
    with gzip.open(out/'confirmation/outputs.jsonl.gz','rt') as f: records=[json.loads(line) for line in f]
    indexed={(r['key'],r['role'],r['scope']):r for r in records}

    def mask(row,m):
        return np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']),np.uint8),bitorder='little')[:m['w']*m['h']]

    def shortest(m):
        cells=bytes.fromhex(m['cells_hex'])
        queue,parents=deque([m['start']]),{m['start']:None}
        while queue:
            p=queue.popleft()
            if p==m['goal']: break
            y,x=divmod(p,m['w'])
            for dy,dx in ((0,-1),(0,1),(-1,0),(1,0)):
                yy,xx=y+dy,x+dx
                q=yy*m['w']+xx
                if 0<=yy<m['h'] and 0<=xx<m['w'] and cells[q] and q not in parents:
                    parents[q]=p
                    queue.append(q)
        result=np.zeros(len(cells),np.uint8)
        p=m['goal']
        if p in parents:
            while p is not None:
                result[p]=1
                p=parents[p]
        return result

    def grid(ax,m,raster,correct,title):
        cells=np.frombuffer(bytes.fromhex(m['cells_hex']),np.uint8)
        pixels=np.where(cells,1,0)
        pixels[raster>0]=2
        ax.imshow(pixels.reshape(m['h'],m['w']),interpolation='nearest',vmin=0,vmax=2,
            cmap=ListedColormap(('#24333e','#eef1f3','#20a18b' if correct else '#d46e52')))
        for field,color,marker in (('start','#2265c8','o'),('goal','#edb51c','*')):
            y,x=divmod(m[field],m['w'])
            ax.scatter(x,y,c=color,marker=marker,s=90 if marker=='*' else 35,edgecolors='white',linewidths=.6)
        ax.set_xticks([]);ax.set_yticks([])
        ax.set_title(title.replace('_',' '),fontsize=9)

    examples=[]
    for topology in ('local','evolved'):
        selected=max(sorted(k for k,v in frozen.items() if v['config']['selection_policy']=='paired'
                            and v['config']['topology']==topology),
                     key=lambda k:tuple(frozen[k]['common_archives']['paired']['rank']))
        rep=frozen[selected]['config']['replicate']
        current=key(topology,'current','evolution',rep)
        rows=indexed[selected,'champion','micro']['cases']
        pairs=[rows[i:i+2] for i in range(0,len(rows),2)]
        challenge=lambda pair:any(f'/level{l}/' in pair[0]['case'] for l in (2,3))
        eligible=[p for p in pairs if challenge(p) and all(r['optimal'] for r in p)]
        rule='first complete 3–8-edge pair'
        if not eligible:
            eligible=[p for p in pairs if '/level0/' not in p[0]['case'] and all(r['optimal'] for r in p)]
            rule='first complete non-adjacent pair; no illustrated-model 3–8-edge pair'
        if not eligible:
            eligible=[p for p in pairs if challenge(p)]
            rule='first 3–8-edge pair; illustrated model has no complete non-adjacent pair'
        pair=eligible[0]
        controls={role:{r['case']:r for r in indexed[k,role,'micro']['cases']}
                  for k,role in ((current,'champion'),(selected,'checkpoint'))}
        fig,axes=plt.subplots(2,4,figsize=(12.5,6.5))
        for row,response in enumerate(pair):
            m=lookup[response['case']]
            grid(axes[row,0],m,shortest(m),True,f"BFS · goal {'AB'[row]} · D={m['oracle_length']-1}")
            for col,label,r in ((1,'Paired',response),(2,'Current',controls['champion'][response['case']]),
                                (3,'V12D',controls['checkpoint'][response['case']])):
                grid(axes[row,col],m,mask(r,m),r['optimal'],label+' · '+('shortest' if r['optimal'] else r['failure']))
        fig.suptitle(f'{topology.capitalize()} signalling · replicate {rep} · validation-ranked primary model',fontsize=13)
        fig.text(.5,.018,'Illustration chosen after confirmation. Blue: source; gold: goal; green: shortest-correct; orange: failed. Each goal is a separate response.',ha='center',fontsize=8)
        fig.subplots_adjust(left=.025,right=.985,bottom=.08,top=.89,wspace=.14,hspace=.20)
        fig.savefig(visual/f'paired_{topology}.png',dpi=170)
        plt.close(fig)
        examples.append(dict(topology=topology,model=selected,cases=[r['case'] for r in pair],case_rule=rule))
    # The evolved-range model above is fixed by validation; show ordinary cases
    # independently of whether its output succeeds.
    general=indexed[selected,'champion','general']['cases']
    other={r['case']:r for r in indexed[current,'champion','general']['cases']}
    previous={r['case']:r for r in indexed[selected,'checkpoint','general']['cases']}
    ordinary_cases=[]
    fig,axes=plt.subplots(2,4,figsize=(12.5,7))
    for row,family in enumerate(('perfect','random')):
        options=[r for r in general if lookup[r['case']]['family']==family and lookup[r['case']]['w']==17]
        response=next((r for r in options if lookup[r['case']]['oracle_length']>=9),options[0])
        m=lookup[response['case']]
        ordinary_cases.append(response['case'])
        grid(axes[row,0],m,shortest(m),True,f"{family.capitalize()} · BFS · D={m['oracle_length']-1}")
        for col,label,r in ((1,'Paired',response),(2,'Current',other[response['case']]),
                            (3,'V12D',previous[response['case']])):
            grid(axes[row,col],m,mask(r,m),r['optimal'],label+' · '+('shortest' if r['optimal'] else r['failure']))
    fig.suptitle(f'Ordinary unseen mazes · evolved signalling · replicate {rep}',fontsize=13)
    fig.text(.5,.018,'First 17×17 case per family with D≥8 when available. Model fixed by validation; illustration does not select on success.',ha='center',fontsize=8)
    fig.subplots_adjust(left=.025,right=.985,bottom=.08,top=.88,wspace=.14,hspace=.25)
    fig.savefig(visual/'ordinary_examples.png',dpi=170)
    plt.close(fig)
    for path in visual.glob('*.svg'):
        path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    (visual/'metadata.json').write_text(json.dumps(dict(matplotlib=matplotlib.__version__,
        scope='Models selected by common validation rank separately within each topology; displayed cases chosen after confirmation by the recorded rule, not a new assay.',
        examples=examples,ordinary_model=selected,ordinary_cases=ordinary_cases),indent=2)+'\n')
    print(visual)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
