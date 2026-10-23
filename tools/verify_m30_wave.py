"""New saved-only M30 wave-arrival check; no additional candidate inference."""
import json,sys,zlib
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.information_flow_m30 import OUT,readz,read_records,writej,check
from maze_evolution.deep_campaign_data import cases_from_manifest
from maze_evolution.evaluator import distances

def main():
    check();assert not (OUT/'wave_arrival_note.json').exists();cases=cases_from_manifest(readz(OUT/'cases.json.gz')['mazes'])
    counts=Counter();per=Counter()
    for spec,r,blob in read_records():
        if spec['phase']!='native' or r['role']=='control':continue
        o=cases[r['case']];h=np.frombuffer(zlib.decompress(blob),dtype='<u2').reshape(r['history_shape']);counts['native_histories']+=1
        for channel,root in ((0,o.maze.start),(1,o.maze.goal)):
            ds=distances(o.maze,root);key=f'C{channel}';counts[key+'_histories']+=1
            for p,open_site in enumerate(o.maze.cells):
                if not open_site:continue
                actual=next((t for t in range(len(h)) if int(h[t,channel,p])>0),None)
                expected=2*ds[p] if ds[p]>=0 else None
                counts[key+'_site_histories']+=1
                if expected is None:
                    assert actual is None,(key,r['case'],p,actual);counts[key+'_unreachable_never_activated']+=1
                elif expected>=len(h):
                    assert actual is None,(key,r['case'],p,actual,expected);counts[key+'_right_censored_before_expected_arrival']+=1
                else:
                    assert actual==expected,(key,r['case'],p,actual,expected);counts[key+'_exact_two_ticks_per_edge']+=1
                    per[(key,actual)]+=1
    writej(OUT/'wave_arrival_note.json',dict(status='PASS',saved_only=True,new_inference=0,new_cases=0,counts=dict(counts),
        arrival_histograms={key:{str(t):v for (c,t),v in sorted(per.items()) if c==key} for key in ('C0','C1')},
        algebraic_reason='C0 is a monotone source-seeded accumulation fed through neighbor-min C5; C7 is monotone accumulation of goal-seeded C1, and C1 reads neighbor-min C7. With zero elsewhere, the first positive crosses exactly one grid edge per two synchronous ticks. Numeric positive values need not be shortest-distance labels.',
        scope='Fixed focal genomes only, inherited mechanism. Source and goal reachability propagate over graph edges; this does not extract a path, prove their full solver general, or establish when the inherited wave first evolved. All tick predictions checked only in actual recorded native windows; later expected arrivals censored.'))

if __name__=='__main__':main()
