"""Descriptive final comparison; all choices were frozen before these results."""
from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/selectivity_pressure'
with gzip.open(OUT/'descriptive_summary.json.gz','rt') as f:s=json.load(f)
arms=('current','selective','resample','frozen');labels=('Current','Selective','Resampling','Frozen')
colors=('#127c80','#8754ad','#d79424','#828b92')
fig,axes=plt.subplots(2,3,figsize=(13,8),layout='constrained')
for row,origin in enumerate(('carry','fresh')):
 for col,(metric,title,denom) in enumerate((('upstream','Prefix 1/2 complete pairs',320),('pairs','All complete pairs',800),('ordinary','Ordinary shortest paths',384))):
  ax=axes[row,col]
  for rep in range(3):
   vals=[s['primaries'][f'{origin}/{rep}/{a}']['metrics'][metric] for a in arms]
   ax.plot(np.arange(4)+(rep-1)*.09,vals,color='#bac2c7',lw=.8,zorder=1)
   for x,(value,color) in enumerate(zip(vals,colors)):ax.scatter(x+(rep-1)*.09,value,color=color,marker=('o','s','^')[rep],s=48,zorder=2)
  ax.set_xticks(range(4),labels,rotation=18,ha='right');ax.set_title(f'{origin.capitalize()} — {title} /{denom}')
  ax.set_ylim(-denom*.025,denom);ax.set_yticks(np.linspace(0,denom,5));ax.grid(axis='y',alpha=.2)
fig.suptitle('Selective-output pressure: untouched final mazes\nThree search replicates per arm; linked dots share founders. Poses and structural variants are correlated.',fontsize=13)
fig.savefig(OUT/'comparison.png',dpi=170);fig.savefig(OUT/'comparison.pdf')
