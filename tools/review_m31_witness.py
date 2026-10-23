"""Independent saved-raster review of ALL M31 rare controlled successes.
No candidate inference, new maze, new nominee or confirmation is generated.
"""
import json,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import OUT,check,readz,writej,panel_stream,entries
from maze_evolution.deep_campaign_data import cases_from_manifest

def bits(row,n):
    raw=bytes.fromhex(row['mask']);return {p for p in range(n) if (raw[p//8]>>(p%8))&1}
def adjacent(p,w,n):return [q for q in (p-1 if p%w else -1,p+1 if p%w<w-1 else -1,p-w if p>=w else -1,p+w if p+w<n else -1) if q>=0]
def strict_saved(row,o):
    m=o.maze;selected=bits(row,len(m.cells));assert selected and all(m.cells[p] for p in selected)
    assert m.start in selected and m.goal in selected
    for p in selected:assert sum(q in selected for q in adjacent(p,m.w,len(m.cells)))==(1 if p in (m.start,m.goal) else 2)
    todo=[m.start];seen=set()
    while todo:
        p=todo.pop()
        if p in seen:continue
        seen.add(p);todo.extend(q for q in adjacent(p,m.w,len(m.cells)) if q in selected and q not in seen)
    assert seen==selected and len(selected)==len(o.path)
    return len(selected)-1

def main():
    check();assert not (OUT/'witness_review.json').exists();s=json.loads((OUT/'saved_diagnostics.json').read_text());assert len(s['all_controlled_or_sixteen_edge_hits'])==1
    rare=s['all_controlled_or_sixteen_edge_hits'][0];identity=rare['id'];assert identity=='m31/regulated/C6/draw0246' and not rare['nominated']
    con,data,_,_=panel_stream('development');rows=None
    for e,r in entries(con):
        if identity in e['aliases']:rows={x['case']:x for x in r['rows']};break
    con.close();assert rows is not None;mazes={m['case_id']:m for m in data['mazes']};wanted=rare['controlled_individual_cases'];cases=cases_from_manifest([mazes[c] for c in wanted])
    lengths=Counter();physical=[];record=[]
    for cid,o in cases.items():
        assert rows[cid]['optimal'];edges=strict_saved(rows[cid],o);lengths[edges]+=1;selected=bits(rows[cid],len(o.maze.cells))
        # The branch-side observer selected by a correct path is spatially WEST
        # of the junction in ALL successes, even when source/goal are reflected.
        m=data['metadata'][cid];junction=m['junction'];arm=[p for p in m['observers'][1:3] if p in selected]
        assert len(arm)==1 and arm[0]//o.maze.w==junction//o.maze.w and arm[0]%o.maze.w<junction%o.maze.w
        physical.append(o.maze.digest);record.append(dict(case=cid,edges=edges,selected_pixels=len(selected),absolute_west_arm=True))
    pairs=[]
    for c in data['contrasts']:
        if c['kind']!='route_swap':continue
        hits=[key for key in ('a','b') if rows[c[key]]['optimal']]
        if hits:
            assert len(hits)==1;fail=c['b'] if hits==['a'] else c['a'];pairs.append(dict(id=c['id'],success=c[hits[0]],failed_counterpart=fail,failure=rows[fail]['failure'],status=rows[fail]['status']))
    assert len(record)==48 and len(set(physical))==36 and len(pairs)==24
    condition=next(c for c in readz(OUT/'development_summary.json.gz')['conditions'] if c['id']==identity)
    unreachable=[r for r in rows.values() if not r['reachable']]
    writej(OUT/'witness_review.json',dict(status='PASS',saved_only_posthoc=True,new_inference=0,new_cases=0,id=identity,nominated=False,freshly_confirmed=False,
        presentations=48,distinct_full_stimuli=36,independent_scalar_saved_rasters=record,edge_lengths=dict(lengths),all_successes_choose_absolute_west_arm=True,
        matched_route_swap_partial_successes=24,matched_pairs=pairs,matched_failures=dict(Counter(p['failure'] for p in pairs)),
        new_individual_inputs_beyond_declared_portfolio=len(rare['controlled_individual_beyond_portfolio']),complete_both_alternatives=0,
        complete_ordinary_bases=condition['metrics']['ordinary_bases_both_poses'],correct_no_path=condition['correct_no_path'],unreachable_inputs=len(unreachable),
        unreachable_statuses=dict(Counter(r['status'] for r in unreachable)),parent_comparisons=condition['comparisons'][condition['parent']],event=condition['event'],
        limitation='USED controlled rectangle fixtures, 48 presentations/36 full stimuli, orientation-specific west-arm specialist with severe losses. No trace of this unselected mutant, no independent confirmation or complete alternative pair, no claim of remote connectivity-dependent branch choice. Earlier ALL-native audit replays its rows.'))
    a=next(c for c in wanted if c.startswith('flow/M30/n21/gate5/A/') and c.endswith('d4-0'));b=a.replace('/A/','/B/')
    writej(OUT/'witness_render.json',dict(id=identity,development_only=True,selection='First size21/gate5/pose0 A success and its exact B counterpart; illustrative, not a nomination.',
        panels=[dict(maze=mazes[c],row=rows[c],path=(cases[c].path if c in cases else cases_from_manifest([mazes[c]])[c].path)) for c in (a,b)]))

if __name__=='__main__':main()
