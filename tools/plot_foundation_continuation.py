"""Standalone figures from saved V12D data; requires optional Matplotlib only."""
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


def read_gz(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


def run(out):
    out = Path(out)
    visual = out / 'visuals'
    visual.mkdir(exist_ok=True)
    data = json.loads((out / 'plot_data.json').read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'savefig.facecolor': 'white'})
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True)
    colors = {'evolution': '#087e8b', 'resample': '#bd5c37'}
    for i, origin in enumerate(('native', 'fresh')):
        for j, topology in enumerate(('local', 'evolved')):
            ax = axes[i, j]
            for method in ('evolution', 'resample'):
                series = []
                for rep in range(3):
                    key = f'foundation_study/{topology}/{origin}/{method}/{rep}'
                    hs = data['histories'][key]
                    ys = [hs[0]['champion_rank'][1], *[h['champion_rank'][1] for h in hs]]
                    series.append(ys)
                    ax.plot(range(len(ys)), ys, color=colors[method], alpha=.20, linewidth=.8)
                values = np.asarray(series)
                ax.plot(np.arange(values.shape[1]), np.median(values, axis=0), color=colors[method],
                        linestyle='-' if method == 'evolution' else '--', linewidth=2, label=method)
            ax.set_title(f'{origin.capitalize()} origins · {topology} signaling')
            ax.axvline(data['start_generation'], color='#556775', linestyle=':', linewidth=1.2)
            ax.set_ylim(0, 136)
            ax.grid(axis='y', alpha=.18)
            ax.set_xlabel('Completed matched generation')
            ax.set_ylabel('Shortest validation outputs / 136')
    axes[0, 0].legend(frameon=False)
    fig.suptitle('Stable search: validation progress, not fresh-test accuracy', fontsize=15)
    fig.text(.5, .01, 'Bold: median of 3 replicates. Thin: individual replicates. Dotted line: V12D continuation begins at generation 442; earlier history is retained.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .03, 1, .95))
    fig.savefig(visual / 'validation.png', dpi=160)
    fig.savefig(visual / 'validation.svg')
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    labels = [('evolution', 'champion', 'Current evolution', '#087e8b'),
              ('evolution', 'checkpoint', 'V12C checkpoint', '#6d88b0'),
              ('resample', 'champion', 'Resampling', '#bd5c37'),
              ('evolution', 'frozen', 'Original frozen', '#9ba8af')]
    for i, origin in enumerate(('native', 'fresh')):
        for j, topology in enumerate(('local', 'evolved')):
            ax = axes[i, j]
            for offset, (method, role, label, color) in enumerate(labels):
                values = np.asarray([[data['results'][f'foundation_study/{topology}/{origin}/{method}/{rep}/{role}/micro']['levels'][str(level)]['pairs'] / 48
                                      for level in range(4)] for rep in range(3)])
                xs = np.arange(4) + (offset - 1.5) * .20
                ax.bar(xs, values.mean(axis=0), .18, label=label, color=color, alpha=.85)
                for rep in range(3):
                    ax.scatter(xs + (rep - 1) * .035, values[rep], color='#172d3a', s=10, zorder=3)
            ax.set_title(f'{origin.capitalize()} origins · {topology} signaling')
            ax.set_xticks(range(4), ('1', '2–4', '4–8', '8–16'))
            ax.set_xlabel('Source–goal distance (edges)')
            ax.set_ylabel('Fraction of fresh pairs solved optimally')
            ax.set_ylim(-.015, 1.05)
            ax.grid(axis='y', alpha=.15)
    axes[0, 0].legend(frameon=False, fontsize=9)
    fig.suptitle('Fresh paired-goal confirmation · primary selections', fontsize=15)
    fig.text(.5, .01, 'Bars: mean of 3 replicates; dots: each replicate. Each level/replicate has 6 base layouts × 8 correlated poses.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .03, 1, .95))
    fig.savefig(visual / 'fresh_pairs.png', dpi=160)
    fig.savefig(visual / 'fresh_pairs.svg')
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True)
    times = sorted({r['additional_generation'] for r in data['timecourse']})
    upper = .02
    for i, origin in enumerate(('native', 'fresh')):
        for j, topology in enumerate(('local', 'evolved')):
            ax = axes[i, j]
            for method in ('evolution', 'resample'):
                values = []
                for rep in range(3):
                    key = f'foundation_study/{topology}/{origin}/{method}/{rep}'
                    series = [next(r for r in data['timecourse'] if r['condition'] == key and r['additional_generation'] == g) for g in times]
                    ys = [sum(r['levels'][str(l)]['paired_optimal'] for l in (1, 2, 3)) / 144 for r in series]
                    values.append(ys)
                    upper = max(upper, *ys)
                    ax.plot(times, ys, color=colors[method], alpha=.25, linewidth=.8)
                ax.plot(times, np.mean(values, axis=0), marker='o', color=colors[method], linewidth=2, label=method)
            ax.set_title(f'{origin.capitalize()} origins · {topology} signaling')
            ax.set_xlabel('Additional completed generations after V12C')
            ax.set_ylabel('Fraction of non-adjacent pairs solved')
            ax.grid(axis='y', alpha=.18)
    axes[0, 0].set_ylim(-.005, max(.05, upper * 1.12))
    axes[0, 0].legend(frameon=False)
    fig.suptitle('Prespecified transfer time course on the same fresh cases', fontsize=15)
    fig.text(.5, .01, 'Bold: mean of 3 replicates; thin: each replicate. Models selected on validation; final cases constructed after all selections froze.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .03, 1, .95))
    fig.savefig(visual / 'timecourse.png', dpi=160)
    fig.savefig(visual / 'timecourse.svg')
    plt.close(fig)

    frozen = read_gz(out / 'frozen_selections.json.gz')
    lookup = {m['case_id']: m for name in ('mazes.json.gz', 'general_mazes.json.gz')
              for m in read_gz(out / 'confirmation' / name)}
    with gzip.open(out / 'confirmation/outputs.jsonl.gz', 'rt') as f:
        records = [json.loads(line) for line in f]
    indexed = {(r['key'], r['role'], r['scope']): r for r in records}

    def mask(row, maze):
        return np.unpackbits(np.frombuffer(bytes.fromhex(row['mask']), np.uint8), bitorder='little')[:maze['w'] * maze['h']]

    def shortest(m):
        cells = bytes.fromhex(m['cells_hex'])
        queue, parents = deque([m['start']]), {m['start']: None}
        while queue:
            p = queue.popleft()
            if p == m['goal']:
                break
            y, x = divmod(p, m['w'])
            for dy, dx in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                yy, xx = y + dy, x + dx
                q = yy * m['w'] + xx
                if 0 <= yy < m['h'] and 0 <= xx < m['w'] and cells[q] and q not in parents:
                    parents[q] = p
                    queue.append(q)
        result = np.zeros(len(cells), np.uint8)
        p = m['goal']
        if p in parents:
            while p is not None:
                result[p] = 1
                p = parents[p]
        return result

    def grid(ax, m, raster, valid, title):
        cells = np.frombuffer(bytes.fromhex(m['cells_hex']), np.uint8)
        image = np.where(cells, 1, 0)
        image[raster > 0] = 2
        ax.imshow(image.reshape(m['h'], m['w']), interpolation='nearest', vmin=0, vmax=2,
                  cmap=ListedColormap(('#24333e', '#eef1f3', '#20a18b' if valid else '#d46e52')))
        for key, color, marker in (('start', '#2265c8', 'o'), ('goal', '#edb51c', '*')):
            y, x = divmod(m[key], m['w'])
            ax.scatter(x, y, c=color, marker=marker, s=100 if marker == '*' else 40, edgecolors='white', linewidths=.6)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title.replace('_', ' '), fontsize=10)

    # Validation chooses this illustrative model; saved final outputs choose the displayed pair.
    key = max(sorted(k for k, v in frozen.items() if v['config']['method'] == 'evolution'
                     and v['config']['origin'] == 'fresh' and v['config']['topology'] == 'evolved'),
              key=lambda k: tuple(frozen[k]['champion_rank']))
    paired_key = key
    chosen = [r for r in indexed[key, 'champion', 'micro']['cases'] if '/level1/' in r['case']]
    original = {r['case']: r for r in indexed[key, 'checkpoint', 'micro']['cases']}
    pairs = [chosen[i:i + 2] for i in range(0, len(chosen), 2)]
    gains = [p for p in pairs if all(r['optimal'] for r in p) and not all(original[r['case']]['optimal'] for r in p)]
    complete = [p for p in pairs if all(r['optimal'] for r in p)]
    pair = (gains or complete or pairs)[0]
    fig, axes = plt.subplots(2, 3, figsize=(10, 8))
    for i, row in enumerate(pair):
        m, old = lookup[row['case']], original[row['case']]
        grid(axes[i, 0], m, shortest(m), True, f"Goal {'AB'[i]} · BFS shortest · D={m['oracle_length'] - 1}")
        grid(axes[i, 1], m, mask(row, m), row['optimal'], 'Current · ' + ('shortest' if row['optimal'] else row['failure']))
        grid(axes[i, 2], m, mask(old, m), old['optimal'], 'V12C checkpoint · ' + ('shortest' if old['optimal'] else old['failure']))
    cfg = frozen[key]['config']
    fig.suptitle(f"New unseen goal pair · fresh/{cfg['topology']}/replicate {cfg['replicate']} · primary selection", fontsize=13)
    fig.text(.5, .025, 'Post-hoc illustration of the passing cohort; model ranked on validation. Blue: source; gold: goal; green: shortest; orange: failed.', ha='center', fontsize=8)
    fig.subplots_adjust(left=.035, right=.985, bottom=.08, top=.88, wspace=.10, hspace=.28)
    fig.savefig(visual / 'paired_example.png', dpi=170)
    plt.close(fig)

    base = pair[0]['case'].rsplit('/d4-', 1)[0][:-2]
    orbit = {r['case']: r for r in chosen if r['case'].rsplit('/d4-', 1)[0][:-2] == base}
    fig, axes = plt.subplots(4, 4, figsize=(12, 12))
    complete_poses = 0
    for pose in range(8):
        complete_poses += all(orbit[f'{base}/{goal}/d4-{pose}']['optimal'] for goal in ('a', 'b'))
        for i, goal in enumerate(('a', 'b')):
            row = orbit[f'{base}/{goal}/d4-{pose}']
            m = lookup[row['case']]
            ax = axes[pose % 4, 2 * (pose // 4) + i]
            grid(ax, m, mask(row, m), row['optimal'], f"Pose {pose} · goal {goal.upper()} · " + ('shortest' if row['optimal'] else 'failed'))
    fig.suptitle(f"Same maze and genome across all eight poses · {complete_poses}/8 complete pairs", fontsize=14)
    fig.text(.5, .018, 'Same post-hoc illustration as the paired-goal figure; poses are correlated, not eight independent layouts.', ha='center', fontsize=9)
    fig.subplots_adjust(left=.025, right=.975, bottom=.055, top=.93, wspace=.10, hspace=.19)
    fig.savefig(visual / 'orientation_example.png', dpi=160)
    plt.close(fig)

    key = paired_key
    chosen = indexed[key, 'champion', 'general']['cases']
    original = {r['case']: r for r in indexed[key, 'checkpoint', 'general']['cases']}
    fig, axes = plt.subplots(2, 3, figsize=(10, 8))
    examples = []
    for i, family in enumerate(('perfect', 'random')):
        row = next(r for r in chosen if lookup[r['case']]['family'] == family and lookup[r['case']]['w'] == 17 and lookup[r['case']]['oracle_length'] >= 9)
        examples.append(row['case'])
        m, old = lookup[row['case']], original[row['case']]
        grid(axes[i, 0], m, shortest(m), True, f"{family.capitalize()} · BFS · D={m['oracle_length'] - 1}")
        grid(axes[i, 1], m, mask(row, m), row['optimal'], 'Evolved · ' + ('shortest' if row['optimal'] else row['failure']))
        grid(axes[i, 2], m, mask(old, m), old['optimal'], 'V12C checkpoint · ' + ('shortest' if old['optimal'] else old['failure']))
    cfg = frozen[key]['config']
    fig.suptitle(f"Fresh ordinary mazes · {cfg['origin']}/{cfg['topology']}/replicate {cfg['replicate']} · primary selection", fontsize=12)
    fig.text(.5, .025, 'Model chosen on validation. First 17×17 case with D≥8 per family. Larger-grid performance must be judged separately from elementary success.', ha='center', fontsize=8)
    fig.subplots_adjust(left=.035, right=.985, bottom=.08, top=.88, wspace=.10, hspace=.28)
    fig.savefig(visual / 'ordinary_examples.png', dpi=170)
    plt.close(fig)
    for path in visual.glob('*.svg'):
        path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
    (visual / 'metadata.json').write_text(json.dumps(dict(matplotlib=matplotlib.__version__,
        illustration_scope='Cohort chosen after confirmation; model ranked on validation within that cohort; cases illustrative, not a new assay',
        paired_model=paired_key, paired_cases=[r['case'] for r in pair],
        orientation_group=base, complete_paired_poses=complete_poses,
        ordinary_model=key, ordinary_cases=examples), indent=2) + '\n')
    print(visual)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    run(p.parse_args().out)
