"""Retrospective illustration from saved normal masks; zero new candidate calls."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.selectivity_study import *

def main():
    choices=read_compressed(OUT/'choices.json.gz');cases,_,meta=load(OUT/'confirmation')
    aliases=['fresh/0/current/primary','fresh/0/selective/primary','carry/0/current/primary'];pids={choices['aliases'][a] for a in aliases}
    rows={e['key']:{r['case']:r for r in e['rows']} for e in lines(OUT/'confirmation/responses.jsonl.gz') if e['key'] in pids}
    anchor=rows[choices['aliases'][aliases[-1]]]
    eligible=[c for c,r in anchor.items() if meta[c]['family']=='paired' and meta[c]['prefix']==2 and meta[c]['graph']=='cycle' and meta[c]['pose']==0 and not r['optimal']]
    first=min(eligible);q=meta[first];ids=sorted(c for c,m in meta.items() if m['family']=='paired' and m['base']==q['base'] and m['pose']==q['pose'])
    out=[]
    for cid in ids:
        o=cases[cid];m=o.maze
        assert rows[choices['aliases'][aliases[0]]][cid]['mask']==rows[choices['aliases'][aliases[1]]][cid]['mask']
        out.append(dict(case=cid,width=m.w,height=m.h,cells=[int(v) for v in m.cells],start=m.start,goal=m.goal,path=o.path,rows={a:rows[choices['aliases'][a]][cid] for a in aliases}))
    assert len(out)==2
    write_json(OUT/'illustration.json',dict(post_hoc=True,new_candidate_calls=0,selection='Lexicographically first pose-zero prefix-two cycle failure of the frozen carried primary, with its paired goal.',cases=out,identities={a:choices['items'][a]['id'] for a in aliases}))
if __name__=='__main__':main()
