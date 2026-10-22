"""Posthoc retention sensitivity; fixed saved results, no new nominees/cases."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.guarded_extension import OUT,check,readz,writej

def main():
    check();assert not (OUT/'retention_sensitivity.json').exists()
    screen=readz(OUT/'selection.json.gz')['features'];s=json.loads((OUT/'summary.json').read_text())
    final={n['identity']:n['result'] for n in s['nominations'] if n['role']!='random_control'}
    result={}
    for split,features in [('development',screen),('confirmation_fixed_nominees',final)]:
        rows=[]
        for cutoff in (1.,.95,.9,.8,.5,0.):
            for a0 in (True,False):
                counts={a:0 for a in ('ordinary','overwrite','guarded')};identities=[]
                for i,v in features.items():
                    keep=1-v['lost_source_correct']/v['source_correct_denominator'] if v['source_correct_denominator'] else 0
                    fractions=[r for r in v['source_retention'].values() if r is not None]
                    if keep<cutoff or min(fractions,default=0)<cutoff or v['metrics']['false_no_path']:continue
                    if a0 and not (v['a0_denominator'] and v['a0_fraction']>=.9):continue
                    if any(v['novel_units_beyond_archive'].values()):counts[i.split('/')[0]]+=1;identities.append(i)
                rows.append(dict(minimum_overall_and_each_nonempty_source_class_retention=cutoff,
                    additional_nonempty_a0_90percent_gate=a0,counts=counts,identities=sorted(identities)))
        result[split]=rows
    writej(OUT/'retention_sensitivity.json',dict(status='PASS',scope='POSTHOC descriptive sensitivity, no new execution/cases or reselection; does not replace primary endpoint',
        fixed_zero_false_no_path=True,results=result))

if __name__=='__main__':main()
