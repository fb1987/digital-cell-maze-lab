"""Post-hoc explanation from saved V12E/F evidence only; no new inference."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cellular_maze_lab import neighbors
from maze_evolution.evaluator import Maze,Oracle
from maze_evolution.foundation_data import load_pairs
from maze_evolution.foundation_calibration import write_json,ROOT
from maze_evolution.route_confirmation import OUT,lines,sha


def run():
    prior=ROOT/'results/foundation_pair'
    original_analysis=json.loads((prior/'analysis.json').read_text())
    selected=[r for r in original_analysis['longer_primary_ordinary_geometry']
              if r['id']=='foundation_study/local/fresh/evolution/1/i72095']
    wanted={r['case'] for r in selected}
    old_geometry=[]
    for row in json.load(gzip.open(prior/'confirmation/general_mazes.json.gz','rt')):
        if row['case_id'] not in wanted:continue
        m=Maze(bytes.fromhex(row['cells_hex']),row['w'],row['h'],row['start'],row['goal'])
        o=Oracle.build(m)
        degree=lambda p:sum(m.cells[q] for q in neighbors(p,m.w,m.h))
        old_geometry.append(dict(case=row['case_id'],edges=len(o.path)-1,
            source_degree=degree(m.start),goal_degree=degree(m.goal),
            internal_degrees=[degree(p) for p in o.path[1:-1]],
            internal_branch_vertices=[p for p in o.path[1:-1] if degree(p)>2],oracle_path=o.path))
    assert len(old_geometry)==3
    rows=list(lines(OUT/'confirmation/normal.jsonl.gz'))
    lookup={(r['model'],r['variant'],r['case']):r for r in rows}
    ids=[r['case'] for r in rows if r['model']=='target' and r['variant']=='normal']
    comparisons={}
    for other in ('parent','flag_off','pulse_off','source_only'):
        model,variant=('parent','normal') if other=='parent' else ('target',other)
        comparisons[other]={}
        for label,fields in (('same_mask',['mask']),('same_output_status_steps',['mask','status','steps']),
                            ('same_work',['reads','dispatches','active'])):
            comparisons[other][label]=sum(all(lookup['target','normal',c][f]==lookup[model,variant,c][f] for f in fields) for c in ids)
    trajectory_hashes={}
    alignments=Counter()
    for record in lines(OUT/'confirmation/trajectories.jsonl.gz'):
        variant=record['variant'];row=record['reaction']
        trajectory_hashes[variant,row['case']]=record['history']['raw_sha256']
        alignments[variant+'/all96']+=row['steps']==96
    reachable=[c for c in ids if lookup['target','normal',c]['reachable']]
    exact_flags={}
    for a,b in (('normal','flag_off'),('pulse_off','both_off')):
        exact_flags[a+'/'+b]=sum(trajectory_hashes[a,c]==trajectory_hashes[b,c] for c in reachable)
    counts={}
    for variant in ('normal','pulse_off','flag_off','both_off','source_only'):
        rs=[lookup['target',variant,c] for c in ids]
        counts[variant]=dict(status=dict(Counter(r['status'] for r in rs)),failures=dict(Counter(r['failure'] for r in rs)),
            steps_min=min(r['steps'] for r in rs),steps_max=max(r['steps'] for r in rs))
    write_json(OUT/'saved_diagnostics.json',dict(scope='Post-hoc explanatory analysis of already inspected V12E and frozen V12F saved data; no new inference, tuning, selection or holdout.',
        previous_long_success_geometry=old_geometry,normal_cases=len(ids),normal_comparisons=comparisons,
        reachable_cases=len(reachable),complete_trace_equality=exact_flags,full96_traces=dict(alignments),
        target_status=counts,source_sha256=sha(__file__),input_sha256={str(p.relative_to(ROOT)):sha(p) for p in
            (prior/'analysis.json',prior/'confirmation/general_mazes.json.gz',OUT/'confirmation/normal.jsonl.gz',OUT/'confirmation/trajectories.jsonl.gz')}))
    print(json.dumps(dict(earlier_internal_branch_counts=[len(r['internal_branch_vertices']) for r in old_geometry],comparisons=comparisons,exact_flags=exact_flags,full96=dict(alignments)),indent=2))


if __name__=='__main__':run()
