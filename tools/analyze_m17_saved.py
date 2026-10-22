"""Post-hoc M17 saved-response comparison only; no evaluations or selection."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.spare_state_assay import OUT,load,readz,writej,check

def main():
    check();assert not (OUT/'saved_response_comparison.json').exists()
    data,rows,_=load(True);summary=json.loads((OUT/'summary.json').read_text());out={};lengths={}
    for n in summary['nominations']:
        if n.get('arm')=='spare' and n.get('anchor'):
            a=rows[n['identity']];b=rows['anchor/'+n['anchor']]
            assert [x['case'] for x in a]==[x['case'] for x in b]
            out[n['identity']]={f:sum(x[f]!=y[f] for x,y in zip(a,b)) for f in ('mask','status','steps','optimal','no_path')}
        if n.get('arm')=='overwrite' and n.get('anchor')=='parent':
            lengths[n['identity']]={base:len(next(m for m in data['metadata'].values() if m.get('base')==base)['path'])-1 for base in n['result']['versus_parent']['new_ordinary_base_keys']}
    del data,rows
    data,rows,_=load();compared=0
    for k in range(256):
        a=rows[f'unchanged/random/{k:04d}'];b=rows[f'spare/random/{k:04d}']
        for x,y in zip(a,b):
            assert {k:v for k,v in x.items() if k!='array_bytes'}=={k:v for k,v in y.items() if k!='array_bytes'}
            compared+=1
    writej(OUT/'saved_response_comparison.json',dict(scope='Post-hoc saved-record comparison, zero candidate calls; no new cases or reselection',
        spare_nominee_anchor_differences=out,overwrite_parent_new_ordinary_lengths=lengths,
        neutral_random_screen_pairs_compared=compared,neutral_random_fields_except_memory_all_equal=True,
        limitation='Finite-panel equality, not proof of global semantic equivalence. Native screen outputs have the registered sampled replay audit, not an additional complete native replay here.'))
if __name__=='__main__':main()
