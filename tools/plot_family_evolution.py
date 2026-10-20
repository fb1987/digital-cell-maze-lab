"""Descriptive figure from frozen selections; no selection or inference."""
from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/family_evolution'
with gzip.open(OUT/'descriptive_summary.json.gz','rt') as f:s=json.load(f)
arms=('current_mutation','family_mutation','resample','frozen');labels=('Mutation','Family reserve','Resampling','Frozen')
colors=('#127c80','#8754ad','#d79424','#828b92')
fig,axes=plt.subplots(2,4,figsize=(16,8),layout='constrained')
for row,origin in enumerate(('carry','fresh')):
 for col,(metric,title) in enumerate((('prefix4','Prefix 4 pairs /224'),('pairs','All complete pairs /1120'),('ordinary','Ordinary paths /384'))):
  ax=axes[row,col]
  for rep in range(3):
   vals=[s['primaries'][f'{origin}/{rep}/{a}']['metrics'][metric] for a in arms]
   ax.plot(np.arange(4)+(rep-1)*.07,vals,color='#bac2c7',lw=.8,zorder=1)
   for x,(value,color) in enumerate(zip(vals,colors)):ax.scatter(x+(rep-1)*.07,value,color=color,marker=('o','s','^')[rep],s=45,zorder=2)
  ax.set_xticks(range(4),labels,rotation=22,ha='right');ax.set_title(f'{origin.capitalize()} — {title}');denom={'prefix4':224,'pairs':1120,'ordinary':384}[metric];ax.set_ylim(-denom*.015,denom);ax.set_yticks(np.linspace(0,denom,5));ax.grid(axis='y',alpha=.2)
 ax=axes[row,3]
 for arm,label,color in zip(arms,labels,colors):
  for rep in range(3):
   ss=s['family_trajectories'][f'{origin}/{rep}/{arm}']
   ax.plot([x['generation'] for x in ss],[x['effective'] for x in ss],color=color,alpha=.65,lw=1,label=label if rep==0 else None)
 ax.set_title(f'{origin.capitalize()} — effective mutable families');ax.set_xlabel('Completed generation');ax.set_yscale('log');ax.grid(alpha=.2)
 if row==0:ax.legend(fontsize=8)
fig.suptitle('Family reserve versus ordinary mutation — untouched final results\nDots are three search replicates; linked dots share founders. Family count is diagnostic, not solver fitness.',fontsize=14)
fig.savefig(OUT/'comparison.png',dpi=170);fig.savefig(OUT/'comparison.pdf')
