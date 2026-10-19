"""Plot all preregistered V12S primary comparisons from saved summaries only."""
from pathlib import Path
import gzip
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/composition_study'
with gzip.open(OUT / 'analysis.json.gz', 'rt') as f:
    analysis = json.load(f)
description = json.loads((OUT / 'descriptive_outcomes.json').read_text())
with gzip.open(OUT / 'confirmation/metadata.json.gz', 'rt') as f:
    metadata = json.load(f)
opportunities = len({(m['base'], m['pose']) for m in metadata.values()
                     if m['family'] == 'paired' and m['prefix'] > 0})

fig, axes = plt.subplots(2, 2, figsize=(12, 7.6))
colors = ['#8996a8', '#2878b5', '#a54db3', '#d48d37']
arms = ('frozen', 'mutation', 'recombination', 'resample')
for col, origin in enumerate(('carry', 'fresh')):
    ax = axes[0, col]
    for j, arm in enumerate(arms):
        values = [analysis['results'][f'{origin}/{r}']['final'][arm]['positive'] for r in range(3)]
        xpos = np.arange(3) + (j - 1.5) * .19
        ax.bar(xpos, values, .18, color=colors[j], label=arm.capitalize())
        for x, y in zip(xpos, values):
            ax.annotate(str(y), (x, y), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=8)
    ax.set_xticks(range(3), ['Replicate 0', 'Replicate 1', 'Replicate 2'])
    ax.set_title('Preserved origins' if origin == 'carry' else 'Fresh random origins')
    ax.set_ylabel(f'Correct positive-prefix pairs / {opportunities}')
    ax.set_ylim(0, max(10, ax.get_ylim()[1] * 1.2))
    ax.grid(axis='y', alpha=.2)
    ax.set_axisbelow(True)
    if col == 1:
        ax.legend(fontsize=8, loc='upper right')
    ax = axes[1, col]
    cs = [description['reproduction'][f'{origin}/{r}/recombination'] for r in range(3)]
    attempts = np.array([c['attempts'] for c in cs])
    splices = np.array([c['splices'] for c in cs])
    useful = np.array([c['any_positive_donor_gain'] for c in cs])
    ax.bar(range(3), useful, color='#a54db3', label='Splice with donor score gain')
    ax.bar(range(3), splices-useful, bottom=useful, color='#d2a8d9', label='Splice without score gain')
    ax.bar(range(3), attempts-splices, bottom=splices, color='#dce0e6', label='No compatible donor')
    ax.set_xticks(range(3), ['Replicate 0', 'Replicate 1', 'Replicate 2'])
    ax.set_ylabel('Mating attempts')
    ax.set_ylim(0,max(attempts)*1.35)
    ax.grid(axis='y', alpha=.2)
    ax.set_axisbelow(True)
    if col == 0:
        ax.legend(fontsize=8, loc='upper right')

common_top = max(ax.get_ylim()[1] for ax in axes[0])
for ax in axes[0]:
    ax.set_ylim(0, common_top)
fig.suptitle('Compatible recombination: fresh confirmation and actual operator use', fontsize=14)
fig.text(.5, .015, 'Top: normal shortest paths to both goals. Bottom: donor score gains include partial credit; they do not prove ability transfer.\nPoses and graph variants are correlated. All primaries shown; no final reselection.\nThe passing recombination-arm winner has mutation-only ancestry.', ha='center', fontsize=9)
fig.tight_layout(rect=(0, .085, 1, .95))
fig.savefig(OUT / 'comparison.png', dpi=180)
fig.savefig(OUT / 'comparison.pdf')
