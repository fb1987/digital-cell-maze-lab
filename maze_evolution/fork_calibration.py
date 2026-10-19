"""V12G construction-only controls; known algorithms never enter research populations."""
import gzip,json,time
import numpy as np
from .fork_data import FIXTURES,load,ForkData,CONSTRUCTION_SEED,cut_group
from .fork_fitness import evaluate,branch_score
from .foundation_calibration import controls,LIMITS,write_json
from .baselines import baseline
from .evaluator import assess


def run():
    t=time.perf_counter();cases,groups=load(FIXTURES)
    selected=[g for g in groups if g.key[0]=='construction']
    data=ForkData(CONSTRUCTION_SEED)
    data.cache=cases;data.groups={g.key:g for g in groups}
    from .foundation_data import layout_hash
    data.layouts={layout_hash(o.maze) for o in cases.values()}
    for g in list(selected):
        if 'corridor' not in g.key and g.level==0:selected.append(cut_group(data,g))
    data.save(FIXTURES)
    pairs=[p for g in selected for p in g.pairs];summary={};synthetic=[]
    with gzip.open(FIXTURES/'calibration.jsonl.gz','wt') as f:
        for name,item in controls().items():
            ev=evaluate(item,pairs,'evolved',LIMITS,'branch')
            f.write(json.dumps(dict(control=name,item=item.save(),rows=ev.rows),separators=(',',':'))+'\n')
            summary[name]=dict(inputs=len(ev.rows),valid=sum(r['valid'] for r in ev.rows),optimal=sum(r['optimal'] for r in ev.rows),no_path=sum(r['no_path'] for r in ev.rows),strict_pairs=sum(r['pair_strict'] for r in ev.rows)//2,complete_fork_pairs=sum(r['fork'] and r['pair_optimal'] for r in ev.rows)//2)
    for g in selected:
        if g.level<0 or 'corridor' in g.key:continue
        for pair in g.pairs:
            for side,o in enumerate(pair.cases):
                lab=o._foundation_label;values={}
                for name,vertices in (('blank',[]),('prefix',lab['prefix']),('leaking',lab['prefix']+lab['exits']),('choice',lab['prefix']+lab['allowed'][side]),('route',o.path)):
                    mask=np.zeros(len(o.maze.cells),np.uint8);mask[vertices]=1
                    values[name]=branch_score(mask,o,side)
                assert values['blank']['score']<values['prefix']['score']<values['leaking']['score']<values['choice']['score']<=values['route']['score']
                assert values['choice']['strict'] and values['route']['strict'] and not values['leaking']['strict']
                synthetic.append(dict(case=o.maze.case_id,values=values))
    bfs=[]
    for pair in pairs:
        for o in pair.cases:
            m=o.maze;r=baseline('compiled_bfs',m.cells,m.w,m.h,m.start,m.goal);a=assess(r,o)
            assert a.optimal or a.no_path_correct
            bfs.append(dict(case=m.case_id,status=r.status,mask=np.packbits(r.mask,bitorder='little').tobytes().hex()))
    assert summary['intact']['optimal']==192 and summary['intact']['no_path']==32 and summary['intact']['complete_fork_pairs']==48
    assert any(v['optimal']<192 for k,v in summary.items() if k!='intact')
    write_json(FIXTURES/'synthetic.json',synthetic);write_json(FIXTURES/'bfs.json',bfs)
    write_json(FIXTURES/'calibration_summary.json',dict(controls=summary,synthetic_outputs=len(synthetic)*5,bfs_inputs=len(bfs),seconds=time.perf_counter()-t,passed=True))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
